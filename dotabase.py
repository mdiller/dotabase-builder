#!/usr/bin/env python

import os
import sys
import json
from kv2json import kvfile2json
from model import *

session = dotabase_session()

# paths---------------
vpk_path = "dota-vpk"
item_img_path = "/resource/flash3/images/items/"
hero_image_path = "/resource/flash3/images/heroes/"
hero_icon_path = "/resource/flash3/images/miniheroes/"
hero_selection_path = "/resource/flash3/images/heroes/selection/"
hero_scripts_file = vpk_path + "/scripts/npc/npc_heroes.txt"
dota_english_file = vpk_path + "/resource/dota_english.txt"

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

	# Load additional information from the dota_english.txt file
	data = kvfile2json(dota_english_file)["lang"]["Tokens"]
	for hero in session.query(Hero):
		hero.localized_name = data[hero.full_name]
		hero.bio = data[hero.full_name + "_bio"]

	# Add img files to hero
	for hero in session.query(Hero):
		hero.icon = hero_icon_path + hero.name + ".png"
		hero.image = hero_image_path + hero.name + ".png"
		hero.portrait = hero_selection_path + hero.full_name + ".png"


	session.commit()
	print("heroes loaded")

# def load_responses():
	

def build_dotabase():
	load_heroes()
	#load_items()
	#load_abilities()

if __name__ == "__main__":
    build_dotabase()