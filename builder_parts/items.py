from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile


def load():
	session.query(Item).delete()
	print("items")

	print("- loading items from item scripts")
	# load all of the item scripts data information
	data = valve_readfile(config.vpk_path, paths['item_scripts_file'], "kv")["DOTAAbilities"]
	for itemname in data:
		if itemname == "Version":
			continue
		item_data = data[itemname]
		item = Item()

		item.name = itemname
		item.id = item_data['ID']
		item.cost = item_data.get('ItemCost')
		item.aliases = "|".join(item_data.get("ItemAliases", "").split(";"))
		item.quality = item_data.get("ItemQuality")
		item.mana_cost = clean_values(item_data.get('AbilityManaCost'))
		item.cooldown = clean_values(item_data.get('AbilityCooldown'))
		item.base_level = item_data.get("ItemBaseLevel")
		item.ability_special = json.dumps(get_ability_special(item_data.get("AbilitySpecial"), itemname), indent=4)

		item.json_data = json.dumps(item_data, indent=4)

		session.add(item)

	print("- loading item data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(config.vpk_path, paths['localization_abilities'], "kv", encoding="UTF-16")["lang"]["Tokens"]
	for item in session.query(Item):
		item_tooltip = "DOTA_Tooltip_Ability_" + item.name 
		item_tooltip2 = "DOTA_Tooltip_ability_" + item.name 
		item.localized_name = data.get(item_tooltip, item.name)
		item.description = data.get(item_tooltip + "_Description", data.get(item_tooltip2 + "_Description", ""))
		item.lore = data.get(item_tooltip + "_Lore", data.get(item_tooltip2 + "_Lore", ""))

		ability_special = json.loads(item.ability_special, object_pairs_hook=OrderedDict)
		ability_special = ability_special_add_header(ability_special, data, item.name)
		item.ability_special = json.dumps(ability_special, indent=4)
		item.description = clean_description(item.description, ability_special, base_level=item.base_level)

	print("- adding item icon files")
	# Add img files to item
	for item in session.query(Item):
		iconpath = paths['item_img_path'] + item.name.replace("item_", "") + "_png.png"
		if os.path.isfile(config.vpk_path + iconpath):
			item.icon = iconpath
		else:
			if "recipe" in item.name:
				item.icon = paths['item_img_path'] + "recipe.png"
			else:
				printerr(f"icon file not found for {item.name}", flush=True)

	session.commit()
