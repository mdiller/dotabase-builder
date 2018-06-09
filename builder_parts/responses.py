from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile
import criteria_sentancing
import os

def load():
	session.query(Response).delete()
	session.query(Criterion).delete()
	print("Responses")

	progress = ProgressBar(session.query(Voice).count(), title="- loading from vsnd files:")
	for voice in session.query(Voice):
		progress.tick()

		if not voice.vsndevts_path:
			continue

		vsndevts_data = valve_readfile(config.vpk_path, voice.vsndevts_path, "vsndevts")

		for key in vsndevts_data:
			data = vsndevts_data[key]
			filename = "/" + data["vsnd_files"][0].replace("vsnd", "mp3")
			
			response = Response()
			response.fullname = key
			response.name = os.path.basename(filename).replace(".mp3", "")

			if not os.path.exists(config.vpk_path + filename):
				filename = filename.replace(".mp3", ".wav")
			if not os.path.exists(config.vpk_path + filename):
				filename = filename.replace(".wav", ".mp3")
				print(f"Missing file: {filename}")

			response.mp3 = filename
			response.voice_id = voice.id
			response.hero_id = voice.hero_id
			response.criteria = ""
			session.add(response)
	

	fulldata = valve_readfile(paths['scraped_responses_dir'], paths['scraped_responses_file'], "scrapedresponses")
	progress = ProgressBar(len(fulldata), title="- loading response texts")
	for voiceid in fulldata:
		progress.tick()
		voice = session.query(Voice).filter_by(id=int(voiceid)).first()
		data = fulldata[voiceid]

		for response in session.query(Response).filter_by(voice_id=voice.id):
			text = ""

			# these to help with some weird shit
			fullname = re.sub(r'^announcer_', '', response.fullname)
			fullname = re.sub(r'defensegrid', 'defense_grid', fullname)
			fullname = re.sub(r'techies_tech_ann', 'tech_ann', fullname)
			fullname = re.sub(r'dlc_tusk_tusk_ann', 'greevling_tusk_ann', fullname)
			if voice.id == 49: # dragon knight
				fullname = f"dk_{response.name}"

			if response.fullname in data:
				text = data[response.fullname]
			elif fullname in data:
				text = data[fullname]
			elif response.name in data:
				text = data[response.name]

			if text != "":
				text = re.sub(r'<!--.*-->', r'', text)
				text = re.sub(r'{{Tooltip\|([^|]+)\|(.*)}}', r'\1 (\2)', text)
				text = re.sub(r'{{tooltip\|\?\|(.*)}}', r'(\1)', text)
				text = re.sub(r'{{.*}}', r'', text)
				response.text = text
				response.text_simple = text.replace("...", " ")
				response.text_simple = " " + re.sub(r'[^a-z^0-9^A-Z^\s]', r'', response.text_simple).lower() + " "
				response.text_simple = re.sub(r'\s+', r' ', response.text_simple)
			else:
				response.text = ""


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