import abc
import asyncio
import collections
import itertools


from chitchat import utils


class AbstractClient(metaclass=abc.ABCMeta):


    @abc.abstractmethod
    def __init__(self, host, port, *, ssl=True):
        pass


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


    @abc.abstractmethod
    def send(self, line):
        pass


class BaseClient(AbstractClient):


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

        # yield from self.trigger('CONNECTED')


    @asyncio.coroutine
    def disconnect(self):

        if not self.connected:
            return

        self.reader = None
        self.writer.close()
        self.writer = None

        self._connected = False

        # yield from self.trigger('DISCONNECTED')


    async def run(self):
        '''
        The main method of the Client class, run within an event loop to connect to an IRC server and iterate over
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


class BotClient(BaseClient):


    def __init__(self, host, port, *, encoding='UTF-8', ssl=True):
        self.encoding = encoding

        self.actions = collections.defaultdict(set)
        self.parsers = {}
        self.plugins = set()

        super().__init__(host, port, ssl=ssl)


    @asyncio.coroutine
    def handle(self, line):
        decoded = line.decode(self.encoding).rstrip('\r\n')

        message = self.parse(decoded)

        yield from self.trigger(message)


    def parse(self, line):
        '''
        Parses an IRC-formatted line into a container object for further processing.

        args:
            line: A decoded string line representing the text to parse.

        returns:
            If the default or simple parser is used, this method will return a namedtuple instance with `prefix`,
            `command`, and `params` attributes. Users may expand the `params` attribute with a simple parser into
            several separate attributes.

            If the user supplies their own complex parser, using the BotClient.parser decorator, this method will
            return an arbitrary object that should implemented at least the `command` attribute.

        raises:
            TypeError: Will be raised if the parser is supplied with more arguments than its constructor can handle.
        '''

        prefix, command, params = utils.ircparse(line)

        Parser = self.parsers.get(command, utils.Message)

        if hasattr(Parser, '_fields') and Parser is not utils.Message:
            fields = Parser._fields
            params = prefix, command, *params

            matched = [value for field, value in itertools.zip_longest(fields, params)]

            try:
                message = Parser._make(matched)

            except TypeError:
                matched = list(itertools.zip_longest(fields, params))
                raise TypeError('too many parameters to parse: {} -> {}'.format(line, matched))

        else:
            message = Parser(prefix, command, params)

        return message


    @asyncio.coroutine
    def trigger(self, message):
        '''
        Passes a message to a set of actions triggered by its various parameters. This method is a coroutine.

        This method should not be called directly. If the user wants to mimic a received message
        consider the `mimic` method instead.

        args:
            message: An object representing the message used to trigger a pre-defined action. This can be any object,
                     usually a namedtuple instance, that implements a `command` attribute.

        yields:
            In the case that the triggered action is a blocking call, this method will yield its result. Otherwise this
            method will return immediately upon calling the triggered actions.
        '''

        actions = self.actions[message.command]

        for action in actions:

            if not action.meets_requirements(message):
                continue

            if action.async:
                asyncio.ensure_future(action.coro(message))

            else:
                yield from action.coro(message)


    def parser(self, command, *commands):
        '''
        Decorator for user-generated parsers.

        Parsers should take three arguments: a string prefix, a string command, and a list of parameters, and should
        return an object with at least a 'command' attribute set to the command to be triggered.
        '''

        commands = command, *commands

        def wrapper(func):

            for command in commands:
                self.parsers.update({command: func})

            return func

        return wrapper


    def simple_parser(self, command, *params, name='Message'):
        '''
        Registers a simple message container to a command.
        '''

        parser = collections.namedtuple(name, ('prefix', 'command') + params)

        self.parsers.update({command: parser})


    def on(self, command, *commands, async=True, **kwargs):
        '''
        Action decorator.

        args:
            command, commands: String commands (e.g., 'NOTICE') or numerics (e.g., '003') used to trigger the
                               decorated function. At least one command must be supplied.
            async: A boolean signifying whether this function should be run asynchronously (non-blocking). This is a
                   keyword-only argument that defaults to True.
            kwargs: Any number of additional keyword arguments used to specify the requirements under which the
                    decorated function should be called. For example, @BotClient.on('PRIVMSG', nick='chitchat') will
                    only be triggered by a PRIVMSG from a user with a nick of 'chitchat', provided that you have
                    defined a parser to populate the `nick` attribute of the message object received.

        returns:
            The decorated function.
        '''

        commands = command, *commands

        def wrapper(func):

            coro = func if asyncio.iscoroutine(func) else asyncio.coroutine(func)

            @asyncio.coroutine
            def wrapped(*args, **kwargs):

                for line in coro(*args, **kwargs):

                    self.send(line.encode())

            action = utils.Action(wrapped, async, utils.requirements(kwargs))

            for command in map(str.upper, commands):
                self.actions[command].add(action)

            return func

        return wrapper


    def command(self, trigger, *triggers, async=True, **kwargs):

        triggers = trigger, *triggers

        def func(text):
            first, *_ = text.split(maxsplit=1)

            return first in triggers

        # func = lambda text: text.split()[0] in triggers

        return self.on('PRIVMSG', async=async, text=func, **kwargs)



# def load_plugins(self, path):
#     '''
#     Locally imports all modules found in `path`.
#
#     This is a convenience method that is nearly equivalent to `from path import *`, however modules are loaded
#     into the namespace of the client instance.
#
#     Plugins are Python modules of helper code used to extend your client while keeping your project modular. For
#     instance a plugin directory may contain a file `pong.py` that includes a decorated (with the `on` decorator)
#     function to reply to every PING with a PONG.
#
#     Modules are executed when loaded, thus you should only use this method with a directory containing modules you
#     trust.
#
#     Args:
#         path: The string path to a directory containing Python modules to import.
#
#     Returns:
#         A tuple containing the modules imported.
#     '''
#     plugins = tuple(utils.load_plugins(path))
#
#     self.plugins.update(plugins)
#
#     return plugins


if __name__ == '__main__':
    from chitchat import num, cmd

    client = BotClient(host='irc.rizon.net', port=6667, ssl=False)

    client.simple_parser('NOTICE', 'target', 'text')
    client.simple_parser('MODE', 'target', 'mode', 'params')
    client.simple_parser('PING', 'target')
    client.simple_parser('PRIVMSG', 'target', 'text')

    @client.on(cmd.PING)
    def pong(message):
        yield 'PONG :' + message.target + '\r\n'

    @client.on(cmd.NOTICE, text='*** Checking Ident')
    def identify(message):
        yield 'NICK Sakubot\r\n'
        yield 'USER v3 0 * :bot.made.of.socks\r\n'

    @client.on(cmd.NOTICE, text='please choose a different nick.')
    def auth(message):
        yield 'PRIVMSG NickServ :IDENTIFY SEA#$hark\r\n'

    @client.on(cmd.MODE, mode='+r')
    def join(message):
        yield 'JOIN #sakubot\r\n'

    @client.command('.rem')
    def rem(message):
        yield 'PRIVMSG ' + message.target + ' :You rolled a Sakuya!\r\n'

    @client.command('.quit')
    def quit(message):
        yield from client.disconnect()

    @client.on(*num.ALL, *cmd.ALL)
    def log(message):
        print(message)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
