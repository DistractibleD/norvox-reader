"""Screen-region capture + OCR, for reading text that can't be selected or
copied (e.g. book viewers that render pages as images or block copying).

Note: region selection covers the primary monitor only.
"""

import tkinter as tk


class RegionSelector:
    """Full-screen click-and-drag overlay that reports the chosen rectangle."""

    def __init__(self, root, on_selected, on_cancel=None):
        self.on_selected = on_selected
        self.on_cancel = on_cancel
        self.start = None
        self.rect_id = None

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.geometry(f"{sw}x{sh}+0+0")
        self.top.attributes("-alpha", 0.3)
        self.top.attributes("-topmost", True)
        self.top.configure(bg="gray12")
        self.top.config(cursor="cross")

        self.canvas = tk.Canvas(self.top, bg="gray12", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.top.bind("<Escape>", self._on_escape)

        self.top.focus_force()
        self.top.grab_set()

    def _on_press(self, event):
        self.start = (event.x, event.y)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#ff4040", width=2
        )

    def _on_drag(self, event):
        if self.rect_id is None:
            return
        x0, y0 = self.start
        self.canvas.coords(self.rect_id, x0, y0, event.x, event.y)

    def _on_release(self, event):
        start = self.start
        self._close()
        if start is None:
            if self.on_cancel:
                self.on_cancel()
            return
        x0, y0 = start
        x1, y1 = event.x, event.y
        bbox = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        if bbox[2] - bbox[0] > 3 and bbox[3] - bbox[1] > 3:
            self.on_selected(bbox)
        elif self.on_cancel:
            self.on_cancel()

    def _on_escape(self, _event=None):
        self._close()
        if self.on_cancel:
            self.on_cancel()

    def _close(self):
        try:
            self.top.grab_release()
            self.top.destroy()
        except tk.TclError:
            pass


def capture_and_ocr(
    bbox, tesseract_path: str = "", tessdata_dir: str = "", langs: str = "eng+nor"
) -> str:
    """Grabs the given screen rectangle and runs OCR on it. Raises on failure."""
    import os

    from PIL import ImageGrab
    import pytesseract

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # Set TESSDATA_PREFIX rather than a "--tessdata-dir <path>" config
    # string: pytesseract splits its config string on whitespace, which
    # breaks a path containing spaces (e.g. under "Program Files"). The
    # subprocess tesseract runs in inherits this process's environment.
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = tessdata_dir

    image = ImageGrab.grab(bbox=bbox)
    text = pytesseract.image_to_string(image, lang=langs)
    return text.strip()
