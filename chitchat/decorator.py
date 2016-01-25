import functools
import inspect
import types

from . import utils


class callback:
    """
    Decorator for functions to trigger on receiving a specified command.
    
    Attributes:
        handle: An awaitable function called to handle lines yielded or returned by the
                decorated function.
        register: A function called to register the decorated function with the listener.
                  It should accept the decorated function as its only argument.
    """
    
    __slots__ = ('handle', 'register')
    
    def __init__(self, handler, registrar):
        self.handle = handler
        self.register = registrar
        
    
    def __call__(self, func):
        awaitable = inspect.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            
            if awaitable:
                lines = await func(*args, **kwargs)
                
            else:
                lines = func(*args, **kwargs)
                
            if not lines:
                return
            
            print(lines)
            
            await self.handle(lines)
            
        # register the function with the listener
        self.register(wrapper)
        
        # return the original function so this decorator can be chained
        return func
    

class plugin:
    """
    Decorates a function to extend a client instance.
    
    Attributes:
    """
    
    """
    @chitchat.plugin('PRIVMSG', channel='#Python', text='hello')
    def func(prefix, target, message):
        
        return chitchat.privmsg(target, 'Hello %s!' % prefix.nick)
    """
    
    def __init__(self, command, channel=None, nick=None, target=None, text=None):
        pass
    
    def __call__(self, func):
        # how should function be marked as a plugin?
        pass
    
    