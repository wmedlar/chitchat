import asyncio
import itertools


from chitchat import utils


# consider adding a `sender` attribute that points to self.send
# easier to override in subclasses

class CommandMixin:
    '''
    A mixin that contains methods to format and send RFC-defined IRC messages, including some commonly implemented
    albeit not officially defined commands and convenience methods for setting modes.

    CommandMixin should be used with a subclass of connection.Connection, or at least a class that implements a send
    method that accepts a bytes object as the only parameter.

    Methods in this class will both send, through self.send, and ultimately return the message sent.

    Attributes:
        encoding: The encoding string used to encode messages by methods of this class; defaults to 'UTF-8'. This
                  is a class attribute.
    '''

    encoding = 'UTF-8'


    # RFC-defined commands in order of definition in RFC 2812
    

    def pass_(self, password:str):
        '''
        Formats and sends a PASS message to an IRC server.

        The PASS command is used to set a 'connection password'. The optional password can and must be set before
        any attempt to register the connection is made. Currently RFC 2812 requires that users send a PASS command
        before sending the NICK/USER combination.

        Args:
            password: A string representing the server's connection password.

        Returns:
            A UTF8-encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'PASS {password}\n'.format(password=password)
        line = utils.bytify(line, self.encoding)
        self.send(line)

        return line


    def nick(self, nickname):
        '''
        Formats and sends a NICK message to an IRC server.

        The NICK command is used to give a user a nickname or change the existing one.

        Args:
            nickname: A string representing the desired nickname.

        Returns:
            A UTF8-encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'NICK {nickname}\n'.format(nickname=nickname)
        line = utils.bytify(line)
        self.send(line)

        return line


    def user(self, user, realname, mode=0):
        '''
        Formats and sends a USER message to an IRC server.

        The USER command is used at the beginning of a connection to specify the username and realname of a new user.

        Args:
            user: A string representing the desired username.
            realname: A string representing the desired realname. May contain space characters.
            mode: An integer or string representing the desired user mode to set when registering with the server.
                  This parameter is a bitmask, with only two bits having any signification: if the bit 2 is set the
                  user mode 'w' will be set; if the bit 3 is set the user mode 'i' will be set.

        Returns:
            A UTF8-encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'USER {user} {mode} * :{realname}\n'.format(user=user,
                                                           mode=mode,
                                                           realname=realname)
        line = utils.bytify(line)
        self.send(line)

        return line


    def oper(self, name, password):
        '''
        Formats and sends an OPER message to an IRC server.

        The OPER command is used to obtain server operator privileges. Upon success the user will receive a MODE
        message indicating the new user modes.

        Args:
            name: A string representing the username to register as an operator.
            password: A string representing the password to register as an operator.

        Returns:
            A UTF8-encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'OPER {name} {password}\n'.format(name=name,
                                                 password=password)
        line = utils.bytify(line)
        self.send(line)

        return line


    def service(self, nickname, info, distribution='*', type=0):
        line = 'SERVICE {nickname} * {distribution} {type} 0 :{info}\n'.format(nickname=nickname,
                                                                               info=info,
                                                                               distribution=distribution,
                                                                               type=type)
        line = utils.bytify(line)
        self.send(line)

        return line
    
    
    def quit(self, message=None):
        line = 'QUIT\n' if message is None else 'QUIT :{message}\n'.format(message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def squit(self, server, message):
        line = 'SQUIT {server} :{message}\n'.format(server=server,
                                                    message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def join(self, channel, *channels, keys=None):
        channels = channel, *channels
        channels, keys = zip(*itertools.zip_longest(channels, keys or (), fillvalue=''))
        line = 'JOIN {channels} {keys}\n'.format(channels=','.join(channels),
                                                 keys=','.join(keys))
        line = utils.bytify(line)
        self.send(line)

        return line


    def part(self, channel, *channels, message=None):
        channels = channel, *channels
        line = 'PART {channels}\n' if message is None else 'PART {channels} :{message}\n'
        line = line.format(channels=','.join(channels),
                           message=message or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def mode(self, target, mode, *params):
        line = 'MODE {target} {mode} {params}\n'.format(target=target,
                                                        mode=mode,
                                                        params=' '.join(params))
        line = utils.bytify(line)
        self.send(line)

        return line


    def topic(self, channel, topic=None):
        line = 'TOPIC {channel}\n' if topic is None else 'TOPIC {channel} :{topic}\n'
        line = line.format(channel=channel, topic=topic)
        line = utils.bytify(line)
        self.send(line)

        return line


    def names(self, channel, *channels, target=None):
        channels = channel, *channels
        line = 'NAMES {channels} {target}\n'.format(channels=','.join(channels),
                                                    target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def list(self, channel, *channels, target=None):
        channels = channel, *channels
        line = 'LIST {channels} {target}\n'.format(channels=','.join(channels),
                                                   target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def invite(self, nickname, channel):
        line = 'INVITE {nickname} {channel}\n'.format(nickname=nickname,
                                                      channel=channel)
        line = utils.bytify(line)
        self.send(line)

        return line


    def kick(self, channel, nickname, *nicknames, message=None):
        nicknames = nickname, *nicknames
        line = 'KICK {channel} {nicknames}\n' if message is None else 'KICK {channel} {nicknames} :{message}\n'
        line = line.format(channel=channel, nicknames=','.join(nicknames), message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def privmsg(self, target, message):
        line = 'PRIVMSG {target} :{message}\n'.format(target=target,
                                                      message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    # name shortened for convenience
    msg = privmsg


    def notice(self, target, message):
        line = 'NOTICE {target} :{message}\n'.format(target=target,
                                                     message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def motd(self, target=None):
        line = 'MOTD {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def lusers(self, mask=None, target=None):

        if (mask is None) and (target is not None):
            raise TypeError('mask must be supplied if target is not None')

        line = 'LUSERS {mask} {target}\n'.format(mask=mask or '',
                                                 target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def version(self, target=None):
        line = 'VERSION {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def stats(self, query=None, target=None):

        if (query is None) and (target is not None):
            raise TypeError('query must be supplied if target is not None')

        line = 'STATS {query} {target}\n'.format(query=query or '',
                                                 target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def links(self, mask=None, target=None):

        if (mask is None) and (target is not None):
            raise TypeError('mask must be supplied if target is not None')

        line = 'LINKS {target} {mask}\n'.format(mask=mask or '',
                                                target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def time(self, target=None):
        line = 'TIME {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def connect(self, target, port, remote=None):
        line = 'CONNECT {target} {port} {remote}\n'.format(target=target,
                                                           port=port,
                                                           remote=remote or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def trace(self, target=None):
        line = 'TRACE {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def admin(self, target=None):
        line = 'ADMIN {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def info(self, target=None):
        line = 'INFO {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def servlist(self, mask=None, type=None):

        if (mask is None) and (type is not None):
            raise TypeError('mask must be supplied if type is not None')

        line = 'SERVLIST {mask} {type}\n'.format(mask=mask or '',
                                                 type=type or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def squery(self, target, message):
        line = 'SQUERY {target} :{message}\n'.format(target=target,
                                                     message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def who(self, mask=None, oper_only=False):
        line = 'WHO {mask} {o}\n'.format(mask=mask or '',
                                         o='o' if oper_only else '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def whois(self, mask, *masks, target=None):
        masks = mask, *masks
        line = 'WHOIS {target} {masks}\n'.format(masks=','.join(masks),
                                                 target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def whowas(self, nickname, *nicknames, count=None, target=None):
        nicknames = nickname, *nicknames
        line = 'WHOWAS {nicknames} {count} {target}\n'.format(nicknames=','.join(nicknames),
                                                              count=count or '',
                                                              target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def kill(self, nickname, message):
        line = 'KILL {nickname} :{message}\n'.format(nickname=nickname,
                                                     message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def ping(self, target):
        line = 'PING :{target}\n'.format(target=target)
        line = utils.bytify(line)
        self.send(line)

        return line


    def pong(self, target):
        line = 'PONG :{target}\n'.format(target=target)
        line = utils.bytify(line)
        self.send(line)

        return line


    def error(self, message):
        line = 'ERROR :{message}\n'.format(message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def away(self, message=None):
        line = 'AWAY\n' if message is None else 'AWAY :{message}\n'.format(message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def rehash(self):
        line = 'REHASH\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def die(self):
        line = 'DIE\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def restart(self):
        line = 'RESTART\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def summon(self, user, target=None, channel=None):

        if (target is None) and (channel is not None):
            raise TypeError('target must be supplied if channel is not None')

        line = 'SUMMON {user} {target} {channel}\n'.format(user=user,
                                                           target=target or '',
                                                           channel=channel or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def users(self, target=None):
        line = 'USERS {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        self.send(line)

        return line


    def wallops(self, message):
        line = 'WALLOPS :{message}\n'.format(message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def userhost(self, nickname, *nicknames):
        nicknames = nickname, *nicknames
        line = 'USERHOST {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        self.send(line)

        return line


    def ison(self, nickname, *nicknames):
        nicknames = nickname, *nicknames
        line = 'ISON {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        self.send(line)

        return line


    # Non-RFC-defined commands in alphabetical order


    def cnotice(self, nickname, channel, message):
        line = 'CNOTICE {nickname} {channel} :{message}\n'.format(nickname=nickname,
                                                                  channel=channel,
                                                                  message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def cprivmsg(self, nickname, channel, message):
        line = 'CPRIVMSG {nickname} {channel} :{message}\n'.format(nickname=nickname,
                                                                   channel=channel,
                                                                   message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def help(self):
        line = 'HELP\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def knock(self, channel, message=None):
        line = 'KNOCK {channel}\n' if message is None else 'KNOCK {channel} :{message}\n'
        line.format(channel=channel, message=message)
        line = utils.bytify(line)
        self.send(line)

        return line


    def namesx(self):
        line = 'PROTOCTL NAMESX\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def rules(self):
        line = 'RULES\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def setname(self, realname):
        line = 'SETNAME :{realname}\n'.format(realname=realname)
        line = utils.bytify(line)
        self.send(line)

        return line


    def silence(self, *nicknames):
        # only adds nicknames to ignore list, see unsilence to remove
        nicknames = map('+{}'.format, nicknames)
        line = 'SILENCE {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        self.send(line)

        return line


    def unsilence(self, *nicknames):
        # only removes nicknames to ignore list, see silence to add
        nicknames = map('-{}'.format, nicknames)
        line = 'SILENCE {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        self.send(line)

        return line


    def uhnames(self):
        line = 'PROTOCTL UHNAMES\n'
        line = utils.bytify(line)
        self.send(line)

        return line


    def userip(self, nickname):
        line = 'USERIP {nickname}\n'.format(nickname=nickname)
        line = utils.bytify(line)
        self.send(line)

        return line


    def watch(self, *nicknames):
        # only adds nicknames to watch list, see unwatch to remove
        nicknames = map('+{}'.format, nicknames)
        line = 'WATCH {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        self.send(line)

        return line


    def unwatch(self, *nicknames):
        # only removes nicknames to watch list, see watch to add
        nicknames = map('-{}'.format, nicknames)
        line = 'WATCH {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        self.send(line)

        return line



class BotMixin:


    @asyncio.coroutine
    def mimic(self, target, message, nick=None, user=None, host=None):
        '''
        Mimic a received PRIVMSG.

        Typical use is for testing or calling renamed commands from inside deprecated functions.

        Args:

        Returns:

        Raises:
        '''

        yield from self.trigger()


if __name__ == '__main__':
    m = CommandMixin()
    m.send = lambda line: line
    print(m.sender)

    print(m.privmsg('#padg', 'test'))
    print(m.users())
    print(m.silence())