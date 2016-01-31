from . import utils


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
        line = '{0.__class__.__name__}({0}, nick={0.nick}, user={0.user}, host={0.host})'
        return line.format(self)