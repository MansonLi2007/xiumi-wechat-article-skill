#!/usr/bin/env python3
"""图片后处理：居中裁切到公众号尺寸、转 sRGB、压到 500KB 内。

用法：
    python prep_images.py cover.png --out images --name cover
    # -> images/cover-235.jpg (900x383, 2.35:1)
    #    images/cover-11.jpg  (1080x1080, 1:1)

    python prep_images.py shot.jpg --out images --name fig1 --body
    # -> images/fig1-169.jpg (1080x608, 16:9)

    python prep_images.py *.png --out images        # 批量，名字取原文件名
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET_BYTES = 500 * 1024


def _lanczos():
    """Pillow >= 10 moved the resample constants under Image.Resampling."""
    from PIL import Image

    return getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)


def crop_to_ratio(im, ratio: float, vertical_bias: float = 0.45):
    w, h = im.size
    if w / h > ratio:  # 太宽，裁左右
        new_w = int(round(h * ratio))
        left = max(0, (w - new_w) // 2)
        return im.crop((left, 0, left + new_w, h))
    new_h = int(round(w / ratio))  # 太高，裁上下（偏上，保护主体）
    top = max(0, int(round((h - new_h) * vertical_bias)))
    return im.crop((0, top, w, top + new_h))


def save_jpeg(im, out: Path, size: tuple[int, int]) -> Path:
    if im.size != size:
        im = im.resize(size, _lanczos())
    quality = 82
    while quality >= 55:
        im.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
        if out.stat().st_size <= TARGET_BYTES:
            break
        quality -= 6
    im.close()
    return out


def process(src: Path, out_dir: Path, name: str, body: bool) -> list[Path]:
    from PIL import Image

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with Image.open(src) as raw:
        im = raw.convert("RGB")
        specs = [("235", 2.35, (900, 383)), ("11", 1.0, (1080, 1080))]
        if body:
            specs = [("169", 16 / 9, (1080, 608))]
        for suffix, ratio, size in specs:
            target = out_dir / f"{name}-{suffix}.jpg"
            cropped = crop_to_ratio(im, ratio)
            save_jpeg(cropped, target, size)
            kb = target.stat().st_size / 1024
            print(f"[ok] {target}  {size[0]}x{size[1]}  {kb:.0f}KB")
            written.append(target)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="crop & compress images for WeChat")
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--out", default="images")
    ap.add_argument("--name", default=None, help="输出文件名前缀，仅单文件时有效")
    ap.add_argument("--body", action="store_true", help="按正文图处理（16:9，不出封面尺寸）")
    args = ap.parse_args()

    out_dir = Path(args.out)
    for item in args.sources:
        src = Path(item)
        if not src.exists():
            print(f"[skip] {src} not found")
            continue
        name = args.name or src.stem
        process(src, out_dir, name, args.body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
