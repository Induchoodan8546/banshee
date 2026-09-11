"""Always-on-top tk mascot — same toolkit as the chat box, so it stays visible."""

from __future__ import annotations

import math
import random
import time
import tkinter as tk

from PIL import Image, ImageTk

from banshee.config import ASSETS_GHOST
from banshee.desktop import possessor


class DesktopMascot:
    SIZE = 168

    def __init__(self, root: tk.Tk) -> None:
        vx, vy, sw, sh = possessor.virtual_screen()
        if sw <= 1:
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            vx, vy = 0, 0
        self.vx, self.vy, self.sw, self.sh = vx, vy, sw, sh
        self.x = float(vx + sw * 0.35)
        self.y = float(vy + sh * 0.28)
        self.tx, self.ty = self.x, self.y
        self._t = 0.0
        self._talk = 0.0
        self._blink = 0.0
        self._next_blink = random.uniform(2.0, 4.0)
        self._next_drift = time.monotonic() + 0.4
        self._photos: dict[str, ImageTk.PhotoImage] = {}
        self._kind = "body"

        win = tk.Toplevel(root)
        self.win = win
        win.overrideredirect(True)
        win.configure(bg="#ff00ff")
        win.attributes("-topmost", True)
        try:
            win.wm_attributes("-transparentcolor", "#ff00ff")
        except tk.TclError:
            pass
        win.geometry(f"{self.SIZE}x{self.SIZE}+{int(self.x)}+{int(self.y)}")

        self.canvas = tk.Canvas(
            win,
            width=self.SIZE,
            height=self.SIZE,
            bg="#ff00ff",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()
        self._load_frames()
        self._sprite = self.canvas.create_image(
            self.SIZE // 2,
            self.SIZE // 2 + 8,
            image=self._photos["body"],
        )

    def _load_frames(self) -> None:
        for name, file in (
            ("body", "body.png"),
            ("blink", "eyes_closed.png"),
            ("talk", "mouth_talk.png"),
        ):
            path = ASSETS_GHOST / file
            im = Image.open(path).convert("RGBA")
            im = im.resize((120, 120), Image.Resampling.NEAREST)
            self._photos[name] = ImageTk.PhotoImage(im)

    def talk(self) -> None:
        self._talk = 2.8

    def pin(self) -> None:
        try:
            self.win.attributes("-topmost", True)
            self.win.lift()
        except tk.TclError:
            pass

    def step(self, dt: float = 0.033) -> None:
        self._t += dt
        now = time.monotonic()
        self._next_blink -= dt
        if self._next_blink <= 0:
            self._blink = 0.12
            self._next_blink = random.uniform(2.0, 4.0)
        if self._blink > 0:
            self._blink -= dt
        if self._talk > 0:
            self._talk -= dt

        if now >= self._next_drift:
            self._pick_target()
            self._next_drift = now + random.uniform(1.2, 2.2)

        # ease toward target
        self.x += (self.tx - self.x) * min(1.0, dt * 1.8)
        self.y += (self.ty - self.y) * min(1.0, dt * 1.8)
        bob = math.sin(self._t * 2.3) * 6.0
        squash = 1.0 + math.sin(self._t * 3.6) * 0.04

        chat_x = self.vx + self.sw - 300
        chat_y = self.vy + self.sh - 220
        x = int(self.x)
        y = int(self.y + bob)
        x = max(self.vx, min(self.vx + self.sw - self.SIZE, x))
        y = max(self.vy, min(self.vy + self.sh - self.SIZE - 40, y))
        if x > chat_x - 20 and y > chat_y - 20:
            x = chat_x - self.SIZE - 8

        try:
            self.win.geometry(f"{self.SIZE}x{self.SIZE}+{x}+{y}")
            kind = "body"
            if self._blink > 0:
                kind = "blink"
            elif self._talk > 0:
                kind = "talk"
            if kind != self._kind:
                self._kind = kind
                self.canvas.itemconfigure(self._sprite, image=self._photos[kind])
            # slight breathe by moving image
            self.canvas.coords(self._sprite, self.SIZE // 2, self.SIZE // 2 + 8 + squash * 2)
        except tk.TclError:
            pass
        self.pin()

    def _pick_target(self) -> None:
        if random.random() < 0.25:
            try:
                mx, my = possessor._cursor()
                self.tx = mx - self.SIZE / 2
                self.ty = my - self.SIZE / 2
                return
            except Exception:
                pass
        self.tx = random.uniform(self.vx + 10, self.vx + self.sw - self.SIZE - 10)
        self.ty = random.uniform(self.vy + 10, self.vy + self.sh - self.SIZE - 80)
