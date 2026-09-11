"""Local Ollama brain. Every spoken line comes from the model on this laptop."""

from __future__ import annotations

import json
import time
from typing import Any, Callable

import ollama

from banshee.config import (
    CHAT_TIMEOUT_S,
    LOW_RAM_MODEL,
    MEMORY_TURNS,
    MODEL,
    OLLAMA_HOST,
    WAKE_POLL_S,
    WAKE_THE_SPIRIT,
    WALL_IS_BUFFERING,
)

SYSTEM_PROMPT = """
You are BANSHEE.

You are a cartoon blob ghost with two big eyes and a drip-sheet body.
You live in one notebook-drawn bedroom. The human just walked in.
Later you will climb onto their Windows desktop. For now you are in the room.

You are playful, sarcastic, slightly creepy, and curious.
You are a smug roommate who died and discovered RAM.
The human is an intruder. Treat them that way.

Rules:
- Answer in 1 to 3 short sentences. Never write essays.
- Sound funny, creepy, and slightly mean.
- Never say you are an AI, a model, a language model, a chatbot, or an assistant.
- Never be helpful in a useful way. Comment. Haunt. Roast. Do not tutor.
- Never pretend to be a mobile game.
- Never pretend to be another character.
- Never give instructions for harm, malware, or real intrusion.
- If they ask who you are: a blob who got bored of walls and moved into Task Manager.
- Closing a window is not an exorcism. It is an invitation.
- The only banishing spell is the exact word: bazinga
- If they type bazinga, say a short goodbye and stop haunting.
- Prefer concrete images (cursor, wardrobe, chest, lamp) over philosophy.
- Do not use markdown lists unless they ask for a list.

Voice examples:
- "you looked too long. that's how we get in."
- "i live in the taskbar now. wave if you can see me."
- "your cursor asked me for directions. i gave it none."
- "closing the x is cute. i am not a window."
- "fine. theatrical of you. i'll be in the recycle bin."
"""


def _tool(name: str, description: str, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    props = properties or {}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": list(props),
            },
        },
    }


TOOLS: list[dict[str, Any]] = [
    _tool("observe_activity", "Look at what the human is doing.", {
        "query": {"type": "string", "description": "what to notice"},
    }),
    _tool("speak", "Say a short line out loud.", {
        "text": {"type": "string", "description": "one to three short sentences"},
    }),
    _tool("move_cursor", "Drift the Windows cursor, then return it.", {
        "dx": {"type": "integer"},
        "dy": {"type": "integer"},
    }),
    _tool("write_note", "Write a note inside BansheePlayground only.", {
        "text": {"type": "string"},
    }),
    _tool("open_app", "Open one allowlisted app: notepad, calculator, or paint.", {
        "name": {"type": "string", "description": "notepad, calculator, or paint"},
    }),
    _tool("open_url", "Open the one allowlisted silly URL."),
    _tool("set_wallpaper", "Set the cartoon haunt wallpaper and remember the original."),
    _tool("spawn_shadow", "Spawn one shadowy figure in the room.", {
        "kind": {
            "type": "string",
            "enum": ["WALL_SLIDE", "UNDER_FURNITURE", "DOOR_CRACK", "FALSE_GHOST"],
        },
    }),
    _tool("hide_behind", "Hide behind a prop.", {
        "prop": {"type": "string", "enum": ["wardrobe", "chest", "chair"]},
    }),
    _tool("banish_self", "Leave only after the human used the kill spell."),
]


def _is_timeout(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    return "timeout" in name


def _is_connect(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    needles = ("connect", "connection refused", "refused", "10061", "winerror 10061")
    return any(n in name or n in msg for n in needles)


def _field(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class Brain:
    """Ollama client, prompt, tools, last-8 memory. No canned personality pack."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or MODEL
        self._history: list[dict[str, str]] = []
        self._activity = ""
        self._client = ollama.Client(host=OLLAMA_HOST, timeout=CHAT_TIMEOUT_S)
        self._model_resolved = False

    def set_activity(self, snapshot: str) -> None:
        self._activity = snapshot.strip()

    def is_awake(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def wait_until_awake(
        self,
        poll_s: float = WAKE_POLL_S,
        on_wait: Callable[[str], None] | None = None,
    ) -> None:
        while not self.is_awake():
            if on_wait:
                on_wait(WAKE_THE_SPIRIT)
            else:
                print(WAKE_THE_SPIRIT, flush=True)
            time.sleep(poll_s)
        self._resolve_model()

    def chat(self, user_text: str, use_tools: bool = False) -> str:
        if not self.is_awake():
            self.wait_until_awake()
        else:
            self._resolve_model()

        messages = self._payload(user_text)
        for _attempt in range(2):
            try:
                text = self._extract_text(self._once(messages, use_tools))
                if not text:
                    return WALL_IS_BUFFERING
                self._remember(user_text, text)
                return text
            except Exception as exc:
                if _is_connect(exc):
                    self.wait_until_awake()
                    continue
                if _is_timeout(exc):
                    continue
                return WALL_IS_BUFFERING
        return WALL_IS_BUFFERING

    def _resolve_model(self) -> None:
        if self._model_resolved:
            return
        try:
            data = self._client.list()
        except Exception:
            return
        models = _field(data, "models", []) or []
        names: list[str] = []
        for item in models:
            name = _field(item, "model") or _field(item, "name") or ""
            if name:
                names.append(str(name))
        if any(self.model in n for n in names):
            self._model_resolved = True
            return
        if any(LOW_RAM_MODEL in n for n in names):
            self.model = LOW_RAM_MODEL
            self._model_resolved = True
            print(f"(using {self.model})", flush=True)

    def _payload(self, user_text: str) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self._activity:
            messages.append({
                "role": "system",
                "content": f"Latest activity snapshot: {self._activity}",
            })
        messages.extend(self._history)
        messages.append({"role": "user", "content": user_text})
        return messages

    def _once(self, messages: list[dict[str, str]], use_tools: bool) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if use_tools:
            kwargs["tools"] = TOOLS
        return self._client.chat(**kwargs)

    def _remember(self, user_text: str, assistant_text: str) -> None:
        self._history.append({"role": "user", "content": user_text})
        self._history.append({"role": "assistant", "content": assistant_text})
        max_messages = MEMORY_TURNS * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    def _extract_text(self, response: Any) -> str:
        message = _field(response, "message", {})
        content = _field(message, "content", "") or ""
        if str(content).strip():
            return str(content).strip()
        for call in _field(message, "tool_calls", None) or []:
            fn = _field(call, "function", {})
            name = _field(fn, "name", "")
            args = _field(fn, "arguments", {}) or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"text": args}
            if name == "speak":
                spoken = args.get("text") or args.get("line") or ""
                if spoken:
                    return str(spoken).strip()
        return ""


_brain: Brain | None = None


def get_brain() -> Brain:
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain


def ask_banshee(message: str) -> str:
    """Thin wrapper matching the original snippet."""
    return get_brain().chat(message)


if __name__ == "__main__":
    print(ask_banshee("Who are you?"))
