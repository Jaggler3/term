"""Document class for the ADOM module."""

from typing import List
import simpleeval
import termbrowser.browser

from .elements import Element, Action, DocumentLink, createTextElement
from .utils import get_all_elements
from .constants import URL_BAR_INDEX


class Document:
    def __init__(self, browser: termbrowser.browser.Browser):
        self.browser = browser
        self.links = []
        self.elements = []
        self.actions = []
        self.focus = -1
        self.hasInputs = False
        self.background = "black"
        self.foreground = "white"
        self.evaluator = self.createEvaluator()

    def createEvaluator(self):
        e = simpleeval.EvalWithCompoundTypes()
        e.functions = simpleeval.DEFAULT_FUNCTIONS
        e.functions.update(self.browser.script_functions())
        return e
    
    def with_message(self, message: str):
        self.elements = [createTextElement(message)]
        return self

    def focus_next(self):
        all: List[Element] = get_all_elements(self.elements)
        focusable = ("input",)
        focusList: List[Element] = []
        for element in all:
            element.focused = False
            if element.type.startswith(focusable):
                focusList.append(element)
                element.focused = False
        if len(focusList) == 0:
            self.focus = URL_BAR_INDEX # no focusable elements, focus on url bar
            return
        
        next_index = self.focus + 1 if self.focus != URL_BAR_INDEX else 0 # skip -1 (no focus)
        if next_index >= len(focusList):
            next_index = 0
        element = focusList[next_index]
        element.focused = True
        element.focus_cursor_index = len(element.value)
        self.focus = next_index

    def get_focused_element(self):
        if self.focus > -1:	
            return self.get_focus_list()[self.focus]
        return None

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
    
    def _focus_on_url_bar(self):
        self.unfocus()
        self.focus = URL_BAR_INDEX

    def add_link(self, key: str, URL: str):
        if int(key) < 0 or int(key) > 9:
            return
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
        self.call_element_action(element, "submit", {
            "value": element.value
        })
    
    def change(self, element: Element):
        self.call_element_action(element, "change", {
            "value": element.value
        })

    def call_action(self, name: str, args: dict):
        action = self.find_action(name)
        if action == None:
            return
        self.evaluator.names = args
        self.evaluator.eval("(" + action.code + ")")

    def call_element_action(self, element: Element, name: str, args: dict):
        actionCall = element.getAttribute(name)
        if actionCall == None:
            return
        action = self.find_action(actionCall)
        if action == None:
            return
        self.evaluator.names = args
        self.evaluator.eval("(" + action.code + ")")

    def call_document_action(self, name: str, args: dict):
        if name == None:
            return
        action = self.find_action("[" + name + "]")
        if action == None:
            return
        self.evaluator.names = args
        self.evaluator.eval("(" + action.code + ")") 