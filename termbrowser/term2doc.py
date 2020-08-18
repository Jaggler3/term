from .adom import Document, Element, createTextElement, Action

elementTypes = [
	"cont",
	"text",
	"link",
	"input"
]

validFormats = [
	"m100"
]

def _crashDoc(reason: str, lineNumber: int):
	doc = Document(None)
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
				return _crashDoc("Term files must start with @termtype:[a valid termtype].\nex. @termtype:m100", lineNumber)
			else:
				termstart = digestAttribute(command[1:])
				passes = False
				for tt in validFormats:
					if termstart["value"] == tt:
						passes = True
						break
				if not passes:
					return _crashDoc("Term file is not in a valid format.", lineNumber)
				continue
				
		if readTo > lineNumber:
			continue

		top: Element = getTop(elementQueue)

		if command.startswith("#"):
			continue
		elif command.startswith("-"):
			if top == None:
				return _crashDoc("No element for attribute to be assigned.", lineNumber)
			else:
				result: dict = digestAttribute(command[1:])

				if result == None:
					return _crashDoc("Could not interpret attribute.", lineNumber)
				else:
					top.setAttribute(result["name"], result["value"])
			
		elif command.startswith(tuple(elementTypes)):
			etype, evalue = digestDeclaration(command)
			newElement = Element(etype)
			newElement.value = evalue

			if top != None:
				top.children.append(newElement)

			if etype == "input":
				res.hasInputs = True
			
			elementQueue.append(newElement)
			
		elif command.startswith("end"):
			if top == None:
				return _crashDoc("No element for `end` keyword to complete.", lineNumber)
			else:
				ele: Element = elementQueue.pop()

				if ele.type == "link":
					linkKey = ele.getAttribute("key")
					linkURL = ele.getAttribute("url")
					if(linkKey == None or linkURL == None):
						return _crashDoc("Link element requires attributes (key, url)", lineNumber)
					res.add_link(linkKey, linkURL)

				if len(elementQueue) == 0:
					res.elements.append(ele)
		elif command.startswith("action"):
			comIndex = command.find(":")
			if comIndex == -1:
				return _crashDoc("Could not find `:` following the `action` declaration. This needs to be on the same line.", lineNumber)
			between = command[len("action"):comIndex]
			if between.strip() != "":
				return _crashDoc("Unrecognized `" + between + "`.", lineNumber)
			
			# determine action name
			startIndex = command.find("(", comIndex)
			if startIndex == -1:
				return _crashDoc("Could not find `(` following the `action:` declaration. This needs to be on the same line.", lineNumber)

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
						return _crashDoc("Unexpected `)`.", lineNumber)
				
				actionContents += newLine + "\n"

			if openCount > 0:
				return _crashDoc("Expected ending `)` for action block.", lineNumber)
			elif openCount < 0:
				return _crashDoc("Unexpected `)`.", lineNumber)
			
			actionContents = actionContents[:actionContents.rfind(")")]

			readTo = lineNumber + 1

			res.actions.append(Action(actionName, actionContents))
		elif len(command) > 0:
			return _crashDoc("Could not interpret line format.", lineNumber)
	return res

def digestDeclaration(line: str) -> tuple:
	restype: str = None
	resvalue: str = ""
	for etype in elementTypes:
		if line.startswith(etype):
			restype = etype
			break
	
	if restype == None:
		return None
	else:
		colIndex = line.find(":")
		if colIndex != -1:
			resvalue = line[colIndex + 1:]
		return (restype, resvalue)

def getTop(queue) -> Element:
	return queue[-1] if len(queue) > 0 else None

def digestAttribute(line) -> dict:
	colIndex = line.find(":")
	if colIndex == -1:
		return None
	
	attribName: str = line[:colIndex]
	if len(attribName) == 0:
		return None
	else:
		attribValue: str = line[colIndex + 1:]
		if len(attribValue) == 0:
			return None
		else:
			return { "name": attribName, "value": attribValue.strip() }