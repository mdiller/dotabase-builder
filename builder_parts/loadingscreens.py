from __main__ import session
import sqlalchemy.orm.session as sqlsession
session: sqlsession.Session
from dotabase import *
from utils import *
from valve2json import DotaFiles, ItemsGame
from PIL import Image
import datetime
import os
import colorgram
import colorsys

def rgb_to_hsv(rgb):
	rgb = tuple(map(lambda v: v / 255.0, rgb))
	hsv = colorsys.rgb_to_hsv(*rgb)
	return tuple(map(lambda v: int(v * 255), hsv))

def load():
	session.query(LoadingScreen).delete()
	print("loadingscreens")

	items_game = ItemsGame()

	custom_paths = {
		"Default Loading Screen": "/panorama/images/loadingscreens/default/startup_background_logo_png.png"
	}

	# this will be used later for assigning category
	couriers = list(map(lambda i: i.get("name"), items_game.by_prefab["courier"]))

	print("- loading loadingscreens from items_game")
	# load all of the item scripts data information
	for data in items_game.by_prefab["loading_screen"]:
		loadingscreen = LoadingScreen()
		loadingscreen.id = int(data["id"])
		loadingscreen.name = data.get("name")
		date_array = list(map(int, data.get("creation_date").split("-")))
		loadingscreen.creation_date = datetime.date(date_array[0], date_array[1], date_array[2])
		loadingscreen.category = "other"


		if loadingscreen.name in custom_paths:
			loadingscreen.image = custom_paths[loadingscreen.name]
		else:
			ass_mod = items_game.get_asset_modifier(data, "loading_screen")
			if ass_mod:
				image_path = ass_mod.asset
				if ".vtex" in image_path:
					image_path = image_path.replace(".vtex", ".png")
				elif ".png" in image_path:
					image_path = image_path.replace(".png", "_png.png")
				else:
					image_path += "_tga.png"
				loadingscreen.image = f"/panorama/images/{image_path}"
		
		loadingscreen.thumbnail = os.path.dirname(loadingscreen.image) + "/thumbnail.png"

		if not os.path.exists(config.vpk_path + loadingscreen.image):
			printerr(f"Couldn't find loadingscreen at {loadingscreen.image}, skipping")
			continue # skip this loadingscreen because it doesn't exist

		session.add(loadingscreen)

	progress = ProgressBar(session.query(LoadingScreen).count(), title="- making thumbnails and retrieving colors")
	for loadingscreen in session.query(LoadingScreen):
		progress.tick()

		if not os.path.exists(config.vpk_path + loadingscreen.thumbnail):
			image = Image.open(config.vpk_path + loadingscreen.image)
			image.thumbnail((128, 64), Image.ANTIALIAS)
			image.save(config.vpk_path + loadingscreen.thumbnail, format="PNG")

		colors = colorgram.extract(config.vpk_path + loadingscreen.thumbnail, 5)

		loadingscreen.color = "#{0:02x}{1:02x}{2:02x}".format(*colors[0].rgb)
		hsv = rgb_to_hsv(colors[0].rgb)
		loadingscreen.hue = hsv[0]
		loadingscreen.saturation = hsv[1]
		loadingscreen.value = hsv[2]

	## Categories:
	# hero_set
	# hud_skin
	# tournament
	# courier
	# other

	item_type_to_category = {
		"#DOTA_WearableType_Hud_Skin_Bundle": "hud_skin",
		"#DOTA_WearableType_Tournament_Bundle": "tournament"
	}

	print("- associating item packs")
	for data in items_game.by_prefab["bundle"]:
		for name in data.get("bundle", []):
			for loadingscreen in session.query(LoadingScreen).filter_by(name=name):
				heroes = data.get("used_by_heroes", {})
				for hero_name in heroes:
					hero = session.query(Hero).filter_by(full_name=hero_name).first()
					if hero:
						loadingscreen.hero_ids = str(hero.id)
						loadingscreen.category = "hero_set"
				if loadingscreen.category == "hero_set":
					continue
				category = item_type_to_category.get(data.get("item_type_name"))
				if category:
					loadingscreen.category = category
					continue
				if any(x in couriers for x in data.get("bundle", [])):
					loadingscreen.category = "courier"
					continue


	print("- linking heroes")
	data = read_json("builderdata/loadingscreen_heroes.json")
	for screen in session.query(LoadingScreen):
		if screen.name in data:
			heroes = []
			if screen.hero_ids:
				heroes.append(screen.hero_ids)
			for heroname in data[screen.name]:
				hero = session.query(Hero).filter_by(name=heroname).first()
				heroes.append(str(hero.id))
			screen.hero_ids = "|".join(heroes)

	session.commit()