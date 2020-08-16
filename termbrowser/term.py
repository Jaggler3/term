import os
import curses
import curses.ascii
import threading
import time

from .adom import Document, Element
from .browser import *
from .render import *
from .util import *
from .window import Window

window = Window(curses.initscr())

browser = Browser("term://welcome")

user_input = None
user_input_thread_handle = None

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

def user_input_thread():
	global window, user_input
	while True:
		user_input = window.get_input()
		linkIndex = browser.document.find_link(user_input)
		if user_input == ord("`"):
			window.exiting = True
			exit(0)
		elif user_input == 9: # tab:
			browser.document.focus_next()
		elif browser.document.focus != -1:
			char = chr(user_input)
			inputChars = " abcdefghijklmnopqrstuvwxyzABCDEFHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*()-=_+[]{}\|'\";:.>,</?"

			if browser.document.focus == -2: # URL
				if inputChars.find(char) != -1:
					browser.URL += str(char)
				elif user_input == 127: # backspace
					browser.URL = browser.URL[:-1] if len(browser.URL) > 0 else ""
				elif user_input == 10: # enter
					browser.open_link(browser.URL)
					browser.document.focus = -1
			else: # input element
				focusedElement = browser.document.get_focused_element()
				if inputChars.find(char) != -1:
					focusedElement.value += str(char)
				elif user_input == 127: # backspace
					focusedElement.value = focusedElement.value[:-1] if len(focusedElement.value) > 0 else ""
				elif user_input == 10: # enter
					browser.document.submit(focusedElement)
				elif user_input == 197: # Alt + Q
					browser.document.unfocus()
		elif user_input == 27:
			browser.document.unfocus()
			browser.document.focus = -2
		elif linkIndex != -1:
			exiting = browser.open_link(browser.document.links[linkIndex].URL)

def update():
	global window, user_input
	if window.exiting:
			exit(0)
	user_input = ""

def remove_spacing(string: str):
	return string.replace("\t", "").replace("\n", "")

def render():
	window.start_render(0, 0)

	render_url_length = window.WIDTH - 1
	render_url = expand_len(
		restrict_len(
			browser.URL + ("\N{FULL BLOCK}" if browser.document.focus == -2 else ""),
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

def get_pieces(styles: list, output_len: int):
	pieces = []
	for i in range(len(styles)):
		current = styles[i]
		follow = None
		if i < len(styles) - 1:
			follow = styles[i + 1]

		startPos = current.start

		endPos = output_len
		if follow != None:
			endPos = follow.start

		col = curses.A_REVERSE

		if current.style == "bold":
			col += curses.A_BOLD
		elif current.style == "underline":
			col += curses.A_UNDERLINE
		pieces.append((startPos, endPos, col))
	return pieces

curses.wrapper(setup)