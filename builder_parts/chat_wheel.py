from __main__ import session, config, paths
from dotabase import *
from utils import *
from valve2json import valve_readfile


def load():
	session.query(ChatWheelMessage).delete()
	print("chat_wheel")

	print("- loading chat_wheel stuff from scripts")
	# load all of the item scripts data information
	data = valve_readfile(config.vpk_path, paths['chat_wheel_scripts_file'], "kv", encoding="UTF-16")["chat_wheel"]["messages"]
	for key in data:
		msg_data = data[key]

		message = ChatWheelMessage()
		message.id = int(msg_data["message_id"])
		message.name = key
		message.label = msg_data["label"]
		message.message = msg_data["message"]
		message.sound = msg_data.get("sound")

		session.add(message)

	print("- loading chat wheel data from dota_english")
	# Load additional information from the dota_english.txt file
	data = valve_readfile(config.vpk_path, paths['dota_english_file'], "kv", encoding="UTF-16")["lang"]["Tokens"]
	for message in session.query(ChatWheelMessage):
		if message.label.startswith("#") and message.label[1:] in data:
			message.label = data[message.label[1:]]
		if message.message.startswith("#") and message.message[1:] in data:
			message.message = data[message.message[1:]]
		if message.id in [ 71, 72 ]:
			message.message = message.message.replace("%s1", "A hero")

	session.commit()