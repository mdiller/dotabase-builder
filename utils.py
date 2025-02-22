import sys, os, json, re
import decimal
import colorama # support ansi colors on windows
import datetime
import re
from collections import OrderedDict
from dotabase import LocaleString
colorama.init()

def clean_values(values: str, join_string=" ", percent=False):
	if values is None or values == "":
		return values
	values = values.strip().split(" ")
	for i in range(len(values)):
		values[i] = re.sub(r"\.0+$", "", values[i])
		values[i] = re.sub(r"^=", "", values[i])
		if percent and values[i][-1] != "%":
			if not re.match(r"^x[0-9]+$", values[i]):
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



# adds/subtracts the modifier from the base value. Assumes 0 if no base value given
def do_simple_math(base_value, modifier):
	if base_value is None:
		base_value = "0"
	if " " in base_value or " " in modifier:
		# this is a multi-part value like "10 20 30 40" so just do these individually
		values = base_value.split(" ")
		modifiers = modifier.split(" ")
		valcount = max(len(values), len(modifiers))

		if len(values) == 1:
			values = [base_value] * valcount
		if len(modifiers) == 1:
			modifiers = [modifier] * valcount

		results = []
		for i in range(valcount):
			results.append(do_simple_math(values[i], modifiers[i]))
		return " ".join(results)

	if base_value == "FIELD_INTEGER":
		base_value_decimal = 0 # god dammit valve y u do this. supposed to be a number n you give me "FIELD_INTEGER"????
	else:
		base_value_decimal = decimal.Decimal(base_value)

	operation = lambda a, b: a + b

	if "%" in modifier:
		modifier = modifier.replace("%", "")
		modifier_decimal = decimal.Decimal(modifier)
		modifier_decimal = modifier_decimal / 100
	elif "=" in modifier: # TODO: this for lifestealer infest aghs, sets it to the new value. too tired to implement right now
		modifier = modifier.replace("=", "")
		modifier_decimal = decimal.Decimal(modifier)
	elif "x" in modifier:
		modifier = modifier.replace("x", "")
		operation = lambda a, b: a * b
		modifier_decimal = decimal.Decimal(modifier)
	else:
		modifier_decimal = decimal.Decimal(modifier)

	value = operation(base_value_decimal, modifier_decimal)
	value = str(value)
	value = re.sub(r"\.0+$", "", value)
	return value

ability_special_talent_keys = { 
	"LinkedSpecialBonus": "talent_name", 
	"LinkedSpecialBonusField": "talent_value_key", 
	"LinkedSpecialBonusOperation": "talent_operation",
	"RequiresScepter": "scepter_upgrade",
	"RequiresShard": "shard_upgrade",
	"RequiresFacet": "facet_upgrade"
}
def get_ability_special_AbilityValues(ability_values, name):
	result = []
	for avkey, value in ability_values.items():
		new_item = OrderedDict()
		new_item["key"] = avkey
		if isinstance(value, str):
			new_item["value"] = value
		else:
			# value is a dictionary
			valuekeys = [ "values", "value" ]
			for key in valuekeys:
				if key in value:
					new_item["value"] = value[key]
					break
			if not "value" in new_item:
				prefix = "special_bonus_facet_"
				for key in value:
					if key.startswith(prefix):
						new_item["value"] = value[key]
						break
			for subkey in value:
				if subkey in ability_special_talent_keys:
					new_item[ability_special_talent_keys[subkey]] = value[subkey]
			
			if "special_bonus_shard" in value:
				new_item["shard_value"] = do_simple_math(value.get("value"), value["special_bonus_shard"])
				new_item["shard_bonus"] = re.sub(r"[^\d]", "", value["special_bonus_shard"])
			if "special_bonus_scepter" in value:
				new_item["scepter_value"] = do_simple_math(value.get("value"), value["special_bonus_scepter"])
				new_item["scepter_bonus"] = re.sub(r"[^\d]", "", value["special_bonus_scepter"])

		result.append(new_item)
	return result

def get_ability_special_AbilitySpecial(ability_special, name):
	result = []
	for index_key in ability_special:
		if isinstance(ability_special[index_key], str):
			obj = { "value": ability_special[index_key] }
		else:
			obj = ability_special[index_key].copy()

		new_item = OrderedDict()

		# remove unneeded stuff (mostly ablility draft? linking)
		bad_keys = [ "CalculateSpellDamageTooltip", "levelkey", "ad_linked_ability", "ad_linked_abilities", "linked_ad_abilities" ]
		for key in bad_keys:
			if key in obj:
				del obj[key]

		# useful keys we can add to the abilityspecial
		good_keys = {
			"DamageTypeTooltip": "damagetype"
		}
		for key in good_keys:
			if key in obj:
				new_item[good_keys[key]] = obj[key]
				del obj[key]

		for key in ability_special_talent_keys:
			if key in obj:
				new_item[ability_special_talent_keys[key]] = obj[key]
				del obj[key]

		items = list(obj.items())
		if len(items) != 2: # catch this for future bad_keys
			bad_keys = list(map(lambda i: i[0], items))
			if "var_type" in bad_keys:
				bad_keys.remove("var_type")
			printerr(f"Theres a bad key in the AbilitySpecial of {name}: one of {bad_keys}")

		if items[0][0] == "var_type":
			del items[0]
		
		if len(items) == 0:
			printerr(f"Empty AbilitySpecial entry in {name}")
			continue

		new_item["key"] = items[0][0]
		new_item["value"] = clean_values(items[0][1])
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
def ability_special_add_talent(ability_special, ability_query, ability_name):
	for attribute in ability_special:
		talent = attribute.get("talent_name")
		if talent:
			talent = ability_query.filter_by(name=talent).first()
			value_key = attribute.get("talent_value_key", "value")
			talent_operation = attribute.get("talent_operation", "SPECIAL_BONUS_ADD") # SUBTRACT, MULTIPLY

			if talent is None:
				printerr(f"The wrong MISSING talent ({attribute.get('talent_name')}) is linked to the ability special for {ability_name}: {attribute.get('key')}")
				return ability_special

			talent_ability_special = json.loads(talent.ability_special, object_pairs_hook=OrderedDict)

			talent_attribute = next((a for a in talent_ability_special if a["key"] == value_key), None)

			if talent_attribute is None:
				printerr(f"The wrong talent ({talent.name}: {talent.localized_name}) is linked to the ability special for {ability_name}: {attribute.get('key')}")
				return ability_special

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
	return ability_special

def ability_special_add_header(ability_special, strings, name):
	for attribute in ability_special:
		key = re.sub("^bonus_", "", attribute['key'])
		keys = []
		for a in ["ability", "Ability"]:
			for b in [key, attribute['key']]:
				keys.append(f"DOTA_Tooltip_{a}_{name}_{b}")

		header = None
		for k in keys:
			if header is None:
				header = strings.get(k)
		if header is None:
			continue
		match = re.match(r"(%)?([\+\-]\$)?(.*)", header)
		header = match.group(3)

		if "value" in attribute:
			attribute["value"] = clean_values(attribute["value"], percent=match.group(1))
		if "talent_value" in attribute:
			attribute["talent_value"] = clean_values(attribute["talent_value"], percent=match.group(1))

		if match.group(2):
			attribute["header"] = match.group(2)[0]
			attribute["footer"] = strings[f"dota_ability_variable_{header}"]
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

ATTRIBUTE_TEMPLATE_PATTERNS = [
	r'%([^%}\s/]*)%',
	r'\{s:([^}\s]*)\}'
]

# Cleans up the descriptions of items and abilities
def clean_description(text, replacements_dict=None, base_level=None, value_bolding=True, report_errors=True):
	if text is None or text == "":
		return text
	text = re.sub(r'</h1> ', r'</h1>', text)
	text = re.sub(r'<h1>([^<]+)</h1>', r'\n# \1\n', text)
	text = re.sub(r'<(br|BR) ?/?>', r'\n', text)
	text = re.sub(r"<i>([^<]+)</i>", r"\*\1\*", text)
	text = re.sub(r'<span class="GameplayValues GameplayVariable">(.*)</span>', r'**\1**', text)
	text = re.sub(r'<font color=.*>(.*)</font>', r'\1', text)
	text = re.sub(r" color='[^']+'>", r'>', text)
	text = re.sub(r'<b>([^<]+)</b>', r'**\1**', text)

	if replacements_dict:
		def replace_attrib(match):
			key = match.group(1)
			if key == "":
				return "%"
			else:
				new_value = None
				if key in replacements_dict:
					new_value = replacements_dict[key]
				elif key.lower() in replacements_dict:
					new_value = replacements_dict[key.lower()]
				
				if new_value is not None:
					new_value = clean_values(new_value, "/")
					if value_bolding:
						new_value = bold_values(new_value, "/", base_level)
					return new_value
			
				if report_errors:
					printerr(f"Missing attrib '{key}' FROM {text}")
				return f"%{key}%"

		for pattern in ATTRIBUTE_TEMPLATE_PATTERNS:
			text = re.sub(pattern, replace_attrib, text)

		# include the percent in bold if the value is in bold
		text = re.sub(r'\*\*%', '%**', text)
		# replace double percents that are redundant now
		text = re.sub(r'%%', '%', text)
		# do what we think the ": {s" stuff means
		text = re.sub(r"^: [x\+\-]?", "", text)

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
	global CURRENT_PROGRESS_BAR
	if CURRENT_PROGRESS_BAR is not None:
		CURRENT_PROGRESS_BAR.errors.append(error_text)
		return
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
		remove_colons = kwargs.get("remove_colons", False)
		self._convert_keys(remove_colons)
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
	def _convert_keys(self, remove_colons=False):
		for k in list(self.keys()):
			v = super(CaseInsensitiveDict, self).pop(k)
			if remove_colons:
				k = re.sub(r":.+$", "", k)
			self.__setitem__(k, v)


CURRENT_PROGRESS_BAR = None

class ProgressBar:
	def __init__(self, total, title="Percent:"):
		global CURRENT_PROGRESS_BAR
		self.total = total
		self.current = 0
		self.max_chunks = 10
		self.title = title
		self.errors = []
		self.render()
		CURRENT_PROGRESS_BAR = self

	def tick(self):
		oldpercent = int(self.percent * 100)
		self.current += 1
		if oldpercent != int(self.percent * 100):
			self.render()

	@property
	def percent(self):
		if self.total == 0:
			return 0
		return self.current / self.total

	def render(self):
		global CURRENT_PROGRESS_BAR
		chunks = '█' * int(round(self.percent * self.max_chunks))
		spaces = ' ' * (self.max_chunks - len(chunks))
		sys.stdout.write(f"\r{self.title} |{chunks + spaces}| {self.percent:.0%}".encode("utf8").decode(sys.stdout.encoding))
		if self.current == self.total:
			sys.stdout.write("\n")
		sys.stdout.flush()
		if self.current == self.total:
			sys.stderr.flush()
			CURRENT_PROGRESS_BAR = None
			for error in self.errors:
				printerr(error)


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
config = Config()


class SimpleTimer():
	def __init__(self, message=None):
		self.message = message
		self.start = datetime.datetime.now()
		self.end = None
	
	def __enter__(self):
		self.start = datetime.datetime.now()
		return self

	def __exit__(self, type, value, traceback):
		self.stop()
		if self.message:
			print(self.message + f": {self.miliseconds} ms")

	def stop(self):
		self.end = datetime.datetime.now()

	@property
	def seconds(self):
		if self.end is None:
			self.stop()
		return int((self.end - self.start).total_seconds())
	
	@property
	def miliseconds(self):
		if self.end is None:
			self.stop()
		return int((self.end - self.start).total_seconds() * 1000.0)

	def __str__(self):
		s = self.seconds % 60
		m = self.seconds // 60
		text = f"{s} second{'s' if s != 1 else ''}"
		if m > 0:
			text = f"{m} minute{'s' if m != 1 else ''} and " + text
		return text

	def __repr__(self):
		return self.__str__()

# adds a locale string to the 
def addLocaleString(session, lang, target, column, value):
	if value == "" or value == None or value == getattr(target, column):
		return None
	string = LocaleString()
	string.lang = lang
	string.target = target
	string.column = column
	string.value = value
	session.add(string)