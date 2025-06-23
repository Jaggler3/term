def isInt(string) -> bool:
    return string.lstrip("-").isdigit()


def restrict_len(string: str, cap: int) -> str:
    return string if len(string) <= cap else string[:cap]


# restrict string to cap length
def rcaplen(string: str, cap: int) -> str:
    return string if len(string) <= cap else string[len(string) - cap :]


# expand string to cap length
def expand_len(string: str, cap: int) -> str:
    return string if len(string) >= cap else string + (" " * (cap - len(string)))


# Show text centered around cursor position when text is longer than cap
def cursor_centered_text(text: str, cursor_pos: int, cap: int) -> str:
    if len(text) <= cap:
        return text

    # Ensure cursor position is valid
    cursor_pos = max(0, min(cursor_pos, len(text) - 1))

    # Calculate the start position to center the cursor
    # Leave some space on the left and right of the cursor
    cursor_margin = min(10, cap // 4)  # Leave some space around cursor

    # Start position should center the cursor
    start_pos = cursor_pos - cursor_margin

    # Adjust if we're near the beginning of the text
    if start_pos < 0:
        start_pos = 0

    # Adjust if we're near the end of the text
    if start_pos + cap > len(text):
        start_pos = max(0, len(text) - cap)

    # Final check: ensure cursor is within the visible range
    if cursor_pos < start_pos:
        start_pos = cursor_pos
    elif cursor_pos >= start_pos + cap:
        start_pos = max(0, cursor_pos - cap + 1)

    return text[start_pos : start_pos + cap]


# removes tabs and newlines
def remove_spacing(string: str) -> str:
    return string.replace("\t", "").replace("\n", "")
