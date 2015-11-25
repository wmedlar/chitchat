import collections
import itertools





_containers = {}


def simple_parser(command, *params, name='Message'):
    '''
    Registers a simple message container to a command.
    '''

    _containers.update({command: collections.namedtuple(name, ('prefix', 'command') + params)})


def parser(command, *commands):
    '''
    Decorator for user-generated parsers.

    Parsers should take three arguments: a string prefix, a string command, and a list of parameters, and should
    return an object with at least a 'command' attribute set to the command to be triggered.
    '''

    commands = command, *commands

    def wrapper(func):

        for command in commands:
            _containers.update({command: func})

        return func

    return wrapper


def do_the_thing(message, default=Message, fill=''):
    '''
    Parses a message into a container object for command triggering.
    '''

    prefix, command, params = parse(message)

    Container = _containers.get(command, default)

    # Container is likely a namedtuple instance, either default or supplied from simple_parser
    if hasattr(Container, '_fields'):

        # the first two fields our prefix and command, included in every message
        # remaining are user-supplied fields for additional args
        fields = Container._fields

        # zip_longest ensures that all fields will receive a value; prevents errors in variable parameter messages
        p = [value for field, value in itertools.zip_longest(fields[2:], params, fillvalue=fill)]

        try:
            obj = Container(prefix, command, *p)

        # message contains more parameters than we can parse
        except TypeError:
            params = prefix, command, *params

            # matches fields to params, using None for any excess params
            # gives a more informational traceback
            matched = itertools.zip_longest(fields, params)

            raise TypeError('too many parameters to parse: {} -> {}'.format(message, tuple(matched)))

    # Container is supplied by the user; assume they're a smart cookie and know what they're doing
    else:
        obj = Container(prefix, command, params)

    return obj


if __name__ == '__main__':

    Privmsg = collections.namedtuple('Privmsg', ['nick', 'user', 'host', 'command', 'target', 'message'])

    @parser('PRIVMSG')
    def privmsg(prefix, command, params):

        nick, prefix = prefix.split('!')
        user, host = prefix.split('@')

        target, message = params

        return Privmsg(nick, user, host, command, target, message)

    print(do_the_thing(b':Sakubot!v3@bot.made.of.socks PRIVMSG #padg :message\r\n'))
    print(do_the_thing(b':irc.rizon.net NOTICE :this is a notice\r\n'))