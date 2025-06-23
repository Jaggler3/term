"""Document class for the ADOM module."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from piko.browser import Browser

from typing import List

import simpleeval

from .constants import URL_BAR_INDEX
from .elements import Action, Element, createTextElement
from .utils import get_all_elements


class Document:
    def __init__(self, browser: "Browser"):
        self.browser = browser
        self.links: List[Element] = []
        self.elements: List[Element] = []
        self.actions: List[Action] = []
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

        # If we're currently focused on the URL bar, try to focus the first element
        if self.focus == URL_BAR_INDEX:
            if len(focusList) > 0:
                element = focusList[0]
                element.focused = True
                element.focus_cursor_index = len(element.value)
                self.focus = 0
            else:
                self.unfocus()
            return

        # If we're focused on an element, try to focus the next one
        if self.focus >= 0:
            next_index = self.focus + 1
            if next_index >= len(focusList):
                # If no more elements, focus URL bar
                self.unfocus()
                self.focus = URL_BAR_INDEX
            else:
                element = focusList[next_index]
                element.focused = True
                element.focus_cursor_index = len(element.value)
                self.focus = next_index
            return

        # If nothing is focused, focus the first element or URL bar
        if len(focusList) > 0:
            element = focusList[0]
            element.focused = True
            element.focus_cursor_index = len(element.value)
            self.focus = 0
        else:
            self.focus = URL_BAR_INDEX

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

    def add_link(self, element: Element):
        key = element.getAttribute("key")
        if key is None:
            return
        if key.isdigit() and (int(key) < 0 or int(key) > 9):
            return
        self.links.append(element)

    def find_link(self, key: int):
        index = 0
        for link in self.links:
            if ord(link.getAttribute("key")) == key:
                return index
            index += 1
        return -1

    def find_action(self, name: str) -> Action:
        for a in self.actions:
            if a.name == name:
                return a
        return None

    def submit(self, element: Element):
        self.call_element_action(element, "submit", {"value": element.value})

    def change(self, element: Element):
        self.call_element_action(element, "change", {"value": element.value})

    def call_action(self, name: str, args: dict):
        action = self.find_action(name)
        if action is None:
            return
        self.evaluator.names = {**args, **self.browser.get_global_variables()}
        self.evaluator.eval("(" + action.code + ")")

    def call_element_action(self, element: Element, name: str, args: dict):
        actionCall = element.getAttribute(name)
        if actionCall is None:
            return
        action = self.find_action(actionCall)
        if action is None:
            return
        self.call_action(actionCall, args)

    def call_document_action(self, name: str, args: dict):
        if name is None:
            return
        name = "[" + name + "]"
        action = self.find_action(name)
        if action is None:
            return
        self.call_action(name, args)
