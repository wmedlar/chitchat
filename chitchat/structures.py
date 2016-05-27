import asyncio
import collections

from . import utils


class Plugin:
    
    
    def __init__(self, func, command, **kwargs):
        self.func = func
        self.command = command
    
        
    @property
    def func(self):
        return self._func
    
    
    @func.setter
    def func(self, value):
        self._func = asyncio.coroutine(value)
    
        
    async def __call__(self, *args, **kwargs):            
        val = await self.func(*args, **kwargs)
        return val
    
    
    def __repr__(self):
        r = '{0.__class__.__name__}(func={0.func})'
        return r.format(self)


class Message(str):
    
    
    @property
    def raw(self):
        """Underlying string message from the server. Alias for `str(self)`."""
        return str(self)


    @utils.lazyproperty
    def parsed(self):
        """Message parsed into component prefix, command, and params."""
        return utils.ircparse(self)
    
    
    @utils.lazyproperty
    def parsed_prefix(self):
        """Prefix of the message sender parsed into component nick, user, and host."""
        return utils.prefixsplit(self.prefix)
    
    
    @property
    def prefix(self):
        """Prefix of the message sender. Alias for `self.parsed.prefix`."""
        return self.parsed.prefix
    
    
    @property
    def command(self):
        """Message command or numeric reply. Alias for `self.parsed.command`."""
        return self.parsed.command
    
    
    @property
    def params(self):
        """Tuple of message parameters. Alias for `self.parsed.params`."""
        return self.parsed.params
    
    
    @property
    def nick(self):
        """Nickname of message sender. Alias for `self.parsed_prefix.nick`."""
        return self.parsed_prefix.nick
    
    
    @property
    def user(self):
        """Username of message sender. Alias for `self.parsed_prefix.user`."""
        return self.parsed_prefix.user
    
    
    @property
    def host(self):
        """Hostname of message sender. Alias for `self.parsed_prefix.host`."""
        return self.parsed_prefix.host
    
    
    @property
    def target(self):
        """Message target channel or user."""
        # target will be the first parameter for *most* messages
        try:
            target = self.params[0]
        except IndexError:
            target = None
            
        return target
    
    
    @property
    def channel(self):
        """Message target channel, or None if target is not a channel."""
        target = self.target
        return target if target and utils.ischannel(target) else None
    
    
    def reply_to(self, public=True):
        """
        Determines the target to reply to.
        
        args:
            public (bool): if True reply publicly (i.e., in channel) if possible,
                           defaults to True
        returns:
            str channel or nick to reply to
        
        """
        channel = self.channel
    
        if public and channel:
            return channel
        
        # if no nick can be identified then this is probably from a server
        return self.nick or self.host
    
    
    def __repr__(self):
        r = '{0.__class__.__name__}({0.raw!r})'
        return r.format(self)
    
    
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