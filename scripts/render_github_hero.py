#!/usr/bin/env python3
"""Render GitHub README hero assets for Sherlockdogs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets"
W, H = 1600, 900


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    candidates = {
        "bold": [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ],
        "regular": [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ],
    }
    for path in candidates[weight]:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F = {
    "hero": font(74, "bold"),
    "brand": font(34, "bold"),
    "h2": font(32, "bold"),
    "h3": font(24, "bold"),
    "body": font(25),
    "small": font(20),
    "tiny": font(17),
}


INK = "#151515"
MUTED = "#63625e"
YELLOW = "#f2b400"
YELLOW_DARK = "#d89400"
GREEN = "#19c45d"
PURPLE = "#7657e6"
BLUE = "#2576f2"
PAPER = "#fffdf8"
LINE = "#ddd8cd"


def rounded(draw: ImageDraw.ImageDraw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def text(draw, xy, value, fill=INK, font_key="body", anchor=None):
    draw.text(xy, value, fill=fill, font=F[font_key], anchor=anchor)


def pill(draw, xy, label, fill, fg=INK):
    x, y = xy
    bbox = draw.textbbox((0, 0), label, font=F["small"])
    tw = bbox[2] - bbox[0]
    rounded(draw, (x, y, x + tw + 36, y + 40), 20, fill=fill)
    text(draw, (x + 18, y + 9), label, fg, "small")
    return x + tw + 46


def arrow(draw, start, end, color=YELLOW, width=6):
    draw.line([start, end], fill=color, width=width)
    x2, y2 = end
    draw.polygon([(x2, y2), (x2 - 18, y2 - 10), (x2 - 18, y2 + 10)], fill=color)


def draw_phone(draw):
    x, y, w, h = 120, 330, 270, 400
    rounded(draw, (x, y, x + w, y + h), 36, "#141414")
    rounded(draw, (x + 14, y + 18, x + w - 14, y + h - 18), 26, "#f7f6f2")
    draw.ellipse((x + 120, y + 8, x + 150, y + 15), fill="#2b2b2b")
    text(draw, (x + 38, y + 58), "Phone WeChat", INK, "h3")
    # WeChat icon
    draw.ellipse((x + 42, y + 110, x + 92, y + 160), fill=GREEN)
    draw.ellipse((x + 76, y + 130, x + 122, y + 176), fill=GREEN)
    draw.ellipse((x + 57, y + 128, x + 64, y + 135), fill="white")
    draw.ellipse((x + 78, y + 128, x + 85, y + 135), fill="white")
    draw.ellipse((x + 91, y + 144, x + 97, y + 150), fill="white")
    draw.ellipse((x + 108, y + 144, x + 114, y + 150), fill="white")
    rounded(draw, (x + 34, y + 205, x + w - 34, y + 276), 16, "white", "#e3dfd6")
    text(draw, (x + 56, y + 223), "#2  article link", INK, "small")
    text(draw, (x + 56, y + 250), "forward to myself", MUTED, "tiny")
    rounded(draw, (x + 34, y + 294, x + w - 34, y + 365), 16, "white", "#e3dfd6")
    text(draw, (x + 56, y + 312), "image / note", INK, "small")
    text(draw, (x + 56, y + 339), "from mobile", MUTED, "tiny")


def draw_workspace(draw):
    x, y, w, h = 520, 326, 560, 420
    rounded(draw, (x, y, x + w, y + h), 26, "#ffffff", "#d7d1c5", 2)
    draw.rectangle((x, y, x + w, y + 58), fill="#f4f0e7")
    draw.ellipse((x + 26, y + 22, x + 40, y + 36), fill="#ff6257")
    draw.ellipse((x + 50, y + 22, x + 64, y + 36), fill=YELLOW)
    draw.ellipse((x + 74, y + 22, x + 88, y + 36), fill=GREEN)
    text(draw, (x + 118, y + 19), "Sherlockdogs local pipeline", INK, "small")
    # dog badge
    cx, cy = x + 130, y + 175
    draw.ellipse((cx - 62, cy - 62, cx + 62, cy + 62), fill="#fffaf0", outline=YELLOW, width=4)
    draw.pieslice((cx - 45, cy - 7, cx - 3, cy + 62), 78, 292, fill="#e8e2d6", outline=INK, width=4)
    draw.ellipse((cx - 22, cy - 6, cx + 46, cy + 46), fill="#fbfaf6", outline=INK, width=4)
    draw.ellipse((cx + 32, cy + 5, cx + 66, cy + 31), fill="#fbfaf6", outline=INK, width=4)
    draw.ellipse((cx + 56, cy + 13, cx + 66, cy + 23), fill=INK)
    draw.ellipse((cx + 23, cy + 9, cx + 30, cy + 16), fill=INK)
    draw.line((cx - 18, cy + 42, cx - 42, cy + 86), fill=INK, width=6)
    draw.line((cx + 16, cy + 43, cx + 37, cy + 84), fill=INK, width=6)
    draw.line((cx - 38, cy + 63, cx + 46, cy + 78), fill=INK, width=9)
    draw.arc((cx - 38, cy - 52, cx + 44, cy + 12), 202, 338, fill=INK, width=5)
    draw.line((cx - 50, cy - 26, cx + 50, cy - 26), fill=INK, width=5)
    draw.line((cx - 10, cy - 55, cx - 10, cy - 37), fill=INK, width=5)
    draw.ellipse((cx - 17, cy - 64, cx - 3, cy - 50), fill=INK)
    text(draw, (x + 230, y + 104), "Opt-in Mac WeChat DB", INK, "h3")
    text(draw, (x + 230, y + 140), "No relay server. No bot account.", MUTED, "small")
    # service cards
    cards = [
        (x + 230, y + 210, "Start", "run services", YELLOW),
        (x + 230, y + 276, "Connect WeChat", "bind self-chat", GREEN),
        (x + 230, y + 342, "OneTouchRepair", "restart + catch up", BLUE),
    ]
    for x1, y1, title, desc, color in cards:
        rounded(draw, (x1, y1, x + w - 42, y1 + 52), 14, "#fbfaf6", "#e4ded3")
        draw.rectangle((x1, y1, x1 + 9, y1 + 52), fill=color)
        text(draw, (x1 + 25, y1 + 8), title, INK, "small")
        text(draw, (x1 + 205, y1 + 11), desc, MUTED, "tiny")


def draw_outputs(draw):
    x, y = 1210, 330
    rounded(draw, (x, y, x + 250, y + 144), 22, "#fff", "#d9d3c8", 2)
    text(draw, (x + 28, y + 28), "Markdown", INK, "h3")
    text(draw, (x + 28, y + 65), "raw.md", MUTED, "small")
    text(draw, (x + 28, y + 96), "metadata.json", MUTED, "small")
    rounded(draw, (x, y + 205, x + 250, y + 349), 22, "#fff", "#d9d3c8", 2)
    rounded(draw, (x + 30, y + 238, x + 82, y + 290), 12, "#ffe074")
    text(draw, (x + 105, y + 230), "Codex", INK, "h3")
    text(draw, (x + 105, y + 267), "ready task", MUTED, "small")


def render(path: Path, size=(W, H), crop=None):
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    # background texture
    for i in range(0, W, 32):
        color = "#fbf8ef" if (i // 32) % 2 == 0 else "#fffdf8"
        draw.line((i, 0, i + 540, H), fill=color, width=2)
    draw.ellipse((900, -170, 1640, 520), fill="#fff2ba")
    draw.ellipse((1080, 520, 1700, 1060), fill="#edf5ff")
    draw.ellipse((-170, 545, 410, 1030), fill="#f1f8ea")

    text(draw, (112, 83), "Sherlockdogs", INK, "brand")
    text(draw, (112, 134), "Your WeChat saves,", INK, "hero")
    text(draw, (112, 214), "ready for Codex.", INK, "hero")
    text(draw, (915, 124), "Send anything to yourself in WeChat.", MUTED, "body")
    text(draw, (915, 162), "Sherlockdogs turns it into local Markdown + Codex tasks.", MUTED, "body")
    pill(draw, (915, 222), "Local-first beta", "#fff0b8")
    x2 = pill(draw, (1110, 222), "Mac verified", "#e8f8ee")
    pill(draw, (x2, 222), "OneTouchRepair", "#e9f0ff")

    draw_phone(draw)
    draw_workspace(draw)
    draw_outputs(draw)
    arrow(draw, (410, 535), (500, 535), YELLOW, 7)
    arrow(draw, (1094, 535), (1190, 535), YELLOW, 7)

    # footer strip
    rounded(draw, (120, 785, 1480, 842), 22, "#151515")
    text(draw, (154, 801), "Phone WeChat -> Desktop WeChat -> Sherlockdogs -> Markdown library -> Codex task", "#fff8e8", "small")
    text(draw, (1015, 801), "If it does not arrive: click OneTouchRepair", "#ffd76a", "small")

    if crop:
        img = img.crop(crop)
    if size != img.size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    img.save(path, quality=95)


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    render(ASSET_DIR / "sherlockdogs-hero.png")
    render(ASSET_DIR / "social-preview.png", size=(1280, 640), crop=(0, 80, 1600, 880))


if __name__ == "__main__":
    main()
