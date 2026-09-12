"""Neural goblin TTS. Speaks each full line from the start — no leftover-only clips."""

from __future__ import annotations

import asyncio
import os
import queue
import tempfile
import threading
import time

audio_mode = False
_listening = False
_q: queue.Queue[str | None] = queue.Queue()
_worker_started = False
_lock = threading.Lock()

_VOICE = "en-US-GuyNeural"
_RATE = "+8%"
_PITCH = "+28Hz"


def set_audio_mode(on: bool) -> None:
    global audio_mode
    audio_mode = bool(on)


def maybe_speak(text: str) -> None:
    if audio_mode:
        finish(text)


def feed(_partial: str) -> None:
    """Streaming is too jumpy — we speak the full line when it finishes."""
    return


def finish(text: str) -> None:
    if not audio_mode:
        return
    text = (text or "").replace("\n", " ").strip()
    if not text or text == "...":
        return
    _ensure_worker()
    _q.put(text)


def speak(text: str) -> None:
    finish(text)


def _ensure_worker() -> None:
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True
        threading.Thread(target=_speaker_loop, daemon=True).start()


def _gen_mp3(text: str, path: str) -> None:
    import edge_tts

    async def _run() -> None:
        comm = edge_tts.Communicate(text, _VOICE, rate=_RATE, pitch=_PITCH)
        await comm.save(path)

    asyncio.run(_run())


def _mixer_ready() -> bool:
    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return True
    except Exception:
        return False


def _play_file(path: str) -> None:
    import pygame

    if not _mixer_ready():
        return
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        if not _q.empty():
            pygame.mixer.music.stop()
            break
        time.sleep(0.05)


def _speak_neural(text: str) -> None:
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        _gen_mp3(text, path)
        # newer line waiting — skip this clip, play the newest next
        if not _q.empty():
            return
        _play_file(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _speaker_loop() -> None:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("[banshee] pip install edge-tts", flush=True)
        return
    while True:
        text = _q.get()
        if text is None:
            break
        # keep only the newest full line
        while True:
            try:
                nxt = _q.get_nowait()
            except queue.Empty:
                break
            if nxt is None:
                return
            text = nxt
        try:
            _speak_neural(text)
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
