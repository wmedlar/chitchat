import operator


from chitchat import utils


# a mapping of IRC server-supported features to callables that parse their parameters
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


def supported(message, default_factory=list) -> dict:
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