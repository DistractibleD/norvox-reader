"""Minimal direct wrapper around Windows SAPI5 via comtypes (MIT-licensed).

Talks to SAPI.SPVoice directly instead of going through a third-party TTS
wrapper library, so the app has no GPL/LGPL dependency in its speech path.
"""

import comtypes.client

_SPF_ASYNC = 1
_SPF_PURGE_BEFORE_SPEAK = 2
_SRSE_IS_SPEAKING = 2

_ONECORE_VOICE_CATEGORY = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices"


class Sapi5Voice:
    """Thin wrapper around one SAPI.SPVoice COM object. Not thread-safe —
    create and use from a single dedicated thread."""

    def __init__(self):
        comtypes.CoInitialize()
        self.tts = comtypes.client.CreateObject("SAPI.SPVoice")

    def close(self):
        try:
            comtypes.CoUninitialize()
        except Exception:
            pass

    def list_voice_tokens(self) -> dict:
        """Returns {voice_id: token}, merging classic desktop voices with
        modern "OneCore" voices (language-pack voices, e.g. Norwegian added
        via Settings > Time & Language > Speech, live in a separate
        registry category that the default voice list does not include)."""
        tokens = {}
        for token in self._safe_tokens(self.tts.GetVoices()):
            tokens[token.Id] = token
        try:
            category = comtypes.client.CreateObject("SAPI.SpObjectTokenCategory")
            category.SetId(_ONECORE_VOICE_CATEGORY, False)
            for token in self._safe_tokens(category.EnumerateTokens()):
                tokens.setdefault(token.Id, token)
        except Exception:
            pass
        return tokens

    @staticmethod
    def _safe_tokens(collection):
        try:
            return list(collection)
        except Exception:
            return []

    def set_voice(self, token):
        self.tts.Voice = token

    def set_rate_wpm(self, wpm: int):
        """SAPI's native Rate is an integer from -10 (slowest) to +10
        (fastest); map our words-per-minute scale onto it linearly,
        treating ~200 wpm as SAPI's default (0)."""
        sapi_rate = round((wpm - 200) / 15)
        self.tts.Rate = max(-10, min(10, sapi_rate))

    def set_volume(self, volume: float):
        self.tts.Volume = max(0, min(100, round(volume * 100)))

    def speak_async(self, text: str):
        self.tts.Speak(text, _SPF_ASYNC)

    def is_speaking(self) -> bool:
        try:
            return self.tts.Status.RunningState == _SRSE_IS_SPEAKING
        except Exception:
            return False

    def purge(self):
        try:
            self.tts.Speak("", _SPF_ASYNC | _SPF_PURGE_BEFORE_SPEAK)
        except Exception:
            pass
