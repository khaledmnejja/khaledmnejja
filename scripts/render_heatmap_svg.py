"""Render data/contributions.json into an animated contrib-heatmap.svg (860px wide)."""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

BG, FG, MUTED, BORDER = "#0d1117", "#c9d1d9", "#8b949e", "#30363d"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

W = 860
CELL, GAP = 12, 3
PAD_X, GRID_Y = 38, 58
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]

    # Lay out in week columns starting on Sunday, like GitHub.
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # Sunday=0
    cells = []
    month_labels = {}
    for i, d in enumerate(days):
        idx = i + offset
        col, row = divmod(idx, 7)
        dt = date.fromisoformat(d["date"])
        # Label a month at the first week column whose Sunday falls in days 1-7.
        if row == 0 and dt.day <= 7:
            month_labels.setdefault(d["date"][:7], col)
        cells.append((col, row, d))

    cols = max(c for c, _, _ in cells) + 1
    grid_w = cols * (CELL + GAP) - GAP
    x0 = PAD_X + (W - 2 * PAD_X - grid_w) / 2 + 10
    grid_h = 7 * (CELL + GAP) - GAP
    H = GRID_Y + grid_h + 78

    step = 0.012
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{esc(data["username"])} contribution graph">',
        "<style>",
        f"text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:{FG}}}",
        f".m{{fill:{MUTED};font-size:11px}}.t{{font-size:15px;font-weight:700}}",
        ".s{font-size:12px}.v{fill:#39d353;font-weight:700}",
    ]
    if not STATIC:
        parts += [
            "@keyframes pop{0%{opacity:0;transform:translateX(-6px) scale(.6)}100%{opacity:1;transform:none}}",
            "@keyframes fade{from{opacity:0}to{opacity:1}}",
            ".c{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .35s ease-out forwards}",
            ".f{opacity:0;animation:fade .6s ease-out forwards}",
        ]
    parts += [
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="{PAD_X}" y="32" class="t">{data["total"]:,} contributions in the last year</text>',
        f'<text x="{W-PAD_X}" y="32" class="m" text-anchor="end">@{esc(data["username"])} · updated {data["generated"]}</text>',
    ]

    for ym, col in month_labels.items():
        if col < cols - 1:
            parts.append(
                f'<text x="{x0 + col*(CELL+GAP):.1f}" y="{GRID_Y-8}" class="m">{MONTHS[int(ym[5:])-1]}</text>'
            )
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{x0-8:.1f}" y="{GRID_Y + row*(CELL+GAP) + 10}" class="m" text-anchor="end">{name}</text>'
        )

    for col, row, d in cells:
        x = x0 + col * (CELL + GAP)
        y = GRID_Y + row * (CELL + GAP)
        anim = "" if STATIC else f' class="c" style="animation-delay:{(col+row)*step:.3f}s"'
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{LEVELS[min(d["level"],4)]}"{anim}><title>{d["count"]} on {d["date"]}</title></rect>'
        )

    end = (cols + 7) * step
    fade = "" if STATIC else f' class="f" style="animation-delay:{end:.2f}s"'
    fy = GRID_Y + grid_h + 30
    best = data["best_day"]
    stats = [
        ("current streak", f'{data["current_streak"]}d'),
        ("longest streak", f'{data["longest_streak"]}d'),
        ("best day", f'{best["count"]}'),
    ]
    parts.append(f"<g{fade}>")
    sx = PAD_X
    for label, val in stats:
        parts.append(f'<text x="{sx}" y="{fy}" class="s"><tspan class="v">{val}</tspan> <tspan class="m">{label}</tspan></text>')
        sx += 170
    lx = W - PAD_X - 5 * (CELL + 3) - 40
    parts.append(f'<text x="{lx-8}" y="{fy}" class="m" text-anchor="end">Less</text>')
    for i, c in enumerate(LEVELS):
        parts.append(f'<rect x="{lx + i*(CELL+3)}" y="{fy-10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    parts.append(f'<text x="{lx + 5*(CELL+3) + 4}" y="{fy}" class="m">More</text>')
    parts.append("</g></svg>")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({cols} weeks)")


if __name__ == "__main__":
    main()
