import asyncio
import collections
import functools

from . import utils


class Callback:
    """
    A callback triggered upon receiving messages from the connected server.
    """
    
    
    def __init__(self, func, validator):
        self.func = func
        self.validator = validator
        
        self.awaitable = asyncio.iscoroutinefunction(func)
    
    
    async def __call__(self, *args):
        
        if not self.validate(*args):
            return False
        
        if self.awaitable:
            result = await self.func(*args)
        
        else:
            result = self.func(*args)
            
        return result
    
    
    def validate(self, *args):
        """
        Determines whether passed arguments are sufficient to trigger the wrapped
        function.
        
        This will return False at the first opportunity to indicate that the supplied
        arguments are insufficient and True if all conditions are met.
        """
        
        return self.validator(*args)
    
        
    def __repr__(self):
        line = '{0.__class__.__name__}(func={0.func.__name__}, validator={0.validator!r})'
        return line.format(self)
    
    
def Validator(*, nick=True, user=True, host=True, target=True, text=True):
    
    funcs = (
        utils.as_comparable(nick),
        utils.as_comparable(user),
        utils.as_comparable(host),
        utils.as_comparable(target),
        utils.as_comparable(text)
    )
    
    @functools.lru_cache(maxsize=128)
    def validate(prefix_, target_, text_=None):
        
        params = (*utils.prefixsplit(prefix_), target_, text_)
            
        return all(func(arg) for func, arg in zip(funcs, params))
    
    rep = 'Validator(nick={0}, user={1}, host={2}, target={3}, text={4})'
    validate.__repr__ = rep.format(nick, user, host, target, text)
    
    return validate
    
    

class prefix(str):
    """
    A string subclass with nick, user, and host attributes and no other added functionality.
    
    All methods will operate on the value passed to the constructer, and will not return a
    new instance of `prefix`.
    """
    
    __slots__ = ('nick', 'user', 'host')
    
    def __new__(cls, ircprefix):
        inst = super().__new__(cls, ircprefix)
        inst.nick, inst.user, inst.host = utils.prefixsplit(ircprefix)
        return inst
        
    def __repr__(self):
        line = '{0.__class__.__name__}({0}, nick={0.nick!r}, user={0.user!r}, host={0.host!r})'
        return line.format(self)
    
    
class CaseInsensitiveDefaultDict(collections.abc.MutableMapping):
    """
    A mashup of a case-insensitive keyed dict and collections.defaultdict.
    
    Write an example for me!
    """
        
    
    @staticmethod
    def _transform(key):
        """Supports non-string keys."""
        
        try:
            return key.casefold()
        
        except AttributeError:
            return key
    
    
    def __init__(self, default_factory, data=None, **kwargs):
        self._dict = {}
        
        self.default_factory = default_factory
        
        if data is None:
            data = {}
            
        self.update(data, **kwargs)
        
    
    def __setitem__(self, key, value):
        self._dict[self._transform(key)] = (key, value)
        
        
    def __getitem__(self, key):
        try:
            origkey, value = self._dict[self._transform(key)]
            
        except KeyError:            
            # call to __missing__ must be explicit because of overloading __getitem__
            value = self.__missing__(key)
            
        return value
    
    
    def __delitem__(self, key):
        del self._dict[self._transform(key)]
    
    
    def __iter__(self):
        return (origkey for origkey, value in self._dict.values())
    
        
    def __len__(self):
        return len(self._dict)
    
    
    def __missing__(self, key):
        # emulate defaultdict's behavior is no default_factory is supplied
        if self.default_factory is None:
            raise KeyError(key)
        
        self[key] = self.default_factory()
        return self[key]
    
    
    def __repr__(self):
        line = '{0.__class__.__name__}({0.default_factory}, {1})'
        return line.format(self, dict(self.items()))
    
    
    def get(self, key, default=None):
        
        try:
            # _dict.get avoids __getitem__'s defaultdict-like behavior
            origkey, value = self._dict.get(self._transform(key))
            
        except TypeError:
            value = default
            
        return value
    
    
    @classmethod
    def fromkeys(cls, default_factory, seq, value=None):        
        return cls(default_factory, dict.fromkeys(seq, value))