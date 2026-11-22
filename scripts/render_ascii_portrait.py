"""Turn a photo into an animated ASCII portrait SVG (avi-style, 370px wide).

Usage:  python scripts/render_ascii_portrait.py path/to/photo.jpg
Extras: pip install pillow numpy rembg  (opencv-python optional, for CLAHE contrast)
Run locally only; the daily workflow does not touch the portrait.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

OUT = Path(__file__).resolve().parent.parent / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

COLS, MAX_ROWS = 100, 72
LINE_H = 1.12  # line height in em
RAMP = " .'`^,:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
W = 370
BG, FG, BORDER, CURSOR = "#0d1117", "#c9d1d9", "#30363d", "#39d353"


def prepare(path: Path) -> np.ndarray:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("RGBA")
    try:
        from rembg import remove

        img = remove(img)
    except Exception as exc:  # rembg is optional
        print(f"rembg skipped: {exc}")
    # Composite onto black so the subject reads as light on the dark card.
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    gray = Image.alpha_composite(bg, img).convert("L")

    # Crop to the subject's bounding box, using alpha if rembg worked.
    bbox = img.getchannel("A").getbbox() or gray.getbbox()
    if bbox:
        gray = gray.crop(bbox)

    arr = np.asarray(gray)
    try:
        import cv2

        arr = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(arr)
    except ImportError:
        arr = np.asarray(ImageOps.autocontrast(Image.fromarray(arr), cutoff=1))

    # A character cell is 0.6em wide and LINE_H em tall; size rows to keep the photo's aspect.
    h, w = arr.shape
    rows = max(20, min(MAX_ROWS, round(COLS * (h / w) * 0.6 / LINE_H)))
    small = Image.fromarray(arr).resize((COLS, rows), Image.LANCZOS)
    return np.asarray(small, dtype=np.float32) / 255.0


def to_rows(arr: np.ndarray) -> list[str]:
    idx = (arr * (len(RAMP) - 1)).round().astype(int)
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(rows: list[str]) -> str:
    pad = 14
    char_w = (W - 2 * pad) / COLS
    font = char_w / 0.6
    line_h = font * LINE_H
    n = len(rows)
    H = int(pad * 2 + line_h * n)
    row_dur, stagger = 0.5, 0.045
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="ASCII portrait">',
        "<style>",
        f"text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:{font:.2f}px;fill:{FG};white-space:pre}}",
    ]
    if not STATIC:
        p += [
            "@keyframes wipe{from{width:0}to{width:%dpx}}" % W,
            "@keyframes sweep{from{transform:translateX(0);opacity:1}99%%{opacity:1}to{transform:translateX(%dpx);opacity:0}}" % (W - 2 * pad),
            ".w{animation:wipe %.2fs steps(%d) forwards;width:0}" % (row_dur, COLS // 4),
            ".cur{animation:sweep %.2fs steps(%d) forwards;opacity:0}" % (row_dur, COLS // 4),
        ]
    p += ["</style>", f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>']
    if not STATIC:
        p.append("<defs>")
        for i in range(n):
            y = pad + i * line_h
            p.append(
                f'<clipPath id="r{i}"><rect class="w" x="{pad}" y="{y:.2f}" height="{line_h+0.5:.2f}" '
                f'style="animation-delay:{i*stagger:.3f}s"/></clipPath>'
            )
        p.append("</defs>")
    for i, row in enumerate(rows):
        y = pad + i * line_h + font * 0.9
        clip = "" if STATIC else f' clip-path="url(#r{i})"'
        p.append(f'<text x="{pad}" y="{y:.2f}"{clip}>{esc(row)}</text>')
        if not STATIC:
            p.append(
                f'<rect class="cur" x="{pad}" y="{pad + i*line_h:.2f}" width="{char_w*1.2:.2f}" height="{line_h:.2f}" '
                f'fill="{CURSOR}" style="animation-delay:{i*stagger:.3f}s"/>'
            )
    p.append("</svg>")
    return "\n".join(p)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    rows = to_rows(prepare(Path(sys.argv[1])))
    OUT.write_text(render(rows), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
