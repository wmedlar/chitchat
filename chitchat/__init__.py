from chitchat import cmd, num
from chitchat.irc import Message, ISUPPORT, supported, add_support
from chitchat.mixins import BotMixin, CommandMixin
from chitchat.structures import BaseClient


class Client(BaseClient, CommandMixin):
    pass


# BotMixin overrides BaseClient's triggered_by method, so it must be higher up in the mro
# meaning that BotMixin must come to the left of BaseClient when subclassing
class Bot(BotMixin, BaseClient, CommandMixin):
    pass