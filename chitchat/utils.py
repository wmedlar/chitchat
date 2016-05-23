import collections
import functools
import itertools
import pkgutil
import re
import textwrap
import types


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


def ircsplit(message):
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


class lazyproperty:
    """
    Code modified from:
    http://stackoverflow.com/questions/3012421/python-lazy-property-decorator/6849299#6849299
    """
    
    def __init__(self, fget):
        self.fget = fget
        self.name = fget.__name__
        
        
    def __get__(self, instance, owner=None):
        if instance is None:
            return None
        
        value = self.fget(instance)
        # replace the descriptor with the returned value
        setattr(instance, self.name, value)
        
        return value


async def try_await(possible_coroutine):
    """
    Attempts to await result of `possible_coroutine`.
    
    If `possible_coroutine` is a coroutine, return its result, otherwise return
    `possible_coroutine`.
    """
    
    try:
        result = await possible_coroutine
        
    except TypeError:
        result = possible_coroutine
        
    return result

    
def as_comparable(arg):
    
    # allow user to define their own behavior
    if callable(arg):
        return arg
    
    # allow all, don't create callable
    elif arg is None or isinstance(arg, bool):
        return boolean(arg)
    
    # strings or bytes
    # bytes are decoded by Client implementation, but are included here for completeness
    elif isinstance(arg, (bytes, str)):
        return equality(arg, case_sensitive=False)
    
    # lists, tuples, generators
    elif isinstance(arg, collections.abc.Iterable):
        return containment(arg, case_sensitive=False)
    
    # try our best
    else:
        return equality(arg)
        

def boolean(a):
    """
    Creates a function that accepts one argument and returns the boolean value of `a`.
    
    >>> true = boolean(True)
    >>> true('abc')
    True
    >>> true(False)
    True
    
    args:
        a: value of any type to be interpreted as a boolean
        
    returns:
        function of one argument that returns the boolean value of `a`
    
    """
    
    bool_a = bool(a)
    
    def func(b):
        
        return bool_a
    
    doc = 'Always returns the boolean value of {0}'
    func.__doc__ = doc.format(a)
    
    return func
    
    
def equality(a, case_sensitive=True):
    """
    Creates a function that accepts one argument and returns whether that argument is
    equal to `a`.
    
    >>> 
    
    args:
        a: value of any type for comparison
        case_sensitive: bool; if False this will attempt to call str.casefold on both
                        `a` and the argument passed to the returned function before
                        equality comparison
    
    returns:
        function of one argument for comparison testing to `a`
        
    """
    
    try:
        lower_a = a.casefold()
    
    except AttributeError:
        lower_a = a

    def func(b):
        
        if not case_sensitive:
            
            try:
                return lower_a == b.casefold()
            
            except AttributeError:
                pass
            
        return a == b
    
    doc = 'Tests for case-{0}sensitive equality with {1!r}.'
    func.__doc__ = doc.format('' if case_sensitive else 'in', a)
    
    return func


def casefold_each(iterable):
    """
    Casefolds each item in `iterable`, skipping items that don't implement a `casefold`
    method.
    
    If `iterable` is a string, return a casefolded copy of that string, otherwise
    return a copy of `iterable` with each item casefolded.
    """

    if isinstance(iterable, str):
        return iterable.casefold()
    
    folded = []
    for item in iterable:
        
        try:
            i = item.casefold()
            
        except AttributeError:
            i = item
            
        folded.append(i)
        
    return folded