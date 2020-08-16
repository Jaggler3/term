from typing import List
import simpleeval
from urllib.parse import quote

class Action:
	def __init__(self, name, contents):
		self.name = name
		self.code = contents

class Attribute:
	def __init__(self, name, value):
		self.name = name
		self.value = value

class Element:
	def __init__(self, type):
		self.type = type
		self.value = None
		self.attributes = []
		self.children = []
		self.focused = False
	
	def setAttribute(self, name, value):
		self.attributes.append(Attribute(name, value))

	def getAttribute(self, name):
		if(name != ""):
			for item in self.attributes:
				if item.name == name:
					return item.value
			return None
		else:
			return None

	def appendChild(self, child):
		self.children.append(child)

def createTextElement(value):
	t = Element("text")
	t.value = value
	return t
	

class DocumentLink:
	def __init__(self, key: chr, URL: str):
		self.key = key
		self.URL = URL

class Document:
	def __init__(self, browser):
		self.browser = browser
		self.links = []
		self.elements = []
		self.actions = []
		self.focus = -1
		self.hasInputs = False
	
	def with_message(self, message: str):
		self.elements = [createTextElement(message)]
		return self

	def focus_next(self):
		self.focus = self._search_focus(self.focus)

	def get_focused_element(self):
		return self.get_focus_list()[self.focus]

	def unfocus(self):
		focus_list: List[Element] = get_all_elements(self.elements)
		for item in focus_list:
			item.focused = False
		self.focus = -1

	def get_focus_list(self):
		all: List[Element] = get_all_elements(self.elements)
		focusable = ("input",)
		focusList: List[Element] = []
		for element in all:
			if element.type.startswith(focusable):
				focusList.append(element)
		return focusList
	
	def _search_focus(self, start: int):
		all: List[Element] = get_all_elements(self.elements)
		focusable = ("input",)
		focusList: List[Element] = []
		for element in all:
			element.focused = False
			if element.type.startswith(focusable):
				focusList.append(element)
		index = start + 1
		index = index if index < len(focusList) else 0
		if len(focusList) > 0:
			focusList[index].focused = True
			return index
		else:
			return -1

	def add_link(self, key: str, URL: str):
		self.links.append(DocumentLink(ord(key), URL))

	def find_link(self, key: int):
		index = 0
		for link in self.links:
			if link.key == key:
				return index
			index += 1
		return -1

	def find_action(self, name: str) -> Action:
		for a in self.actions:
			if a.name == name:
				return a
		return None

	def submit(self, element: Element):
		actionCall = element.getAttribute("submit")
		if actionCall == None:
			return
		action = self.find_action(actionCall)
		if action == None:
			return
		browser_functions = simpleeval.DEFAULT_FUNCTIONS.copy()
		browser_functions.update(
			visit=(self.browser.open_link),
			encode=(quote)
		)
		simpleeval.simple_eval(action.code, names={"value":element.value}, functions=browser_functions)
		

def get_all_elements(elementList: List[Element]):
	res = []
	for element in elementList:
		res.append(element)
		if len(element.children) > 0:
			res.extend(get_all_elements(element.children))
	return res