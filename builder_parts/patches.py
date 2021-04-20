from __main__ import session, config, paths
from dotabase import *
from utils import *
import requests
from datetime import datetime, time


def load():
	session.query(Patch).delete()
	print("Patches")

	print("- loading older patches from wiki data")
	# old patches and their dates scraped from dota 2 wiki
	data = read_json("builderdata/old_patch_dates.json")
	for patch_number in data:
		datestring = data[patch_number]
		patch = Patch()

		patch.number = patch_number
		if datestring is not None:
			date = datetime.strptime(datestring, "%Y-%m-%d")
			timeofday = time(hour=21) # use ~2pm PST as an estimate
			date = datetime.combine(date, timeofday)
			patch.timestamp = date
		patch.wiki_url = f"https://dota2.gamepedia.com/Version_{patch.number}"

		session.add(patch)

	print("- loading patches from api")
	# load all of the item scripts data information
	data = requests.get("https://www.dota2.com/datafeed/patchnoteslist?language=english").json()
	for patch_data in data["patches"]:
		patch = Patch()

		patch.number = patch_data["patch_number"]
		patch.timestamp = datetime.fromtimestamp(patch_data["patch_timestamp"])
		patch.wiki_url = f"https://dota2.gamepedia.com/Version_{patch.number}"
		patch.dota_url = f"https://www.dota2.com/patches/{patch.number}"
		if "patch_website" in patch_data:
			patch.custom_url = f"https://www.dota2.com/{patch_data['patch_website']}"

		session.add(patch)

	session.commit()