"""System tray icon so TextReader can sit in the background: the window can
be closed while hotkeys keep working, and the tray menu gives quick access
to the same actions.
"""

import threading

from app.i18n import t


class TrayIcon:
    def __init__(self, on_show, on_read_selection, on_capture_screen, on_quit):
        self.lang = "en"
        self._on_show = on_show
        self._on_read_selection = on_read_selection
        self._on_capture_screen = on_capture_screen
        self._on_quit = on_quit
        self._icon = None
        self._thread = None
        self.available = True
        try:
            import pystray  # noqa: F401
        except Exception:
            self.available = False

    def set_language(self, lang: str):
        self.lang = lang

    def start(self):
        if not self.available:
            return
        import pystray

        image = self._make_image()
        menu = pystray.Menu(
            pystray.MenuItem(lambda item: t("tray_show", self.lang), self._show),
            pystray.MenuItem(lambda item: t("tray_read_selection", self.lang), self._read_selection),
            pystray.MenuItem(lambda item: t("tray_capture_screen", self.lang), self._capture_screen),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: t("tray_quit", self.lang), self._quit),
        )
        self._icon = pystray.Icon("TextReader", image, "TextReader", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass

    def _show(self, icon, item):
        self._on_show()

    def _read_selection(self, icon, item):
        self._on_read_selection()

    def _capture_screen(self, icon, item):
        self._on_capture_screen()

    def _quit(self, icon, item):
        self._on_quit()

    @staticmethod
    def _make_image(size: int = 64):
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((2, 2, size - 2, size - 2), fill=(30, 110, 200, 255))
        d.polygon(
            [
                (size * 0.30, size * 0.38),
                (size * 0.30, size * 0.62),
                (size * 0.45, size * 0.62),
                (size * 0.62, size * 0.78),
                (size * 0.62, size * 0.22),
                (size * 0.45, size * 0.38),
            ],
            fill=(255, 255, 255, 255),
        )
        d.arc(
            (size * 0.55, size * 0.28, size * 0.88, size * 0.72),
            start=300,
            end=60,
            fill=(255, 255, 255, 255),
            width=3,
        )
        return img
