#!/usr/bin/env python3.6

from sqlalchemy import desc
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
	print("overwriting db")
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
talents,
responses,
voices,
loadingscreens,
patches)

parts_dict = {
	"chat_wheel": chat_wheel,
	"emoticons": emoticons,
	"items": items,
	"abilities": abilities,
	"heroes": heroes,
	"talents": talents,
	"voices": voices,
	"responses": responses,
	"loadingscreens": loadingscreens,
	"patches": patches
}

def dump_sql():
	print("dumping sql...")
	os.system(f"cd \"{dotabase_dir}\" && sqlite3 dotabase.db \".dump\" > dotabase.db.sql")

# updates the dotabase readme info
def update_readme():
	print("updating readme info...")
	dota_version_path = os.path.join(dotabase_dir, "../DOTA_VERSION")
	data = read_json(dota_version_path)

	patch = session.query(Patch).order_by(desc(Patch.timestamp)).first()
	data["message"] = patch.number

	write_json(dota_version_path, data)

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
		talents.load()
		voices.load()
		responses.load()
		loadingscreens.load()
		patches.load()
	generate_json()
	dump_sql()
	update_readme()
	print("done")


if __name__ == "__main__":
	try:
		build_dotabase()
	except KeyboardInterrupt:
		print("\ndone (canceled)")
