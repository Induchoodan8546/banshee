"""Blob TTS + user mic. Speaks as the text streams in, like a person."""

from __future__ import annotations

import queue
import threading
import xml.sax.saxutils as xml

audio_mode = False
_listening = False
_q: queue.Queue[tuple[str, str] | None] = queue.Queue()
_worker_started = False
_lock = threading.Lock()

_SVS_ASYNC = 1
_SVS_PURGE = 2
_SVS_ISXML = 8


def set_audio_mode(on: bool) -> None:
    global audio_mode
    audio_mode = bool(on)


def maybe_speak(text: str) -> None:
    """Finish the current line (room/desktop final text)."""
    if audio_mode:
        finish(text)


def feed(partial: str) -> None:
    """Speak new complete words as the bubble fills."""
    if audio_mode:
        _put("feed", partial)


def finish(text: str) -> None:
    if audio_mode:
        _put("finish", text)


def speak(text: str) -> None:
    finish(text)


def _put(kind: str, text: str) -> None:
    text = (text or "").replace("\n", " ").strip()
    if not text or text == "...":
        return
    _ensure_worker()
    _q.put((kind, text))


def _ensure_worker() -> None:
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True
        threading.Thread(target=_speaker_loop, daemon=True).start()


def _speaker_loop() -> None:
    sapi = None
    try:
        import win32com.client

        sapi = win32com.client.Dispatch("SAPI.SpVoice")
        # 0 = normal person pace; a little lively, not rushed
        sapi.Rate = 0
        sapi.Volume = 100
    except Exception as exc:
        print(f"[banshee] tts init failed: {exc}", flush=True)
        return

    spoken = ""

    def _say(chunk: str, purge: bool) -> None:
        if not chunk.strip():
            return
        # Higher pitch, normal English — chattering goblin, not a robot.
        payload = "<pitch absmiddle='7'>" + xml.escape(chunk) + "</pitch>"
        flags = _SVS_ASYNC | _SVS_ISXML
        if purge:
            flags |= _SVS_PURGE
        sapi.Speak(payload, flags)

    while True:
        item = _q.get()
        if item is None:
            break
        kind, text = item
        try:
            if kind == "feed":
                if spoken and not text.startswith(spoken):
                    spoken = ""
                rest = text[len(spoken) :] if text.startswith(spoken) else text
                if not rest:
                    continue
                if rest[-1].isspace() or rest[-1] in ".!?,;:":
                    chunk = rest
                elif " " in rest:
                    chunk = rest.rsplit(" ", 1)[0] + " "
                else:
                    continue
                _say(chunk, purge=not spoken)
                spoken += chunk
            elif kind == "finish":
                if spoken and text.startswith(spoken):
                    rest = text[len(spoken) :]
                    purge = False
                else:
                    rest = text
                    purge = True
                _say(rest, purge=purge)
                spoken = ""
        except Exception as exc:
            print(f"[banshee] tts failed: {exc}", flush=True)
            spoken = ""


def listen_once() -> str:
    global _listening
    if _listening:
        return ""
    _listening = True
    try:
        import speech_recognition as sr
    except ImportError:
        _listening = False
        return ""
    recog = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recog.adjust_for_ambient_noise(source, duration=0.25)
            audio = recog.listen(source, timeout=5, phrase_time_limit=6)
        try:
            return (recog.recognize_google(audio) or "").strip()
        except Exception:
            try:
                return (recog.recognize_sphinx(audio) or "").strip()
            except Exception:
                return ""
    except Exception:
        return ""
    finally:
        _listening = False


def is_listening() -> bool:
    return _listening
