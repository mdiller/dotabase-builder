import dota2api
import urllib
import re
import string

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

#define dictionary of hero names to http-sensitive hero localized name
# dota_api = dota2api.Initialise()

heroes = []

for hero in dota_api.get_heroes()['heroes']:
	heroes.append(hero["localized_name"])
heroes.sort()

f = open("responses_data.txt", "w+")
# f.write("{\n")


for hero in heroes:
	hero = hero.replace(" ", "_")
	hero = hero.replace("'", "%27")
	url = "http://dota2.gamepedia.com/index.php?title={0}/Responses&action=edit".format(hero)

	req = urllib.request.Request(url, headers = {"User-Agent" : 'Mozilla/5.0'})
	response = urllib.request.urlopen(req)
	the_page = response.read()

	string = str(the_page)

	start = string.find("wpTextbox1\">")
	end = string.find("</textarea>", start)

	lines = string[start:end].split("\\n")

	for line in lines:
		if line.startswith("* &lt;sm2>"):
			line = unicodetoascii(line)
			line = line.replace("* &lt;sm2>", "\t\"")
			line = line.replace("&lt;sm2>", "")
			line = line.replace(".mp3&lt;/sm2> ", "\": \"")
			line = line.replace("\\'", "'")
			line = line.replace("[", "")
			line = line.replace("]", "")
			line = re.sub("\{.*\} ", "", line)
			line = line + "\","
			f.write(line + "\n")
			print(line)

# f.write("}")
f.close()
#FOR ALL HEROES
#download responses html page for hero
#grab important box "wpTextbox1"
#parse for important data and export to hero.json file
