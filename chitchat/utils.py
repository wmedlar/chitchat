import pkgutil
import re
import typing


__all__ = ('lazyattribute', 'bytify', 're_partition')


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


# matches all spaces in groups of two or more, used in bytify method
TRIM_PATTERN = re.compile('( {2,})')


def bytify(message: str, encoding='UTF-8') -> bytes:
    '''
    Encodes an IRC-formatted message and trims excess whitespace in leading (i.e., before ':') params.

    Undesired whitespace may be leftover from formatting of optional arguments.

    Args:
        message: A string representing a, typically IRC-formatted, message to be trimmed and encoded.
        encoding: A string representing the encoding passed to the str.encode method.

    Returns:
        An `encoding` encoded bytes object representing the trimmed message.

    Raises:
        None. Any UnicodeError from str.encode will be suppressed with errors='ignore'.
    '''

    # excess spaces might be wanted in trailing param
    # so we'll leave it alone and only work on the leading params
    leading, sep, trailing = message.partition(':')

    # replace groups of two or more spaces with a single space and reform messages
    line = TRIM_PATTERN.sub(' ', leading) + sep + trailing

    return line.encode(encoding, errors='ignore')


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


# uses named groups to parse a nickmask
NICKMASK = re.compile(r'^(?P<nick>[^@!\s]+)?(?:!(?P<user>[^@!\s]+))?(?:@(?P<host>[^@!\s]+))?$')

# regex pattern equivalent of '*' for nickmasks
PREFIX_WILDCARD = '[^@!\s]+'


def create_nickmask(seq):
    '''Parses a sequence of string nickmasks into a compiled regex.'''

    if not seq:
        return None

    ignored = []

    for mask in seq:

        match = NICKMASK.match(mask)

        if not match:
            raise ValueError('{} is not a valid nickmask'.format(mask))

        nick, user, host = match.groups()

        mask = r'{nick}!{user}@{host}'.format(nick=nick or PREFIX_WILDCARD,
                                              user=user or PREFIX_WILDCARD,
                                              host=host or PREFIX_WILDCARD)

        # hosts often include periods, must be escaped
        mask = mask.replace('.', '\.').replace('*', PREFIX_WILDCARD)

        ignored.append(mask)

    return re.compile('|'.join(ignored))


def comma_delimited_one_to_one_mapping(parameters: str) -> dict:
    '''Parses a comma-delimited list of one-to-one mappings of the form "<str key>:<int value>,[...]".'''

    d = {}

    for value in parameters.split(','):
        command, n = value.split(':')

        d.update({command: int(n) if n else 0})

    return d


def comma_delimited_many_to_one_mapping(parameters: str) -> dict:
    '''Parses a comma-delimited list of many-to-one mappings of the form "<str keys>:<int value>,[...]".'''

    d = {}

    for value in parameters.split(','):
        command, n = value.split(':')

        n = int(n) if n else 0

        for prefix in command:
            d.update({prefix: n})

    return d


def parenthesis_separated_one_to_one_mapping(parameters: str) -> dict:
    '''Parses a string of one-to-one mappings of the form "(<str keys>)<str values>".'''

    # remove opening parenthesis then split at closing parenthesis
    keys, values = parameters.replace('(', '').split(')')

    return dict(zip(keys, values))