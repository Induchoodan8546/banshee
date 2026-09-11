"""Boot. Phase 0 is a terminal chat. The pygame room starts in a later phase."""

from __future__ import annotations

import argparse
import sys

from banshee import config
from banshee.brain import Brain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BANSHEE — local poltergeist")
    parser.add_argument("--chat", action="store_true", help="talk to the ghost in the terminal")
    parser.add_argument("--safe", action="store_true", help="no-op desktop mischief later")
    parser.add_argument("--house-only", action="store_true", help="room only; later phases")
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


def main() -> int:
    args = parse_args()
    config.SAFE = bool(args.safe)
    config.HOUSE_ONLY = bool(args.house_only)
    if args.chat:
        return run_chat()
    print("Phase 0: python main.py --chat")
    print("The room is not built yet. Do not start pygame until the ghost talks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
