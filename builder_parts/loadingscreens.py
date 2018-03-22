from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile
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

	items_data = valve_readfile(config.vpk_path, paths['cosmetics_scripts_file'], "kv_nocomment", encoding="UTF-16")["items_game"]["items"]

	custom_paths = {
		"Default Loading Screen": "/panorama/images/loadingscreens/default/startup_background_logo_png.png"
	}

	print("- loading loadingscreens from items_game")
	# load all of the item scripts data information
	for key in items_data:
		data = items_data[key]
		if data.get("prefab") != "loading_screen":
			continue # These are team loadingscreens
		loadingscreen = LoadingScreen()
		loadingscreen.id = int(key)
		loadingscreen.name = data.get("name")
		date_array = list(map(int, data.get("creation_date").split("-")))
		loadingscreen.creation_date = datetime.date(date_array[0], date_array[1], date_array[2])

		if loadingscreen.name in custom_paths:
			loadingscreen.image = custom_paths[loadingscreen.name]
		else:
			for asset in data["visuals"]:
				asset_data = data["visuals"][asset]
				if not isinstance(asset_data, str) and asset_data.get("type") == "loading_screen":
					image_path = asset_data["asset"]
					if ".vtex" in image_path:
						image_path = image_path.replace(".vtex", "")
					else:
						image_path += "_tga"
					loadingscreen.image = f"/panorama/images/{image_path}.png"
		
		loadingscreen.thumbnail = os.path.dirname(loadingscreen.image) + "/thumbnail.png"

		if not os.path.exists(config.vpk_path + loadingscreen.image):
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




	print("- associating hero packs")
	for key in items_data:
		data = items_data[key]
		if data.get("prefab") != "bundle":
			continue
		for name in data.get("bundle", []):
			for loadingscreen in session.query(LoadingScreen).filter_by(name=name):

				heroes = data.get("used_by_heroes", {})
				if len(heroes) > 1:
					print("MORE HEROES IN THIS PACK")
				for hero_name in heroes:
					hero = session.query(Hero).filter_by(full_name=hero_name).first()
					if hero:
						loadingscreen.hero_id = hero.id
		

	session.commit()