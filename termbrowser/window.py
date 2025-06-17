import curses

class Window:
	def __init__(self, screen):
		pass
		y, x = screen.getmaxyx()
		self.WIDTH = x
		self.HEIGHT = y
		curses.noecho()
		screen.keypad(True)
		screen.clear()
		self.screen = screen
		self.exiting = False
	def resize(self):
		y, x = self.screen.getmaxyx()
		self.screen.clear()
		curses.resizeterm(y, x)
		self.WIDTH = x
		self.HEIGHT = y
		self.refresh()
	def refresh(self):
		self.screen.refresh()
	def get_resized(self) -> bool:
		return curses.is_term_resized(self.HEIGHT, self.WIDTH)
	def get_input(self) -> chr:
		res = self.screen.getch()
		return res
	def get_input_text(self) -> str:
		res = self.screen.getstr()
		return res
	def get_wide_char(self) -> str:
		res = self.screen.get_wch()
		return res
	def start_render(self, y: int, x: 0):
		self.screen.move(y, x)
	def render(self, string: str, option, partial_backgrounds: list, partial_foregrounds: list):
		try:
			for i in range(len(string)):
				pair = partial_backgrounds[i] * 10 + partial_foregrounds[i]
				self.screen.addstr(string[i], curses.color_pair(pair) | option)
		except Exception as e:
			# write to a log file
			with open("render.log", "a") as f:
				f.write(f"Error rendering string: {e}\n")
				f.write(f"String: {string}\n")
			print("Error rendering string:")
			print(e)
			print(f"String: {string}")
	def disable_cursor(self):
		curses.curs_set(False)