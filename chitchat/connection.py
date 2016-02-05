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
        self._connected_message()


    async def disconnect(self):
        """Disconnect from server."""

        self.connected = False
        self._disconnected_message()
    

    async def handle(self, line):
        """
        This method exists to be overridden in subclasses and does nothing by default.
        """

        # TODO: subclass asyncio.Protocol to send data to handle as it is received

        pass


    async def send(self, lines):
        """
        Buffers and writes messages to the connected server.

        args:
            lines: An iterable of string or bytes objects representing the messages to
            write.

        returns:
            None
        """
        
        self.writer.write(lines)
        
    
    def _connected_message(self):
        # networks will redirect connections to lower-load servers
        # this will get the actual host (ip, port) connected to
        host, port = self.writer.get_extra_info('peername')
        
        # :<HOST> CONNECTED <PORT>
        line = utils.ircjoin(':' + host, constants.CONNECTED, port).encode(self.encoding)
        
        # feed the pseudocommand to the StreamReader
        # allows it to be the first line read when async iterated over
        self.reader.feed_data(line)
        
    
    def _disconnected_message(self):
        # networks will redirect connections to lower-load servers
        # this will get the actual host (ip, port) that we had connected to
        # just in case we want to reconnect to that specific server
        host, port = self.writer.get_extra_info('peername')

        # :<HOST> DISCONNECTED <PORT>
        line = utils.ircjoin(':' + host, constants.DISCONNECTED, port).encode(self.encoding)
        
        # can't feed data to the reader after it has received eof (which signals disconnect)
        # send this one directly to the handle method
        asyncio.ensure_future(self.handle(line))
    
    