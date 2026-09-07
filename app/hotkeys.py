"""Registers global hotkeys (work even when the window isn't focused) using
the `keyboard` library. Hotkeys fire on key release so modifier keys are
already up by the time we simulate Ctrl+C for the selection reader.
"""


class HotkeyManager:
    def __init__(self):
        self._registered = {}  # name -> hotkey string
        self._available = True
        try:
            import keyboard  # noqa: F401
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def register(self, name: str, hotkey: str, callback):
        if not self._available or not hotkey:
            return
        import keyboard

        self.unregister(name)
        try:
            keyboard.add_hotkey(hotkey, callback, trigger_on_release=True)
            self._registered[name] = hotkey
        except Exception:
            pass

    def unregister(self, name: str):
        if not self._available:
            return
        import keyboard

        old = self._registered.pop(name, None)
        if old:
            try:
                keyboard.remove_hotkey(old)
            except Exception:
                pass

    def unregister_all(self):
        for name in list(self._registered.keys()):
            self.unregister(name)
        if self._available:
            import keyboard

            try:
                keyboard.unhook_all()
            except Exception:
                pass
