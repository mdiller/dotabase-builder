#!/usr/bin/env python

import os
import sys
import json
import re
from PIL import Image
from valve2json import valve_readfile, read_json
import criteria_sentancing
from dotabase import *
from utils import *

# paths---------------
vpk_path = "C:/Development/Projects/dotabase-web/dota-vpk" # Should be updated to be command line variable if needed
item_img_path = "/resource/flash3/images/items/"
ability_icon_path = "/resource/flash3/images/spellicons/"
hero_image_path = "/resource/flash3/images/heroes/"
hero_icon_path = "/resource/flash3/images/miniheroes/"
emoticon_image_path = "/resource/flash3/images/emoticons/"
hero_selection_path = "/resource/flash3/images/heroes/selection/"
response_rules_path = "/scripts/talker/"
response_mp3_path = "/sounds/vo/"
hero_scripts_file = "/scripts/npc/npc_heroes.txt"
item_scripts_file = "/scripts/npc/items.txt"
ability_scripts_file = "/scripts/npc/npc_abilities.txt"
emoticon_scripts_file = "/scripts/emoticons.txt"
dota_english_file = "/resource/dota_english.txt"
scraped_responses_dir = "ResponseScraper"
scraped_responses_file = "/responses_data.txt"

def load_emoticons():
	session.query(Emoticon).delete()
	print("emoticons")

	print("- loading emoticons from scripts")
	# load all of the item scripts data information
	data = valve_readfile(vpk_path, emoticon_scripts_file, "kv")["emoticons"]
	for emoticonid in data:
		if int(emoticonid) >= 1000:
			continue # These are team emoticons
		emoticon = Emoticon()
		emoticon.id = int(emoticonid)
		emoticon.name = data[emoticonid]['aliases']['0']
		emoticon.ms_per_frame = data[emoticonid]['ms_per_frame']
		emoticon.url = emoticon_image_path + data[emoticonid]['image_name']
		try:
			img = Image.open(vpk_path + emoticon.url)
			emoticon.frames = int(img.size[0] / img.size[1])
		except:
			# Error loading this image, so dont add it to the database
			continue

		session.add(emoticon)

	session.commit()

def load_items():
	session.query(Item).delete()
	print("items")

	print("- loading items from item scripts")
	# load all of the item scripts data information
	data = valve_readfile(vpk_path, item_scripts_file, "kv")["DOTAAbilities"]
	for itemname in data:
		if itemname == "Version":
			continue
		item_data = data[itemname]
		item = Item()

		item.name = itemname
		item.id = item_data['ID']
		item.cost = item_data['ItemCost']

		item.json_data = json.dumps(item_data, indent=4)

		session.add(item)

	print("- loading item data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(vpk_path, dota_english_file, "kv")["lang"]["Tokens"]
	for item in session.query(Item):
		item_tooltip = "DOTA_Tooltip_Ability_" + item.name 
		item_tooltip2 = "DOTA_Tooltip_ability_" + item.name 
		item.localized_name = data.get(item_tooltip, item.name)
		item.description = data.get(item_tooltip + "_Description", data.get(item_tooltip2 + "_Description", ""))
		item.lore = data.get(item_tooltip + "_Lore", data.get(item_tooltip2 + "_Lore", ""))

	print("- adding item icon files")
	# Add img files to item
	for item in session.query(Item):
		if os.path.isfile(vpk_path + item_img_path + item.name.replace("item_", "") + ".png"):
			item.icon = item_img_path + item.name.replace("item_", "") + ".png"
		else:
			if "recipe" in item.name:
				item.icon = item_img_path + "recipe.png"
			else:
				raise ValueError("icon file not found for {}".format(item.name))

	session.commit()

def get_value(hero_data, key, base_data):
	if(key in hero_data):
		return hero_data[key]
	else:
		return base_data[key]
		print("using default for: " + key)

def load_abilities():
	session.query(Ability).delete()
	print("Abilities")

	print("- loading abilities from ability scripts")
	# load all of the ability scripts data information
	data = valve_readfile(vpk_path, ability_scripts_file, "kv")["DOTAAbilities"]
	for abilityname in data:
		if(abilityname == "Version" or
			abilityname == "ability_base" or
			abilityname == "ability_deward" or
			abilityname == "default_attack"):
			continue

		ability_data = data[abilityname]
		ability = Ability()

		ability.name = abilityname
		ability.id = ability_data['ID']

		ability.json_data = json.dumps(ability_data, indent=4)

		session.add(ability)

	print("- loading ability data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(vpk_path, dota_english_file, "kv")["lang"]["Tokens"]
	for ability in session.query(Ability):
		ability_tooltip = "DOTA_Tooltip_ability_" + ability.name 
		ability.localized_name = data.get(ability_tooltip, ability.name)
		ability.description = data.get(ability_tooltip + "_Description", "")
		ability.lore = data.get(ability_tooltip + "_Lore", "")

	print("- adding ability icon files")
	# Add img files to ability
	for ability in session.query(Ability):
		if os.path.isfile(vpk_path + ability_icon_path + ability.name + ".png"):
			ability.icon = ability_icon_path + ability.name + ".png"
		else:
			ability.icon = ability_icon_path + "wisp_empty1.png"

	session.commit()

def load_heroes():
	session.query(Hero).delete()
	print("Heroes")

	# load all of the hero scripts data information
	data = valve_readfile(vpk_path, hero_scripts_file, "kv")["DOTAHeroes"]
	base_data = data["npc_dota_hero_base"]
	progress = ProgressBar(len(data), title="- loading from hero scripts")
	for heroname in data:
		progress.tick()
		if(heroname == "Version" or
			heroname == "npc_dota_hero_target_dummy" or
			heroname == "npc_dota_hero_base"):
			continue

		hero_data = data[heroname]
		hero = Hero()

		hero.full_name = heroname
		hero.media_name = hero_data['VoiceFile'][37:-9]
		hero.name = heroname.replace("npc_dota_hero_", "")
		hero.id = get_value(hero_data, 'HeroID', base_data)
		hero.team = get_value(hero_data, 'Team', base_data)
		hero.base_health_regen = get_value(hero_data, 'StatusHealthRegen', base_data)
		hero.base_movement = get_value(hero_data, 'MovementSpeed', base_data)
		hero.turn_rate = get_value(hero_data, 'MovementTurnRate', base_data)
		hero.base_armor = get_value(hero_data, 'ArmorPhysical', base_data)
		hero.attack_range = get_value(hero_data, 'AttackRange', base_data)
		hero.attack_projectile_speed = get_value(hero_data, 'ProjectileSpeed', base_data)
		hero.attack_damage_min = get_value(hero_data, 'AttackDamageMin', base_data)
		hero.attack_damage_max = get_value(hero_data, 'AttackDamageMax', base_data)
		hero.attack_rate = get_value(hero_data, 'AttackRate', base_data)
		hero.attack_point = get_value(hero_data, 'AttackAnimationPoint', base_data)
		hero.attr_primary = get_value(hero_data, 'AttributePrimary', base_data)
		hero.attr_base_strength = get_value(hero_data, 'AttributeBaseStrength', base_data)
		hero.attr_strength_gain = get_value(hero_data, 'AttributeStrengthGain', base_data)
		hero.attr_base_intelligence = get_value(hero_data, 'AttributeBaseIntelligence', base_data)
		hero.attr_intelligence_gain = get_value(hero_data, 'AttributeIntelligenceGain', base_data)
		hero.attr_base_agility = get_value(hero_data, 'AttributeBaseAgility', base_data)
		hero.attr_agility_gain = get_value(hero_data, 'AttributeAgilityGain', base_data)

		hero.json_data = json.dumps(hero_data, indent=4)

		talents = []

		# Link abilities and add talents
		for slot in range(1, 30):
			if "Ability" + str(slot) in hero_data:
				ability = session.query(Ability).filter_by(name=hero_data["Ability" + str(slot)]).first()
				if ability.name.startswith("special_bonus"):
					talents.append(ability.localized_name)
				else:
					ability.hero_id = hero.id
					ability.ability_slot = slot
		if len(talents) != 8:
			raise ValueError("{} only has {} talents?".format(hero.localized_name, len(talents)))
		hero.talents = "|".join(talents)

		session.add(hero)


	print("- loading hero data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(vpk_path, dota_english_file, "kv")["lang"]["Tokens"]
	for hero in session.query(Hero):
		hero.localized_name = data[hero.full_name]
		hero.bio = data[hero.full_name + "_bio"]

	print("- adding hero image files")
	# Add img files to hero
	for hero in session.query(Hero):
		hero.icon = hero_icon_path + hero.name + ".png"
		hero.image = hero_image_path + hero.name + ".png"
		hero.portrait = hero_selection_path + hero.full_name + ".png"

	print("- adding hero real names")
	data = read_json("builderdata/hero_names.json")
	for hero in session.query(Hero):
		hero.real_name = data.get(hero.name, "")

	print("- adding hero aliases")
	data = read_json("builderdata/hero_aliases.json")
	for hero in session.query(Hero):
		aliases = []
		aliases.append(hero.name.replace("_", " "))
		text = re.sub(r'[^a-z^\s]', r'', hero.localized_name.replace("_", " ").lower())
		if text not in aliases:
			aliases.append(text)
		if hero.real_name != "":
			aliases.append(re.sub(r'[^a-z^\s]', r'', hero.real_name.lower()))
		aliases.extend(data.get(hero.name, []))
		hero.aliases = "|".join(aliases)


	session.commit()

def load_responses():
	session.query(Response).delete()
	session.query(Criterion).delete()
	print("Responses")

	# Add a response for each file in each hero folder in the /sounds/vo folder
	progress = ProgressBar(session.query(Hero).count(), title="- loading from mp3 files:")
	for hero in session.query(Hero):
		progress.tick()
		for root, dirs, files in os.walk(vpk_path + response_mp3_path + hero.media_name):
			for file in files:
				response = Response()
				response.name = file[:-4]
				response.fullname = hero.media_name + "_" + response.name
				response.mp3 = response_mp3_path + hero.media_name + "/" + file
				response.hero_id = hero.id
				response.criteria = ""
				session.add(response)

	load_responses_text()

	print("- loading criteria")
	rules = {}
	groups = {}
	criteria = {}
	# Load response_rules
	for root, dirs, files in os.walk(vpk_path + response_rules_path):
		for file in files:
			if "announcer" in file:
				continue
			data = valve_readfile(vpk_path, response_rules_path + file, "rules")
			for key in data:
				if key.startswith("rule_"):
					rules[key[5:]] = data[key]
				elif key.startswith("response_"):
					groups[key[9:]] = data[key]
				elif key.startswith("criterion_"):
					criteria[key[10:]] = data[key]

	for key in criteria:
		criterion = Criterion()
		criterion.name = key
		vals = criteria[key].split(" ")
		criterion.matchkey = vals[0]
		criterion.matchvalue = vals[1]
		criterion.weight = vals[3] if "weight" in vals else 1.0
		criterion.required = "required" in vals
		session.add(criterion)

	progress = ProgressBar(len(rules), title="- linking rules:")
	for key in rules:
		response_criteria = rules[key]['criteria'].rstrip()
		progress.tick()

		for fullname in groups[rules[key]['response']]:
			response = session.query(Response).filter_by(fullname=fullname).first()
			if response is not None:
				if response.criteria == "":
					response.criteria = response_criteria
				else:
					response.criteria += "|" + response_criteria

	print("- generating pretty criteria")
	criteria_sentancing.load_pretty_criteria(session)

	session.commit()

def load_responses_text():
	progress = ProgressBar(session.query(Response).count(), title="- loading response texts")
	data = valve_readfile(scraped_responses_dir, scraped_responses_file, "scrapedresponses")
	for response in session.query(Response):
		progress.tick()
		if response.name in data:
			text = data[response.name]
			text = re.sub(r'<!--.*-->', r'', text)
			text = re.sub(r'{{Tooltip\|([^|]+)\|(.*)}}', r'\1 (\2)', text)
			text = re.sub(r'{{tooltip\|\?\|(.*)}}', r'(\1)', text)
			text = re.sub(r'{{.*}}', r'', text)
			response.text = text
			response.text_simple = text.replace("...", " ")
			response.text_simple = " " + re.sub(r'[^a-z^0-9^A-Z^\s]', r'', response.text_simple).lower() + " "
			response.text_simple = re.sub(r'\s+', r' ', response.text_simple)
		else:
			response.text = ""
	

def build_dotabase():
	load_emoticons()
	load_items()
	load_abilities()
	load_heroes()
	load_responses()
	print("done")

if __name__ == "__main__":
	global session
	if os.path.isfile(dotabase_db):
		os.remove(dotabase_db)
	session = dotabase_session()
	try:
		build_dotabase()
	except KeyboardInterrupt:
		print("\ndone (canceled)")
