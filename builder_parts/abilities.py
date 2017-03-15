from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile


def load():
	session.query(Ability).delete()
	print("Abilities")

	print("- loading abilities from ability scripts")
	# load all of the ability scripts data information
	data = valve_readfile(config.vpk_path, paths['ability_scripts_file'], "kv")["DOTAAbilities"]
	for abilityname in data:
		if(abilityname == "Version" or
			abilityname == "ability_deward"):
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
		ability.id = ability_data['ID']
		ability.type = get_val('AbilityType', default_base=True)
		ability.behavior = get_val('AbilityBehavior', default_base=True)
		ability.cast_range = get_val('AbilityCastRange')
		ability.cast_point = get_val('AbilityCastPoint')
		ability.channel_time = get_val('AbilityChannelTime')
		ability.cooldown = get_val('AbilityCooldown')
		ability.duration = get_val('AbilityDuration')
		ability.damage = get_val('AbilityDamage')
		ability.mana_cost = get_val('AbilityManaCost')

		ability.json_data = json.dumps(ability_data, indent=4)

		session.add(ability)

	print("- loading ability data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(config.vpk_path, paths['dota_english_file'], "kv", encoding="UTF-16")["lang"]["Tokens"]
	for ability in session.query(Ability):
		ability_tooltip = "DOTA_Tooltip_ability_" + ability.name 
		ability.localized_name = data.get(ability_tooltip, ability.name)
		ability.description = data.get(ability_tooltip + "_Description", "")
		ability.lore = data.get(ability_tooltip + "_Lore", "")
		notes = []
		for i in range(8):
			key = f"{ability_tooltip}_Note{i}"
			if key in data:
				notes.append(data[key])
		ability.note = "" if len(notes) == 0 else "\n".join(notes)

	print("- adding ability icon files")
	# Add img files to ability
	for ability in session.query(Ability):
		if os.path.isfile(config.vpk_path + paths['ability_icon_path'] + ability.name + ".png"):
			ability.icon = paths['ability_icon_path'] + ability.name + ".png"
		else:
			ability.icon = paths['ability_icon_path'] + "wisp_empty1.png"

	session.commit()