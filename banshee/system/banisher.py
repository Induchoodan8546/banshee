"""Global bazinga hook. Letters only, case-insensitive rolling buffer."""

from __future__ import annotations

import threading

from banshee.config import KILL_SPELL


class Banisher:
    def __init__(self) -> None:
        self.hit = threading.Event()
        self._buf = ""
        self._listener = None

    def start(self) -> None:
        try:
            from pynput import keyboard
        except ImportError:
            print("[banshee] pynput missing — type bazinga in this console instead", flush=True)
            return
        needle = KILL_SPELL.lower()

        def on_press(key: object) -> None:
            ch = getattr(key, "char", None)
            if not ch or not ch.isalpha():
                return
            self._buf = (self._buf + ch.lower())[-len(needle) :]
            if self._buf == needle:
                self.hit.set()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
