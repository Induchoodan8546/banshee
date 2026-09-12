"""Hidden Tk root + always-visible chat Toplevel. Mascot is a sibling window."""

from __future__ import annotations

import random
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

from banshee.config import KILL_SPELL
from banshee.desktop import monitor
from banshee.desktop.mascot import DesktopMascot
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher

BOX_W, BOX_H = 300, 210


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
        self._mode_hint: tk.Label | None = None
        self._speak_btn: tk.Button | None = None
        self._next_ambient = 0.0
        self._chat_box = (0, 0, 0, 0)
        self._chatting_until = 0.0

    def attach(self, voice: Voice, killer: Banisher) -> None:
        self.voice = voice
        self.killer = killer

    def add(self, who: str, text: str) -> None:
        text = (text or "").replace("\n", " ").strip()
        if not text:
            return
        if who == "banshee":
            from banshee.voice_io import maybe_speak

            maybe_speak(text)
        if self._log is None:
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
        """Chat is independent of possession — only keep it on top."""
        self.keep_front()

    def release_input(self) -> None:
        self.keep_front()

    def chat_screen_rect(self) -> tuple[int, int, int, int] | None:
        box = self._chat_box
        if box[2] <= box[0]:
            return None
        return box

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
        from banshee.desktop import possessor as _pos

        _pos.set_cursor_safe_zone(self.chat_screen_rect)
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
            if self.voice.busy:
                live = self.voice.snapshot()
                if live and self.mascot is not None:
                    self.mascot.say(live, hold=2.5)
            line = self.voice.poll()
            if line:
                self.add("banshee", line)
                if self.mascot is not None:
                    self.mascot.say(line)
                    self.mascot.talk()
            now = time.monotonic()
            if (
                now >= self._next_ambient
                and not self.voice.talking_to_player()
                and not self.voice.pending_work()
            ):
                title = monitor.foreground_title() or "the desktop"
                self.voice.ask(
                    f"the human is using this window right now: {title}. "
                    "mock what they are doing in one short sentence. stay on that topic.",
                    activity=f"they are in: {title}",
                    kind="ambient",
                )
                self._next_ambient = now + random.uniform(7.0, 11.0)
        if self.mascot is not None:
            self.mascot.step()
        self._remember_chat_rect()
        now = time.monotonic()
        if now - getattr(self, "_last_pin", 0) > 0.45:
            self._pin_chat()
            self._last_pin = now
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
        modes = tk.Frame(chat, bg="#1a1028")
        modes.pack(fill=tk.X, padx=8)
        self._mode_label = tk.StringVar(value="text")
        tiny_btn = {"bg": "#3a2450", "fg": "#f4e8ff", "relief": "flat", "font": tiny}
        tk.Button(modes, text="text", command=lambda: self._set_mode(False), **tiny_btn).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(modes, text="audio", command=lambda: self._set_mode(True), **tiny_btn).pack(side=tk.LEFT, padx=(0, 4))
        self._speak_btn = tk.Button(modes, text="speak", command=self._listen, **tiny_btn)
        self._speak_btn.pack(side=tk.LEFT)
        self._mode_hint = tk.Label(modes, text="mode: text", bg="#1a1028", fg="#9a7ab8", font=tiny)
        self._mode_hint.pack(side=tk.LEFT, padx=8)

        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self._entry.bind("<Return>", self._send)
        self._entry.bind("<FocusIn>", self._on_user_chat)
        self._entry.bind("<Key>", self._on_user_chat)
        self._entry.bind("<Button-1>", self._on_user_chat)
        chat.bind("<Button-1>", self._on_user_chat)
        chat.bind("<FocusIn>", self._on_user_chat)
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

    def _chat_hwnd(self) -> int:
        chat = self._chat
        if chat is None:
            return 0
        import ctypes

        wid = int(chat.winfo_id())
        user32 = ctypes.windll.user32
        hwnd = int(user32.GetAncestor(wid, 2) or user32.GetParent(wid) or wid)
        return hwnd

    def _force_foreground(self) -> None:
        hwnd = self._chat_hwnd()
        if not hwnd:
            return
        import ctypes

        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)
        user32.keybd_event(0x12, 0, 0, 0)
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)

    def _focus_chat(self, hard: bool = False) -> None:
        chat = self._chat
        if chat is None or not self._alive:
            return
        try:
            chat.deiconify()
            chat.attributes("-topmost", True)
            chat.lift()
            if hard:
                self._force_foreground()
            if self._entry is not None:
                self._entry.focus_set()
                self._entry.focus_force()
            if hard:
                pos = self.cursor_target()
                if pos:
                    from banshee.desktop import possessor

                    if not possessor.SAFE:
                        possessor._set_cursor(pos[0], pos[1])
        except tk.TclError:
            pass

    def _remember_chat_rect(self) -> None:
        chat = self._chat
        if chat is None:
            return
        try:
            chat.update_idletasks()
            x0 = int(chat.winfo_rootx())
            y0 = int(chat.winfo_rooty())
            self._chat_box = (x0, y0, x0 + int(chat.winfo_width()), y0 + int(chat.winfo_height()))
        except tk.TclError:
            pass

    def _pin_chat(self) -> None:
        chat = self._chat
        if chat is None or not self._alive:
            return
        try:
            chat.attributes("-topmost", True)
            typing = self._entry is not None and chat.focus_get() is self._entry
            if not typing:
                chat.lift()
        except tk.TclError:
            pass

    def _on_user_chat(self, event: object | None = None) -> None:
        self._chatting_until = time.monotonic() + 14.0
        from banshee.desktop import possessor as _pos

        _pos.pause_cursor(14.0)

    def chatting(self) -> bool:
        return time.monotonic() < self._chatting_until

    def _set_mode(self, audio: bool) -> None:
        from banshee.voice_io import set_audio_mode

        set_audio_mode(audio)
        if self._mode_hint is not None:
            self._mode_hint.config(text="mode: audio" if audio else "mode: text")
        self.add("banshee", "i'll hiss in your speakers." if audio else "fine. text only.")

    def _listen(self) -> None:
        self._on_user_chat()
        if self._speak_btn is not None:
            self._speak_btn.config(text="...")

        def _job() -> None:
            from banshee.voice_io import listen_once

            heard = listen_once()
            self._on_ui(lambda: self._finish_listen(heard))

        threading.Thread(target=_job, daemon=True).start()

    def _finish_listen(self, heard: str) -> None:
        if self._speak_btn is not None:
            self._speak_btn.config(text="speak")
        if not heard:
            self.add("banshee", "i didn't catch that. try again.")
            return
        if self._entry is not None:
            self._entry.delete(0, tk.END)
        self._submit(heard)

    def _send(self, event: object | None = None) -> None:
        if self._entry is None:
            return
        text = self._entry.get().strip()
        self._entry.delete(0, tk.END)
        if not text:
            return
        self._submit(text)

    def _submit(self, text: str) -> None:
        text = (text or "").strip()
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
        import threading as _th

        from banshee.desktop import possessor as _pos

        _th.Thread(target=_pos.defy, args=(text,), daemon=True).start()

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
