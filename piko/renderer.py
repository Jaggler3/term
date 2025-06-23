"""
Rendering module for the terminal browser.
"""

import curses

from .browser import Browser
from .config import CHECK_MARK, DEBUG_WINDOW_HEIGHT, LOADING_MARK, URL_CURSOR
from .pieces import get_pieces
from .rendering.render import renderDebugger, renderDocument
from .util import (
    cursor_centered_text,
    expand_len,
    rcaplen,
    remove_spacing,
    restrict_len,
)
from .window import Window


class Renderer:
    def __init__(self, window: Window, browser: Browser):
        self.window = window
        self.browser = browser
        self.reset_state_cache()

    def reset_state_cache(self):
        """Reset all cached state values."""
        self.last_url = None
        self.last_loading = None
        self.last_scroll = None
        self.last_focus = None
        self.last_cursor_index = None
        self.last_document_hash = None
        self.last_input_values = {}
        self.last_input_cursors = {}

    def _should_render(self) -> bool:
        """Determine if we need to render based on state changes."""
        current_doc_hash = hash(str(self.browser.document.elements))

        # Track input element values and cursor positions
        current_input_values = {}
        current_input_cursors = {}
        for element in self.browser.document.get_focus_list():
            element_id = id(element)  # Use object id as unique identifier
            current_input_values[element_id] = element.value
            current_input_cursors[element_id] = element.focus_cursor_index

        needs_render = (
            self.last_url != self.browser.URL
            or self.last_loading != self.browser.loading
            or self.last_scroll != self.browser.scroll
            or self.last_focus != self.browser.document.focus
            or self.last_cursor_index != self.browser.cursor_index
            or self.last_document_hash != current_doc_hash
            or self.last_input_values != current_input_values
            or self.last_input_cursors != current_input_cursors
        )

        # Update cached state
        self.last_url = self.browser.URL
        self.last_loading = self.browser.loading
        self.last_scroll = self.browser.scroll
        self.last_focus = self.browser.document.focus
        self.last_cursor_index = self.browser.cursor_index
        self.last_document_hash = current_doc_hash
        self.last_input_values = current_input_values
        self.last_input_cursors = current_input_cursors

        return needs_render

    def render(self, force: bool = False) -> None:
        """Main rendering function with optimizations."""
        if not force and not self._should_render():
            return

        self.window.start_render(0, 0)
        self._render_url_bar()
        self._render_document()
        self._render_debugger()
        self.window.disable_cursor()

    def _render_url_bar(self) -> None:
        """Render the URL bar at the top of the screen."""
        render_url_length = self.window.WIDTH - 1

        # Pre-calculate cursor position and text
        draw_cursor_end = (
            self.browser.URL[self.browser.cursor_index + 1 :]
            if self.browser.cursor_index < len(self.browser.URL)
            and self.browser.cursor_index != -1
            else ""
        )
        draw_cursor = (
            self.browser.URL[: self.browser.cursor_index] + URL_CURSOR + draw_cursor_end
            if self.browser.document.focus == -2
            else self.browser.URL
        )

        # Choose display method based on whether we're editing
        if self.browser.document.focus == -2 and self.browser.cursor_index >= 0:
            # When editing, center around cursor position
            # Account for the URL_CURSOR character in the cursor position
            cursor_pos_with_marker = self.browser.cursor_index + len(URL_CURSOR)
            render_url = expand_len(
                cursor_centered_text(
                    draw_cursor, cursor_pos_with_marker, render_url_length
                ),
                render_url_length,
            )
        else:
            # When not editing, show rightmost portion
            render_url = expand_len(
                rcaplen(draw_cursor, render_url_length), render_url_length
            )

        # Render URL with styles
        url_focused = self.browser.document.focus == -2
        url_style = curses.A_BOLD if url_focused else curses.A_UNDERLINE
        self.window.render(
            render_url,
            url_style,
            [1 if url_focused else 2] * len(render_url),
            [2 if url_focused else 1] * len(render_url),
        )

        # Render status indicator
        self.window.render(
            CHECK_MARK if not self.browser.loading else LOADING_MARK,
            curses.A_UNDERLINE,
            [1] * 2,
            [2] * 2,
        )

    def _render_document(self) -> None:
        """Render the main document content with optimizations."""
        output, styles, backgrounds, foregrounds, calculated_size = renderDocument(
            self.browser.document,
            self.window.WIDTH,
            self.window.HEIGHT,
            self.browser.scroll,
        )
        self.browser.document_size = calculated_size

        # Flatten color arrays once
        backgrounds_flattened = [item for sublist in backgrounds for item in sublist]
        foregrounds_flattened = [item for sublist in foregrounds for item in sublist]

        # Process output string once
        output = restrict_len(
            remove_spacing(output), self.window.WIDTH * (self.window.HEIGHT - 1) - 1
        )

        # Get render pieces and batch render them
        render_pieces = get_pieces(styles, len(output))
        self.window.start_render(1, 0)

        for piece in render_pieces:
            start_pos, end_pos, col = piece
            partial_backgrounds = backgrounds_flattened[start_pos:end_pos]
            partial_foregrounds = foregrounds_flattened[start_pos:end_pos]
            self.window.render(
                output[start_pos:end_pos], col, partial_backgrounds, partial_foregrounds
            )

    def _render_debugger(self) -> None:
        """Render the debug window if debug mode is enabled."""
        if not self.browser.debugMode:
            return

        self.window.start_render(self.window.HEIGHT - DEBUG_WINDOW_HEIGHT, 0)
        debugged = renderDebugger(
            self.browser.debugHistory, self.window.WIDTH, DEBUG_WINDOW_HEIGHT
        )[:-1]

        self.window.render(
            debugged, curses.A_NORMAL, [2] * len(debugged), [1] * len(debugged)
        )
