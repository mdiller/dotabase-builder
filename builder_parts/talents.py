from __main__ import session, config, paths
from dotabase import *
from utils import *
import re

# Talent slots appear like this on the tree:

#   7   6
#   5   4
#   3   2
#   1   0

def load():
	session.query(Talent).delete()
	print("Talents")

	link_fixes = {
		"axe_counter_culling_blade": "axe_culling_blade",
		"troll_warlord_whirling_axes": "troll_warlord_whirling_axes_ranged troll_warlord_whirling_axes_melee",
		"invoker_sunstrike": "invoker_sun_strike",
		"morphling_adaptive_strike": "morphling_adaptive_strike_agi morphling_adaptive_strike_str"
	}

	# load all talents from heroes
	talent_names = []
	progress = ProgressBar(session.query(Hero).count(), title="- loading talents from heroes")
	for hero in session.query(Hero):
		# Link abilities and add talents
		progress.tick()
		talent_slot = 0
		hero_data = json.loads(hero.json_data)
		for slot in range(1, 30):
			if "Ability" + str(slot) in hero_data:
				ability = session.query(Ability).filter_by(name=hero_data["Ability" + str(slot)]).first()
				if ability:
					if ability.name.startswith("special_bonus"):
						# create a new talent
						talent = Talent()
						talent.hero_id = hero.id
						talent.ability_id = ability.id
						talent.slot = talent_slot
						talent_names.append(ability.name)
						# link talents
						ability_data = json.loads(ability.json_data)
						ability_specials = ability_data.get("AbilitySpecial", {}).values()
						for special in ability_specials:
							link = special.get("ad_linked_abilities")
							if not link:
								link = ability_data.get("ad_linked_abilities")
							if link:
								if link in [ "special_bonus_inherent" ]:
									continue # doesn't link to a different ability
								if link in link_fixes:
									link = link_fixes[link]
								link = link.replace(" ", "|")
								talent.linked_abilities = link
						session.add(talent)
						talent_slot += 1
		if talent_slot != 8:
			raise ValueError("{} only has {} talents?".format(hero.localized_name, len(talents)))
	
	talent_names = "|".join(talent_names)
	print("- scanning abilities to link them to talents where necessary")
	for ability in session.query(Ability):
		if "AbilityValues" in ability.json_data and re.search(talent_names, ability.json_data):
			ability_data = json.loads(ability.json_data)
			for value in ability_data["AbilityValues"].values():
				if not isinstance(value, str):
					for key in value:
						if re.match(f"^({talent_names})$", key):
							talent_ability = session.query(Ability).filter_by(name=key).first()
							talent = session.query(Talent).filter_by(ability_id=talent_ability.id).first()
							if talent.linked_abilities is None:
								talent.linked_abilities = ability.name
							elif ability.name not in talent.linked_abilities:
								talent.linked_abilities += f"|{ability.name}"
									



	# load ability draft gold talents
	print("- loading ability draft talents")
	for ability in session.query(Ability):
		gold_talent_match = re.match(r"ad_special_bonus_gold_(lvl\d+_.)", ability.name)
		if gold_talent_match:
			talent_slot = [
				"lvl10_l", # note that "l" apparently means right, and "r" apparently means left.
				"lvl10_r",
				"lvl15_l",
				"lvl15_r",
				"lvl20_l",
				"lvl20_r",
				"lvl25_l",
				"lvl25_r"
			].index(gold_talent_match.group(1))
			talent = Talent()
			talent.ability_id = ability.id
			talent.slot = talent_slot
			session.add(talent)

	session.commit()