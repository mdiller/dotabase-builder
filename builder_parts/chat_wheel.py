from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile


def load():
	session.query(ChatWheelMessage).delete()
	print("chat_wheel")

	print("- loading chat_wheel stuff from scripts")
	# load all of the item scripts data information
	data = valve_readfile(config.vpk_path, paths['chat_wheel_scripts_file'], "kv", encoding="utf-8")["chat_wheel"]
	for key in data["messages"]:
		msg_data = data["messages"][key]

		message = ChatWheelMessage()
		message.id = int(msg_data["message_id"])
		message.name = key
		message.label = msg_data.get("label")
		message.message = msg_data.get("message")
		message.sound = msg_data.get("sound")
		message.image = msg_data.get("image")
		message.all_chat = msg_data.get("all_chat") == "1"
		if message.sound:
			if message.sound == "soundboard.crash":
				message.sound = "soundboard.crash_burn"
			message.sound = f"/sounds/misc/soundboard/{message.sound.replace('soundboard.', '')}.wav"
		if message.image:
			message.image = f"/panorama/images/{message.image}"

		session.add(message)

	for category in data["categories"]:
		for msg in data["categories"][category]["messages"]:
			for message in session.query(ChatWheelMessage).filter_by(name=msg):
				if message.category is not None:
					raise ValueError(f"More than one category for chatwheel: {message.name}")
				message.category = category

	print("- loading chat wheel data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(config.vpk_path, paths['dota_english_file'], "kv", encoding="UTF-16")["lang"]["Tokens"]
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