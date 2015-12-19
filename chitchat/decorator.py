import asyncio
import functools
import inspect
import weakref

from chitchat import utils

class on:
    
    def __init__(self, obj, command, *commands, async=True, **requirements):
        self.obj = weakref.ref(obj)
        self.commands = {cmd.upper() for cmd in (command, *commands)}
        self.async = async
        self.reqs = requirements
    
    def __call__(self, func):
        # must be a coroutine so it can be yielded from
        func = func if asyncio.iscoroutine(func) else asyncio.coroutine(func)
        
        @functools.wraps(func)
        @asyncio.coroutine
        def wrapped(message):
            
            obj = self.obj()
            
            if obj is None:
                raise Exception('does not exist anymore')
            
            coro = func(message)
            
            for line in coro:
                
                print(repr(line), type(line))
                
                # yielding from Future and Task instances allows us to chain coroutines
                # and use functions such as `asyncio.sleep`
                if isinstance(line, asyncio.Future) or inspect.isgenerator(line):
                    line = yield from asyncio.wait_for(line, None)
                    
                    if line is None:
                        continue
                 
                # functools.partial is used for `reply` magic
                elif isinstance(line, functools.partial):
                    target = utils.target(message.target)
                    line = line(target=target)
            
                encoded = line.encode(obj.encoding)
                obj.send(encoded)
            
        action = utils.Action(wrapped, self.async, utils.requirements(self.reqs))
        
        self._add(action)            
        
        return wrapped
        
    def _add(self, action):
        obj = self.obj()
        
        if obj is None:
            raise Exception('does not exist anymore')
        
        for command in self.commands:
            actions = obj.actions[command]
            actions.add(action)
        
    
    def _remove(self, action):
        obj = self.obj()
        
        if obj is None:
            raise Exception('does not exist anymore')
        
        for command in self.commands:
            actions = obj.actions[command]
            actions.remove(action)