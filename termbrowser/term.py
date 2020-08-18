import os
import curses
import threading
import time
import pyperclip

from .adom import Document, Element
from .browser import *
from .render import *
from .util import *
from .window import Window
from .pieces import get_pieces

window = Window(curses.initscr())

browser = Browser("term://welcome")

user_input = None
user_input_thread_handle = None
cursor_index = -1

paste_mode = False

fps = 30 # 30 frames per second

def setup(screen):
	lifecycle()

def lifecycle():
	global window, user_input_thread_handle

	user_input_thread_handle = threading.Thread(name ='daemon', target=user_input_thread, args=())
	user_input_thread_handle.setDaemon(True)
	user_input_thread_handle.start()

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
			time.sleep(1.0 / fps)
		except KeyboardInterrupt:
			sys.exit(0)
		except Exception as e:
			exit(str(e))
		

def user_input_thread():
	global window, user_input, cursor_index
	while True:
		user_input = window.get_input()
		linkIndex = browser.document.find_link(user_input)
		if user_input == ord("`") and browser.document.focus == -1:
			window.exiting = True
			exit(0)
		elif user_input == 9: # tab:
			browser.document.focus_next()
			_focused = browser.document.get_focused_element()
			_focused.focus_cursor_index = len(_focused.value)
		elif browser.document.focus != -1:
			char = chr(user_input)
			inputChars = " abcdefghijklmnopqrstuvwxyzABCDEFHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*()-=_+[]{}\|'\";:.>,</?`~"
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

				if user_input == 226: # alt + v to enable paste
					toInsert = remove_spacing(pyperclip.paste())
					focusedElement.value = focusedElement.value[:old_index] + toInsert + focusedElement.value[old_index:]
					focusedElement.focus_cursor_index += len(toInsert)
				elif user_input == 260: # left arrow
					focusedElement.focus_cursor_index -= 1 if old_index != 0 else 0
				elif user_input == 261: # right arrow
					focusedElement.focus_cursor_index += 1 if old_index != len(focusedElement.value) else 0

				elif inputChars.find(char) != -1:
					focusedElement.value = focusedElement.value[:old_index] + str(char) + focusedElement.value[old_index:]
					focusedElement.focus_cursor_index += 1
				elif user_input == 127: # backspace
					if len(focusedElement.value) == 0 or old_index == 0:
						continue
					focusedElement.value = focusedElement.value[:old_index - 1] + focusedElement.value[old_index:]
					focusedElement.focus_cursor_index -= 1
				elif user_input == 10: # enter
					browser.document.submit(focusedElement)
				elif user_input == 197: # Alt + Q
					browser.document.unfocus()
		elif user_input == 27: # esc
			browser.document.unfocus()
			browser.document.focus = -2
			cursor_index = len(browser.URL)
		elif linkIndex != -1:
			exiting = browser.open_link(browser.document.links[linkIndex].URL)

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

	window.render(render_url, curses.A_UNDERLINE)
	window.render("\N{HEAVY CHECK MARK}" if not browser.loading else "\N{DOTTED CIRCLE}", curses.A_UNDERLINE)
	
	(output, styles) = renderDocument(browser.document, window.WIDTH, window.HEIGHT)
	output = restrict_len(
		remove_spacing(output),
		window.WIDTH * (window.HEIGHT - 1) - 1 # remove last line to account for URL bar, remove last character to stop scroll
	)
	render_pieces = get_pieces(styles, len(output))

	window.start_render(1, 0)
	
	for piece in render_pieces:
		(startPos, endPos, col) = piece
		window.render(output[startPos:endPos], col)
	
	window.disable_cursor()



curses.wrapper(setup)