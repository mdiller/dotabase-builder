#!/usr/bin/env python

import os
import sys
import dota2api
from kv2json import kvfile2json
from model import *

session = dotabase_session()

# paths---------------
vpk_path = "dota-vpk"
item_img_path = vpk_path + "/resource/flash3/images/items/"
hero_img_path = vpk_path + "/resource/flash3/images/heroes/"
hero_icon_path = vpk_path + "/resource/flash3/images/miniheroes/"
hero_icon_path = vpk_path + "/resource/flash3/images/miniheroes/"
hero_scripts_path = vpk_path + "/scripts/npc/npc_heroes.txt"
dota_english_path = vpk_path + "/resource/dota_english.txt"

# important dictionaries----------------
attr_icon_dict = {
	"STR" : hero_img_path + "selection/pip_str.png",
	"INT" : hero_img_path + "selection/pip_int.png",
	"AGI" : hero_img_path + "selection/pip_agi.png"
}

def load_abilities():
	# spell imgs in /resource/flash3/images/spellicons
	print("abilities loaded")

def load_items():
	session.delete(Item)
	for item in dota_api.get_game_items()['items']:
		db.session.add(Item(id=item['id'], 
							name=item['name'],  
							localized_name=item['localized_name'], 
							cost=item['cost'], 
							recipe=item['recipe'], 
							secret_shop=item['secret_shop'], 
							side_shop=item['side_shop']))

	# load all images for items
	for item in Item.query.all():
		if(item.recipe):
			item.img_path = item_img_path + "recipe.png"
		else:
			item.img_path = item_img_path + item.name[5:] + ".png"

	db.session.commit()
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
	data = kvfile2json(hero_scripts_path)["DOTAHeroes"]
	base_data = data["npc_dota_hero_base"]
	for heroname in data:
		if(heroname == "Version" or
			heroname == "npc_dota_hero_target_dummy" or
			heroname == "npc_dota_hero_base"):
			continue

		hero_data = data[heroname]
		hero = Hero()

		hero.name = heroname
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

		session.add(hero)

	# Load additional information from the dota_english.txt file
	data = kvfile2json(dota_english_path)["lang"]["Tokens"]
	for hero in session.query(Hero):
		hero.localized_name = data[hero.name]
		hero.bio = data[hero.name + "_bio"]

	session.commit()
	print("heroes loaded")

def build_dotabase():
	load_heroes()
	#load_items()
	#load_abilities()

if __name__ == "__main__":
    build_dotabase()