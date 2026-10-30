"""Hand-authored neofetch-style info card SVG.

Edit the ROWS list below when your role, stack or highlights change, then run:
    python scripts/make_info_card.py            # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py   # frozen frame (no animation)
"""
import os
from xml.sax.saxutils import escape

USER = "aswin"
HOST = "github"

# (key, value) rows. A key of None draws a blank spacer line.
ROWS = [
    ("Role", "Senior Software Engineer · 4+ yrs"),
    ("Now", "Senior Software Engineer @ UK-based company"),
    ("Prev", "KurlTech Systems · HR Geckos (US, remote)"),
    ("Location", "Palakkad, Kerala, India"),
    (None, None),
    ("Core", "React · Next.js · TypeScript · Node.js"),
    ("Data", "PostgreSQL · MySQL · MongoDB"),
    ("Security", "JWT · RBAC · OAuth · OWASP Top 10"),
    ("DevOps", "AWS (EC2, S3) · Docker · GitHub Actions"),
    (None, None),
    ("Impact", "50% faster APIs · 35% faster debugging"),
    ("Quality", "0 critical regressions in 6 releases"),
    ("Projects", "HI5 Overseas · Subscription & Payments"),
    ("Open to", "Remote & relocation"),
]

W, H = 735, 546
PAD_X = 28
FONT = 15
LH = 25
TOP = 86
KEY_W = 11  # key column width in characters
CW = FONT * 0.6

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
KEY = "#39d353"
ACCENT = "#58a6ff"
SWATCHES = ["#ff7b72", "#ffa657", "#d2a8ff", "#79c0ff", "#56d364", "#39d353", "#e3b341", "#c9d1d9"]

STAGGER = 0.12
START = 0.3


def build(static: bool) -> str:
    css = (
        "" if static else
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".l{opacity:0;animation:in .45s ease-out both}"
    )
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="About Aswin P">',
        f"<style>{css}text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;font-size:{FONT}px}}</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M10.5 .5h{W - 21}a10 10 0 0 1 10 10v24H.5v-24a10 10 0 0 1 10-10z" fill="{BAR}"/>',
        f'<line x1="0" y1="34.5" x2="{W}" y2="34.5" stroke="{BORDER}"/>',
    ]
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        o.append(f'<circle cx="{20 + i * 18}" cy="17.5" r="6" fill="{c}"/>')
    o.append(f'<text x="{W / 2}" y="22" text-anchor="middle" fill="{MUTED}" font-size="13">{USER}@{HOST}: ~</text>')

    def line(idx: int, y: float, inner: str) -> str:
        if static:
            return f"<g>{inner}</g>"
        return f'<g class="l" style="animation-delay:{START + idx * STAGGER:.2f}s">{inner}</g>'

    n = 0
    y = TOP
    title = f'<text x="{PAD_X}" y="{y}"><tspan fill="{KEY}" font-weight="bold">{USER}</tspan><tspan fill="{TEXT}">@</tspan><tspan fill="{KEY}" font-weight="bold">{HOST}</tspan></text>'
    o.append(line(n, y, title)); n += 1; y += LH
    rule = "-" * len(f"{USER}@{HOST}")
    o.append(line(n, y, f'<text x="{PAD_X}" y="{y}" fill="{MUTED}">{rule}</text>')); n += 1; y += LH

    for key, val in ROWS:
        if key is None:
            y += LH * 0.5
            continue
        inner = (
            f'<text x="{PAD_X}" y="{y}"><tspan fill="{ACCENT}" font-weight="bold">{escape(key)}</tspan>'
            f'<tspan fill="{MUTED}">:</tspan></text>'
            f'<text x="{PAD_X + KEY_W * CW}" y="{y}" fill="{TEXT}">{escape(val)}</text>'
        )
        o.append(line(n, y, inner)); n += 1; y += LH

    y += LH * 0.4
    sw = "".join(
        f'<rect x="{PAD_X + i * 30}" y="{y - 14}" width="26" height="16" rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    o.append(line(n, y, sw))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    with open("info-card.svg", "w", encoding="utf-8") as f:
        f.write(build(static=os.environ.get("STATIC") == "1"))
    print("wrote info-card.svg")
