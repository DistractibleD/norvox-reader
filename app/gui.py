"""Main Tkinter application window and all UI wiring."""

import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.config import DEFAULTS, load, save
from app.hotkeys import HotkeyManager
from app.i18n import t
from app.ocr_screen import RegionSelector, capture_and_ocr
from app.paths import bundled_tessdata_dir, bundled_tesseract_exe, has_bundled_tesseract
from app.selection_reader import read_current_selection
from app.tray import TrayIcon
from app.tts_engine import TTSEngine

_LANG_OVERRIDE_CODES = ["auto", "en", "no"]


def _guess_voice_lang(voice) -> str:
    hay = f"{voice.id} {voice.name}".lower()
    if any(s in hay for s in ("nb-no", "nn-no", "nb_no", "nn_no", "norwegian", "norsk")):
        return "no"
    if any(s in hay for s in ("en-us", "en-gb", "en_us", "en_gb", "english")):
        return "en"
    return "other"


class App:
    def __init__(self):
        self.cfg = load()
        self.lang = self.cfg["ui_language"]
        self._current_state = "idle"
        self._voice_by_display = {}

        self.tts = TTSEngine(rate=self.cfg["rate"], volume=self.cfg["volume"])
        self.tts.on_state_change = lambda state: self.root.after(0, self._apply_state, state)

        self.root = tk.Tk()
        self.root.title(t("app_title", self.lang))
        self.root.geometry("760x600")
        self.root.minsize(600, 480)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_button)

        self.hotkeys = HotkeyManager()
        self.tray = TrayIcon(
            on_show=lambda: self.root.after(0, self._show_window),
            on_read_selection=lambda: self.root.after(0, self._read_selection_flow),
            on_capture_screen=lambda: self.root.after(0, self._on_capture_clicked),
            on_quit=lambda: self.root.after(0, self._quit),
        )

        self._build_ui()
        self._push_voice_selection_to_engine()
        self._register_hotkeys()
        self.tray.set_language(self.lang)
        self.tray.start()

        self._apply_state("idle")

    def run(self):
        self.root.mainloop()

    # ---------------------------------------------------------------- UI --

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.read_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.read_tab, text="")
        self.notebook.add(self.settings_tab, text="")

        self._build_read_tab()
        self._build_settings_tab()

        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken").pack(
            fill="x", side="bottom"
        )

        self._apply_language()

    def _build_read_tab(self):
        frame = self.read_tab
        self.text_box = tk.Text(frame, wrap="word", height=16, font=("Segoe UI", 11))
        self.text_box.pack(fill="both", expand=True, padx=4, pady=(4, 8))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(0, 6))
        self.btn_read = ttk.Button(btn_row, command=self._on_read_clicked)
        self.btn_pause = ttk.Button(btn_row, command=self._on_pause_clicked)
        self.btn_stop = ttk.Button(btn_row, command=self._on_stop_clicked)
        self.btn_clear = ttk.Button(btn_row, command=self._on_clear_clicked)
        self.btn_paste = ttk.Button(btn_row, command=self._on_paste_clicked)
        for b in (self.btn_read, self.btn_pause, self.btn_stop, self.btn_clear, self.btn_paste):
            b.pack(side="left", padx=4)

        lang_row = ttk.Frame(frame)
        lang_row.pack(fill="x", pady=(0, 6))
        self.lang_override_label = ttk.Label(lang_row)
        self.lang_override_label.pack(side="left", padx=(4, 6))
        self.lang_override_combo = ttk.Combobox(lang_row, state="readonly", width=16)
        self.lang_override_combo.pack(side="left")

        action_row = ttk.Frame(frame)
        action_row.pack(fill="x", pady=(6, 0))
        self.btn_capture = ttk.Button(action_row, command=self._on_capture_clicked)
        self.btn_capture.pack(side="left", padx=4)
        self.btn_read_selection = ttk.Button(action_row, command=self._read_selection_flow)
        self.btn_read_selection.pack(side="left", padx=4)

        self.hotkey_hint_var = tk.StringVar()
        ttk.Label(
            frame, textvariable=self.hotkey_hint_var, foreground="#666", wraplength=700, justify="left"
        ).pack(fill="x", padx=4, pady=(10, 0))

    def _build_settings_tab(self):
        frame = self.settings_tab
        pad = {"padx": 6, "pady": 5}

        self.ui_lang_label = ttk.Label(frame)
        self.ui_lang_label.grid(row=0, column=0, sticky="w", **pad)
        self.ui_lang_combo = ttk.Combobox(frame, state="readonly", width=20, values=["English", "Norsk"])
        self.ui_lang_combo.grid(row=0, column=1, sticky="w", **pad)
        self.ui_lang_combo.current(0 if self.lang == "en" else 1)
        self.ui_lang_combo.bind("<<ComboboxSelected>>", self._on_ui_lang_changed)

        self.voices_label = ttk.Label(frame, font=("Segoe UI", 10, "bold"))
        self.voices_label.grid(row=1, column=0, sticky="w", pady=(14, 2), padx=6)
        self.refresh_voices_btn = ttk.Button(frame, command=self._on_refresh_voices_clicked)
        self.refresh_voices_btn.grid(row=1, column=1, sticky="w", pady=(14, 2))

        self.en_voice_label = ttk.Label(frame)
        self.en_voice_label.grid(row=2, column=0, sticky="w", **pad)
        self.en_voice_combo = ttk.Combobox(frame, state="readonly", width=45)
        self.en_voice_combo.grid(row=2, column=1, sticky="we", **pad)

        self.no_voice_label = ttk.Label(frame)
        self.no_voice_label.grid(row=3, column=0, sticky="w", **pad)
        self.no_voice_combo = ttk.Combobox(frame, state="readonly", width=45)
        self.no_voice_combo.grid(row=3, column=1, sticky="we", **pad)
        self.install_no_voice_btn = ttk.Button(frame, command=self._on_install_norwegian_voice_clicked)
        self.install_no_voice_btn.grid(row=3, column=2, sticky="w", padx=6)

        self.rate_label = ttk.Label(frame)
        self.rate_label.grid(row=4, column=0, sticky="w", **pad)
        self.rate_var = tk.IntVar(value=self.cfg["rate"])
        ttk.Scale(frame, from_=80, to=300, orient="horizontal", variable=self.rate_var).grid(
            row=4, column=1, sticky="we", **pad
        )
        ttk.Label(frame, textvariable=self.rate_var, width=5).grid(row=4, column=2, sticky="w")

        self.volume_label = ttk.Label(frame)
        self.volume_label.grid(row=5, column=0, sticky="w", **pad)
        self.volume_var = tk.IntVar(value=int(round(self.cfg["volume"] * 100)))
        ttk.Scale(frame, from_=0, to=100, orient="horizontal", variable=self.volume_var).grid(
            row=5, column=1, sticky="we", **pad
        )
        self.volume_display_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.volume_display_var, width=5).grid(row=5, column=2, sticky="w")
        self.volume_var.trace_add(
            "write", lambda *_: self.volume_display_var.set(f"{self.volume_var.get()}%")
        )
        self.volume_display_var.set(f"{self.volume_var.get()}%")

        self.hotkeys_label = ttk.Label(frame, font=("Segoe UI", 10, "bold"))
        self.hotkeys_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(14, 2), padx=6)

        self.hotkey_sel_label = ttk.Label(frame)
        self.hotkey_sel_label.grid(row=7, column=0, sticky="w", **pad)
        self.hotkey_sel_var = tk.StringVar(value=self.cfg["hotkey_read_selection"])
        ttk.Entry(frame, textvariable=self.hotkey_sel_var, width=20).grid(row=7, column=1, sticky="w", **pad)

        self.hotkey_cap_label = ttk.Label(frame)
        self.hotkey_cap_label.grid(row=8, column=0, sticky="w", **pad)
        self.hotkey_cap_var = tk.StringVar(value=self.cfg["hotkey_capture_screen"])
        ttk.Entry(frame, textvariable=self.hotkey_cap_var, width=20).grid(row=8, column=1, sticky="w", **pad)

        self.tess_label = ttk.Label(frame, font=("Segoe UI", 10, "bold"))
        self.tess_label.grid(row=9, column=0, columnspan=2, sticky="w", pady=(14, 2), padx=6)

        self.tess_path_label = ttk.Label(frame)
        self.tess_path_label.grid(row=10, column=0, sticky="w", **pad)
        self.tess_path_var = tk.StringVar(value=self.cfg["tesseract_path"])
        ttk.Entry(frame, textvariable=self.tess_path_var, width=45).grid(row=10, column=1, sticky="we", **pad)
        self.browse_btn = ttk.Button(frame, command=self._on_browse_tesseract)
        self.browse_btn.grid(row=10, column=2, sticky="w", padx=6)

        self.save_btn = ttk.Button(frame, command=self._on_save_settings)
        self.save_btn.grid(row=11, column=1, sticky="w", pady=(16, 4))

        frame.columnconfigure(1, weight=1)

        self._populate_voice_lists()

    # ------------------------------------------------------------ voices --

    def _populate_voice_lists(self):
        try:
            voices = self.tts.list_voices()
        except Exception:
            voices = []

        self._voice_by_display = {}
        entries = []
        seen_labels = set()
        for v in voices:
            label = v.name
            if label in seen_labels:
                label = f"{v.name} ({v.id})"
            seen_labels.add(label)
            self._voice_by_display[label] = v.id
            entries.append((label, _guess_voice_lang(v)))

        en_primary = [d for d, l in entries if l == "en"]
        en_other = [d for d, l in entries if l == "other"]
        en_list = en_primary + en_other or [d for d, _ in entries]

        no_primary = [d for d, l in entries if l == "no"]
        no_other = [d for d, l in entries if l == "other"]
        no_list = no_primary + no_other or [d for d, _ in entries]

        self.en_voice_combo["values"] = en_list
        self.no_voice_combo["values"] = no_list

        self._select_voice(self.en_voice_combo, self.cfg.get("voice_en"), en_primary or en_list)
        self._select_voice(self.no_voice_combo, self.cfg.get("voice_no"), no_primary or no_list)

    def _select_voice(self, combo, voice_id, fallback_list):
        if voice_id:
            for label, vid in self._voice_by_display.items():
                if vid == voice_id and label in combo["values"]:
                    combo.set(label)
                    return
        if fallback_list:
            combo.set(fallback_list[0])

    def _push_voice_selection_to_engine(self):
        en_id = self._voice_by_display.get(self.en_voice_combo.get())
        no_id = self._voice_by_display.get(self.no_voice_combo.get())
        if en_id:
            self.tts.set_voice_for_lang("en", en_id)
            self.cfg["voice_en"] = en_id
        if no_id:
            self.tts.set_voice_for_lang("no", no_id)
            self.cfg["voice_no"] = no_id
        if not no_id:
            self._set_status_text(t("no_voice_found", self.lang))

    def _on_refresh_voices_clicked(self):
        self._populate_voice_lists()
        self._push_voice_selection_to_engine()
        self._set_status_text(t("settings_saved", self.lang))

    def _on_install_norwegian_voice_clicked(self):
        if not messagebox.askyesno(
            t("install_no_voice_confirm_title", self.lang),
            t("install_no_voice_confirm", self.lang),
        ):
            return
        try:
            import ctypes

            params = (
                '-NoExit -NoProfile -Command "Add-WindowsCapability -Online -Name '
                "'Language.TextToSpeech~~~nb-NO~0.0.1.0'\""
            )
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "powershell.exe", params, None, 1
            )
            if int(result) <= 32:
                raise OSError(f"ShellExecuteW returned {result}")
            self._set_status_text(t("install_no_voice_started", self.lang))
        except Exception as exc:
            self._set_status_text(t("install_no_voice_failed", self.lang).format(error=str(exc)))

    # -------------------------------------------------------------- text --

    def _current_lang_override(self) -> str:
        idx = self.lang_override_combo.current()
        return _LANG_OVERRIDE_CODES[idx] if idx >= 0 else "auto"

    def _start_reading(self, text=None):
        if text is None:
            text = self.text_box.get("1.0", "end")
        if not text.strip():
            return
        self.tts.speak(text, lang_override=self._current_lang_override())

    def _on_read_clicked(self):
        self._start_reading()

    def _on_pause_clicked(self):
        if self._current_state == "paused":
            self.tts.resume()
        else:
            self.tts.pause()

    def _on_stop_clicked(self):
        self.tts.stop()

    def _on_clear_clicked(self):
        self.text_box.delete("1.0", "end")

    def _on_paste_clicked(self):
        try:
            import pyperclip

            text = pyperclip.paste()
        except Exception:
            text = ""
        if text:
            self.text_box.delete("1.0", "end")
            self.text_box.insert("1.0", text)

    def _read_selection_flow(self):
        text = read_current_selection()
        if not text.strip():
            return
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
        self._start_reading(text)

    # --------------------------------------------------------- screen OCR --

    def _resolve_tesseract(self):
        """Returns (tesseract_exe_path, tessdata_dir), preferring a
        user-configured path, then the bundled portable copy, then
        whatever's on the system PATH."""
        custom = self.cfg.get("tesseract_path", "").strip()
        if custom:
            return custom, ""
        if has_bundled_tesseract():
            return bundled_tesseract_exe(), bundled_tessdata_dir()
        return "", ""

    def _on_capture_clicked(self):
        tess_path, _ = self._resolve_tesseract()
        if not tess_path and shutil.which("tesseract") is None:
            self._set_status_text(t("status_no_tesseract", self.lang))
            return
        self._set_status_text(t("status_capturing", self.lang))
        self.root.withdraw()
        self.root.after(150, self._start_region_selector)

    def _start_region_selector(self):
        RegionSelector(self.root, on_selected=self._on_region_selected, on_cancel=self._on_region_cancelled)

    def _on_region_cancelled(self):
        self.root.deiconify()
        self._apply_state(self._current_state)

    def _on_region_selected(self, bbox):
        self.root.deiconify()
        self._set_status_text(t("status_ocr", self.lang))
        threading.Thread(target=self._run_ocr_thread, args=(bbox,), daemon=True).start()

    def _run_ocr_thread(self, bbox):
        tess_path, tessdata_dir = self._resolve_tesseract()
        try:
            text = capture_and_ocr(bbox, tesseract_path=tess_path, tessdata_dir=tessdata_dir)
        except Exception as exc:
            msg = t("status_ocr_error", self.lang).format(error=str(exc))
            self.root.after(0, lambda: self._set_status_text(msg))
            return
        self.root.after(0, self._on_ocr_done, text)

    def _on_ocr_done(self, text):
        if not text:
            self._set_status_text(t("status_ocr_empty", self.lang))
            return
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
        self._start_reading(text)

    # ------------------------------------------------------------ status --

    def _apply_state(self, state):
        self._current_state = state
        is_paused = state == "paused"
        self.btn_pause.config(text=t("btn_resume" if is_paused else "btn_pause", self.lang))
        mapping = {"idle": "status_idle", "reading": "status_reading", "paused": "status_paused"}
        self.status_var.set(t(mapping.get(state, "status_idle"), self.lang))

    def _set_status_text(self, text: str):
        self.status_var.set(text)

    # ---------------------------------------------------------- settings --

    def _on_browse_tesseract(self):
        path = filedialog.askopenfilename(
            title=t("settings_tesseract_path", self.lang),
            filetypes=[("tesseract.exe", "tesseract.exe"), ("All files", "*.*")],
        )
        if path:
            self.tess_path_var.set(path)

    def _on_save_settings(self):
        self.cfg["rate"] = int(self.rate_var.get())
        self.cfg["volume"] = round(self.volume_var.get() / 100.0, 2)
        self.cfg["hotkey_read_selection"] = self.hotkey_sel_var.get().strip() or DEFAULTS["hotkey_read_selection"]
        self.cfg["hotkey_capture_screen"] = self.hotkey_cap_var.get().strip() or DEFAULTS["hotkey_capture_screen"]
        self.cfg["tesseract_path"] = self.tess_path_var.get().strip()

        self._push_voice_selection_to_engine()
        self.tts.set_rate(self.cfg["rate"])
        self.tts.set_volume(self.cfg["volume"])

        save(self.cfg)
        self._register_hotkeys()
        self._refresh_read_tab_texts()
        self._set_status_text(t("settings_saved", self.lang))

    def _register_hotkeys(self):
        self.hotkeys.register(
            "selection", self.cfg["hotkey_read_selection"], lambda: self.root.after(0, self._read_selection_flow)
        )
        self.hotkeys.register(
            "capture", self.cfg["hotkey_capture_screen"], lambda: self.root.after(0, self._on_capture_clicked)
        )

    # ------------------------------------------------------------ language --

    def _on_ui_lang_changed(self, _event=None):
        self.lang = "en" if self.ui_lang_combo.current() == 0 else "no"
        self.cfg["ui_language"] = self.lang
        save(self.cfg)
        self._apply_language()

    def _apply_language(self):
        self.root.title(t("app_title", self.lang))
        self.notebook.tab(self.read_tab, text=t("tab_read", self.lang))
        self.notebook.tab(self.settings_tab, text=t("tab_settings", self.lang))
        self._refresh_read_tab_texts()
        self._refresh_settings_texts()
        self.tray.set_language(self.lang)
        self._apply_state(self._current_state)

    def _refresh_read_tab_texts(self):
        self.btn_read.config(text=t("btn_read", self.lang))
        self.btn_pause.config(text=t("btn_resume" if self._current_state == "paused" else "btn_pause", self.lang))
        self.btn_stop.config(text=t("btn_stop", self.lang))
        self.btn_clear.config(text=t("btn_clear", self.lang))
        self.btn_paste.config(text=t("btn_paste", self.lang))
        self.btn_capture.config(text=t("btn_capture_screen", self.lang))
        self.btn_read_selection.config(text=t("btn_read_selection", self.lang))
        self.lang_override_label.config(text=t("lang_override_label", self.lang))

        current_code = self._current_lang_override() if hasattr(self, "lang_override_combo") else "auto"
        self.lang_override_combo["values"] = [
            t("lang_auto", self.lang),
            t("lang_en", self.lang),
            t("lang_no", self.lang),
        ]
        self.lang_override_combo.current(_LANG_OVERRIDE_CODES.index(current_code))

        self.hotkey_hint_var.set(t("hotkey_hint", self.lang).format(hotkey=self.cfg["hotkey_read_selection"]))

    def _refresh_settings_texts(self):
        self.ui_lang_label.config(text=t("settings_ui_language", self.lang))
        self.voices_label.config(text=t("settings_voices", self.lang))
        self.en_voice_label.config(text=t("settings_en_voice", self.lang))
        self.no_voice_label.config(text=t("settings_no_voice", self.lang))
        self.refresh_voices_btn.config(text=t("settings_refresh_voices", self.lang))
        self.install_no_voice_btn.config(text=t("settings_install_no_voice", self.lang))
        self.rate_label.config(text=t("settings_rate", self.lang))
        self.volume_label.config(text=t("settings_volume", self.lang))
        self.hotkeys_label.config(text=t("settings_hotkeys", self.lang))
        self.hotkey_sel_label.config(text=t("settings_hotkey_selection", self.lang))
        self.hotkey_cap_label.config(text=t("settings_hotkey_capture", self.lang))
        self.tess_label.config(text=t("settings_tesseract", self.lang))
        self.tess_path_label.config(text=t("settings_tesseract_path", self.lang))
        self.browse_btn.config(text=t("settings_browse", self.lang))
        self.save_btn.config(text=t("settings_save", self.lang))

    # ---------------------------------------------------------- lifecycle --

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_close_button(self):
        if self.tray.available:
            self.root.withdraw()
        else:
            self._quit()

    def _quit(self):
        try:
            self.hotkeys.unregister_all()
        except Exception:
            pass
        try:
            self.tray.stop()
        except Exception:
            pass
        try:
            self.tts.shutdown()
        except Exception:
            pass
        self.root.destroy()
