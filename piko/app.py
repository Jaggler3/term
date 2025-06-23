"""
Main application module for the terminal browser.
"""

import argparse
import curses
import sys
import time
import traceback
from typing import Optional

from .browser import Browser
from .config import ESCAPE_DELAY_MS, FPS
from .input_handler import InputHandler
from .renderer import Renderer
from .window import Window


class TerminalBrowser:
    def __init__(self, initial_url: Optional[str] = None):
        self.window: Optional[Window] = None
        self.browser: Optional[Browser] = None
        self.input_handler: Optional[InputHandler] = None
        self.renderer: Optional[Renderer] = None
        self.initial_url = initial_url or "piko://welcome"
        self.force_render = False

    def setup(self, screen: curses.window) -> None:
        """Initialize the terminal browser."""
        self.window = Window(screen)
        self.browser = Browser(self.initial_url)
        self.input_handler = InputHandler(self.window, self.browser)
        self.renderer = Renderer(self.window, self.browser)

        self._initialize_colors()
        curses.set_escdelay(ESCAPE_DELAY_MS)
        self.input_handler.start_input_thread()
        self._main_loop()

    def _initialize_colors(self) -> None:
        """Initialize color pairs for curses."""
        from .config import COLORMAP

        for background in range(1, 9):
            for foreground in range(1, 9):
                key = background * 10 + foreground
                curses.init_pair(key, COLORMAP[foreground], COLORMAP[background])

    def _main_loop(self) -> None:
        """Main application loop."""
        while True:
            try:
                if self.window.get_resized():
                    self.window.resize()
                    self.force_render = True  # Force a re-render after resize
                    continue

                self._update()

                # Always render if force_render is True, otherwise normal render check
                if self.force_render:
                    self.renderer.render(force=True)
                    self.force_render = False
                else:
                    self.renderer.render()

                if self.browser.loading:
                    self.browser.start_load()

                self.window.refresh()
                time.sleep(1 / FPS)
            except KeyboardInterrupt:
                curses.endwin()
                sys.exit(0)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                self.browser.debug(str(e))

    def _update(self) -> None:
        """Update application state."""
        if self.window.exiting:
            sys.exit(0)


def parse_args() -> Optional[str]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="the URL you would like to visit")
    args = parser.parse_args()
    return args.url


def main() -> None:
    """Application entry point."""
    initial_url = parse_args()
    browser = TerminalBrowser(initial_url)
    curses.wrapper(browser.setup)


if __name__ == "__main__":
    main()
