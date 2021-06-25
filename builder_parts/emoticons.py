from __main__ import session, config, paths
from dotabase import *
from utils import *
from PIL import Image
from valve2json import valve_readfile
import os

def load():
	session.query(Emoticon).delete()
	print("Emoticons")

	print("- loading emoticons from scripts")
	data = valve_readfile(config.vpk_path, paths['emoticon_scripts_file'], "kv", encoding="UTF-16")["emoticons"]
	emoticons_scripts_subdir = "scripts/emoticons"
	for file in os.listdir(os.path.join(config.vpk_path, emoticons_scripts_subdir)):
		filepath = f"/{emoticons_scripts_subdir}/{file}"
		more_emoticon_data = valve_readfile(config.vpk_path, filepath, "kv", encoding="UTF-8")["emoticons"]
		data.update(more_emoticon_data)

	print("- process emoticon data")
	for emoticonid in data:
		if len(data[emoticonid]['aliases']) == 0 or data[emoticonid]['aliases']['0'] == "proteam":
			continue # These are team emoticons, all with the same key. skip em
		emoticon = Emoticon()
		emoticon.id = int(emoticonid)
		emoticon.name = data[emoticonid]['aliases']['0']
		emoticon.ms_per_frame = data[emoticonid]['ms_per_frame']
		emoticon.url = paths['emoticon_image_path'] + data[emoticonid]['image_name'].replace(".png", "_png.png")
		try:
			img = Image.open(config.vpk_path + emoticon.url)
			emoticon.frames = int(img.size[0] / img.size[1])
		except:
			# Error loading this image, so dont add it to the database
			printerr(f"Couldn't find emoticon {emoticon.name} at {emoticon.url}")
			continue

		session.add(emoticon)

	session.commit()