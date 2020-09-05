from .adom import Document, Element
from .vector import *
from .util import *

from textwrap import TextWrapper

text_wrapper = TextWrapper(
	replace_whitespace=False,
	break_long_words=True,
	expand_tabs=True,
	tabsize=4,
	#drop_whitespace=True # try this out??
)

class OutputStyle:
	def __init__(self, start: Vec, style: str):
		self.start = start
		self.style = style

def renderDocument(document: Document, width: int, height: int, scroll: int):
	res = clearScreen(width, height)
	styles: List[OutputStyle] = [
		OutputStyle(Vec(0, 0), "normal")
	]

	cursor = Vec(0, 0)

	for element in document.elements:
		writeSize = renderElement(element, cursor.x, cursor.y - scroll, width, height, res, styles, None)
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

def renderDebugger(text: str, width: int, height: int) -> str:
	textlines = text.splitlines()
	if len(textlines) > height:
		textlines = textlines[-height:]
	out = ""
	for line in textlines:
		out += restrict_len(expand_len(line, width), width)
	
	for i in range(height - len(textlines)):
		out += " " * width
	
	return out
	

allStyles = (
	"bold",
	"underline"
)

def renderElement(element: Element, x: int, y: int, WIDTH: int, HEIGHT: int, res: list, styles: list, parentSize: Vec):
	writeSize = Vec(0, 0)

	if element.type == "cont":
		padding = getPadding(element, WIDTH, HEIGHT)
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
			otherSingleSize = getElementSize(child, WIDTH, HEIGHT)
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
		outerSize = parentSize if parentSize != None else Vec(WIDTH, HEIGHT)
		alignOffset = getAlignOffset(element, outerSize)
		maxWidth = outerSize.x
		widthAttr = element.getAttribute("width")
		renderWidth = parseSize(widthAttr, maxWidth) if widthAttr != None else maxWidth

		wrapped_text_size = getWrapAndSize(element.value, renderWidth)
		wrapped_text = wrapped_text_size["text"]
		wrapped_size = wrapped_text_size["size"]

		writeSize = wrapped_size
		startPos = x + alignOffset

		textStyle = element.getAttribute("style")
		
		renderRows = wrapped_text.splitlines()
		for rowIndex in range(len(renderRows)):
			rowText = renderRows[rowIndex]
			rowTextLen = len(rowText)
			renderY = y + rowIndex

			if renderY < len(res) and renderY >= 0:
				if textStyle != None and textStyle.startswith(allStyles):
					styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
					styles.append(OutputStyle(Vec(startPos + rowTextLen, renderY), "normal"))
				newRow = res[renderY][0:startPos]
				newRow += rowText
				newRow += res[renderY][startPos + rowTextLen:]
				res[renderY] = newRow
		
	elif element.type == "link":
		toRender = getLinkText(element)
		toRenderLength = len(toRender)
		
		outerSize = parentSize if parentSize != None else Vec(WIDTH, HEIGHT)
		alignOffset = getAlignOffset(element, outerSize)
		maxWidth = WIDTH
		if parentSize != None:
			maxWidth = parentSize.x
		widthAttr = element.getAttribute("width")
		renderWidth = parseSize(widthAttr, maxWidth) if widthAttr != None else maxWidth

		wrapped_text_size = getWrapAndSize(toRender, renderWidth)
		wrapped_text = wrapped_text_size["text"]
		wrapped_size = wrapped_text_size["size"]

		writeSize = wrapped_size
		startPos = x + alignOffset

		textStyle = element.getAttribute("style")
		
		renderRows = wrapped_text.splitlines()
		for rowIndex in range(len(renderRows)):
			rowText = renderRows[rowIndex]
			rowTextLen = len(rowText)
			renderY = y + rowIndex
			
			if renderY < len(res) and renderY >= 0:
				if textStyle != None and textStyle.startswith(allStyles):
					styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
					styles.append(OutputStyle(Vec(startPos + rowTextLen, renderY), "normal"))
				newRow = res[renderY][0:startPos]
				newRow += rowText
				newRow += res[renderY][startPos + rowTextLen:]
				res[renderY] = newRow
		
	elif element.type == "input":
		defSize = getDefinedSize(element, WIDTH, HEIGHT)
		calcWidth = defSize.x if defSize.x != -1 else 15
		renderCursor = "\N{FULL BLOCK}" if element.focused else ""
		val = element.value
		idx = element.focus_cursor_index
		draw_cursor_end = val[idx + 1:] if idx < len(val) and idx != -1 else ""
		draw_cursor = val[:idx] + renderCursor + draw_cursor_end
		toRender = rcaplen(
			expand_len(
				draw_cursor if idx != -1 else val,
				calcWidth
			),
			calcWidth
		)

		toRenderLength = len(toRender)

		outerSize = parentSize if parentSize != None else Vec(WIDTH, HEIGHT)
		alignOffset = getAlignOffset(element, outerSize)

		borderType = "dotted thick" if element.focused else "dotted thin"
		renderBorder(borderType, Vec(x, y), Vec(toRenderLength, 1), res)
		writeSize = Vec(toRenderLength, 3)
		startPos = x + alignOffset + 1
		renderY = y + 1
		if renderY < len(res) and renderY >= 0:
			newRow = res[renderY][0:startPos]
			newRow += toRender
			newRow += res[renderY][startPos + toRenderLength:]
			res[renderY] = newRow

	elif element.type == "br":
		writeSize = Vec(1, 1)
	
	return writeSize

def getLinkText(element):
	return "[" + element.getAttribute("key") + "] " + element.value 

def getWrapAndSize(text: str, maxWidth: int):
	if maxWidth == None:
		return {
			"text": text,
			"size": Vec(len(text), 1)
		}
	text_wrapper.width = maxWidth
	wrappedText = text_wrapper.fill(text)
	return {
		"text": wrappedText,
		"size": Vec(maxWidth if maxWidth < len(text) else len(text), len(wrappedText.splitlines()))
	}

def getAlignOffset(element: Element, parentSize: Vec) -> int:
	val = element.value
	if element.type == "link":
		val = getLinkText(element)
	
	align = element.getAttribute("align")
	defWidth = getDefinedSize(element, parentSize.x, parentSize.y).x
	wrapped = getWrapAndSize(val, defWidth if defWidth != -1 else parentSize.x)
	if align == "center":
		return round(float(parentSize.x) / 2.0) - round(float(wrapped["size"].x) / 2.0)
	return 0

def getElementSize(element: Element, WIDTH: int, HEIGHT: int) -> Vec:
	if element.type == "text":
		widthAttr = element.getAttribute("width")
		renderWidth = parseSize(widthAttr, WIDTH) if widthAttr != None else WIDTH
		wrapped_text_size = getWrapAndSize(element.value, renderWidth)
		return wrapped_text_size["size"]
	elif element.type == "link":
		widthAttr = element.getAttribute("width")
		renderWidth = parseSize(widthAttr, WIDTH) if widthAttr != None else WIDTH
		wrapped_text_size = getWrapAndSize(getLinkText(element), renderWidth)
		return wrapped_text_size["size"]
	elif element.type == "input":
		widthAttr = element.getAttribute("width")
		renderWidth = parseSize(widthAttr, WIDTH) if widthAttr != None else WIDTH
		return Vec(renderWidth + 2, 3)
	elif element.type == "cont":
		childrenSize = Vec(0, 0)
		padding = getPadding(element, WIDTH, HEIGHT)
		paddingSize = Vec(padding['left'] + padding['right'], padding['top'] + padding['bottom'])
		defSize = getDefinedSize(element, WIDTH, HEIGHT)
		hasDefWidth = defSize.x != -1
		hasDefHeight = defSize.y != -1

		for child in element.children:
			singleSize = getElementSize(child, WIDTH, HEIGHT)
			direction = getDirection(element)
			if direction == "row":
				childrenSize.x += singleSize.x
				childrenSize.y = max(childrenSize.y, singleSize.y)
			elif direction == "column":
				childrenSize.y += singleSize.y
				childrenSize.x = max(childrenSize.x, singleSize.x)
		
		res = Vec(
			defSize.x if hasDefWidth else childrenSize.x + paddingSize.x,
			defSize.y if hasDefHeight else childrenSize.y + paddingSize.y
		)

		return res
	elif element.type == "br":
		return Vec(1, 1)
	return None

def renderBorder(type: str, pos: Vec, size: Vec, res: list):
	screenSize = Vec(len(res[0]), len(res))
	borderCodes = getBorderCodes(type)
	
	# any of border visible
	if pos.y >= len(res):
		return
	
	# first row
	if pos.y >= 0:
		firstRow = ""
		
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
		borderContentY = pos.y + 1 + y
		if borderContentY < len(res) and borderContentY >= 0:
			newRow = res[borderContentY][0:pos.x]
			newRow += borderCodes["left"]
			newRow += res[borderContentY][pos.x + 1:pos.x + 1 + size.x]
			newRow += borderCodes["right"]
			newRow += res[borderContentY][pos.x + 1 + size.x + 1:screenSize.x]
			res[borderContentY] = newRow if len(newRow) <= screenSize.x else newRow[:screenSize.x]

	# last row
	lastBorderContentY = pos.y + size.y + 1
	if lastBorderContentY < len(res) and lastBorderContentY >= 0:
		lastRow = ""
		# margin
		lastRow += res[lastBorderContentY][0:pos.x]
		
		# bottom left corner
		lastRow += borderCodes["bottom-left"]
		# bottom
		lastRow += borderCodes["bottom"] * size.x
		# bottom right corner
		lastRow += borderCodes["bottom-right"]

		lastRow += res[lastBorderContentY][pos.x + 1 + size.x + 1:screenSize.x]
		
		# establish last row
		res[lastBorderContentY] = lastRow if len(lastRow) <= screenSize.x else lastRow[:screenSize.x]

def getDefinedSize(element: Element, WIDTH: int, HEIGHT: int) -> Vec:
	res = Vec(-1, -1)
	defWidth = element.getAttribute("width")
	defHeight = element.getAttribute("height")
	padding = getPadding(element, WIDTH, HEIGHT)
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

def getPadding(element: Element, width: int, height: int) -> dict:
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
		vert = parseSize(padding, height)
		horiz = parseSize(padding, width)
		paddingOut = {
			'top': vert,
			'bottom': vert,
			'left': horiz,
			'right': horiz
		}
	
	if padding_top != None:
		paddingOut['top'] += parseSize(padding_top, height)
		
	if padding_bottom != None:
		paddingOut['bottom'] += parseSize(padding_bottom, height)
	
	if padding_left != None:
		paddingOut['left'] += parseSize(padding_left, width)

	if padding_right != None:
		paddingOut['right'] += parseSize(padding_right, width)

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