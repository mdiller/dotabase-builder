import re
import json

# http://dev.dota2.com/showthread.php?t=87191

replacement_dict = {
	# removing comments
	r'//(.*)\n': '\n',
	# converting to json
	r'"([^"]*)"(\s*){': r'"\1": {',
	r'"([^"]*)"\s*"([^"]*)"': r'"\1": "\2",',
	r',(\s*[}\]])': r'\1',
	r'([}\]])(\s*)("[^"]*":\s*)?([{\[])': r'\1,\2\3\4',
	r'}(\s*"[^"]*":)': r'},\1',
}
f = open("dota-vpk/scripts/npc/npc_heroes.txt", 'r')

text = f.read()

f.close()

# To get rid of comments
text = re.sub(r'//(.*)\n', '\n', text)
# To deal with how some people are idiots and only do single slash comments
text = re.sub(r'\n\s*/(.*)\n', '\n', text)

# The following are to convert Valve's KeyValue format to Json
text = re.sub(r'"([^"]*)"(\s*){', r'"\1": {', text)
text = re.sub(r'"([^"]*)"\s*"([^"]*)"', r'"\1": "\2",', text)
text = re.sub(r',(\s*[}\]])', r'\1', text)
text = re.sub(r'([}\]])(\s*)("[^"]*":\s*)?([{\[])', r'\1,\2\3\4', text)
text = re.sub(r'}(\s*"[^"]*":)', r'},\1', text)
text = "{ " + text + " }"

f = open("temp.json", "w+")
f.write(text)
f.close()

print(json.loads(text))