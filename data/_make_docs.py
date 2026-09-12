"""Generate BANSHEE_Project_Documentation.pdf"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Image as RLImage,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = r"c:\Users\induc\uselessproject_3.0\banshee\BANSHEE_Project_Documentation.pdf"

PURPLE = colors.HexColor("#3d2463")
LILAC = colors.HexColor("#7b5ea7")
CREAM = colors.HexColor("#f7f0fc")
INK = colors.HexColor("#1c122a")
ROW = colors.HexColor("#efe6f8")


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("CoverTitle", fontName="Times-Bold", fontSize=28, textColor=PURPLE, alignment=TA_CENTER, spaceAfter=8, leading=34))
    s.add(ParagraphStyle("CoverSub", fontName="Times-Italic", fontSize=13, textColor=LILAC, alignment=TA_CENTER, spaceAfter=6, leading=18))
    s.add(ParagraphStyle("H1b", fontName="Times-Bold", fontSize=16, textColor=PURPLE, spaceBefore=16, spaceAfter=8, leading=20))
    s.add(ParagraphStyle("H2b", fontName="Times-Bold", fontSize=13, textColor=LILAC, spaceBefore=12, spaceAfter=6, leading=17))
    s.add(ParagraphStyle("BodyJ", fontName="Times-Roman", fontSize=10.5, textColor=INK, alignment=TA_JUSTIFY, leading=15, spaceAfter=8))
    s.add(ParagraphStyle("BodyL", fontName="Times-Roman", fontSize=10.5, textColor=INK, alignment=TA_LEFT, leading=15, spaceAfter=6))
    s.add(ParagraphStyle("Cell", fontName="Times-Roman", fontSize=9, textColor=INK, leading=12))
    s.add(ParagraphStyle("CellB", fontName="Times-Bold", fontSize=9, textColor=PURPLE, leading=12))
    s.add(ParagraphStyle("CellW", fontName="Times-Bold", fontSize=9, textColor=colors.white, leading=12))
    s.add(ParagraphStyle("Caption", fontName="Times-Italic", fontSize=9, textColor=LILAC, alignment=TA_CENTER, spaceAfter=10))
    s.add(ParagraphStyle("Footer", fontName="Times-Italic", fontSize=8, textColor=LILAC, alignment=TA_CENTER))
    s.add(ParagraphStyle("BulletBody", fontName="Times-Roman", fontSize=10.5, textColor=INK, leading=14, leftIndent=8))
    return s


def P(text, st):
    return Paragraph(text, st)


def shot(path, st, caption, max_w):
    from PIL import Image as PILImage

    im = PILImage.open(path)
    iw, ih = im.size
    nw = float(max_w)
    nh = nw * ih / iw
    cap = 3.4 * inch
    if nh > cap:
        nh = cap
        nw = nh * iw / ih
    return [
        RLImage(path, width=nw, height=nh, hAlign="CENTER"),
        P(caption, st["Caption"]),
        Spacer(1, 6),
    ]


def bullets(items, st):
    return ListFlowable(
        [ListItem(Paragraph(i, st), leftIndent=12, bulletColor=PURPLE) for i in items],
        bulletType="bullet",
        leftIndent=18,
        bulletFontSize=9,
        spaceAfter=8,
    )


def table(headers, rows, col_w, st):
    head = [P(h, st["CellW"]) for h in headers]
    body = [[P(c, st["Cell"]) for c in r] for r in rows]
    t = Table([head] + body, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), CREAM),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CREAM, ROW]),
        ("GRID", (0, 0), (-1, -1), 0.4, LILAC),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(PURPLE)
    canvas.rect(0, h - 14, w, 14, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Italic", 8)
    canvas.drawString(18 * mm, h - 10, "BANSHEE  ·  Project Documentation")
    canvas.drawRightString(w - 18 * mm, h - 10, "Useless Projects  ·  TinkerHub")
    canvas.setFillColor(PURPLE)
    canvas.rect(0, 0, w, 16, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Roman", 8)
    canvas.drawCentredString(w / 2, 6, f"kill spell: bazinga     ·     page {doc.page}")
    canvas.restoreState()


def build():
    st = styles()
    story = []
    W = A4[0] - 36 * mm

    story += [
        Spacer(1, 40 * mm),
        P("BANSHEE", st["CoverTitle"]),
        P("A cartoon poltergeist that starts in a drawing<br/>and then sits on your real Windows desktop.", st["CoverSub"]),
        Spacer(1, 8),
        P("Detailed project documentation", st["CoverSub"]),
        Spacer(1, 16),
        P("Author: Induchoodan VS", st["BodyL"]),
        P("Event: TinkerHub Useless Projects", st["BodyL"]),
        P("Platform: Windows  ·  Language: Python 3.11  ·  Brain: local Ollama (llama3.2:3b)", st["BodyL"]),
        P("Off switch: type <b>bazinga</b> in the chat box.", st["BodyL"]),
        PageBreak(),
    ]

    story += [
        P("1. What is this project?", st["H1b"]),
        P(
            "BANSHEE is a joke desktop ghost. She is a white pixel blob with two square eyes. "
            "She begins inside <b>one cartoon bedroom</b> drawn like a notebook game. You poke the furniture. "
            "Shadows slide behind the wardrobe. Then she fades in, talks, and wanders the room.",
            st["BodyJ"],
        ),
        P(
            "Closing that bedroom window is not an exorcism. It is an invitation. After you close it, she "
            "<b>possesses the real Windows desktop</b>: a mascot walks over your screens, a small chat box "
            "stays in the bottom-right corner, she comments on whatever window is in front, and she opens "
            "harmless apps (Notepad, Paint, Calculator, browser searches). The only way to send her away "
            "is the word <b>bazinga</b>.",
            st["BodyJ"],
        ),
        P(
            "Nothing she does is real malware. She never deletes files, never touches passwords, never "
            "disables Task Manager, and never writes outside a folder called BansheePlayground in your user profile.",
            st["BodyJ"],
        ),
        P("2. How it feels to play (the loop)", st["H1b"]),
        bullets([
            "<b>Boot.</b> Python starts. Ollama must be running on this laptop (no ChatGPT cloud).",
            "<b>Act I — the room.</b> Empty bedroom, chair rocks, whispers, a shadow on the wall, then she lands.",
            "<b>Talk.</b> You type in the dock. Every spoken line after she appears comes from llama3.2:3b.",
            "<b>Audio (optional).</b> Click Audio. The same text is also spoken in a pitched-up neural goblin voice.",
            "<b>Close the window.</b> That starts possession. --house-only skips this and just quits.",
            "<b>Act II — the desktop.</b> Blob wanders, chat box stays on top, apps and searches ramp up over ~90 seconds.",
            "<b>Banish.</b> Type bazinga in the box. Wallpaper is restored. Process exits.",
        ], st["BulletBody"]),
        P("Screenshots from the build", st["H1b"]),
        *shot(
            r"c:\Users\induc\uselessproject_3.0\banshee\assets\ghost\Screenshot 2026-09-12 091758.png",
            st,
            "Possession running: the terminal logs Paint scribble, cursor haunt, Calculator, and a unique Google search.",
            W,
        ),
        *shot(
            r"c:\Users\induc\uselessproject_3.0\banshee\assets\ghost\Screenshot 2026-09-12 092024.png",
            st,
            "The local brain in brain.py: Ollama client, config imports, and the BANSHEE system prompt.",
            W,
        ),
        *shot(
            r"c:\Users\induc\uselessproject_3.0\banshee\assets\ghost\Screenshot 2026-09-12 092414.png",
            st,
            "Screenshot 3 — Act I: the pixel bedroom. The blob floats by the night window.",
            W,
        ),
        *shot(
            r"c:\Users\induc\uselessproject_3.0\banshee\assets\ghost\Screenshot 2026-09-12 092427.png",
            st,
            "Screenshot 4 — Act II: she scribbles in Paint, talks in a bubble, chat box stays bottom-right.",
            W,
        ),
        P("Project demo video", st["H2b"]),
        P(
            "A full playthrough is in the repo at <b>assets/ghost/banshee.mp4</b>. "
            "It shows the bedroom haunt and the desktop possession (mascot, chat, Paint, apps).",
            st["BodyJ"],
        ),
        P("3. How the program is structured (simple picture)", st["H1b"]),
        P(
            "Think of three layers. <b>main.py</b> is the front door. It reads flags (--house-only, --safe, --chat) "
            "and either opens the pygame bedroom or, after that window closes, starts the desktop haunt. "
            "The <b>brain</b> is a small HTTP client to Ollama on localhost:11434. The <b>room</b> package draws Act I. "
            "The <b>desktop</b> package draws Act II. The <b>system</b> package holds the kill switch.",
            st["BodyJ"],
        ),
        table(
            ["Piece", "Job in one sentence"],
            [
                ["main.py", "Parse flags, run the room, then optionally start possession."],
                ["banshee/brain.py", "Talk to Ollama. Keep last 8 turns. Never use a canned joke script as the brain."],
                ["banshee/room/", "The one pygame bedroom: furniture, shadows, blob, bubbles, chat dock."],
                ["banshee/actors/", "Motion quality: easing, breathing, blink, scare. Not the scene clock."],
                ["banshee/desktop/", "Mascot, chat box, wallpaper, apps, searches, cursor, Paint scribble."],
                ["banshee/system/", "Global bazinga listener (pynput) plus an unused watcher stub."],
                ["banshee/voice_io.py", "Text/audio toggle. edge-tts goblin voice. Mic → speech-to-text."],
                ["assets/", "Pixel art: room, ghost layers, shadows. Ghost and shadows never share a sheet."],
            ],
            [1.6 * inch, W - 1.6 * inch],
            st,
        ),
        P("4. Tech stack — what each tool is for", st["H1b"]),
        P("4.1 Languages and runtimes", st["H2b"]),
        table(
            ["Stack", "How it is implemented"],
            [
                ["Python 3.11", "The whole project is Python. Run from .venv. Entry point is main.py."],
                ["Ollama + llama3.2:3b", "Local LLM at http://127.0.0.1:11434. POST /api/chat via the official ollama Python package. If RAM is tight, config can fall back to phi3:mini. If Ollama is down the UI says “wake the spirit” and waits — it does not switch to a joke script."],
                ["Windows", "Desktop haunt uses ctypes (cursor, wallpaper, window titles) and subprocess to launch allowlisted apps only."],
            ],
            [1.5 * inch, W - 1.5 * inch],
            st,
        ),
        P("4.2 Libraries (from requirements.txt)", st["H2b"]),
        table(
            ["Library", "Where it is used"],
            [
                ["pygame", "Act I bedroom: 1072×596 pixel room + a chat dock under it. 60 FPS. Sprite blit, click hit-tests, drag furniture."],
                ["tkinter", "Act II: hidden Tk root, always-on-top chat Toplevel (bottom-right), always-on-top mascot Toplevel (the walking blob). Built into Python on Windows."],
                ["Pillow (PIL)", "Load/resize ghost PNGs for the mascot; pack/key assets; Paint is no longer a pre-drawn ellipse — drawing is done with the real cursor."],
                ["pynput", "Global keyboard hook for bazinga; mouse controller to scribble in Paint; optional activity watch."],
                ["edge-tts", "Neural Microsoft voice (en-US-GuyNeural) pitched up into a chattering goblin. Plays through pygame.mixer. Needs internet the first time."],
                ["SpeechRecognition + PyAudio", "Speak button: microphone → text, then the same path as typing."],
                ["pyttsx3", "Offline SAPI fallback if edge-tts is missing."],
            ],
            [1.7 * inch, W - 1.7 * inch],
            st,
        ),
        P("4.3 How the local brain is wired", st["H2b"]),
        P(
            "banshee/brain.py holds the character SYSTEM_PROMPT (smug cartoon ghost, 1–3 short sentences, never admits it is an AI). "
            "Brain.chat() builds [system + last 8 turns + latest activity + user]. Timeout 12 seconds, retry once, then “the wall is buffering”. "
            "Player chat is marked as_human so her memory is the real conversation. Ambient mutters (window-title roasts) are not stored, so they cannot drown “who are you?”. "
            "Desktop tools (cursor, wallpaper, apps) are legal in the tool list but the live haunt mostly calls Python functions on a timer rather than waiting for the model to pick every app.",
            st["BodyJ"],
        ),
        P("5. Act I — the bedroom (pygame)", st["H1b"]),
        P(
            "scene.py opens the window, loads bg.png, and runs a director. First you only feel a presence (whispers, lamp, chest). "
            "Then shadows (wall-slide, under furniture, door crack, false ghost). Then she manifests with a landing squash — she does not teleport. "
            "After that a director picks actions: drift, hide in an open wardrobe, peek, scare, mutter via Ollama. "
            "You can open the wardrobe, drag the chair/stool, toggle the lamp, open the chest. Three prop clicks before she appears skip ahead to the landing.",
            st["BodyJ"],
        ),
        P(
            "Draw order (layers.py): background → shadows → furniture → lagging ground shadow → ghost → speech bubble → chat dock. "
            "The ground oval lags the body by ~100 ms so she feels off the floor. Breathing is whole-pixel squash, not a blurry scale.",
            st["BodyJ"],
        ),
        P("6. Act II — desktop possession", st["H1b"]),
        P(
            "If you did not pass --house-only, closing the pygame window returns “possess”. haunt_loop.py then: writes DO_NOT_READ.txt, opens Notepad on that file, "
            "changes wallpaper (original path saved in data/wallpaper.json), starts a mischief thread, and runs the tk overlay (chat + mascot).",
            st["BodyJ"],
        ),
        bullets([
            "<b>Mascot (mascot.py).</b> A small transparent Toplevel. Click-through so you can use apps underneath. Slow random wander across the virtual desktop. Speech bubble drawn on the same canvas. Almost still while a bubble is up so you can read it.",
            "<b>Chat box (overlay.py).</b> Separate always-on-top window, bottom-right, small. Type to talk. Buttons: text / audio / speak. bazinga here banishes. Possession is not allowed to steal this box: a safe zone around it pauses the cursor haunt.",
            "<b>Mischief (haunt_loop.py).</b> Round-robin: notepad, Google search, Paint scribble, calculator, cursor yank, WordPad skip if missing, character map, more searches. Gaps start ~2s and get shorter over 90 seconds. After 15s the cursor is locked except over the chat box. If you close a haunted app, she opens it again (window-title check, because Windows 11 Calculator is not always calc.exe).",
            "<b>Paint.</b> She launches mspaint, waits for the window, maximises it, clicks the canvas (below the ribbon), and drag-scribbles with pynput — not a pre-drawn circle.",
            "<b>Browser.</b> Each search is a new query. If Ollama is free she invents one from your front window title; otherwise a unused fallback string. URL is https://www.google.com/search?q=…",
            "<b>Dare her.</b> If you type “you can’t open a browser” or “stop the cursor”, defy() does that thing anyway.",
        ], st["BulletBody"]),
        P("7. Safety rails", st["H1b"]),
        table(
            ["Rule", "How it is enforced"],
            [
                ["Playground only", "Notes and doodles go to %USERPROFILE%\\BansheePlayground\\"],
                ["App allowlist", "notepad, calc, mspaint, write (skipped if missing), charmap. Missing exes are skipped, not crashed."],
                ["--safe", "possessor methods log “would …” and do not call Win32."],
                ["--house-only", "Closing the room just quits. No desktop."],
                ["Wallpaper restore", "Path saved before change; bazinga / exit restores it."],
                ["Never", "No file deletes, no passwords, no Task Manager disable, no Windows service."],
            ],
            [1.6 * inch, W - 1.6 * inch],
            st,
        ),
        P("8. File-by-file guide", st["H1b"]),
        P("8.1 Root", st["H2b"]),
        table(
            ["File", "What it does"],
            [
                ["main.py", "argparse: --chat, --safe, --house-only. Default: run_house then maybe run_possession."],
                ["requirements.txt", "ollama, pygame, pillow, pynput, pyttsx3, SpeechRecognition, PyAudio, edge-tts."],
                ["run.bat / run-safe.bat", "Launch with the venv Python if present."],
                ["README.md", "TinkerHub Useless Projects template, filled for a solo build."],
            ],
            [1.8 * inch, W - 1.8 * inch],
            st,
        ),
        P("8.2 Package banshee/", st["H2b"]),
        table(
            ["File", "What it does"],
            [
                ["config.py", "Paths, Ollama host, model names, kill spell, window sizes, allowlists, search URL list, --safe / --house-only flags."],
                ["state.py", "Haunt enum (ROOM / MANIFEST / POSSESS / SYSTEM / BANISHED) and a clock."],
                ["brain.py", "SYSTEM_PROMPT, Ollama client, 12s timeout, retry, last-8 memory, as_human vs ambient."],
                ["voice_io.py", "audio_mode toggle. finish() speaks a full line with edge-tts. Speak button = listen_once()."],
            ],
            [1.5 * inch, W - 1.5 * inch],
            st,
        ),
        P("8.3 banshee/room/", st["H2b"]),
        table(
            ["File", "What it does"],
            [
                ["scene.py", "Pygame loop, input, director tick, bubble + dock, return quit vs possess."],
                ["director.py", "Acts UNEASE → SHADOWS → APPEAR → HAUNT. First LLM line. Restless idle drift."],
                ["props.py", "Hotspots, open wardrobe, drag chair, chest lid, lamp, occlusion_map.json."],
                ["layers.py", "Draw order including hide-behind-furniture."],
                ["whispers.py", "Scripted caption lines before she appears (not the LLM)."],
                ["bubbles.py", "Speech bubble wrap + beat-by-beat long replies."],
                ["chat.py", "Pygame dock: log, input, text/audio/speak buttons."],
                ["voice.py", "Threaded Ollama: player chat jumps the queue; ambient does not block it."],
            ],
            [1.4 * inch, W - 1.4 * inch],
            st,
        ),
        P("8.4 banshee/actors/", st["H2b"]),
        table(
            ["File", "What it does"],
            [
                ["motion.py", "ease-in-out, lag-shadow (80–120 ms), whole-pixel breathe."],
                ["ghost.py", "States: ABSENT, MANIFEST, IDLE, DRIFT, HIDE, PEEK, SCARE, TALK. Talking does not freeze a drift. Desktop bounds via set_world()."],
                ["shade.py", "One shadow at a time: WALL_SLIDE, UNDER_FURNITURE, DOOR_CRACK, FALSE_GHOST."],
            ],
            [1.4 * inch, W - 1.4 * inch],
            st,
        ),
        P("8.5 banshee/desktop/", st["H2b"]),
        table(
            ["File", "What it does"],
            [
                ["haunt_loop.py", "Possession entry: note, notepad, wallpaper, mischief thread, overlay.run()."],
                ["overlay.py", "Hidden Tk root + chat Toplevel + mascot. Polls Ollama, pins chat on top, bazinga, audio buttons."],
                ["mascot.py", "Transparent click-through blob. Random slow wander. Bubble on the same window."],
                ["possessor.py", "Cursor grab/lock, wallpaper, allowlisted apps, Paint scribble, unique Google searches, reopen-if-closed, defy()."],
                ["monitor.py", "GetForegroundWindow title for roasts and search hints."],
                ["wander.py", "Older pygame desktop-pet path; live haunt uses tk mascot instead."],
            ],
            [1.5 * inch, W - 1.5 * inch],
            st,
        ),
        P("8.6 banshee/system/", st["H2b"]),
        table(
            ["File", "What it does"],
            [
                ["banisher.py", "pynput listener, rolling 7 letters, match bazinga (also typed in the chat box)."],
                ["watcher.py", "Stub for optional relaunch. Not used in the live demo."],
            ],
            [1.5 * inch, W - 1.5 * inch],
            st,
        ),
        P("8.7 assets/", st["H2b"]),
        table(
            ["Folder", "Contents"],
            [
                ["assets/room/", "bg.png (empty bedroom), isolated props, wardrobe_open.png, occlusion_map.json, reference art."],
                ["assets/ghost/", "body, eyes_closed, mouth_talk, peek, ground_shadow. Cute blob only."],
                ["assets/shadows/", "wall_slide, crawl, door_crack, false_ghost. Dark figures, no smile."],
                ["assets/ui/", "wallpaper.png used when she possesses the desktop."],
                ["data/", "wallpaper.json (saved original), banished.flag."],
            ],
            [1.6 * inch, W - 1.6 * inch],
            st,
        ),
        P("9. How to run", st["H1b"]),
        P(
            "Need: Windows, Python 3.11, Ollama with <b>llama3.2:3b</b> pulled, a microphone only if you use Speak. "
            "Install: <font face='Courier'>pip install -r requirements.txt</font>. "
            "Full haunt: <font face='Courier'>python main.py</font> or run.bat. "
            "Room only: <font face='Courier'>python main.py --house-only</font>. "
            "No real desktop changes: <font face='Courier'>python main.py --safe</font>. "
            "Terminal ghost only: <font face='Courier'>python main.py --chat</font>.",
            st["BodyJ"],
        ),
        P("10. What we deliberately did not build", st["H1b"]),
        bullets([
            "A second room or hallway.",
            "Cloud LLMs (OpenAI, Gemini, Groq).",
            "Deleting files, stealing passwords, or blocking Task Manager.",
            "A Windows service or real persistence after bazinga.",
        ], st["BulletBody"]),
        Spacer(1, 16),
        P("Closing the window is consent. The only spell is bazinga.", st["Caption"]),
    ]

    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title="BANSHEE — Project Documentation",
        author="Induchoodan VS",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
