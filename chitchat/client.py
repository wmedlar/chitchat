import abc
import asyncio
import collections
import itertools


from chitchat import utils


class AbstractClient(metaclass=abc.ABCMeta):
    

    @property
    @abc.abstractmethod
    def connected(self):
        pass


    @asyncio.coroutine
    @abc.abstractmethod
    def connect(self):
        pass


    @asyncio.coroutine
    @abc.abstractmethod
    def disconnect(self):
        pass


    @abc.abstractmethod
    async def run(self):
        pass


    @asyncio.coroutine
    @abc.abstractmethod
    def handle(self, line):
        pass


class BaseClient(AbstractClient):
    """
    Concrete implmenetation of AbstractClient.
    """


    def __init__(self, host, port, *, ssl=True):
        self._host = host
        self._port = port
        self._ssl = ssl
        self._connected = False

        self.reader = None
        self.writer = None


    @property
    def host(self):
        return self._host


    @host.setter
    def host(self, value):

        if self.connected:
            raise AttributeError("can't modify host while connected")

        self._host = value


    @property
    def port(self):
        return self._port


    @port.setter
    def port(self, value):

        if self.connected:
            raise AttributeError("can't modify port while connected")

        self._port = value


    @property
    def ssl(self):
        return self._ssl


    @ssl.setter
    def ssl(self, value):

        if self.connected:
            raise AttributeError("can't modify ssl while connected")

        self._ssl = value


    @property
    def connected(self):
        return self._connected


    @asyncio.coroutine
    def connect(self):
        '''Connect to `self.host` on `self.port`.'''

        if self.connected:
            raise RuntimeError('connection to {0.host!r} already opened on port {0.port!r}'.format(self))

        self.reader, self.writer = yield from asyncio.open_connection(self.host, self.port, ssl=self.ssl)
        self._connected = True

        yield from self.handle(b'CONNECTED\r\n')


    @asyncio.coroutine
    def disconnect(self):

        if not self.connected:
            return

        self.reader = None
        self.writer.close()
        self.writer = None

        self._connected = False

        yield from self.handle(b'DISCONNECTED\r\n')


    async def run(self):
        '''
        The main method of the BaseClient class, run within an event loop to connect to an IRC server and iterate over
        messages received.
        '''

        await self.connect()

        while self.connected:

            # async for loop will yield a line as it is received
            async for line in self.reader:
                await self.handle(line)

            # disconnect in the loop allows the client to reconnect without returning
            await self.disconnect()


    @asyncio.coroutine
    def handle(self, line):
        '''
        Message handler called by `BaseClient.run`. This method exists to be overridden in subclasses
        and does nothing by default.
        '''

        pass


    def send(self, line):
        '''
        Writes message to the transport stream asynchronously. This method is not a coroutine and
        should not be yielded from.

        args:
            line: A bytes object representing the encoded string to write.

        returns:
            None

        raises:
            RuntimeError: Will be raised if the transport stream (self.writer) is falsey.
        '''

        if not self.writer:
            raise RuntimeError('connection is not ready')

        self.writer.write(line)


if __name__ == '__main__':
    import random
    import os
    from chitchat import num, cmd, commands as cc

    client = BotClient(host='irc.rizon.net', port=6667, ssl=False)

    client.simple_parser(cmd.NOTICE, 'target', 'text')
    client.simple_parser(cmd.MODE, 'target', 'mode', 'params')
    client.simple_parser(cmd.PING, 'target')
    client.simple_parser(cmd.PRIVMSG, 'target', 'text')

    @client.on(cmd.PING)
    def pong(message):
        yield cc.pong(message.target)

    @client.on(cmd.NOTICE, text='*** Checking Ident')
    def identify(message):
        yield cc.nick('Sakubot')
        yield cc.user('v3', 'bot.made.of.socks')

    @client.on(cmd.NOTICE, text='please choose a different nick.')
    def auth(message):
        yield cc.privmsg('NickServ', 'identify ' + os.environ.get('RIZON_BOT'))

    @client.on(cmd.MODE, mode='+r')
    def join(message):
        yield cc.join('#sakubot')

    @client.command('.rem')
    def rem(message):
        
        roll = random.choice(['Sakuya', 'Haku', 'Meimei', 'Leilan', 'Karin'])
        
        yield cc.privmsg(message.target, 'You rolled a {}!'.format(roll))

    @client.command('.quit')
    def quit(message):
        yield from client.disconnect()
    

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
