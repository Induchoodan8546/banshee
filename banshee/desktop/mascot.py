"""Always-on-top ghost. Click-through so the chat box stays usable."""

from __future__ import annotations

import ctypes
import math
import random
import time
import tkinter as tk

from PIL import Image, ImageTk

from banshee.config import ASSETS_GHOST
from banshee.desktop import possessor

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


def _click_through(widget: tk.Misc) -> None:
    try:
        widget.update_idletasks()
        user32 = ctypes.windll.user32
        wid = int(widget.winfo_id())
        parent = int(user32.GetParent(wid) or 0)
        hwnd = parent or wid
        if ctypes.sizeof(ctypes.c_void_p) == 8:
            get_long = user32.GetWindowLongPtrW
            set_long = user32.SetWindowLongPtrW
        else:
            get_long = user32.GetWindowLongW
            set_long = user32.SetWindowLongW
        style = get_long(hwnd, GWL_EXSTYLE)
        set_long(
            hwnd,
            GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
        )
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    except Exception:
        pass


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
        win.update_idletasks()
        _click_through(win)

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
            _click_through(self.win)
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

        self.x += (self.tx - self.x) * min(1.0, dt * 1.8)
        self.y += (self.ty - self.y) * min(1.0, dt * 1.8)
        bob = math.sin(self._t * 2.3) * 6.0

        chat_x = self.vx + self.sw - 300
        chat_y = self.vy + self.sh - 220
        x = int(self.x)
        y = int(self.y + bob)
        x = max(self.vx, min(self.vx + self.sw - self.SIZE, x))
        y = max(self.vy, min(self.vy + self.sh - self.SIZE - 40, y))
        if x > chat_x - 20 and y > chat_y - 20:
            x = int(chat_x - self.SIZE - 12)

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
            self.canvas.coords(self._sprite, self.SIZE // 2, self.SIZE // 2 + 8)
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
