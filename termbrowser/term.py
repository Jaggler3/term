"""
Term Browser - A terminal-based web browser implementation using curses.
"""

import argparse
import curses
import sys
import threading
import time
import traceback
from typing import Optional

import pyperclip

from .browser import Browser
from .rendering.render import renderDocument, renderDebugger
from .util import expand_len, restrict_len, remove_spacing
from .vector import Vec
from .window import Window
from .pieces import get_pieces

# Constants
FPS = 60
ESCAPE_DELAY_MS = 25
DEBUG_WINDOW_HEIGHT = 8
URL_CURSOR = "\N{FULL BLOCK}"
CHECK_MARK = "\N{HEAVY CHECK MARK}"
LOADING_MARK = "\N{DOTTED CIRCLE}"

# Color mapping
COLORMAP = {
	1: curses.COLOR_WHITE,
	2: curses.COLOR_BLACK,
	3: curses.COLOR_BLUE,
	4: curses.COLOR_RED,
	5: curses.COLOR_GREEN,
	6: curses.COLOR_YELLOW,
	7: curses.COLOR_MAGENTA,
	8: curses.COLOR_CYAN,
}

# Input character set
VALID_INPUT_CHARS = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*()-=_+[]{}\|'\";:.>,</?`~"

# Global state
window: Optional[Window] = None
browser: Optional[Browser] = None
user_input: Optional[int] = None
special_keys_input_thread_handle: Optional[threading.Thread] = None
cursor_index: int = -1
scroll: int = 0
document_size: Vec = Vec(0, 0)

def parse_args() -> Optional[str]:
	"""Parse command line arguments."""
	parser = argparse.ArgumentParser()
	parser.add_argument("--url", help="the URL you would like to visit")
	args = parser.parse_args()
	return args.url

def initialize_colors() -> None:
	"""Initialize color pairs for curses."""
	for background in range(1, 9):
		for foreground in range(1, 9):
			key = background * 10 + foreground
			curses.init_pair(key, COLORMAP[foreground], COLORMAP[background])

	curses.set_escdelay(ESCAPE_DELAY_MS)  # Reduce ESC delay to 25ms

def handle_url_input(char: str) -> None:
	"""Handle input when URL bar is focused."""
	global cursor_index, browser
	if not browser:
		return

	if char == chr(226):  # alt + v
		to_insert = remove_spacing(pyperclip.paste())
		browser.URL = browser.URL[:cursor_index] + to_insert + browser.URL[cursor_index:]
		cursor_index += len(to_insert)
	elif char == chr(260):  # left arrow
		cursor_index = max(0, cursor_index - 1)
	elif char == chr(261):  # right arrow
		cursor_index = min(len(browser.URL), cursor_index + 1)
	elif char == chr(127):  # backspace
		if browser.URL and cursor_index > 0:
			browser.URL = browser.URL[:cursor_index - 1] + browser.URL[cursor_index:]
			cursor_index -= 1
	elif char == chr(10):  # enter
		browser.open_link(browser.URL)
		browser.document.focus = -1
		cursor_index = -1
	elif char in VALID_INPUT_CHARS:
		browser.URL = browser.URL[:cursor_index] + char + browser.URL[cursor_index:]
		cursor_index += 1

def handle_element_input(char: str) -> None:
	"""Handle input when an element is focused."""
	global browser
	if not browser:
		return

	focused_element = browser.document.get_focused_element()
	if not focused_element:
		return

	old_index = focused_element.focus_cursor_index
	
	if char == chr(260):  # left arrow
		focused_element.focus_cursor_index = max(0, old_index - 1)
	elif char == chr(261):  # right arrow
		focused_element.focus_cursor_index = min(len(focused_element.value), old_index + 1)
	elif char in VALID_INPUT_CHARS:
		focused_element.value = focused_element.value[:old_index] + char + focused_element.value[old_index:]
		focused_element.focus_cursor_index += 1
		browser.document.change(focused_element)
	elif char == chr(127):  # backspace
		if focused_element.value and old_index > 0:
			focused_element.value = focused_element.value[:old_index - 1] + focused_element.value[old_index:]
			focused_element.focus_cursor_index -= 1
	elif char == chr(10):  # enter
		browser.document.submit(focused_element)
	elif char == chr(197):  # Alt + Q
		browser.document.unfocus()

def handle_special_keys() -> None:
	"""Handle special key inputs."""
	global window, browser, user_input, cursor_index, scroll
	if not window or not browser:
		return

	if user_input == ord("`") and browser.document.focus == -1:
		window.exiting = True
		curses.nocbreak()
		curses.echo()
		window.screen.keypad(0)
		curses.endwin()
		sys.exit(0)
	elif user_input == 203:  # Alt + K
		browser.debugMode = not browser.debugMode
	elif user_input == 9:  # tab
		browser.document.focus_next()
	elif user_input == 27:  # esc
		if browser.document.focus == -1:
			browser.document.unfocus()
			browser.document.focus = -2
			cursor_index = len(browser.URL)
		else:
			browser.document.unfocus()
			browser.document.focus = -1
			cursor_index = -1
	elif user_input == 259:  # up arrow
		scroll = max(0, scroll - 1)
	elif user_input == 258:  # down arrow
		scroll = min(document_size.y - window.HEIGHT, scroll + 1)

def special_keys_input_thread() -> None:
	"""Thread for handling special key inputs."""
	global window, user_input, cursor_index, scroll
	while True:
		user_input = window.get_input()
		handle_special_keys()

		if browser.document.focus != -1:
			handle_element_input(chr(user_input))
		elif browser.document.focus == -2:
			handle_url_input(chr(user_input))
		elif browser.document.find_link(user_input) != -1:
			window.exiting = browser.open_link(browser.document.links[browser.document.find_link(user_input)].URL)

		scroll = max(0, min(scroll, document_size.y - window.HEIGHT))

def render_url_bar() -> None:
	"""Render the URL bar at the top of the screen."""
	global window, browser, cursor_index
	if not window or not browser:
		return

	url_cursor = URL_CURSOR
	render_url_length = window.WIDTH - 1
	draw_cursor_end = browser.URL[cursor_index + 1:] if cursor_index < len(browser.URL) and cursor_index != -1 else ""
	draw_cursor = browser.URL[:cursor_index] + url_cursor + draw_cursor_end
	render_url = expand_len(
		restrict_len(
			draw_cursor if browser.document.focus == -2 else browser.URL,
			render_url_length
		),
		render_url_length
	)
	window.render(render_url, curses.A_UNDERLINE, [2] * len(render_url), [1] * len(render_url))
	window.render(
		CHECK_MARK if not browser.loading else LOADING_MARK,
		curses.A_UNDERLINE,
		[1] * 2,
		[2] * 2
	)

def render_document() -> None:
	"""Render the main document content."""
	global window, browser, document_size
	if not window or not browser:
		return

	output, styles, backgrounds, foregrounds, calculated_size = renderDocument(
		browser.document,
		window.WIDTH,
		window.HEIGHT,
		scroll
	)
	document_size = calculated_size

	backgrounds_flattened = [item for sublist in backgrounds for item in sublist]
	foregrounds_flattened = [item for sublist in foregrounds for item in sublist]
	output = restrict_len(
		remove_spacing(output),
		window.WIDTH * (window.HEIGHT - 1) - 1
	)

	render_pieces = get_pieces(styles, len(output))
	window.start_render(1, 0)
	for piece in render_pieces:
		start_pos, end_pos, col = piece
		partial_backgrounds = backgrounds_flattened[start_pos:end_pos]
		partial_foregrounds = foregrounds_flattened[start_pos:end_pos]
		window.render(output[start_pos:end_pos], col, partial_backgrounds, partial_foregrounds)

def render_debugger() -> None:
	"""Render the debug window if debug mode is enabled."""
	global window, browser
	if not window or not browser or not browser.debugMode:
		return

	window.start_render(window.HEIGHT - DEBUG_WINDOW_HEIGHT, 0)
	debugged = renderDebugger(browser.debugHistory, window.WIDTH, DEBUG_WINDOW_HEIGHT)[:-1]
	window.render(debugged, curses.A_NORMAL, [2] * len(debugged), [1] * len(debugged))

def render() -> None:
	"""Main rendering function."""
	global window, browser
	if not window or not browser:
		return

	window.start_render(0, 0)
	render_url_bar()
	render_document()
	render_debugger()
	window.disable_cursor()

def update() -> None:
	"""Update state."""
	global window, user_input
	if window.exiting:
		sys.exit(0)
	user_input = ""

def lifecycle() -> None:
	"""Main loop."""
	global window, special_keys_input_thread_handle, browser
	if not window or not browser:
		return

	special_keys_input_thread_handle = threading.Thread(
		name="daemon",
		target=special_keys_input_thread,
		args=()
	)
	special_keys_input_thread_handle.setDaemon(True)
	special_keys_input_thread_handle.start()

	while True:
		try:
			if window.get_resized():
				window.resize()
				continue
			update()
			render()
			if browser.loading:
				browser.start_load()
			window.refresh()
			time.sleep(1/FPS)
		except KeyboardInterrupt:
			curses.endwin()
			sys.exit(0)
		except Exception as e:
			traceback.print_exc(file=sys.stdout)
			browser.debug(str(e))

def setup(screen: curses.window) -> None:
	"""Initialize the terminal browser."""
	global window, browser
	window = Window(screen)
	browser = Browser(parse_args() if parse_args() is not None else "term://welcome")
	
	initialize_colors()
	curses.set_escdelay(ESCAPE_DELAY_MS)
	lifecycle()

curses.wrapper(setup)
