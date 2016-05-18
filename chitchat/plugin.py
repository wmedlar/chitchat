import functools
import inspect
import weakref

from . import structures


PLUGIN_VAR = '__chitchat_plugins__'


def on(command, func=None, **kwargs):
    
    # fun idiom to facilitate use as a decorator and a function
    # also saves a level of indentation!
    if func is None:
        return functools.partial(on, command, **kwargs)
    
    plugin = Plugin(func, **kwargs)
    
    # the module defining the decorated function is given a global variable
    # that contains a mapping of `command` to a `WeakSet` of plugins
    module = inspect.getmodule(func)
    keyed_weak_reference(obj=module, attr=PLUGIN_VAR, key=command, ref=plugin)
    
    # plugins require a strong reference to stay alive in the module variable
    # by attaching them to the decorated function, the plugins will remain alive
    # until the module is reloaded
    strong_reference(obj=func, attr=PLUGIN_VAR, ref=plugin)
    
    return func


class Plugin:
    
    def __init__(self, func):
        self.func = func
    
    
    @property
    def func(self):
        """Abstraction of weak reference to func."""
        return self._func_weakref()
    
    
    @func.setter
    def func(self, value):
        self._func_weakref = weakref.ref(value)
        
        
    async def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


    def __repr__(self):
        r = '{0.__class__.__name__}(func={0.func})'
        return r.format(self)


def strong_reference(obj, attr, ref):
    """Add `ref` to a `set` found at `obj.attr`, creating `attr` if necessary."""
    
    try:
        val = getattr(obj, attr)
    
    except AttributeError:
        val = set()
        setattr(obj, attr, val)
        
    val.add(ref)
    
    return val
    
    
def keyed_weak_reference(obj, attr, key, ref):
    """Add `ref` to a `WeakSet` found at `obj.attr[key]`, creating `attr` if necessary."""
    
    try:
        d = getattr(obj, attr)
        
    except AttributeError:
        d = structures.CaseInsensitiveDefaultDict(weakref.WeakSet)
        setattr(obj, attr, d)
        
    val = d[key]
    val.add(ref)
    
    return val