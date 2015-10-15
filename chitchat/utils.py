import re

# matches all spaces in groups of two or more, used in bytify method
TRIM_PATTERN = re.compile('( {2,})')


def bytify(message, encoding='UTF-8'):
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