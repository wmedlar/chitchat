import asyncio
import itertools
import re


from chitchat import cmd, irc, utils


class BotMixin:


    @asyncio.coroutine
    def triggered_by(self, message):
        '''A generator of actions triggered by `message`.'''

        actions = self.actions[message.command]

        for action in actions:

            if message.command == cmd.PRIVMSG:

                target, text = message.params

                # actions triggered by PRIVMSGs are not required to have `ignore` or `trigger` attributes,
                # such as functions decorated by the `on` decorator
                try:

                    # skip to next action if message does not contain action's trigger
                    if not action.trigger.search(text):
                        continue

                    # skip to next action if message was sent by someone matching action's ignore pattern
                    if action.ignore.match(message.prefix):
                        continue

                # action has no attribute `trigger` or `ignore`, or either of those is None
                except AttributeError:
                    pass

            yield action


    def command(self, trigger, *, async=False, ignore=None):
        '''
        A function decorator to register a listener called when a PRIVMSG with text matching `trigger` is received,
        with additional support for nonblocking calls and an ignore list.

        The decorated function should take only one parameter, an irc.Message object containing lazily-parsed
        parameters in its attributes.

        This decorator uses a function attribute to qualify passed args and kwargs, thus the `async`, `ignore`,
        and `trigger` attributes of the function must be available to the decorator for use.

        Args:
            trigger: A string or compiled regex pattern representing the command used to trigger the decorated function
                     (e.g., "!weather"). If a string is passed it is escaped and converted to a compiled regex pattern.
                     A string is assumed to be case insensitive. Internally re.search is used instead of re.match to
                     match the pattern anywhere in the message passed.

            async: A boolean used to specify that this function is to be run as nonblocking. This is a keyword-only
                   argument.

            ignore: A sequence of string prefix masks (e.g., nick!*@*) to prevent from triggering the decorated
                    function. This is a keyword-only argument.

        Returns:
            The decorated function wrapped in asyncio.coroutine.
        '''

        # if it quacks like a compiled regex...
        if not hasattr(trigger, 'search'):

            # ensure conversion to string and proper escaping of special characters
            pattern = re.escape('{}'.format(trigger))

            # assume case-insensitive, this is mentioned in the docstring
            trigger = re.compile(pattern, flags=re.IGNORECASE)

        def wrapper(func):
            '''
            Wraps the decorated function in a coroutine and appends it to self.actions.

            Args:
                func: The function to be decorated.

            Returns:
                The decorated function wrapped in asycio.coroutine.
            '''

            # function must be a coroutine to be yielded from
            if not asyncio.iscoroutine(func):
                func = asyncio.coroutine(func)

            # this line looked strange without a comment
            func.trigger = trigger

            # async attribute is used in self.trigger to determine a blocking or nonblocking call
            func.async = async

            # ignore attribute is a compiled regex of nickmasks to ignore
            func.ignore = utils.create_nickmask(ignore) if ignore else None

            # add function to set of PRIVMSG handlers
            self.actions[cmd.PRIVMSG].add(func)

            return func

        return wrapper


    @asyncio.coroutine
    def mimic(self, target: str, message: str, nick=None, user=None, host=None):
        '''
        Mimic a received PRIVMSG.

        This function attempts to construct a valid PRIVMSG string from the parameters given and pass it to
        self.trigger as if it were organically received. Typical usage is for testing or rerouting of commands.

        Args:
            target: A string representing the target of the mimicked message; can either be a channel or a nickname.
            message: A string representing the mimicked message.
            nick: A string representing the mimicked nickname of the sender. This argument is optional.
            user: A string representing the mimicked user id or identity of the sender. This argument is optional.
            host: A string representing the mimicked host name of the sender. This argument is optional.

        Yields:
            Yields from self.trigger.
        '''

        # colon signifies presence of prefix, must not be present in a message with no supplied prefix
        prefix = ':' if any([nick, user, host]) else ''
        line = 'PRIVMSG {target} :{message}\r\n'

        if nick is not None:
            prefix += '{nick}'

        if user is not None:
            prefix += '!{user}'

        if host is not None:
            prefix += '@{host}'

        if prefix:
            prefix += ' '

        line = prefix.format(nick=nick, user=user, host=host) + line.format(target=target, message=message)

        yield from self.trigger(irc.Message(line))


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
            A UTF-8 encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'PASS {password}\n'.format(password=password)
        line = utils.bytify(line, self.encoding)
        
        return self.send(line)


    def nick(self, nickname):
        '''
        Formats and sends a NICK message to an IRC server.

        The NICK command is used to give a user a nickname or change the existing one.

        Args:
            nickname: A string representing the desired nickname.

        Returns:
            A UTF-8 encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'NICK {nickname}\n'.format(nickname=nickname)
        line = utils.bytify(line)

        return self.send(line)


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
            A UTF-8 encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'USER {user} {mode} * :{realname}\n'.format(user=user,
                                                           mode=mode,
                                                           realname=realname)
        line = utils.bytify(line)

        return self.send(line)


    def oper(self, name, password):
        '''
        Formats and sends an OPER message to an IRC server.

        The OPER command is used to obtain server operator privileges. Upon success the user will receive a MODE
        message indicating the new user modes.

        Args:
            name: A string representing the username to register as an operator.
            password: A string representing the password to register as an operator.

        Returns:
            A UTF-8 encoded bytes object representing the formatted line sent to the server.
        '''

        line = 'OPER {name} {password}\n'.format(name=name,
                                                 password=password)
        line = utils.bytify(line)

        return self.send(line)


    def service(self, nickname, info, distribution='*', type=0):
        line = 'SERVICE {nickname} * {distribution} {type} 0 :{info}\n'.format(nickname=nickname,
                                                                               info=info,
                                                                               distribution=distribution,
                                                                               type=type)
        line = utils.bytify(line)
        
        return self.send(line)
    
    
    def quit(self, message=None):
        line = 'QUIT\n' if message is None else 'QUIT :{message}\n'.format(message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def squit(self, server, message):
        line = 'SQUIT {server} :{message}\n'.format(server=server,
                                                    message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def join(self, channel, *channels, keys=None):
        channels = channel, *channels
        channels, keys = zip(*itertools.zip_longest(channels, keys or (), fillvalue=''))
        line = 'JOIN {channels} {keys}\n'.format(channels=','.join(channels),
                                                 keys=','.join(keys))
        line = utils.bytify(line)
        
        return self.send(line)


    def part(self, channel, *channels, message=None):
        channels = channel, *channels
        line = 'PART {channels}\n' if message is None else 'PART {channels} :{message}\n'
        line = line.format(channels=','.join(channels),
                           message=message or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def mode(self, target, mode, *params):
        line = 'MODE {target} {mode} {params}\n'.format(target=target,
                                                        mode=mode,
                                                        params=' '.join(params))
        line = utils.bytify(line)
        
        return self.send(line)


    def topic(self, channel, topic=None):
        line = 'TOPIC {channel}\n' if topic is None else 'TOPIC {channel} :{topic}\n'
        line = line.format(channel=channel, topic=topic)
        line = utils.bytify(line)
        
        return self.send(line)


    def names(self, channel, *channels, target=None):
        channels = channel, *channels
        line = 'NAMES {channels} {target}\n'.format(channels=','.join(channels),
                                                    target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def list(self, channel, *channels, target=None):
        channels = channel, *channels
        line = 'LIST {channels} {target}\n'.format(channels=','.join(channels),
                                                   target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def invite(self, nickname, channel):
        line = 'INVITE {nickname} {channel}\n'.format(nickname=nickname,
                                                      channel=channel)
        line = utils.bytify(line)
        
        return self.send(line)


    def kick(self, channel, nickname, *nicknames, message=None):
        nicknames = nickname, *nicknames
        line = 'KICK {channel} {nicknames}\n' if message is None else 'KICK {channel} {nicknames} :{message}\n'
        line = line.format(channel=channel, nicknames=','.join(nicknames), message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def privmsg(self, target, message):
        line = 'PRIVMSG {target} :{message}\n'.format(target=target,
                                                      message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    # name shortened for convenience
    msg = privmsg


    def notice(self, target, message):
        line = 'NOTICE {target} :{message}\n'.format(target=target,
                                                     message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def motd(self, target=None):
        line = 'MOTD {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def lusers(self, mask=None, target=None):

        if (mask is None) and (target is not None):
            raise TypeError('mask must be supplied if target is not None')

        line = 'LUSERS {mask} {target}\n'.format(mask=mask or '',
                                                 target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def version(self, target=None):
        line = 'VERSION {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def stats(self, query=None, target=None):

        if (query is None) and (target is not None):
            raise TypeError('query must be supplied if target is not None')

        line = 'STATS {query} {target}\n'.format(query=query or '',
                                                 target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def links(self, mask=None, target=None):

        if (mask is None) and (target is not None):
            raise TypeError('mask must be supplied if target is not None')

        line = 'LINKS {target} {mask}\n'.format(mask=mask or '',
                                                target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def time(self, target=None):
        line = 'TIME {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def connect_(self, target, port, remote=None):
        line = 'CONNECT {target} {port} {remote}\n'.format(target=target,
                                                           port=port,
                                                           remote=remote or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def trace(self, target=None):
        line = 'TRACE {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def admin(self, target=None):
        line = 'ADMIN {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def info(self, target=None):
        line = 'INFO {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def servlist(self, mask=None, type=None):

        if (mask is None) and (type is not None):
            raise TypeError('mask must be supplied if type is not None')

        line = 'SERVLIST {mask} {type}\n'.format(mask=mask or '',
                                                 type=type or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def squery(self, target, message):
        line = 'SQUERY {target} :{message}\n'.format(target=target,
                                                     message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def who(self, mask=None, oper_only=False):
        line = 'WHO {mask} {o}\n'.format(mask=mask or '',
                                         o='o' if oper_only else '')
        line = utils.bytify(line)
        
        return self.send(line)


    def whois(self, mask, *masks, target=None):
        masks = mask, *masks
        line = 'WHOIS {target} {masks}\n'.format(masks=','.join(masks),
                                                 target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def whowas(self, nickname, *nicknames, count=None, target=None):
        nicknames = nickname, *nicknames
        line = 'WHOWAS {nicknames} {count} {target}\n'.format(nicknames=','.join(nicknames),
                                                              count=count or '',
                                                              target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def kill(self, nickname, message):
        line = 'KILL {nickname} :{message}\n'.format(nickname=nickname,
                                                     message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def ping(self, target):
        line = 'PING :{target}\n'.format(target=target)
        line = utils.bytify(line)
        
        return self.send(line)


    def pong(self, target):
        line = 'PONG :{target}\n'.format(target=target)
        line = utils.bytify(line)
        
        return self.send(line)


    def error(self, message):
        line = 'ERROR :{message}\n'.format(message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def away(self, message=None):
        line = 'AWAY\n' if message is None else 'AWAY :{message}\n'.format(message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def rehash(self):
        line = 'REHASH\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def die(self):
        line = 'DIE\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def restart(self):
        line = 'RESTART\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def summon(self, user, target=None, channel=None):

        if (target is None) and (channel is not None):
            raise TypeError('target must be supplied if channel is not None')

        line = 'SUMMON {user} {target} {channel}\n'.format(user=user,
                                                           target=target or '',
                                                           channel=channel or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def users(self, target=None):
        line = 'USERS {target}\n'.format(target=target or '')
        line = utils.bytify(line)
        
        return self.send(line)


    def wallops(self, message):
        line = 'WALLOPS :{message}\n'.format(message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def userhost(self, nickname, *nicknames):
        nicknames = nickname, *nicknames
        line = 'USERHOST {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        
        return self.send(line)


    def ison(self, nickname, *nicknames):
        nicknames = nickname, *nicknames
        line = 'ISON {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        
        return self.send(line)


    # Non-RFC-defined commands in alphabetical order


    def cnotice(self, nickname, channel, message):
        line = 'CNOTICE {nickname} {channel} :{message}\n'.format(nickname=nickname,
                                                                  channel=channel,
                                                                  message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def cprivmsg(self, nickname, channel, message):
        line = 'CPRIVMSG {nickname} {channel} :{message}\n'.format(nickname=nickname,
                                                                   channel=channel,
                                                                   message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def help(self):
        line = 'HELP\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def knock(self, channel, message=None):
        line = 'KNOCK {channel}\n' if message is None else 'KNOCK {channel} :{message}\n'
        line.format(channel=channel, message=message)
        line = utils.bytify(line)
        
        return self.send(line)


    def namesx(self):
        line = 'PROTOCTL NAMESX\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def rules(self):
        line = 'RULES\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def setname(self, realname):
        line = 'SETNAME :{realname}\n'.format(realname=realname)
        line = utils.bytify(line)
        
        return self.send(line)


    def silence(self, nickname, *nicknames):
        # only adds nicknames to ignore list, see unsilence to remove
        nicknames = nickname, *nicknames
        nicknames = map('+{}'.format, nicknames)
        line = 'SILENCE {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        
        return self.send(line)


    def unsilence(self, nickname, *nicknames):
        # only removes nicknames to ignore list, see silence to add
        nicknames = nickname, *nicknames
        nicknames = map('-{}'.format, nicknames)
        line = 'SILENCE {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        
        return self.send(line)


    def uhnames(self):
        line = 'PROTOCTL UHNAMES\n'
        line = utils.bytify(line)
        
        return self.send(line)


    def userip(self, nickname):
        line = 'USERIP {nickname}\n'.format(nickname=nickname)
        line = utils.bytify(line)
        
        return self.send(line)


    def watch(self, nickname, *nicknames):
        # only adds nicknames to watch list, see unwatch to remove
        nicknames = nickname, *nicknames
        nicknames = map('+{}'.format, nicknames)
        line = 'WATCH {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        
        return self.send(line)


    def unwatch(self, nickname, *nicknames):
        # only removes nicknames to watch list, see watch to add
        nicknames = nickname, *nicknames
        nicknames = map('-{}'.format, nicknames)
        line = 'WATCH {nicknames}\n'.format(nicknames=' '.join(nicknames))
        line = utils.bytify(line)
        
        return self.send(line)


    # Convenience methods


    def ban(self, nickname, *nicknames):
        nicknames = nickname, *nicknames