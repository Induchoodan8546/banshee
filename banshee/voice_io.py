"""Blob TTS + user mic. Windows SAPI is re-created per line so it keeps speaking."""

from __future__ import annotations

import queue
import threading
import time

audio_mode = False
_listening = False
_q: queue.Queue[str | None] = queue.Queue()
_worker_started = False
_lock = threading.Lock()
_last_spoken = ""
_last_t = 0.0


def set_audio_mode(on: bool) -> None:
    global audio_mode
    audio_mode = bool(on)


def maybe_speak(text: str) -> None:
    if audio_mode:
        speak(text)


def speak(text: str) -> None:
    global _last_spoken, _last_t
    text = (text or "").replace("\n", " ").strip()
    if not text or text == "...":
        return
    now = time.monotonic()
    if text == _last_spoken and now - _last_t < 1.8:
        return
    _last_spoken = text
    _last_t = now
    _ensure_worker()
    _q.put(text)


def _ensure_worker() -> None:
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True
        threading.Thread(target=_speaker_loop, daemon=True).start()


def _speak_one(text: str) -> None:
    # Fresh engine every line — reuse dies after the first utterance on Windows.
    try:
        import win32com.client

        voice = win32com.client.Dispatch("SAPI.SpVoice")
        voice.Rate = -4
        voice.Volume = 100
        voice.Speak(text)
        return
    except Exception:
        pass
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 100)
        engine.setProperty("volume", 1.0)
        try:
            for v in engine.getProperty("voices") or []:
                name = (getattr(v, "name", "") or "").lower()
                if any(s in name for s in ("david", "mark", "male", "george", "james", "zira")):
                    engine.setProperty("voice", v.id)
                    break
        except Exception:
            pass
        engine.say(text)
        engine.runAndWait()
        try:
            engine.stop()
        except Exception:
            pass
        del engine
    except Exception as exc:
        print(f"[banshee] tts failed: {exc}", flush=True)


def _speaker_loop() -> None:
    while True:
        text = _q.get()
        if text is None:
            break
        try:
            _speak_one(text)
        except Exception as exc:
            print(f"[banshee] tts failed: {exc}", flush=True)


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
