from importlib.resources import path
import json
import re
import string
import os
import os.path
import collections
from utils import *
import typing

# Converts valve's obsure and unusable text formats to json
# can do the following formats:
# KV3 (KeyValue)
# response_rules script format

json_cache_dir = "jsoncache"
if not os.path.exists(json_cache_dir):
    os.makedirs(json_cache_dir)

def dict_handle_duplicates(ordered_pairs):
	d = collections.OrderedDict()
	for k, v in ordered_pairs:
		original_k = k
		i = 1
		while k in d:
			k = f"{original_k}{i}"
			i += 1
		d[k] = v
	return d

class CustomJsonParsingException(Exception):
	def __init__(self, message):
		self.message = message

def tryloadjson(text, strict=True, parser=None):
	try:
		return json.loads(text, strict=strict, object_pairs_hook=dict_handle_duplicates)
	except json.JSONDecodeError as e:
		filename = "jsoncache/errored.json"
		with open(filename, "w+", encoding="utf-16") as f:
			f.write(text)
		print(f"bad converted file saved to: {filename}")

		lines = text.split("\n")
		start = e.lineno - 4
		end = e.lineno + 4
		if start < 0:
			start = 0
		if end > len(lines):
			end = len(lines)
		if parser:
			print(f"Parser: {parser}()")
		raise CustomJsonParsingException("Error parsing this JSON text:\n" + "\n".join(lines[start:end]) + "\n")

# Redefine with error printing
def read_json(filename):
	with open(filename, 'r') as f:
		text = f.read()
		return tryloadjson(text)

def uncommentkvfile(text):
	in_value = False
	in_comment = False
	result = ""

	for i in range(len(text)):
		if in_comment:
			if text[i] == "\n":
				in_comment = False
				result += text[i]
			continue

		if text[i] == '"':
			in_value = not in_value
			result += text[i]
			continue

		if (not in_value) and text[i] == "/":
			in_comment = True
			continue
		
		result += text[i]

	return result

# converts an old file to the new format
def vsndevts_from_old(text):
	file_data = kvfile2json(text)
	for key in file_data:
		old_data = file_data[key]["operator_stacks"]["update_stack"]["reference_operator"]
		data = OrderedDict()
		data["type"] = old_data["reference_stack"]
		for var in old_data["operator_variables"]:
			value = old_data["operator_variables"][var]["value"]
			if isinstance(value, str):
				data[var] = value
			else:
				value_list = []
				for i in value:
					value_list.append(value[i])
				data[var] = value_list
		file_data[key] = data
	return file_data


def vsndevts2json(text):
	# If this isnt there, its a kv1 file
	# if not (re.match(r'^\{\s*[^\s"]+\s=\s+\{', text) or ("<!-- kv3 " in text)):
	# 	return vsndevts_from_old(text)
	# else its a kv3 file

	# get rid of troublesome comments
	text = re.sub(r'<!-- .* -->', "", text)
	# To convert Valve's KeyValue format to Json
	text = re.sub(r'"\n{', r'": {', text)
	text = re.sub(r'(\n\s*)([^\s]+) =', r'\1"\2":', text)
	text = re.sub(r'(null|]|"|}|\d)(\n[\s]+")', r'\1,\2', text)
	text = re.sub(r'("|\d),(\n\s*)(]|})', r'\1\2\3', text)

	text = re.sub(r'{\s*{([^{}]+)}\s*}', r'{\1}', text)
	if not re.match(r"^\s*\{", text):
		text = "{ " + text + " }"
	# To re-include non-functional quotes
	text = re.sub(r'TEMP_QUOTE_TOKEN', '\\"', text)

	# undo places where we quoted already-quoted stuff:
	text = re.sub(r'(\n\s+")"([^"]+)"(":\s*\n)', r'\1\2\3', text)

	return tryloadjson(text, strict=False, parser="vsndevts2json")

# Regex strings for vk2json from:
# http://dev.dota2.com/showthread.php?t=87191
# Loads a kv file as json
def kv_nocommentfile2json(text):
	return kvfile2json(text, False)

# Regex strings for vk2json from:
# http://dev.dota2.com/showthread.php?t=87191
# Loads a kv file as json
def kvfile2json(text, remove_comments=True):
	# To temporarily hide non-functional quotes
	text = re.sub(r'\\"', 'TEMP_QUOTE_TOKEN', text)
	# remove the null hex char at the end of some files
	text = re.sub(r'\x00$', '', text)
	# fix places where people forgot a closing quote
	text = re.sub(r'(\n\s+"[^"]*"\s*"[^"\n]*)(?=\n\s+"[^\s\n])', r'\1"', text)

	# get rid of troublesome comments
	if remove_comments:
		text = uncommentkvfile(text)
	
	# To convert Valve's KeyValue format to Json
	text = re.sub('﻿', '', text) # remove zero width no-break space
	
	text = re.sub(r'(\n\s+)(value)', r'\1"\2"', text) # fix a thing where some valve employees forgot to put double quotes around the thing
	text = re.sub(r'(?:\n\s*)([a-z_]+)\s*\n\s*{', r'"\1": {', text)
	text = re.sub(r'"([^"]*)"(\s*){', r'"\1": {', text)
	text = re.sub(r'(\n\s+"[^"]*"\s*)([0-9\-]+)(?=\n\s+["}])', r'\1"\2"', text) # fix places where a number doesnt have quotes around it
	text = re.sub(r'"([^"]*)"\s*"([^"]*)"', r'"\1": "\2",', text)
	text = re.sub(r',(\s*[}\]])', r'\1', text)
	text = re.sub(r'([}\]])(\s*)("[^"]*":\s*)?([{\[])', r'\1,\2\3\4', text)
	text = re.sub(r'}(\s*"[^"]*":)', r'},\1', text)
	if not re.match(r"^\s*\{", text):
		text = "{ " + text + " }"

	# cut-off things after closing quotes
	text = re.sub(r'(\n\s+"[^"]*":\s*"[^"\n]*",?\s*)[^,"{}]+\n', r'\1\n', text)

	# ignore dangling quotes
	text = re.sub(r'\n\s*"\s*\n', r'\n', text)

	# uncomment single quotes
	text = re.sub(r"\\'", "'", text)

	# custom fixes because Valve does dum things (this is for when this is just randomly on a line)
	# text = re.sub("and turn rate reduced by %dMODIFIER_PROPERTY_TURN_RATE_PERCENTAGE%%%.", "", text)

	# To re-include non-functional quotes
	text = re.sub(r'TEMP_QUOTE_TOKEN', '\\"', text)

	return tryloadjson(text, strict=False, parser="kvfile2json")

# Loads a response_rules file as json
def rulesfile2json(text):
	text = "\n" + text + "\n"
	text = re.sub(r'\n//[^\n]*', r'\n', text)
	text = re.sub(r'\n#[^\n]*', r'\n', text)

	text = re.sub(r'scene "(.*)".*\n', r'"\1",\n', text)
	text = re.sub(r'"scenes.*/(.*)\.vcd"', r'"\1"', text)
	text = re.sub(r'Response ([^\s]*)\n{([^}]*)}', r'"response_\1": [\2],', text)
	text = re.sub(r'Rule ([^\s]*)\n{([^}]*)}', r'"rule_\1": {\2},', text)
	text = re.sub(r'criteria (.*)\n', r'"criteria": "\1",\n', text)
	text = re.sub(r'response (.*)\n', r'"response": "\1",\n', text)
	text = re.sub(r'criterion\s*"(.*)"\s*"(.*)"\s*"(.*)\n?"(.*)\n', r'"criterion_\1": "\2 \3\4",\n', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)
	text = re.sub(r',(\s*)]', r'\1]', text)

	return tryloadjson(text, parser="rulesfile2json")

class AssetModifier():
	def __init__(self, data):
		self.data = data
		self.type = data.get("type")
		self.asset = data.get("asset")
		self.modifier = data.get("modifier")

# a class that allows easier access to the items_game file
class ItemsGame():
	def __init__(self):
		self.data = DotaFiles.items_game.read()["items_game"]
		self.items = self.data["items"]
		self.item_name_dict = {}
		self.by_prefab = {}
		for key, item in self.items.items():
			item["id"] = key
			self.item_name_dict[item.get("name")] = item
			prefab = item.get("prefab")
			if prefab not in self.by_prefab:
				self.by_prefab[prefab] = []
			self.by_prefab[prefab].append(item)

	def get_asset_modifiers(self, item, asset_type):
		result = []
		for key, data in item.get("visuals", {}).items():
			if not "asset_modifier" in key:
				continue
			elif data.get("type") == asset_type:
				result.append(AssetModifier(data))
		return result

	def get_asset_modifier(self, item, asset_type):
		for key, data in item.get("visuals", {}).items():
			if not "asset_modifier" in key:
				continue
			elif data.get("type") == asset_type:
				return AssetModifier(data)
		return None


# Reads from converted json file unless overwrite parameter is specified
def valve_readfile(filepath, fileformat, encoding=None, overwrite=False) -> dict:
	sourcedir = config.vpk_path
	json_file = os.path.splitext(json_cache_dir + filepath)[0]+'.json'
	vpk_file = sourcedir + filepath

	try:
		if (not (overwrite or config.overwrite_json)) and os.path.isfile(json_file) and (os.path.getmtime(json_file) > os.path.getmtime(vpk_file)):
			with open(json_file, 'r') as f:
				text = f.read()
				return tryloadjson(text)

		if(fileformat in file_formats):
			with open(vpk_file, 'r', encoding=encoding) as f:
				text = f.read()
				data = file_formats[fileformat](text)
		else:
			raise ValueError("invalid fileformat argument: " + fileformat)
	except CustomJsonParsingException as e:
		message = f"Errored loading: {vpk_file}\n" + e.message
		print(message)
		exit(1)

	os.makedirs(os.path.dirname(json_file), exist_ok=True)
	write_json(json_file, data)
	return data

class ValveFile():
	path: str
	format: str
	encoding: str
	def __init__(self, path, format="kv", encoding=None):
		self.path = path
		self.format = format
		self.encoding = encoding
		self.read_data = None
	
	def read(self) -> dict:
		if self.read_data:
			return self.read_data
		else:
			self.read_data = valve_readfile(self.path, self.format, self.encoding)
			return self.read_data

# creates a list of tuples of a given type of lang files
def createLangFiles(dir, pattern) -> typing.List[typing.Tuple[str, ValveFile]]:
	fulldir = config.vpk_path + dir
	files = os.listdir(fulldir)
	files = [f for f in files if os.path.isfile(os.path.join(fulldir, f)) and re.search(pattern, f)]
	results = []
	for file in files:
		match = re.search(pattern, file)
		lang = match.group(1)
		new_tuple = (
			lang,
			ValveFile(dir + file, encoding="UTF-8")
		)
		if lang == "english":
			results.insert(0, new_tuple)
		else:
			results.append(new_tuple)
	
	return results

file_formats = {
	"kv": kvfile2json,
	"rules": rulesfile2json,
	"kv_nocomment": kv_nocommentfile2json,
	"vsndevts": vsndevts2json
}

class DotaFiles():
	npc_ids = ValveFile("/scripts/npc/npc_ability_ids.txt")
	npc_abilities = ValveFile("/scripts/npc/npc_abilities.txt")
	npc_heroes = ValveFile("/scripts/npc/npc_heroes.txt")
	items = ValveFile("/scripts/npc/items.txt")
	neutral_items = ValveFile("/scripts/npc/neutral_items.txt")
	emoticons = ValveFile("/scripts/emoticons.txt", encoding="UTF-16")
	chat_wheel = ValveFile("/scripts/chat_wheel.txt", encoding="utf-8")
	chat_wheel_categories = ValveFile("/scripts/chat_wheel_categories.txt", encoding="utf-8")
	chat_wheel_heroes = ValveFile("/scripts/chat_wheel_heroes.txt", encoding="utf-8")
	game_sounds_vsndevts = ValveFile("/soundevents/game_sounds.vsndevts", "vsndevts")
	dota_english = ValveFile("/resource/localization/dota_english.txt", encoding="UTF-8")
	items_game = ValveFile("/scripts/items/items_game.txt", "kv_nocomment", encoding="UTF-8")
	hero_lore_english = ValveFile("/resource/localization/hero_lore_english.txt", encoding="utf-8")
	abilities_english = ValveFile("/resource/localization/abilities_english.txt", encoding="UTF-8")
	teamfandom_english = ValveFile("/resource/localization/teamfandom_english.txt", encoding="utf-8")
	
	lang_abilities = createLangFiles("/resource/localization/", r"abilities_(.*)\.txt")
	lang_hero_lore = createLangFiles("/resource/localization/", r"hero_lore_(.*)\.txt")
	lang_dota = createLangFiles("/resource/localization/", r"dota_(.*)\.txt")

class DotaPaths():
	response_mp3s = "/sounds/vo/"
	item_images = "/panorama/images/items/"
	ability_icon_images = "/panorama/images/spellicons/"
	hero_side_images = "/panorama/images/heroes/"
	hero_icon_images = "/panorama/images/heroes/icons/"
	facet_icon_images = "/panorama/images/hud/facets/icons/"
	hero_selection_images = "/panorama/images/heroes/selection/"
	emoticon_images = "/panorama/images/emoticons/"
	response_rules = "/scripts/talker/"
	npc_hero_scripts = "/scripts/npc/heroes/"


