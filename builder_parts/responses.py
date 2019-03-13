from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile
from vccd_reader import ClosedCaptionFile
import criteria_sentancing
import os

file_types = [ "mp3", "wav", "aac" ]

def load():
	session.query(Response).delete()
	session.query(Criterion).delete()
	print("Responses")

	progress = ProgressBar(session.query(Voice).count(), title="- loading from vsnd files:")
	for voice in session.query(Voice):
		progress.tick()

		if not voice.media_name:
			continue

		vsndevts_path = f"/soundevents/voscripts/game_sounds_vo_{voice.media_name}.vsndevts"
		vsndevts_data = valve_readfile(config.vpk_path, vsndevts_path, "vsndevts")
		captionsFilename = f"{config.vpk_path}/resource/subtitles/subtitles_{voice.media_name}_english.dat"
		if os.path.exists(captionsFilename):
			captionsFile = ClosedCaptionFile(captionsFilename)
		else:
			printerr(f"missing {captionsFilename}")
			captionsFile = None

		for key in vsndevts_data:
			data = vsndevts_data[key]
			filename = "/" + data["vsnd_files"][0].replace("vsnd", "mp3")
			
			response = Response()
			response.fullname = key
			response.name = os.path.basename(filename).replace(".mp3", "")

			for ext in file_types:
				newname = filename.replace(".mp3", f".{ext}")
				if os.path.exists(config.vpk_path + newname):
					filename = newname
					break

			if not os.path.exists(config.vpk_path + filename):
				printerr(f"Missing file: {filename}")

			response.mp3 = filename
			response.voice_id = voice.id
			response.hero_id = voice.hero_id
			response.criteria = ""

			if captionsFile:
				text = captionsFile.lookup(response.fullname)
				if text and not ("_arc_" in text):
					response.text = text
					response.text_simple = text.replace("...", " ")
					response.text_simple = " " + re.sub(r'[^a-z^0-9^A-Z^\s]', r'', response.text_simple).lower() + " "
					response.text_simple = re.sub(r'\s+', r' ', response.text_simple)
				else:
					response.text = ""

			session.add(response)

	print("- loading criteria")
	rules = {}
	groups = {}
	criteria = {}
	# Load response_rules
	for root, dirs, files in os.walk(config.vpk_path + paths['response_rules_path']):
		for file in files:
			data = valve_readfile(config.vpk_path, paths['response_rules_path'] + file, "rules")
			for key in data:
				if key.startswith("rule_"):
					rules[key[5:]] = data[key]
				elif key.startswith("response_"):
					groups[key[9:]] = data[key]
				elif key.startswith("criterion_"):
					criteria[key[10:]] = data[key]

	for key in criteria:
		criterion = Criterion()
		criterion.name = key
		vals = criteria[key].split(" ")
		criterion.matchkey = vals[0]
		criterion.matchvalue = vals[1]
		criterion.weight = vals[3] if "weight" in vals else 1.0
		criterion.required = "required" in vals
		session.add(criterion)

	progress = ProgressBar(len(rules), title="- linking rules:")
	for key in rules:
		response_criteria = rules[key]['criteria'].rstrip()
		progress.tick()

		for fullname in groups[rules[key]['response']]:
			response = session.query(Response).filter_by(fullname=fullname).first()
			if response is not None:
				if response.criteria == "":
					response.criteria = response_criteria
				else:
					response.criteria += "|" + response_criteria

	print("- generating pretty criteria")
	criteria_sentancing.load_pretty_criteria(session)

	session.commit()