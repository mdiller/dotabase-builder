#!/usr/bin/env python3.6

from dotabase import *
from utils import *
import os

config = Config()
paths = read_json("paths.json")
if config.overwrite_db and os.path.isfile(dotabase_db):
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
	

def build_dotabase():
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
