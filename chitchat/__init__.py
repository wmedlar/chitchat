import asyncio
import collections

from chitchat.connection import Connection
from chitchat import irc
from chitchat.mixins import CommandMixin


class Client(Connection, CommandMixin):
    '''

    '''
    actions = collections.defaultdict(set)


    async def run(self):

        await self.connect()

        while self.connected:

            async for line in self.reader:

                message = irc.parse(line.decode())
                await self.trigger(message)

            # disconnect in the loop allows the client to reconnect without returning
            await self.disconnect()


    def on(self, command, *commands, async=False):

        commands = command, *commands

        def wrapper(func):

            if not asyncio.iscoroutine(func):
                func = asyncio.coroutine(func)

            func.async = async

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

    @client.on('PRIVMSG')
    def test(message):
        if message.nick == 'necromanteion' and message.params[1] == 'sync':
            for i in range(3):
                client.msg('#Sakubot', message='sync! {}'.format(i))
                yield from asyncio.sleep(1)

    @client.on('PRIVMSG', async=True)
    def test2(message):
        if message.nick == 'necromanteion' and message.params[1] == 'async':
            for i in range(10):
                print('async! {}'.format(i))
                yield from asyncio.sleep(0.5)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()