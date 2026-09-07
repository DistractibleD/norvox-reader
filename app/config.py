"""Loads and saves per-user settings from %APPDATA%\\TextReader\\config.json."""

import json
import os

DEFAULTS = {
    "ui_language": "en",
    "rate": 175,
    "volume": 1.0,
    "voice_en": None,
    "voice_no": None,
    "hotkey_read_selection": "ctrl+alt+s",
    "hotkey_capture_screen": "ctrl+alt+d",
    "tesseract_path": "",
}


def _config_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "TextReader")
    os.makedirs(path, exist_ok=True)
    return path


def _config_path() -> str:
    return os.path.join(_config_dir(), "config.json")


def load() -> dict:
    cfg = dict(DEFAULTS)
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update({k: v for k, v in saved.items() if k in DEFAULTS})
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save(cfg: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}, f, indent=2, ensure_ascii=False)
