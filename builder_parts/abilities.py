'''''
PROMPT:

[- Used So Far: 0.0154¢ | 217 tokens -]
'''''
from builder import session
from dotabase import *
from utils import *
from valve2json import DotaFiles, DotaPaths, ValveFile, valve_readfile
import re

def build_replacements_dict_facetabilitystrings(facet: Facet, ability: Ability):
	specials = json.loads(facet.ability_special, object_pairs_hook=OrderedDict)
	result = build_replacements_dict(ability)
	for attrib in specials:
		result[attrib["key"]] = attrib["value"]
	return result

def build_replacements_dict_facet(facet: Facet):
	specials = json.loads(facet.ability_special, object_pairs_hook=OrderedDict)
	result = {}
	for attrib in specials:
		if attrib["key"] not in result:
			result[attrib["key"]] = attrib["value"]
	return result

def build_replacements_dict(ability: Ability, scepter=False, shard=False):
	specials = json.loads(ability.ability_special, object_pairs_hook=OrderedDict)
	result = {
		"abilityduration": ability.duration,
		"abilitychanneltime": ability.channel_time,
		"abilitycastpoint": ability.cast_point,
		"abilitycastrange": ability.cast_range,
		"abilitychargerestoretime": ability.cooldown,
		"charge_restore_time": ability.cooldown,
		"abilitycooldown": ability.cooldown,
		"max_charges": ability.charges,
		"AbilityCharges": ability.charges,
		"abilitymanacost": ability.mana_cost
	}
	for attrib in specials:
		is_scepter_upgrade = attrib.get("scepter_upgrade") == "1" and not ability.scepter_grants
		is_shard_upgrade = attrib.get("shard_upgrade") == "1" and not ability.shard_grants
		if (is_scepter_upgrade and not scepter) or (is_shard_upgrade and not shard):
			if (attrib["key"] in result):
				continue # skip this if we we don't want to *override* stuff with shard/scepter stuff
		if (attrib["key"] not in result) or is_scepter_upgrade or is_shard_upgrade:
			value = attrib.get("value")
			if shard and attrib.get("shard_value"):
				value = attrib.get("shard_value")
			if scepter and attrib.get("scepter_value"):
				value = attrib.get("scepter_value")
			if value and value != "":
				result[attrib["key"]] = value
		if shard and attrib.get("shard_bonus"):
			result[f"bonus_{attrib['key']}"] = attrib.get("shard_bonus")
			result[f"shard_{attrib['key']}"] = attrib.get("shard_value")
		if scepter and attrib.get("scepter_bonus"):
			result[f"bonus_{attrib['key']}"] = attrib.get("scepter_bonus")
			result[f"scepter_{attrib['key']}"] = attrib.get("scepter_value")
	return result

def load():
	session.query(Ability).delete()
	print("Abilities")

	added_ids = []
	
	print("- loading abilities from ability scripts")
	# load all of the ability scripts data information
	ability_id_map = DotaFiles.npc_ids.read()["DOTAAbilityIDs"]["UnitAbilities"]["Locked"]
	main_data = DotaFiles.npc_abilities.read()["DOTAAbilities"]
	ability_base = main_data["ability_base"]

	# FIX ID_MAP CUZ APPARENTLY THESE ONES ARE BROKEN FOR SOME REASON
	id_remap = {
		"special_bonus_unique_lina_dragon_slave_crits": "special_bonus_unique_lina_crit_debuff",
		# "special_bonus_unique_timbersaw_reactive_armor_regen_per_stack1": "special_bonus_unique_timbersaw_reactive_armor_regen_per_stack"
	}
	for bad_name in id_remap:
		good_name = id_remap[bad_name]
		ability_id_map[good_name] = ability_id_map[bad_name]
		del ability_id_map[bad_name]

	# this method called by loop below it
	def add_ability(abilityname, data_source):
		if(abilityname == "Version" or
			abilityname == "ability_deward" or
			abilityname == "dota_base_ability"):
			return

		ability_data = data_source[abilityname]
		ability = Ability()

		def get_val(key, default_base=False):
			if key in ability_data:
				val = ability_data[key]
				if ' ' in val and all(x == val.split(' ')[0] for x in val.split(' ')):
					return val.split(' ')[0]
				return val
			elif "AbilityValues" in ability_data and key in ability_data["AbilityValues"]:
				val = ability_data["AbilityValues"][key]
				if not isinstance(val, str):
					val = val["value"]
				if ' ' in val and all(x == val.split(' ')[0] for x in val.split(' ')):
					return val.split(' ')[0]
				return val
			elif default_base:
				return ability_base[key]
			else:
				return None
		
		# TEMP? CODE TO IGNORE ABILITIES THAT DONT HAVE IDS
		# if abilityname not in ability_id_map and get_val("BaseClass") == "special_bonus_base":
		# 	printerr(f"Missing ID for {abilityname}")
		# 	return
		if abilityname in id_remap or "special_bonus_unique_timbersaw_reactive_armor_regen_per_stack1" == abilityname:
			return # these are not real abilities

		def get_ability_id(name):
			if name in ability_id_map:
				return ability_id_map[name]
			name = name.replace("1", "")
			return ability_id_map[name]

		ability.name = abilityname
		ability.id = get_ability_id(ability.name)
		ability.type = get_val('AbilityType', default_base=True)
		ability.behavior = get_val('AbilityBehavior', default_base=True)
		ability.cast_range = clean_values(get_val('AbilityCastRange'))
		ability.cast_point = clean_values(get_val('AbilityCastPoint'))
		ability.channel_time = clean_values(get_val('AbilityChannelTime'))
		ability.charges = clean_values(get_val('AbilityCharges'))
		if ability.charges:
			ability.cooldown = clean_values(get_val('AbilityChargeRestoreTime'))
		else:
			ability.cooldown = clean_values(get_val('AbilityCooldown'))
		ability.duration = clean_values(get_val('AbilityDuration'))
		ability.damage = clean_values(get_val('AbilityDamage'))
		ability.health_cost = clean_values(get_val('AbilityHealthCost'))
		ability.mana_cost = clean_values(get_val('AbilityManaCost'))
		ability.ability_special = json.dumps(get_ability_special(ability_data, ability.name), indent=4)
		ability.scepter_grants = get_val("IsGrantedByScepter") == "1"
		ability.shard_grants = get_val("IsGrantedByShard") == "1"
		ability.scepter_upgrades = get_val("HasScepterUpgrade") == "1"
		ability.shard_upgrades = get_val("HasShardUpgrade") == "1"
		ability.innate = get_val("Innate") == "1"


		if ability.id in added_ids:
			printerr(f"duplicate id on: {ability.name}")
			return
		added_ids.append(ability.id)

		def get_enum_val(key, prefix):
			value = get_val(key)
			if value:
				return re.sub(prefix, "", value).lower().replace(" ", "")
			else:
				return value

		ability.behavior = get_enum_val('AbilityBehavior', "DOTA_ABILITY_BEHAVIOR_")
		ability.damage_type = get_enum_val('AbilityUnitDamageType', "DAMAGE_TYPE_")
		ability.spell_immunity = get_enum_val('SpellImmunityType', "SPELL_IMMUNITY_(ENEMIES|ALLIES)_")
		ability.target_team = get_enum_val('AbilityUnitTargetTeam', "DOTA_UNIT_TARGET_TEAM_")
		ability.dispellable = get_enum_val('SpellDispellableType', "SPELL_DISPELLABLE_")

		ability.json_data = json.dumps(ability_data, indent=4)

		session.add(ability)


	for key in main_data:
		add_ability(key, main_data)

	for root, dirs, files in os.walk(config.vpk_path + DotaPaths.npc_hero_scripts):
		for file in files:
			hero_data = valve_readfile(DotaPaths.npc_hero_scripts + file, "kv")["DOTAAbilities"]
			for key in hero_data:
				add_ability(key, hero_data)
	

	print("- intermediate ability linking")
	# intermedate re-linking and setting of ability metadata
	for ability in session.query(Ability):
		ability_data = json.loads(ability.json_data, object_pairs_hook=OrderedDict)
		abilityvalues = ability_data.get("AbilityValues")
		if abilityvalues:
			for key, valdict in abilityvalues.items():
				if not isinstance(valdict, str):
					for subkey in valdict:
						if subkey.startswith("special_bonus"):
							# this is a talent value we need to link
							value = valdict[subkey]
							value = re.sub(r"(\+|-)", "", value) # clean it up so we dont have duplicate things (the header contains these)

							# special_bonus_facet_drow_ranger_sidestep
							facet = session.query(Facet).filter_by(name=subkey).first()
							facet_prefix = "special_bonus_facet_"
							if subkey.startswith(facet_prefix):
								facet_name = subkey.replace(facet_prefix, "")
								talent = session.query(Facet).filter_by(name=facet_name).first()
							else:
								talent = session.query(Ability).filter_by(name=subkey).first()
							if talent is None:
								if subkey not in [ "special_bonus_scepter", "special_bonus_shard" ]:
									# EXPLANATION: When parsing ability_special/AbilityValues, can't find the right talent/facet to link this upgrade to
									printerr(f"Can't find special_bonus when attempting to link '{ability.name}' '{key}' ('{subkey}')")
								break
							talent_ability_special = json.loads(talent.ability_special, object_pairs_hook=OrderedDict)
							talent_ability_special.append({
								"key": f"bonus_{key}",
								"value": value
							})
							talent.ability_special = json.dumps(talent_ability_special, indent=4)

	print("- loading ability localization files")
	# Load additional information from the ability localization files
	english_data = DotaFiles.abilities_english.read()["lang"]["Tokens"]
	english_data = CaseInsensitiveDict(english_data)
	lang_data = []
	for lang, file in DotaFiles.lang_abilities:
		data = file.read()["lang"]["Tokens"]
		data = CaseInsensitiveDict(data)
		lang_data.append((lang, data))

	progress = ProgressBar(session.query(Ability).count(), title="- loading data from ability localization files")
	for ability in session.query(Ability):
		progress.tick()
		ability_tooltip = "DOTA_Tooltip_ability_" + ability.name

		# do ability_special with just english
		ability_special_value_fixes = {
			"abilityduration": ability.duration
		}
		ability_special = json.loads(ability.ability_special, object_pairs_hook=OrderedDict)
		ability_special = ability_special_add_talent(ability_special, session.query(Ability), ability.name)
		ability_special = ability_special_add_header(ability_special, english_data, ability.name)
		for key in ability_special_value_fixes:
			for special in ability_special:
				if special["key"] == key and special["value"] == "":
					special["value"] = ability_special_value_fixes[key]
		ability.ability_special = json.dumps(ability_special, indent=4)

		# construct replacement dicts
		replacements_dict = build_replacements_dict(ability)
		replacements_dict_scepter = build_replacements_dict(ability, scepter=True)
		replacements_dict_shard = build_replacements_dict(ability, shard=True)

		# language-specific stuff
		for lang, data in lang_data:
			info = {}
			info["localized_name"] = data.get(ability_tooltip, ability.name)
			info["description"] = data.get(ability_tooltip + "_Description", "")
			info["lore"] = data.get(ability_tooltip + "_Lore", "")

			if ability.scepter_upgrades:
				info["scepter_description"] = data.get(ability_tooltip + "_scepter_description", "")
			else:
				info["scepter_description"] = ""
			if ability.shard_upgrades:
				info["shard_description"] = data.get(ability_tooltip + "_shard_description", "")
			else:
				info["shard_description"] = ""

			notes = []
			for i in range(8):
				key = f"{ability_tooltip}_Note{i}"
				if key in data:
					notes.append(data[key])
			info["note"] = "" if len(notes) == 0 else "\n".join(notes)

			is_probably_talent = ability.name.startswith("special_bonus")

			report_errors = lang == "english"

			info["localized_name"] = clean_description(info["localized_name"], replacements_dict, value_bolding=False, report_errors=report_errors and not is_probably_talent)
			info["description"] = clean_description(info["description"], replacements_dict, report_errors=report_errors and not is_probably_talent)
			info["note"] = clean_description(info["note"], replacements_dict, report_errors=report_errors)
			info["scepter_description"] = clean_description(info["scepter_description"], replacements_dict_scepter, report_errors=report_errors)
			info["shard_description"] = clean_description(info["shard_description"], replacements_dict_shard, report_errors=report_errors)

			if lang == "english":
				for key in info:
					setattr(ability, key, info[key])
			else:
				for key in info:
					addLocaleString(session, lang, ability, key, info[key])

		if ability.localized_name.startswith(": "):
			ability.localized_name = ability.localized_name[2:]

		if ability.scepter_grants and ability.scepter_description == "":
			ability.scepter_description = f"Adds new ability: {ability.localized_name}."

		if ability.shard_grants and ability.shard_description == "":
			ability.shard_description = f"Adds new ability: {ability.localized_name}."

		# special case for skywrath who has an innate shard
		if ability.id == 5584:
			ability.shard_description = data.get("DOTA_Tooltip_ability_skywrath_mage_shard_description", "")

	print("- adding ability icon files")
	# Add img files to ability
	for ability in session.query(Ability):
		iconpath = DotaPaths.ability_icon_images + ability.name + "_png.png"
		if os.path.isfile(config.vpk_path + iconpath):
			ability.icon = iconpath
		elif ability.innate:
			ability.icon = "/panorama/images/hud/facets/innate_icon_large_png.png"
		else:
			ability.icon = DotaPaths.ability_icon_images + "attribute_bonus_png.png"
	
	session.query(FacetAbilityString).delete()
	# LOCALIZE FACET STRINGS
	lang_data = []
	facet_ability_string_id_current = 1

	for lang, file in DotaFiles.lang_abilities:
		data = file.read()["lang"]["Tokens"]
		data = CaseInsensitiveDict(data)
		lang_data.append((lang, data))
	
	lang_data.sort(key=lambda x: x[0] != 'english')

	facet_related_keys = []
	for lang, data in lang_data:
		for key in data:
			key = key.lower()
			if "facet" in key and key not in facet_related_keys:
				facet_related_keys.append(key)
	
	facets = session.query(Facet).all()
	progress = ProgressBar(len(facets), title="- localize strings for facets")
	for facet in facets:
		progress.tick()
		replacements_dict = build_replacements_dict_facet(facet)
		abilitystrings_pattern = f"DOTA_Tooltip_ability_(.*)_Facet_{facet.name}"
		abilitystrings_keys = [key.lower() for key in facet_related_keys if re.match(abilitystrings_pattern, key, re.I)]
		abilitystrings_map = {}

		for lang, data in lang_data:
			localized_name = data.get(f"DOTA_Tooltip_facet_{facet.name}", "")
			description = data.get(f"DOTA_Tooltip_facet_{facet.name}_Description", "")

			if localized_name == "":
				localized_name = data.get(f"DOTA_Tooltip_ability_{facet.name}", "")
			if description == "":
				description = data.get(f"DOTA_Tooltip_ability_{facet.name}_Description", "")
			
			description = clean_description(description, replacements_dict, report_errors=(lang == "english"))

			if lang == "english":
				facet.localized_name = localized_name
				facet.description = description
			else:
				addLocaleString(session, lang, facet, "localized_name", localized_name)
				addLocaleString(session, lang, facet, "description", description)
			
			# DO ABILITYSTRINGS STUFF
			for key in abilitystrings_keys:
				if key in data:
					if lang == "english":
						ability_name = re.match(abilitystrings_pattern, key, re.I).group(1)
						ability = session.query(Ability).filter_by(name=ability_name).first()

						if ability is not None:
							newstring = FacetAbilityString()
							newstring.id = facet_ability_string_id_current
							newstring.facet_id = facet.id
							newstring.ability_id = ability.id

							replacements_dict = build_replacements_dict_facetabilitystrings(facet, ability)
							newstring.description = clean_description(data[key], replacements_dict, report_errors=True)
				
							session.add(newstring)
							abilitystrings_map[key] = (newstring, replacements_dict)
							facet_ability_string_id_current += 1
					else:
						if key in abilitystrings_map:
							thestring, replacements_dict = abilitystrings_map[key]
							description = clean_description(data[key], replacements_dict, report_errors=False)
							addLocaleString(session, lang, thestring, "description", description)


	session.commit()