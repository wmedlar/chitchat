import asyncio
import os
import chitchat as cc

sakubot = cc.SimpleBot(host='irc.rizon.net', port=6667, ssl=False)

sakubot.simple_parser('PRIVMSG', 'target', 'text')
sakubot.simple_parser('NOTICE', 'target', 'text')
sakubot.simple_parser('PING', 'target')

@sakubot.on('CONNECTED')
def login(message):
    yield cc.nick('Sakubot')
    yield cc.user('v3', 'bot.made.of.socks')
    
    with sakubot.intercept('NOTICE', text=lambda a: 'nickname is registered' in a) as fut:
        msg = yield from fut
        
    password = os.environ.get('RIZON_BOT')
    yield cc.privmsg('NickServ', 'identify %s' % password)
    
    with sakubot.intercept('NOTICE', text=lambda a: 'vhost' in a) as future:
        msg = yield from future
        
    yield cc.join('#sakubot')

        
@sakubot.on('PING')
def pong(message):
    yield cc.pong(message.target)
    

@sakubot.command('.rem')
def rem(message):
    
    yield cc.privmsg(message.target, 'Do you really wanna roll, onii-chan?')
    
    with sakubot.intercept('PRIVMSG', prefix=message.prefix, timeout=25) as future:
        try:
            msg = yield from future
        except Exception as e:
            print(e)
            msg = None
    
    if msg:
        yield cc.privmsg(msg.target, 'You rolled a Sakuya!')

    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    loop.run_until_complete(sakubot.run())
    loop.close()