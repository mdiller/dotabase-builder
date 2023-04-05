from builder import session
from dotabase import *
from utils import *
from valve2json import DotaFiles, DotaPaths
import re

attribute_dict = {
	"DOTA_ATTRIBUTE_STRENGTH": "strength",
	"DOTA_ATTRIBUTE_AGILITY": "agility",
	"DOTA_ATTRIBUTE_INTELLECT": "intelligence"
}

def load():
	session.query(Hero).delete()
	print("Heroes")

	# load all of the hero scripts data information
	data = DotaFiles.npc_heroes.read()["DOTAHeroes"]
	progress = ProgressBar(len(data), title="- loading from hero scripts")
	for heroname in data:
		progress.tick()
		if(heroname == "Version" or
			heroname == "npc_dota_hero_target_dummy" or
			heroname == "npc_dota_hero_base"):
			continue

		hero = Hero()
		hero_data = data[heroname]

		def get_val(key):
			if key in hero_data:
				return hero_data[key]
			else:
				return data["npc_dota_hero_base"].get(key)

		hero.full_name = heroname
		hero.media_name = hero_data['VoiceFile'][37:-9]
		hero.name = heroname.replace("npc_dota_hero_", "")
		hero.id = get_val('HeroID')
		hero.team = get_val('Team')
		hero.base_health_regen = get_val('StatusHealthRegen')
		hero.base_mana_regen = get_val('StatusManaRegen')
		hero.base_movement = get_val('MovementSpeed')
		hero.base_attack_speed = get_val('BaseAttackSpeed')
		hero.turn_rate = get_val('MovementTurnRate')
		hero.base_armor = get_val('ArmorPhysical')
		hero.magic_resistance = get_val('MagicalResistance')
		hero.attack_range = get_val('AttackRange')
		hero.attack_projectile_speed = get_val('ProjectileSpeed')
		hero.attack_damage_min = get_val('AttackDamageMin')
		hero.attack_damage_max = get_val('AttackDamageMax')
		hero.attack_rate = get_val('AttackRate')
		hero.attack_point = get_val('AttackAnimationPoint')
		hero.attr_primary = attribute_dict[get_val('AttributePrimary')]
		hero.attr_strength_base = get_val('AttributeBaseStrength')
		hero.attr_strength_gain = get_val('AttributeStrengthGain')
		hero.attr_intelligence_base = get_val('AttributeBaseIntelligence')
		hero.attr_intelligence_gain = get_val('AttributeIntelligenceGain')
		hero.attr_agility_base = get_val('AttributeBaseAgility')
		hero.attr_agility_gain = get_val('AttributeAgilityGain')
		hero.vision_day = get_val('VisionDaytimeRange')
		hero.vision_night = get_val('VisionNighttimeRange')
		hero.is_melee = get_val('AttackCapabilities') == "DOTA_UNIT_CAP_MELEE_ATTACK"
		hero.material = get_val('GibType')
		hero.legs = get_val('Legs')
		hero.roles = hero_data.get('Role', '').replace(',', '|')
		hero.role_levels = hero_data.get('Rolelevels', '').replace(',', '|')
		glow_color = hero_data.get('HeroGlowColor', None)
		hero.color = "#ffffff" # should have a default color
		if glow_color:
			hero.color = "#{0:02x}{1:02x}{2:02x}".format(*map(int, glow_color.split(' ')))

		hero.json_data = json.dumps(hero_data, indent=4)

		talents = []

		# Link abilities
		for slot in range(1, 30):
			if "Ability" + str(slot) in hero_data:
				ability = session.query(Ability).filter_by(name=hero_data["Ability" + str(slot)]).first()
				if ability:
					if not ability.name.startswith("special_bonus"):
						ability.hero_id = hero.id
						ability.slot = slot

		session.add(hero)


	print("- loading hero names from dota_lang files")
	# Load hero names from dota_english file
	lang_data = DotaFiles.lang_dota
	for hero in session.query(Hero):
		for lang, data in lang_data:
			data = data.read()["lang"]["Tokens"]
			hero_full_name = hero.full_name + ":n"
			
			localized_name = data.get(hero_full_name, "")
			localized_name = re.sub(r"#\|[fm]\|#", "", localized_name)
			hype = clean_description(data.get(hero.full_name + "_hype"))
			if lang == "english":
				hero.localized_name = localized_name
				hero.hype = hype
			else:
				addLocaleString(session, lang, hero, "localized_name", localized_name)
				addLocaleString(session, lang, hero, "hype", hype)


	print("- loading bio from hero lore files")
	# Load bio from hero lore file
	lang_data = DotaFiles.lang_hero_lore
	for hero in session.query(Hero):
		for lang, data in lang_data:
			data = data.read()["lang"]["Tokens"]
			bio = clean_description(data.get(hero.full_name + "_bio"))
			if lang == "english":
				hero.bio = bio
			else:
				addLocaleString(session, lang, hero, "bio", bio)
	

	print("- adding hero image files")
	# Add img files to hero
	for hero in session.query(Hero):
		file_ending = hero.full_name + "_png.png"
		hero.icon = DotaPaths.hero_icon_images + file_ending
		hero.image = DotaPaths.hero_side_images + file_ending
		hero.portrait = DotaPaths.hero_selection_images + file_ending

	print("- adding hero real names")
	data = read_json("builderdata/hero_names.json")
	for hero in session.query(Hero):
		hero.real_name = data.get(hero.name, "")

	print("- adding hero aliases")
	data = read_json("builderdata/hero_aliases.json")
	for hero in session.query(Hero):
		aliases = []
		aliases.append(hero.name.replace("_", " "))
		text = re.sub(r'[^a-z^\s]', r'', hero.localized_name.replace("_", " ").lower())
		if text not in aliases:
			aliases.append(text)
		if hero.real_name != "":
			aliases.append(re.sub(r'[^a-z^\s]', r'', hero.real_name.lower()))
		aliases.extend(data.get(hero.name, []))
		hero.aliases = "|".join(aliases)

	print("- adding hero colors")
	data = read_json("builderdata/hero_colors.json")
	for hero_name in data:
		hero = session.query(Hero).filter_by(name=hero_name).first()
		hero.color = data[hero_name]



	session.commit()
