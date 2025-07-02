from textwrap import TextWrapper
from typing import Union

from art import text2art

from ..vector import Vec

# Text wrapper that preserves whitespace more strictly
text_wrapper_preserve = TextWrapper(
    replace_whitespace=False,
    break_long_words=True,
    expand_tabs=True,
    tabsize=4,
    drop_whitespace=False,
)

# Text wrapper for normal text
text_wrapper = TextWrapper(
    replace_whitespace=False,
    break_long_words=True,
    expand_tabs=True,
    tabsize=4,
)


def getWrapAndSize(text: str, maxWidth: int, preserve_whitespace: bool = False):
    if preserve_whitespace:
        # When preserving whitespace, don't do any automatic wrapping
        # Just split by existing line breaks and truncate lines that are too long
        lines = text.splitlines()
        truncated_lines = []
        actual_width = 0

        for line in lines:
            if len(line) > maxWidth:
                truncated_line = line[:maxWidth]
                truncated_lines.append(truncated_line)
                actual_width = max(actual_width, maxWidth)
            else:
                truncated_lines.append(line)
                actual_width = max(actual_width, len(line))

        result_text = "\n".join(truncated_lines)
        return {"text": result_text, "size": Vec(actual_width, len(truncated_lines))}
    else:
        # Use normal text wrapping

        wrapper = text_wrapper
        wrapper.width = maxWidth
        wrappedText = wrapper.fill(text)

        lines = wrappedText.splitlines()
        longest_line = max(len(line) for line in lines) if len(lines) > 0 else 0

        return {"text": wrappedText, "size": Vec(longest_line, len(lines))}


def getRenderedFont(value: Union[str, None], preserve_whitespace: bool, font: str) -> str:
    if not value:
        return ""
    if not preserve_whitespace:
        value = value.strip()
    if font:
        return text2art(value, font=font).rstrip()
    return value


def getLinkText(element):
    return "[" + element.getAttribute("key") + "] " + (element.value or "")
