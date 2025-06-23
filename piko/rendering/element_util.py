from ..adom import Element
from ..vector import Vec
from .text_util import getLinkText, getRenderedFont, getWrapAndSize
from .util import getDefinedSize, getDirection, getPadding, parseSize


def getAlignOffset(element: Element, val: str, parentSize: Vec) -> int:
    if element.type == "link":
        val = getLinkText(element)

    isBox = element.type == "input"

    align = element.getAttribute("align")
    defWidth = getDefinedSize(element, parentSize).x
    preserve_whitespace = (
        element.getAttribute("preserve") == "true" if element.type == "text" else False
    )

    finalWidth = defWidth if defWidth != -1 else parentSize.x
    if not isBox:
        wrapped = getWrapAndSize(
            val, defWidth if defWidth != -1 else parentSize.x, preserve_whitespace
        )
        finalWidth = wrapped["size"].x
    if align == "center":
        return round(float(parentSize.x) / 2.0) - round(float(finalWidth) / 2.0)
    if align == "right":
        wrapped = getWrapAndSize(
            val, defWidth if defWidth != -1 else parentSize.x, preserve_whitespace
        )
        finalWidth = wrapped["size"].x
        return parentSize.x - finalWidth
    return 0


def getElementSize(element: Element, parentSize: Vec) -> Vec:
    if element.type == "text":
        widthAttr = element.getAttribute("width")
        padding = getPadding(element, parentSize.x, parentSize.y)
        renderWidth = (
            parseSize(widthAttr, parentSize.x - padding["left"] - padding["right"])
            if widthAttr is not None
            else parentSize.x - padding["left"] - padding["right"]
        )
        preserve_whitespace = element.getAttribute("preserve") == "true"
        val = getRenderedFont(
            element.value, preserve_whitespace, element.getAttribute("font")
        )
        wrapped_text_size = getWrapAndSize(val, renderWidth, preserve_whitespace)
        res = wrapped_text_size["size"]
        res.x += padding["left"] + padding["right"]
        res.y += padding["top"] + padding["bottom"]
        return res
    elif element.type == "link":
        widthAttr = element.getAttribute("width")
        renderWidth = (
            parseSize(widthAttr, parentSize.x)
            if widthAttr is not None
            else parentSize.x
        )
        wrapped_text_size = getWrapAndSize(getLinkText(element), renderWidth)
        return wrapped_text_size["size"]
    elif element.type == "input":
        widthAttr = element.getAttribute("width")
        lines_attr = element.getAttribute("lines")
        lines = int(lines_attr) if lines_attr else 1
        renderWidth = (
            parseSize(widthAttr, parentSize.x)
            if widthAttr is not None
            else parentSize.x
        )

        if lines > 1:
            # Multi-line input: height is lines + 2 for borders
            return Vec(renderWidth, lines + 2)
        else:
            # Single line input: height is 3 (original behavior)
            return Vec(renderWidth, 3)
    elif element.type == "cont":
        childrenSize = Vec(0, 0)
        padding = getPadding(element, parentSize.x, parentSize.y)
        paddingSize = Vec(
            padding["left"] + padding["right"], padding["top"] + padding["bottom"]
        )
        innerSize = parentSize - paddingSize
        defSize = getDefinedSize(element, parentSize)
        hasDefWidth = defSize.x != -1
        hasDefHeight = defSize.y != -1
        borderType = element.getAttribute("border")

        for child in element.children:
            singleSize = getElementSize(child, innerSize)
            direction = getDirection(element)
            if direction == "row":
                childrenSize.x += singleSize.x
                childrenSize.y = max(childrenSize.y, singleSize.y)
            elif direction == "column":
                childrenSize.y += singleSize.y
                childrenSize.x = max(childrenSize.x, singleSize.x)

        res = Vec(
            defSize.x if hasDefWidth else childrenSize.x + paddingSize.x,
            defSize.y if hasDefHeight else childrenSize.y + paddingSize.y,
        )

        # enforce box-sizing
        if borderType is not None:
            res.add(-2 if hasDefWidth else 0, -2 if hasDefHeight else 0)

        return res
    elif element.type == "br":
        return Vec(1, 1)
    elif element.type == "table":
        childrenSize = Vec(0, 0)
        defSize = getDefinedSize(element, parentSize)
        hasDefWidth = defSize.x != -1
        hasDefHeight = defSize.y != -1

        tableRows = [x for x in element.children if x.type == "row"]

        # get column widths by getting max width of cells in each column
        rowWithMostCells = max(
            tableRows, key=lambda x: len([x for x in x.children if x.type == "cell"])
        )
        columnWidths = [1] * len(
            [x for x in rowWithMostCells.children if x.type == "cell"]
        )
        rowHeights = [1] * len(tableRows)

        for row in tableRows:
            rowCells = [x for x in row.children if x.type == "cell"]
            for i, cell in enumerate(rowCells):
                cellSize = getElementSize(cell, parentSize)
                columnWidths[i] = max(columnWidths[i], cellSize.x)
            rowHeights[i] = max(rowHeights[i], cellSize.y)

        childrenSize.x = (
            sum(columnWidths) + len(columnWidths) - 1
        )  # account for borders
        childrenSize.y = sum(rowHeights) + len(rowHeights) - 1  # account for borders

        res = Vec(
            defSize.x if hasDefWidth else childrenSize.x,
            defSize.y if hasDefHeight else childrenSize.y,
        )

        # enforce box-sizing
        res.add(-2 if hasDefWidth else 0, -2 if hasDefHeight else 0)

        return res
    elif element.type == "cell":
        childrenSize = Vec(0, 0)
        padding = getPadding(element, parentSize.x, parentSize.y)
        paddingSize = Vec(
            padding["left"] + padding["right"], padding["top"] + padding["bottom"]
        )
        innerSize = parentSize - paddingSize
        defSize = getDefinedSize(element, parentSize)
        hasDefWidth = defSize.x != -1
        hasDefHeight = defSize.y != -1

        for child in element.children:
            singleSize = getElementSize(child, innerSize)
            direction = getDirection(element)
            if direction == "row":
                childrenSize.x += singleSize.x
                childrenSize.y = max(childrenSize.y, singleSize.y)
            elif direction == "column":
                childrenSize.y += singleSize.y
                childrenSize.x = max(childrenSize.x, singleSize.x)

        res = Vec(
            defSize.x if hasDefWidth else childrenSize.x + paddingSize.x,
            defSize.y if hasDefHeight else childrenSize.y + paddingSize.y,
        )

        return res
    return None
