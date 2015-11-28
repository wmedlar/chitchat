import asyncio
import collections
import contextlib
import functools
import itertools

from chitchat import constants, utils
from chitchat.client import BaseClient


class SimpleBot(BaseClient):
    """
    
    attributes:
        actions: A defaultdict of sets which contain utils.Action instances to trigger
                 upon receiving a line of the corresponding key command. This attribute
                 is empty upon initialization and is filled by using the `on` and
                 `command` decorators.
                 
        encoding: A string representing the encoding to use in both sending to and
                  receiving messages from the server.
                 
        parsers: A one-to-one dict of message commands matched to callables that parse
                 message strings from the connected server. This attribute contains
                 default parsers upon intialization and can be overridden or added to
                 using the parser decorator or simple_parser method.
                 
        plugins: A set of imported modules containing additional features for the bot.
                 This attribute is empty by default.
    """
    

    def __init__(self, host, port, *, encoding='UTF-8', ssl=True):
        self.encoding = encoding

        self.actions = collections.defaultdict(set)
        self.parsers = {}
        self.plugins = set()

        super().__init__(host, port, ssl=ssl)


    @asyncio.coroutine
    def handle(self, line):
        """
        Method called by `run`, passing each message received. This is a coroutine.
        
        This implementation of `handle` will decode and parse (through the `parse` method)
        the received message, and pass it to the `trigger` method to be sent to
        corresponding actions.
        
        args:
            line: Bytes object containing the encoded message to be handled.
            
        yields:
            Yields from the `trigger` method.
        """
        decoded = line.decode(self.encoding).rstrip('\r\n')

        command, message = self.parse(decoded)
        
        print(message)

        yield from self.trigger(command, message)


    def parse(self, line):
        '''
        Parses an IRC-formatted line into a container object for further processing.

        args:
            line: A string line representing the text to parse.
        '''

        prefix, command, params = utils.ircparse(line)
        
        parser = self.parsers.get(command, utils.Message)
        
        return command, parser(prefix, command, params)


    @asyncio.coroutine
    def trigger(self, command, message=None):
        '''
        Passes a message to a set of actions triggered by its various parameters. This
        method is a coroutine.

        args:
            command: A string representing the command received.
            message: An object representing the message used to trigger a pre-defined
                     action.

        yields:
            In the case that the triggered action is a blocking call, this method will
            yield its result. Otherwise this method will return immediately upon calling
            the triggered actions.
        '''

        actions = self.actions[command]

        for action in actions:

            if not action.meets_requirements(message):
                continue

            if action.async:
                asyncio.ensure_future(action.coro(message))

            else:
                yield from action.coro(message)


    def parser(self, command, *commands):
        """
        Decorator for user-generated parsers.

        Parsers are passed three arguments: a string prefix, a string command, and a list
        of message parameters.
        """

        commands = command, *commands

        def wrapper(func):

            for command in commands:
                self.parsers.update({command: func})

            return func

        return wrapper


    def simple_parser(self, command, *fields, name='Message'):
        """
        Registers a simple message container to a command.
        
        The container returned by commands of this type will be a namedtuple instance
        of name `name`, contained the fields `prefix`, `command`, and all user-supplied
        fields in the order given.
        
        If the parser attempts to parse more argiments than the message supplies,
        excess fields will be filled with empty spaces.
        
        If the parser attempts to parse less arguments than the message supplies,
        excess arguments will be concatenated into the final field.
        
        If no user fields are supplied (i.e., just the defaults `prefix` and `command`),
        and the message contains excess parameters, they will be concatenated into a
        third `params` field to avoid concatenation into the `command` field.
        """
        
        defaults = ('prefix', 'command')
        
        def parse(fields, prefix, command, params):
            
            # message contains more args than fields supplied
            if len(params) > len(fields):
                
                # no additional fields, excess will be concatenated into `params` attr
                if fields == defaults:
                    fields = *fields, 'params'
                
                # unpacks params for each field except last
                # passes remaining params as tuple
                args = *params[:len(fields) - 1], params[len(fields) - 1:]
                
            else:
                # zip_longest fills fields that would otherwise have no value with empty str
                args = [param for param, field in itertools.zip_longest(params, fields, fillvalue='')]
            
            # utils.container caches namedtuple instances so they aren't
            # regenerated on each message
            Container = utils.container(name, defaults + fields)
            
            return Container(prefix, command, *args)
        
        func = functools.partial(parse, fields)

        self.parsers.update({command: func})


    def on(self, command, *commands, async=True, **kwargs):
        '''
        Action decorator.

        args:
            commands: String commands (e.g., 'NOTICE') or numerics (e.g., '003') used to
                      trigger the decorated function. At least one command must be
                      supplied.
                      
            async: A boolean signifying whether this function should be run asynchronously
                   (non-blocking). This is a keyword-only argument that defaults to True.
                   
            kwargs: Any number of additional keyword arguments used to specify the
                    requirements under which the decorated function should be called.
                    For example, @SimpleBot.on('PRIVMSG', nick='chitchat') will only be
                    triggered by a PRIVMSG from a user with a nick of 'chitchat'.

        returns:
            The decorated function.
        '''

        commands = command, *commands

        def wrapper(func):

            # coerces func into a coroutine so it can be yielded from
            coro = func if asyncio.iscoroutine(func) else asyncio.coroutine(func)

            @asyncio.coroutine
            def wrapped(message):

                # iterate over lines yielded
                for line in coro(message):
                    
                    # coroutines (like asyncio.sleep) must be yielded from
                    # or we'll get a nasty traceback
                    if isinstance(line, (asyncio.Future, asyncio.Task)):
                        yield from line
                        continue
                    
                    # a partial PRIVMSG that is only missing its `target` kwarg
                    elif isinstance(line, functools.partial):
                        target = utils.reply_to(message.target)
                        line = line(target=target)
                
                    # a regular, good ol'-fashioned string
                    self.send(line.encode(self.encoding))

            # namedtuple wrapper Action makes for cleaner code
            action = utils.Action(wrapped, async, utils.requirements(kwargs))

            # ensure commands are uppercase for proper triggering
            for command in map(str.upper, commands):
                self.actions[command].add(action)

            return func

        return wrapper


    def command(self, trigger, *triggers, async=True, **kwargs):
        """
        Convenience wrapper for SimpleBot.on('PRIVMSG')
        """

        triggers = trigger, *triggers

        def func(text):
            # the first bit of text needs to match one of our triggers
            # we can't use str.startswith here because it doesn't end
            # at a word boundary
            
            first, *_ = text.split(maxsplit=1)

            return first in triggers

        # func = lambda text: text.split()[0] in triggers

        return self.on(constants.PRIVMSG, async=async, text=func, **kwargs)
    
    
    @contextlib.contextmanager
    @asyncio.coroutine
    def intercept(self, command, *commands, timeout=None, **kwargs):
        """
        Intecepts a command and triggers a one-time action with the message received.
        """
        
        commands = command, *commands
        
        queue = asyncio.Queue(maxsize=1)
        
        @asyncio.coroutine
        def interceptor(message):
            
            # we only want to intercept one message, so check if the queue is full first
            if queue.full():
                return
            
            yield from queue.put(message)

        # namedtuple wrapper Action makes for cleaner code
        action = utils.Action(interceptor, True, utils.requirements(kwargs))

        # ensure commands are uppercase for proper triggering
        for command in map(str.upper, commands):
            self.actions[command].add(action)
        
        # wait_for must be wrapped in a Task to ensure it yields a future if
        # a timeout is passed
        task = asyncio.ensure_future(asyncio.wait_for(queue.get(), timeout))

        try:
            yield from task
            
        except asyncio.TimeoutError as e:
            task.cancel()
            raise e
            
        finally:
            for command in map(str.upper, commands):
                self.actions[command].remove(action)