"""Boot. Close the bedroom to possess the desktop (unless --house-only)."""

from __future__ import annotations

import argparse
import shutil
import sys

from banshee import config
from banshee.brain import Brain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BANSHEE — local poltergeist")
    parser.add_argument("--chat", action="store_true", help="talk to the ghost in the terminal")
    parser.add_argument("--safe", action="store_true", help="fake desktop mischief; no real changes")
    parser.add_argument("--house-only", action="store_true", help="bedroom only; closing just quits")
    return parser.parse_args()


def run_chat() -> int:
    brain = Brain()
    brain.wait_until_awake()
    print(brain.chat("Who are you?"), flush=True)
    print(f"(type {config.KILL_SPELL} to banish)", flush=True)
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.lower() == config.KILL_SPELL:
            print(
                brain.chat(
                    f"the human said {config.KILL_SPELL}. "
                    "say a short goodbye and stop haunting."
                ),
                flush=True,
            )
            return 0
        print(brain.chat(line), flush=True)


def _ensure_wallpaper_asset() -> None:
    dest = config.ASSETS_UI / "wallpaper.png"
    if dest.exists():
        return
    src = config.ASSETS_ROOM / "bg.png"
    if src.exists():
        config.ASSETS_UI.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)


def main() -> int:
    args = parse_args()
    config.SAFE = bool(args.safe)
    config.HOUSE_ONLY = bool(args.house_only)
    if args.chat:
        return run_chat()
    _ensure_wallpaper_asset()
    from banshee.room.scene import run_house

    outcome = run_house(possess_on_close=not config.HOUSE_ONLY)
    if outcome == "possess":
        from banshee.desktop.haunt_loop import run_possession

        return run_possession()
    return 0


if __name__ == "__main__":
    sys.exit(main())
