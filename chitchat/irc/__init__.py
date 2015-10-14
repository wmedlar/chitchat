import collections
import re
import typing

from irc.isupport import *
from irc.replies import *


class UnsupportedFormat(TypeError):
    '''
    Raised while parsing IRC string if improper format.
    '''
    pass


Message = collections.namedtuple('Message', ['raw', 'prefix', 'nick', 'user', 'host', 'command', 'params'])

pattern = re.compile('''
      ^(?P<raw>
          (:                                     # optional prefix begins with : and ends with space
             (?P<prefix>                         # nick[[!user]@host]
                 (?P<nick>[^@!\s]*)              # nick does not contain @, !, or space
                 (                               # user/host pair is optional
                     (!                          # user always begins with !
                         (?P<user>[^@]*)         # user does not contain @ or space
                     )?                          # optional if host is given
                     (@                          # host always begins with @
                         (?P<host>[^\s]*)        # host does not contain space
                     )
                 )?                              # user/host pair is optional
             )\s                                 # prefix ends with a space
          )?                                     # again prefix is optional
          (?P<command>                           # command (e.g., NICK, JOIN) is required
             (\w+|\d{3})                         # can be upper case letters or three digits
          )
          (\s                                    # optional params begin with a space
             (?P<text>(.*))                      # parameters encompass remainder of message
          )?                                     # optional
          \\r\\n                                 # all irc lines end with a carriage return (\\r) and a newline (\\n)
      )$
                     ''', flags=re.VERBOSE)


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

    if length == 1:
        # pattern not matched
        split.extend([''] * 2)

    elif length == 2:
        # pattern matched but no capturing group included
        split.insert(1, '')

    return tuple(split)



def parse(message):

    match = pattern.match(message)

    if match:
        # match object in convenient dictionary form
        groups = match.groupdict()

        # text is not an argument of the Message constructor, must be removed
        params = groups.pop('text', '')

        # match colon preceded by either start of line or at least one space
        leading, sep, trailing = re_partition(r'(?:\A| +)(:)', params)

        # sep is only truthy if partition was successful, otherwise all params are stored in leading
        groups['params'] = [*leading.split(), trailing] if sep else leading.split()

        return Message(**groups)

    else:
        return None


def command(message):
    match = pattern.match(message)

    if not match:
        raise UnsupportedFormat('{!r} not in a parsable format'.format(message))

    return match.group('command')



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
    string = 'Sakubot CHANLIMIT=#:75 CHANNELLEN=50 CHANMODES=beI,k,l,BCMNORScimnpstz ELIST=CMNTU SAFELIST AWAYLEN=160 KNOCK FNC NAMESX UHNAMES EXCEPTS=e INVEX=I :are supported by this server'
    # match, capture
    print(re_partition(r'(?:\A| +)(:)', string))
    # no match
    print(re_partition(r'(?:\A| +)(:NOMATCH)', string))
    # match, no capture
    print(re_partition(r'(?:\A| +):', string))