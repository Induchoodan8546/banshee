"""Paths, kill spell, model, and flags. No cloud endpoints."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
ASSETS_ROOM = ASSETS / "room"
ASSETS_GHOST = ASSETS / "ghost"
ASSETS_SHADOWS = ASSETS / "shadows"
ASSETS_UI = ASSETS / "ui"

# Cropped bedroom only — no TV / controller bezel.
ROOM_W = 1072
ROOM_H = 596
CHAT_DOCK_H = 168
WINDOW_W = ROOM_W
WINDOW_H = ROOM_H + CHAT_DOCK_H
FPS = 60
INNER = (0, 0, ROOM_W, ROOM_H)
FLOOR_Y = 510
CAPTION_Y = ROOM_H - 34

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.environ.get("BANSHEE_MODEL", "llama3.2:3b")
LOW_RAM_MODEL = "phi3:mini"
CHAT_TIMEOUT_S = 12
MEMORY_TURNS = 8
WAKE_POLL_S = 2.0

KILL_SPELL = "bazinga"
WAKE_THE_SPIRIT = "wake the spirit"
WALL_IS_BUFFERING = "the wall is buffering"

SAFE = False
HOUSE_ONLY = False

PLAYGROUND = Path.home() / "BansheePlayground"
NOTE_NAME = "DO_NOT_READ.txt"
WALLPAPER_SAVE = DATA / "wallpaper.json"
BANISHED_FLAG = DATA / "banished.flag"
ALLOWED_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",
    "charmap": "charmap.exe",
}
SEARCH_URLS = [
    "https://www.google.com/search?q=how+to+remove+a+cartoon+ghost+from+windows",
    "https://www.google.com/search?q=is+my+cursor+haunted",
    "https://www.google.com/search?q=bazinga+exorcism+spell",
]
SIDEBAR_W = 300
