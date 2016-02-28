import collections
import itertools

from . import utils


class prefix(str):
    """
    A string subclass with nick, user, and host attributes and no other added functionality.
    
    All methods will operate on the value passed to the constructer, and will not return a
    new instance of `prefix`.
    """
    
    __slots__ = ('nick', 'user', 'host')
    
    # immutables initialize in __new__, not __init__
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
    
    
    def __init__(self, default_factory, data=None, **kwargs):
        self._dict = {}
        
        self.default_factory = default_factory
        
        if data is None:
            data = {}
            
        self.update(data, **kwargs)
        
    
    def _transform(self, key):
        """Supports non-string keys."""
        
        try:
            return key.casefold()
        
        except AttributeError:
            return key
        
    
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
        # repeat value indefinitely
        repeater = itertools.repeat(value)
        
        return cls(default_factory, zip(seq, repeater))