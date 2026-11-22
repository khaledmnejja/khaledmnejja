"""Render a neofetch-style animated info-card.svg (490px wide). Edit INFO to change it."""
from __future__ import annotations

import os
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

TITLE = "khaled@github"
INFO: list[tuple[str, str]] = [
    ("Name", "Khaled Mnejja"),
    ("Now", "L3 GLSI student @ IIT Sfax"),
    ("Focus", "Full-stack web & machine learning"),
    ("", ""),
    ("Stack", "TypeScript · React · Next.js"),
    ("", "Python · scikit-learn · Jupyter"),
    ("3D", "Three.js · interior configurators"),
    ("", ""),
    ("Built", "Zen Design Engine"),
    ("", "  3D interior config + quotation"),
    ("", "Online-shopping intent predictor"),
    ("", "  ML on UCI Online Shoppers"),
    ("", ""),
    ("Site", "khaled-mnejja-portfolio.vercel.app"),
]

BG, FG, MUTED, BORDER = "#0d1117", "#c9d1d9", "#8b949e", "#30363d"
KEY, ACCENT = "#58a6ff", "#39d353"
W, LINE, TOP = 490, 21, 64


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    H = TOP + len(INFO) * LINE + 46
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="About Khaled">',
        "<style>",
        f"text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13.5px;fill:{FG};white-space:pre}}",
        f".k{{fill:{KEY};font-weight:700}}.m{{fill:{MUTED}}}.a{{fill:{ACCENT};font-weight:700}}",
    ]
    if not STATIC:
        p += [
            "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}",
            "@keyframes blink{50%{opacity:0}}",
            ".l{opacity:0;animation:in .45s ease-out forwards}",
            ".cur{animation:blink 1s steps(1) infinite}",
        ]
    p += [
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0.5 32 H{W-0.5}" stroke="{BORDER}"/>',
    ]
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        p.append(f'<circle cx="{20 + i*18}" cy="16.5" r="5.5" fill="{c}"/>')
    p.append(f'<text x="{W/2}" y="21" class="m" text-anchor="middle">{TITLE} — neofetch</text>')

    delay = 0.3
    header = f'<tspan class="a">{TITLE}</tspan>'
    p.append(f'<text x="22" y="{TOP-6}" class="{"" if STATIC else "l"}" style="animation-delay:{delay:.2f}s">{header}</text>')
    for i, (k, v) in enumerate(INFO):
        if not k and not v:
            continue
        delay += 0.12
        y = TOP + 16 + i * LINE
        key = f'<tspan class="k">{esc(k):<6}</tspan> ' if k else f'<tspan>{"":<7}</tspan>'
        cls = "" if STATIC else ' class="l"'
        p.append(f'<text x="22" y="{y}"{cls} style="animation-delay:{delay:.2f}s">{key}{esc(v)}</text>')

    y = TOP + 16 + len(INFO) * LINE + 6
    palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#58a6ff", "#bc8cff", "#ff7b72"]
    g_cls = "" if STATIC else ' class="l"'
    p.append(f'<g{g_cls} style="animation-delay:{delay+0.15:.2f}s">')
    for i, c in enumerate(palette):
        p.append(f'<rect x="{22 + i*26}" y="{y-12}" width="22" height="12" rx="2" fill="{c}"/>')
    p.append(f'<text x="{22 + len(palette)*26 + 8}" y="{y-1}" class="a">$ <tspan class="cur">█</tspan></text>')
    p.append("</g></svg>")
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
