"""Minimal hover tooltip for Tkinter widgets — used to label icon-only
buttons (the floating toolbar) without needing visible text."""

import tkinter as tk


class Tooltip:
    def __init__(self, widget, text: str = "", bg: str = "#333333", fg: str = "#ffffff"):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self._tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def set_text(self, text: str):
        self.text = text

    def _show(self, _event=None):
        if self._tip is not None or not self.text:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = tk.Toplevel(self.widget)
        self._tip.overrideredirect(True)
        self._tip.attributes("-topmost", True)
        tk.Label(
            self._tip, text=self.text, bg=self.bg, fg=self.fg, padx=6, pady=2, font=("Segoe UI", 9)
        ).pack()
        self._tip.geometry(f"+{x}+{y}")

    def _hide(self, _event=None):
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
