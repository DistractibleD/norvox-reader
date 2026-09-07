"""TextReader entry point.

A standalone accessibility tool that reads text aloud in English and
Norwegian: paste text, capture a screen region (OCR) when text can't be
selected, or press a global hotkey to read whatever is currently selected
in another window (browser, PDF, document).

Copyright (C) 2026 Distracted

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 2 of the License, or (at your
option) any later version. See the LICENSE file for the full text, and
THIRD_PARTY_LICENSES.md for the licenses of bundled third-party
components (this program bundles Tesseract OCR, which is why the whole
package is GPL-2.0-or-later rather than a more permissive license).
"""

import os
import sys


def _set_dpi_awareness():
    """Makes screen-region capture line up with real pixels on HiDPI displays."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    _set_dpi_awareness()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from app.gui import App

    app = App()
    app.run()


if __name__ == "__main__":
    main()
    os._exit(0)
