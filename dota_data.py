#!/usr/bin/env python

import os
import sys
import dota2api
import json
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import SQLALCHEMY_DATABASE_URI
from model import *

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

# dota_api = dota2api.Initialise()

# paths---------------
vpk_path = "dota-vpk"
item_img_path = vpk_path + "/resource/flash3/images/items/"
hero_img_path = vpk_path + "/resource/flash3/images/heroes/"
hero_icon_path = vpk_path + "/resource/flash3/images/miniheroes/"
hero_icon_path = vpk_path + "/resource/flash3/images/miniheroes/"
hero_scripts_path = os.getcwd() + vpk_path + "/scripts/npc/npc_heroes.json"

# important dictionaries----------------
attr_icon_dict = {
	"STR" : hero_img_path + "selection/pip_str.png",
	"INT" : hero_img_path + "selection/pip_int.png",
	"AGI" : hero_img_path + "selection/pip_agi.png"
}

def load_abilities():
	# spell imgs in /resource/flash3/images/spellicons
	print "abilities loaded"

def load_items():
	Item.query.delete()
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
	print "items loaded"


def get_value(hero_data, key, default):
	if(key in hero_data):
		return hero_data[key]
	else:
		return default

def get_attr(hero_data):
	if("AttributePrimary" in hero_data):
		attr_dict = {
			"DOTA_ATTRIBUTE_STRENGTH" : "STR",
			"DOTA_ATTRIBUTE_INTELLECT" : "INT",
			"DOTA_ATTRIBUTE_AGILITY" : "AGI"
		}
		return attr_dict[hero_data['AttributePrimary']]
	else:
		return "DOTA_ATTRIBUTE_STRENGTH"

def load_heroes():
	Hero.query.delete()
	for hero in dota_api.get_heroes()['heroes']:
		db.session.add(Hero(id=hero['id'], 
							name=hero['name'], 
							localized_name=hero['localized_name']))

	# load all images and icons for heroes
	for hero in Hero.query.all():
		hero.img_path = hero_img_path + hero.name[14:] + ".png"
		hero.icon_path = hero_icon_path + hero.name[14:] + ".png"

	# load all of the hero scripts data information
	data = json.load(file(hero_scripts_path))['DOTAHeroes']
	for hero in Hero.query.all():
		hero_data = data[hero.name]
		hero.base_health_regen = get_value(hero_data, 'StatusHealthRegen', 0.25)
		hero.base_movement = get_value(hero_data, 'MovementSpeed', 0.25)
		hero.turn_rate = get_value(hero_data, 'MovementTurnRate', 0.5)
		hero.base_armor = get_value(hero_data, 'ArmorPhysical', -1)
		hero.attack_range = get_value(hero_data, 'AttackRange', 600)
		hero.attack_projectile_speed = get_value(hero_data, 'ProjectileSpeed', 0)
		hero.attack_damage_min = get_value(hero_data, 'AttackDamageMin', 1)
		hero.attack_damage_max = get_value(hero_data, 'AttackDamageMax', 1)
		hero.attack_rate = get_value(hero_data, 'AttackRate', 1)
		hero.attack_point = get_value(hero_data, 'AttackAnimationPoint', 1)
		hero.attr_primary = get_attr(hero_data)
		hero.attr_base_strength = get_value(hero_data, 'AttributeBaseStrength', 0)
		hero.attr_strength_gain = get_value(hero_data, 'AttributeStrengthGain', 0)
		hero.attr_base_intelligence = get_value(hero_data, 'AttributeBaseIntelligence', 0)
		hero.attr_intelligence_gain = get_value(hero_data, 'AttributeIntelligenceGain', 0)
		hero.attr_base_agility = get_value(hero_data, 'AttributeBaseAgility', 0)
		hero.attr_agility_gain = get_value(hero_data, 'AttributeAgilityGain', 0)

	db.session.commit()
	print "heroes loaded"

def load_all():
	load_heroes()
	load_items()
	load_abilities()


if __name__ == "__main__":
    load_all()
    print "load all complete"