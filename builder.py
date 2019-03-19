#!/usr/bin/env python3.6

from dotabase import *
from utils import *
import os
import sys

single_part = None
if len(sys.argv) > 1:
	single_part = sys.argv[1]

config = Config()
paths = read_json("paths.json")
if config.overwrite_db and os.path.isfile(dotabase_db) and (single_part is None):
	os.remove(dotabase_db)
session = dotabase_session()


from generate_json import generate_json

# Import all parts now that we have the things they need
from builder_parts import (
chat_wheel,
emoticons, 
items, 
abilities, 
heroes, 
responses,
voices,
loadingscreens)

parts_dict = {
	"chat_wheel": chat_wheel,
	"emoticons": emoticons,
	"items": items,
	"abilities": abilities,
	"heroes": heroes,
	"voices": voices,
	"responses": responses,
	"loadingscreens": loadingscreens
}

def build_dotabase():
	if single_part:
		if single_part not in parts_dict:
			print("invalid builder part. valid parts are:")
			for key in parts_dict:
				print(key)
			return None
		parts_dict[single_part].load()
	else:
		chat_wheel.load()
		emoticons.load()
		items.load()
		abilities.load()
		heroes.load()
		voices.load()
		responses.load()
		loadingscreens.load()
	generate_json()
	print("done")


if __name__ == "__main__":
	try:
		build_dotabase()
	except KeyboardInterrupt:
		print("\ndone (canceled)")
