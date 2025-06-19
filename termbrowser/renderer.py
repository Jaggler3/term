"""
Rendering module for the terminal browser.
"""

import curses
from typing import Tuple, List

from .browser import Browser
from .window import Window
from .rendering.render import renderDocument, renderDebugger
from .util import expand_len, restrict_len, remove_spacing, rcaplen
from .pieces import get_pieces
from .config import (
    URL_CURSOR,
    CHECK_MARK,
    LOADING_MARK,
    DEBUG_WINDOW_HEIGHT
)

class Renderer:
    def __init__(self, window: Window, browser: Browser):
        self.window = window
        self.browser = browser

    def render(self) -> None:
        """Main rendering function."""
        self.window.start_render(0, 0)
        self._render_url_bar()
        self._render_document()
        self._render_debugger()
        self.window.disable_cursor()

    def _render_url_bar(self) -> None:
        """Render the URL bar at the top of the screen."""
        render_url_length = self.window.WIDTH - 1
        draw_cursor_end = (
            self.browser.URL[self.browser.cursor_index + 1:]
            if self.browser.cursor_index < len(self.browser.URL) and self.browser.cursor_index != -1
            else ""
        )
        draw_cursor = (
            self.browser.URL[:self.browser.cursor_index] + URL_CURSOR + draw_cursor_end
            if self.browser.document.focus == -2
            else self.browser.URL
        )
        
        # Use rcaplen to show the rightmost portion when text is too long
        # This allows the cursor to scroll into view when it's beyond the visible area
        render_url = expand_len(
            rcaplen(draw_cursor, render_url_length),
            render_url_length
        )
        
        self.window.render(
            render_url,
            curses.A_UNDERLINE,
            [2] * len(render_url),
            [1] * len(render_url)
        )
        
        self.window.render(
            CHECK_MARK if not self.browser.loading else LOADING_MARK,
            curses.A_UNDERLINE,
            [1] * 2,
            [2] * 2
        )

    def _render_document(self) -> None:
        """Render the main document content."""
        output, styles, backgrounds, foregrounds, calculated_size = renderDocument(
            self.browser.document,
            self.window.WIDTH,
            self.window.HEIGHT,
            self.browser.scroll
        )
        self.browser.document_size = calculated_size

        backgrounds_flattened = [item for sublist in backgrounds for item in sublist]
        foregrounds_flattened = [item for sublist in foregrounds for item in sublist]
        
        output = restrict_len(
            remove_spacing(output),
            self.window.WIDTH * (self.window.HEIGHT - 1) - 1
        )

        render_pieces = get_pieces(styles, len(output))
        self.window.start_render(1, 0)
        
        for piece in render_pieces:
            start_pos, end_pos, col = piece
            partial_backgrounds = backgrounds_flattened[start_pos:end_pos]
            partial_foregrounds = foregrounds_flattened[start_pos:end_pos]
            self.window.render(
                output[start_pos:end_pos],
                col,
                partial_backgrounds,
                partial_foregrounds
            )

    def _render_debugger(self) -> None:
        """Render the debug window if debug mode is enabled."""
        if not self.browser.debugMode:
            return

        self.window.start_render(self.window.HEIGHT - DEBUG_WINDOW_HEIGHT, 0)
        debugged = renderDebugger(
            self.browser.debugHistory,
            self.window.WIDTH,
            DEBUG_WINDOW_HEIGHT
        )[:-1]
        
        self.window.render(
            debugged,
            curses.A_NORMAL,
            [2] * len(debugged),
            [1] * len(debugged)
        ) 