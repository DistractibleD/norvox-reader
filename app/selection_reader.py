"""Reads whatever text is currently selected/highlighted in another window
(a browser, a PDF viewer, a word processor) by simulating Ctrl+C and reading
the clipboard, then restoring whatever was on the clipboard beforehand.
"""

import time

_SENTINEL = " __TEXTREADER_EMPTY__ "


def read_current_selection(copy_delay: float = 0.15) -> str:
    import keyboard
    import pyperclip

    try:
        previous = pyperclip.paste()
    except Exception:
        previous = ""

    try:
        pyperclip.copy(_SENTINEL)
    except Exception:
        pass

    keyboard.send("ctrl+c")
    time.sleep(copy_delay)

    try:
        text = pyperclip.paste()
    except Exception:
        text = ""

    try:
        pyperclip.copy(previous)
    except Exception:
        pass

    if text == _SENTINEL:
        return ""
    return text
