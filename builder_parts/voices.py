from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile

def load():
	session.query(Voice).delete()
	print("Voices")

	# For announcers (later)
	# data = valve_readfile(config.vpk_path, paths['cosmetics_scripts_file'], "kv_nocomment", encoding="UTF-16")

	progress = ProgressBar(session.query(Hero).count(), title="- loading from heroes:")
	for hero in session.query(Hero):
		progress.tick()
		voice = Voice()

		voice.id = hero.id
		voice.name = hero.full_name
		voice.localized_name = hero.localized_name
		voice.icon = hero.icon
		voice.image = hero.portrait
		voice.vsndevts_path = "/" + json.loads(hero.json_data).get("VoiceFile")
		voice.hero_id = hero.id

		session.add(voice)


	session.commit()