import abc
import asyncio

from . import constants, structures, utils


class IRCProtocol(asyncio.Protocol):
    
    
    def __init__(self, client, loop=None):
        self.client = client
        self.loop = loop or asyncio.get_event_loop()
        
        self.buffer = bytearray()
    
    
    def connection_lost(self, exc):
        coro = self.client.disconnect(exc=exc)
        self.loop.create_task(coro)
    
    
    def data_received(self, data):
        
        self.buffer.extend(data)
        
        try:
            # splits the buffer at the rightmost newline
            # new buffer will be empty if a full line is received
            lines, self.buffer = self.buffer.rsplit(b'\n', maxsplit=1)
            
        except ValueError:
            # buffer is only part of a single line
            # wait to receive more data before passing this to the client
            return
        
        for line in lines.splitlines():
            self.client.handle(line)
    
    
    def eof_received(self):
        pass
        
        
class AsyncConnection:
    """
    An asynchronous connection object for reading from and writing to an IRC server.
    """
    
    EXIT = object()
    
    
    def __init__(self, encoding, loop):
        self.encoding = encoding
        self.loop = loop
        
        # override in subclass for some form of flood control?
        self.queue = asyncio.Queue(maxsize=0, loop=loop)
        
        self.transport = None
        self.protocol = None
        
        
    def protocol_factory(self):
        """
        Factory function for creating IRCProtocol instances.
        """
        return IRCProtocol(client=self, loop=self.loop)  
    
    
    async def connect(self, host, port, **kwargs):
        """
        Connect to a remote `host` on port `port`. Additional kwargs are passed to
        `asyncio.BaseEventLoop.create_connection`.
        
        Triggers functions decorated with @chitchat.on('CONNECTED').
        """
        
        # don't store the host, port, etc. as attributes to make
        # it clear that they can't be changed while connected
        
        self.transport, self.protocol = await self.loop.create_connection(
            self.protocol_factory, host, port, **kwargs
        )
        
        self.loop.create_task(self._run())
        
        
    async def disconnect(self, exc=None):
        """
        Cleans up the transport after disconnecting from the remote host and stops the
        event loop.
        
        Triggers functions decorated with @chitchat.on('DISCONNECTED') with the remote
        host and port, and any exception propagated from the server.
        
        args:
            exc: Exception propagated from the transport. This exception is passed as
                 the last argument to any function triggered.
        """
        
        # let the queue know it ought to stop, otherwise it would
        # block until it received another message that will never come
        await self.queue.put(AsyncConnection.EXIT)
        await self.queue.join()
        
        self.transport = None
        self.protocol = None
        
        
    async def send(self, line):
        """Schedules a line to be sent to the host server."""
        
        # strings have to be encoded before sending
        if isinstance(line, str):
            line = line.encode(self.encoding)
        
        # queue implemented for flood control
        await self.queue.put(line)
        
    
    async def _run(self):
        
        # local scope for speedier loops
        queue = self.queue
        
        while True:
            
            line = await queue.get()
            
            # this is so the task completes gracefully
            if line is AsyncConnection.EXIT:
                queue.task_done()
                break
            
            self.transport.write(line)
            queue.task_done()

    
    @abc.abstractmethod
    def handle(self, line):
        pass