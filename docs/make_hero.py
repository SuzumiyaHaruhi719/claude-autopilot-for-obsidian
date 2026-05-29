#!/usr/bin/env python3
"""Render the README hero banner (docs/hero.png).

A wide title card: project name + tagline + OS line on the left, a glowing
Obsidian-style synapse cluster bleeding off the right edge — same neural look
as the animation, frozen into one frame.

    python docs/make_hero.py     # writes docs/hero.png

Dev-only. Needs Pillow + numpy.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, SS = 1280, 440, 2
RW, RH = W * SS, H * SS

BG_TOP = (10, 12, 22)
BG_BOT = (26, 18, 42)
VIOLET = (168, 85, 247)
HOT = (236, 232, 255)
CYAN = (34, 211, 238)
EDGE = (120, 70, 190)

HERE = Path(__file__).resolve().parent

# Decorative graph, clustered on the right, some nodes off-canvas for bleed.
NODES = [
    (0.72, 0.50, 17), (0.86, 0.30, 11), (0.93, 0.58, 12), (0.78, 0.78, 10),
    (0.62, 0.30, 9), (0.66, 0.72, 9), (1.00, 0.40, 10), (0.84, 0.52, 8),
    (0.97, 0.80, 9), (0.58, 0.55, 7), (0.90, 0.14, 8),
]
EDGES = [
    (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 6), (2, 6), (2, 8),
    (1, 10), (3, 5), (0, 7), (7, 2), (4, 9), (5, 9), (3, 8),
]


def _font(size, *names):
    for name in names + ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def scaled(color, k):
    return tuple(int(max(0, min(255, c * k))) for c in color)


def background():
    col = np.zeros((RH, RW, 3), np.float32)
    for c in range(3):
        col[:, :, c] = np.linspace(BG_TOP[c], BG_BOT[c], RH)[:, None]
    yy, xx = np.mgrid[0:RH, 0:RW]
    # glow bias toward the right cluster
    d = np.sqrt(((xx - RW * 0.8) / (RW * 0.7)) ** 2 + ((yy - RH / 2) / (RH * 0.8)) ** 2)
    col *= (1 - 0.4 * np.clip(d - 0.1, 0, 1))[:, :, None]
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB")


def render():
    base = background()
    glow = Image.new("RGB", (RW, RH), 0)
    gd = ImageDraw.Draw(glow)
    sharp = base.copy()
    sd = ImageDraw.Draw(sharp)

    def px(i):
        x, y, _ = NODES[i]
        return x * RW, y * RH

    for a, b in EDGES:
        ax, ay = px(a)
        bx, by = px(b)
        gd.line([(ax, ay), (bx, by)], fill=scaled(EDGE, 0.6), width=SS)
        sd.line([(ax, ay), (bx, by)], fill=scaled(EDGE, 0.75), width=1)
        # a couple of synapse pulses for life
        if (a + b) % 3 == 0:
            q = 0.4 + 0.2 * ((a + b) % 4)
            hx, hy = ax + (bx - ax) * q, ay + (by - ay) * q
            gd.ellipse([hx - 6 * SS, hy - 6 * SS, hx + 6 * SS, hy + 6 * SS], fill=CYAN)

    for i, (nx, ny, size) in enumerate(NODES):
        x, y, r = nx * RW, ny * RH, size * SS
        b = 0.8 + 0.2 * math.sin(i)
        gd.ellipse([x - r * 2.6, y - r * 2.6, x + r * 2.6, y + r * 2.6], fill=scaled(VIOLET, 0.45 * b))
        gd.ellipse([x - r, y - r, x + r, y + r], fill=scaled(VIOLET, b))
        sd.ellipse([x - r, y - r, x + r, y + r], fill=scaled(VIOLET, b))
        cr = r * 0.45
        sd.ellipse([x - cr, y - cr, x + cr, y + cr], fill=HOT)

    halo = glow.filter(ImageFilter.GaussianBlur(SS * 6))
    img = ImageChops.screen(sharp, halo)
    img = ImageChops.screen(img, glow.filter(ImageFilter.GaussianBlur(SS * 2)))

    # ---- left-hand text block ----
    d = ImageDraw.Draw(img)
    lx = 70 * SS
    # compass-ish accent mark
    d.ellipse([lx, 92 * SS, lx + 16 * SS, 108 * SS], outline=CYAN, width=SS)
    f_title = _font(int(58 * SS), "segoeuib.ttf", "arialbd.ttf")
    f_tag = _font(int(23 * SS))
    f_os = _font(int(18 * SS), "segoeuib.ttf", "arialbd.ttf")
    f_kick = _font(int(15 * SS), "segoeuib.ttf", "arialbd.ttf")

    d.text((lx + 26 * SS, 86 * SS), "CLAUDE CODE  ×  OBSIDIAN", font=f_kick, fill=(150, 120, 210))
    d.text((lx, 116 * SS), "Obsidian Autopilot", font=f_title, fill=(238, 232, 252))
    d.text((lx, 196 * SS),
           "Your vault, kept as the single source of", font=f_tag, fill=(176, 170, 200))
    d.text((lx, 226 * SS),
           "truth for your code — automatically.", font=f_tag, fill=(176, 170, 200))

    # violet underline accent
    d.rectangle([lx, 286 * SS, lx + 150 * SS, 289 * SS], fill=VIOLET)

    # OS line + badge
    d.text((lx, 306 * SS), "macOS   ·   Linux   ·   Windows",
           font=f_os, fill=(120, 200, 220))
    badge = "pure-Python  ·  zero-deps"
    bb = d.textbbox((0, 0), badge, font=f_kick)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    bx, by = lx, 344 * SS
    d.rounded_rectangle([bx, by, bx + bw + 24 * SS, by + bh + 16 * SS],
                        radius=10 * SS, outline=(120, 90, 170), width=SS)
    d.text((bx + 12 * SS, by + 7 * SS), badge, font=f_kick, fill=(190, 160, 230))

    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    out = HERE / "hero.png"
    render().save(out)
    print(f"hero -> {out}  ({out.stat().st_size // 1024} KB)")
