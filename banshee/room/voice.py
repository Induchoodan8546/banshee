"""Threaded Ollama calls. Player chat beats ambient mutters."""

from __future__ import annotations

import threading
import time
from collections import deque

from banshee.brain import Brain
from banshee.config import WAKE_POLL_S, WAKE_THE_SPIRIT, WALL_IS_BUFFERING


class Voice:
    def __init__(self) -> None:
        self.brain = Brain()
        self.busy = False
        self.bubble = ""
        self._lock = threading.Lock()
        self._pending: str | None = None
        self._queue: deque[tuple[str, str, str]] = deque()
        self._job_kind = "ambient"

    def ask(self, prompt: str, activity: str = "", kind: str = "ambient") -> bool:
        with self._lock:
            if kind == "player":
                self._queue = deque(item for item in self._queue if item[2] == "player")
                self._queue.appendleft((prompt, activity, "player"))
            else:
                if self.busy or any(item[2] == "player" for item in self._queue):
                    return False
                if any(item[2] == "ambient" for item in self._queue):
                    return False
                self._queue.append((prompt, activity, kind))
        self._kick()
        return True

    def poll(self) -> str | None:
        with self._lock:
            text = self._pending
            self._pending = None
            return text

    def snapshot(self) -> str:
        with self._lock:
            return self.bubble

    def pending_work(self) -> bool:
        with self._lock:
            return self.busy or bool(self._queue)

    def talking_to_player(self) -> bool:
        with self._lock:
            if self.busy and self._job_kind == "player":
                return True
            return any(item[2] == "player" for item in self._queue)

    def _kick(self) -> None:
        with self._lock:
            if self.busy:
                return
            if not self._queue:
                return
            prompt, activity, kind = self._queue.popleft()
            self.busy = True
            self._job_kind = kind
        thread = threading.Thread(
            target=self._run,
            args=(prompt, activity, kind),
            daemon=True,
        )
        thread.start()

    def _run(self, prompt: str, activity: str, kind: str) -> None:
        as_human = kind == "player"
        if as_human:
            self.brain.set_activity("the human is talking to you. answer them.")
        elif activity:
            self.brain.set_activity(activity)
        if not self.brain.is_awake():
            with self._lock:
                self.bubble = WAKE_THE_SPIRIT
            while not self.brain.is_awake():
                time.sleep(WAKE_POLL_S)

        def on_token(partial: str) -> None:
            with self._lock:
                self.bubble = partial

        try:
            text = self.brain.chat(
                prompt,
                use_tools=False,
                on_token=on_token,
                remember=as_human,
                as_human=as_human,
            )
        except Exception:
            text = WALL_IS_BUFFERING
        text = (text or WALL_IS_BUFFERING).strip()
        with self._lock:
            self._pending = text
            self.bubble = text
            self.busy = False
        self._kick()
