"""Locates bundled resources (the vendored portable Tesseract OCR engine),
whether running from source or from a PyInstaller build."""

import os
import sys


def get_app_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # set for both --onefile and --onedir builds
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundled_tesseract_exe() -> str:
    return os.path.join(get_app_base_dir(), "vendor", "tesseract", "tesseract.exe")


def bundled_tessdata_dir() -> str:
    return os.path.join(get_app_base_dir(), "vendor", "tesseract", "tessdata")


def has_bundled_tesseract() -> bool:
    return os.path.isfile(bundled_tesseract_exe())
