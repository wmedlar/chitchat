import asyncio
import functools
import inspect

from . import connection, constants, structures, utils


class Client(connection.AsyncConnection):
    
    
    def __init__(self, *, encoding='UTF-8', loop=None):
        super().__init__(
            encoding=encoding,
            loop=loop or asyncio.get_event_loop()
        )

        # list ensures plugins trigger in the order they were added
        self.callbacks = structures.CaseInsensitiveDefaultDict(list)
    
    
    async def connect(self, host, port, **kwargs):
        """
        Connect to a remote `host` on port `port`. Additional kwargs are passed to
        `asyncio.BaseEventLoop.create_connection`.
        
        Triggers functions decorated with @chitchat.on('CONNECTED').
        """
        
        await super().connect(host, port, **kwargs)
        
        # trigger CONNECTED commands with remote peer host and port
        peer = self.transport.get_extra_info('peername')
        self.trigger(constants.CONNECTED, *peer)
        
        
    async def disconnect(self, exc=None):
        """
        Closes the transport after disconnecting from the remote host.
        
        Triggers functions decorated with @chitchat.on('DISCONNECTED') with the remote
        host and port, and any exception propagated from the server. No messages are
        sent after this function is called, until reconnecting to the server. Any messages
        returned by triggered functions will be sent as soon as the client reconnects.
        
        args:
            exc: Exception propagated from the transport. This exception is passed as
                 the last argument to any function triggered.
        """
        
        # remote host and port must be grabbed before AsyncConnection closes the transport
        peer = self.transport.get_extra_info('peername')
        
        # closes the transport, no messages are sent after this until reconnected
        await super().disconnect(exc)
        
        # trigger afterwards, as a triggered function may want to reconnect
        self.trigger(constants.DISCONNECTED, *peer, exc)

    
    def handle(self, raw):
        """
        Called by the protocol to handle each line received from the server.
        """
        command, *params = self.parse(raw)
        self.trigger(command, *params)
        
        
    def parse(self, raw):
        decoded = raw.decode(self.encoding)
        prefix, command, params = utils.ircsplit(decoded)
        
        return (command, structures.prefix(prefix), *params)
    
    
    def on(self, command, *, validator=None, **kwargs):
        """
        Register a function to be called when a message of type `command` is received.
        """
        
        if validator is None:
            validator = structures.Validator(**kwargs)
        
        def wrapped(func):
            cb = structures.Callback(func, validator)
            # cb = structures.Callback(func, kwargs)
            self.register(command, cb)
            
            # return original function so this decorator can be chained
            return func
        
        return wrapped
    
    
    def register(self, command, callback):
        """
        Add an asynchronous function to a client's set of callbacks.
        """
        cb = callback
        self.callbacks[command].append(cb)
    
    
    def deregister(self, command, callback):
        """
        Remove a function from a client's set of callbacks.
        """
        cb = callback
        self.callbacks[command].remove(cb)
    
    
    def trigger(self, command, *args):
        """
        Arrange for registered callbacks to be run with args, and for their returned
        values to be sent to the server.
        """
        
        callbacks = self.callbacks[command] + self.callbacks[constants.ALL]
        
        # schedule the coroutines to be executed and awaited
        # a separate task awaits each coroutine so they don't block each other
        for cb in callbacks:
            coro = self._run_callback(cb, *args)
            self.loop.create_task(coro)
            
        return callbacks
    
    
    async def shutdown(self):
        
        await self.queue.put(connection.AsyncConnection.EXIT)
        await self.queue.join()
        
        for task in asyncio.Task.all_tasks():
            task.cancel()
            
        self.loop.stop()

    
    def run(self, host, port, **kwargs):
        
        coro = self.connect(host, port, **kwargs)
        self.loop.run_until_complete(coro)
        
        try:
            self.loop.run_forever()
            
        except KeyboardInterrupt:
            coro = self.shutdown()
            self.loop.run_until_complete(coro)
            
        finally:
            self.loop.close()
    
    
    def wait_for(self, command, *, timeout=None, **kwargs):
        
        # this function returns a coroutine that must be awaited
        # but is not a (native or otherwise) coroutine itself
        # async def would require a user to decorate their plugin with @types.coroutine
        
        future = asyncio.Future(loop=self.loop)
        
        def waiter(*args):
            
            # multiple messages can trigger our waiter before the done callback
            # has had a chance to remove the waiter from a client's plugins
            # so we'll make sure the future's result hasn't been set by a previous
            # message before we attempt to set it
            
            if not future.done():
                future.set_result(args)
        
        cb = structures.Callback(waiter, structures.Validator(**kwargs))
        self.register(command, cb)
        
        def remove(future):
            self.deregister(command, cb)
        
        # create a callback to remove the future from our plugins once it completes
        future.add_done_callback(remove)
        
        # wrap future in asyncio.wait_for to allow for a timeout
        return asyncio.wait_for(future, timeout)

    
    async def _run_callback(self, callback, *args):
        """
        Asynchronously runs a triggered callback function and schedules any yielded or
        returned lines to be sent to the server.
        """
        
        result = await callback(*args)
        it = filter(None, result or [])
        
        for i in it:
            
            try:
                # coroutines like Client.wait_for or asyncio.sleep must be awaited
                await i
            
            except TypeError:
                # non-awaitables are sent to the server
                await self.send(i)
                
        return