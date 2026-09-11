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

WINDOW_W = 1248
WINDOW_H = 832
FPS = 60
INNER = (77, 70, 1171, 540)
CAPTION_RECT = (710, 726, 1140, 800)
FLOOR_Y = 518

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
