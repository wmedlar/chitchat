import collections

from . import constants, exceptions


def ircjoin(*args, spaced=None):
    """
    Joins a command with its arguments into a valid IRC message.
    
    args:
        command: A string representing the command of the message.
        args: Variable number of positional args, formatted in the order they were passed.
        spaced: Keyword-only argument specifying a parameter that allows spaces.
        
    returns:
        A string representing the formatted message.
    """
    
    # waiting for f-strings
    format_list = ['{}'] * len(args)
    
    if spaced:
        format_list.append(':{}')
    
    line = ' '.join(format_list)
    
    return line.format(*args, spaced) + constants.CRLF


Message = collections.namedtuple('Message', ['prefix', 'command', 'params'])


def ircparse(message):
    """
    Parse an IRC message into its component prefix, command, and parameters, according to
    the general structure `:prefix command params\r\n`.
    
    Prefix and command are returned as strings; params is returned as a tuple. Delimiters
    are not part of the result, and each component may be empty.
    
    This function does not determine whether a message is valid -- that is whether it
    contains all the appropriate components in the proper order -- rather it simply
    separates an arbitrary string into likely components, similar to
    `urllib.parse.urlparse`.
    
    args:
        message: A string representing the IRC message to parse.
        
    returns:
        A namedtuple containing `prefix`, `command`, and `params` read-only attributes.
    """
    message = message.rstrip('\r\n')
    
    try:
        # last arg is separated by ' :' and may contain spaces itself
        leading, spaced = message.rsplit(' :', maxsplit=1)
    
    except ValueError:
        leading, spaced = message, None
    
    try:
        # all remaining args are space-delimited
        first, *remaining = leading.split()
        
    except ValueError:
        # leading is empty or is all whitespace, so this message has no other args
        first, remaining = '', ()
    
    if first.startswith(':'):
        # leading colon signifies presence of (non-empty) prefix
        prefix = first[1:]
        # command must be second arg, or non-existent if remaining is empty
        command, *remaining = remaining or ('', )
    
    else:
        # no prefix means leading arg is command
        prefix, command = '', first
    
    # concatenate remaining args, if any, into tuple
    params = tuple(remaining) if spaced is None else (*remaining, spaced)
    
    return Message(prefix, command, params)


Prefix = collections.namedtuple('Prefix', ['nick', 'user', 'host'])


def prefixsplit(prefix):
    """
    Parses an IRC prefix into its component nick, user, and host.
    
    args:
        prefix: A string representing the IRC prefix to parse.
    
    returns:
        A namedtuple containing the parsed nick, user, and host as strings.
    """
    
    if not prefix:
        return Prefix(nick='', user='', host='')
    
    try:
        nick, prefix = prefix.split('!', maxsplit=1)
    
    except ValueError:
        nick = ''
        
    try:
        user, host = prefix.split('@', maxsplit=1)
    
    except ValueError:
        # probably from the host server
        user = ''
        host = prefix if not nick else ''
        
    return Prefix(nick, user, host)


def ischannel(chanstring, prefixes=None):
    """
    Attempts to verify the validity of a channel string according to grammar defined
    in IRC spec.
    
    Per RFC 2812 (Section 1.3) channel names are strings prefixed with '&', '#', '+',
    or '!' of length up to fifty characters. Channel names may not contain spaces,
    control G characters (\\x07), or commas.
    
    args:
        chanstring: str to verify
        prefixes: iterable of valid str channel prefixes, defaults to ('&', '#', '+', '!')
        
    returns:
        bool describing whether `chanstring` is likely a channel
    """
    
    # str.startswith only accepts strings or tuples of strings, no lists
    prefixes = tuple(prefixes) if prefixes else ('&', '#', '+', '!')
    max_len = 50
    restricted = {' ', '\x07', ','}
    
    return (chanstring.startswith(prefixes) and
            len(chanstring) <= max_len and
            not restricted.intersection(chanstring))


def isplugin(object):
    """Returns True if the object is a `Plugin`."""
    return isinstance(object, Plugin)


def find_plugins(object=None):
    """Find all `Plugin` instances in `object`.
    
    If `object` is `None`, find all `Plugin` instances in the current module (i.e.,
    __main__). If `object` itself is a `Plugin` instance, it will be yielded first,
    before checking its members.
    
    This function will only discover `Plugin` instances in the top-level namespace of
    `object`.
    
    args:
        object: object to search that may be a `Plugin` instance, or may contain
                members that are `Plugin` instances
    
    yields:
        `Plugin` instances found in `object`.
    """
    if object is None:
        object = sys.modules['__main__']
    
    elif isplugin(object):
        yield object
        # don't return early as `object` may have plugins as members
        # unlikely, but we'll check anyway on the off chance
    
    for name, value in inspect.getmembers(object, isplugin):
        yield value


class lazyproperty:
    """
    Code modified from:
    http://stackoverflow.com/questions/3012421/python-lazy-property-decorator/6849299#6849299
    """
    
    def __init__(self, fget):
        self.fget = fget
        self.attr_name = fget.__name__
        
        
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        
        value = self.fget(instance)
        # replace the property with the returned value
        setattr(instance, self.attr_name, value)
        
        return value