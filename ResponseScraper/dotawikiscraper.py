from dotabase import *
import urllib.request
import re
import string
import html
import collections
import json
from bs4 import BeautifulSoup

def unicodetoascii(text):
	conversions = {
		'’': '\'',
		'…': '...',
		'—': '-',
		'–': '-',
		'é': 'e'
	}
	for key in conversions:
		text = text.replace(key, conversions[key])
	return text

session = dotabase_session()

completed_urls = []
f = open("responses_data.txt", "w+")

for voice in session.query(Voice).order_by(Voice.name):
	print(f"Retrieving for {voice.name}")
	url = f"http://dota2.gamepedia.com/index.php?title={voice.url}&action=edit"

	if voice.url in completed_urls:
		continue
	completed_urls.append(voice.url)

	req = urllib.request.Request(url, headers = {"User-Agent" : 'Mozilla/5.0'})
	response = urllib.request.urlopen(req)
	page_html = response.read()

	page_html = BeautifulSoup(page_html, 'html.parser')
	string = page_html.find(id="wpTextbox1").contents[0]
	string = unicodetoascii(string)

	lines = string.split("\n")

	loaded_lines = False
	for line in lines:
		if line.startswith("* <sm2>"):
			f.write(line + "\n")
			loaded_lines = True

	if not loaded_lines:
		print(f"didnt load any lines from {voice.name}")


f.close()
