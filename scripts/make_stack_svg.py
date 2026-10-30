"""Tech-stack panel: official logos (from simple-icons, CC0) grouped by area.

Tiles pop in one after another on load, then stay put.
Edit STACK below, then run:  python scripts/make_stack_svg.py   # writes stack.svg
Icon paths + brand colours live in assets/stack-icons.json.
"""
import json
import os
from xml.sax.saxutils import escape

# (area, [(icon slug or None, label)])  None -> generic cloud glyph
STACK = [
    ("frontend", [("react", "React"), ("nextdotjs", "Next.js"), ("typescript", "TypeScript"),
                  ("javascript", "JavaScript"), ("redux", "Redux"), ("reactquery", "TanStack"),
                  ("tailwindcss", "Tailwind"), ("vite", "Vite"), ("webpack", "Webpack")]),
    ("backend", [("nodedotjs", "Node.js"), ("express", "Express"), ("graphql", "GraphQL"),
                 ("razorpay", "Razorpay")]),
    ("data", [("postgresql", "PostgreSQL"), ("mysql", "MySQL"), ("mongodb", "MongoDB")]),
    ("cloud & ops", [(None, "AWS"), ("docker", "Docker"), ("githubactions", "Actions"),
                     ("gitlab", "GitLab CI"), ("linux", "Linux"), ("git", "Git")]),
    ("testing & tools", [("jest", "Jest"), ("postman", "Postman"), ("figma", "Figma")]),
]

W = 900
PAD = 28
LABEL_W = 150
TILE, GAP = 50, 18
ROW_H = 84
TOP = 74
BG, BAR, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED, KEY, ACCENT = "#c9d1d9", "#8b949e", "#39d353", "#58a6ff"
AWS_ORANGE = "#FF9900"
CLOUD = ("M19.35 10.04A7.49 7.49 0 0 0 12 4C9.11 4 6.6 5.64 5.35 8.04A5.99 5.99 0 0 0 0 14c0 "
         "3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z")
STAGGER = 0.06
START = 0.25

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def visible(hexv: str) -> str:
    """Brand colours too dark for a dark tile fall back to light text colour."""
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#e6edf3" if lum < 0.16 else f"#{hexv}"


def build() -> str:
    icons = json.load(open(os.path.join(ROOT, "assets", "stack-icons.json"), encoding="utf-8"))
    H = TOP + len(STACK) * ROW_H + 12
    font = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Tech stack">',
        "<style>"
        f"text{{font-family:{font}}}"
        "@keyframes pop{0%{opacity:0;transform:translateY(8px) scale(.7)}70%{transform:translateY(-2px) scale(1.06)}"
        "100%{opacity:1;transform:none}}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".t{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .5s ease-out both}"
        ".l{opacity:0;animation:in .45s ease-out both}"
        "</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M10.5 .5h{W - 21}a10 10 0 0 1 10 10v24H.5v-24a10 10 0 0 1 10-10z" fill="{BAR}"/>',
        f'<line x1="0" y1="34.5" x2="{W}" y2="34.5" stroke="{BORDER}"/>',
    ]
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        o.append(f'<circle cx="{20 + i * 18}" cy="17.5" r="6" fill="{c}"/>')
    o.append(f'<text x="{W / 2}" y="22" text-anchor="middle" fill="{MUTED}" font-size="13">aswin@github: ~/stack</text>')
    o.append(f'<text x="{PAD}" y="60" font-size="14"><tspan fill="{KEY}">$</tspan>'
             f'<tspan fill="{TEXT}"> ls --group-by area ~/stack</tspan></text>')

    n = 0
    for r, (area, items) in enumerate(STACK):
        y = TOP + r * ROW_H
        o.append(f'<g class="l" style="animation-delay:{START + n * STAGGER:.2f}s">'
                 f'<text x="{PAD}" y="{y + TILE / 2 + 5}" font-size="13">'
                 f'<tspan fill="{MUTED}">▸ </tspan><tspan fill="{ACCENT}" font-weight="bold">{escape(area)}</tspan></text></g>')
        for c, (slug, label) in enumerate(items):
            x = PAD + LABEL_W + c * (TILE + GAP)
            if slug is None:
                color, path, scale = AWS_ORANGE, CLOUD, 26 / 24
            else:
                ic = icons[slug]
                color, path, scale = visible(ic["hex"]), ic["path"], 26 / 24
            off = (TILE - 26) / 2
            tile = (
                f'<rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="11" fill="{BAR}" stroke="{BORDER}"/>'
                f'<rect x="{x + 1}" y="{y + TILE - 3}" width="{TILE - 2}" height="2" rx="1" fill="{color}" opacity=".55"/>'
                f'<path transform="translate({x + off} {y + off}) scale({scale:.4f})" d="{path}" fill="{color}"/>'
                f'<text x="{x + TILE / 2}" y="{y + TILE + 16}" text-anchor="middle" font-size="10.5" fill="{TEXT}">{escape(label)}</text>'
            )
            title = escape(label if slug is None else icons[slug]["title"])
            o.append(f'<g class="t" style="animation-delay:{START + n * STAGGER:.2f}s"><title>{title}</title>{tile}</g>')
            n += 1
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    with open("stack.svg", "w", encoding="utf-8") as f:
        f.write(build())
    print("wrote stack.svg")
