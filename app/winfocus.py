"""Tracks the last non-Norvox-Reader window that had focus, and can restore
focus to it. Needed because clicking one of our own buttons (main window or
the floating toolbar) shifts Windows focus to us — but "read selection" /
"read this page" work by simulating Ctrl+A / Ctrl+C, which only affects
whichever window currently has focus. Without restoring focus first, a
button click would copy nothing from the window the user actually meant."""

import ctypes

_GA_ROOT = 2

_user32 = ctypes.windll.user32
_user32.GetForegroundWindow.restype = ctypes.c_void_p
_user32.GetForegroundWindow.argtypes = []
_user32.SetForegroundWindow.restype = ctypes.c_int
_user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
_user32.GetAncestor.restype = ctypes.c_void_p
_user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]


def get_foreground_window():
    try:
        return _user32.GetForegroundWindow()
    except Exception:
        return None


def set_foreground_window(hwnd) -> bool:
    if not hwnd:
        return False
    try:
        return bool(_user32.SetForegroundWindow(hwnd))
    except Exception:
        return False


def get_root_hwnd(hwnd):
    """Resolves any window handle up to its real top-level window. Needed
    because Tkinter's widget.winfo_id() returns an internal child HWND, not
    the actual top-level window Windows tracks for focus/activation."""
    if not hwnd:
        return hwnd
    try:
        root = _user32.GetAncestor(hwnd, _GA_ROOT)
        return root or hwnd
    except Exception:
        return hwnd
