"""Always-on-top ghost chat. X is not an exorcism."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import font as tkfont

from banshee.config import ASSETS_GHOST, KILL_SPELL, SAFE


class Overlay:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._line = "you closed the window."
        self._thread: threading.Thread | None = None
        self._root: tk.Tk | None = None
        self._label: tk.Label | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if SAFE:
            print("[banshee] would show uncloseable overlay", flush=True)
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_line(self, text: str) -> None:
        text = (text or "").replace("\n", " ").strip()
        if not text:
            return
        with self._lock:
            self._line = text[:140]
        root = self._root
        label = self._label
        if root is not None and label is not None:
            try:
                root.after(0, lambda: label.config(text=self._line))
            except Exception:
                pass

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
        root.resizable(False, False)
        root.attributes("-topmost", True)
        try:
            root.attributes("-toolwindow", True)
        except tk.TclError:
            pass
        w, h = 280, 150
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{sw - w - 24}+{sh - h - 64}")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        face = tk.Label(root, text="ghost", bg="#1a1028", fg="#e8d4f0")
        png = ASSETS_GHOST / "body.png"
        if png.exists():
            try:
                img = tk.PhotoImage(file=str(png))
                img = img.subsample(max(1, img.width() // 48), max(1, img.height() // 48))
                face.configure(image=img, text="")
                face.image = img
            except Exception:
                face.configure(text="B")
        face.pack(side=tk.LEFT, padx=8, pady=8)

        body = tk.Frame(root, bg="#1a1028")
        body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=8)
        hint = tkfont.Font(family="Consolas", size=8)
        speech = tkfont.Font(family="Consolas", size=10)
        self._label = tk.Label(
            body,
            text=self._line,
            bg="#1a1028",
            fg="#f4e8ff",
            font=speech,
            wraplength=190,
            justify=tk.LEFT,
            anchor="nw",
        )
        self._label.pack(anchor="w")
        tk.Label(
            body,
            text=f"type {KILL_SPELL}",
            bg="#1a1028",
            fg="#9a7ab8",
            font=hint,
        ).pack(anchor="w", pady=(8, 0))

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
