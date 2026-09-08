"""Background text-to-speech worker built directly on Windows SAPI5 (via
app.sapi5 / comtypes — no third-party TTS wrapper library, so the app has no
GPL/LGPL dependency in its speech path).

SAPI5 must be created and driven from a single thread, so this module owns
one dedicated worker thread. All public methods are safe to call from any
thread (typically the Tkinter main thread); they communicate with the
worker through a queue and a generation counter that lets a new "speak" or
"stop" call interrupt whatever is currently playing.
"""

import queue
import re
import threading
import time
from collections import namedtuple

from app.lang_detect import detect_language
from app.sapi5 import Sapi5Voice

_MAX_CHUNK_LEN = 300

Voice = namedtuple("Voice", ["id", "name"])


def _split_chunks(text: str):
    text = (text or "").strip()
    if not text:
        return []
    raw = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    for piece in raw:
        piece = piece.strip()
        if not piece:
            continue
        while len(piece) > _MAX_CHUNK_LEN:
            cut = piece.rfind(",", 0, _MAX_CHUNK_LEN)
            if cut == -1:
                cut = piece.rfind(" ", 0, _MAX_CHUNK_LEN)
            if cut == -1:
                cut = _MAX_CHUNK_LEN
            chunks.append(piece[: cut + 1].strip())
            piece = piece[cut + 1 :].strip()
        if piece:
            chunks.append(piece)
    return chunks


class TTSEngine:
    def __init__(self, rate: int = 175, volume: float = 1.0):
        self._cmd_queue: "queue.Queue[dict]" = queue.Queue()
        self._lock = threading.Lock()
        self._generation = 0
        self._pause_event = threading.Event()
        self._pause_event.set()  # set = playing, clear = paused
        self._ready_event = threading.Event()
        self._voice = None  # Sapi5Voice, created on the worker thread

        self._rate = rate
        self._volume = volume
        self._voices_by_lang = {"en": None, "no": None}
        self._voice_tokens = {}  # voice id -> live SAPI token (worker thread only)

        self.on_state_change = None  # callable(state: str)

        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ---- public API -----------------------------------------------------

    def wait_ready(self, timeout: float = 5.0) -> bool:
        return self._ready_event.wait(timeout)

    def set_voice_for_lang(self, lang: str, voice_id):
        self._voices_by_lang[lang] = voice_id

    def set_rate(self, rate: int):
        self._rate = rate

    def set_volume(self, volume: float):
        self._volume = volume

    def list_voices(self):
        """Returns installed SAPI5 voices, including modern "OneCore" voices
        added via Settings > Time & Language > Speech (e.g. language-pack
        Norwegian voices), which SAPI's default voice list does not include."""
        if not self.wait_ready():
            return []
        return self._call_sync(self._do_list_voices)

    def speak(self, text: str, lang_override: str = "auto"):
        chunks = _split_chunks(text)
        if not chunks:
            return
        self._drain_queue()
        with self._lock:
            self._generation += 1
            gen = self._generation
        self._pause_event.set()
        self._cmd_queue.put(
            {"kind": "speak", "chunks": chunks, "lang_override": lang_override, "gen": gen}
        )

    def pause(self):
        self._pause_event.clear()
        self._set_state("paused")

    def resume(self):
        self._pause_event.set()
        self._set_state("reading")

    def stop(self):
        self._drain_queue()
        with self._lock:
            self._generation += 1
        self._pause_event.set()
        self._set_state("idle")

    def shutdown(self):
        self._drain_queue()
        self._cmd_queue.put({"kind": "shutdown"})
        self._thread.join(timeout=3)

    # ---- internals --------------------------------------------------------

    def _drain_queue(self):
        try:
            while True:
                self._cmd_queue.get_nowait()
        except queue.Empty:
            pass

    def _set_state(self, state: str):
        if self.on_state_change:
            try:
                self.on_state_change(state)
            except Exception:
                pass

    def _call_sync(self, fn, timeout: float = 5.0):
        result = {}
        done = threading.Event()

        def wrapper():
            try:
                result["value"] = fn()
            except Exception as exc:  # noqa: BLE001
                result["error"] = exc
            finally:
                done.set()

        self._cmd_queue.put({"kind": "call", "fn": wrapper})
        done.wait(timeout)
        if "error" in result:
            raise result["error"]
        return result.get("value")

    def _worker(self):
        self._voice = Sapi5Voice()
        self._voice.set_rate_wpm(self._rate)
        self._voice.set_volume(self._volume)
        self._ready_event.set()

        try:
            while True:
                job = self._cmd_queue.get()
                kind = job.get("kind")
                if kind == "shutdown":
                    break
                elif kind == "call":
                    job["fn"]()
                elif kind == "speak":
                    self._do_speak_job(job)
        finally:
            self._voice.close()

    def _do_speak_job(self, job):
        gen = job["gen"]
        lang_override = job["lang_override"]

        self._set_state("reading")
        for chunk in job["chunks"]:
            if not self._still_current(gen):
                return
            if not self._wait_while_paused(gen):
                return

            lang = lang_override if lang_override in ("en", "no") else detect_language(chunk)
            voice_id = self._voices_by_lang.get(lang)
            try:
                if voice_id:
                    self._set_voice(voice_id)
                self._voice.set_rate_wpm(self._rate)
                self._voice.set_volume(self._volume)
            except Exception:
                pass

            self._speak_chunk_interruptible(chunk, gen)

        if self._still_current(gen):
            self._set_state("idle")

    def _wait_while_paused(self, gen) -> bool:
        while not self._pause_event.is_set():
            if not self._still_current(gen):
                return False
            time.sleep(0.05)
        return True

    def _do_list_voices(self):
        """Runs on the worker thread."""
        tokens = self._voice.list_voice_tokens()
        self._voice_tokens = tokens

        result = []
        for voice_id, token in tokens.items():
            try:
                name = token.GetDescription()
            except Exception:
                name = voice_id
            result.append(Voice(voice_id, name))
        return result

    def _set_voice(self, voice_id):
        token = self._voice_tokens.get(voice_id)
        if token is not None:
            try:
                self._voice.set_voice(token)
            except Exception:
                pass

    def _speak_chunk_interruptible(self, chunk: str, gen: int) -> None:
        self._voice.speak_async(chunk)
        # Generous safety timeout (real speech is ~150-200 wpm, i.e. well
        # under 0.15s/char) in case SAPI status ever gets stuck, so a single
        # bad chunk can't hang the app forever.
        deadline = time.time() + max(10.0, len(chunk) * 0.15)
        while not self._voice.is_done():
            if not self._still_current(gen):
                self._voice.purge()
                break
            if time.time() > deadline:
                self._voice.purge()
                break
            time.sleep(0.02)

    def _still_current(self, gen: int) -> bool:
        with self._lock:
            return gen == self._generation
