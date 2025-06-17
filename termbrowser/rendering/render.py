from typing import List
import ast

from ..adom.constants import COLORS_PAIRS_REVERSE
from ..adom import Document, Element
from ..vector import *
from ..util import *
from .style import OutputStyle
from .util import getPadding, getDirection, parseSize
from .text_util import getWrapAndSize, getRenderedFont, getLinkText
from .border_util import renderBorder
from .element_util import getAlignOffset, getElementSize
from .style_constants import TextStyles, DEFAULT_INPUT_WIDTH

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

	# mock container with all children to get the size of the document
	mockContainer = Element("cont")
	mockContainer.children = document.elements
	mockContainer.type = "cont"
	mockContainer.setAttribute("width", "100pc")

	mockSize = getElementSize(mockContainer, Vec(width, height))

	# recursively render all elements to the screen
	for element in document.elements:
		writeSize = renderElement(element, cursor.x, cursor.y - scroll, width, height, res, styles, Vec(width, height))
		# move the cursor down using the size of the rendered element
		cursor.y += writeSize.y

	# combine rows
	out = ""
	for row in res.rows:
		out += row

	# style start changes from Vec(x, y) -> out[i]
	for style in styles:
		style.start = style.start.x + (style.start.y * width)

	return (out, styles, res.backgrounds, res.foregrounds, mockSize)

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
		if y < len(res.backgrounds):
			res.backgrounds[y][pos.x:pos.x + size.x] = [background_index] * size.x

def renderForeground(foreground_index: int, pos: Vec, size: Vec, res: RenderOutput):
	for y in range(pos.y, pos.y + size.y):
		if y < len(res.foregrounds):
			res.foregrounds[y][pos.x:pos.x + size.x] = [foreground_index] * size.x

def renderElement(element: Element, x: int, y: int, SCREEN_WIDTH: int, SCREEN_HEIGHT: int, res: RenderOutput, styles: list, parentSize: Vec):
	# the write size is used to determine how far away the next element in queue should be placed
	writeSize = Vec(0, 0)

	background = element.getAttribute("background")
	background_index = COLORS_PAIRS_REVERSE.get(background, None) if background != None else None
	foreground = element.getAttribute("foreground")
	foreground_index = COLORS_PAIRS_REVERSE.get(foreground, None) if foreground != None else None

	if element.type == "cont":
		id = element.getAttribute("id")
		padding = getPadding(element, parentSize.x, parentSize.y)
		direction = getDirection(element)
		borderType = element.getAttribute("border")
		initialOffset = Vec(padding['left'], padding['top'])
		calculatedSize = getElementSize(element, parentSize)

		if borderType != None:
			initialOffset.add(1, 1)

		offset = cloneVec(initialOffset)

		# set write size
		writeSize = calculatedSize

		# render background
		if background_index != None:
			renderBackground(background_index, Vec(x, y), writeSize, res)
		if foreground_index != None:
			renderForeground(foreground_index, Vec(x, y), writeSize, res)

		# render children with clamp, calculated pc
		for child in element.children:
			singleSize = renderElement(child, x + offset.x, y + offset.y, SCREEN_WIDTH, SCREEN_HEIGHT, res, styles, calculatedSize)

			if direction == "row":
				offset.x += singleSize.x
			elif direction == "column":
				offset.y += singleSize.y

		# render border
		if borderType != None:
			renderBorder(borderType, Vec(x, y), calculatedSize, res)

	elif element.type == "text":
		if element.value != "":
			preserve_whitespace = element.getAttribute("preserve") == "true"

			padding = getPadding(element, parentSize.x, parentSize.y)
			paddingSize = Vec(padding['left'] + padding['right'], padding['top'] + padding['bottom'])
			innerSize = parentSize - paddingSize

			maxWidth = innerSize.x
			widthAttr = element.getAttribute("width")
			renderWidth = parseSize(widthAttr, maxWidth) if widthAttr != None else maxWidth

			toRender = getRenderedFont(f"{element.value}", preserve_whitespace, element.getAttribute("font"))
			alignOffset = getAlignOffset(element, toRender, innerSize)

			# We need to preserve whitespace when using a custom font to maintain the font's layout
			wrapped_text_size = getWrapAndSize(toRender, renderWidth, True if element.getAttribute("font") else preserve_whitespace)
			wrapped_text: str = wrapped_text_size["text"]
			wrapped_size: Vec = wrapped_text_size["size"]

			writeSize = wrapped_size + paddingSize
			boxStartPos = x + alignOffset
			startPos = boxStartPos + paddingSize.x

			textStyle = element.getAttribute("style")
			
			renderRows = wrapped_text.splitlines()
			for rowIndex in range(len(renderRows)):
				rowText = renderRows[rowIndex]
				endPos = startPos + len(rowText)

				renderY = y + rowIndex + padding['top']

				# in bounds
				if renderY < len(res.rows) and renderY >= 0:
					# styled text
					if textStyle != None and textStyle.startswith(TextStyles):
						styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
						styles.append(OutputStyle(Vec(startPos + len(rowText), renderY), "normal"))
					# render single line of text
					res.rows[renderY] = res.rows[renderY][0:startPos] + rowText + res.rows[renderY][endPos:]

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
		icon = element.getAttribute("icon")
		calculatedSize = getElementSize(element, parentSize)
		calcWidth = calculatedSize.x if calculatedSize.x != -1 else DEFAULT_INPUT_WIDTH
		renderCursor = "\N{FULL BLOCK}" if element.focused else ""
		val = element.value
		idx = element.focus_cursor_index
		draw_cursor_end = val[idx + 1:] if idx < len(val) and idx != -1 else ""
		draw_cursor = val[:idx] + renderCursor + draw_cursor_end

		innerWidth = calcWidth - 2 # account for border
		if icon != None:
			innerWidth -= 3 # account for icon

		toRender = rcaplen(
			expand_len(
				draw_cursor if idx != -1 else val,
				innerWidth
			),
			innerWidth
		)
		
		# add icon if it exists
		if icon != None:
			icon = ast.literal_eval(f"'{icon}'")
			toRender = f" {icon} {toRender}"

		toRenderLength = len(toRender)

		alignOffset = getAlignOffset(element, toRender, parentSize)

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
