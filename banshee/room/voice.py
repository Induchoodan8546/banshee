"""Threaded Ollama calls so the bedroom never freezes."""

from __future__ import annotations

import threading
import time

from banshee.brain import Brain
from banshee.config import WAKE_POLL_S, WAKE_THE_SPIRIT, WALL_IS_BUFFERING


class Voice:
    def __init__(self) -> None:
        self.brain = Brain()
        self.busy = False
        self.bubble = ""
        self._lock = threading.Lock()
        self._pending: str | None = None

    def ask(self, prompt: str, activity: str = "") -> bool:
        with self._lock:
            if self.busy:
                return False
            self.busy = True
            self.bubble = "..."
        thread = threading.Thread(
            target=self._run,
            args=(prompt, activity),
            daemon=True,
        )
        thread.start()
        return True

    def poll(self) -> str | None:
        with self._lock:
            text = self._pending
            self._pending = None
            return text

    def _run(self, prompt: str, activity: str) -> None:
        if activity:
            self.brain.set_activity(activity)
        if not self.brain.is_awake():
            with self._lock:
                self.bubble = WAKE_THE_SPIRIT
            while not self.brain.is_awake():
                time.sleep(WAKE_POLL_S)
        try:
            text = self.brain.chat(prompt, use_tools=False)
        except Exception:
            text = WALL_IS_BUFFERING
        text = (text or WALL_IS_BUFFERING).strip()
        with self._lock:
            self._pending = text
            self.bubble = text
            self.busy = False
