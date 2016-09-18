import json
import re

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

def kvfile2json(filename):
	f = open(filename, 'r', encoding="UTF8")
	text = f.read()
	f.close()

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

	return json.loads(text, strict=False)