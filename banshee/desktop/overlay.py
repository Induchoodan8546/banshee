"""Small bottom-right chat. Stays on top of every window. Bazinga lives here."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import font as tkfont

from banshee.config import KILL_SPELL
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher

BOX_W, BOX_H = 280, 168


class Overlay:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._root: tk.Tk | None = None
        self._log: tk.Text | None = None
        self._entry: tk.Entry | None = None
        self.voice: Voice | None = None
        self.killer: Banisher | None = None

    def attach(self, voice: Voice, killer: Banisher) -> None:
        self.voice = voice
        self.killer = killer

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_line(self, text: str) -> None:
        self.add("banshee", text)

    def add(self, who: str, text: str) -> None:
        text = (text or "").replace("\n", " ").strip()
        if not text:
            return
        prefix = "you: " if who == "you" else "banshee: "

        def _write() -> None:
            if self._log is None:
                return
            self._log.configure(state="normal")
            self._log.insert("end", prefix + text + "\n")
            self._log.see("end")
            self._log.configure(state="disabled")

        self._ui(_write)

    def stop(self) -> None:
        self._stop.set()
        root = self._root
        if root is not None:
            try:
                root.after(0, root.destroy)
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _ui(self, fn) -> None:
        root = self._root
        if root is None:
            return
        try:
            root.after(0, fn)
        except Exception:
            pass

    def _run(self) -> None:
        try:
            self._build()
            assert self._root is not None
            self._root.mainloop()
        except Exception as exc:
            print(f"[banshee] chat box failed: {exc}", flush=True)

    def _build(self) -> None:
        root = tk.Tk()
        self._root = root
        root.title("BANSHEE")
        root.configure(bg="#1a1028")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        try:
            root.attributes("-toolwindow", True)
        except tk.TclError:
            pass
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = max(8, sw - BOX_W - 16)
        y = max(8, sh - BOX_H - 56)
        root.geometry(f"{BOX_W}x{BOX_H}+{x}+{y}")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        tiny = tkfont.Font(family="Consolas", size=8)
        tk.Label(
            root,
            text=f"banshee  ·  type {KILL_SPELL} here to banish",
            bg="#1a1028",
            fg="#9a7ab8",
            font=tiny,
        ).pack(anchor="w", padx=8, pady=(6, 0))

        self._log = tk.Text(
            root,
            height=5,
            bg="#12081c",
            fg="#e8d4f0",
            font=tiny,
            wrap="word",
            state="disabled",
            relief="flat",
        )
        self._log.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        row = tk.Frame(root, bg="#1a1028")
        row.pack(fill=tk.X, padx=8, pady=(0, 8))
        self._entry = tk.Entry(
            row,
            bg="#2a1838",
            fg="#f4e8ff",
            insertbackground="#f4e8ff",
            relief="flat",
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self._entry.bind("<Return>", self._send)
        tk.Button(
            row,
            text="say",
            command=self._send,
            bg="#3a2450",
            fg="#f4e8ff",
            relief="flat",
            font=tiny,
        ).pack(side=tk.LEFT, padx=(6, 0))

    def _send(self, event: object | None = None) -> None:
        if self._entry is None:
            return
        text = self._entry.get().strip()
        self._entry.delete(0, tk.END)
        if not text:
            return
        if text.lower().replace(" ", "") == KILL_SPELL:
            self.add("you", text)
            if self.killer is not None:
                self.killer.hit.set()
            return
        self.add("you", text)
        if self.voice is not None:
            self.voice.ask(text, activity="player", kind="player")

    def _on_close(self) -> None:
        root = self._root
        if root is None or self._stop.is_set():
            return
        self.add("banshee", "closing the x is cute. i am not a window.")
        root.withdraw()
        root.after(1500, self._come_back)

    def _come_back(self) -> None:
        if self._stop.is_set() or self._root is None:
            return
        try:
            self._root.deiconify()
            self._root.attributes("-topmost", True)
        except tk.TclError:
            pass
