import curses


class Window:
    def __init__(self, screen):
        y, x = screen.getmaxyx()
        self.WIDTH = x
        self.HEIGHT = y
        curses.noecho()
        screen.keypad(True)
        screen.clear()
        self.screen = screen
        self.exiting = False

        # Create a buffer window for double buffering
        self.buffer = curses.newwin(y, x)
        self.buffer.keypad(True)

        # Track dirty regions
        self.dirty_regions = []
        self.last_frame = None

    def resize(self):
        """Handle terminal resize events."""
        # Get new dimensions
        y, x = self.screen.getmaxyx()

        # Clear both screens
        self.screen.clear()
        if self.buffer:
            self.buffer.clear()

        # Resize terminal
        curses.resizeterm(y, x)
        self.WIDTH = x
        self.HEIGHT = y

        # Recreate buffer with new dimensions
        self.buffer = curses.newwin(y, x)
        self.buffer.keypad(True)

        # Reset state
        self.dirty_regions = []
        self.last_frame = None

        # Mark entire screen as dirty
        self.mark_dirty_region(0, 0, y, x)

        # Immediate refresh to prevent flickering
        self.screen.refresh()
        self.buffer.refresh()

    def refresh(self):
        """Refresh the screen with dirty regions."""
        # Only copy dirty regions from buffer to screen
        if self.dirty_regions:
            for region in self.dirty_regions:
                y, x, h, w = region
                try:
                    self.buffer.copywin(
                        self.screen, y, x, y, x, y + h - 1, x + w - 1, False
                    )
                except Exception:
                    pass  # Skip if region is invalid
            self.dirty_regions = []
        self.screen.refresh()
        self.buffer.refresh()

    def mark_dirty_region(self, y: int, x: int, height: int, width: int):
        """Mark a region as needing refresh."""
        self.dirty_regions.append(
            (max(0, y), max(0, x), min(height, self.HEIGHT), min(width, self.WIDTH))
        )

    def get_resized(self) -> bool:
        return curses.is_term_resized(self.HEIGHT, self.WIDTH)

    def get_input(self) -> chr:
        res = self.screen.getch()
        return res

    def get_input_text(self) -> str:
        res = self.screen.getstr()
        return res

    def get_wide_char(self) -> str:
        res = self.screen.get_wch()
        return res

    def start_render(self, y: int, x: int):
        """Start rendering at the specified position."""
        try:
            self.buffer.move(y, x)
            self.mark_dirty_region(y, x, 1, self.WIDTH - x)
        except Exception:
            pass  # Skip if position is invalid

    def render(
        self, string: str, option, partial_backgrounds: list, partial_foregrounds: list
    ):
        """Render a string with attributes."""
        try:
            y, x = self.buffer.getyx()
            for i in range(len(string)):
                pair = self.get_color_combination(
                    partial_backgrounds[i], partial_foregrounds[i]
                )
                try:
                    self.buffer.addstr(string[i], curses.color_pair(pair) | option)
                except curses.error:
                    pass  # Skip if we're at the screen edge
            self.mark_dirty_region(y, x, 1, len(string))
        except Exception as e:
            print("Error rendering string:")
            print(e)
            print(f"String: {string}")

    def disable_cursor(self):
        curses.curs_set(False)

    def get_color_combination(self, background: int, foreground: int) -> int:
        return background * 10 + foreground
