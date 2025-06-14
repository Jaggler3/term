from typing import List
from art import text2art

from ..adom.constants import COLORS_PAIRS_REVERSE
from ..adom import Document, Element
from ..vector import *
from ..util import *
from .borders import getBorderCodes
from .style import OutputStyle

from textwrap import TextWrapper

text_wrapper = TextWrapper(
	replace_whitespace=False,
	break_long_words=True,
	expand_tabs=True,
	tabsize=4,
	#drop_whitespace=True # try this out??
)

# Text wrapper that preserves whitespace more strictly
text_wrapper_preserve = TextWrapper(
	replace_whitespace=False,
	break_long_words=True,
	expand_tabs=True,
	tabsize=4,
	drop_whitespace=False
)

# all possible text styling options
TextStyles = (
	"bold",
	"underline"
)

DEFAULT_INPUT_WIDTH = 15

COLORS_PAIRS = {
	1: "white",
	2: "black",
	3: "blue",
	4: "red",
	5: "green",
	6: "yellow",
	7: "magenta",
}

class RenderOutput:
	def __init__(self, rows: list, backgrounds: list, foregrounds: list):
		self.rows = rows
		self.backgrounds = backgrounds
		self.foregrounds = foregrounds

# document --(render)--> list of rows (strings)
def renderDocument(document: Document, width: int, height: int, scroll: int):
	# initialize frame with cleared screen
	background_index = COLORS_PAIRS_REVERSE.get(document.background, COLORS_PAIRS_REVERSE["black"]) if document.background != None else None
	foreground_index = COLORS_PAIRS_REVERSE.get(document.foreground, COLORS_PAIRS_REVERSE["white"]) if document.foreground != None else None
	res = clearScreen(width, height, background_index, foreground_index)

	# initialize frame with single normal style
	styles: List[OutputStyle] = [
		OutputStyle(Vec(0, 0), "normal")
	]

	# cursor starts at the top left corner
	cursor = Vec(0, 0)

	# recursively render all elements to the screen
	for element in document.elements:
		writeSize = renderElement(element, cursor.x, cursor.y - scroll, width, height, res, styles, None)
		# move the cursor down using the size of the rendered element
		cursor.y += writeSize.y

	# combine rows
	out = ""
	for row in res.rows:
		out += row

	# style start changes from Vec(x, y) -> out[i]
	for style in styles:
		style.start = style.start.x + (style.start.y * width)

	return (out, styles, res.backgrounds, res.foregrounds)

# row list filled with empty
def clearScreen(width: int, height: int, background: int, foreground: int) -> RenderOutput:
	return RenderOutput(
		[" " * width] * height,
		[[background for _ in range(width)] for _ in range(height)],
		[[foreground for _ in range(width)] for _ in range(height)]
	)

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

def renderBackground(background_index: int, pos: Vec, size: Vec, res: RenderOutput):
	for y in range(pos.y, pos.y + size.y):
		for x in range(pos.x, pos.x + size.x):
			res.backgrounds[y][x] = background_index

def renderForeground(foreground_index: int, pos: Vec, size: Vec, res: RenderOutput):
	for y in range(pos.y, pos.y + size.y):
		for x in range(pos.x, pos.x + size.x):
			res.foregrounds[y][x] = foreground_index

def renderElement(element: Element, x: int, y: int, WIDTH: int, HEIGHT: int, res: RenderOutput, styles: list, parentSize: Vec):
	# the write size is used to determine how far away the next element in queue should be placed
	writeSize = Vec(0, 0)

	background = element.getAttribute("background")
	background_index = COLORS_PAIRS_REVERSE.get(background, None) if background != None else None
	foreground = element.getAttribute("foreground")
	foreground_index = COLORS_PAIRS_REVERSE.get(foreground, None) if foreground != None else None

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

		# set write size
		if borderType != None:
			writeSize = Vec(contSize.x + 2, contSize.y + 2)
		else:
			writeSize = contSize

		# render background
		if background_index != None:
			renderBackground(background_index, Vec(x, y), writeSize, res)
		if foreground_index != None:
			renderForeground(foreground_index, Vec(x, y), writeSize, res)

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

	elif element.type == "text":
		# has value
		if element.value != "":
			preserve_whitespace = element.getAttribute("preserve") == "true"

			padding = getPadding(element, WIDTH, HEIGHT)

			toRender = getRenderedFont(element.value, preserve_whitespace, element.getAttribute("font"))
			outerSize = parentSize if parentSize != None else Vec(WIDTH - padding['left'] - padding['right'], HEIGHT - padding['top'] - padding['bottom'])
			alignOffset = getAlignOffset(element, toRender, outerSize)
			maxWidth = outerSize.x
			widthAttr = element.getAttribute("width")
			renderWidth = parseSize(widthAttr, maxWidth) if widthAttr != None else maxWidth

			# We need to preserve whitespace when using a custom font to maintain the font's layout
			wrapped_text_size = getWrapAndSize(toRender, renderWidth, True if element.getAttribute("font") else preserve_whitespace)
			wrapped_text: str = wrapped_text_size["text"]
			wrapped_size: Vec = wrapped_text_size["size"]

			writeSize = wrapped_size
			writeSize.x += padding['left'] + padding['right']
			writeSize.y += padding['top'] + padding['bottom']
			boxStartPos = x + alignOffset
			startPos = x + alignOffset + padding['left']

			textStyle = element.getAttribute("style")

			renderRows = wrapped_text.splitlines()
			for rowIndex in range(len(renderRows)):
				rowText = renderRows[rowIndex]
				rowTextLen = len(rowText)
				renderY = y + rowIndex + padding['top']

				# in bounds
				if renderY < len(res.rows) and renderY >= 0:
					# styled text
					if textStyle != None and textStyle.startswith(TextStyles):
						styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
						styles.append(OutputStyle(Vec(startPos + rowTextLen, renderY), "normal"))
					# render single line of text
					res.rows[renderY] = res.rows[renderY][0:startPos] + rowText + res.rows[renderY][startPos + rowTextLen:]

			# render background
			if background_index != None:
				renderBackground(background_index, Vec(boxStartPos, y), writeSize, res)
			if foreground_index != None:
				renderForeground(foreground_index, Vec(boxStartPos, y), writeSize, res)
		else:
			writeSize = Vec(0, 1)

	elif element.type == "link":
		toRender = getLinkText(element)

		outerSize = parentSize if parentSize != None else Vec(WIDTH, HEIGHT)
		alignOffset = getAlignOffset(element, toRender, outerSize)
		maxWidth = outerSize.x
		widthAttr = element.getAttribute("width")
		renderWidth = parseSize(widthAttr, maxWidth) if widthAttr != None else maxWidth

		wrapped = getWrapAndSize(toRender, renderWidth)

		writeSize = wrapped["size"]
		startPos = x + alignOffset

		textStyle = element.getAttribute("style")

		# render background
		if background_index != None:
			renderBackground(background_index, Vec(x, y), writeSize, res)
		if foreground_index != None:
			renderForeground(foreground_index, Vec(x, y), writeSize, res)

		renderRows = wrapped["text"].splitlines()
		for rowIndex in range(len(renderRows)):
			rowText = renderRows[rowIndex]
			rowTextLen = len(rowText)
			renderY = y + rowIndex

			if renderY < len(res.rows) and renderY >= 0:
				endPos = startPos + rowTextLen
				if textStyle != None and textStyle.startswith(TextStyles):
					styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
					styles.append(OutputStyle(Vec(endPos, renderY), "normal"))
				res.rows[renderY] = res.rows[renderY][0:startPos] + rowText + res.rows[renderY][endPos:]

	elif element.type == "input":
		defSize = getDefinedSize(element, WIDTH, HEIGHT)
		calcWidth = defSize.x if defSize.x != -1 else DEFAULT_INPUT_WIDTH
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
		alignOffset = getAlignOffset(element, toRender, outerSize, True)

		borderType = "dotted thick" if element.focused else "dotted thin"
		renderBorder(borderType, Vec(x, y), Vec(toRenderLength, 1), res)
		writeSize = Vec(toRenderLength + 2, 3)
		startPos = x + alignOffset + 1
		renderY = y + 1
		if renderY < len(res.rows) and renderY >= 0:
			res.rows[renderY] = res.rows[renderY][0:startPos] + toRender + res.rows[renderY][startPos + toRenderLength:]

	elif element.type == "br":
		writeSize = Vec(1, 1)

	return writeSize

def getLinkText(element):
	return "[" + element.getAttribute("key") + "] " + element.value

def getWrapAndSize(text: str, maxWidth: int, preserve_whitespace: bool = False):
	if preserve_whitespace:
		# When preserving whitespace, don't do any automatic wrapping
		# Just split by existing line breaks and truncate lines that are too long
		lines = text.splitlines()
		truncated_lines = []
		actual_width = 0
		
		for line in lines:
			if len(line) > maxWidth:
				truncated_line = line[:maxWidth]
				truncated_lines.append(truncated_line)
				actual_width = max(actual_width, maxWidth)
			else:
				truncated_lines.append(line)
				actual_width = max(actual_width, len(line))

		result_text = '\n'.join(truncated_lines)
		return {
			"text": result_text,
			"size": Vec(actual_width, len(truncated_lines))
		}
	else:
		# Use normal text wrapping
		wrapper = text_wrapper
		wrapper.width = maxWidth
		wrappedText = wrapper.fill(text)

		longest_line = max(len(line) for line in wrappedText.splitlines())

		return {
			"text": wrappedText,
			"size": Vec(longest_line, len(wrappedText.splitlines()))
		}

def getRenderedFont(value: str, preserve_whitespace: bool, font: str) -> str:
	if not preserve_whitespace:
		value = value.strip()
	if font:
		return text2art(value, font=font).rstrip()
	return value

def getAlignOffset(element: Element, val: str, parentSize: Vec, isBox: bool = False) -> int:
	if element.type == "link":
		val = getLinkText(element)

	align = element.getAttribute("align")
	defWidth = getDefinedSize(element, parentSize.x, parentSize.y).x
	preserve_whitespace = element.getAttribute("preserve") == "true" if element.type == "text" else False
	
	finalWidth = defWidth if defWidth != -1 else parentSize.x
	if not isBox:
		wrapped = getWrapAndSize(val, defWidth if defWidth != -1 else parentSize.x, preserve_whitespace)
		finalWidth = wrapped["size"].x
	if align == "center":
		return round(float(parentSize.x) / 2.0) - round(float(finalWidth) / 2.0)
	return 0

def getElementSize(element: Element, WIDTH: int, HEIGHT: int) -> Vec:
	if element.type == "text":
		widthAttr = element.getAttribute("width")
		padding = getPadding(element, WIDTH, HEIGHT)
		renderWidth = parseSize(widthAttr, WIDTH - padding['left'] - padding['right']) if widthAttr != None else WIDTH - padding['left'] - padding['right']
		preserve_whitespace = element.getAttribute("preserve") == "true"
		val = getRenderedFont(element.value, preserve_whitespace, element.getAttribute("font"))
		wrapped_text_size = getWrapAndSize(val, renderWidth, preserve_whitespace)
		res = wrapped_text_size["size"]
		res.x += padding['left'] + padding['right']
		res.y += padding['top'] + padding['bottom']
		return res
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

def renderBorder(type: str, pos: Vec, size: Vec, res: RenderOutput):
	screenSize = Vec(len(res.rows[0]), len(res.rows))
	borderCodes = getBorderCodes(type)

	# any of border visible
	if pos.y >= len(res.rows):
		return

	# first row
	if pos.y >= 0:
		firstRow = ""

		# margin
		firstRow += res.rows[pos.y][0:pos.x]

		# top left corner
		firstRow += borderCodes["top-left"]
		# top
		firstRow += borderCodes["top"] * size.x
		# top right corner
		firstRow += borderCodes["top-right"]

		firstRow += res.rows[pos.y][pos.x + 1 + size.x + 1:screenSize.x]

		# establish first row
		res.rows[pos.y] = firstRow if len(firstRow) <= screenSize.x else firstRow[:screenSize.x]

	# middle rows
	for y in range(size.y):
		borderContentY = pos.y + 1 + y
		if borderContentY < len(res.rows) and borderContentY >= 0:
			newRow = res.rows[borderContentY][0:pos.x]
			newRow += borderCodes["left"]
			newRow += res.rows[borderContentY][pos.x + 1:pos.x + 1 + size.x]
			newRow += borderCodes["right"]
			newRow += res.rows[borderContentY][pos.x + 1 + size.x + 1:screenSize.x]
			res.rows[borderContentY] = newRow if len(newRow) <= screenSize.x else newRow[:screenSize.x]

	# last row
	lastBorderContentY = pos.y + size.y + 1
	if lastBorderContentY < len(res.rows) and lastBorderContentY >= 0:
		lastRow = ""
		# margin
		lastRow += res.rows[lastBorderContentY][0:pos.x]

		# bottom left corner
		lastRow += borderCodes["bottom-left"]
		# bottom
		lastRow += borderCodes["bottom"] * size.x
		# bottom right corner
		lastRow += borderCodes["bottom-right"]

		lastRow += res.rows[lastBorderContentY][pos.x + 1 + size.x + 1:screenSize.x]

		# establish last row
		res.rows[lastBorderContentY] = lastRow if len(lastRow) <= screenSize.x else lastRow[:screenSize.x]

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
