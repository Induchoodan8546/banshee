"""One-shot: chroma-key magenta, crop, scale, write game PNGs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SESSION = Path(
    r"C:\Users\induc\.grok\sessions"
    r"\c%3A%5CUsers%5Cinduc%5Cuselessproject_3.0%5Cbanshee"
    r"\01a09106-77c5-7d33-bbf8-6b956ca2b9d9\images"
)
ROOM = ROOT / "assets" / "room"
GHOST = ROOT / "assets" / "ghost"
SHADOWS = ROOT / "assets" / "shadows"
UI = ROOT / "assets" / "ui"

JOBS = [
    (SESSION / "7.jpg", ROOM / "bg.png", None, False),
    (SESSION / "1.jpg", GHOST / "body.png", 96, False),
    (SESSION / "11.jpg", GHOST / "eyes_closed.png", 96, False),
    (SESSION / "13.jpg", GHOST / "mouth_talk.png", 96, False),
    (SESSION / "12.jpg", GHOST / "peek.png", 72, True),
    (SESSION / "2.jpg", ROOM / "wardrobe.png", 300, False),
    (SESSION / "5.jpg", ROOM / "chair.png", 190, False),
    (SESSION / "6.jpg", ROOM / "chest.png", 110, False),
    (SESSION / "4.jpg", ROOM / "stool.png", 78, False),
    (SESSION / "3.jpg", ROOM / "lamp.png", 210, False),
    (SESSION / "8.jpg", SHADOWS / "wall_slide.png", 240, False),
    (SESSION / "9.jpg", SHADOWS / "crawl.png", 48, False),
    (SESSION / "14.jpg", SHADOWS / "false_ghost.png", 96, False),
    (SESSION / "10.jpg", SHADOWS / "door_crack.png", 110, False),
]


def key_magenta(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    corner = im.getpixel((2, 2))
    cr, cg, cb, _ = corner
    pix = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            dist = abs(r - cr) + abs(g - cg) + abs(b - cb)
            if dist < 90 or (r > 140 and b > 80 and g < 120 and r > g + 20):
                pix[x, y] = (0, 0, 0, 0)
    return im


def tight_crop(im: Image.Image) -> Image.Image:
    bbox = im.getbbox()
    if not bbox:
        return im
    pad = 2
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(im.width, x1 + pad)
    y1 = min(im.height, y1 + pad)
    return im.crop((x0, y0, x1, y1))


def scale_h(im: Image.Image, height: int) -> Image.Image:
    w, h = im.size
    if h <= 0:
        return im
    nw = max(1, round(w * (height / h)))
    return im.resize((nw, height), Image.Resampling.NEAREST)


def main() -> None:
    for src, dst, height, flip in JOBS:
        im = Image.open(src)
        if height is None:
            im.convert("RGB").save(dst)
            print("bg", dst, im.size)
            continue
        keyed = tight_crop(key_magenta(im))
        if flip:
            keyed = keyed.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        keyed = scale_h(keyed, height)
        dst.parent.mkdir(parents=True, exist_ok=True)
        keyed.save(dst)
        print(dst.name, keyed.size)

    shadow = Image.new("RGBA", (64, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.ellipse((2, 4, 62, 18), fill=(20, 10, 30, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(1.2))
    (GHOST / "ground_shadow.png").parent.mkdir(parents=True, exist_ok=True)
    shadow.save(GHOST / "ground_shadow.png")
    print("ground_shadow", shadow.size)


if __name__ == "__main__":
    main()
