#!/usr/bin/env python3
"""Render GitHub hero assets from the approved illustration source."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets"
SOURCE = ASSET_DIR / "sherlockdogs-hero-source.png"


def cover_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    source_w, source_h = img.size
    target_ratio = target_w / target_h
    source_ratio = source_w / source_h

    if source_ratio > target_ratio:
        crop_w = round(source_h * target_ratio)
        left = (source_w - crop_w) // 2
        box = (left, 0, left + crop_w, source_h)
    else:
        crop_h = round(source_w / target_ratio)
        top = (source_h - crop_h) // 2
        box = (0, top, source_w, top + crop_h)

    return img.crop(box).resize(size, Image.Resampling.LANCZOS)


def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source image: {SOURCE}")

    source = Image.open(SOURCE).convert("RGB")
    save_png(cover_resize(source, (1600, 900)), ASSET_DIR / "sherlockdogs-hero.png")
    save_png(cover_resize(source, (1280, 640)), ASSET_DIR / "social-preview.png")


if __name__ == "__main__":
    main()
