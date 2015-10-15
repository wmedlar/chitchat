import re
import typing

# from irc.isupport import *
# from irc.replies import *


class UnsupportedFormat(TypeError):
    '''
    Raised while parsing IRC string if improper format.
    '''
    pass


class lazyattribute:
    '''
    A lazily-evaluated property-like attribute decorator.

    Meant solely for use with data that should only be computed once, as the lazyattribute instance will replace itself
    with the return value of the decorated function.

    Attributes:
        fget: The getter function called to evaluate the property.
        attr: The attribute that this instance is bound to and the name of the getter function.
    '''

    def __init__(self, fget):
        '''
        Initializes the property instance.

        Args:
            fget: The getter function called to evaluate the property.
        '''
        self.fget = fget
        self.attr = fget.__name__


    def __get__(self, instance, owner):

        # instance is None if the property is accessed through the class rather than the instance
        if instance is None:
            # return instance of lazyproperty to mimic the behavior of property
            return self

        # instance is passed to fget as the `self` argument
        value = self.fget(instance)

        # instance attribute is set to value, replacing this instance of lazyproperty
        setattr(instance, self.attr, value)

        return value


def parse(message: str, pattern: typing.re.Pattern[str]):
    '''
    Parses the first appearance of `pattern` in `message` and returns it as a string.

    Args:
        message: A string message to match against `pattern`.
        pattern: A compiled regular expression for matching message.

    Returns:
        A string representing the first appearance of `pattern` in `message`, or None if `pattern` is not found in
        `message`.
    '''

    match = pattern.search(message)

    if match:
        # group(0) is the whole string
        # group(1) is the first captured group
        return match.group(1)

    else:
        return None


NICK = re.compile(r'^:([^@!\s]*)')
USER = re.compile(r'^:[^!\s]*!([^@\s]*)')
HOST = re.compile(r'^:[^@\s]*@([^\s]*)')
COMMAND = re.compile(r'^(?::[^\s]*\s)?([^\s]*)')
PARAMS = re.compile(r'^(?::[^\s]*\s)?(?:[^\s]*)\s(.*)\r\n$')


class Message:
    '''
    Container for an IRC message with lazily-evaluated attributes.

    Attributes:
        raw: A string containing the read-only, unparsed message. This attribute is a property with only a getter.

        prefix: A string containing the prefix of the message sender, of the form 'nick[!user[@host]]', or None if the
                sender's prefix cannot be parsed. This attribute is evaluated lazily and will reference self.nick,
                self.user, and self.host, resulting in their evaluation as well.

        nick: A string containing the nickname of the message sender, or None if the sender's nickname cannot be parsed.
              This attribute is evaluated lazily.

        user: A string containing the user id or identity of the message sender, or None if the sender's identity cannot
              be parsed. This attribute is evaluated lazily.

        host: A string containing the host name and domain of the message sender, or None if the sender's host cannot be
              parsed. This attribute is evaluated lazily.

        command: A string containing the command name or three-digit numeric representing the type of message received,
                 or None if the command cannot be parsed. This attribute is evaluated lazily.

        params: A tuple of strings containing the command parameters, or an empty tuple if parameters cannot be parsed.
                This attribute is evaluated lazily.
    '''

    def __init__(self, message):
        self._raw = message

    @property
    def raw(self):
        '''Read-only unparsed message.'''
        return self._raw

    # @property
    # def sender(self):
    #     '''Alias for self.nick.'''
    #     return self.nick

    @lazyattribute
    def prefix(self):

        # nick will always appear if a prefix is given
        # the absence of a nick indicates the absence of a prefix
        if not self.nick:
            return None

        prefix = '{nick}'

        # both user and host are optional
        if self.user:
            prefix += '!{user}'

        if self.host:
            prefix += '@{host}'

        return prefix.format(nick=self.nick, user=self.user, host=self.host)

    @lazyattribute
    def nick(self):

        return parse(self.raw, pattern=NICK)

    @lazyattribute
    def user(self):

        return parse(self.raw, pattern=USER)

    @lazyattribute
    def host(self):

        return parse(self.raw, pattern=HOST)

    @lazyattribute
    def command(self) -> str:

        return parse(self.raw, pattern=COMMAND)

    @lazyattribute
    def params(self) -> tuple:

        params = parse(self.raw, pattern=PARAMS)

        if not params:
            return ()

        # match colon preceded by either start of line or at least one space
        leading, sep, trailing = re_partition(r'(?:\A| +)(:)', params)

        # sep is only truthy if partition was successful and separator was captured
        # otherwise all params are stored in leading
        return (*leading.split(), trailing) if sep else tuple(leading.split())

    def __repr__(self):
        return 'Message(raw={0.raw!r})'.format(self)


def re_partition(pattern: str, string: str, flags=0) -> typing.Tuple[str, str, str]:
    '''
    Split `string` at the first occurrence of `pattern`.

    Args:
        pattern: A string regular expression pattern containing the separator in a capturing group.
        string: The string to partition.
        flags: A combination of any of the flags found in the re module, combined using the bitwise OR (the | operator).

    Returns:
        A 3-tuple containing the part before the separator, the separator itself, and the part after the separator.
        If the separator is not found, return a 3-tuple containing the string itself, followed by two empty strings.
        If the separator is not enclosed in a capturing group, return a 3-tuple containing the part before the
        separator, an empty string, and the part after the separator.

    Raises:
        re.error: Raised on an invalid regular expression.
        ValueError: re.split does not currently split a string on an empty pattern match and will raise a
                    ValueError if it is attempted since Python 3.5.
    '''

    split = re.split(pattern, string, maxsplit=1, flags=flags)

    length = len(split)

    # pattern not matched
    if length == 1:
        split.extend([''] * 2)

    # pattern matched but no capturing group included
    elif length == 2:
        split.insert(1, '')

    # returns a tuple rather than list to mimic the behaviour of str.partition
    return tuple(split)


def supported(message: str, default_factory=list) -> dict:
    '''
    Parses an RPL_ISUPPORT (005) message and returns a dict of supported features.

    Args:
        message: A string representing an RPL_ISUPPORT message from an IRC server.
        default_factory: A callable to transform parameters of unsupported (i.e., not in ISUPPORT) features.
                         The default `default_factory` is `list`.

    Returns:
        A dict of varying types in the format feature: params.

        * Features that do not support params will have a value of None.
        * Features that should have only one value (e.g., NICKLEN=30) will be an integer if numeric otherwise a string.
        * Features that contain a mapping, usually specified by a comma-separated list of key:value pairs
          (e.g., TARGMAX=ACCEPT:,KICK:1,PRIVMSG:4) will retain this mapping as a dict. Discluded values
          (ACCEPT in our examples) are assumed to be falsy and thus given the value 0.
          This also applies to PREFIX, which contains a mapping of user modes to their associated symbols.
        * Features that contain a comma-separated list of items will be returned as a list separated at the commas.
        * Features that do not trigger any of the previous conditions will have `default_factory` called on them.
          The default `default_factory` is `list`.
    '''

    features = {}

    params = parse(message).params

    # message takes the form <target> [ token=value ]* :are supported by this server
    # trims off the target and message parameters
    _, *tokens, _ = params

    for token in tokens:
        feature, sep, params = token.partition('=')

        func = ISUPPORT.get(feature)

        if not params:
            d = {feature: None}

        elif func:
            d = {feature: func(params)}

        else:
            d = {feature: default_factory(params)}

        features.update(d)

    return features


if __name__ == '__main__':
    lines = [
        ':irc.x2x.cc 439 * :Please wait while we process your connection.\r\n',
        ':irc.x2x.cc 001 Sakubot :Welcome to the Rizon Internet Relay Chat Network Sakubot\r\n',
        ':irc.x2x.cc 005 Sakubot CALLERID CASEMAPPING=rfc1459 DEAF=D KICKLEN=160 MODES=4 NICKLEN=30 TOPICLEN=390 PREFIX=(qaohv)~&@%+ STATUSMSG=~&@%+ NETWORK=Rizon MAXLIST=beI:250 TARGMAX=ACCEPT:,KICK:1,LIST:1,NAMES:1,NOTICE:4,PRIVMSG:4,WHOIS:1 CHANTYPES=# :are supported by this server\r\n',
        ':irc.x2x.cc 005 Sakubot CHANLIMIT=#:75 CHANNELLEN=50 CHANMODES=beI,k,l,BCMNORScimnpstz NAMESX UHNAMES AWAYLEN=160 FNC KNOCK ELIST=CMNTU SAFELIST EXCEPTS=e INVEX=I :are supported by this server\r\n',
        ':irc.x2x.cc 376 Sakubot :End of /MOTD command.\r\n',
        ':Sakubot!~skbt@Rizon-70FB98F4.dhcp.ftwo.tx.charter.com MODE Sakubot :+ix\r\n',
        ':NickServ!service@rizon.net NOTICE Sakubot :please choose a different nick.\r\n',
        ':NickServ!service@rizon.net NOTICE Sakubot :Password incorrect.\r\n',
        ':py-ctcp!ctcp@ctcp-scanner.rizon.net PRIVMSG Sakubot :VERSION\r\n',
        ':peer!service@rizon.net NOTICE Sakubot :For network safety, your client is being scanned for open proxies by scanner.rizon.net (80.65.51.220). This scan will not harm your computer.\r\n'
    ]

    from timeit import Timer

    # t = Timer('oldparse(":peer!service@rizon.net NOTICE Sakubot :For network safety, your client is being '
    #           'scanned for open proxies by scanner.rizon.net (80.65.51.220). This scan will not harm your computer.")',
    #           'from __main__ import oldparse')
    # print(t.timeit(), 'us per iteration')

    t = Timer('m = Message(":peer!service@rizon.net NOTICE Sakubot :For network safety, your client is being '
              'scanned for open proxies by scanner.rizon.net (80.65.51.220). This scan will not harm your computer.")'
              '; m.command, m.params',
              'from __main__ import Message')

    print(t.timeit(), 'us per iteration')