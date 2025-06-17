"""
Input handling module for the terminal browser.
"""

import curses
import threading
from typing import Optional

from .browser import Browser
from .window import Window
from .config import VALID_INPUT_CHARS
from .util import remove_spacing
import pyperclip

class InputHandler:
    def __init__(self, window: Window, browser: Browser):
        self.window = window
        self.browser = browser
        self.user_input: Optional[int] = None
        self.input_thread: Optional[threading.Thread] = None

    def start_input_thread(self) -> None:
        """Start the input handling thread."""
        self.input_thread = threading.Thread(
            name="input_handler",
            target=self._input_thread_loop,
            args=()
        )
        self.input_thread.setDaemon(True)
        self.input_thread.start()

    def _input_thread_loop(self) -> None:
        """Main input handling loop."""
        while True:
            self.user_input = self.window.get_input()
            
            # Handle URL bar input first if focused
            if self.browser.document.focus == -2:
                self._handle_url_input(chr(self.user_input))
            # Then handle element input if focused
            elif self.browser.document.focus != -1:
                self._handle_element_input(chr(self.user_input))
            # Then handle special keys if nothing is focused
            elif self.browser.document.focus == -1:
                self._handle_special_keys()
                # Handle link navigation
                if self.browser.document.find_link(self.user_input) != -1:
                    self.window.exiting = self.browser.open_link(
                        self.browser.document.links[self.browser.document.find_link(self.user_input)].URL
                    )

            self.browser.scroll = max(0, min(self.browser.scroll, self.browser.document_size.y - self.window.HEIGHT))

    def _handle_special_keys(self) -> None:
        """Handle special key inputs."""
        if self.user_input == ord("`") and self.browser.document.focus == -1:
            self.window.exiting = True
            curses.nocbreak()
            curses.echo()
            self.window.screen.keypad(0)
            curses.endwin()
            exit(0)
        elif self.user_input == 203:  # Alt + K
            self.browser.debugMode = not self.browser.debugMode
        elif self.user_input == 9:  # tab
            self.browser.document.focus_next()
        elif self.user_input == 27:  # esc
            if self.browser.document.focus == -1:
                self.browser.focus_url_bar()
            else:
                self.browser.unfocus_url_bar()
        elif self.user_input == 259:  # up arrow
            self.browser.scroll = max(0, self.browser.scroll - 1)
        elif self.user_input == 258:  # down arrow
            self.browser.scroll = min(self.browser.document_size.y - self.window.HEIGHT, self.browser.scroll + 1)

    def _handle_url_input(self, char: str) -> None:
        """Handle input when URL bar is focused."""
        # Debug log
        self.browser.debug(f"URL input: {char} (ord: {ord(char)})")
        
        if char == chr(226):  # alt + v
            to_insert = remove_spacing(pyperclip.paste())
            self.browser.URL = self.browser.URL[:self.browser.cursor_index] + to_insert + self.browser.URL[self.browser.cursor_index:]
            self.browser.cursor_index += len(to_insert)
        elif char == chr(260):  # left arrow
            self.browser.cursor_index = max(0, self.browser.cursor_index - 1)
        elif char == chr(261):  # right arrow
            self.browser.cursor_index = min(len(self.browser.URL), self.browser.cursor_index + 1)
        elif char == chr(127):  # backspace
            if self.browser.URL and self.browser.cursor_index > 0:
                self.browser.URL = self.browser.URL[:self.browser.cursor_index - 1] + self.browser.URL[self.browser.cursor_index:]
                self.browser.cursor_index -= 1
        elif char == chr(10):  # enter
            self.browser.open_link(self.browser.URL)
            self.browser.unfocus_url_bar()
        elif char == chr(27):  # esc
            self.browser.unfocus_url_bar()
        elif char in VALID_INPUT_CHARS:
            self.browser.URL = self.browser.URL[:self.browser.cursor_index] + char + self.browser.URL[self.browser.cursor_index:]
            self.browser.cursor_index += 1

    def _handle_element_input(self, char: str) -> None:
        """Handle input when an element is focused."""
        focused_element = self.browser.document.get_focused_element()
        if not focused_element:
            return

        old_index = focused_element.focus_cursor_index
        
        if char == chr(260):  # left arrow
            focused_element.focus_cursor_index = max(0, old_index - 1)
        elif char == chr(261):  # right arrow
            focused_element.focus_cursor_index = min(len(focused_element.value), old_index + 1)
        elif char in VALID_INPUT_CHARS:
            focused_element.value = focused_element.value[:old_index] + char + focused_element.value[old_index:]
            focused_element.focus_cursor_index += 1
            self.browser.document.change(focused_element)
        elif char == chr(127):  # backspace
            if focused_element.value and old_index > 0:
                focused_element.value = focused_element.value[:old_index - 1] + focused_element.value[old_index:]
                focused_element.focus_cursor_index -= 1
        elif char == chr(10):  # enter
            self.browser.document.submit(focused_element)
        elif char == chr(27):  # esc
            self.browser.document.unfocus()
        elif char == chr(197):  # Alt + Q
            self.browser.document.unfocus() 