from chitchat import cmd, num
from chitchat.base import BaseClient
from chitchat.mixins import BotMixin, CommandMixin


class Client(BaseClient, CommandMixin):
    pass


# BotMixin overrides BaseClient's triggered_by method, so it must be higher up in the mro
# meaning that BotMixin must come to the left of BaseClient when subclassing
class Bot(BotMixin, BaseClient, CommandMixin):
    pass