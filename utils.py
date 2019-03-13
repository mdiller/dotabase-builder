import sys, os, json, re
from collections import OrderedDict

def printerr(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

def clean_values(values, join_string=" ", percent=False):
	if values is None:
		return None
	values = values.split(" ")
	for i in range(len(values)):
		values[i] = re.sub(r"\.0+$", "", values[i])
		if percent and values[i][-1] != "%":
			values[i] += "%"
	if all(x == values[0] for x in values):
		return values[0]
	return join_string.join(values)

def bold_values(values, separator, base_level):
	values = values.split(separator)
	if base_level and base_level <= len(values):
		values[base_level - 1] = f"**{values[base_level - 1]}**"
	else:
		values = map(lambda v: f"**{v}**", values)
	return separator.join(values)


def get_ability_special(ability_special, name):
	if ability_special is None:
		return []
	result = []
	for index_key in ability_special:
		obj = ability_special[index_key].copy()

		new_item = OrderedDict()

		# remove unneeded stuff (mostly talents linking)
		bad_keys = [ "CalculateSpellDamageTooltip", "levelkey" ]
		for key in bad_keys:
			if key in obj:
				del obj[key]

		talent_keys = { 
			"LinkedSpecialBonus": "talent_name", 
			"LinkedSpecialBonusField": "talent_value_key", 
			"LinkedSpecialBonusOperation": "talent_operation"
		}
		for key in talent_keys:
			if key in obj:
				new_item[talent_keys[key]] = obj[key]
				del obj[key]

		items = list(obj.items())
		if len(items) != 2: # catch this for future bad_keys
			raise ValueError(f"Theres a bad key in the AbilitySpecial of {name}")

		new_item["key"] = items[1][0]
		new_item["value"] = clean_values(items[1][1])
		result.append(new_item)

	return result

def ability_special_add_talent(ability_special, ability_query):
	for attribute in ability_special:
		talent = attribute.get("talent_name")
		if talent:
			talent = ability_query.filter_by(name=talent).first()
			value_key = attribute.get("talent_value_key", "value")
			talent_operation = attribute.get("talent_operation", "SPECIAL_BONUS_ADD") # SUBTRACT, MULTIPLY

			talent_ability_special = json.loads(talent.ability_special, object_pairs_hook=OrderedDict)

			talent_attribute = next(a for a in talent_ability_special if a["key"] == value_key)

			def do_op(value1, value2):
				return {
					"SPECIAL_BONUS_ADD": value1 + value2,
					"SPECIAL_BONUS_SUBTRACT": value1 - value2,
					"SPECIAL_BONUS_MULTIPLY": value1 * value2
				}[talent_operation]

			values = attribute["value"].split(" ")
			talent_value = float(re.sub(r"[a-z]", "", talent_attribute["value"]))
			for i in range(len(values)):
				values[i] = str(do_op(float(values[i]), talent_value))
			attribute["talent_value"] = clean_values(" ".join(values))
	return ability_special

def ability_special_add_header(ability_special, strings, name):
	for attribute in ability_special:
		header = strings.get(f"DOTA_Tooltip_ability_{name}_{attribute['key']}")
		if header is None:
			continue
		match = re.match(r"(%)?(\+\$)?(.*)", header)
		header = match.group(3)

		attribute["value"] = clean_values(attribute["value"], percent=match.group(1))
		if "talent_value" in attribute:
			attribute["talent_value"] = clean_values(attribute["talent_value"], percent=match.group(1))

		if match.group(2):
			attribute["header"] = "+"
			attribute["footer"] = strings[f"dota_ability_variable_{header}"]
			if header in "dota_ability_variable_attack_range":
				attribute["footer"] = re.sub(r"<[^>]*>", "", attribute["footer"])
		else:
			attribute["header"] = re.sub(r"<[^>]*>", "", header)
	return ability_special

# Cleans up the descriptions of items and abilities
def clean_description(text, ability_special, base_level=None):
	text = re.sub(r'</h1> ', r'</h1>', text)
	text = re.sub(r'<h1>([^<]+)</h1>', r'\n# \1\n', text)
	text = re.sub(r'<(br|BR)>', r'\n', text)
	text = re.sub(r'<span class="GameplayValues GameplayVariable">(.*)</span>', r'**\1**', text)
	text = re.sub(r'<font color=.*>(.*)</font>', r'\1', text)

	def replace_attrib(match):
		value = match.group(1)
		if value == "":
			return "%"
		else:
			for attrib in ability_special:
				if attrib["key"] == value:
					value = clean_values(attrib["value"], "/")
					return bold_values(value, "/", base_level)
			print(f"Missing attrib %{value}%")
			return f"%{value}%"

	text = re.sub(r'%([^%\s]*)%', replace_attrib, text)

	# include the percent in bold if the value is in bold
	text = re.sub(r'\*\*%', '%**', text)
	# replace double percents that are redundant now
	text = re.sub(r'%%', '%', text)

	if text.startswith("\n"):
		text = text[1:]

	return text

def write_json(filename, data):
	text = json.dumps(data, indent="\t")
	with open(filename, "w+") as f:
		f.write(text) # Do it like this so it doesnt break mid-file

def read_json(filename):
	with open(filename) as f:
		return json.load(f, object_pairs_hook=OrderedDict)

class ProgressBar:
	def __init__(self, total, title="Percent:"):
		self.total = total
		self.current = 0
		self.max_chunks = 10
		self.title = title
		self.render()

	def tick(self):
		oldpercent = int(self.percent * 100)
		self.current += 1
		if oldpercent != int(self.percent * 100):
			self.render()

	@property
	def percent(self):
		return self.current / self.total

	def render(self):
		chunks = '█' * int(round(self.percent * self.max_chunks))
		spaces = ' ' * (self.max_chunks - len(chunks))
		sys.stdout.write(f"\r{self.title} |{chunks + spaces}| {self.percent:.0%}".encode("utf8").decode(sys.stdout.encoding))
		if self.current == self.total:
			sys.stdout.write("\n")
		sys.stdout.flush()
		if self.current == self.total:
			sys.stderr.flush()


class Config:
	def __init__(self):
		self.path = "config.json"
		self.defaults = OrderedDict([  ("vpk_path", None), ("overwrite_db", True), ("overwrite_json", False)  ])
		if not os.path.exists(self.path):
			self.json_data = self.defaults
			self.save_settings()
			self.bad_config_file()
		else:
			self.json_data = read_json(self.path)
			if self.vpk_path is None:
				self.bad_config_file()

	def bad_config_file(self):
		print("You gotta fill out the config.json file")
		print("vpk_path example: C:/foo/dota-vpk")
		sys.exit()


	def save_settings(self):
		write_json(self.path, self.json_data)

	@property
	def vpk_path(self):
		return self.json_data["vpk_path"]

	@property
	def overwrite_db(self):
		return self.json_data["overwrite_db"]

	@property
	def overwrite_json(self):
		return self.json_data["overwrite_json"]