"""Right-side chat dock. Always on top. X is not an exorcism."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import font as tkfont

from banshee.config import ASSETS_GHOST, KILL_SPELL, SIDEBAR_W
from banshee.room.voice import Voice


class Overlay:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._line = "you closed the window."
        self._thread: threading.Thread | None = None
        self._root: tk.Tk | None = None
        self._label: tk.Label | None = None
        self._log: tk.Text | None = None
        self._entry: tk.Entry | None = None
        self._lock = threading.Lock()
        self.voice: Voice | None = None

    def attach_voice(self, voice: Voice) -> None:
        self.voice = voice

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_line(self, text: str) -> None:
        text = (text or "").replace("\n", " ").strip()
        if not text:
            return
        with self._lock:
            self._line = text[:160]
        self._ui(lambda: self._label and self._label.config(text=self._line))
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
            self._thread.join(timeout=1.2)
        self._thread = None

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
            print(f"[banshee] overlay failed: {exc}", flush=True)

    def _build(self) -> None:
        root = tk.Tk()
        self._root = root
        root.title("BANSHEE")
        root.configure(bg="#1a1028")
        root.resizable(False, True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-toolwindow", True)
        except tk.TclError:
            pass
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        h = min(560, int(sh * 0.55))
        root.geometry(f"{SIDEBAR_W}x{h}+{sw - SIDEBAR_W - 12}+80")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        top = tk.Frame(root, bg="#1a1028")
        top.pack(fill=tk.X, padx=8, pady=8)
        face = tk.Label(top, text="B", bg="#1a1028", fg="#e8d4f0")
        png = ASSETS_GHOST / "body.png"
        if png.exists():
            try:
                img = tk.PhotoImage(file=str(png))
                img = img.subsample(max(1, img.width() // 40), max(1, img.height() // 40))
                face.configure(image=img, text="")
                face.image = img
            except Exception:
                pass
        face.pack(side=tk.LEFT)
        speech = tkfont.Font(family="Consolas", size=10)
        hintf = tkfont.Font(family="Consolas", size=8)
        self._label = tk.Label(
            top,
            text=self._line,
            bg="#1a1028",
            fg="#f4e8ff",
            font=speech,
            wraplength=SIDEBAR_W - 80,
            justify=tk.LEFT,
            anchor="nw",
        )
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        tk.Label(root, text=f"type {KILL_SPELL} anywhere", bg="#1a1028", fg="#9a7ab8", font=hintf).pack(anchor="w", padx=10)

        self._log = tk.Text(
            root,
            height=12,
            bg="#12081c",
            fg="#e8d4f0",
            insertbackground="#f4e8ff",
            font=hintf,
            wrap="word",
            state="disabled",
            relief="flat",
        )
        self._log.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        row = tk.Frame(root, bg="#1a1028")
        row.pack(fill=tk.X, padx=10, pady=(0, 10))
        self._entry = tk.Entry(row, bg="#2a1838", fg="#f4e8ff", insertbackground="#f4e8ff", relief="flat")
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self._entry.bind("<Return>", self._send)
        tk.Button(
            row,
            text="say",
            command=self._send,
            bg="#3a2450",
            fg="#f4e8ff",
            relief="flat",
        ).pack(side=tk.LEFT, padx=(6, 0))
        self._entry.focus_set()

    def _send(self, event: object | None = None) -> None:
        if self._entry is None:
            return
        text = self._entry.get().strip()
        self._entry.delete(0, tk.END)
        if not text or self.voice is None:
            return
        self.add("you", text)
        if text.lower() == KILL_SPELL:
            self.voice.ask("bazinga", activity="bazinga", kind="player")
        else:
            self.voice.ask(text, activity="player", kind="player")

    def _on_close(self) -> None:
        root = self._root
        if root is None or self._stop.is_set():
            return
        self.set_line("closing the x is cute. i am not a window.")
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
