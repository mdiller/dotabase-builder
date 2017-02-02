from valve2json import valve_readfile, read_json
from dotabase import *
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
def get_special_pretty_crit_dict(session):
	replace_dict = {}
	for hero in session.query(Hero):
		replace_dict[hero.full_name] = hero.localized_name

	for ability in session.query(Ability):
		replace_dict[ability.name] = ability.localized_name

	for item in session.query(Item):
		replace_dict[item.name] = "a " + item.localized_name

	replace_dict.update({
		"DOTA_RUNE_ARCANE": "an arcane rune",
		"DOTA_RUNE_DOUBLEDAMAGE": "a double damage rune",
		"DOTA_RUNE_REGENERATION": "a regeneration rune",
		"DOTA_RUNE_BOUNTY": "a bounty rune",
		"DOTA_RUNE_HASTE": "a haste rune",
		"DOTA_RUNE_ILLUSION": "an illusion rune",
		"DOTA_RUNE_INVISIBILITY": "an invisibility rune"
		})

	pretty_dict = {}
	for match in replace_dict:
		for crit in session.query(Criterion).filter_by(matchvalue=match):
			pretty_dict[crit.name] = replace_dict[match] if crit.matchkey != "classname" else ""
	return pretty_dict


def get_pretty_crit_dict(session):
	pretty_dict = read_json("builderdata/criteria_pretty.json")

	for crit in session.query(Criterion).filter(Criterion.name.like("Chance_%")):
		pretty_dict[crit.name] = "({} chance)".format(crit.name[7:])

	for crit in session.query(Criterion).filter_by(matchkey="gametime"):
		pretty_dict[crit.name] = "and the game is {} in".format(pretty_time(crit.matchvalue))

	for crit in session.query(Criterion).filter_by(matchkey="drop_type"):
		pretty_dict[crit.name] = "of type {}".format(crit.matchvalue)

	for crit in session.query(Criterion).filter_by(matchkey="lane"):
		pretty_dict[crit.name] = "from {} lane".format({
			"mid": "middle",
			"bot": "bottom",
			"top": "top"
			}[crit.matchvalue.lower()])

	pretty_dict["LittleNag"] = ""
	pretty_dict["MediumNag"] = "(medium naggy)"
	pretty_dict["SuperNag"] = "(very naggy)"

	for crit in session.query(Criterion).filter_by(matchkey="customresponse"):
		pretty_dict[crit.name] = "(using the '{}' cosmetic)".format(crit.matchvalue)

	return pretty_dict

def to_pretty_criteria(crits):
	crits = crits.split(" ")
	postfixes = re.compile(" (a rune|a hero|an ability|an item|a lane)$")
	i = 0
	while i < len(crits):
		if crits[i] in pretty_dict:
			crits[i] = pretty_dict[crits[i]]
		elif crits[i] in special_pretty_dict:
			crits[i] = special_pretty_dict[crits[i]]
			if crits[0] == pretty_dict["AllyNear"]:
				crits[0] = "{} is nearby".format(crits[i])
				crits[i] = ""
			if crits[i] != "":
				crits[0] = re.sub(postfixes, "", crits[0])

		if crits[i] == "":
			crits.pop(i) # Indicates to remove this from pretty list
			continue
		i += 1
	return " ".join(crits)


def get_pretty_crit(crit_name):
	return pretty_dict.get(crit_name, special_pretty_dict.get(crit_name))

def get_response_pretty_crit(response_crit):
	if response_crit == "" or response_crit is None:
		return "Unused"
	else:
		return "\n".join([to_pretty_criteria(c) for c in response_crit.split("|")])

def init_pretty_dicts(session):
	global pretty_dict
	global special_pretty_dict
	# This stuff in the main function
	pretty_dict = get_pretty_crit_dict(session)
	special_pretty_dict = get_special_pretty_crit_dict(session)

