import sys

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