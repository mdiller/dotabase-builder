from builder import session
from dotabase import *
from utils import *
from valve2json import DotaFiles, DotaPaths


def load():
	session.query(Facet).delete()
	print("Facets")

	current_id = 1

	# load all of the item scripts data information
	data = DotaFiles.npc_heroes.read()["DOTAHeroes"]
	progress = ProgressBar(len(data), title="- loading from hero scripts")
	for heroname in data:
		progress.tick()
		if(heroname == "Version" or
			heroname == "npc_dota_hero_target_dummy" or
			heroname == "npc_dota_hero_base"):
			continue

		hero_data = data[heroname]

		if "Facets" not in hero_data:
			continue

		slot = 0
		for facetname in hero_data["Facets"]:
			facet_data = hero_data["Facets"][facetname]

			facet = Facet()

			facet.id = current_id
			facet.name = facetname
			# facet.hero_id = ""
			facet.icon_name = facet_data["Icon"]
			facet.icon = DotaPaths.facet_icon_images + facet.icon_name + "_png.png"
			facet.color = facet_data["Color"]
			facet.gradient_id = int(facet_data.get("GradientID", 0))
			facet.slot = slot

			facet.ability_special = "[]"
			facet.json_data = json.dumps(facet_data, indent=4)

			session.add(facet)
			current_id += 1
			slot += 1

	# abilities_english
	# DOTA_Tooltip_Facet_drow_ranger_sidestep (name)
	# DOTA_Tooltip_ability_drow_ranger_multishot_Facet_drow_ranger_sidestep (description/bullet on a related ability)
	# DOTA_Tooltip_Facet_drow_ranger_vantage_point_Description (description)
	# DOTA_Tooltip_ability_vengefulspirit_soul_strike_bat_tooltip (BASE ATTACK TIME: xx)
	# "DOTA_Tooltip_ability_abaddon_the_quickening_Note0": "Every time a unit dies within %radius% range of Abaddon, reduce all of his Cooldowns by %cooldown_reduction_creeps% seconds if they are a creep or %cooldown_reduction_heroes% seconds if they are a hero.",
	# "DOTA_Tooltip_facet_alchemist_seed_money_Description": "Alchemist starts with {s:bonus_starting_gold_bonus} more gold.",

	# string localization for facets done in abilities.py cuz we need our ability_special stuff filled in

	session.commit()
