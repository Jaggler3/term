"""Element classes for the ADOM module."""

from typing import List


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
        self.value: str | None = None
        self.attributes: List[Attribute] = []
        self.children: List[Element] = []
        self.focused = False
        self.focus_cursor_index = 0
        self.parent: Element | None = None

    def setAttribute(self, name, value):
        self.attributes.append(Attribute(name, value))

    def getAttribute(self, name) -> str:
        if name != "":
            for item in self.attributes:
                if item.name == name:
                    return item.value
            return None
        else:
            return None

    def appendChild(self, child):
        self.children.append(child)

    def find_element_by_id(self, id: str):
        if self.getAttribute("id") == id:
            return self
        for child in self.children:
            result = child.find_element_by_id(id)
            if result is not None:
                return result
        return None


def createTextElement(value):
    t = Element("text")
    t.value = value
    return t
