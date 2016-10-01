#!/usr/bin/env python

import os
import sys
import json
from valve2json import kvfile2json, rulesfile2json, scrapedresponses2json
from dotabase import *

session = dotabase_session()

# paths---------------
vpk_path = os.path.join(dotabase_dir, "dota-vpk")
item_img_path = vpk_path + "/resource/flash3/images/items/"
hero_image_path = vpk_path + "/resource/flash3/images/heroes/"
hero_icon_path = vpk_path + "/resource/flash3/images/miniheroes/"
hero_selection_path = vpk_path + "/resource/flash3/images/heroes/selection/"
response_rules_path = vpk_path + "/scripts/talker/"
response_mp3_path = vpk_path + "/sounds/vo/"
hero_scripts_file = vpk_path + "/scripts/npc/npc_heroes.txt"
dota_english_file = vpk_path + "/resource/dota_english.txt"
scraped_responses_file = "ResponseScraper/responses_data.txt"

def load_abilities():
	# spell imgs in /resource/flash3/images/spellicons
	print("abilities loaded")

def load_items():
	print("items loaded")

def get_value(hero_data, key, base_data):
	if(key in hero_data):
		return hero_data[key]
	else:
		return base_data[key]
		print("using default for: " + key)

def load_heroes():
	session.query(Hero).delete()
	print("Heroes")

	print("- loading heroes from hero scripts")
	# load all of the hero scripts data information
	data = kvfile2json(hero_scripts_file)["DOTAHeroes"]
	base_data = data["npc_dota_hero_base"]
	for heroname in data:
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

		session.add(hero)

	print("- loading hero data from dota_english")
	# Load additional information from the dota_english.txt file
	data = kvfile2json(dota_english_file)["lang"]["Tokens"]
	for hero in session.query(Hero):
		hero.localized_name = data[hero.full_name]
		hero.bio = data[hero.full_name + "_bio"]

	print("- adding hero image files")
	# Add img files to hero
	for hero in session.query(Hero):
		hero.icon = hero_icon_path + hero.name + ".png"
		hero.image = hero_image_path + hero.name + ".png"
		hero.portrait = hero_selection_path + hero.full_name + ".png"


	session.commit()
	print("heroes loaded")

def load_responses():
	session.query(Response).delete()
	print("Responses")

	print("- loading reponses from /sounds/vo/ mp3 files")
	# Add a response for each file in each hero folder in the /sounds/vo folder
	for hero in session.query(Hero):
		for root, dirs, files in os.walk(response_mp3_path + hero.media_name):
			for file in files:
				response = Response()
				response.name = file[:-4]
				response.fullname = hero.media_name + "_" + response.name
				response.mp3 = response_mp3_path + hero.media_name + "/" + file
				response.hero_id = hero.id
				session.add(response)

	print("- loading response texts")
	data = scrapedresponses2json(scraped_responses_file)
	for response in session.query(Response):
		if response.name in data:
			response.text = data[response.name]
		else:
			response.text = ""

	print("- loading response_rules (takes long time)")
	rules = {}
	groups = {}
	criteria = {}
	# Load response_rules
	for root, dirs, files in os.walk(response_rules_path):
		for file in files:
			if "announcer" in file:
				continue
			data = rulesfile2json(response_rules_path + file)
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

	for key in rules:
		responserule = ResponseRule()
		responserule.name = rules[key]['response']
		for fullname in groups[responserule.name]:
			response = session.query(Response).filter_by(fullname=fullname).first()
			if response is not None:
				response.groups.append(responserule)

		index = 0
		for arg in rules[key]['criteria'].split(" "):
			criteriarg = CriteriArg()
			criteriarg.criterion_name = arg
			criteriarg.group_name = responserule.name
			criteriarg.index = index
			index += 1
			session.add(criteriarg)

		session.add(responserule)


	session.commit()
	print("responses loaded")
	

def build_dotabase():
	load_heroes()
	load_responses()
	print("done")
	#load_items()
	#load_abilities()

if __name__ == "__main__":
    build_dotabase()
