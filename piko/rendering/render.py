import ast
from typing import List

from ..adom import Document, Element
from ..adom.constants import COLORS_PAIRS_REVERSE
from ..util import expand_len, rcaplen, restrict_len
from ..vector import Vec, cloneVec
from .border_util import renderBorder, renderTableBorder
from .element_util import getAlignOffset, getElementSize
from .style import OutputStyle
from .style_constants import TextStyles
from .text_util import getLinkText, getRenderedFont, getWrapAndSize
from .util import getDirection, getPadding, parseSize


class RenderOutput:
    def __init__(self, rows: list, backgrounds: list, foregrounds: list):
        self.rows = rows
        self.backgrounds = backgrounds
        self.foregrounds = foregrounds


# document --(render)--> list of rows (strings)
def renderDocument(document: Document, width: int, height: int, scroll: int):
    # initialize frame with cleared screen
    background_index = (
        COLORS_PAIRS_REVERSE.get(document.background, COLORS_PAIRS_REVERSE["black"])
        if document.background is not None
        else None
    )
    foreground_index = (
        COLORS_PAIRS_REVERSE.get(document.foreground, COLORS_PAIRS_REVERSE["white"])
        if document.foreground is not None
        else None
    )
    res = clearScreen(width, height, background_index, foreground_index)

    # initialize frame with single normal style
    styles: List[OutputStyle] = [OutputStyle(Vec(0, 0), "normal")]

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
        writeSize = renderElement(
            element,
            cursor.x,
            cursor.y - scroll,
            width,
            height,
            res,
            styles,
            Vec(width, height),
        )
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
def clearScreen(
    width: int, height: int, background: int, foreground: int
) -> RenderOutput:
    return RenderOutput(
        [" " * width] * height,
        [[background for _ in range(width)] for _ in range(height)],
        [[foreground for _ in range(width)] for _ in range(height)],
    )


def renderDebugger(text: str, width: int, height: int) -> str:
    textlines = text.splitlines()
    if len(textlines) > height:
        textlines = textlines[-height:]
    out = ""
    for line in textlines:
        out += restrict_len(expand_len(line, width), width)

    for _ in range(height - len(textlines)):
        out += " " * width

    return out


def renderBackground(background_index: int, pos: Vec, size: Vec, res: RenderOutput):
    for y in range(pos.y, pos.y + size.y):
        if y < len(res.backgrounds):
            res.backgrounds[y][pos.x : pos.x + size.x] = [background_index] * size.x


def renderForeground(foreground_index: int, pos: Vec, size: Vec, res: RenderOutput):
    for y in range(pos.y, pos.y + size.y):
        if y < len(res.foregrounds):
            res.foregrounds[y][pos.x : pos.x + size.x] = [foreground_index] * size.x


def renderElement(
    element: Element,
    x: int,
    y: int,
    SCREEN_WIDTH: int,
    SCREEN_HEIGHT: int,
    res: RenderOutput,
    styles: list,
    parentSize: Vec,
):
    # the write size is used to determine how far away the next element in queue should be placed
    writeSize = Vec(0, 0)

    background = element.getAttribute("background")
    background_index = (
        COLORS_PAIRS_REVERSE.get(background, None) if background is not None else None
    )
    foreground = element.getAttribute("foreground")
    foreground_index = (
        COLORS_PAIRS_REVERSE.get(foreground, None) if foreground is not None else None
    )

    if element.type == "cont":
        padding = getPadding(element, parentSize.x, parentSize.y)
        direction = getDirection(element)
        borderType = element.getAttribute("border")

        writeSize = getElementSize(element, parentSize)

        paddingSize = Vec(
            padding["left"] + padding["right"], padding["top"] + padding["bottom"]
        )
        innerSize = writeSize - paddingSize

        initialOffset = Vec(padding["left"], padding["top"])
        if borderType is not None:
            initialOffset.x += 1
            initialOffset.y += 1
            innerSize.x -= 2
            innerSize.y -= 2

        offset = cloneVec(initialOffset)

        if background_index is not None:
            renderBackground(background_index, Vec(x, y), writeSize, res)
        if foreground_index is not None:
            renderForeground(foreground_index, Vec(x, y), writeSize, res)

        # render children with clamp, calculated pc
        for child in element.children:
            singleSize = renderElement(
                child,
                x + offset.x,
                y + offset.y,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                res,
                styles,
                innerSize,
            )

            if direction == "row":
                offset.x += singleSize.x
            elif direction == "column":
                offset.y += singleSize.y

        # render border
        if borderType is not None:
            renderBorder(borderType, Vec(x, y), writeSize, res)

    elif element.type == "text":
        val = element.value or ""
        if len(val) > 0:
            preserve_whitespace = element.getAttribute("preserve") == "true"

            padding = getPadding(element, parentSize.x, parentSize.y)
            paddingSize = Vec(
                padding["left"] + padding["right"], padding["top"] + padding["bottom"]
            )
            innerSize = parentSize - paddingSize

            maxWidth = innerSize.x
            widthAttr = element.getAttribute("width")
            renderWidth = (
                parseSize(widthAttr, maxWidth) if widthAttr is not None else maxWidth
            )

            toRender = getRenderedFont(
                f"{element.value}", preserve_whitespace, element.getAttribute("font")
            )
            alignOffset = getAlignOffset(element, toRender, innerSize)

            # We need to preserve whitespace when using a custom font to maintain the font's layout
            wrapped_text_size = getWrapAndSize(
                toRender,
                renderWidth,
                (
                    True
                    if element.getAttribute("font") is not None
                    else preserve_whitespace
                ),
            )
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

                renderY = y + rowIndex + padding["top"]

                # in bounds
                if renderY < len(res.rows) and renderY >= 0:
                    # styled text
                    if textStyle is not None and textStyle.startswith(TextStyles):
                        styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
                        styles.append(
                            OutputStyle(Vec(startPos + len(rowText), renderY), "normal")
                        )
                    # render single line of text
                    res.rows[renderY] = (
                        res.rows[renderY][0:startPos]
                        + rowText
                        + res.rows[renderY][endPos:]
                    )

            # render background
            if background_index is not None:
                renderBackground(background_index, Vec(boxStartPos, y), writeSize, res)
            if foreground_index is not None:
                renderForeground(foreground_index, Vec(boxStartPos, y), writeSize, res)
        else:
            writeSize = Vec(0, 1)

    elif element.type == "link":
        toRender = getLinkText(element)

        outerSize = parentSize
        alignOffset = getAlignOffset(element, toRender, outerSize)
        maxWidth = outerSize.x
        widthAttr = element.getAttribute("width")
        renderWidth = (
            parseSize(widthAttr, maxWidth) if widthAttr is not None else maxWidth
        )

        wrapped = getWrapAndSize(toRender, renderWidth)

        writeSize = wrapped["size"]
        startPos = x + alignOffset

        textStyle = element.getAttribute("style")

        # render background
        if background_index is not None:
            renderBackground(background_index, Vec(x, y), writeSize, res)
        if foreground_index is not None:
            renderForeground(foreground_index, Vec(x, y), writeSize, res)

        renderRows = wrapped["text"].splitlines()
        for rowIndex in range(len(renderRows)):
            rowText = renderRows[rowIndex]
            rowTextLen = len(rowText)
            renderY = y + rowIndex

            if renderY < len(res.rows) and renderY >= 0:
                endPos = startPos + rowTextLen
                if textStyle is not None and textStyle.startswith(TextStyles):
                    styles.append(OutputStyle(Vec(startPos, renderY), textStyle))
                    styles.append(OutputStyle(Vec(endPos, renderY), "normal"))
                res.rows[renderY] = (
                    res.rows[renderY][0:startPos] + rowText + res.rows[renderY][endPos:]
                )

    elif element.type == "input":
        icon = element.getAttribute("icon")
        mask = element.getAttribute("mask")
        lines_attr = element.getAttribute("lines")
        lines = int(lines_attr) if lines_attr else 1

        calculatedSize = getElementSize(element, parentSize)
        calcWidth = calculatedSize.x
        renderCursor = "\N{FULL BLOCK}" if element.focused else ""
        val = element.value or ""
        idx = element.focus_cursor_index

        # Handle multi-line input
        if lines > 1:
            # Split value into lines
            val_lines = val.split("\n") if val else [""]

            # Calculate cursor position across lines
            current_pos = 0
            cursor_line = 0
            cursor_col = 0
            for i, line in enumerate(val_lines):
                if current_pos + len(line) >= idx:
                    cursor_line = i
                    cursor_col = idx - current_pos
                    break
                current_pos += len(line) + 1  # +1 for newline
            else:
                # Cursor is at the end
                cursor_line = len(val_lines) - 1
                cursor_col = len(val_lines[cursor_line])

            # Calculate which lines to display (scrolling)
            start_line = max(0, cursor_line - lines + 1) if cursor_line >= lines else 0
            end_line = min(len(val_lines), start_line + lines)

            # Get the lines to display
            display_lines = val_lines[start_line:end_line]

            # Pad with empty lines if needed
            while len(display_lines) < lines:
                display_lines.append("")

            # Adjust cursor line for display
            display_cursor_line = cursor_line - start_line

            # Apply mask if specified
            if mask:
                display_lines = [mask * len(line) for line in display_lines]

            # Render each line
            innerWidth = calcWidth - 2  # account for border
            if icon is not None:
                innerWidth -= 3  # account for icon

            alignOffset = getAlignOffset(element, " " * innerWidth, parentSize)
            borderType = "thin"

            writeSize = Vec(innerWidth, lines)

            # Render border
            renderBorder(borderType, Vec(x, y), writeSize, res)

            # Clear the inside of the input area before rendering text
            for i in range(lines):
                renderY = y + 1 + i
                start_pos = x + alignOffset + 1
                # Ensure we don't write past the screen width
                clear_width = min(innerWidth, SCREEN_WIDTH - start_pos)
                if (
                    renderY < SCREEN_HEIGHT
                    and start_pos < SCREEN_WIDTH
                    and clear_width > 0
                ):
                    res.rows[renderY] = (
                        res.rows[renderY][:start_pos]
                        + " " * clear_width
                        + res.rows[renderY][start_pos + clear_width :]
                    )

            # Render each line
            for line_idx in range(lines):
                line_text = (
                    display_lines[line_idx] if line_idx < len(display_lines) else ""
                )

                # Add cursor if this is the focused line and element is focused
                if element.focused and line_idx == display_cursor_line:
                    if cursor_col <= len(line_text):
                        line_text = (
                            line_text[:cursor_col]
                            + renderCursor
                            + line_text[cursor_col:]
                        )
                    else:
                        line_text = line_text + renderCursor

                # Truncate and pad line to fit width
                toRender = rcaplen(expand_len(line_text, innerWidth), innerWidth)

                # Add icon to first line if it exists
                if icon is not None and line_idx == 0:
                    icon_char = ast.literal_eval(f"'{icon}'")
                    toRender = f" {icon_char} {toRender}"

                startPos = x + alignOffset + 1
                renderY = y + 1 + line_idx
                if renderY < len(res.rows) and renderY >= 0:
                    res.rows[renderY] = (
                        res.rows[renderY][0:startPos]
                        + toRender
                        + res.rows[renderY][startPos + len(toRender) :]
                    )

        else:
            # Single line input (original logic)
            # Apply mask if specified
            if mask and val:
                # Replace each character with the mask character, but preserve cursor position
                masked_val = mask * len(val)
                draw_cursor_end = (
                    masked_val[idx + 1 :] if idx < len(masked_val) and idx != -1 else ""
                )
                draw_cursor = masked_val[:idx] + renderCursor + draw_cursor_end
            else:
                # No mask, use original value
                draw_cursor_end = val[idx + 1 :] if idx < len(val) and idx != -1 else ""
                draw_cursor = val[:idx] + renderCursor + draw_cursor_end

            innerWidth = calcWidth - 2  # account for border
            if icon is not None:
                innerWidth -= 3  # account for icon

            toRender = rcaplen(
                expand_len(
                    (
                        draw_cursor
                        if idx != -1
                        else (mask * len(val) if mask and val else val)
                    ),
                    innerWidth,
                ),
                innerWidth,
            )

            # add icon if it exists
            if icon is not None:
                icon = ast.literal_eval(f"'{icon}'")
                toRender = f" {icon} {toRender}"

            toRenderLength = len(toRender)

            alignOffset = getAlignOffset(element, toRender, parentSize)

            borderType = "thin"
            renderBorder(borderType, Vec(x, y), Vec(toRenderLength, 1), res)
            writeSize = Vec(toRenderLength + 2, 3)
            startPos = x + alignOffset + 1
            renderY = y + 1
            if renderY < len(res.rows) and renderY >= 0:
                res.rows[renderY] = (
                    res.rows[renderY][0:startPos]
                    + toRender
                    + res.rows[renderY][startPos + toRenderLength :]
                )

    elif element.type == "br":
        writeSize = Vec(1, 1)

    elif element.type == "table":
        # tables are just like containers, but they manage the rows and cells
        # notes:
        # - tables dont have padding
        # - tables have a default border type of "dotted thick"

        borderType = element.getAttribute("border")
        borderType = "dotted thick" if borderType is None else borderType

        writeSize = getElementSize(element, parentSize)

        if background_index is not None:
            renderBackground(background_index, Vec(x, y), writeSize, res)
        if foreground_index is not None:
            renderForeground(foreground_index, Vec(x, y), writeSize, res)

        tableRows = [x for x in element.children if x.type == "row"]

        # get column widths by getting max width of cells in each column
        rowWithMostCells = max(
            tableRows, key=lambda x: len([x for x in x.children if x.type == "cell"])
        )
        columnWidths = [1] * len(
            [x for x in rowWithMostCells.children if x.type == "cell"]
        )
        rowHeights = [1] * len(tableRows)

        for i, row in enumerate(tableRows):
            rowCells = [x for x in row.children if x.type == "cell"]
            for j, cell in enumerate(rowCells):
                cellSize = getElementSize(cell, parentSize)
                columnWidths[j] = max(columnWidths[j], cellSize.x)
                rowHeights[i] = max(rowHeights[i], cellSize.y)

        offset = Vec(1, 1)
        for i, row in enumerate(tableRows):
            rowCells = [x for x in row.children if x.type == "cell"]
            for j, cell in enumerate(rowCells):
                cellSize = getElementSize(cell, writeSize)
                renderElement(
                    cell,
                    x + offset.x,
                    y + offset.y,
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT,
                    res,
                    styles,
                    cellSize,
                )
                offset.x += columnWidths[j]
            offset.x = 1
            offset.y += rowHeights[i] + 1

        if borderType is not None:
            renderTableBorder(borderType, Vec(x, y), columnWidths, rowHeights, res)

    elif element.type == "cell":
        # a cell is just like a container, except the default width is to fit the content
        # and the default height is to fit the content
        writeSize = getElementSize(element, parentSize)

        padding = getPadding(element, parentSize.x, parentSize.y)
        paddingSize = Vec(
            padding["left"] + padding["right"], padding["top"] + padding["bottom"]
        )
        innerSize = parentSize - paddingSize

        if background_index is not None:
            renderBackground(background_index, Vec(x, y), writeSize, res)
        if foreground_index is not None:
            renderForeground(foreground_index, Vec(x, y), writeSize, res)

        direction = getDirection(element)
        offset = Vec(padding["left"], padding["top"])
        for child in element.children:
            singleSize = renderElement(
                child,
                x + offset.x,
                y + offset.y,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                res,
                styles,
                innerSize,
            )
            if direction == "row":
                offset.x += singleSize.x
            elif direction == "column":
                offset.y += singleSize.y

    return writeSize
