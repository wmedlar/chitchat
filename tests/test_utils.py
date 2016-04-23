from chitchat import utils

server = 'irc.rizon.net'
p = 'sakubot!v3@bot.made.of.socks'
nohost = 'sakubot!v3@'
nouser = 'sakubot!@bot.made.of.socks'

print(utils.prefixsplit(server))
print(utils.prefixsplit(p))
print(utils.prefixsplit(nohost))
print(utils.prefixsplit(nouser))
