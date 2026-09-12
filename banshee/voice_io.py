"""Neural goblin TTS (edge-tts) + mic. Speaks as sentences appear; skips backlog."""

from __future__ import annotations

import asyncio
import os
import queue
import re
import tempfile
import threading
import time

audio_mode = False
_listening = False
_q: queue.Queue[tuple[str, str] | None] = queue.Queue()
_worker_started = False
_lock = threading.Lock()

# Natural male English, pitched up — chattering goblin, still a real accent.
_VOICE = "en-US-GuyNeural"
_RATE = "+10%"
_PITCH = "+32Hz"


def set_audio_mode(on: bool) -> None:
    global audio_mode
    audio_mode = bool(on)


def maybe_speak(text: str) -> None:
    if audio_mode:
        finish(text)


def feed(partial: str) -> None:
    """Start speaking as soon as a sentence (or clause) is ready."""
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


def _clauses(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


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
        time.sleep(0.04)


def _speak_neural(text: str) -> None:
    text = text.strip()
    if not text:
        return
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        _gen_mp3(text, path)
        if not _q.empty():
            return
        _play_file(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _speak_sapi(text: str, voice) -> None:
    import xml.sax.saxutils as xml

    payload = "<pitch absmiddle='6'>" + xml.escape(text) + "</pitch>"
    voice.Speak(payload, 1 | 2 | 8)


def _speaker_loop() -> None:
    use_neural = True
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        use_neural = False
        print("[banshee] pip install edge-tts for the goblin voice", flush=True)

    sapi = None
    if not use_neural:
        try:
            import win32com.client

            sapi = win32com.client.Dispatch("SAPI.SpVoice")
            sapi.Rate = 2
            sapi.Volume = 100
        except Exception as exc:
            print(f"[banshee] tts init failed: {exc}", flush=True)
            return

    spoken = ""

    def _say(chunk: str) -> None:
        if use_neural:
            _speak_neural(chunk)
        elif sapi is not None:
            _speak_sapi(chunk, sapi)

    while True:
        item = _q.get()
        if item is None:
            break
        # stay on the newest line
        while True:
            try:
                nxt = _q.get_nowait()
            except queue.Empty:
                break
            if nxt is None:
                return
            item = nxt
        kind, text = item
        try:
            if kind == "feed":
                if spoken and not text.startswith(spoken):
                    spoken = ""
                rest = text[len(spoken) :] if text.startswith(spoken) else text
                # speak finished sentences as they appear
                done = []
                buf = ""
                for ch in rest:
                    buf += ch
                    if ch in ".!?":
                        done.append(buf.strip())
                        buf = ""
                for sent in done:
                    if sent:
                        _say(sent)
                        spoken += sent + " "
                continue
            if kind == "finish":
                if spoken and text.startswith(spoken.strip()):
                    rest = text[len(spoken.strip()) :].strip()
                else:
                    rest = text
                spoken = ""
                if rest:
                    _say(rest)
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
