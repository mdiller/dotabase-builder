import json
import re
import string
import os.path
import collections

# Converts valve's obsure and unusable text formats to json
# can do the following formats:
# KV3 (KeyValue)
# response_rules script format

json_cache_dir = "jsoncache"

def tryloadjson(text, strict=True):
	try:
		return json.loads(text, strict=strict, object_pairs_hook=collections.OrderedDict)
	except json.JSONDecodeError as e:
		lines = text.split("\n")
		start = e.lineno - 2
		end = e.lineno + 2
		if start < 0:
			start = 0
		if end > len(lines):
			end = len(lines)
		print("Error parsing this JSON text:\n" + "\n".join(lines[start:end]) + "\n")
		raise

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

# Regex strings for vk2json from:
# http://dev.dota2.com/showthread.php?t=87191
# Loads a kv file as json
def kvfile2json(filename):
	with open(filename, 'r', encoding="UTF16") as f:
		text = f.read()

	# To fix html quotes in values
	text = re.sub(r'\\"', 'QUOTE', text)
	# get rid of troublesome comments
	text = uncommentkvfile(text)
	# To convert Valve's KeyValue format to Json
	text = re.sub(r'"([^"]*)"(\s*){', r'"\1": {', text)
	text = re.sub(r'"([^"]*)"\s*"([^"]*)"', r'"\1": "\2",', text)
	text = re.sub(r',(\s*[}\]])', r'\1', text)
	text = re.sub(r'([}\]])(\s*)("[^"]*":\s*)?([{\[])', r'\1,\2\3\4', text)
	text = re.sub(r'}(\s*"[^"]*":)', r'},\1', text)
	text = "{ " + text + " }"

	return tryloadjson(text, strict=False)

# Loads a response_rules file as json
def rulesfile2json(filename):
	with open(filename, 'r') as f:
		text = f.read()

	text = "\n" + text + "\n"
	text = re.sub(r'\n//[^\n]*', r'\n', text)
	text = re.sub(r'\n#[^\n]*', r'\n', text)

	text = re.sub(r'scene "(.*)".*\n', r'"\1",\n', text)
	text = re.sub(r'"scenes.*/(.*)\.vcd"', r'"\1"', text)
	text = re.sub(r'Response ([^\s]*)\n{([^}]*)}', r'"response_\1": [\2],', text)
	text = re.sub(r'Rule ([^\s]*)\n{([^}]*)}', r'"rule_\1": {\2},', text)
	text = re.sub(r'criteria (.*)\n', r'"criteria": "\1",\n', text)
	text = re.sub(r'response (.*)\n', r'"response": "\1",\n', text)
	text = re.sub(r'criterion\s*"(.*)"\s*"(.*)"\s*"(.*)"(.*)\n', r'"criterion_\1": "\2 \3\4",\n', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)
	text = re.sub(r',(\s*)]', r'\1]', text)

	return tryloadjson(text)

# Loads the response_texts scraped from the wiki as json
def scrapedresponses2json(filename):
	with open(filename, 'r') as f:
		text = f.read()

	text = re.sub(r'"', r"'", text)
	text = re.sub(r'\* <sm2>', r'\t"', text)
	text = re.sub(r'<sm2>', r'', text)
	text = re.sub(r'\.mp3</sm2> ', r'": "', text)
	text = re.sub(r'\.mp3</sm2>', r'": "', text)
	text = re.sub(r'\\\'', r"'", text)
	text = re.sub(r'\[\[[^[]+]]', r'', text)
	text = re.sub(r'\[', r'', text)
	text = re.sub(r']', r'', text)
	text = re.sub(r'\{.*\} ', r'', text)
	text = re.sub(r'"(.*)": "(.*)": "(.*)\n', r'"\1": "\3\n', text) # Arcana stuff
	text = re.sub(r'"(.*)": "(.*)": "(.*)\n', r'"\1": "\3\n', text) # Multiple Arcana stuff
	text = re.sub(r'\n.*\.wav.*\n', r'\n', text) # No wav files allowed
	text = re.sub(r'\n', '",\n', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)

	data = tryloadjson(text)
	newdata = {}
	for key in data:
		newdata[key.lower()] = data[key]
	return newdata

def read_json(filename):
	with open(filename, 'r') as f:
		text = f.read()
		return tryloadjson(text)

file_formats = {
	"scrapedresponses": scrapedresponses2json,
	"rules": rulesfile2json,
	"kv": kvfile2json
}

# Reads from converted json file unless overwrite parameter is specified
def valve_readfile(sourcedir, filepath, fileformat, overwrite=False):
	json_file = os.path.splitext(json_cache_dir + filepath)[0]+'.json'
	vpk_file = sourcedir + filepath

	if ((not overwrite) and os.path.isfile(json_file) and (os.path.getmtime(json_file) > os.path.getmtime(vpk_file))):
		with open(json_file, 'r') as f:
			text = f.read()
			return tryloadjson(text)

	if(fileformat in file_formats):
		data = file_formats[fileformat](vpk_file)
	else:
		raise ValueError("invalid fileformat argument: " + fileformat)


	os.makedirs(os.path.dirname(json_file), exist_ok=True)
	with open(json_file, 'w+') as f:
		json.dump(data, f, indent='\t')
	return data