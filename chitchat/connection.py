import abc
import asyncio

from .constants import CONNECTED, DISCONNECTED
from .utils import prep
    

class Connection:
    
    
    def __init__(self, host, port, *, encoding='UTF-8', **kwargs):
        self.host = host
        self.port = port
        self.encoding = encoding
        self.kwargs = kwargs
        
        self.connected = False
        self.reader = None
        self.writer = None
        
    
    async def connect(self, *, loop=None):
        """Open a connection to the host."""
        
        loop = loop or asyncio.get_event_loop()
        
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port, loop=loop, **self.kwargs)
        self.connected = True

        # mimic recieving a 'CONNECTED' command - a pseudocommand to signify that we have connected to the server
        await self.handle(prep(CONNECTED, self.encoding))
    


    async def disconnect(self):
        """Disconnect from server and clean up transport."""

        self.connected = False

        # mimic recieving a 'DISCONNECTED' command - a pseudocommand to signify that we have been disconnected from the server
        await self.handle(prep(DISCONNECTED, self.encoding))
    

    async def handle(self, line):
        """
        Message handler called by `self.run`. This method exists to be overridden in subclasses
        and does nothing by default.
        """

        pass
    
    
    async def prepare(self, line):
        """
        Prepares a string to be sent to the transport stream. By default this method simply encodes the string to a
        bytes object using the supplied encoding.
        """
        return line.encode(self.encoding)
    


    async def run(self, *, loop=None):
        """
        The main method of the Connection class, run within an event loop to connect to an IRC server and iterate over
        messages received.
        """

        await self.connect(loop=loop)

        while self.connected:
            
            async for line in self.reader:
                await self.handle(line)

            # disconnect inside the loop allows the client to reconnect without returning
            await self.disconnect()


    async def send(self, lines):
        """
        Prepares and writes messages to the connected server.

        args:
            lines: An iterable of string or bytes objects representing the messages to write. Strings will be
                   passed to `self.prepare` before being written to the transport stream.

        returns:
            None

        raises:
            RuntimeError: Will be raised if the transport stream is closed.
        """

        if not self.writer:
            raise RuntimeError('connection is not ready')
        
        for line in lines:
            
            if isinstance(line, str):
                line = await self.prepare(line)
                
            self.writer.write(line)