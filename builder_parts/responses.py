from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile
from vccd_reader import ClosedCaptionFile
import criteria_sentancing
import re
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
		captionsFilename2 = f"{config.vpk_path}/resource/subtitles/subtitles_{voice.media_name}_english_staging.dat"
		if os.path.exists(captionsFilename):
			captionsFile = ClosedCaptionFile(captionsFilename)
		elif os.path.exists(captionsFilename2):
			captionsFile = ClosedCaptionFile(captionsFilename2)
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
				if text:
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
		if "weight" in vals:
			criterion.weight = float(vals[vals.index("weight") + 1])
		else:
			criterion.weight = 1.0
		criterion.required = "required" in vals
		session.add(criterion)

	voice_linker = {}

	
	custom_voice_criteria = { # because valve did customresponse:arcana for 2 things
		"Tempest Helm of the Thundergod": "IsZeusEconArcana"
	}
	# fix up voice.criteria
	for voice in session.query(Voice):
		if voice.criteria:
			if voice.name in custom_voice_criteria:
				voice.criteria = custom_voice_criteria[voice.name]
				continue
			crits = []
			for crit in voice.criteria.split("|"):
				key, value = crit.split(":")
				realcrit = session.query(Criterion).filter_by(matchkey=key).filter_by(matchvalue=value).first()
				if realcrit:
					crits.append(realcrit.name)
			voice.criteria = "|".join(crits)
			pattern = f"(^|\|| ){voice.criteria}($|\|| )"
			voice_linker[pattern] = voice

	progress = ProgressBar(len(rules) + session.query(Response).count(), title="- linking rules:")
	pre_responses = {}
	for key in rules:
		progress.tick()
		response_criteria = rules[key]['criteria'].rstrip()
		for fullname in groups[rules[key]['response']]:
			if fullname not in pre_responses:
				pre_responses[fullname] = response_criteria
			else:
				pre_responses[fullname] += "|" + response_criteria

	for response in session.query(Response):
		progress.tick()
		if response.fullname in pre_responses:
			response.criteria = pre_responses[response.fullname]
			for pattern, voice in voice_linker.items():
				if re.search(pattern, response.criteria):
					response.voice_id = voice.id

	print("- adding hero chatwheel criteria")
	chatwheel_criteria = []
	chatwheel_data = valve_readfile(config.vpk_path, paths['chat_wheel_scripts_file'], "kv", encoding="utf-8")["chat_wheel"]
	for hero in chatwheel_data["hero_messages"]:
		for chatwheel_id in chatwheel_data["hero_messages"][hero]:
			chatwheel_message = chatwheel_data["hero_messages"][hero][chatwheel_id]
			badge_tier = chatwheel_message['unlock_hero_badge_tier']
			if badge_tier not in chatwheel_criteria:
				chatwheel_criteria.append(badge_tier)
			new_criteria = f"HeroChatWheel {badge_tier}"
			for response in session.query(Response).filter_by(fullname=chatwheel_message["sound"]):
				if response.criteria != "":
					new_criteria = "|" + new_criteria
				response.criteria += new_criteria
	for crit in chatwheel_criteria:
		criterion = Criterion()
		criterion.name = crit
		criterion.matchkey = "badge_tier"
		criterion.matchvalue = crit.replace("Tier", "").lower()
		criterion.weight = 1.0
		criterion.required = True
		session.add(criterion)
	criterion = Criterion()
	criterion.name = "HeroChatWheel"
	criterion.matchkey = "Concept"
	criterion.matchvalue = "DOTA_CHATWHEEL_THINGIE"
	criterion.weight = 1.0
	criterion.required = True
	session.add(criterion)


	print("- generating pretty criteria")
	criteria_sentancing.load_pretty_criteria(session)

	session.commit()