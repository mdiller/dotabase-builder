from __main__ import session, config, paths
from dotabase import *
from utils import *
from PIL import Image
from valve2json import valve_readfile


def load():
	session.query(Emoticon).delete()
	print("emoticons")

	print("- loading emoticons from scripts")
	# load all of the item scripts data information
	data = valve_readfile(config.vpk_path, paths['emoticon_scripts_file'], "kv", encoding="UTF-16")["emoticons"]
	for emoticonid in data:
		if int(emoticonid) >= 1000:
			continue # These are team emoticons
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
			continue

		session.add(emoticon)

	session.commit()