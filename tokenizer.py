# an attempt at building a custom parser for kvfiles

# it works but its way too slow to be usable

from utils import *
import re
from valve2json import valve_readfile

from parsimonious.grammar import Grammar

config = Config()

timer = SimpleTimer()
valve_readfile("/scripts/npc/npc_abilities.txt", "kv", overwrite=True)
print(timer.miliseconds)


timer = SimpleTimer()
with open("F:\\dota_vpk\\scripts\\npc\\npc_abilities.txt", "r") as f:
	text = f.read()

grammar = Grammar(
    r"""
	base = comment object (comment / ws)*
	object  = object_start (kv / comment / object / ws)* object_end
	kv = ~'"[^"]+"\s+"[^"]*"'
    comment = ~"//.*\n"
	object_start = string_lit (comment / ws)* object_start_char
	object_start_char = '{'
	string_lit = ~'"[^"]+"'
	string_lit_empty = '""'
	object_end = '}'
	ws          = ~"\s*"
    emptyline   = ws+
    """
)


grammar.parse(text)

print(timer.miliseconds)
