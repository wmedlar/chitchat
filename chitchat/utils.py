import collections
import functools
import itertools
import pkgutil
import re
import textwrap


from . import constants


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


def ircsplit(message):
    """
    Parses an IRC message into its component prefix, command, and parameters.
    """

    if message.startswith(':'):
        prefix, message = message[1:].split(maxsplit=1)
        
    else:
        prefix = ''

    # ' :' signifies the final parameter, which may contain any character except NUL ('\0') or CRLF ('\r\n')
    # prior parameters may contain a colon if and only if it is not the first character
    message, *trailing = message.split(' :', maxsplit=1)

    # command is the first arg of message, remainder are concatenated with trailing into params
    command, *params = *message.split(), *trailing

    return prefix, command, params


def prefixsplit(prefix):
    """
    Parses an IRC prefix into its component nick, user, and host.
    
    args:
        prefix: A string representing the IRC prefix to parse.
    
    returns:
        A tuple containing the parsed nick, user, and host, in that order.
    """
    
    if not prefix:
        return '', '', ''
    
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
        
    return nick, user, host


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