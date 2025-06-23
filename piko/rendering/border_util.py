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
        firstRow += res.rows[pos.y][0 : pos.x]

        # top left corner
        firstRow += borderCodes["top-left"]
        # top
        firstRow += borderCodes["top"] * size.x
        # top right corner
        firstRow += borderCodes["top-right"]

        firstRow += res.rows[pos.y][pos.x + 1 + size.x + 1 : screenSize.x]

        # establish first row
        res.rows[pos.y] = (
            firstRow if len(firstRow) <= screenSize.x else firstRow[: screenSize.x]
        )

    # middle rows
    for y in range(size.y):
        borderContentY = pos.y + 1 + y
        if borderContentY < len(res.rows) and borderContentY >= 0:
            newRow = res.rows[borderContentY][0 : pos.x]
            newRow += borderCodes["left"]
            newRow += res.rows[borderContentY][pos.x + 1 : pos.x + 1 + size.x]
            newRow += borderCodes["right"]
            newRow += res.rows[borderContentY][pos.x + 1 + size.x + 1 : screenSize.x]
            res.rows[borderContentY] = (
                newRow if len(newRow) <= screenSize.x else newRow[: screenSize.x]
            )

    # last row
    lastBorderContentY = pos.y + size.y + 1
    if lastBorderContentY < len(res.rows) and lastBorderContentY >= 0:
        lastRow = ""
        # margin
        lastRow += res.rows[lastBorderContentY][0 : pos.x]

        # bottom left corner
        lastRow += borderCodes["bottom-left"]
        # bottom
        lastRow += borderCodes["bottom"] * size.x
        # bottom right corner
        lastRow += borderCodes["bottom-right"]

        lastRow += res.rows[lastBorderContentY][pos.x + 1 + size.x + 1 : screenSize.x]

        # establish last row
        res.rows[lastBorderContentY] = (
            lastRow if len(lastRow) <= screenSize.x else lastRow[: screenSize.x]
        )


def renderTableBorder(
    type: str, pos: Vec, col_widths: list[int], row_heights: list[int], res
):
    screenSize = Vec(len(res.rows[0]), len(res.rows))
    borderCodes = getBorderCodes(type)

    current_y = pos.y
    total_width = (
        sum(col_widths) + len(col_widths) + 1
    )  # column widths + separators + outer borders

    # Render top border
    if current_y >= 0:
        top_row = res.rows[current_y][0 : pos.x]
        top_row += borderCodes["top-left"]

        for i, width in enumerate(col_widths):
            top_row += borderCodes["top"] * width
            if i < len(col_widths) - 1:
                top_row += borderCodes["top-intersect"]

        top_row += borderCodes["top-right"]
        top_row += res.rows[current_y][pos.x + total_width : screenSize.x]
        res.rows[current_y] = (
            top_row if len(top_row) <= screenSize.x else top_row[: screenSize.x]
        )
        current_y += 1

    # Render rows and their separators
    for row_idx, height in enumerate(row_heights):
        # Content rows
        for _ in range(height):
            if current_y >= len(res.rows) or current_y < 0:
                break

            content_row = res.rows[current_y][0 : pos.x]
            content_row += borderCodes["left"]

            current_x = pos.x + 1
            for i, width in enumerate(col_widths):
                content_row += res.rows[current_y][current_x : current_x + width]
                current_x += width
                if i < len(col_widths) - 1:
                    content_row += borderCodes["left"]

            content_row += borderCodes["right"]
            content_row += res.rows[current_y][pos.x + total_width : screenSize.x]
            res.rows[current_y] = (
                content_row
                if len(content_row) <= screenSize.x
                else content_row[: screenSize.x]
            )
            current_y += 1

        # Row separator (not after last row)
        if (
            row_idx < len(row_heights) - 1
            and current_y < len(res.rows)
            and current_y >= 0
        ):
            separator_row = res.rows[current_y][0 : pos.x]
            separator_row += borderCodes["left-intersect"]

            for i, width in enumerate(col_widths):
                separator_row += borderCodes["top"] * width
                if i < len(col_widths) - 1:
                    separator_row += borderCodes["middle-intersect"]

            separator_row += borderCodes["right-intersect"]
            separator_row += res.rows[current_y][pos.x + total_width : screenSize.x]
            res.rows[current_y] = (
                separator_row
                if len(separator_row) <= screenSize.x
                else separator_row[: screenSize.x]
            )
            current_y += 1

    # Render bottom border
    if current_y < len(res.rows) and current_y >= 0:
        bottom_row = res.rows[current_y][0 : pos.x]
        bottom_row += borderCodes["bottom-left"]

        for i, width in enumerate(col_widths):
            bottom_row += borderCodes["bottom"] * width
            if i < len(col_widths) - 1:
                bottom_row += borderCodes["bottom-intersect"]

        bottom_row += borderCodes["bottom-right"]
        bottom_row += res.rows[current_y][pos.x + total_width : screenSize.x]
        res.rows[current_y] = (
            bottom_row
            if len(bottom_row) <= screenSize.x
            else bottom_row[: screenSize.x]
        )
