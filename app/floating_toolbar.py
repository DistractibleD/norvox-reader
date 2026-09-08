"""A small, borderless, always-on-top control bar with icon buttons (read
selection / read page / pause / resume / stop / open settings), so those
stay reachable while the main window is hidden — e.g. while reading a web
page, where the main window would otherwise cover the text. This is the
app's primary UI: the main window starts hidden and this is what's shown
instead."""

import tkinter as tk

from app.tooltip import Tooltip

_BG = "#2D6CDF"
_FG = "#ffffff"
_BTN_BG = "#3D79E8"
_BTN_ACTIVE = "#255BC4"
_ICON_FONT = ("Segoe UI Symbol", 13)


class FloatingToolbar:
    def __init__(
        self,
        root,
        on_read_selection,
        on_read_page,
        on_pause_resume,
        on_stop,
        on_settings,
        on_minimize,
        on_close,
        rate_var,
        on_rate_changed,
    ):
        self._on_read_selection = on_read_selection
        self._on_read_page = on_read_page
        self._on_pause_resume = on_pause_resume
        self._on_stop = on_stop
        self._on_settings = on_settings
        self._on_minimize = on_minimize
        self._on_close = on_close
        self._on_rate_changed = on_rate_changed
        self._drag_start = None
        self._is_paused = False

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(bg=_BG)
        self.top.withdraw()

        outer = tk.Frame(self.top, bg=_BG, padx=4, pady=4)
        outer.pack()

        self.grip = tk.Label(outer, text="⣿", bg=_BG, fg=_FG, cursor="fleur", padx=4, font=_ICON_FONT)
        self.grip.pack(side="left")
        self.grip.bind("<ButtonPress-1>", self._start_drag)
        self.grip.bind("<B1-Motion>", self._on_drag)

        self.btn_read = self._make_button(outer, "▶", self._on_read_selection)
        self.btn_page = self._make_button(outer, "¶", self._on_read_page)
        self.btn_pause = self._make_button(outer, "⏸", self._on_pause_resume)
        self.btn_stop = self._make_button(outer, "⏹", self._on_stop)
        self.btn_settings = self._make_button(outer, "⚙", self._on_settings)

        self.btn_minimize = tk.Label(outer, text="−", bg=_BG, fg=_FG, cursor="hand2", padx=6, font=_ICON_FONT)
        self.btn_minimize.pack(side="left")
        self.btn_minimize.bind("<Button-1>", lambda _e: self._on_minimize())

        self.btn_close = tk.Label(outer, text="✕", bg=_BG, fg=_FG, cursor="hand2", padx=6, font=_ICON_FONT)
        self.btn_close.pack(side="left")
        self.btn_close.bind("<Button-1>", lambda _e: self._on_close())

        self.tip_read = Tooltip(self.btn_read)
        self.tip_page = Tooltip(self.btn_page)
        self.tip_pause = Tooltip(self.btn_pause)
        self.tip_stop = Tooltip(self.btn_stop)
        self.tip_settings = Tooltip(self.btn_settings)
        self.tip_minimize = Tooltip(self.btn_minimize)
        self.tip_close = Tooltip(self.btn_close)

        speed_row = tk.Frame(self.top, bg=_BG, padx=4)
        speed_row.pack(fill="x", pady=(0, 4))

        self.speed_icon = tk.Label(speed_row, text="⏩", bg=_BG, fg=_FG, font=("Segoe UI Symbol", 10))
        self.speed_icon.pack(side="left", padx=(0, 4))

        self.rate_scale = tk.Scale(
            speed_row,
            from_=1,
            to=10,
            orient="horizontal",
            variable=rate_var,
            command=self._on_rate_changed,
            bg=_BG,
            fg=_FG,
            troughcolor=_BTN_BG,
            activebackground=_FG,
            highlightthickness=0,
            bd=0,
            showvalue=0,
            sliderlength=14,
            width=8,
        )
        self.rate_scale.pack(side="left", fill="x", expand=True)

        self.rate_display = tk.Label(speed_row, textvariable=rate_var, bg=_BG, fg=_FG, font=("Segoe UI", 8), width=2)
        self.rate_display.pack(side="left", padx=(4, 0))

        self.tip_speed = Tooltip(self.speed_icon)

    def _make_button(self, parent, icon, command):
        btn = tk.Button(
            parent,
            text=icon,
            command=command,
            font=_ICON_FONT,
            bg=_BTN_BG,
            fg=_FG,
            activebackground=_BTN_ACTIVE,
            activeforeground=_FG,
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
        )
        btn.pack(side="left", padx=2)
        return btn

    def _start_drag(self, event):
        self._drag_start = (event.x_root - self.top.winfo_x(), event.y_root - self.top.winfo_y())

    def _on_drag(self, event):
        if self._drag_start is None:
            return
        x = event.x_root - self._drag_start[0]
        y = event.y_root - self._drag_start[1]
        self.top.geometry(f"+{x}+{y}")

    def show(self):
        self.top.deiconify()
        self.top.attributes("-topmost", True)

    def hide(self):
        self.top.withdraw()

    def is_visible(self) -> bool:
        return self.top.winfo_viewable() != 0

    def set_position(self, x: int, y: int):
        self.top.geometry(f"+{x}+{y}")

    def set_paused(self, is_paused: bool):
        self._is_paused = is_paused
        self.btn_pause.config(text="▶" if is_paused else "⏸")

    def set_tooltips(
        self,
        read: str,
        page: str,
        pause: str,
        resume: str,
        stop: str,
        settings: str,
        minimize: str,
        close: str,
        speed: str,
    ):
        self.tip_read.set_text(read)
        self.tip_page.set_text(page)
        self.tip_pause.set_text(resume if self._is_paused else pause)
        self.tip_stop.set_text(stop)
        self.tip_settings.set_text(settings)
        self.tip_minimize.set_text(minimize)
        self.tip_close.set_text(close)
        self.tip_speed.set_text(speed)

    def destroy(self):
        self.top.destroy()
