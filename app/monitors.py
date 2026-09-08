"""Multi-monitor detection via ctypes (no extra dependency)."""

import ctypes
from ctypes import wintypes


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


_MONITORINFOF_PRIMARY = 0x1

_MonitorEnumProc = ctypes.WINFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(wintypes.RECT), ctypes.c_ssize_t
)


def get_monitors():
    """Returns a list of {"left","top","right","bottom","primary"} dicts,
    one per connected monitor, in physical pixel coordinates. Requires the
    process to already be DPI-aware (see main.py) for coordinates to be
    meaningful."""
    monitors = []

    def _callback(hmonitor, _hdc, lprc_monitor, _data):
        rect = lprc_monitor.contents
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info))
        monitors.append(
            {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "primary": bool(info.dwFlags & _MONITORINFOF_PRIMARY),
            }
        )
        return 1

    try:
        ctypes.windll.user32.EnumDisplayMonitors(0, 0, _MonitorEnumProc(_callback), 0)
    except Exception:
        return []
    return monitors


def get_target_monitor_rect():
    """Returns the monitor the app should open on: the first secondary
    monitor found, so the primary display stays free (e.g. for gaming) —
    or the primary monitor if there's only one connected."""
    monitors = get_monitors()
    if not monitors:
        return None
    for m in monitors:
        if not m["primary"]:
            return m
    for m in monitors:
        if m["primary"]:
            return m
    return monitors[0]
