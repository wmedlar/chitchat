# Chitchat: IRC for Bots that Get Stuff Done
Writing an IRC bot has never been easier!
``` Python
import chitchat as cc

bot = cc.Bot('your.favorite.server', port=6667)

@bot.on('CONNECTED')
def bootup(*args):
    yield cc.identify(nick='Chitchat', user='v1a', password='chitchatrocks!')
    yield cc.join('#chitchatdev', '#mycoolchannel')

@bot.on(text='!hello')
def hello(prefix, command, target, message):
    return cc.privmsg(target, 'Hello, ' + prefix.nick + '!')

if __name__ == '__main__':
    bot.run()
```

"Hmph! Every IRC library does this!", you might say, you ol' grump. But where Chitchat outshines its competitors isn't only in simple "hello, world" scripts, but in complicated, high-functioning bots that Get Stuff Done.

## Features
- Asynchronous Commands: so your long-running housekeeping tasks won't disrupt your bot's service!
- Simple, Pythonic API: with Chitchat everything is right where you expect it!
- Vast Extensability: there's nothing your Chitchat bot can't do!

Check out the docs for more information. If you're in need of some inspiration, take a look at our collection of real-world examples!

## Todo
- [ ] Test coverage and more documentation
- [ ] Numerics support for all large IRC networks; currently only supporting Freenode on top of RFC-defined numerics
- [ ] Logging support
- [ ] CTCP and IRCv3 support
- [ ] Public API cleanup
- [ ] Line-splitting support for long (>512 char) messages with textwrap
- [ ] event scheduler decorator using asyncio.BaseEventLoop.call_at and call_later
- [ ] Client.wait_for to intercept server replies
- [ ] Plugin support completely separated from Client instances
- [ ] Release!
