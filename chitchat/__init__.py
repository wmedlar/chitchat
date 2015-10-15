import asyncio
import collections
import typing

from chitchat.connection import Connection
from chitchat import irc
from chitchat.mixins import CommandMixin


class Client(Connection, CommandMixin):


    actions = collections.defaultdict(set)


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

        def wrapper(func: typing.Callable[[irc.Message], typing.Any]) -> typing.Callable[[irc.Message], typing.Any]:
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
                self.actions[command].add(func)

            return func

        return wrapper


    @asyncio.coroutine
    def trigger(self, message):

        actions = self.actions[message.command]
        synonym = irc.REPLIES.get(message.command)

        if synonym:
            actions |= self.actions[synonym]

        for action in actions:

            if action.async:
                # asyncio.ensure_future schedules the tasks for execution
                # tasks are then asynchronously executed in arbitrary order
                asyncio.ensure_future(action(message))

            else:
                # synchronous calls will block execution of asynchronous calls
                yield from action(message)


if __name__ == '__main__':
    import os

    client = Client(host='irc.rizon.net', port=6667, ssl=False)

    @client.on('NOTICE')
    def dostuff(message):
        if 'No Ident response' in message.raw:
            client.nick('Sakubot')
            client.user('skbt', realname='Sakubot')
            client.msg('NickServ', message='IDENTIFY {}'.format(os.environ.get('RIZON_PASSWORD')))

        elif 'Password accepted' in message.raw:
            client.join('#sakubot')

    @client.on('PING')
    def pong(message):
        client.pong(message.params[0])

    @client.on(*irc.ALL, async=True)
    def log(message):
        print(message.raw)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()