"""Blob TTS + user mic. Text chat stays; audio is a mode on top."""

from __future__ import annotations

import queue
import threading
import xml.sax.saxutils as xml

audio_mode = False
_listening = False
_q: queue.Queue[str | None] = queue.Queue()
_worker_started = False
_lock = threading.Lock()


def set_audio_mode(on: bool) -> None:
    global audio_mode
    audio_mode = bool(on)


def maybe_speak(text: str) -> None:
    if audio_mode:
        speak(text)


def speak(text: str) -> None:
    text = (text or "").replace("\n", " ").strip()
    if not text:
        return
    _ensure_worker()
    _q.put(text)


def _ensure_worker() -> None:
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True
        threading.Thread(target=_speaker_loop, daemon=True).start()


def _speaker_loop() -> None:
    try:
        import pyttsx3
    except ImportError:
        print("[banshee] pyttsx3 missing — pip install pyttsx3", flush=True)
        return
    engine = pyttsx3.init()
    engine.setProperty("rate", 108)
    engine.setProperty("volume", 0.95)
    try:
        voices = engine.getProperty("voices") or []
        pick = None
        for v in voices:
            name = (getattr(v, "name", "") or "").lower()
            if any(s in name for s in ("david", "mark", "male", "george", "james")):
                pick = v.id
                break
        if pick:
            engine.setProperty("voice", pick)
    except Exception:
        pass
    while True:
        text = _q.get()
        if text is None:
            break
        payload = (
            '<pitch absmiddle="-8"><rate speed="-6">'
            + xml.escape(text)
            + "</rate></pitch>"
        )
        try:
            engine.say(payload)
            engine.runAndWait()
        except Exception:
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as exc:
                print(f"[banshee] tts failed: {exc}", flush=True)


def listen_once() -> str:
    """Record one phrase. Empty string on failure."""
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
            recog.adjust_for_ambient_noise(source, duration=0.35)
            audio = recog.listen(source, timeout=5, phrase_time_limit=7)
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
