"""Parser functions for the ADOM module."""

import xml.etree.ElementTree as ET

from .document import Document
from .elements import Element, Action, createTextElement
from .utils import getTop, digestAttribute, digestDeclaration
from .constants import elementTypes, validFormats


def _crashDoc(reason: str, lineNumber: int, browser):
    doc = Document(browser)
    doc.elements = [createTextElement("Line {}: ".format(lineNumber + 1) + reason)]
    return doc


def term2doc(contents, browser):
    res = Document(browser)

    contents = contents.strip(" \n\r")
    lines: list = contents.splitlines()
    
    elementQueue: list = []

    readTo = -1
    for lineNumber in range(len(lines)):
        command: str = lines[lineNumber].strip()

        if lineNumber == 0:
            if not command.startswith("@termtype"):
                return _crashDoc("Term files must start with @termtype:[a valid termtype].\nex. @termtype:m100", lineNumber, browser)
            else:
                termstart = digestAttribute(command[1:])
                passes = False
                for tt in validFormats:
                    if termstart["value"] == tt:
                        passes = True
                        break
                if not passes:
                    return _crashDoc("Term file is not in a valid format.", lineNumber, browser)
                continue
                
        if readTo > lineNumber:
            continue

        top: Element = getTop(elementQueue)

        if command.startswith("#"):
            continue
        elif command.startswith("-"):
            if top == None:
                return _crashDoc("No element for attribute to be assigned.", lineNumber, browser)
            else:
                result: dict = digestAttribute(command[1:])

                if result == None:
                    return _crashDoc("Could not interpret attribute.", lineNumber, browser)
                else:
                    top.setAttribute(result["name"], result["value"])
                    if result["name"] == "initial" and top.type == "input":
                        top.value = result["value"]
            
        elif command.startswith(tuple(elementTypes)):
            etype, evalue = digestDeclaration(command)
            newElement = Element(etype)
            newElement.value = evalue

            if top != None:
                top.children.append(newElement)

            if etype == "input":
                res.hasInputs = True
            
            if etype != "br": # br does not have an ending tag and cannot have chilren
                elementQueue.append(newElement)
            
        elif command.startswith("end"):
            if top == None:
                return _crashDoc("No element for `end` keyword to complete.", lineNumber, browser)
            else:
                ele: Element = elementQueue.pop()

                if ele.type == "link":
                    linkKey = ele.getAttribute("key")
                    linkURL = ele.getAttribute("url")
                    if(linkKey == None or linkURL == None):
                        return _crashDoc("Link element requires attributes (key, url)", lineNumber, browser)
                    res.add_link(linkKey, linkURL)

                if len(elementQueue) == 0:
                    res.elements.append(ele)
        elif command.startswith("action"):
            comIndex = command.find(":")
            if comIndex == -1:
                return _crashDoc("Could not find `:` following the `action` declaration. This needs to be on the same line.", lineNumber, browser)
            between = command[len("action"):comIndex]
            if between.strip() != "":
                return _crashDoc("Unrecognized `" + between + "`.", lineNumber, browser)
            
            # determine action name
            startIndex = command.find("(", comIndex)
            if startIndex == -1:
                return _crashDoc("Could not find `(` following the `action:` declaration. This needs to be on the same line.", lineNumber, browser)

            actionName = command[comIndex + 1:startIndex].strip()

            # track opening parenthesis to determine the end of the action, set to 1 because the action block is wrapped in parenthesis
            openCount = 1

            firstRow = command[startIndex + 1:].strip()

            # start to build the contents of the action
            actionContents = firstRow + "\n"

            for c in firstRow:
                if c == "(":
                    openCount += 1
                elif c == ")":
                    openCount -= 1

            # move onto other lines, action block is still open
            while openCount != 0 and lineNumber < len(lines) - 1:
                lineNumber += 1
                newLine = lines[lineNumber].strip()
                for c in newLine:
                    if c == "(":
                        openCount += 1
                    elif c == ")":
                        openCount -= 1

                    if openCount < 0:
                        return _crashDoc("Unexpected `)`.", lineNumber, browser)
                
                actionContents += newLine + "\n"

            if openCount > 0:
                return _crashDoc("Expected ending `)` for action block.", lineNumber, browser)
            elif openCount < 0:
                return _crashDoc("Unexpected `)`.", lineNumber, browser)
            
            actionContents = actionContents[:actionContents.rfind(")")]

            readTo = lineNumber + 1

            res.actions.append(Action(actionName, actionContents))
        elif len(command) > 0:
            return _crashDoc("Could not interpret line format.", lineNumber, browser)
    return res


def xml2doc(contents, browser):
    res = Document(browser)
    
    try:
        root = ET.fromstring(contents)
    except ET.ParseError as e:
        return _crashDoc(f"XML Parse Error: {str(e)}", 0, browser)
    
    # Check if it's a valid term XML file
    if root.tag != "term":
        return _crashDoc("XML file must have a <term> root element", 0, browser)
    
    term_type = root.get("type")
    if term_type not in ["m100_xml"]:
        return _crashDoc(f"Unsupported term type: {term_type}", 0, browser)
    
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


def _xml_element_to_adom(xml_element, document):
    # Map XML tag names to internal element types
    tag_mapping = {
        "container": "cont",
        "text": "text",
        "link": "link",
        "input": "input",
        "br": "br"
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
        # Convert some XML attribute names to match the term format
        if attr_name == "padding-top":
            element.setAttribute("padding-top", attr_value)
        elif attr_name == "padding-bottom":
            element.setAttribute("padding-bottom", attr_value)
        else:
            element.setAttribute(attr_name, attr_value)
    
    # Handle special cases
    if element_type == "input" and element.getAttribute("initial"):
        element.value = element.getAttribute("initial")
        document.hasInputs = True
    
    if element_type == "link":
        link_key = element.getAttribute("key")
        link_url = element.getAttribute("url")
        if link_key and link_url:
            document.add_link(link_key, link_url)
    
    # Process child elements recursively
    for child in xml_element:
        child_element = _xml_element_to_adom(child, document)
        if child_element:
            element.appendChild(child_element)
    
    return element 