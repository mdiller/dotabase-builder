from builder import session
from dotabase import *
from utils import *
from valve2json import DotaFiles, DotaPaths


def build_replacements_dict(item: Item):
	specials = json.loads(item.ability_special, object_pairs_hook=OrderedDict)
	result = {
		"abilityhealthcost": item.health_cost,
		"abilitychargerestoretime": item.cooldown,
		"abilitycooldown": item.cooldown,
		"abilityduration": item.duration,
		"abilitycastrange": item.cast_range,
		"customval_team_tomes_used": "0",
		"abilitychanneltime": json.loads(item.json_data).get("AbilityChannelTime", "")
	}
	for attrib in specials:
		if attrib["key"] not in result:
			result[attrib["key"]] = attrib["value"]
	return result

def load():
	session.query(Item).delete()
	print("Items")

	added_ids = []

	item_name_fixes = {
		"item_trident1": "item_trident"
	}
	print("- loading items from item scripts")

	# load all of the item scripts data information
	item_id_map = DotaFiles.npc_ids.read()["DOTAAbilityIDs"]["ItemAbilities"]["Locked"]
	data = DotaFiles.items.read()["DOTAAbilities"]
	for itemname in data:
		if itemname == "Version":
			continue
		item_data = data[itemname]
		if item_data.get('IsObsolete') == "1":
			continue # ignore obsolete items
		item = Item()

		item.name = item_name_fixes.get(itemname, itemname)
		item.id = item_id_map[item.name]
		item.cost = item_data.get('ItemCost')
		item.aliases = "|".join(item_data.get("ItemAliases", "").split(";"))
		item.quality = item_data.get("ItemQuality")
		item.health_cost = clean_values(item_data.get('AbilityHealthCost'))
		item.mana_cost = clean_values(item_data.get('AbilityManaCost'))
		item.cooldown = clean_values(item_data.get('AbilityCooldown'))
		if item_data.get('AbilityChargeRestoreTime'):
			item.cooldown = clean_values(item_data.get('AbilityChargeRestoreTime'))
		item.cast_range = clean_values(item_data.get('AbilityCastRange'))
		item.duration = clean_values(item_data.get('AbilityDuration'))
		item.base_level = item_data.get("ItemBaseLevel")
		item.secret_shop = item_data.get("SecretShop") == "1"
		item.shop_tags = "|".join(item_data.get("ItemShopTags", "").split(";"))
		item.ability_special = json.dumps(get_ability_special(item_data, item.name), indent=4)

		item.json_data = json.dumps(item_data, indent=4)

		if item.id in added_ids:
			print(f"duplicate id on: {itemname}")
			continue
		added_ids.append(item.id)

		session.add(item)


	print("- adding item aliases")
	data = read_json("builderdata/item_aliases.json")
	for item in session.query(Item):
		aliases = item.aliases.split("|")
		aliases.extend(data.get(item.name, []))
		item.aliases = "|".join(aliases)

	# Load additional information from the dota_english.txt file
	english_data = DotaFiles.abilities_english.read()["lang"]["Tokens"]
	lang_data = DotaFiles.lang_abilities
	progress = ProgressBar(session.query(Item).count(), title="- loading item data from lang files")
	for item in session.query(Item):
		progress.tick()
		item_tooltip = "DOTA_Tooltip_Ability_" + item.name 
		item_tooltip2 = "DOTA_Tooltip_ability_" + item.name 

		ability_special = json.loads(item.ability_special, object_pairs_hook=OrderedDict)
		ability_special = ability_special_add_header(ability_special, english_data, item.name)
		item.ability_special = json.dumps(ability_special, indent=4)
		replacements_dict = build_replacements_dict(item)
		
		for lang, data in lang_data:
			data = CaseInsensitiveDict(data.read()["lang"]["Tokens"])
			info = {}
			info["localized_name"] = data.get(item_tooltip, item.name)
			info["description"] = data.get(item_tooltip + "_Description", data.get(item_tooltip2 + "_Description", ""))
			info["lore"] = data.get(item_tooltip + "_Lore", data.get(item_tooltip2 + "_Lore", ""))

			report_errors = lang == "english"

			info["description"] = clean_description(info["description"], replacements_dict, base_level=item.base_level, report_errors=report_errors)
			info["lore"] = clean_description(info["lore"])
			
			if lang == "english":
				for key in info:
					setattr(item, key, info[key])
			else:
				for key in info:
					addLocaleString(session, lang, item, key, info[key])

	print("- adding neutral item data")
	data = DotaFiles.neutral_items.read()["neutral_items"]
	item_tier_map = {}
	for tier in data:
		for name in data[tier]["items"]:
			item_tier_map[name] = tier
	for item in session.query(Item):
		if item.name in item_tier_map:
			item.neutral_tier = item_tier_map[item.name]

	print("- linking recipes")
	for recipe in session.query(Item):
		json_data = json.loads(recipe.json_data)
		if json_data.get("ItemRecipe", "0") != "0":
			components = list(json_data.get("ItemRequirements", {"01": None}).values())[0]
			if components is None:
				continue
			components = components.replace(";", " ").replace("*", "").strip().split(" ")
			if recipe.cost != 0:
				components.append(recipe.name)
			crafted_item_name = json_data.get("ItemResult")
			crafted_item = session.query(Item).filter_by(name=crafted_item_name).first()
			if not crafted_item:
				raise ValueError(f"Can't find crafted item {crafted_item_name}")
			crafted_item.recipe = "|".join(components)
			if recipe.neutral_tier is not None: # stuff like trident
				crafted_item.neutral_tier = recipe.neutral_tier

			if recipe.cost == 0 and not json_data.get("ItemIsNeutralDrop"):
				session.delete(recipe)

	print("- adding item icon files")
	# Add img files to item
	for item in session.query(Item):
		iconpath = DotaPaths.item_images + item.name.replace("item_", "") + "_png.png"
		if os.path.isfile(config.vpk_path + iconpath):
			item.icon = iconpath
		else:
			if "recipe" in item.name:
				item.icon = DotaPaths.item_images + "recipe.png"
			else:
				printerr(f"icon file not found for {item.name}")

	session.commit()
