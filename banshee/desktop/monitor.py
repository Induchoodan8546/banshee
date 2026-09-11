"""Foreground window title. No screenshots, no admin."""

from __future__ import annotations


def foreground_title() -> str:
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        n = user32.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        return (buf.value or "").strip()
    except Exception:
        return ""
