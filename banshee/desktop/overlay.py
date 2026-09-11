"""Hidden Tk root + always-visible chat Toplevel. Mascot is a sibling window."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from banshee.config import KILL_SPELL
from banshee.desktop.mascot import DesktopMascot
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher

BOX_W, BOX_H = 280, 176


class Overlay:
    def __init__(self) -> None:
        self._root: tk.Tk | None = None
        self._chat: tk.Toplevel | None = None
        self._log: tk.Text | None = None
        self._entry: tk.Entry | None = None
        self.voice: Voice | None = None
        self.killer: Banisher | None = None
        self.mascot: DesktopMascot | None = None
        self._alive = True

    def attach(self, voice: Voice, killer: Banisher) -> None:
        self.voice = voice
        self.killer = killer

    def add(self, who: str, text: str) -> None:
        text = (text or "").replace("\n", " ").strip()
        if not text or self._log is None:
            return
        prefix = "you: " if who == "you" else "banshee: "
        try:
            self._log.configure(state="normal")
            self._log.insert("end", prefix + text + "\n")
            self._log.see("end")
            self._log.configure(state="disabled")
        except tk.TclError:
            pass

    def set_line(self, text: str) -> None:
        self.add("banshee", text)

    def cursor_target(self) -> tuple[int, int] | None:
        entry = self._entry
        if entry is None:
            return None
        try:
            entry.update_idletasks()
            x = entry.winfo_rootx() + max(12, entry.winfo_width() // 2)
            y = entry.winfo_rooty() + max(6, entry.winfo_height() // 2)
            return (int(x), int(y))
        except tk.TclError:
            return None

    def _on_ui(self, fn) -> None:
        root = self._root
        if root is None:
            return
        try:
            root.after(0, fn)
        except tk.TclError:
            pass

    def seize_input(self) -> None:
        def _go() -> None:
            self._pin_chat()
            chat = self._chat
            if chat is None:
                return
            try:
                chat.deiconify()
                chat.lift()
                chat.focus_force()
                if self._entry is not None:
                    self._entry.focus_force()
                    self._entry.icursor("end")
                pos = self.cursor_target()
                if pos:
                    from banshee.desktop import possessor

                    if not possessor.SAFE:
                        possessor._set_cursor(pos[0], pos[1])
            except tk.TclError:
                pass

        self._on_ui(_go)

    def release_input(self) -> None:
        self._on_ui(self._pin_chat)

    def keep_front(self) -> None:
        def _go() -> None:
            if self.mascot is not None:
                self.mascot.pin()
            self._pin_chat()

        self._on_ui(_go)

    def stop(self) -> None:
        self._alive = False
        root = self._root
        if root is not None:
            try:
                root.quit()
                root.destroy()
            except Exception:
                pass

    def run(self) -> None:
        self._build()
        assert self._root is not None
        self.mascot = DesktopMascot(self._root)
        self.add("banshee", "now your system is mine. type here.")
        self._root.after(30, self._tick)
        self._root.mainloop()

    def _tick(self) -> None:
        root = self._root
        if root is None or not self._alive:
            return
        if self.killer is not None and self.killer.hit.is_set():
            self.stop()
            return
        if self.voice is not None:
            line = self.voice.poll()
            if line:
                self.add("banshee", line)
                if self.mascot is not None:
                    self.mascot.talk()
        if self.mascot is not None:
            self.mascot.step()
        self._pin_chat()
        root.after(33, self._tick)

    def _build(self) -> None:
        root = tk.Tk()
        self._root = root
        root.withdraw()

        chat = tk.Toplevel(root)
        self._chat = chat
        chat.title("BANSHEE")
        chat.configure(bg="#1a1028")
        chat.resizable(False, False)
        chat.attributes("-topmost", True)
        sw = chat.winfo_screenwidth()
        sh = chat.winfo_screenheight()
        x = max(8, sw - BOX_W - 16)
        y = max(8, sh - BOX_H - 56)
        chat.geometry(f"{BOX_W}x{BOX_H}+{x}+{y}")
        chat.protocol("WM_DELETE_WINDOW", self._on_close)

        tiny = tkfont.Font(family="Consolas", size=8)
        tk.Label(
            chat,
            text=f"chat  ·  type {KILL_SPELL} here to banish",
            bg="#1a1028",
            fg="#9a7ab8",
            font=tiny,
        ).pack(anchor="w", padx=8, pady=(6, 0))

        self._log = tk.Text(
            chat,
            height=5,
            bg="#12081c",
            fg="#e8d4f0",
            font=tiny,
            wrap="word",
            state="disabled",
            relief="flat",
        )
        self._log.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        row = tk.Frame(chat, bg="#1a1028")
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
        chat.update_idletasks()
        self._pin_chat()
        self._entry.focus_set()

    def _pin_chat(self) -> None:
        chat = self._chat
        if chat is None or not self._alive:
            return
        try:
            chat.deiconify()
            chat.attributes("-topmost", True)
            chat.lift()
        except tk.TclError:
            pass

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
        if not self._alive or self._chat is None:
            return
        self.add("banshee", "closing the x is cute. i am not a window.")
        self._chat.withdraw()
        if self._root is not None:
            self._root.after(1500, self._come_back)

    def _come_back(self) -> None:
        if not self._alive or self._chat is None:
            return
        try:
            self._chat.deiconify()
            self._pin_chat()
        except tk.TclError:
            pass
