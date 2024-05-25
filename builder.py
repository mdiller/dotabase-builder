#!/usr/bin/env python3.6

from sqlalchemy import desc
from dotabase import *
from utils import *
import importlib.metadata
import os
import sys

single_part = None
if len(sys.argv) > 1:
	single_part = sys.argv[1]

if __name__ == "__main__" and config.overwrite_db and os.path.isfile(dotabase_db) and (single_part is None):
	print("overwriting db")
	os.remove(dotabase_db)
session = dotabase_session()


from generate_json import generate_json

# Import all parts now that we have the things they need
from builder_parts import (
chat_wheel,
emoticons, 
items, 
facets, 
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
	"facets": facets,
	"abilities": abilities,
	"heroes": heroes,
	"talents": talents,
	"voices": voices,
	"responses": responses,
	"loadingscreens": loadingscreens,
	"patches": patches
}

def update_pkg_version():
	pkgversion = importlib.metadata.version("dotabase")
	filename = os.path.join(dotabase_dir, "../VERSION")

	with open(filename, "r") as f:
		fileversion = f.read()

	if fileversion.strip() == pkgversion.strip():
		version = list(map(lambda i: int(i), pkgversion.split(".")))
		version[-1] += 1
		version = ".".join(map(lambda s: str(s), version))
		with open(filename, "w+") as f:
			f.write(version)
		print(f"version updated to: {version}")

def dump_sql():
	print("dumping sql...")
	os.system(f"cd \"{dotabase_dir}\" && sqlite3 dotabase.db \".dump\" > dotabase.db.sql")

# updates the dotabase readme info
def update_readme():
	print("updating readme info...")
	dota_version_path = os.path.join(dotabase_dir, "../DOTA_VERSION")
	data = read_json(dota_version_path)

	patch = session.query(Patch).order_by(desc(Patch.timestamp)).first()
	if patch is None:
		printerr("No patches found!")
	else:
		if data["message"] != patch.number:
			print(f"dota version updated to: {patch.number}")
			data["message"] = patch.number
		else:
			print(f"keeping patch at: {data['message']}")

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
		facets.load()
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
	update_pkg_version()
	print("done!")


if __name__ == "__main__":
	try:
		build_dotabase()
	except KeyboardInterrupt:
		print("\ndone (canceled)")
