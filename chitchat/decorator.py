import functools
import inspect
import types

from . import utils


class callback:
    """
    Decorator for functions to trigger on receiving a specified command.
    
    Attributes:
        handle: An awaitable function called to handle lines yielded or returned by the decorated function.
        register: A function called to register the decorated function with the listener. It should accept the decorated function as its only argument.
        requirements: A boolean-returning callable designed to compare the attributes of a message container to specified values.
    """
    
    def __init__(self, handler, registrar, **attrs):
        self.handle = handler
        self.register = registrar
        self.requirements = utils.require(False, **attrs)
        
    
    def __call__(self, func):
        
        # async def functions, must be awaited
        coro = inspect.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            
            # ignore any call that does not meet the requirements
            if not self.requirements(*args, **kwargs):
                return
            
            if coro:
                lines = await func(*args, **kwargs)
            else:
                lines = func(*args, **kwargs)
                
            if not lines:
                return
            
            await self.handle(lines)
            
        # register the function with the listener
        self.register(wrapper)
        
        # return the original function so this decorator can be chained
        return func
    