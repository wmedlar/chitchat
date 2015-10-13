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


    def on(self, command, *commands):

        commands = command, *commands

        def wrapper(func):

            func = asyncio.coroutine(func)

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

        if actions:
            tasks = [asyncio.ensure_future(action(message)) for action in actions]
            # waiting on tasks allows any action triggered to run in parallel
            yield from asyncio.wait(tasks)

        return


if __name__ == '__main__':
    import os

    client = Client(host='irc.rizon.net', port=6667, ssl=False)

    irc.add_support(AWAYLEN=int, DEAF=str)

    @client.on('NOTICE')
    def dostuff(message):
        if 'No Ident response' in message.raw:
            client.nick('Sakubot')
            client.user('skbt', realname='Sakubot')
            client.msg('NickServ', message='IDENTIFY {}'.format(os.environ.get('RIZON_PASSWORD')))

        elif 'Password accepted' in message.raw:
            client.join('#padg')

    @client.on('PING')
    def pong(message):
        client.pong(message.params[0])

    @client.on(*irc.ALL)
    def log(message):
        print(message.params)

    @client.on('KICK')
    def rejoin(message):
        channel, nick, reason = message.params

        if nick == 'Sakubot':
            client.join(channel)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()