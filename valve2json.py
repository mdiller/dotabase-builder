import json
import re
import urllib
import string
import html

# Converts valve's obsure and unusable text formats to json
# can do the following formats:
# KV3 (KeyValue)
# response_rules script format

def unicodetoascii(text):
    TEXT = (text.
    		replace('\\xe2\\x80\\x99', "'").
            replace('\\xc3\\xa9', 'e').
            replace('\\xe2\\x80\\x90', '-').
            replace('\\xe2\\x80\\x91', '-').
            replace('\\xe2\\x80\\x92', '-').
            replace('\\xe2\\x80\\x93', '-').
            replace('\\xe2\\x80\\x94', '-').
            replace('\\xe2\\x80\\x94', '-').
            replace('\\xe2\\x80\\x98', "'").
            replace('\\xe2\\x80\\x9b', "'").
            replace('\\xe2\\x80\\x9c', '"').
            replace('\\xe2\\x80\\x9c', '"').
            replace('\\xe2\\x80\\x9d', '"').
            replace('\\xe2\\x80\\x9e', '"').
            replace('\\xe2\\x80\\x9f', '"').
            replace('\\xe2\\x80\\xa6', '...').#
            replace('\\xe2\\x80\\xb2', "'").
            replace('\\xe2\\x80\\xb3', "'").
            replace('\\xe2\\x80\\xb4', "'").
            replace('\\xe2\\x80\\xb5', "'").
            replace('\\xe2\\x80\\xb6', "'").
            replace('\\xe2\\x80\\xb7', "'").
            replace('\\xe2\\x81\\xba', "+").
            replace('\\xe2\\x81\\xbb', "-").
            replace('\\xe2\\x81\\xbc', "=").
            replace('\\xe2\\x81\\xbd', "(").
            replace('\\xe2\\x81\\xbe', ")"))
    return TEXT

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
def rulesfile2json(filename):
	f = open(filename, 'r')
	text = f.read()
	f.close()

	text = re.sub(r'scene "scenes.*/(.*)\.vcd".*\n', r'"\1",\n', text)
	text = re.sub(r'Response ([^\s]*)\n{([^}]*)}', r'"response_\1": [\2],', text)
	text = re.sub(r'Rule ([^\s]*)\n{([^}]*)}', r'"rule_\1": {\2},', text)
	text = re.sub(r'criteria (.*)\n', r'"criteria": "\1",\n', text)
	text = re.sub(r'response (.*)\n', r'"response": "\1",\n', text)
	text = re.sub(r'criterion.*\n', r'', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)
	text = re.sub(r',(\s*)]', r'\1]', text)

	return json.loads(text)

# Loads the response_texts scraped from the wiki as json
def scrapedresponses2json(filename):
	f = open(filename, 'r')
	text = f.read()
	f.close()

	text = unicodetoascii(text)
	text = html.unescape(text)
	text = re.sub(r'"', r"'", text)
	text = re.sub(r'\* <sm2>', r'\t"', text)
	text = re.sub(r'<sm2>', r'', text)
	text = re.sub(r'\.mp3</sm2> ', r'": "', text)
	text = re.sub(r'\.mp3</sm2>', r'": "', text)
	text = re.sub(r'\\\'', r"'", text)
	text = re.sub(r'\[', r'', text)
	text = re.sub(r']', r'', text)
	text = re.sub(r'\{.*\} ', r'', text)
	text = re.sub(r'"(.*)": "(.*)": "(.*)\n', r'"\1": "\3\n', text) # Arcana stuff
	text = re.sub(r'"(.*)": "(.*)": "(.*)\n', r'"\1": "\3\n', text) # Multiple Arcana stuff
	text = re.sub(r'\n.*\.wav.*\n', r'\n', text) # No wav files allowed
	text = re.sub(r'\n', '",\n', text)
	text = "{" + text + "}"
	text = re.sub(r',(\s*)}', r'\1}', text)

	data = json.loads(text)
	newdata = {}
	for key in data:
		newdata[key.lower()] = data[key]
	return newdata