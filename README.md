# Chitchat: IRC for Bots that Get Stuff Done
Writing an IRC bot has never been easier!
``` Python
import asyncio
import chitchat as cc

<<<<<<< HEAD
## Writing an IRC bot has never been easier!
```
import asyncio
import chitchat as cc

=======
>>>>>>> 69ce64729cb4351d5a859f089cc8fd6c184f89af
bot = cc.Bot('your.favorite.server', port=6667)

@bot.on(cc.CONNECTED)
def bootup(message):
    yield cc.identify(nick='Chitchat', user='v1', password='chitchatrocks!')
    yield cc.join('#chitchatdev', '#mycoolchannel')
    
<<<<<<< HEAD
    
@bot.command('!hello', target='#mycoolchannel')
def hello(message):
    yield cc.msg('Hello, ' + message.nick + '!', target=message.target)
=======
@bot.command('!hello', target='#mycoolchannel')
def hello(message):
    yield cc.reply('Hello, ' + message.nick + '!')
>>>>>>> 69ce64729cb4351d5a859f089cc8fd6c184f89af
    
loop = asyncio.get_event_loop()
loop.run_until_complete(bot.run())
```
<<<<<<< HEAD
Pretty simple, right? Only a couple lines of code and you've already got yourself a bot that replies to a command. "But every IRC library does this", you might say. And you're right!

## Features
- Asynchronous Commands: so your long-running housekeeping tasks won't disrupt your bot's service!
- Simple, Pythonic API: with Chitchat everything is right where you expect it!
- Vast Extensability: there's nothing your Chitchat bot can't do!
=======
Pretty simple, right? Only a handful of lines of code and you've already got yourself a reactive bot!

"Hmph! Every IRC library does this!", you might say, you ol' grump. But where Chitchat outshines its competitors isn't only in simple "hello, world" scripts, but in complicated, high-functioning bots that Get Stuff Done.
``` Python
some neat code
```
Check out the docs for more information. If you're in need of some inspiration, take a look at our collection of real-world examples!
>>>>>>> 69ce64729cb4351d5a859f089cc8fd6c184f89af

## Todo
- Test coverage and more documentation
- Add numeric support for all large IRC networks; currently only supporting Freenode on top of RFC-defined numerics
- Add logging support
- CTCP and IRCv3 support
- Public API cleanup
- Add line-splitting support for long (>512 char) messages with textwrap
- Release!
