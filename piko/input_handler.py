"""
Input handling module for the terminal browser.
"""

import curses
import threading
from typing import Optional

import pyperclip

from .browser import Browser
from .config import VALID_INPUT_CHARS
from .util import remove_spacing
from .window import Window


class InputHandler:
    def __init__(self, window: Window, browser: Browser):
        self.window = window
        self.browser = browser
        self.user_input: Optional[int] = None
        self.input_thread: Optional[threading.Thread] = None

    def start_input_thread(self) -> None:
        """Start the input handling thread."""
        self.input_thread = threading.Thread(
            name="input_handler", target=self._input_thread_loop, args=()
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
                found_index = self.browser.document.find_link(self.user_input)
                if found_index != -1:
                    found_link = self.browser.document.links[found_index]
                    url = found_link.getAttribute("url")
                    submit = found_link.getAttribute("submit")
                    if url:
                        self.window.exiting = self.browser.open_link(url)
                    elif submit:
                        self.browser.document.call_action(submit, {})

            self.browser.scroll = max(
                0,
                min(
                    self.browser.scroll,
                    self.browser.document_size.y - self.window.HEIGHT,
                ),
            )

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
            self.browser.scroll = min(
                self.browser.document_size.y - self.window.HEIGHT,
                self.browser.scroll + 1,
            )

    def _handle_url_input(self, char: str) -> None:
        """Handle input when URL bar is focused."""

        if char == chr(226):  # alt + v
            to_insert = remove_spacing(pyperclip.paste())
            self.browser.URL = (
                self.browser.URL[: self.browser.cursor_index]
                + to_insert
                + self.browser.URL[self.browser.cursor_index :]
            )
            self.browser.cursor_index += len(to_insert)
        elif char == chr(260):  # left arrow
            self.browser.cursor_index = max(0, self.browser.cursor_index - 1)
        elif char == chr(261):  # right arrow
            self.browser.cursor_index = min(
                len(self.browser.URL), self.browser.cursor_index + 1
            )
        elif char == chr(127):  # backspace
            if self.browser.URL and self.browser.cursor_index > 0:
                self.browser.URL = (
                    self.browser.URL[: self.browser.cursor_index - 1]
                    + self.browser.URL[self.browser.cursor_index :]
                )
                self.browser.cursor_index -= 1
        elif char == chr(10):  # enter
            self.browser.open_link(self.browser.URL)
            self.browser.unfocus_url_bar()
        elif char == chr(27):  # esc
            self.browser.unfocus_url_bar()
        elif char in VALID_INPUT_CHARS:
            self.browser.URL = (
                self.browser.URL[: self.browser.cursor_index]
                + char
                + self.browser.URL[self.browser.cursor_index :]
            )
            self.browser.cursor_index += 1

    def _handle_element_input(self, char: str) -> None:
        """Handle input when an element is focused."""
        focused_element = self.browser.document.get_focused_element()
        if not focused_element:
            return

        old_index = focused_element.focus_cursor_index
        lines_attr = focused_element.getAttribute("lines")
        lines = int(lines_attr) if lines_attr else 1

        if char == chr(260):  # left arrow
            focused_element.focus_cursor_index = max(0, old_index - 1)
        elif char == chr(261):  # right arrow
            focused_element.focus_cursor_index = min(
                len(focused_element.value), old_index + 1
            )
        elif char == chr(258):  # down arrow
            if lines > 1:
                # Move cursor down one line for multiline inputs
                val_lines = (
                    focused_element.value.split("\n") if focused_element.value else [""]
                )
                current_pos = 0
                cursor_line = 0
                cursor_col = 0

                # Find current line and column
                for i, line in enumerate(val_lines):
                    if current_pos + len(line) >= old_index:
                        cursor_line = i
                        cursor_col = old_index - current_pos
                        break
                    current_pos += len(line) + 1  # +1 for newline
                else:
                    cursor_line = len(val_lines) - 1
                    cursor_col = len(val_lines[cursor_line])

                # Move to next line if possible
                if cursor_line < len(val_lines) - 1:
                    next_line = val_lines[cursor_line + 1]
                    new_col = min(cursor_col, len(next_line))
                    # Calculate new position
                    new_pos = 0
                    for i in range(cursor_line + 1):
                        new_pos += len(val_lines[i]) + 1
                    new_pos += new_col
                    focused_element.focus_cursor_index = new_pos
            else:
                # Scroll down for single-line inputs
                self.browser.scroll = min(
                    self.browser.document_size.y - self.window.HEIGHT,
                    self.browser.scroll + 1,
                )
        elif char == chr(259):  # up arrow
            if lines > 1:
                # Move cursor up one line for multiline inputs
                val_lines = (
                    focused_element.value.split("\n") if focused_element.value else [""]
                )
                current_pos = 0
                cursor_line = 0
                cursor_col = 0

                # Find current line and column
                for i, line in enumerate(val_lines):
                    if current_pos + len(line) >= old_index:
                        cursor_line = i
                        cursor_col = old_index - current_pos
                        break
                    current_pos += len(line) + 1  # +1 for newline
                else:
                    cursor_line = len(val_lines) - 1
                    cursor_col = len(val_lines[cursor_line])

                # Move to previous line if possible
                if cursor_line > 0:
                    prev_line = val_lines[cursor_line - 1]
                    new_col = min(cursor_col, len(prev_line))
                    # Calculate new position
                    new_pos = 0
                    for i in range(cursor_line - 1):
                        new_pos += len(val_lines[i]) + 1
                    new_pos += new_col
                    focused_element.focus_cursor_index = new_pos
            else:
                # Scroll up for single-line inputs
                self.browser.scroll = max(0, self.browser.scroll - 1)
        elif char == chr(10):  # Enter key
            if lines > 1:
                # Insert newline at cursor position for multi-line inputs
                focused_element.value = (
                    focused_element.value[:old_index]
                    + "\n"
                    + focused_element.value[old_index:]
                )
                focused_element.focus_cursor_index += 1
                self.browser.document.change(focused_element)
            else:
                # Submit for single line inputs
                self.browser.document.submit(focused_element)
        elif char in VALID_INPUT_CHARS:
            # Regular character input
            focused_element.value = (
                focused_element.value[:old_index]
                + char
                + focused_element.value[old_index:]
            )
            focused_element.focus_cursor_index += 1
            self.browser.document.change(focused_element)
        elif char == chr(127):  # backspace
            if focused_element.value and old_index > 0:
                # Check if we're deleting a newline
                if old_index > 0 and focused_element.value[old_index - 1] == "\n":
                    # Merge lines when deleting newline
                    lines_before = focused_element.value[: old_index - 1].split("\n")
                    lines_after = focused_element.value[old_index:].split("\n")

                    if len(lines_before) > 1 and len(lines_after) > 0:
                        # Merge the last line before with the first line after
                        merged_line = lines_before[-1] + lines_after[0]
                        new_value = (
                            "\n".join(lines_before[:-1])
                            + "\n"
                            + merged_line
                            + "\n".join(lines_after[1:])
                        )
                        focused_element.value = new_value
                        focused_element.focus_cursor_index = old_index - 1
                    else:
                        # Simple newline deletion
                        focused_element.value = (
                            focused_element.value[: old_index - 1]
                            + focused_element.value[old_index:]
                        )
                        focused_element.focus_cursor_index -= 1
                else:
                    # Regular backspace
                    focused_element.value = (
                        focused_element.value[: old_index - 1]
                        + focused_element.value[old_index:]
                    )
                    focused_element.focus_cursor_index -= 1
        elif char == chr(27):  # esc
            self.browser.document.unfocus()
        elif char == chr(197):  # Alt + Q
            self.browser.document.unfocus()
        elif char == chr(9):  # tab to go to next focus
            self.browser.document.focus_next()
