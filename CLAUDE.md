# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Norvox Reader: a standalone Windows desktop app (Tkinter) that reads text aloud in English and Norwegian, targeted at accessibility use (e.g. reading schoolbooks that block text selection/copying). Four input paths: typed/pasted text, a screen-region OCR capture, a global hotkey that reads whatever is currently selected in *any* other window, and a dedicated hotkey straight to screen capture. UI is bilingual (English/Norwegian) via `app/i18n.py`.

Windows-only by design (SAPI5 speech, Win32 DPI/window APIs, `keyboard`/`pystray` Windows backends). There is no test suite and no linter configured — don't invent commands for either.

## Commands

```bash
# Setup (venv already exists at .venv; recreate with `python -m venv .venv` if needed)
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Run from source
.venv\Scripts\python.exe main.py

# Sanity-check all modules compile (closest thing to a lint check here)
.venv\Scripts\python.exe -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('app/*.py') + ['main.py']]"

# Build a standalone --onedir exe (needs pyinstaller; see build_exe.ps1)
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

There's no `pytest`/`unittest` suite. Ad hoc verification during development has been done by writing small throwaway scripts that import `app.*` modules directly (e.g. instantiate `TTSEngine`, call `.list_voices()`/`.speak()`), running them via `.venv\Scripts\python.exe`, and deleting them afterward — follow that pattern rather than adding a permanent test framework unless asked.

## Architecture

### TTS: single-threaded COM owner + queue, not a call-and-return API

`app/sapi5.py` (`Sapi5Voice`) is a thin direct wrapper around the Windows `SAPI.SPVoice` COM object via `comtypes` — no third-party TTS library. `app/tts_engine.py` (`TTSEngine`) owns one dedicated background thread that creates and exclusively drives that COM object (COM/SAPI must stay on one thread). All public methods (`speak`, `pause`, `resume`, `stop`, `list_voices`) are called from the Tk main thread but only ever *enqueue* work or read from a `threading.Event`/lock-guarded counter — they never touch the COM object directly.

The interrupt model is a monotonically increasing **generation counter**: `speak()`/`stop()` bump it, and the speak loop (chunk-by-chunk, split on sentence boundaries in `_split_chunks`) checks `_still_current(gen)` between/during chunks to bail out early. This is how a new "Read" click or a Stop press interrupts speech that's already playing — there's no direct thread-cancellation. Pause takes effect at the next sentence boundary, not mid-utterance (SAPI limitation).

Voice enumeration merges two separate sources: SAPI's default `GetVoices()` (classic desktop voices) and a manually-queried `SAPI.SpObjectTokenCategory` pointed at the `Speech_OneCore\Voices` registry key (modern/language-pack voices, e.g. a Norwegian voice added via Windows Settings). The default API alone misses OneCore voices entirely — this is the fix for a real bug where a newly-installed Norwegian voice didn't show up. See `Sapi5Voice.list_voice_tokens()`.

`pyttsx3` was deliberately removed and is not a dependency — it's GPLv3-licensed, which was incompatible with this project's licensing at the time it was removed (see Licensing below). Don't reintroduce it or a similar copyleft-incompatible wrapper without checking current license constraints first.

### OCR: bundled portable Tesseract, resolved by run mode

`vendor/tesseract/` contains a trimmed, portable copy of Tesseract OCR (`tesseract.exe` + its runtime DLLs + `tessdata/{eng,nor,osd}.traineddata`) — no separate Tesseract install is required. `app/paths.py` resolves the bundled exe/tessdata path relative to `sys._MEIPASS` when frozen (PyInstaller) or relative to the repo root when run from source; `app/gui.py`'s `_resolve_tesseract()` prefers a user-configured custom path over the bundled one, and falls back to whatever's on `PATH` if neither exists.

`app/ocr_screen.py`'s `capture_and_ocr()` sets `TESSDATA_PREFIX` as an environment variable rather than passing `--tessdata-dir "<path>"` as a pytesseract config string — pytesseract splits its config string on whitespace, which silently breaks on a bundled path containing spaces (e.g. under `Program Files`).

`RegionSelector` (same file) is a borderless, semi-transparent fullscreen `Toplevel` used for drag-to-select; it only covers the primary monitor by design.

### Everything cross-thread routes back through `root.after(0, ...)`

The GUI runs background work on separate threads (TTS engine's worker thread, OCR capture, the `pystray` tray icon's own thread) and Tkinter is not thread-safe. Any callback originating off the main thread (TTS state changes, tray menu clicks, OCR completion) is wrapped in `self.root.after(0, ...)` before it touches a widget — see the lambdas passed to `TrayIcon(...)` and `self.tts.on_state_change` in `app/gui.py`. Keep this pattern for any new cross-thread callback.

### Selection-reading hotkey: release-triggered, sentinel-guarded

`app/selection_reader.py` reads "currently selected text anywhere" by writing a sentinel string to the clipboard, sending `Ctrl+C`, then checking whether the clipboard actually changed (distinguishes "nothing selected" from "the previous clipboard content"). `app/hotkeys.py` registers global hotkeys with `trigger_on_release=True` specifically so the hotkey's own modifier keys (e.g. `Ctrl+Alt+S`) are already released before the `Ctrl+C` simulation fires — otherwise a held Alt could turn it into `Ctrl+Alt+C`, which most apps don't treat as copy.

### Config and i18n

Per-user settings live in `%APPDATA%\NorvoxReader\config.json` (`app/config.py`); the schema is a flat dict with hardcoded defaults (`DEFAULTS`), no migration system. UI strings are a two-level dict (`STRINGS[lang][key]`) in `app/i18n.py` with a `t(key, lang)` lookup that falls back to English then to the raw key — add new UI text to *both* language blocks, not just one.

### Licensing shapes what dependencies are allowed

This project is licensed **GPL-2.0-or-later** (see `LICENSE`), specifically because the bundled Tesseract pulls in `libjbig-0.dll` (JBIG-KIT), which is GPL-2.0-only with no linking exception and is a hard runtime dependency (verified by removing it — Tesseract fails to launch). `THIRD_PARTY_LICENSES.md` has the full per-dependency/per-DLL license audit and the reasoning trail (an earlier closed-source-commercial plan and a later "free but non-commercial-only" plan were both ruled out by this). Before adding any new dependency or bundled binary, check it's GPL-2.0-or-later-compatible (GPL-3.0-*only* components are specifically incompatible with the existing GPL-2.0-only JBIG-KIT dependency) and update `THIRD_PARTY_LICENSES.md` accordingly — see the project's saved Claude memory for the full rule.
