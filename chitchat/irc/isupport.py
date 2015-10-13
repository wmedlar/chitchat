import operator

__all__ = ('add_support', 'ISUPPORT')

def split_at_colon(values):

    d = {}

    for value in values.split(','):
        command, n = value.split(':')

        d.update({command: int(n) if n else 0})

    return d

def split_at_colon_iter(values):

    d = {}

    for value in values.split(','):
        prefixes, n = value.split(':')

        n = int(n) if n else 0

        for prefix in prefixes:
            d.update({prefix: n})

    return d


def prefix(values):
    # (modes)prefixes, 1:1 mapping

    modes, prefixes = values.split(')')

    return dict(zip(modes[1:], prefixes))


ISUPPORT = {
    'CASEMAPPING': str,
    'CHANLIMIT': split_at_colon_iter,
    'CHANMODES': operator.methodcaller('split', ','),
    'CHANNELLEN': int,
    'CHANTYPES': list,
    'EXCEPTS': str,
    # 'IDCHAN': ?
    'INVEX': str,
    'KICKLEN': int,
    'MAXLIST': split_at_colon_iter,
    'MODES': int,
    'NETWORK': str,
    'NICKLEN': int,
    'PREFIX': prefix,
    'SAFELIST': None,
    'STATUSMSG': list,
    'STD': str,
    'TARGMAX': split_at_colon,
    'TOPICLEN': int
}


def add_support(parameter=None, **kwargs):

    ISUPPORT.update(other=parameter, **kwargs)

    return ISUPPORT


if __name__ == '__main__':
    s = '#+:10,&:'
    print(chanlimit(s))

    s = ',,,'
    print(parameters.get('CHANMODES')(s))