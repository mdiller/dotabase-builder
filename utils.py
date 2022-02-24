import sys, os, json, re
import colorama # support ansi colors on windows
from collections import OrderedDict
colorama.init()

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
	if values is None:
		printerr("bad values passed to bold_values()")
		return "";
	values = values.split(separator)
	if base_level and base_level <= len(values):
		values[base_level - 1] = f"**{values[base_level - 1]}**"
	else:
		values = map(lambda v: f"**{v}**", values)
	return separator.join(values)


ability_special_talent_keys = { 
	"LinkedSpecialBonus": "talent_name", 
	"LinkedSpecialBonusField": "talent_value_key", 
	"LinkedSpecialBonusOperation": "talent_operation",
	"RequiresScepter": "scepter_upgrade",
	"RequiresShard": "shard_upgrade"
}
def get_ability_special_AbilityValues(ability_values, name):
	result = []
	for key, value in ability_values.items():
		new_item = OrderedDict()
		new_item["key"] = key
		if isinstance(value, str):
			new_item["value"] = value
		else:
			if "values" in value:
				new_item["value"] = value["values"]
			else:
				new_item["value"] = value["value"]
			for subkey in value:
				if subkey in ability_special_talent_keys:
					new_item[ability_special_talent_keys[subkey]] = value[subkey]
		result.append(new_item)
	return result

def get_ability_special_AbilitySpecial(ability_special, name):
	result = []
	for index_key in ability_special:
		obj = ability_special[index_key].copy()

		new_item = OrderedDict()

		# remove unneeded stuff (mostly ablility draft? linking)
		bad_keys = [ "CalculateSpellDamageTooltip", "levelkey", "ad_linked_ability", "ad_linked_abilities", "linked_ad_abilities" ]
		for key in bad_keys:
			if key in obj:
				del obj[key]

		for key in ability_special_talent_keys:
			if key in obj:
				new_item[ability_special_talent_keys[key]] = obj[key]
				del obj[key]

		items = list(obj.items())
		if len(items) != 2: # catch this for future bad_keys
			bad_keys = list(map(lambda i: i[0], items))
			bad_keys.remove("var_type")
			printerr(f"Theres a bad key in the AbilitySpecial of {name}: one of {bad_keys}")

		new_item["key"] = items[1][0]
		new_item["value"] = clean_values(items[1][1])
		result.append(new_item)

	return result


def get_ability_special(json_data, name):
	if "AbilitySpecial" in json_data:
		return get_ability_special_AbilitySpecial(json_data.get("AbilitySpecial"), name)
	elif "AbilityValues" in json_data:
		return get_ability_special_AbilityValues(json_data.get("AbilityValues"), name)
	else:
		return []

# adds talent info
def ability_special_add_talent(ability_special, ability_query):
	for attribute in ability_special:
		talent = attribute.get("talent_name")
		if talent:
			try:
				talent = ability_query.filter_by(name=talent).first()
				value_key = attribute.get("talent_value_key", "value")
				talent_operation = attribute.get("talent_operation", "SPECIAL_BONUS_ADD") # SUBTRACT, MULTIPLY

				talent_ability_special = json.loads(talent.ability_special, object_pairs_hook=OrderedDict)

				talent_attribute = next(a for a in talent_ability_special if a["key"] == value_key)

				def do_op(value1, value2):
					return {
						"SPECIAL_BONUS_ADD": value1 + value2,
						"SPECIAL_BONUS_SUBTRACT": value1 - value2,
						"SPECIAL_BONUS_MULTIPLY": value1 * value2,
						"SPECIAL_BONUS_PERCENTAGE_ADD": value1 * (1 + (value2 / 100))
					}[talent_operation]

				values = attribute["value"].split(" ")
				talent_value = float(re.sub(r"[a-z]", "", talent_attribute["value"]))
				for i in range(len(values)):
					if values[i] == "":
						values[i] = "0"
					values[i] = str(do_op(float(values[i]), talent_value))
				attribute["talent_value"] = clean_values(" ".join(values))
			except Exception as e:
				print("errored while adding talent")
				return ability_special
	return ability_special

def ability_special_add_header(ability_special, strings, name):
	for attribute in ability_special:
		header = strings.get(f"DOTA_Tooltip_ability_{name}_{attribute['key']}")
		if header is None:
			header = strings.get(f"DOTA_Tooltip_Ability_{name}_{attribute['key']}")
		if header is None:
			continue
		match = re.match(r"(%)?([\+\-]\$)?(.*)", header)
		header = match.group(3)

		attribute["value"] = clean_values(attribute["value"], percent=match.group(1))
		if "talent_value" in attribute:
			attribute["talent_value"] = clean_values(attribute["talent_value"], percent=match.group(1))

		if match.group(2):
			attribute["header"] = match.group(2)[0]
			attribute["footer"] = strings[f"dota_ability_variable_{header}"]
			if header in "dota_ability_variable_attack_range":
				attribute["footer"] = re.sub(r"<[^>]*>", "", attribute["footer"])
		else:
			# check if we look like "-Something" (without colon) or w/ a plus
			header = re.sub(r"<[^>]*>", "", header)
			match = re.match(r"([\+\-])([^:]*)", header)
			if match:
				attribute["header"] = match.group(1)
				attribute["footer"] = match.group(2)
			else:
				attribute["header"] = header
	return ability_special

# Cleans up the descriptions of items and abilities
def clean_description(text, replacements_dict, base_level=None, value_bolding=True):
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
			if value in replacements_dict:
				new_value = clean_values(replacements_dict[value], "/")
				if value_bolding:
					new_value = bold_values(new_value, "/", base_level)
				return new_value

			printerr(f"Missing attrib '{value}' FROM {text}")
			return f"%{value}%"

	text = re.sub(r'%([^%}\s]*)%', replace_attrib, text)
	text = re.sub(r'\{s:([^}\s]*)\}', replace_attrib, text)

	# include the percent in bold if the value is in bold
	text = re.sub(r'\*\*%', '%**', text)
	# replace double percents that are redundant now
	text = re.sub(r'%%', '%', text)

	if text.startswith("\n"):
		text = text[1:]

	return text

class ansicolors:
	CLEAR = '\033[0m'
	RED = '\033[31m'
	GREEN = '\033[32m'
	YELLOW = '\033[33m'
	BLUE = '\033[34m'
def printerr(error_text):
	print(f"{ansicolors.RED}   {error_text}{ansicolors.CLEAR}")


def write_json(filename, data):
	text = json.dumps(data, indent="\t")
	with open(filename, "w+") as f:
		f.write(text) # Do it like this so it doesnt break mid-file

def read_json(filename):
	with open(filename) as f:
		return json.load(f, object_pairs_hook=OrderedDict)

# this class pulled from https://stackoverflow.com/questions/2082152/case-insensitive-dictionary
class CaseInsensitiveDict(dict):
	@classmethod
	def _k(cls, key):
		return key.lower() if isinstance(key, str) else key
	def __init__(self, *args, **kwargs):
		super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
		self._convert_keys()
	def __getitem__(self, key):
		return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))
	def __setitem__(self, key, value):
		super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)
	def __delitem__(self, key):
		return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))
	def __contains__(self, key):
		return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))
	def has_key(self, key):
		return super(CaseInsensitiveDict, self).has_key(self.__class__._k(key))
	def pop(self, key, *args, **kwargs):
		return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)
	def get(self, key, *args, **kwargs):
		return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)
	def setdefault(self, key, *args, **kwargs):
		return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)
	def update(self, E={}, **F):
		super(CaseInsensitiveDict, self).update(self.__class__(E))
		super(CaseInsensitiveDict, self).update(self.__class__(**F))
	def _convert_keys(self):
		for k in list(self.keys()):
			v = super(CaseInsensitiveDict, self).pop(k)
			self.__setitem__(k, v)

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