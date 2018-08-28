import json
import re
import string
import os.path
import collections
from utils import *
from __main__ import config

# Converts valve's obsure and unusable text formats to json
# can do the following formats:
# KV3 (KeyValue)
# response_rules script format

json_cache_dir = "jsoncache"

def tryloadjson(text, strict=True):
	try:
		return json.loads(text, strict=strict, object_pairs_hook=collections.OrderedDict)
	except json.JSONDecodeError as e:
		filename = "jsoncache/errored.json"
		with open(filename, "w+", encoding="utf-16") as f:
			f.write(text)
		print(f"bad converted file saved to: {filename}")

		lines = text.split("\n")
		start = e.lineno - 2
		end = e.lineno + 2
		if start < 0:
			start = 0
		if end > len(lines):
			end = len(lines)
		print("Error parsing this JSON text:\n" + "\n".join(lines[start:end]) + "\n")
		raise

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
	if "<!-- kv3 " not in text:
		return vsndevts_from_old(text)
	# else its a kv3 file

	# get rid of troublesome comments
	text = re.sub(r'<!-- .* -->', "", text)
	# To convert Valve's KeyValue format to Json
	text = re.sub(r'"\n{', r'": {', text)
	text = re.sub(r'(\n\s*)([^\s]+) =', r'\1"\2":', text)
	text = re.sub(r'(]|"|})(\n[\s]*")', r'\1,\2', text)
	text = re.sub(r'",(\n\s*)(]|})', r'"\1\2', text)

	text = re.sub(r'{\s*{([^{}]+)}\s*}', r'{\1}', text)
	text = "{ " + text + " }"
	# To re-include non-functional quotes
	text = re.sub(r'TEMP_QUOTE_TOKEN', '\\"', text)

	return tryloadjson(text, strict=False)

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
	# get rid of troublesome comments
	if remove_comments:
		text = uncommentkvfile(text)
	# To convert Valve's KeyValue format to Json
	text = re.sub('﻿', '', text) # remove zero width no-break space
	text = re.sub(r'"([^"]*)"(\s*){', r'"\1": {', text)
	text = re.sub(r'"([^"]*)"\s*"([^"]*)"', r'"\1": "\2",', text)
	text = re.sub(r',(\s*[}\]])', r'\1', text)
	text = re.sub(r'([}\]])(\s*)("[^"]*":\s*)?([{\[])', r'\1,\2\3\4', text)
	text = re.sub(r'}(\s*"[^"]*":)', r'},\1', text)
	text = "{ " + text + " }"
	# To re-include non-functional quotes
	text = re.sub(r'TEMP_QUOTE_TOKEN', '\\"', text)

	return tryloadjson(text, strict=False)

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

	return tryloadjson(text)

# Loads the response_texts scraped from the wiki as json
def scrapedresponses2json(text):
	text = re.sub(r'"', r'\'', text)
	text = re.sub(r'\t', '', text)
	text = re.sub(r'<!--.*-->', r'', text)
	text = re.sub(r'\* <sm2>', r'\t"', text)
	text = re.sub(r'<sm2>', r'', text)
	text = re.sub(r'\.mp3</sm2> ', r'": "', text)
	text = re.sub(r'\.mp3</sm2>', r'": "', text)
	text = re.sub(r'\\\'', r"'", text)
	text = re.sub(r'\[https[^ ]+ ([^\]]+)]', r'\1', text)
	text = re.sub(r'\[\[File:[^[]+]]', r'', text)
	text = re.sub(r'\[\[[^[\|]+\|([^[]+)]]', r'\1', text)
	text = re.sub(r'\[\[([^[]+)]]', r'\1', text)
	text = re.sub(r'\[', r'', text)
	text = re.sub(r']', r'', text)
	text = re.sub(r'\{.*\} ', r'', text)
	text = re.sub(r'"(.*)": "(.*)": "(.*)\n', r'"\1": "\3\n', text) # Arcana stuff
	text = re.sub(r'"(.*)": "(.*)": "(.*)\n', r'"\1": "\3\n', text) # Multiple Arcana stuff
	text = re.sub(r'\n.*\.wav.*\n', r'\n', text) # No wav files allowed
	text = re.sub(r'\n', '",\n', text)
	text = re.sub(r'<br />', ' ', text)
	text = re.sub(r'<small>[^<]*</small>', r'', text)
	text = re.sub(r'<([^>]+)>', r'*\1*', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)

	# fix the hero identification things
	text = re.sub(r'\'(\d+)\': {",', r'"\1": {', text)

	# custom issues for these 2
	text = re.sub('rick_and_morty_announcer_', 'rick_and_morty_', text, flags=re.IGNORECASE)
	text = re.sub('rick_and_morty_killing_spree_announcer_', 'rick_and_morty_killing_spree_', text, flags=re.IGNORECASE)
	text = re.sub('dlc_cm_', 'cm_ann_', text, flags=re.IGNORECASE)

	data = tryloadjson(text)
	newdata = {}
	for heroid in data:
		herodata = {}
		for key in data[heroid]:
			value = data[heroid][key]
			value = value.strip()
			value = re.sub(r"''(.+)''", r'*\1*', value)
			herodata[key.lower()] = value
		newdata[heroid] = herodata
	return newdata

file_formats = {
	"scrapedresponses": scrapedresponses2json,
	"rules": rulesfile2json,
	"kv": kvfile2json,
	"kv_nocomment": kv_nocommentfile2json,
	"vsndevts": vsndevts2json
}

# Reads from converted json file unless overwrite parameter is specified
def valve_readfile(sourcedir, filepath, fileformat, encoding=None, overwrite=False):
	json_file = os.path.splitext(json_cache_dir + filepath)[0]+'.json'
	vpk_file = sourcedir + filepath

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

	os.makedirs(os.path.dirname(json_file), exist_ok=True)
	write_json(json_file, data)
	return data