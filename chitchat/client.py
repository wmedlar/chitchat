import asyncio
import collections
import functools

from .connection import IRCProtocol
from . import constants, decorator, structures, utils


class Client:
    
    
    def __init__(self, *, encoding='UTF-8', loop=None):
        self.encoding = encoding
        self.loop = loop or asyncio.get_event_loop()

        # list ensures plugins trigger in the order they were added
        self.plugins = structures.CaseInsensitiveDefaultDict(list)
        self.protocol = None
    
    
    async def handle(self, line):
        """
        Called to handle each line received from the server.
        """
        
        decoded = line.decode(self.encoding)
        
        try:
            # split message into its component parts
            prefix, command, params = utils.ircsplit(decoded)
        except ValueError:
            raise ValueError(decoded)
        
        # parses the nick, user, and host from prefix and sets as attributes
        prefix = structures.prefix(prefix)
        
        triggered = await self.trigger(command, prefix, *params)
        
        return triggered
    
    
    def on(self, command=constants.PRIVMSG, **conditions):
        """
        Decorator for functions to trigger upon receiving a specified type of message.
        """
        
        # the method called to handle lines returned by the callback
        handler = self.send
        conditional = utils.conditional(**conditions)
        
        # method called to register the callback with the listener
        registrar = functools.partial(self.register, command, conditional=conditional)
        
        return decorator.callback(handler, registrar)
    
    
    def register(self, command, func, conditional=None):
        """
        Adds a function to the client's set of triggers.
        """
        
        self.plugins[command].append((func, conditional))
            
        return self.plugins
    
    
    async def connect(self, host, port, **kwargs):
        
        # don't store the host, port, etc. as attributes to make
        # it clear that they can't be changed while connected
        
        protocol = IRCProtocol(client=self, loop=self.loop)
        
        self.transport, self.protocol = await self.loop.create_connection(
            (lambda: protocol), host, port, **kwargs
        )
        
        # trigger CONNECTED commands with remote peer host and port
        peer = self.transport.get_extra_info('peername')
        await self.trigger(constants.CONNECTED, *peer)
        
        
    async def disconnect(self):
        
        # must grab this info before we close the transport
        peer = self.transport.get_extra_info('peername')
        
        # close the transport, blocking any more data from being sent to the server
        self.transport.close()
        self.transport = None
        
        # trigger DISCONNECTED commands with remote peer host and port
        await self.trigger(constants.DISCONNECTED, *peer)

    
    def run(self, host, port, **kwargs):
        self.loop.run_until_complete(self.connect(host, port, **kwargs))
        self.loop.run_forever()
        
    
    async def send(self, lines):
        
        if not self.protocol:
            raise RuntimeError('connect to a server first')
        
        self.protocol.send(lines)
    
    
    async def trigger(self, command, *args, **kwargs):
        """
        Passes parsed arguments to any registered listeners.
        """
        
        # TODO: move conditions inside function call so they don't block in the loop
        #       can return early if the message is insufficient
        
        plugins = self.plugins[command]
        
        for func, conditions in plugins:
            
            if not conditions or conditions(*args, **kwargs):
                coro = func(*args, **kwargs)
                self.loop.create_task(coro)
    
    
    def wait_for(self, command=constants.PRIVMSG, timeout=None, **conditions):
        
        # this function returns a coroutine that must be awaited
        # but is not a (native or otherwise) coroutine itself
        # async def would require a user to decorate their plugin with @asyncio.coroutine
        
        future = asyncio.Future(loop=self.loop)
        
        async def waiter(*args, **kwargs):
            
            # multiple messages can trigger our waiter before the done callback
            # has had a chance to remove the waiter from a client's plugins
            # so we'll make sure the future's result hasn't been set by a previous
            # message before we attempt to set it
            
            if not future.done(): # does this encounter a race condition?
                future.set_result(args)
        
        # TODO: handle conditions
        self.register(command, waiter, None)
        
        def remove(future):
            self.plugins[command].remove((waiter, None))
            
        # create a callback to remove the future from our plugins once it completes
        future.add_done_callback(remove)
        
        # coroutine must be awaited
        return asyncio.wait_for(future, timeout)
        
        