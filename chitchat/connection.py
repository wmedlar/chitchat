import asyncio
import abc
    
    
class AsynchronousConnection:
    """
    Attributes:
        loop:
    """
    
    def __init__(self, *, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        
        self.reader, self.writer = None, None
        
    
    @abc.abstractmethod
    def handle_incoming(self, data):
        """Called to handle each line of data sent by the server."""
        pass
        
        
    @property
    def loop(self):
        """Read-only event loop."""
        return self._loop
    
    
    @property
    def connected(self):
        """Read-only connection status."""
        try:
            # if reader or writer have received EOF then we've disconnected
            return (not self.reader.at_eof()) and (not self.writer.is_closing())
        
        except AttributeError:
            # reader/writer haven't been set yet
            return False
    
    
    async def run(self, host, port, **kwargs):
        
        await self.connect(host, port, **kwargs)
        
        handle = self.handle_incoming
        
        # iterate over lines as they're received, until EOF
        async for line in self.reader:
            handle(line)
        
        await self.disconnect()
        
    
    def run_blocking(self, host, port, **kwargs):
    
        coro = self.run(host, port, **kwargs)
        self.loop.run_until_complete(coro)

    
    async def connect(self, host, port, **kwargs):
        """
        Open a connection to `host`.
        """        
        streams = await asyncio.open_connection(host, port, loop=self.loop, **kwargs)
        
        self.reader, self.writer = streams
        
        return streams
    
    
    async def disconnect(self):
        """
        Close the connection with the host.
        """
        self.close_streams()
        self.reader, self.writer = None, None
        
        
    def close_streams(self):
        reader, writer = self.reader, self.writer
        
        if not reader.at_eof():
            reader.feed_eof()
        
        if writer.can_write_eof():
            writer.write_eof()
            
        writer.close()
        
        
    async def read(self, n=None):
        """
        Read up to `n` bytes.
        
        If `n` is not provided, or negative, read until EOF and return all bytes.
        
        This method is a coroutine.
        """
        # default of None is more Pythonic than -1
        n = -1 if n is None or n < 0 else n
        return self.reader.read(n)
    
    
    async def readline(self):
        """
        Read one line, where "line" is a sequence of bytes ending with "\n".
        
        If EOF is received, and \n was not found, the method will return the partial read
        bytes.

        If the EOF was received and the internal buffer is empty, return an empty bytes
        object.
        
        This method is a coroutine.
        """
        return self.reader.readline()
    
    
    async def readexactly(self, n):
        """
        Read exactly `n` bytes.
        
        Raise an `asyncio.IncompleteReadError` if the end of the stream is reached before
        `n` can be read, the `asyncio.IncompleteReadError.partial` attribute of the
        exception contains the partial read bytes.
        
        This method is a coroutine.
        """
        return self.reader.readexactly(n)
    
    
    async def write(self, data):
        """
        Write some data bytes to the transport and flush the buffer.
        
        This method is a coroutine.
        """
        writer = self.writer
        writer.write(data)
        await writer.drain()
        
        
    async def writelines(self, data):
        """
        Write an iterable of data bytes to the transport and flush the buffer.
        
        This method is a coroutine.
        """
        writer = self.writer
        writer.writelines(data)
        await writer.drain()