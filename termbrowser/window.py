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
		curses.flushinp()
		return res
	def start_render(self, y: int, x: 0):
		self.screen.move(y, x)
	def render(self, string: str, option):
		self.screen.addstr(string, option)
	def disable_cursor(self):
		curses.curs_set(False)