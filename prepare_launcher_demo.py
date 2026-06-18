# -*- coding: utf-8 -*-
"""Prepare launcher_demo.png for website."""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from pathlib import Path

for key in list(os.environ):
    if "proxy" in key.lower():
        os.environ.pop(key, None)
os.environ["NO_PROXY"] = "*"
urllib.request.getproxies = lambda: {}  # type: ignore[method-assign]

BASE = Path(__file__).resolve().parent
SRC = Path(
    r"C:\Users\artur\.cursor\projects\d-okeykalauch-OkeyRustLauncher\assets"
    r"\c__Users_artur_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_launcher_demo-91d01691-4b2b-489a-b279-2c48c936087e.png"
)
OUT_DIR = BASE / "website" / "assets"
OUT = OUT_DIR / "launcher_demo.png"


def ensure_pillow() -> None:
    try:
        import PIL  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "Pillow", "--no-cache-dir", "-i", "https://pypi.org/simple"]
        )


def make_sr_avatar(size: int):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 16)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=max(6, size // 7), fill=(8, 8, 12, 255), outline=(40, 24, 24, 255), width=2)
    font_size = max(14, size // 2)
    try:
        font = ImageFont.truetype("segoeui.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
    text = "SR"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 1), text, fill=(255, 45, 45, 255), font=font)
    return img


def draw_player_count(draw, box, text: str, font):
    from PIL import ImageDraw

    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(18, 18, 24, 255))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2 - 1), text, fill=(232, 232, 236, 255), font=font)


def main() -> None:
    ensure_pillow()
    from PIL import Image, ImageDraw, ImageFont

    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    draw = ImageDraw.Draw(im)

    # Relative layout tuned for launcher screenshot (995x649)
    avatar_size = int(h * 0.108)
    avatar_x = int(w * 0.298)
    server1_y = int(h * 0.288)
    server2_y = int(h * 0.438)
    dot_size = max(11, avatar_size // 5)

    sr = make_sr_avatar(avatar_size)
    for y in (server1_y, server2_y):
        cover = (avatar_x - 2, y - 2, avatar_x + avatar_size + 6, y + avatar_size + 8)
        draw.rounded_rectangle(cover, radius=10, fill=(14, 14, 20, 255))
        im.paste(sr, (avatar_x, y), sr)
        dot_x = avatar_x + avatar_size - dot_size + 2
        dot_y = y + avatar_size - dot_size + 2
        draw.ellipse((dot_x, dot_y, dot_x + dot_size, dot_y + dot_size), fill=(76, 175, 80, 255), outline=(18, 18, 24, 255), width=2)

    try:
        count_font = ImageFont.truetype("segoeui.ttf", max(17, int(h * 0.03)))
    except OSError:
        try:
            count_font = ImageFont.truetype("arial.ttf", max(17, int(h * 0.03)))
        except OSError:
            count_font = ImageFont.load_default()

    count_w = int(w * 0.09)
    count_h = int(h * 0.07)
    count_x = int(w * 0.735)
    for y in (int(h * 0.295), int(h * 0.445)):
        draw.rectangle((count_x, y, count_x + count_w, y + count_h), fill=(14, 14, 20, 255))
        bbox = draw.textbbox((0, 0), "999/999", font=count_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((count_x + (count_w - tw) / 2, y + (count_h - th) / 2 - 1), "999/999", fill=(232, 232, 236, 255), font=count_font)

    im.convert("RGB").save(OUT, format="PNG", optimize=True)
    print(f"Saved: {OUT} ({w}x{h})")


if __name__ == "__main__":
    main()
