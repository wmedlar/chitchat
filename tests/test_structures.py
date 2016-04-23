from chitchat import structures

d = structures.CaseInsensitiveDefaultDict.fromkeys(list, range(15))

print(d)

print(d['this'])