import asyncio
import collections
import functools
import inspect
import operator
import types

from .connection import Connection
from . import constants
from .decorator import callback
from .utils import ircsplit, require


class Client(Connection):
    
    
    def __init__(self, host, port, *, encoding='UTF-8', ssl=True):
        super().__init__(host, port, encoding=encoding, ssl=ssl)
    
        self.containers = {}
        self.triggers = collections.defaultdict(set)
    
    
    async def handle(self, line):
        """
        Called to handle each line received from the server.
        """
        
        # lines recieved must be converted from bytes to strings
        decoded = line.decode(self.encoding).rstrip(constants.CRLF)
        
        # see utils.ircsplit
        prefix, command, params = ircsplit(decoded)
        
        # converts the recieved message into a namedtuple object with attribute access
        # see structures.Message
        # message = Message(*prefix, command, params)
        
        Container = self.containers.get(command, lambda *a: a)
        
        message = Container(prefix, command, params)
        
        # trigger relevant functions
        triggered = await self.trigger(command, message)
        
        return triggered
    
    
    def on(self, command, **kwargs):
        """
        Decorator for functions to trigger on receiving a specified type of message.
        
        Kwargs is a dict of arbitrary requirements to trigger functions based on the
        attributes of the receieved message.
        """
        
        # the method called to handle lines returned by the callback
        handler = self.send
        
        # method called to register the callback with the listener
        registrar = functools.partial(self.register, command)
        
        return callback(handler, registrar, **kwargs)
    
    
    def register(self, command, func):
        """
        Adds a function to the client's set of triggers.
        """
        
        self.triggers[command].add(func)
            
        return self.triggers
    
    
    def start(self, loop=None):
        """
        Opens a connection to the server in an event loop.
        """
        
        loop = loop or asyncio.get_event_loop()
        loop.run_until_complete(self.run(loop=loop))
        loop.close()
    
    
    async def trigger(self, command, message=None):
        """
        Passes message to triggered functions.
        """
        
        coros = self.triggers[command]
        
        # schedule the triggered coroutines to be executed
        tasks = [asyncio.ensure_future(coro(message)) for coro in coros]
        
        return tasks
    
    
class Bot(Client):
    
    
    def command(self, trigger, *, case_sensitive=False, **kwargs):
        
        decorator = self.on(constants.PRIVMSG,
                            case_sensitive=case_sensitive,
                            text=operator.methodcaller('startswith', trigger),
                            **kwargs)
        
        return decorator
    
    
    
