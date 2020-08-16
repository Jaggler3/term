from adom import Document, Element
from vector import *
from util import *

class OutputStyle:
	def __init__(self, start: Vec, style: str):
		self.start = start
		self.style = style

def renderDocument(document: Document, width: int, height: int):
	res = clearScreen(width, height)
	styles: List[OutputStyle] = [
		OutputStyle(Vec(0, 0), "normal")
	]

	cursor = Vec(0, 0)

	for element in document.elements:
		writeSize = renderElement(element, cursor.x, cursor.y, width, height, res, styles, None)
		cursor.y += writeSize.y

	# combine rows
	out = ""
	for row in res:
		out += row

	# style Vec -> indices
	for style in styles:
		style.start = style.start.x + (style.start.y * width)
	
	return (out, styles)

def clearScreen(width: int, height: int) -> list:
	return [" " * width] * height

allStyles = (
	"bold",
	"underline"
)

def renderElement(element: Element, x: int, y: int, WIDTH: int, HEIGHT: int, res: list, styles: list, parentSize: Vec):
	writeSize = Vec(0, 0)

	if element.type == "cont":
		padding = getPadding(element)
		direction = getDirection(element)
		borderType = element.getAttribute("border")
		paddingSize = Vec(padding['left'] + padding['right'], padding['top'] + padding['bottom'])

		initialOffset = Vec(padding['left'], padding['top'])

		defSize = getDefinedSize(element, WIDTH, HEIGHT)
		hasDefWidth = defSize.x != -1
		hasDefHeight = defSize.y != -1

		if borderType != None:
			initialOffset.add(1, 1)

		offset = cloneVec(initialOffset)

		childrenSize = Vec(0, 0)

		# get children size (uncalculated pc)
		for child in element.children:
			defSingleSize = getDefinedSize(child, WIDTH, HEIGHT)
			otherSingleSize = getElementSize(child)
			singleSize = Vec(
				otherSingleSize.x if defSingleSize.x == -1 else defSingleSize.x,
				otherSingleSize.y if defSingleSize.y == -1 else defSingleSize.y
			)

			if direction == "row":
				childrenSize.x += singleSize.x
				childrenSize.y = max(childrenSize.y, singleSize.y)
			elif direction == "column":
				childrenSize.y += singleSize.y
				childrenSize.x = max(childrenSize.x, singleSize.x)

		# get defined size -> fallback on children collective size
		contSize = Vec(
			defSize.x if hasDefWidth else childrenSize.x + paddingSize.x,
			defSize.y if hasDefHeight else childrenSize.y + paddingSize.y
		)

		# enforce box-sizing
		if borderType != None:
			contSize.add(-2 if hasDefWidth else 0, -2 if hasDefHeight else 0)

		# render children with clamp, calculated pc
		for child in element.children:
			singleSize = renderElement(child, x + offset.x, y + offset.y, WIDTH, HEIGHT, res, styles, contSize)

			if direction == "row":
				offset.x += singleSize.x
			elif direction == "column":
				offset.y += singleSize.y
		
		# render border
		if borderType != None:
			renderBorder(borderType, Vec(x, y), contSize, res)
			writeSize = Vec(contSize.x + 2, contSize.y + 2)
		else:
			writeSize = contSize

	elif element.type == "text" and element.value != "":
		alignOffset = getAlignOffset(element, parentSize)
		writeSize = Vec(len(element.value), 1)
		startPos = x + alignOffset
		textStyle = element.getAttribute("style")
		if textStyle != None and textStyle.startswith(allStyles):
			styles.append(OutputStyle(Vec(startPos, y), textStyle))
			styles.append(OutputStyle(Vec(startPos + len(element.value), y), "normal"))
		newRow = res[y][0:startPos]
		newRow += element.value
		newRow += res[y][startPos + len(element.value):]
		res[y] = newRow
	elif element.type == "link":
		toRender = getLinkText(element)
		toRenderLength = len(toRender)
		alignOffset = getAlignOffset(element, parentSize)
		writeSize = Vec(toRenderLength, 1)
		startPos = x + alignOffset
		textStyle = element.getAttribute("style")
		if textStyle != None and textStyle.startswith(allStyles):
			styles.append(OutputStyle(Vec(startPos, y), textStyle))
			styles.append(OutputStyle(Vec(startPos + toRenderLength, y), "normal"))
		newRow = res[y][0:startPos]
		newRow += toRender
		newRow += res[y][startPos + toRenderLength:]
		res[y] = newRow
	elif element.type == "input":
		defSize = getDefinedSize(element, WIDTH, HEIGHT)
		calcWidth = defSize.x if defSize.x != -1 else 15
		toRender = rcaplen(extlen(element.value + ("\N{FULL BLOCK}" if element.focused else ""), calcWidth), calcWidth)
		toRenderLength = len(toRender)
		alignOffset = getAlignOffset(element, parentSize)
		borderType = "dotted thick" if element.focused else "dotted thin"
		renderBorder(borderType, Vec(x, y), Vec(toRenderLength, 1), res)
		writeSize = Vec(toRenderLength, 3)
		startPos = x + alignOffset + 1
		newRow = res[y + 1][0:startPos]
		newRow += toRender
		newRow += res[y + 1][startPos + toRenderLength:]
		res[y + 1] = newRow

	return writeSize

def getLinkText(element):
	return "[" + element.getAttribute("key") + "] " + element.value 

def getAlignOffset(element: Element, parentSize: Vec) -> int:
	val = element.value
	if element.type == "link":
		val = getLinkText(element)
	align = element.getAttribute("align")
	if align == "center":
		return round(float(parentSize.x) / 2.0) - round(float(len(val)) / 2.0)
	return 0

def getElementSize(element: Element) -> Vec:
	if element.type == "text":
		return Vec(len(element.value), 1)
	elif element.type == "link":
		return Vec(len(getLinkText(element)), 1)
	elif element.type == "input":
		return Vec(len(extlen(element.value, 10)) + 2, 3)
	elif element.type == "cont":
		childrenSize = Vec(0, 0)
		for child in element.children:
			singleSize = getElementSize(child)
			direction = getDirection(element)
			if direction == "row":
				childrenSize.x += singleSize.x
				childrenSize.y = max(childrenSize.y, singleSize.y)
			elif direction == "column":
				childrenSize.y += singleSize.y
				childrenSize.x = max(childrenSize.x, singleSize.x)
		return childrenSize
	return None

def renderBorder(type: str, pos: Vec, size: Vec, res: list):
	screenSize = Vec(len(res[0]), len(res))
	borderCodes = getBorderCodes(type)

	# first row
	firstRow = ""
	if pos.y >= len(res):
			return
	
	# margin
	firstRow += res[pos.y][0:pos.x]
	
	# top left corner
	firstRow += borderCodes["top-left"]
	# top
	firstRow += borderCodes["top"] * size.x
	# top right corner
	firstRow += borderCodes["top-right"]

	firstRow += res[pos.y][pos.x + 1 + size.x + 1:screenSize.x]

	# establish first row
	res[pos.y] = firstRow if len(firstRow) <= screenSize.x else firstRow[:screenSize.x]

	# middle rows
	for y in range(size.y):
		if pos.y + 1 + y >= len(res):
			break
		
		newRow = res[pos.y + 1 + y][0:pos.x]
		newRow += borderCodes["left"]
		newRow += res[pos.y + 1 + y][pos.x + 1:pos.x + 1 + size.x]
		newRow += borderCodes["right"]
		newRow += res[pos.y + 1 + y][pos.x + 1 + size.x + 1:screenSize.x]
		res[pos.y + 1 + y] = newRow if len(newRow) <= screenSize.x else newRow[:screenSize.x]

	# last row
	lastRow = ""
	if pos.y + size.y + 1 >= len(res):
			return

	# margin
	lastRow += res[pos.y + size.y + 1][0:pos.x]
	
	# bottom left corner
	lastRow += borderCodes["bottom-left"]
	# bottom
	lastRow += borderCodes["bottom"] * size.x
	# bottom right corner
	lastRow += borderCodes["bottom-right"]

	lastRow += res[pos.y + size.y + 1][pos.x + 1 + size.x + 1:screenSize.x]
	
	# establish last row
	res[pos.y + size.y + 1] = lastRow if len(lastRow) <= screenSize.x else lastRow[:screenSize.x]

def getDefinedSize(element: Element, WIDTH: int, HEIGHT: int) -> Vec:
	res = Vec(-1, -1)
	defWidth = element.getAttribute("width")
	defHeight = element.getAttribute("height")
	if defWidth != None:
		res.x = parseSize(defWidth, WIDTH)
	if defHeight != None:
		res.y = parseSize(defHeight, HEIGHT)
	return res

def parseSize(size, MAX) -> int:
	if isInt(size):
		return int(size)
	else:
		last = size[-2:]
		start = size[:-2]
		if isInt(start):
			value = int(start)
			if last == "pc":
				return round(float(MAX) / 100.0 * value)
			else:
				return -1
		else:
			return -1

def getPadding(element: Element) -> dict:
	paddingOut = {
		'top': 0,
		'bottom': 0,
		'left': 0,
		'right': 0
	}
	
	padding = element.getAttribute("padding")
	padding_top = element.getAttribute("padding-top")
	padding_bottom = element.getAttribute("padding-bottom")
	padding_left = element.getAttribute("padding-left")
	padding_right = element.getAttribute("padding-right")

	if padding != None:
		paddingVal = int(padding)
		paddingOut = {
			'top': paddingVal,
			'bottom': paddingVal,
			'left': paddingVal,
			'right': paddingVal
		}
	
	if padding_top != None:
		paddingOut['top'] += int(padding_top)
		
	if padding_bottom != None:
		paddingOut['bottom'] += int(padding_bottom)
	
	if padding_left != None:
		paddingOut['left'] += int(padding_left)

	if padding_right != None:
		paddingOut['right'] += int(padding_right)

	return paddingOut

def getDirection(element: Element) -> str:
	dir = element.getAttribute("direction")
	if dir == None:
		return "column"
	else:
		return dir

def getBorderCodes(type: str) -> dict:
	# defaults are for 'line'
	res = {
		"top-left": "\u2554",
		"top-right": "\u2557",
		"bottom-left": "\u255A",
		"bottom-right": "\u255D",
		"top": "\u2550",
		"bottom": "\u2550",
		"left": "\u2551",
		"right": "\u2551",
	}

	if type == "dotted thick":
		res["top-left"] = "\u250F"
		res["top-right"] = "\u2513"
		res["bottom-left"] = "\u2517"
		res["bottom-right"] = "\u251B"
		res["top"] = "\u2505"
		res["bottom"] = "\u2505"
		res["left"] = "\u2507"
		res["right"] = "\u2507"

	if type == "dotted thin":
		res["top-left"] = "\u250C"
		res["top-right"] = "\u2510"
		res["bottom-left"] = "\u2514"
		res["bottom-right"] = "\u2518"
		res["top"] = "\u2504"
		res["bottom"] = "\u2504"
		res["left"] = "\u2506"
		res["right"] = "\u2506"

	return res