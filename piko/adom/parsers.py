"""Parser functions for the ADOM module."""

import xml.etree.ElementTree as ET

from .document import Document
from .elements import Action, Element, createTextElement


def _crashDoc(reason: str, lineNumber: int, browser):
    doc = Document(browser)
    doc.elements = [createTextElement(f"Line {lineNumber + 1}: " + reason)]
    return doc


def xml2doc(contents, browser):
    res = Document(browser)

    try:
        root = ET.fromstring(contents)
    except ET.ParseError as e:
        return _crashDoc(f"XML Parse Error: {str(e)}", 0, browser)

    # Check if it's a valid piko XML file
    if root.tag != "piko":
        return _crashDoc("XML file must have a <piko> root element", 0, browser)

    piko_type = root.get("type")
    if piko_type not in ["m100_xml"]:
        return _crashDoc(f"Unsupported piko type: {piko_type}", 0, browser)

    # background and foreground colors
    background_color = root.get("background")
    foreground_color = root.get("foreground")
    if background_color:
        res.background = background_color
    if foreground_color:
        res.foreground = foreground_color

    # Process child elements
    for child in root:
        if child.tag == "action":
            # Handle action elements
            action_name = child.get("name")
            if action_name and child.text:
                action_code = child.text.strip()
                res.actions.append(Action(action_name, action_code))
        else:
            element = _xml_element_to_adom(child, res)
            if element:
                res.elements.append(element)

    return res


def _xml_element_to_adom(xml_element: ET.Element, document: Document):
    # Map XML tag names to internal element types
    tag_mapping = {
        "container": "cont",
        "text": "text",
        "link": "link",
        "input": "input",
        "br": "br",
        "table": "table",
        "row": "row",
        "cell": "cell",
    }

    tag = xml_element.tag
    if tag not in tag_mapping:
        return None

    element_type = tag_mapping[tag]
    element = Element(element_type)

    # Set element value (text content)
    if xml_element.text and xml_element.text:
        element.value = xml_element.text

    # Convert XML attributes to ADOM attributes
    for attr_name, attr_value in xml_element.attrib.items():
        # Convert some XML attribute names to match the piko format
        if attr_name == "padding-top":
            element.setAttribute("padding-top", attr_value)
        elif attr_name == "padding-bottom":
            element.setAttribute("padding-bottom", attr_value)
        else:
            element.setAttribute(attr_name, attr_value)

    # Handle special cases
    if element_type == "input":
        element.value = element.getAttribute("initial") or ""
        document.hasInputs = True

    if element_type == "link":
        document.add_link(element)

    if element_type == "text" and element.value:
        if (
            not element.getAttribute("preserve")
            or element.getAttribute("preserve") == "false"
        ):
            element.value = element.value.strip()

    # Process child elements recursively
    for child in xml_element:
        child_element = _xml_element_to_adom(child, document)
        if child_element:
            element.appendChild(child_element)
            child_element.parent = element

    return element
