import asyncio
import collections
import functools

from .connection import Connection
from . import constants, decorator, utils


class Client(Connection):
    
    
    def __init__(self, host, port, *, encoding='UTF-8', ssl=True):
        super().__init__(host, port, encoding=encoding, ssl=ssl)

        self.listeners = collections.defaultdict(set)
    
    
    async def handle(self, line):
        """
        Called to handle each line received from the server.
        """
        
        # lines recieved must be converted from bytes to strings
        decoded = line.decode(self.encoding).rstrip(constants.CRLF)
        
        # see utils.ircsplit
        prefix, command, params = utils.ircsplit(decoded)
        
        triggered = await self.trigger(command=command, prefix, command, *params)
        
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
        
        return decorator.callback(handler, registrar, **kwargs)
    
    
    def register(self, command, func):
        """
        Adds a function to the client's set of triggers.
        """
        
        self.listeners[command].add(func)
            
        return self.listeners
    
    
    def start(self, loop=None):
        """
        Opens a connection to the server in an event loop.
        """
        
        loop = loop or asyncio.get_event_loop()
        loop.run_until_complete(self.run(loop=loop))
        loop.close()
    
    
    async def trigger(self, command, *args, **kwargs):
        """
        Passes parsed arguments to any registered listeners.
        """
        
        listeners = self.listeners[command]
        
        # schedule the triggered coroutines to be executed
        tasks = [asyncio.ensure_future(coro(*args, **kwargs)) for listener in listeners]
        
        return tasks
    
    
class Bot(Client):
    
    pass
    
    
