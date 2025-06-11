# > Term Browser <

# interpret args
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--url", help="the URL you would like to visit")
args = parser.parse_args()
INIT_URL = args.url

import os
import traceback
import curses
import threading
import time
import pyperclip

from .adom import Document, Element
from .browser import *
from .rendering.render import *
from .util import *
from .window import Window
from .pieces import get_pieces

window: Window = Window(curses.initscr())

browser: Browser = Browser(INIT_URL if INIT_URL != None else "term://welcome")

user_input = None
special_keys_input_thread_handle = None
text_input_thread_handle = None
cursor_index: int = -1
scroll: int = 0

paste_mode: bool = False

fps: int = 60 # 20 frames per second

def setup(screen):
	curses.start_color()
	curses.use_default_colors()
	curses.init_pair(1, -1, curses.COLOR_WHITE)
	curses.init_pair(2, -1, curses.COLOR_BLACK)
	curses.set_escdelay(25)  # Reduce ESC delay to 25ms
	window = Window(screen)
	lifecycle()

def lifecycle():
	global window, text_input_thread_handle, special_keys_input_thread_handle

	# text_input_thread_handle = threading.Thread(name="daemon", target=text_input_thread, args=())
	# text_input_thread_handle.setDaemon(True)
	# text_input_thread_handle.start()

	special_keys_input_thread_handle = threading.Thread(name="daemon", target=special_keys_input_thread, args=())
	special_keys_input_thread_handle.setDaemon(True)
	special_keys_input_thread_handle.start()

	render()

	while True:
		try:
			resized = window.get_resized()
			if resized:
				window.resize()
				continue
			update()
			render()
			if browser.loading:
				browser.start_load()
			window.refresh()
			time.sleep(0.01)
		except KeyboardInterrupt:
			curses.endwin()
			sys.exit(0)
		except Exception as e:
			# curses.endwin()
			traceback.print_exc(file=sys.stdout)
			browser.debug(str(e))

def text_input_thread():
	global window, user_input, cursor_index, scroll
	while True:
		user_input = window.get_input_text()
		browser.debugHistory += f"Text Input: {user_input}\n"
		time.sleep(0.01)


def special_keys_input_thread():
	global window, user_input, cursor_index, scroll
	while True:
		user_input = window.get_input()
		browser.debugHistory += f"Special Keys Input: {user_input} \n"
		browser.debugHistory += f"Focus: {browser.document.focus} \n"

		if user_input == ord("`") and browser.document.focus == -1:
			window.exiting = True
			curses.nocbreak()
			curses.echo()
			window.screen.keypad(0)
			curses.endwin()
			exit(0)
		elif user_input == 203: # Alt + K (or Alt + I + I?)
			browser.debugMode = not browser.debugMode
		elif user_input == 9: # tab:
			browser.document.focus_next()
			# _focused = browser.document.get_focused_element()
		elif user_input == 27: # esc
			browser.debugHistory += f"Esc: {user_input}\n"
			browser.document.unfocus()
			browser.document.focus = -2
			cursor_index = len(browser.URL)
		elif user_input == 259: # up arrow
			scroll -= 1 if scroll > 0 else 0
		elif user_input == 258: # down arrow
			scroll += 1
		elif browser.document.focus != -1:
			char = chr(user_input)
			inputChars = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*()-=_+[]{}\|'\";:.>,</?`~"
			# use for debugging
			# browser.URL += str(user_input) + char
			if browser.document.focus == -2: # URL
				if user_input == 226: # alt + v to enable paste
					toInsert = remove_spacing(pyperclip.paste())
					browser.URL = browser.URL[:cursor_index] + toInsert + browser.URL[cursor_index:]
					cursor_index += len(toInsert)
				elif user_input == 260: # left arrow
					cursor_index -= 1 if cursor_index != 0 else 0
				elif user_input == 261: # right arrow
					cursor_index += 1 if cursor_index != len(browser.URL) else 0
				elif user_input == 127: # backspace
					if len(browser.URL) == 0 or cursor_index == 0:
						continue
					browser.URL = browser.URL[:cursor_index - 1] + browser.URL[cursor_index:]
					cursor_index -= 1
				elif user_input == 10: # enter
					browser.open_link(browser.URL)
					browser.document.focus = -1
					cursor_index = -1
				elif inputChars.find(char) != -1:
					browser.URL = browser.URL[:cursor_index] + str(char) + browser.URL[cursor_index:]
					cursor_index += 1
			else: # input element
				focusedElement = browser.document.get_focused_element()

				old_index = focusedElement.focus_cursor_index
				if user_input == 260: # left arrow
					focusedElement.focus_cursor_index -= 1 if old_index != 0 else 0
				elif user_input == 261: # right arrow
					focusedElement.focus_cursor_index += 1 if old_index != len(focusedElement.value) else 0

				elif inputChars.find(char) != -1:
					focusedElement.value = focusedElement.value[:old_index] + str(char) + focusedElement.value[old_index:]
					focusedElement.focus_cursor_index += 1
					browser.document.change(focusedElement)
				elif user_input == 127: # backspace
					if len(focusedElement.value) == 0 or old_index == 0:
						continue
					focusedElement.value = focusedElement.value[:old_index - 1] + focusedElement.value[old_index:]
					focusedElement.focus_cursor_index -= 1
				elif user_input == 10: # enter
					browser.document.submit(focusedElement)
				elif user_input == 197: # Alt + Q
					browser.document.unfocus()
		elif browser.document.find_link(user_input) != -1:
			window.exiting = browser.open_link(browser.document.links[browser.document.find_link(user_input)].URL)

def update():
	global window, user_input
	if window.exiting:
		exit(0)
	if browser.loading:
		cursor_index = -1
	user_input = ""

def remove_spacing(string: str):
	return string.replace("\t", "").replace("\n", "")

def render():
	window.start_render(0, 0)

	# URL
	url_cursor = "\N{FULL BLOCK}"
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
	window.render(render_url, curses.A_UNDERLINE, [2] * len(render_url))
	# Check and Loading symbols
	window.render("\N{HEAVY CHECK MARK}" if not browser.loading else "\N{DOTTED CIRCLE}", curses.A_UNDERLINE, [1])

	# Document
	(output, styles, backgrounds) = renderDocument(browser.document, window.WIDTH, window.HEIGHT, scroll)
	backgrounds_flattened = [item for sublist in backgrounds for item in sublist]
	output = restrict_len(
		remove_spacing(output),
		window.WIDTH * (window.HEIGHT - 1) - 1 # remove last line to account for URL bar, remove last character to stop scroll
	)
	render_pieces = get_pieces(styles, len(output))
	window.start_render(1, 0)
	for piece in render_pieces:
		(startPos, endPos, col) = piece
		partial_backgrounds = backgrounds_flattened[startPos:endPos]
		window.render(output[startPos:endPos], col, partial_backgrounds)

	# Debugger
	debugHeight = 8
	if browser.debugMode:
		window.start_render(window.HEIGHT - debugHeight, 0)
		debugged = renderDebugger(browser.debugHistory, window.WIDTH, debugHeight)[:-1]
		window.render(debugged, curses.A_NORMAL, [2] * len(debugged))

	# Disable Cursor
	window.disable_cursor()



curses.wrapper(setup)
