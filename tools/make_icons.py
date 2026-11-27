#!/usr/bin/env python3
"""App icons: a gold microphone on the charcoal stage.   python3 tools/make_icons.py

docs/icon-192.png, docs/icon-512.png  full-bleed squares, art inside the maskable safe zone
docs/icon-mono.png                    white mic on transparent ("monochrome" purpose)
docs/badge-96.png                     small white mic for Android notification badges (alpha only)
Drawn at 4x and scaled down for smooth lines. Needs Pillow."""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
GOLD = (245, 197, 66, 255)
WHITE = (255, 255, 255, 255)


def stage(size):
    img = Image.new("RGBA", (size, size))
    top, bot = (29, 18, 24), (42, 21, 32)
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
        for x in range(size):
            px[x, y] = c
    return img


def mic(d, cx, cy, h, w, col):
    """Capsule, cradle and stand, all inside the maskable safe zone."""
    lw = max(2, int(h * 0.055))
    rx = w / 2
    top = cy - h * 0.42
    bottom = cy + h * 0.12
    d.rounded_rectangle([cx - rx, top, cx + rx, bottom], radius=rx, outline=col, width=lw)
    arc_r = w * 0.92
    d.arc([cx - arc_r, cy - h * 0.15, cx + arc_r, cy + h * 0.36], 0, 180, fill=col, width=lw)
    d.line([(cx, cy + h * 0.36), (cx, cy + h * 0.47)], fill=col, width=lw)
    d.line([(cx - w * 0.55, cy + h * 0.47), (cx + w * 0.55, cy + h * 0.47)], fill=col, width=lw)


def art(size, col, background=True):
    K = 4
    S = size * K
    img = stage(S) if background else Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mic(ImageDraw.Draw(img), S / 2, S / 2, S * 0.62, S * 0.30, col)
    return img.resize((size, size), Image.LANCZOS)


def app_icon(size):
    return art(size, GOLD)


def mono(size):
    return art(size, WHITE, background=False)


if __name__ == "__main__":
    for n in (192, 512):
        app_icon(n).save(os.path.join(OUT, "icon-%d.png" % n), optimize=True)
    mono(512).save(os.path.join(OUT, "icon-mono.png"), optimize=True)
    mono(96).save(os.path.join(OUT, "badge-96.png"), optimize=True)
    print("icons written to", os.path.abspath(OUT))
