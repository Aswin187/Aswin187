"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each row is revealed by a left-to-right clip wipe with a small block cursor,
staggered top to bottom. Plays once, then freezes (SMIL, works on GitHub).

Usage: python scripts/make_ascii_svg.py [in.png] [out.svg]
       STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import os
import sys
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter, ImageOps

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
COLS = 74
GAMMA = 1.35  # >1 deepens mid-tones so facial features read clearly
FONT = 10
CW = FONT * 0.6  # monospace advance width
LH = FONT * 1.1
PAD = 18
BG = "#0d1117"
INK = "#c9d1d9"
CURSOR = "#39d353"

ROW_STAGGER = 0.045  # seconds between rows starting
ROW_DUR = 0.35  # seconds for one row's wipe


def to_ascii(path: str) -> list[str]:
    img = Image.open(path).convert("L")
    w, h = img.size
    rows = int(round(COLS * (h / w) * (CW / LH)))  # keep the photo's proportions
    img = img.resize((COLS, rows), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=2))
    img = ImageOps.autocontrast(img, cutoff=1)
    a = (np.asarray(img, dtype=np.float32) / 255.0) ** GAMMA
    idx = ((1.0 - a) * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def span(line: str) -> tuple[float, float]:
    """x start and width of the printed (non-blank) part of a row."""
    lead = len(line) - len(line.lstrip(" "))
    return PAD + lead * CW, (len(line) - lead) * CW


def build_svg(lines: list[str], static: bool) -> str:
    width = COLS * CW + PAD * 2
    height = len(lines) * LH + PAD * 2
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-label="ASCII portrait of Aswin P">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        "<defs>",
    ]
    for i, line in enumerate(lines):
        y = PAD + i * LH
        begin = i * ROW_STAGGER
        x0, w = span(line)
        if static:
            out.append(f'<clipPath id="r{i}"><rect x="{x0:.1f}" y="{y:.1f}" width="{w:.1f}" height="{LH:.1f}"/></clipPath>')
        else:
            out.append(
                f'<clipPath id="r{i}"><rect x="{x0:.1f}" y="{y:.1f}" width="0" height="{LH:.1f}">'
                f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{begin:.3f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            )
    out.append("</defs>")
    out.append(
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" '
        f'font-size="{FONT}" fill="{INK}" xml:space="preserve">'
    )
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = PAD + i * LH + FONT * 0.85
        body = line.lstrip(" ")
        lead = len(line) - len(body)
        # position by leading offset and use non-breaking spaces inside, so no
        # renderer can collapse whitespace and skew the picture
        body = body.replace(" ", " ")
        out.append(
            f'<text x="{PAD + lead * CW:.1f}" y="{y:.1f}" textLength="{len(body) * CW:.1f}" '
            f'lengthAdjust="spacing" clip-path="url(#r{i})">{escape(body)}</text>'
        )
    out.append("</g>")
    if not static:
        # block cursor riding the wipe edge of each row
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            y = PAD + i * LH + 1
            begin = i * ROW_STAGGER
            end = begin + ROW_DUR
            x0, w = span(line)
            out.append(
                f'<rect x="{x0:.1f}" y="{y:.1f}" width="{CW:.1f}" height="{LH - 2:.1f}" fill="{CURSOR}" opacity="0">'
                f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
                f'<animate attributeName="x" from="{x0:.1f}" to="{x0 + w:.1f}" begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{end:.3f}s"/></rect>'
            )
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    dst = sys.argv[2] if len(sys.argv) > 2 else "aswin-ascii.svg"
    lines = to_ascii(src)
    svg = build_svg(lines, static=os.environ.get("STATIC") == "1")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {dst} ({len(lines)} rows)")


if __name__ == "__main__":
    main()
