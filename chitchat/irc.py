import operator
import re
import typing


from chitchat import utils


__all__ = ('Message', 'ISUPPORT', 'supported', 'add_support')


NICK = re.compile(r'^:([^@!\s]+)')
USER = re.compile(r'^:[^!\s]*!([^@\s]+)')
HOST = re.compile(r'^:[^@\s]*@([^\s]+)')
COMMAND = re.compile(r'^(?::[^\s]*\s)?([^\s]+)')
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


    @property
    def sender(self):
        '''Alias for self.nick.'''
        return self.nick


    @utils.lazyattribute
    def prefix(self):

        prefix = ''

        if self.nick:
            prefix = '{nick}'

        if self.user:
            prefix += '!{user}'

        if self.host:
            prefix += '@{host}'

        return prefix.format(nick=self.nick, user=self.user, host=self.host) if prefix else None


    @utils.lazyattribute
    def nick(self):

        return parse(self.raw, pattern=NICK)


    @utils.lazyattribute
    def user(self):

        return parse(self.raw, pattern=USER)


    @utils.lazyattribute
    def host(self):

        return parse(self.raw, pattern=HOST)


    @utils.lazyattribute
    def command(self) -> str:

        return parse(self.raw, pattern=COMMAND)


    @utils.lazyattribute
    def params(self) -> tuple:

        params = parse(self.raw, pattern=PARAMS)

        if not params:
            return ()

        # match colon preceded by either start of line or at least one space
        leading, sep, trailing = utils.re_partition(r'(?:\A| +)(:)', params)

        # sep is only truthy if partition was successful and separator was captured
        # otherwise all params are stored in leading
        return (*leading.split(), trailing) if sep else tuple(leading.split())


    def __repr__(self):
        return 'Message(raw={0.raw!r})'.format(self)


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
        # group(0) is the whole string, group(1) is the first captured group
        return match.group(1)

    else:
        return None


ISUPPORT = {
    'CASEMAPPING': str,
    'CHANLIMIT': utils.comma_delimited_many_to_one_mapping,
    'CHANMODES': operator.methodcaller('split', ','),
    'CHANNELLEN': int,
    'CHANTYPES': list,
    'EXCEPTS': str,
    # 'IDCHAN': ?
    'INVEX': str,
    'KICKLEN': int,
    'MAXLIST': utils.comma_delimited_many_to_one_mapping,
    'MODES': int,
    'NETWORK': str,
    'NICKLEN': int,
    'PREFIX': utils.parenthesis_separated_one_to_one_mapping,
    'SAFELIST': None,
    'STATUSMSG': list,
    'STD': str,
    'TARGMAX': utils.comma_delimited_one_to_one_mapping,
    'TOPICLEN': int
}


def supported(message: typing.Union[str, Message], default_factory=list) -> dict:
    '''
    Parses an RPL_ISUPPORT (005) message and returns a dict of supported features.

    Args:
        message: A string or Message object representing an RPL_ISUPPORT message from an IRC server.
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

    params = message.params if isinstance(message, Message) else Message(message).params

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


def add_support(other=None, **kwargs):
    '''
    Add support for a mapping of parameters: callables to the irc.ISUPPORT dict.

    This method is equivalent to irc.ISUPPORT.update.

    Args:
        other: A mapping of {parameter: callable} pairs. This is an optional argument.
        kwargs: This function mimics dict.update, thus arbitrary keyword arguments may be passed instead of a mapping.
                This is an optional argument.

    Returns:
        None, to closer mimic dict.update.
    '''

    ISUPPORT.update(other=other, **kwargs)

    return None