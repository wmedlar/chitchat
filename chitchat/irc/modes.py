__all__ = ('CREATOR', 'OPER', 'VOICE', 'ANONYMOUS', 'INVITEONLY', 'MODERATED', 'NOOUTSIDE', 'QUIET', 'PRIVATE', 'SECRET',
           'REOP', 'TOPICLOCK', 'KEY', 'LIMIT', 'BAN', 'EXCEPTION', 'INVITEMASK')

class Mode:

    __slots__ = ('name', 'flag')

    def __init__(self, name, flag):
        self.name = name
        self.flag = flag

    # def set(self, target, *params):
    #     return 'MODE {0} +{1} {2}\n'.format(target, self.flag * len(params), ' '.join(params)) if params else ''
    #
    # def unset(self, target, *params):
    #     return 'MODE {0} -{1} {2}\n'.format(target, self.flag * len(params), ' '.join(params)) if params else ''

    def __pos__(self):
        return '+{0.flag}'.format(self)

    def __neg__(self):
        return '-{0.flag}'.format(self)

    def __str__(self):
        return '{0.flag}'.format(self)

    def __repr__(self):
        return 'Mode(name={0.name!r}, flag={0.flag!r}, params={0.params!r})'.format(self)


CREATOR = Mode('channel creator', 'O')
OPER = Mode('channel operator', 'o')
VOICE = Mode('ability to speak on a moderated channel', 'v')
ANONYMOUS = Mode('anonymous', 'a')
INVITEONLY = Mode('invite-only', 'i')
MODERATED = Mode('moderated', 'm')
NOOUTSIDE = Mode('no messages to channel from clients on the outside', 'n')
QUIET = Mode('quiet', 'q')
PRIVATE = Mode('private', 'p')
SECRET = Mode('secret', 's')
REOP = Mode('server reop', 'r')
TOPICLOCK = Mode('topic settable by channel operator only', 't')
KEY = Mode('channel key', 'k')
LIMIT = Mode('user limit', 'l')
BAN = Mode('ban mask to keep users out', 'b')
EXCEPTION = Mode('exception mask to override a ban mask', 'e')
INVITEMASK = Mode('invitation mask to override the invite-only flag', 'I')
WALLOPS = Mode('receive WALLOPS messages', 'w')