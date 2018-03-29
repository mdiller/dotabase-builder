from valve2json import valve_readfile, read_json
from dotabase import *
from sqlalchemy import func
import re


def pretty_time(time):
	if "," in time:
		return "between {} and {}".format(pretty_time(time.split(",")[0][1:]), pretty_time(time.split(",")[1][1:]))
	if time.startswith("<"):
		return "less than {}".format(pretty_time(time[1:]))
	if time.startswith(">"):
		return "more than {}".format(pretty_time(time[1:]))
	seconds = int(time)
	if seconds < 60:
		return "{} seconds".format(seconds)
	elif seconds == 60:
		return "1 minute"
	elif seconds < 3600:
		return "{} minutes".format(seconds // 60)
	elif seconds == 3600:
		return "1 hour"
	else:
		return "{} hour and {} minutes".format(seconds // 3600, (seconds % 3600) // 60)


# pretty criteria which alters the first criteria in the list
def build_dictionaries(session):
	global pretty_dict
	global crit_type_dict
	pretty_dict = read_json("builderdata/criteria_pretty.json")
	crit_type_dict = {}

	replace_dict = {}
	replace_type_dict = {}
	for hero in session.query(Hero):
		replace_dict[hero.full_name] = hero.localized_name
		replace_type_dict[hero.full_name] = "hero"

	for ability in session.query(Ability):
		replace_dict[ability.name] = ability.localized_name
		replace_type_dict[ability.name] = "ability"

	for item in session.query(Item):
		replace_dict[item.name] = item.localized_name
		replace_type_dict[item.name] = "item"

	replace_dict.update({
		"DOTA_RUNE_ARCANE": "an arcane rune",
		"DOTA_RUNE_DOUBLEDAMAGE": "a double damage rune",
		"DOTA_RUNE_REGENERATION": "a regeneration rune",
		"DOTA_RUNE_BOUNTY": "a bounty rune",
		"DOTA_RUNE_HASTE": "a haste rune",
		"DOTA_RUNE_ILLUSION": "an illusion rune",
		"DOTA_RUNE_INVISIBILITY": "an invisibility rune"
		})
	for key in replace_dict:
		if key.startswith("DOTA_RUNE"):
			replace_type_dict[key] = "rune"

	for match in replace_dict:
		for crit in session.query(Criterion).filter(func.lower(Criterion.matchvalue) == func.lower(match)):
			pretty_dict[crit.name] = replace_dict[match]
			crit_type_dict[crit.name] = replace_type_dict.get(match)
			if crit.matchkey == "stolenspell":
				pretty_dict[crit.name] = "and stealing " + replace_dict[match]
				crit_type_dict[crit.name] = "stolenspell"

	ignore_matchkeys = [ "classname", "announcer_voice", "taunt_type", "spectator", "player_team", "special_spawn", "customresponse" ]
	for key in ignore_matchkeys:
		for crit in session.query(Criterion).filter_by(matchkey=key):
			pretty_dict[crit.name] = ""
			crit_type_dict[crit.name] = None

	for crit in session.query(Criterion).filter(Criterion.name.like("Chance_%")):
		pretty_dict[crit.name] = f"{crit.name[7:]} chance"
		crit_type_dict[crit.name] = "chance"

	for crit in session.query(Criterion).filter_by(matchkey="gametime"):
		pretty_dict[crit.name] = f"at {pretty_time(crit.matchvalue)} in"
		crit_type_dict[crit.name] = "gametime"

	pretty_matchkeys = read_json("builderdata/criteria_matchkeys.json")
	for matchkey in pretty_matchkeys:
		for crit in session.query(Criterion).filter_by(matchkey=matchkey["key"]):
			template = matchkey.get("template", "{}")
			value = crit.matchvalue
			if "convert" in matchkey:
				if crit.matchvalue.lower() in matchkey["convert"]:
					value = matchkey["convert"][crit.matchvalue.lower()]
				else:
					print(f"Missing key '{crit.matchvalue}' for matchkey '{crit.matchkey}'")
			pretty_dict[crit.name] = template.format(value)
			crit_type_dict[crit.name] = matchkey.get("new_key", matchkey["key"])


	pretty_dict = {k.lower():v for k, v in pretty_dict.items()}
	crit_type_dict = {k.lower():v for k, v in crit_type_dict.items()}

def replace_template(template, crit_list):
	pattern = re.compile(r"\{([^\{]*?)\|([^\{]*?)\|([^\{]*?)\}")
	match = pattern.search(template)

	while match:
		replacement = match.group(2)
		for i in range(len(crit_list)):
			if crit_type_dict.get(crit_list[i].lower()) == match.group(1) and pretty_dict[crit_list[i].lower()] != "":
				replacement = match.group(3).replace("%", pretty_dict[crit_list[i].lower()])
				crit_list.pop(i)
				break
		
		template = re.sub(pattern, replacement, template, count=1)
		match = pattern.search(template)

	return template

def pretty_response_crit(crits):
	def is_significant(crit):
		if (crit == "Custom" or crit.startswith("Followup")):
			return False
		if pretty_dict.get(crit.lower()) == "":
			return False
		return True

	crits = crits.split(" ")

	result = None
	for i in range(len(crits)):
		if is_significant(crits[i]):
			result = crits.pop(i)
			break
	if not result:
		result = crits.pop(0)

	result = pretty_dict.get(result.lower(), result)

	result = replace_template(result, crits)
	ending = replace_template("{gametime|| %}{nag|| (%)}{chance|| (%)}", crits)

	for crit in crits:
		temp = pretty_dict.get(crit.lower(), crit)
		if temp != "":
			result += " " + temp

	result += ending
	return result


def load_pretty_criteria(session):
	build_dictionaries(session)

	for criterion in session.query(Criterion):
		criterion.pretty = replace_template(pretty_dict.get(criterion.name.lower(), criterion.name), [])
	for response in session.query(Response):
		if response.criteria == "" or response.criteria is None:
			response.pretty_criteria = "Unused"
		else:
			crits = [pretty_response_crit(c) for c in response.criteria.split("|")]
			while "" in crits:
				crits.remove("")
			if len(crits) == 0:
				crits.append("Unused")
			response.pretty_criteria = "|".join(crits)

