import collections
import re

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


def re_partition(pattern, message):

    split = re.split(pattern, message, maxsplit=1)

    if len(split) < 3:
        split.extend([''] * 2)

    return split



def parse(message):

    match = pattern.match(message)

    if match:
        # match object in convenient dictionary form
        groups = match.groupdict()

        # text is not an argument of the Message constructor, must be removed
        params = groups.pop('text')

        leading, sep, trailing = re_partition('(?:\A| +)(:)', params)

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



def supported(message:str, default_factory=list):
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