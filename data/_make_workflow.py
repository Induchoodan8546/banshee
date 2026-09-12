"""Draw assets/ui/workflow.png for the README diagrams section."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "assets" / "ui" / "workflow.png"

W, H = 1600, 780
PURPLE = (61, 36, 99)
LILAC = (123, 94, 167)
CREAM = (247, 240, 252)
INK = (28, 18, 42)
WHITE = (255, 255, 255)
CARD = (255, 252, 255)
ROW = (239, 230, 248)
ACCENT = (92, 58, 140)


def font(size, bold=False, italic=False):
    name = "segoeuib.ttf" if bold else ("segoeuii.ttf" if italic else "segoeui.ttf")
    try:
        return ImageFont.truetype(rf"C:\Windows\Fonts\{name}", size)
    except OSError:
        return ImageFont.load_default()


F_TITLE = font(34, bold=True)
F_SUB = font(16, italic=True)
F_H = font(15, bold=True)
F_STEP = font(18, bold=True)
F_BODY = font(14)
F_SMALL = font(13)
F_NUM = font(16, bold=True)
F_CAP = font(13, italic=True)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def shadow_round(draw, box, r=18):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 5, y0 + 6, x1 + 5, y1 + 6), radius=r, fill=(210, 198, 224))
    draw.rounded_rectangle(box, radius=r, fill=CARD, outline=PURPLE, width=2)


def arrow_right(draw, x0, y, x1):
    draw.line((x0, y, x1 - 12, y), fill=LILAC, width=4)
    draw.polygon([(x1, y), (x1 - 16, y - 8), (x1 - 16, y + 8)], fill=PURPLE)


def arrow_down(draw, x, y0, y1):
    draw.line((x, y0, x, y1 - 12), fill=LILAC, width=3)
    draw.polygon([(x, y1), (x - 7, y1 - 14), (x + 7, y1 - 14)], fill=PURPLE)


def numbered_card(draw, box, n, title, lines):
    shadow_round(draw, box, r=18)
    x0, y0, x1, y1 = box
    cx, cy = x0 + 28, y0 + 28
    draw.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=PURPLE)
    tw = draw.textlength(str(n), font=F_NUM)
    draw.text((cx - tw / 2, cy - 11), str(n), font=F_NUM, fill=WHITE)
    draw.text((x0 + 52, y0 + 16), title, font=F_STEP, fill=PURPLE)
    y = y0 + 52
    for line in lines:
        for wrapped in wrap(draw, line, F_BODY, x1 - x0 - 28):
            draw.text((x0 + 18, y), wrapped, font=F_BODY, fill=INK)
            y += 20


def mini_card(draw, box, title, body):
    shadow_round(draw, box, r=14)
    x0, y0, x1, _ = box
    draw.rounded_rectangle((x0, y0, x1, y0 + 34), radius=14, fill=PURPLE)
    draw.rectangle((x0, y0 + 18, x1, y0 + 34), fill=PURPLE)
    draw.text((x0 + 14, y0 + 8), title, font=F_H, fill=WHITE)
    y = y0 + 46
    for line in body:
        for wrapped in wrap(draw, line, F_SMALL, x1 - x0 - 24):
            draw.text((x0 + 14, y), wrapped, font=F_SMALL, fill=INK)
            y += 18


def build():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, W, 88), fill=PURPLE)
    draw.text((48, 18), "BANSHEE  ·  session workflow", font=F_TITLE, fill=WHITE)
    draw.text(
        (48, 58),
        "One bedroom. Local Ollama. Then the real desktop. Off switch: bazinga.",
        font=F_SUB,
        fill=(220, 208, 236),
    )

    draw.text((48, 108), "How a session runs", font=F_H, fill=ACCENT)

    cards = 5
    gap = 36
    left, right = 40, W - 40
    usable = right - left
    cw = (usable - gap * (cards - 1)) / cards
    ch = 210
    y0 = 138
    titles = [
        "Boot",
        "Act I  ·  Bedroom",
        "Close the window",
        "Act II  ·  Desktop",
        "Banish",
    ]
    bodies = [
        [
            "python main.py  (or run.bat)",
            "Ollama must be running locally — no cloud.",
            "--chat skips the pictures.",
        ],
        [
            "One pygame room. Poke furniture.",
            "The blob lands, wanders, talks.",
            "Every spoken line is llama3.2:3b.",
        ],
        [
            "Closing is consent, not an exorcism.",
            "--house-only: just quit here.",
            "Otherwise possession starts.",
        ],
        [
            "Mascot walks the real desktop.",
            "Chat box stays bottom-right.",
            "Notepad, Paint, Calc, searches.",
        ],
        [
            "Type bazinga in the chat box.",
            "Wallpaper is restored.",
            "Process exits. She is gone.",
        ],
    ]
    boxes = []
    for i in range(cards):
        x = left + i * (cw + gap)
        box = (x, y0, x + cw, y0 + ch)
        boxes.append(box)
        numbered_card(draw, box, i + 1, titles[i], bodies[i])
        if i < cards - 1:
            ax0 = x + cw + 4
            ax1 = x + cw + gap - 4
            arrow_right(draw, ax0, y0 + ch / 2, ax1)

    # flag callouts under steps 1, 3, 4
    note_y = y0 + ch + 16
    notes = [
        (boxes[0], "--chat  terminal ghost only"),
        (boxes[2], "--house-only  never leaves the room"),
        (boxes[3], "--safe  logs “would …” — no real Win32"),
    ]
    for box, text in notes:
        x0, _, x1, _ = box
        tw = draw.textlength(text, font=F_CAP)
        nx = (x0 + x1) / 2 - tw / 2
        draw.rounded_rectangle((nx - 10, note_y, nx + tw + 10, note_y + 26), radius=10, fill=ROW, outline=LILAC)
        draw.text((nx, note_y + 5), text, font=F_CAP, fill=PURPLE)

    # architecture
    ay = note_y + 54
    draw.text((48, ay), "How the pieces talk", font=F_H, fill=ACCENT)
    ay += 28
    cols = 4
    agap = 28
    aw = (usable - agap * (cols - 1)) / cols
    ah = 168
    arch = [
        ("You", ["Type or Speak in the chat box.", "Poke the wardrobe, chair, lamp, chest."]),
        ("UI", ["Act I: pygame bedroom + dock.", "Act II: tk mascot + always-on-top chat."]),
        ("Brain", ["banshee/brain.py → Ollama.", "llama3.2:3b on localhost:11434.", "Last 8 turns. No canned script."]),
        ("Haunt tools", ["possessor.py: wallpaper, cursor,", "notepad / mspaint / calc / Google.", "Playground folder only."]),
    ]
    arch_boxes = []
    for i, (title, body) in enumerate(arch):
        x = left + i * (aw + agap)
        box = (x, ay, x + aw, ay + ah)
        arch_boxes.append(box)
        mini_card(draw, box, title, body)
        if i < cols - 1:
            arrow_right(draw, x + aw + 4, ay + ah / 2, x + aw + agap - 4)

    # kill + safety strip
    by = ay + ah + 22
    draw.rounded_rectangle((left, by, right, H - 24), radius=16, fill=PURPLE)
    draw.text((left + 24, by + 14), "Off switch and rails", font=F_H, fill=WHITE)
    rails = (
        "Kill spell: type bazinga in the bottom-right box.   "
        "Never deletes files, never touches passwords, never disables Task Manager.   "
        "Writes only in %USERPROFILE%\\BansheePlayground\\."
    )
    y = by + 40
    for line in wrap(draw, rails, F_SMALL, usable - 40):
        draw.text((left + 24, y), line, font=F_SMALL, fill=(235, 226, 246))
        y += 20

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print("wrote", OUT)


if __name__ == "__main__":
    build()
