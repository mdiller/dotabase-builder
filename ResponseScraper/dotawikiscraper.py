from dotabase import *
import urllib.request
import re
import string
import html

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

session = dotabase_session()

heroes = []

for hero in session.query(Hero):
	heroes.append(hero.localized_name)

heroes.sort()

f = open("responses_data.txt", "w+")

for hero in heroes:
	print("Retrieving for {}".format(hero))
	hero = hero.replace(" ", "_")
	hero = hero.replace("'", "%27")
	url = "http://dota2.gamepedia.com/index.php?title={0}/Responses&action=edit".format(hero)

	req = urllib.request.Request(url, headers = {"User-Agent" : 'Mozilla/5.0'})
	response = urllib.request.urlopen(req)
	the_page = response.read()

	string = str(the_page)

	start = string.find("wpTextbox1\">")
	end = string.find("</textarea>", start)

	string = string[start:end]
	string = html.unescape(string)
	string = unicodetoascii(string)


	lines = string.split("\\n")

	for line in lines:
		if line.startswith("* <sm2>"):
			f.write(line + "\n")

f.close()
