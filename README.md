# Chitchat: IRC for Robots
Description! Maybe even a logo!

## Writing an IRC bot has never been easier!
```
import asyncio
import chitchat as cc

bot = cc.Bot('your.favorite.server', port=6667)

@bot.on(cc.CONNECTED)
def bootup(message):
    yield cc.identify(nick='Chitchat', user='v1', password='chitchatrocks!')
    yield cc.join('#chitchatdev', '#mycoolchannel')
    
    
@bot.command('!hello', target='#mycoolchannel')
def hello(message):
    yield cc.msg('Hello, ' + message.nick + '!', target=message.target)
    
loop = asyncio.get_event_loop()
loop.run_until_complete(bot.run())
```
Pretty simple, right? Only a couple lines of code and you've already got yourself a bot that replies to a command. "But every IRC library does this", you might say. And you're right!

## Features
- Asynchronous Commands: so your long-running housekeeping tasks won't disrupt your bot's service!
- Simple, Pythonic API: with Chitchat everything is right where you expect it!
- Vast Extensability: there's nothing your Chitchat bot can't do!

## Todo
- Test coverage and more documentation
- Unify and simplify internal handling of CommandMixin methods
- Add numeric support for all large IRC networks, currently only supporting Freenode on top of RFC-defined numerics
- Deprecate Client class, I'm all about bots now
- Add logging support
- Come up with a logo
- CTCP and IRCv3 support
- Public API cleanup
- Add line-splitting support for long (>512 char) messages with textwrap
- Attempt to simplify module code with context managers and contextlib
