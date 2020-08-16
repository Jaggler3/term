import os
import curses
import threading
import time

from adom import Document, Element
from browser import *
from render import renderDocument
from util import *

stdscr = curses.initscr()

HEIGHT, WIDTH = stdscr.getmaxyx()

exiting = False

URL = "term://welcome"
browser = Browser(URL)

USER_INPUT = None
USER_INPUT_THREAD_HANDLE = None

FRAME_RATE = 30 # 30 frames per second

def setup(screen):
	setup_window()
	lifecycle()

def setup_window():
	curses.noecho()
	stdscr.keypad(True)
	stdscr.clear()

def lifecycle():
	global WIDTH
	global HEIGHT
	global USER_INPUT_THREAD_HANDLE
	# update()

	USER_INPUT_THREAD_HANDLE = threading.Thread(name ='daemon', target=user_input_thread, args=())
	USER_INPUT_THREAD_HANDLE.setDaemon(True)
	USER_INPUT_THREAD_HANDLE.start()

	render()
	stdscr.refresh()

	while True:
		resized = curses.is_term_resized(HEIGHT, WIDTH)
		if resized:
			y, x = stdscr.getmaxyx()
			stdscr.clear()
			curses.resizeterm(y, x)
			WIDTH = x
			HEIGHT = y
			stdscr.refresh()
			continue
		update()
		render()
		if browser.loading:
			browser.start_load()
		stdscr.refresh()
		time.sleep(1.0 / FRAME_RATE)

def user_input_thread():
	global USER_INPUT, exiting, URL
	while True:
		USER_INPUT = stdscr.getch()
		curses.flushinp()
		linkIndex = browser.document.find_link(USER_INPUT)
		if USER_INPUT == ord("`"):
			exiting = True
			exit(0)
		elif USER_INPUT == 9: # tab:
			browser.document.focus_next()
		elif browser.document.focus != -1:
			char = chr(USER_INPUT)
			inputChars = " abcdefghijklmnopqrstuvwxyzABCDEFHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*()-=_+[]{}\|'\";:.>,</?"

			if browser.document.focus == -2: # URL
				if inputChars.find(char) != -1:
					browser.URL += str(char)
				elif USER_INPUT == 127: # backspace
					browser.URL = browser.URL[:-1] if len(browser.URL) > 0 else ""
				elif USER_INPUT == 10: # enter
					browser.open_link(browser.URL)
					browser.document.focus = -1
			else: # input element
				focusedElement = browser.document.get_focused_element()
				if inputChars.find(char) != -1:
					focusedElement.value += str(char)
				elif USER_INPUT == 127: # backspace
					focusedElement.value = focusedElement.value[:-1] if len(focusedElement.value) > 0 else ""
				elif USER_INPUT == 10: # enter
					browser.document.submit(focusedElement)
				elif USER_INPUT == 197: # Alt + Q
					browser.document.unfocus()
		elif USER_INPUT == 27:
			browser.document.unfocus()
			browser.document.focus = -2
		elif linkIndex != -1:
			exiting = browser.open_link(browser.document.links[linkIndex].URL)

def update():
	global USER_INPUT
	global exiting

	if exiting:
		exit(0)
	USER_INPUT = None

def format(string: str):
	return string.replace("\t", "").replace("\n", "")

def render():

	stdscr.move(0, 0)

	renderURL = extlen(
		caplen(
			browser.URL + ("\N{FULL BLOCK}" if browser.document.focus == -2 else ""),
			WIDTH - 2
		),
		WIDTH - 2
	)

	stdscr.addstr(renderURL)

	stdscr.addstr("\N{HEAVY CHECK MARK}" if not browser.loading else "\N{DOTTED CIRCLE}", curses.A_NORMAL)
	
	(output, styles) = renderDocument(browser.document, WIDTH, HEIGHT)
	output = caplen(format(output), (WIDTH * (HEIGHT - 1) - 1))

	stdscr.move(1, 0)
	for i in range(len(styles)):
		current = styles[i]
		follow = None
		if i < len(styles) - 1:
			follow = styles[i + 1]

		startPos = current.start

		endPos = len(output)
		if follow != None:
			endPos = follow.start

		col = curses.A_REVERSE

		if current.style == "bold":
			col += curses.A_BOLD
		elif current.style == "underline":
			col += curses.A_UNDERLINE
		
		stdscr.addstr(output[startPos:endPos], col)
	curses.curs_set(False)

curses.wrapper(setup)