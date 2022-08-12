from __main__ import session
session: sqlsession.Session
from dotabase import *
from utils import *
from valve2json import ItemsGame

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
		voice.criteria = None

		voice.media_name = vsndevts_to_media_name(json.loads(hero.json_data).get("VoiceFile"))
		voice.hero_id = hero.id

		session.add(voice)

	print("- loading cosmetics file (takes a bit)")
	items_game = ItemsGame()

	custom_urls = {
		"Announcer: Tuskar": "Announcer:_Tusk",
		"Default Announcer": "Announcer_responses",
		"Default Mega-Kill Announcer": "Announcer_responses",
		"Announcer: Bristleback": "Bristleback_Announcer_Pack",
		"Mega-Kills: Bristleback": "Bristleback_Announcer_Pack"
	}
	custom_media_name = {
		"Default Announcer": "announcer",
		"Default Mega-Kill Announcer": "announcer_killing_spree"
	}

	print("- loading from announcers")
	for announcer in items_game.by_prefab["announcer"]:
		voice = Voice()

		# the first announcer has id = 586, so this will not interfere with hero ids
		voice.id = int(announcer["id"])
		voice.name = announcer["name"]
		voice.icon = "/panorama/images/icon_announcer_psd.png"
		voice.image = f"/panorama/images/{announcer['image_inventory']}_png.png"
		voice.criteria = None

		if voice.name in custom_urls:
			voice.url = custom_urls[voice.name]
		else:
			voice.url = name_to_url(announcer["name"])

		if voice.name in custom_media_name:
			voice.media_name = custom_media_name[voice.name]
		else:
			ass_mod = items_game.get_asset_modifier(announcer, "announcer")
			if ass_mod:
				voice.media_name = ass_mod.asset.replace("npc_dota_hero_", "")

		session.add(voice)

	added_names = []
	print("- loading from hero cosmetics")
	for item in items_game.by_prefab["wearable"]:
		criteria = []
		for ass_mod in items_game.get_asset_modifiers(item, "response_criteria"):
			criteria.append(ass_mod.asset)
		if len(criteria) == 0:
			continue
		criteria = "|".join(map(lambda c: f"customresponse:{c}", criteria))
		icon = None
		for ass_mod in items_game.get_asset_modifiers(item, "icon_replacement_hero_minimap"):
			icon = f"/panorama/images/heroes/icons/{ass_mod.modifier}_png.png"
		skip = False
		for pack in items_game.by_prefab["bundle"]:
			if item["name"] not in pack["bundle"]:
				continue
			for item_name in pack["bundle"]:
				if item_name in added_names:
					voice = session.query(Voice).filter_by(name=item_name).first()
					voice.criteria += f"|{criteria}"
					skip = True
				if not icon:
					related_item = items_game.item_name_dict[item_name]
					for ass_mod in items_game.get_asset_modifiers(related_item, "icon_replacement_hero_minimap"):
						icon = f"/panorama/images/heroes/icons/{ass_mod.modifier}_png.png"
						break
		if skip:
			continue

		voice = Voice()
		voice.id = int(item["id"])
		voice.name = item["name"]
		voice.image = f"/panorama/images/{item['image_inventory']}_png.png"
		voice.icon = icon
		voice.criteria = criteria
		voice.media_name = None

		for hero_name in item.get("used_by_heroes", {}):
			hero = session.query(Hero).filter_by(full_name=hero_name).first()
			if hero:
				voice.hero_id = hero.id
				if not voice.icon:
					voice.icon = hero.icon

		added_names.append(voice.name)
		session.add(voice)


	print("- associating announcer packs")
	for pack in items_game.by_prefab["bundle"]:
		if pack.get("name") == "Assembly of Announcers Pack":
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