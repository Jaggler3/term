"""
Configuration module for the terminal browser.
"""

import curses

# Application settings
FPS = 60
ESCAPE_DELAY_MS = 25
DEBUG_WINDOW_HEIGHT = 8

# UI Elements
URL_CURSOR = "\N{FULL BLOCK}"
CHECK_MARK = "\N{HEAVY CHECK MARK}"
LOADING_MARK = "\N{DOTTED CIRCLE}"

# Color mapping
COLORMAP = {
    1: curses.COLOR_WHITE,
    2: curses.COLOR_BLACK,
    3: curses.COLOR_BLUE,
    4: curses.COLOR_RED,
    5: curses.COLOR_GREEN,
    6: curses.COLOR_YELLOW,
    7: curses.COLOR_MAGENTA,
    8: curses.COLOR_CYAN,
}

# Input settings
VALID_INPUT_CHARS = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*()-=_+[]{}\\|'\";:.>,</?`~"

# Key mappings
KEY_EXIT = ord("`")
KEY_DEBUG = 203  # Alt + K
KEY_TAB = 9
KEY_ESC = 27
KEY_UP = 259
KEY_DOWN = 258
KEY_LEFT = 260
KEY_RIGHT = 261
KEY_BACKSPACE = 127
KEY_ENTER = 10
KEY_PASTE = 226  # Alt + V
KEY_UNFOCUS = 197  # Alt + Q
