import json
import re

# Converts valve's obsure and unusable text formats to json
# can do the following formats:
# KV3 (KeyValue)
# response_rules script format


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

# Loads a response_rules file as json
def rules2json(filename):
	f = open(filename, 'r')
	text = f.read()
	f.close()

	text = re.sub(r'scene "scenes(.*)vcd".*\n', r'"sounds/vo\1mp3",\n', text)
	text = re.sub(r'Response ([^\s]*)\n{([^}]*)}', r'"response_\1": [\2],', text)
	text = re.sub(r'Rule ([^\s]*)\n{([^}]*)}', r'"rule_\1": {\2},', text)
	text = re.sub(r'criteria (.*)\n', r'"criteria": "\1",\n', text)
	text = re.sub(r'response (.*)\n', r'"response": "\1",\n', text)
	text = re.sub(r'criterion.*\n', r'', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)
	text = re.sub(r',(\s*)]', r'\1]', text)

	return json.loads(text)