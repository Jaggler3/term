from typing import Dict
from ..vector import Vec
from ..adom import Element

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

def getPadding(element: Element, width: int, height: int) -> Dict[str, int]:
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

def getDefinedSize(element: Element, parentSize: Vec) -> Vec:
    res = Vec(-1, -1)
    defWidth = element.getAttribute("width")
    if element.type == "cont":
        defWidth = defWidth if defWidth != None else "100pc"
    defHeight = element.getAttribute("height")
    if defWidth != None:
        res.x = parseSize(defWidth, parentSize.x)
    if defHeight != None:
        res.y = parseSize(defHeight, parentSize.y)
    return res

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False 