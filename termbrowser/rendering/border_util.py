from ..vector import Vec
from .borders import getBorderCodes

def renderBorder(type: str, pos: Vec, size: Vec, res):
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