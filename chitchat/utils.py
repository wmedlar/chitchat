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


# not cached as messages are unlikely to be repeated exactly
# thus caching would just be a waste of memory
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


# prefixes, on the other hand, are repeated often
# caching should speed up construction of structures.prefix objects
@functools.lru_cache()
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
        # probably from a server, convention is to set the prefix as host
        user = ''
        host = prefix if not nick else ''
        
    return nick, user, host


def ascallable(chan=None, host=None, nick=None, user=None, text=None):
    """
    Creates a callable of message requirements.
    """
    
    # message.target in chan
    # chan=[] to restrict to private messages only
    # host == message.host
    # nick == message.nick
    # user == message.user
    # text == message.text
    
    return None

def _compare(*args):
    
    pass
    


def load_plugins(path):
    """
    Load all modules found in `path`.

    Args:
        path: The path of the specified directory to load.

    Yields:
        The loaded module object.
    """

    for finder, name, is_package in pkgutil.walk_packages(path=[path]):
        # `finder` is used to find a `loader` which can then load the package into memory
        loader, _ = finder.find_loader(name)

        module = loader.load_module()

        yield module