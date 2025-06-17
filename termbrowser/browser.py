import os
import requests as requests
from time import sleep
import simpleeval
from urllib.parse import quote
import threading

import termbrowser.adom

class Browser:
	def __init__(self, initialURL: str):
		self.document = termbrowser.adom.Document(self)
		self.URL = initialURL
		self.loading = True
		self.context = {}
		self.debugHistory = "Debugger: Press Alt+K to close.\n"
		self.debugMode = False
		self.cursor_index = -1
		self.scroll = 0
		self.document.focus = -1  # Initialize focus to -1 (no focus)
		self.load_thread = None

	def start_load(self):
		if not self.loading:
			return
		if self.load_thread and self.load_thread.is_alive():
			return
		
		self.load_thread = threading.Thread(target=self._load_url)
		self.load_thread.daemon = True
		self.load_thread.start()

	def _load_url(self):
		self.evaluator = self.createEvaluator() # reset evaluator before new page is loaded
		self.document = loadFromURL(self.URL, self)
		sleep(.2)  # Add a small delay to ensure loading indicator is visible
		self.loading = False
		self.document.call_document_action("start", {})
		# Reset focus state
		self.document.unfocus()
		self.cursor_index = -1
		# Only auto-focus if there are inputs and autofocus is enabled
		if self.document.hasInputs:
			self.document.focus_next()
			focused = self.document.get_focused_element()
			if focused and focused.getAttribute("autofocus") == "no":
				self.document.unfocus()

	def createEvaluator(self):
		evaluator = simpleeval.EvalWithCompoundTypes()
		evaluator.functions = simpleeval.DEFAULT_FUNCTIONS
		evaluator.functions.update(self.script_functions())
		return evaluator
	
	# returns if the browser should exit
	def open_link(self, URL: str) -> bool:
		if URL != "term://exit":
			if URL.startswith("term://") and not self.URL.startswith("term://"):
				self.document = termbrowser.adom.Document(self)
				self.document.elements.append(termbrowser.adom.createTextElement("Can not open term:// links. Only Term can open these links."))
			else:
				self.URL = URL
				self.loading = True
			return False
		else:
			return True

	def var(self, name: str, value):
		self.debug(name + ": " + value)
		self.context[name] = value

	def getvar(self, name: str):
		if name in self.context:
			return self.context[name]
		else:
			return "None"

	def encode(self, text: str):
		return quote(text)

	def debug(self, text: str):
		self.debugHistory += text + "\n"
	
	def action(self, name: str):
		self.document.call_action(name, {})

	def script_functions(self):
		return {
			"visit": self.open_link,
			"getvar": self.getvar,
			"var": self.var,
			"action": self.action,
			"encode": self.encode,
			"debug": self.debug
		}

	def focus_url_bar(self) -> None:
		"""Focus the URL bar and set cursor position."""
		self.document.unfocus()
		self.document.focus = -2
		self.cursor_index = len(self.URL)

	def unfocus_url_bar(self) -> None:
		"""Unfocus the URL bar."""
		self.document.unfocus()
		self.document.focus = -1
		self.cursor_index = -1

"""
term:// -> files in the ./local/ folder of the term project
file:// -> files on the user's computer
http:// & https:// -> files to curl from the internet
"""
def loadFromURL(URL: str, browser: Browser):
	if URL == '':
		return termbrowser.adom.Document(browser).with_message("Error: URL is empty")
	protocol = None
	protocols = ["term://", "http://", "https://"]
	for p in protocols:
		if URL.startswith(p):
			protocol = p
			break
	if protocol == None:
		return termbrowser.adom.Document(browser).with_message("Error: Could not determine URL protocol `{}`".format(URL))
	elif protocol == "term://":
		file_path = os.path.dirname(os.path.realpath(__file__)) + "/local/" + URL[len("term://"):] + ".xml"
		try:
			stream = open(file_path)
			res = stream.read()
			stream.close()
			return termbrowser.adom.xml2doc(res, browser)
		except FileNotFoundError:
			return termbrowser.adom.Document(browser).with_message("Could not load `{}`".format(file_path))
	elif protocol == "https://" or protocol == "http://":
		sleep(.1)
		try:
			return makeRequest(browser, URL)
		except Exception as e:
			browser.debug(str(e))
			return termbrowser.adom.Document(browser).with_message("Could not load URL. \n" + str(e))

def makeRequest(browser: Browser, url: str):
	try:
		page = requests.get(url, headers={"Content-Type": "Term"}).text
		return termbrowser.adom.xml2doc(page, browser)
	except Exception as e:
		browser.debug(str(e))
		return termbrowser.adom.Document(browser).with_message("Could not load URL. \n" + str(e))