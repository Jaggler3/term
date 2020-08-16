import sys
import requests as requests

from term2doc import *

class Browser:
	def __init__(self, initialURL: str):
		self.document = Document(self)
		self.URL = initialURL
		self.loading = True

	def start_load(self):
		if not self.loading:
			return
		self.document = loadFromURL(self.URL, self)
		self.loading = False
		if self.document.hasInputs:
			self.document.focus_next()
	
	# returns if the browser should exit
	def open_link(self, URL: str) -> bool:
		if URL != "term://exit":
			if URL.startswith("term://") and not self.URL.startswith("term://"):
				self.document = Document(self)
				self.document.elements.append(createTextElement("Can not open term:// links. Only Term can open these links."))
			else:
				self.loading = True
				self.URL = URL
			return False
		else:
			return True

"""
term:// -> files in the ./local/ folder of the term project
file:// -> files on the user's computer
http:// & https:// -> files to curl from the internet
"""
def loadFromURL(URL: str, browser: Browser):
	protocol = None
	protocols = ["term://", "http://", "https://"]
	for p in protocols:
		if URL.startswith(p):
			protocol = p
			break
	if protocol == None:
		sys.exit("Error: Could not determine URL protocol `{}`".format(URL))
	elif protocol == "term://":
		file_path = "local/" + URL[len("term://"):] + ".term"
		try:
			stream = open(file_path)
			res = stream.read()
			stream.close()
			return term2doc(res, browser)
		except FileNotFoundError:
			return Document(browser).with_message("Could not load `{}`".format(file_path))
	elif protocol == "https://" or protocol == "http://":
		couldOpen = True
		try:
			r = requests.get(URL)
			return term2doc(r.text, browser)
		except:
			return Document(browser).with_message("Could not load URL.")
	
