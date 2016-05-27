import functools

from . import connection
from . import constants
from . import structures
from . import utils
        
        
class Client(connection.AsynchronousConnection):
    
    
    def __init__(self, *args, encoding='UTF-8', **kwargs):
        super().__init__(*args, **kwargs)
        
        self.encoding = encoding
        self.plugins = structures.CaseInsensitiveDefaultDict(set)
    
    
    def register(self, object=None):
        """Registers a `Plugin` or module of `Plugins` with `Client`.
        
        args:
            object: plugin or module containing plugins
            
        returns:
            `None`
        """
        for plugin in utils.find_plugins(object):
            self.plugins[plugin.command].add(plugin)
            
            
    def on(self, command, func=None, **kwargs):
        
        if func is None:
            return functools.partialmethod(command, **kwargs)
        
        plugin = structures.Plugin(func, command, **kwargs)
        self.register(plugin)
        
        return plugin
    
    
    def handle_incoming(self, data):
        """Parse `data` and route to the proper callbacks."""
        # Message constructor decodes data into a regular str
        message = structures.Message(data, encoding=self.encoding)
        self.trigger(message.command, message)

    
    def trigger(self, command, *args, **kwargs):
        """Triggers plugins associated with `command` to be run asynchronously."""
        
        funcs = self.plugins[command] | self.plugins[constants.ALL]
        
        run = self.loop.create_task
        
        for func in funcs:
            coro = func(self, *args, **kwargs)
            run(coro)