import collections
import itertools
import pkgutil
import re
import textwrap


Action = collections.namedtuple('Action', ['coro', 'async', 'meets_requirements'])
Message = collections.namedtuple('Message', ['prefix', 'command', 'params'])


def requirements(reqs):
    """
    Converts a dict of message requirements into a callable used to determine whether
    subsequent messages meet those requirements.
    """

    def meets_requirements(message):

        for key, value in reqs.items():

            attr = getattr(message, key)

            if callable(value) and value(attr):
                continue

            elif not callable(value) and value == attr:
                continue

            else:
                return False

        return True

    return meets_requirements


def ircparse(message):
    '''
    Parses an IRC message into its component prefix, command, and parameters.
    '''

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


def format(command, *args, spaced=False):
    '''
    Formats a bunch of args into a valid IRC message.
    
    args:
        command: A string representing the command of the message.
        args: Variable number of positional args, formatted in the order they were passed.
        spaced: Keyword-only boolean specifying whether the last parameter allows for spaces.
        
    returns:
        A string representing the formatted message.
    '''
    
    CRLF = '\r\n'
    
    # isolate last, possibly spaced arg
    *args, last = command, *args
    
    # colon delimiter represents an arg that allows spaces
    line = '{} ' * len(args) + (':{}' if spaced else '{}')
    
    return line.format(*args, last) + CRLF


def container(name, fields, *, cache={}):
    """
    Caches containers created by `Client.simple_parser` method.
    
    args:
        name: string
        fields: tuple
        
    returns:
        cached container or new container
    """
    
    # using cache as a mutable default arg allows it to persist
    container = cache.get((name, fields))
    
    if not container:
        container = collections.namedtuple(name, fields)
        cache.update({(name, fields): container})
        
    return container


def load_plugins(path):
    '''
    Load all modules found in `path`.

    Args:
        path: The path of the specified directory to load.

    Yields:
        The loaded module object.
    '''

    for finder, name, is_package in pkgutil.walk_packages(path=[path]):
        # `finder` is used to find a `loader` which can then load the package into memory
        loader, _ = finder.find_loader(name)

        module = loader.load_module()

        yield module