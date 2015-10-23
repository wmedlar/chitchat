import abc
import asyncio
import collections


from chitchat import irc, utils


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
    def send(self, message):
        pass


    @abc.abstractmethod
    async def run(self):
        pass


    @asyncio.coroutine
    @abc.abstractmethod
    def triggered_by(self, message):
        pass


    @asyncio.coroutine
    @abc.abstractmethod
    def trigger(self, message):
        pass


class BaseClient(AbstractClient):


    def __init__(self, host, port, *, ssl=True):
        self._host = host
        self._port = port
        self._ssl = ssl
        self._connected = False

        self.reader = None
        self.writer = None

        self.actions = collections.defaultdict(set)

        # plugins is a set of module objects imported using the `BaseClient.load_plugins` method
        self.plugins = set()


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


    def send(self, message):

        if not self.writer:
            raise RuntimeError('connection is not ready')

        # StreamWriter buffers and writes message asynchronously and returns None
        self.writer.write(message)

        return message


    async def run(self) -> None:
        '''
        The main method of the Client class, run within an event loop to connect to an IRC server and iterate over
        messages received.
        '''

        await self.connect()

        while self.connected:

            # async for loop will yield a line as it is received
            async for line in self.reader:
                # irc.Message object allows lazily-evaluated attribute access
                # offers a speedup in some cases compared to eager evaluation of parameters
                message = irc.Message(line.decode())

                # async triggered actions will return immediately
                # sync triggered actions will block until completion
                await self.trigger(message)

            # disconnect in the loop allows the client to reconnect without returning
            await self.disconnect()


    def on(self, command: str, *commands, async=False):
        '''
        A function decorator to register a listener called when a message of type `command` is received, with optional
        blocking and nonblocking calls.

        The decorated function should take only one parameter, an irc.Message object containing lazily-parsed
        parameters in its attributes.

        This decorator uses a function attribute to qualify a blocking or nonblocking call, thus the `async` attribute
        of the function must be available to the decorator for use.

        Args:
            command: The string IRC command or three-digit numeric that will trigger the decorated function. At least
                     one command is required.
            *commands: Additional commands or numerics used to trigger the decorated function.
            async: Boolean keyword-only argument used to specify that this function is to be run as nonblocking.

        Returns:
            The decorated function wrapped in asyncio.coroutine.
        '''

        commands = command, *commands

        def wrapper(func):
            '''
            Wraps the decorated function in a coroutine and appends it to self.actions for each command passed.

            Args:
                func: The function to be decorated.

            Returns:
                The decorated function wrapped in asycio.coroutine.
            '''

            # function must be a coroutine to be yielded from
            if not asyncio.iscoroutine(func):
                func = asyncio.coroutine(func)

            # async attribute is used in self.trigger to determine a blocking or nonblocking call
            func.async = async

            # allows multiple commands to trigger the function
            for command in commands:
                # upper() ensures that triggers will not be missed from case-insensitivity
                self.actions[command.upper()].add(func)

            return func

        return wrapper


    @asyncio.coroutine
    def triggered_by(self, message):
        '''This method is equivalent to `yield from self.actions[message.command]` and exists to be overridden.'''

        actions = self.actions[message.command]

        yield from actions


    @asyncio.coroutine
    def trigger(self, message):

        actions = self.triggered_by(message)

        for action in actions:

            if action.async:
                # asyncio.ensure_future schedules the tasks for execution
                # tasks are then asynchronously executed in arbitrary order
                asyncio.ensure_future(action(message))

            else:
                # synchronous calls will block execution of asynchronous calls
                yield from action(message)


    def load_plugins(self, path):
        '''
        Locally imports all modules found in `path`.

        This is a convenience method that is nearly equivalent to `from path import *`, however modules are loaded
        into the namespace of the client instance.

        Plugins are Python modules of helper code used to extend your client while keeping your project modular. For
        instance a plugin directory may contain a file `pong.py` that includes a decorated (with the `on` decorator)
        function to reply to every PING with a PONG.

        Modules are executed when loaded, thus you should only use this method with a directory containing modules you
        trust.

        Args:
            path: The string path to a directory containing Python modules to import.

        Returns:
            A tuple containing the modules imported.
        '''
        plugins = tuple(utils.load_plugins(path))

        self.plugins.update(plugins)

        return plugins



if __name__ == '__main__':
    client = BaseClient(host='irc.rizon.net', port=6667, ssl=False)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())