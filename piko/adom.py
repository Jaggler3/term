"""Compatibility layer for the refactored ADOM module.

This file provides backward compatibility by importing all classes and functions
from the new adom package structure.
"""

# Import everything from the new adom package to maintain backward compatibility
from .adom import *  # noqa: F403
