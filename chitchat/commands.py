import asyncio
import itertools

from chitchat import constants, utils

# RFC-defined commands in order of definition in RFC 2812


def pass_(password):
    
    return utils.format(constants.PASS, password)


def nick(nickname):
    
    return utils.format(constants.NICK, nickname)


def user(user, realname, mode=0, unused='*'):
    
    return utils.format(constants.USER, user, mode, unused, realname, spaced=True)


def oper(name, password):
    
    return utils.format(constants.OPER, name, password)


def service(nickname, info, distribution='*', type=0, reserved='*'):
    
    return utils.format(constants.SERVICE, nickname, reserved, distribution,
                        type, reserved, info, spaced=True)


def quit(message=None):
    
    if message is None:
        return utils.format(constants.QUIT)
    
    return utils.format(constants.QUIT, message, spaced=True)


def squit(server, message):
    
    return utils.format(constants.SQUIT, server, message, spaced=True)


def join(channel, *channels, keys=None):
    channels = channel, *channels
    
    if keys is None:
        channels = ','.join(channels)        
        return utils.format(constants.JOIN, channels)
    
    channels, keys = zip(*itertools.zip_longest(channels, keys, fillvalue=''))
    
    channels = ','.join(channels)
    keys = ','.join(keys)
    
    return utils.format(constants.JOIN, channels, keys)


def part(channel, *channels, message=None):
    
    channels = channel, *channels
    channels = ','.join(channels)
    
    if message is None:
        return utils.format(constants.PART, channels)
    
    return utils.format(constants.PART, channels, message, spaced=True)


def mode(target, mode, *params):
    
    return utils.format(constants.MODE, target, mode, *params)


def topic(channel, topic=None):
    
    if topic is None:
        return utils.format(constants.TOPIC, channel)
    
    return utils.format(constants.TOPIC, channel, topic, spaced=True)


def names(channel, *channels, target=None):
    
    channels = channel, *channels
    channels = ','.join(channels)
    
    if target is None:
        return utils.format(constants.NAMES, channels)
    
    return utils.format(constants.NAMES, channels, target)


def list(channel, *channels, target=None):
    
    channels = channel, *channels
    channels = ','.join(channels)
    
    if target is None:
        return utils.format(constants.LIST, channels)
    
    return utils.format(constants.LIST, channels, target)


def invite(nickname, channel):
    
    return utils.format(constants.INVITE, nickname, channel)


def kick(channel, nickname, *nicknames, message=None):
    
    nicknames = nickname, *nicknames
    nicknames = ','.join(nicknames)
    
    if message is None:
        return utils.format(constants.KICK, channel, nicknames)
    
    return utils.format(constants.KICK, channel, nicknames, message, spaced=True)


def privmsg(target, message):
    
    return utils.format(constants.PRIVMSG, target, message, spaced=True)


# name shortened for convenience
msg = privmsg


def notice(target, message):
    
    return utils.format(constants.NOTICE, target, message, spaced=True)


def motd(target=None):
    
    if target is None:
        return utils.format(constants.MOTD)
    
    return utils.format(constants.MOTD, target)


def lusers(mask='', target=None):
    
    if target is None:
        return utils.format(constants.LUSERS, mask)
    
    return utils.format(constants.LUSERS, mask, target)


def version(target=None):
    
    if target is None:
        return utils.format(constants.VERSION)
    
    return utils.format(constants.VERSION, target)


def stats(query='', target=None):
    
    if target is None:
        return utils.format(constants.STATS, query)
    
    return utils.format(constants.STATS, query, target)


def links(mask='', target=None):
    
    if target is None:
        return utils.format(constants.LINKS, mask)
    
    return utils.format(constants.LINKS, mask, target)


def time(target=None):
    
    if target is None:
        return utils.format(constants.TIME)
    
    return utils.format(constants.TIME, target)


def connect(target, port, remote=None):
    
    if remote is None:
        return utils.format(constants.CONNECT, target, port)
    
    return utils.format(constants.CONNECT, target, port, remote)


def trace(target=None):
    
    if target is None:
        return utils.format(constants.TRACE)
    
    return utils.format(constants.TRACE, target)


def admin(target=None):
    
    if target is None:
        return utils.format(constants.ADMIN)
    
    return utils.format(constants.ADMIN, target)


def info(target=None):
    
    if target is None:
        return utils.format(constants.INFO)
    
    return utils.format(constants.INFO, target)


def servlist(mask='', type=None):
    
    if type is None:
        return utils.format(constants.SERVLIST, mask)
    
    return utils.format(constants.SERVLIST, mask, type)


def squery(target, message):
    
    return utils.format(constants.SQUERY, target, message, spaced=True)


def who(mask='', op_only=False):
    
    if op_only:
        return utils.format(constants.WHO, mask, 'o')
    
    return utils.format(constants.WHO, mask)


def whois(mask, *masks, target=None):
    masks = mask, *masks
    masks = ','.join(masks)
    
    if target is None:
        return utils.format(constants.WHOIS, masks)
    
    return utils.format(constants.WHOIS, target, masks)


def whowas(nickname, *nicknames, count=None, target=None):
    nicknames = nickname, *nicknames
    nicknames = ','.join(nicknames)
    
    args = [constants.WHOWAS, nicknames]
    
    if count is not None:
        args.append(count)
        
    if target is not None:
        args.append(target)
        
    return utils.format(*args)


def kill(nickname, message):
    
    return utils.format(constants.KILL, nickname, message, spaced=True)


def ping(target):
    
    return utils.format(constants.PING, target, spaced=True)


def pong(target):
    
    return utils.format(constants.PONG, target, spaced=True)


def error(message):
    
    return utils.format(constants.ERROR, message, spaced=True)


def away(message=None):
    
    if message is None:
        return utils.format(constants.AWAY)
    
    return utils.format(constants.AWAY, message, spaced=True)


def rehash():
    
    return utils.format(constants.REHASH)


def die():
    
    return utils.format(constants.DIE)


def restart():
    
    return utils.format(constants.RESTART)


def summon(user, target=None, channel=None):
    
    args = [constants.SUMMON, user]
    
    if target is not None:
        args.append(target)
        
    if channel is not None:
        args.append(channel)
        
    return utils.format(*args)


def users(target=None):
    
    if target is None:
        return utils.format(constants.USERS)
        
    return utils.format(constants.USERS, target)


def wallops(message):
    
    return utils.format(constants.WALLOPS, message, spaced=True)


def userhost(nickname, *nicknames):
    
    nicknames = nickname, *nicknames
    nicknames = ' '.join(nicknames)
    
    return utils.format(constants.USERHOST, nicknames)


def ison(nickname, *nicknames):
    
    nicknames = nickname, *nicknames
    nicknames = ' '.join(nicknames)
    
    return utils.format(constants.ISON, nicknames)


# Non-RFC-defined commands in alphabetical order


def cnotice(nickname, channel, message):
    
    return utils.format(constants.CNOTICE, nickname, channel, message, spaced=True)


def cprivmsg(nickname, channel, message):
    
    return utils.format(constants.CPRIVMSG, nickname, channel, message, spaced=True)


def help():
    
    return utils.format(constants.HELP)


def knock(channel, message=None):
    
    if message is None:
        return utils.format(constants.KNOCK, channel)
    
    return utils.format(constants.KNOCK, channel, message, spaced=True)


def namesx():
    
    return utils.format(constants.NAMESX)


def rules():
    
    return utils.format(constants.RULES)


def setname(realname):
    
    return utils.format(constants.SETNAME, realname, spaced=True)


def silence(nickname, *nicknames):
    # only adds nicknames to ignore list, see unsilence to remove
    nicknames = nickname, *nicknames
    formatted = ['+{}'.format(nick) for nick in nicknames]
    
    
    return utils.format(constants.SILENCE, *formatted)


def unsilence(nickname, *nicknames):
    # only removes nicknames to ignore list, see silence to add
    nicknames = nickname, *nicknames
    formatted = ['-{}'.format(nick) for nick in nicknames]
    
    
    return utils.format(constants.SILENCE, *formatted)


def uhnames():
    
    return utils.format(constants.UHNAMES)


def userip(nickname):
    
    return utils.format(constants.USERIP, nickname)


def watch(nickname, *nicknames):
    # only adds nicknames to watch list, see unwatch to remove
    nicknames = nickname, *nicknames
    formatted = ['+{}'.format(nick) for nick in nicknames]
    
    return utils.format(constants.WATCH, *formatted)


def unwatch(nickname, *nicknames):
    # only removes nicknames to watch list, see watch to add
    nicknames = nickname, *nicknames
    formatted = ['-{}'.format(nick) for nick in nicknames]
    
    return utils.format(constants.WATCH, *formatted)