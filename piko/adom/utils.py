"""Utility functions for the ADOM module."""

from typing import List

from .constants import elementTypes
from .elements import Element


def get_all_elements(elementList: List[Element]):
    res = []
    for element in elementList:
        res.append(element)
        if len(element.children) > 0:
            res.extend(get_all_elements(element.children))
    return res


def getTop(queue) -> Element:
    return queue[-1] if len(queue) > 0 else None


def digestDeclaration(line: str) -> tuple:
    restype: str = None
    resvalue: str = ""
    for etype in elementTypes:
        if line.startswith(etype):
            restype = etype
            break

    if restype is None:
        return None
    else:
        colIndex = line.find(":")
        if colIndex != -1:
            resvalue = line[colIndex + 1 :]
        return (restype, resvalue)


def digestAttribute(line) -> dict:
    colIndex = line.find(":")
    if colIndex == -1:
        return None

    attribName: str = line[:colIndex]
    if len(attribName) == 0:
        return None
    else:
        attribValue: str = line[colIndex + 1 :]
        if len(attribValue) == 0:
            return None
        else:
            return {"name": attribName, "value": attribValue.strip()}
