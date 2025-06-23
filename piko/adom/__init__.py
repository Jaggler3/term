"""ADOM (Abstract Document Object Model) module.

This module provides classes and functions for working with piko documents.
"""

# Import main classes and functions that should be available when importing adom
from .elements import Action, Attribute, Element, createTextElement
from .document import Document
from .parsers import xml2doc
from .constants import URL_BAR_INDEX, elementTypes, validFormats
from .utils import get_all_elements, getTop, digestDeclaration, digestAttribute

# Define what gets exported when using "from adom import *"
__all__ = [
    'Action',
    'Attribute', 
    'Element',
    'createTextElement',
    'Document',
    'xml2doc',
    'URL_BAR_INDEX',
    'elementTypes',
    'validFormats',
    'get_all_elements',
    'getTop',
    'digestDeclaration',
    'digestAttribute'
] 