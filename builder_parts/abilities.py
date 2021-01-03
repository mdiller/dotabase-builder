from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile
import re

def build_replacements_dict(ability, aghanim=False):
	specials = json.loads(ability.ability_special, object_pairs_hook=OrderedDict)
	result = {
		"abilityduration": ability.duration,
		"abilitychanneltime": ability.channel_time,
		"abilitycastpoint": ability.cast_point,
		"abilitycastrange": ability.cast_range,
		"abilitychargerestoretime": ability.cooldown,
		"charge_restore_time": ability.cooldown,
		"max_charges": ability.charges
	}
	for attrib in specials:
		is_aghs_upgrade = attrib.get("aghs_upgrade") == "1" and not ability.scepter_grants
		if is_aghs_upgrade and not aghanim:
			continue
		if (attrib["key"] not in result) or is_aghs_upgrade:
			result[attrib["key"]] = attrib["value"]
	return result

def load():
	session.query(Ability).delete()
	print("Abilities")

	added_ids = []

	print("- loading abilities from ability scripts")
	# load all of the ability scripts data information
	data = valve_readfile(config.vpk_path, paths['ability_scripts_file'], "kv")["DOTAAbilities"]
	for abilityname in data:
		if(abilityname == "Version" or
			abilityname == "ability_deward" or
			abilityname == "dota_base_ability" or
			not data[abilityname]['ID'].isdigit()):
			continue

		ability_data = data[abilityname]
		ability = Ability()

		def get_val(key, default_base=False):
			if key in ability_data:
				val = ability_data[key]
				if ' ' in val and all(x == val.split(' ')[0] for x in val.split(' ')):
					return val.split(' ')[0]
				return val
			elif default_base:
				return data["ability_base"][key]
			else:
				return None

		ability.name = abilityname
		ability.id = int(ability_data['ID'])
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
		ability.mana_cost = clean_values(get_val('AbilityManaCost'))
		ability.ability_special = json.dumps(get_ability_special(ability_data.get("AbilitySpecial"), abilityname), indent=4)
		ability.scepter_grants = get_val("IsGrantedByScepter") == "1"
		ability.shard_grants = get_val("IsGrantedByShard") == "1"
		ability.scepter_description = get_val("HasScepterUpgrade")
		ability.shard_description = get_val("HasShardUpgrade")


		if ability.id in added_ids:
			print_error(f"duplicate id on: {abilityname}")
			continue
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

	print("- loading ability data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(config.vpk_path, paths['localization_abilities'], "kv", encoding="UTF-8")["lang"]["Tokens"]
	data = CaseInsensitiveDict(data)
	for ability in session.query(Ability):
		ability_tooltip = "DOTA_Tooltip_ability_" + ability.name 
		ability.localized_name = data.get(ability_tooltip, ability.name)
		ability.description = data.get(ability_tooltip + "_Description", "")
		ability.lore = data.get(ability_tooltip + "_Lore", "")
		if ability.scepter_description == "1":
			ability.scepter_description = data.get(ability_tooltip + "_scepter_description", "")
		else:
			ability.scepter_description = ""
		if ability.shard_description == "1":
			ability.shard_description = data.get(ability_tooltip + "_shard_description", "")
		else:
			ability.shard_description = ""

		notes = []
		for i in range(8):
			key = f"{ability_tooltip}_Note{i}"
			if key in data:
				notes.append(data[key])
		ability.note = "" if len(notes) == 0 else "\n".join(notes)

		ability_special = json.loads(ability.ability_special, object_pairs_hook=OrderedDict)
		ability_special = ability_special_add_talent(ability_special, session.query(Ability))
		ability_special = ability_special_add_header(ability_special, data, ability.name)
		ability.ability_special = json.dumps(ability_special, indent=4)

		replacements_dict = build_replacements_dict(ability)
		ability.localized_name = clean_description(ability.localized_name, replacements_dict, value_bolding=False)
		ability.description = clean_description(ability.description, replacements_dict)
		ability.note = clean_description(ability.note, replacements_dict)
		replacements_dict = build_replacements_dict(ability, aghanim=True)
		ability.scepter_description = clean_description(ability.scepter_description, replacements_dict)
		ability.shard_description = clean_description(ability.shard_description, replacements_dict)

		if ability.localized_name.startswith(": "):
			ability.localized_name = ability.localized_name[2:]

		if ability.scepter_grants and ability.scepter_description == "":
			ability.scepter_description = f"Adds new ability: {ability.localized_name}."

		if ability.shard_grants and ability.shard_description == "":
			ability.shard_description = f"Adds new ability: {ability.localized_name}."

	print("- adding ability icon files")
	# Add img files to ability
	for ability in session.query(Ability):
		iconpath = paths['ability_icon_path'] + ability.name + "_png.png"
		if os.path.isfile(config.vpk_path + iconpath):
			ability.icon = iconpath
		else:
			ability.icon = paths['ability_icon_path'] + "attribute_bonus_png.png"

	session.commit()