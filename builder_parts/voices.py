from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile

def name_to_url(name):
	conversions = {
		' ': '_',
		'\'': '%27',
		'.': '%2E',
		'&': '%26'
	}
	for key in conversions:
		name = name.replace(key, conversions[key])
	return name

def vsndevts_to_media_name(text):
	text = text.replace("soundevents/voscripts/game_sounds_vo_", "")
	text = text.replace(".vsndevts", "")
	return text 

def load():
	session.query(Voice).delete()
	print("Voices")

	print("- loading from heroes")
	for hero in session.query(Hero):
		voice = Voice()

		voice.id = hero.id
		voice.name = hero.localized_name
		voice.icon = hero.icon
		voice.image = hero.portrait
		voice.url = name_to_url(hero.localized_name) + "/Responses"

		voice.media_name = vsndevts_to_media_name(json.loads(hero.json_data).get("VoiceFile"))
		voice.hero_id = hero.id

		session.add(voice)

	print("- loading cosmetics file (takes a bit)")
	data = valve_readfile(config.vpk_path, paths['cosmetics_scripts_file'], "kv_nocomment", encoding="UTF-8")["items_game"]["items"]

	custom_urls = {
		"Announcer: Tuskar": "Announcer:_Tusk",
		"Default Announcer": "Announcer_responses",
		"Default Mega-Kill Announcer": "Announcer_responses",
		"Announcer: Bristleback": "Bristleback_Announcer_Pack",
		"Mega-Kills: Bristleback": "Bristleback_Announcer_Pack"
	}
	custom_media_name = {
		"Default Announcer": "announcer",
		"Default Mega-Kill Announcer": "announcer_killing_spree",
		"Announcer: Kunkka & Tidehunter": "announcer_dlc_kunkka_tide",
		"Mega-Kills: Kunkka & Tidehunter": "announcer_dlc_kunkka_tide_killing_spree",
		"Announcer: Meepo": "announcer_dlc_meepo",
		"Mega-Kills: Meepo": "announcer_dlc_meepo_killing_spree",
		"Mega-Kills: Gabe Newell": "announcer_dlc_gaben_killing_spree"
	}

	print("- loading from announcers")
	for key in data:
		announcer = data[key]
		if announcer.get("prefab") != "announcer":
			continue

		voice = Voice()

		# the first announcer has id = 586, so this will not interfere with hero ids
		voice.id = int(key)
		voice.name = announcer["name"]
		voice.icon = "/panorama/images/icon_announcer_psd.png"
		voice.image = f"/panorama/images/{announcer['image_inventory']}_png.png"

		if voice.name in custom_urls:
			voice.url = custom_urls[voice.name]
		else:
			voice.url = name_to_url(announcer["name"])

		if voice.name in custom_media_name:
			voice.media_name = custom_media_name[voice.name]
		else:
			for asset in announcer["visuals"]:
				if announcer["visuals"][asset]["type"] == "announcer":
					voice.media_name = vsndevts_to_media_name(announcer["visuals"][asset]["modifier"])

		session.add(voice)

	print("- associating announcer packs")
	for key in data:
		pack = data[key]
		if pack.get("prefab") != "bundle" or pack.get("name") == "Assembly of Announcers Pack":
			continue
		for name in pack.get("bundle", []):
			for voice in session.query(Voice).filter_by(name=name):
				voice.url = name_to_url(pack["name"])
		

	data = read_json("builderdata/voice_actors.json")
	print("- adding voice actors")
	for voice in session.query(Voice):
		if str(voice.id) in data:
			voice.voice_actor = data[str(voice.id)]



	session.commit()