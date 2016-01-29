import asyncio
import itertools

from chitchat import constants, utils

# RFC-defined commands in order of definition in RFC 2812


def pass_(password):
    """
    Builds a PASS command used to set a connection password. The optional password can and
    must be set before any attempt to register the connection is made (i.e., before
    sending a NICK/USER combination).
    
    args:
        password: A spaceless string representing the connection password.
        
    returns:
        An unencoded string representing the PASS command.
    """
    
    return utils.ircjoin(constants.PASS, password)


def nick(nickname):
    """
    Builds a NICK command used to give or change a user's nickname.
    
    args:
        nickname: A spaceless string representing the user's desired nickname.
        
    returns:
        An unencoded string representing the NICK command.
    """
    
    return utils.ircjoin(constants.NICK, nickname)


def user(username, realname=None, mode=0, unused='*'):
    """
    Builds a USER command used at the beginning of a connection to specify the username,
    mode, and real name of a new user.
    
    args:
        username: A spaceless string representing the user's username.
        realname: A string representing the user's real name. This optional parameter may
              contain spaces. If this parameter is None, it will be the same as the `user`
              parameter.
        mode: An integer, or string representing an integer, used to specify the user mode
              set when registering with the server. This optional parameter defaults to 0
              to signify no user mode.
        unused: This field is unused in the IRC specification and is included for
                completeness.
    
    returns:
        An unencoded string representing the USER command.
    """
    
    if realname is None:
        realname = username
    
    return utils.ircjoin(constants.USER, username, mode, unused, spaced=realname)


def oper(username, password):
    """
    Builds an OPER command used to obtain server operator privileges.
    
    args:
        username: A spaceless string representing the username to register with.
        password: A spaceless string representing the password to register with.
        
    returns:
        An unencoded string representing the OPER command.
    """
    
    return utils.ircjoin(constants.OPER, username, password)


def mode(target, *params):
    """
    Builds a MODE command used to modify user or channel modes.
    
    args:
        target: A spaceless string representing the nick or channel to modify.
        *params: Mode parameters.
    
    returns:
        An unencoded string representing the MODE command.
    """

    return utils.ircjoin(constants.MODE, target, *params)


def service(nickname, info, distribution='*', type=0, reserved='*'):
    """
    Builds a SERVICE command used to register a new service.
    
    args:
        nickname: A spaceless string representing the service's desired nickname.
        info: A string description of the service; may contain spaces.
        distribution: A spaceless string representing the server mask specifying the
                      visibility of the service.
        type: Currently unused and reserved for future use; included for completeness.
        reserved: Currently unused and reserved for future use; included for completness.
        
    returns:
        An unencoded string representing the SERVICE command.
    """
    
    return utils.ircjoin(constants.SERVICE, nickname, reserved, distribution, type, 0,
                         spaced=info)


def quit(message=None):
    """
    Builds a QUIT command used to terminate a client session.
    
    args:
        message: A string comment to leave upon quitting; may contain spaces.
        
    returns:
        An unencoded string representing the QUIT command.
    """
    
    return utils.ircjoin(constants.QUIT, spaced=message)


def squit(server, message):
    """
    Builds a SQUIT command used to disconnect server links. This command is only available
    to operators.
    
    args:
        server: A spaceless string representing the server to disconnect.
        message: A string reason for disconnecting the server; may contain spaces.
        
    returns:
        An unencoded string representing the SQUIT command.
    """
    
    return utils.ircjoin(constants.SQUIT, server, spaced=message)


# can't use **kwargs for channel=key pairings because channels begin with symbols
def join(*channels, keys=None):
    """
    Builds a JOIN command used to request joining a channel.
    
    args:
        *channels: Any number of string channels to join.
        keys: If supplied keys should be an iterable of channel keys that map to channels.
        
    returns:
        An unencoded string representing the JOIN command.
    """
    
    if keys is None:
        
        return utils.ircjoin(constants.JOIN, ','.join(channels))
    
    channels, keys = zip(*itertools.zip_longest(channels, keys, fillvalue=''))

    return utils.ircjoin(constants.JOIN, ','.join(channels), ','.join(keys))


def part(*channels, message=None):
    
    return utils.ircjoin(constants.PART, ','.join(channels), spaced=message)


def topic(channel, topic=None):
    
    return utils.ircjoin(constants.TOPIC, channel, spaced=topic)


def names(*channels, server=None):
    
    return utils.ircjoin(constants.NAMES, ','.join(channels), server)


def list(*channels, server=None):
    
    return utils.ircjoin(constants.LIST, ','.join(channels), server)


def invite(nickname, channel):
    
    return utils.ircjoin(constants.INVITE, nickname, channel)


def kick(channel, *nicknames, message=None):
    
    return utils.ircjoin(constants.KICK, channel, ','.join(nicknames), spaced=message)


def privmsg(target, message):
    
    return utils.ircjoin(constants.PRIVMSG, target, spaced=message)


# name shortened for convenience
msg = privmsg


def notice(target, message):
    
    return utils.ircjoin(constants.NOTICE, target, spaced=message)


def motd(server=None):
    
    if server is None:
        return utils.ircjoin(constants.MOTD)
    
    return utils.ircjoin(constants.MOTD, server)


def lusers(mask='', server=None):
    
    if server is None:
        return utils.ircjoin(constants.LUSERS, mask)
    
    return utils.ircjoin(constants.LUSERS, mask, server)


def version(server=None):
    
    if server is None:
        return utils.ircjoin(constants.VERSION)
    
    return utils.ircjoin(constants.VERSION, server)


def stats(query='', server=None):
    
    if server is None:
        return utils.ircjoin(constants.STATS, mask)
    
    return utils.ircjoin(constants.STATS, query, server)


def links(mask='', server=None):
    
    if server is None:
        return utils.ircjoin(constants.LINKS, mask)
    
    return utils.ircjoin(constants.LINKS, mask, server)


def time(server=None):
    
    if server is None:
        return utils.ircjoin(constants.TIME)
    
    return utils.ircjoin(constants.TIME, server)


def connect(server, port, remote=None):
    
    if remote is None:
        return utils.ircjoin(constants.CONNECT, server, port)
    
    return utils.ircjoin(constants.CONNECT, server, port, remote)


def trace(server=None):
    
    if server is None:
        return utils.ircjoin(constants.TRACE)
    
    return utils.ircjoin(constants.TRACE, server)


def admin(server=None):
    
    if server is None:
        return utils.ircjoin(constants.ADMIN)
    
    return utils.ircjoin(constants.ADMIN, server)


def info(server=None):
    
    if server is None:
        return utils.ircjoin(constants.INFO)
    
    return utils.ircjoin(constants.INFO, server)


def servlist(mask='', type=None):
    
    if type is None:
        return utils.ircjoin(constants.SERVLIST, mask)
    
    return utils.ircjoin(constants.SERVLIST, mask, type)


def squery(target, message):
    
    return utils.ircjoin(constants.SQUERY, target, spaced=message)


def who(mask='', ops_only=False):
    
    if ops_only:
        return utils.ircjoin(constants.WHO, mask, 'o')
    
    return utils.ircjoin(constants.WHO, mask)


def whois(*masks, server=None):

    masks = ','.join(masks)
    
    if server is None:
        return utils.ircjoin(constants.WHOIS, masks)
    
    return utils.ircjoin(constants.WHOIS, server, masks)


def whowas(*nicknames, count=None, server=None):

    nicknames = ','.join(nicknames)
    
    args = [constants.WHOWAS, nicknames]
    
    if count is not None:
        args.append(count)
        
    if server is not None:
        args.append(target)
        
    return utils.ircjoin(*args)


def kill(nickname, message):
    
    return utils.ircjoin(constants.KILL, nickname, spaced=message)


def ping(server):
    
    return utils.ircjoin(constants.PING, server)


def pong(server):
    
    return utils.ircjoin(constants.PONG, server)


def error(message):
    
    return utils.ircjoin(constants.ERROR, spaced=message)


def away(message=None):
    
    return utils.ircjoin(constants.AWAY, spaced=message)


def rehash():
    
    return utils.ircjoin(constants.REHASH)


def die():
    
    return utils.ircjoin(constants.DIE)


def restart():
    
    return utils.ircjoin(constants.RESTART)


def summon(user, server=None, channel=None):
    
    args = [constants.SUMMON, user]
    
    if server is not None:
        args.append(server)
        
    if channel is not None:
        args.append(channel)
        
    return utils.ircjoin(*args)


def users(server=None):
    
    if server is None:
        return utils.ircjoin(constants.USERS)
        
    return utils.ircjoin(constants.USERS, target)


def wallops(message):
    
    return utils.ircjoin(constants.WALLOPS, spaced=message)


def userhost(*nicknames):
    
    return utils.ircjoin(constants.USERHOST, ' '.join(nicknames))


def ison(*nicknames):
    
    return utils.ircjoin(constants.ISON, ' '.join(nicknames))


# Non-RFC-defined commands in alphabetical order


def cnotice(nickname, channel, message):
    
    return utils.ircjoin(constants.CNOTICE, nickname, channel, spaced=message)


def cprivmsg(nickname, channel, message):
    
    return utils.ircjoin(constants.CPRIVMSG, nickname, channel, spaced=message)


def help():
    
    return utils.ircjoin(constants.HELP)


def knock(channel, message=None):
    
    return utils.ircjoin(constants.KNOCK, channel, spaced=message)


def namesx():
    
    return utils.ircjoin(constants.NAMESX)


def rules():
    
    return utils.ircjoin(constants.RULES)


def setname(realname):
    
    return utils.ircjoin(constants.SETNAME, spaced=realname)


def silence(*nicknames):
    # only adds nicknames to ignore list, see unsilence to remove
    formatted = ['+{}'.format(nick) for nick in nicknames]
    
    return utils.ircjoin(constants.SILENCE, *formatted)


def unsilence(*nicknames):
    # only removes nicknames to ignore list, see silence to add
    formatted = ['-{}'.format(nick) for nick in nicknames]
    
    return utils.ircjoin(constants.SILENCE, *formatted)


def uhnames():
    
    return utils.ircjoin(constants.UHNAMES)


def userip(nickname):
    
    return utils.ircjoin(constants.USERIP, nickname)


def watch(*nicknames):
    # only adds nicknames to watch list, see unwatch to remove
    formatted = ['+{}'.format(nick) for nick in nicknames]
    
    return utils.ircjoin(constants.WATCH, *formatted)


def unwatch(*nicknames):
    # only removes nicknames to watch list, see watch to add
    formatted = ['-{}'.format(nick) for nick in nicknames]
    
    return utils.ircjoin(constants.WATCH, *formatted)


# convenience functions so users don't have to be intimate with IRC spec to run a bot

def identify(nickname, username, password=None):
    """
    Registers a user with the server. Convenience function that wraps `pass`, `nick`, and
    `user` in the correct order. This function returns one string containing three commands.
    """
    
    lines = '' if password is None else pass_(password), nick(nickname), user(username)

    return ''.join(lines)