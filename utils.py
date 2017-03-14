import sys, os, json
from collections import OrderedDict

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
		sys.stdout.write(f"\r{self.title} |{chunks + spaces}| {self.percent:.0%}")
		if self.current == self.total:
			sys.stdout.write("\n")
		sys.stdout.flush()


class Config:
	def __init__(self):
		self.path = "config.json"
		self.defaults = OrderedDict([  ("vpk_path", None) ])
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