import asyncio

from . import constants, utils

# TODO: move Connection.run to Client

class Connection:
    
    
    def __init__(self, *, encoding='UTF-8', loop=None):
        self.encoding = encoding
        self.loop = loop or asyncio.get_event_loop()
        
        self.connected = False
        self.reader = None
        self.writer = None
        
    
    async def connect(self, host, port, **kwargs):
        """Open a connection to the host."""
        
        self.reader, self.writer = await asyncio.open_connection(host, port,
                                                                 loop=self.loop, **kwargs)
        
        self.connected = True
        host_ip, host_port = self.writer.get_extra_info('peername')
        
        # pseudocommand signifying a successful connection
        line = utils.ircjoin(':' + host_ip, constants.CONNECTED, host_port).encode(self.encoding)
        
        # feed the pseudocommand to the StreamReader
        self.reader.feed_data(line)


    async def disconnect(self):
        """Disconnect from server."""

        self.connected = False
        host_ip, host_port = self.writer.get_extra_info('peername')

        # pseudocommand signifying a closed or lost connection from the server
        line = utils.ircjoin(':' + host_ip, constants.DISCONNECTED, host_port).encode(self.encoding)
        
        # iteration over the reader has stopped, so we'll send this one to self.handle
        await self.handle(line)
    

    async def handle(self, line):
        """
        Message handler called by `self.run`. This method exists to be overridden in
        subclasses and does nothing by default.
        """

        pass


    async def run(self):
        """
        The main method of the Connection class, run within an event loop to connect to an
        IRC server and iterate over messages received.
        """

        await self.connect()

        while self.connected:
            
            async for line in self.reader:
                
                await self.handle(line)

            # disconnect inside the loop allows the client to reconnect without returning
            await self.disconnect()


    def send(self, lines):
        """
        Prepares and writes messages to the connected server.

        args:
            lines: An iterable of string or bytes objects representing the messages to
            write.

        returns:
            None

        raises:
            RuntimeError: Will be raised if the transport stream is closed.
        """

        if not self.writer:
            raise RuntimeError('connection is not ready')
        
        self.writer.write(lines)