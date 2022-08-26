from builder import session
from dotabase import *
from utils import *
from valve2json import valve_readfile, DotaFiles
import os


def load():
	session.query(ChatWheelMessage).delete()
	print("Chat Wheels")

	print("- loading chat_wheel vsndevts infos")
	# load sounds info from vsndevts file
	vsndevts_data = CaseInsensitiveDict(DotaFiles.game_sounds_vsndevts.read())
	extra_vsndevts_dirs = [ "teamfandom", "team_fandom" ]
	for subdir in extra_vsndevts_dirs:
		fulldirpath = os.path.join(config.vpk_path, f"soundevents/{subdir}")
		for file in os.listdir(fulldirpath):
			if file.endswith(".vsndevts"):
				filepath = f"/soundevents/{subdir}/{file}"
				more_vsndevts_data = valve_readfile(filepath, "vsndevts")
				vsndevts_data.update(more_vsndevts_data)	

	print("- loading chat_wheel info from scripts")
	# load all of the item scripts data information
	scripts_data = DotaFiles.chat_wheel.read()["chat_wheel"]
	chatwheel_scripts_subdir = "scripts/chat_wheels"
	scripts_messages = CaseInsensitiveDict(scripts_data["messages"])
	scripts_categories = CaseInsensitiveDict(scripts_data["categories"])
	for file in os.listdir(os.path.join(config.vpk_path, chatwheel_scripts_subdir)):
		filepath = f"/{chatwheel_scripts_subdir}/{file}"
		more_chatwheel_data = valve_readfile(filepath, "kv", encoding="utf-8")["chat_wheel"]
		scripts_messages.update(more_chatwheel_data.get("messages", {}))
		scripts_categories.update(more_chatwheel_data.get("categories", {}))

	existing_ids = set()
	print("- process all chat_wheel data")
	data = DotaFiles.chat_wheel.read()["chat_wheel"]
	for key in scripts_messages:
		msg_data = scripts_messages[key]

		message_id = int(msg_data["message_id"])
		if message_id in existing_ids:
			printerr(f"duplicate message_id {message_id} found, skipping")
			continue
		existing_ids.add(message_id)

		message = ChatWheelMessage()
		message.id = message_id
		message.name = key
		message.label = msg_data.get("label")
		message.message = msg_data.get("message")
		message.sound = msg_data.get("sound")
		message.image = msg_data.get("image")
		message.all_chat = msg_data.get("all_chat") == "1"
		if message.sound:
			if message.sound not in vsndevts_data:
				printerr(f"Couldn't find vsndevts entry for {message.sound}, skipping")
				continue
			if "vsnd_files" not in vsndevts_data[message.sound]:
				printerr(f"no associated vsnd files found for {message.sound}, skipping")
				continue

			soundfile = vsndevts_data[message.sound]["vsnd_files"]
			if isinstance(soundfile, list):
				soundfile = soundfile[0]
			message.sound = "/" + soundfile

			if not os.path.exists(config.vpk_path + message.sound):
				message.sound = message.sound.replace("vsnd", "wav")
			if not os.path.exists(config.vpk_path + message.sound):
				message.sound = message.sound.replace("wav", "mp3")

			if not os.path.exists(config.vpk_path + message.sound):
				printerr(f"Missing chatweel id {message.id} file: {message.sound}")
		if message.image:
			message.image = f"/panorama/images/{message.image}"

		session.add(message)

	for category in scripts_categories:
		for msg in scripts_categories[category]["messages"]:
			for message in session.query(ChatWheelMessage).filter_by(name=msg):
				if message.category is not None:
					raise ValueError(f"More than one category for chatwheel: {message.name}")
				message.category = category

	print("- loading chat wheel data from dota_english")
	# Load localization info from dota_english.txt and teamfandom_english.txt
	data = DotaFiles.dota_english.read()["lang"]["Tokens"]
	data.update(DotaFiles.teamfandom_english.read()["lang"]["Tokens"])

	for message in session.query(ChatWheelMessage):
		if message.label is None or message.message is None:
			continue
		if message.label.startswith("#") and message.label[1:] in data:
			message.label = data[message.label[1:]]
		if message.message.startswith("#") and message.message[1:] in data:
			message.message = data[message.message[1:]]
		if message.id in [ 71, 72 ]:
			message.message = message.message.replace("%s1", "A hero")

	session.commit()