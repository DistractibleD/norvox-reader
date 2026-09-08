"""Reads text from whatever window currently has focus (a browser, a PDF
viewer, a word processor) via the clipboard: either whatever is already
selected, or — for "read this page" — everything, by simulating Select All
first. Restores whatever was on the clipboard beforehand either way.
"""

import time

_SENTINEL = " __TEXTREADER_EMPTY__ "


def _copy_via_clipboard(pre_copy_keys: str = None, copy_delay: float = 0.15) -> str:
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

    if pre_copy_keys:
        keyboard.send(pre_copy_keys)
        time.sleep(0.05)

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


def read_current_selection(copy_delay: float = 0.15) -> str:
    return _copy_via_clipboard(copy_delay=copy_delay)


def read_current_page(copy_delay: float = 0.15) -> str:
    """Selects everything in the focused window first (Ctrl+A), then reads
    it — for reading a whole web page/document without hand-selecting text."""
    return _copy_via_clipboard(pre_copy_keys="ctrl+a", copy_delay=copy_delay)
