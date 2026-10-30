"""Render data/contributions.json as an animated contribution heatmap SVG.

Boxes slide in along a diagonal once on load, then stay put (no looping).

Usage: python scripts/render_heatmap_svg.py [in.json] [out.svg]
"""
import datetime as dt
import json
import os
import sys

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end for your biggest days)

CELL, GAP = 13, 3
STEP = CELL + GAP
LEFT, TOP = 44, 44
W = 900
BG, BORDER = "#0d1117", "#30363d"
TEXT, MUTED, ACCENT = "#c9d1d9", "#8b949e", "#39d353"
DIAG_DELAY = 0.014  # seconds per diagonal step


def level_for(count: int, gh_level: int, top: int) -> int:
    if count <= 0:
        return 0
    if top and count >= max(top * 0.85, 10):
        return 5
    return max(1, min(4, gh_level or 1))


def build(data: dict | None) -> str:
    days = (data or {}).get("days", [])
    st = (data or {}).get("stats", {})
    if days:
        first = dt.date.fromisoformat(days[0]["date"])
        start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
    else:
        today = dt.date.today()
        start = today - dt.timedelta(days=(today.weekday() + 1) % 7) - dt.timedelta(weeks=52)
        days = [{"date": (start + dt.timedelta(d)).isoformat(), "count": 0, "level": 0}
                for d in range(53 * 7)]
    top = max((d["count"] for d in days), default=0)
    weeks = max((dt.date.fromisoformat(d["date"]) - start).days // 7 for d in days) + 1
    grid_h = 7 * STEP
    H = TOP + grid_h + 78

    font = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="GitHub contribution graph">',
        "<style>"
        f"text{{font-family:{font}}}"
        "@keyframes drop{from{opacity:0;transform:translateY(-7px)}to{opacity:1;transform:none}}"
        ".c{opacity:0;transform-box:fill-box;animation:drop .4s ease-out both}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        ".f{opacity:0;animation:fade .6s ease-out both}"
        "</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    ]

    grid_w = weeks * STEP
    x0 = LEFT + (W - LEFT - 20 - grid_w) / 2

    # month labels
    seen = set()
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        w = (date - start).days // 7
        key = (date.year, date.month)
        if date.day <= 7 and key not in seen and w < weeks - 1:
            seen.add(key)
            o.append(f'<text x="{x0 + w * STEP:.1f}" y="{TOP - 12}" fill="{MUTED}" font-size="11">{date.strftime("%b")}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="{x0 - 8:.1f}" y="{TOP + row * STEP + 10}" fill="{MUTED}" font-size="10" text-anchor="end">{name}</text>')

    max_delay = 0.0
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        w, r = (date - start).days // 7, (date.weekday() + 1) % 7
        lvl = level_for(d["count"], d.get("level", 0), top)
        delay = (w + r) * DIAG_DELAY
        max_delay = max(max_delay, delay)
        title = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {date:%b %d, %Y}'
        o.append(
            f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x0 + w * STEP:.1f}" y="{TOP + r * STEP}" '
            f'width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[lvl]}"><title>{title}</title></rect>'
        )

    fy = TOP + grid_h + 22
    fd = f'style="animation-delay:{max_delay:.2f}s"'
    # legend
    lx = W - 20 - len(PALETTE) * 16 - 70
    legend = [f'<text x="{lx}" y="{fy + 10}" fill="{MUTED}" font-size="11">Less</text>']
    for i, c in enumerate(PALETTE):
        legend.append(f'<rect x="{lx + 36 + i * 16}" y="{fy}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    legend.append(f'<text x="{lx + 36 + len(PALETTE) * 16 + 4}" y="{fy + 10}" fill="{MUTED}" font-size="11">More</text>')
    o.append(f'<g class="f" {fd}>{"".join(legend)}</g>')

    if st:
        total = f'{st.get("total", 0):,}'
        line1 = (f'<tspan fill="{ACCENT}" font-weight="bold">{total}</tspan>'
                 f'<tspan fill="{TEXT}"> contributions in the last year</tspan>')
        best = st.get("best_day") or {}
        bits = [f'current streak {st.get("current_streak", 0)}d',
                f'longest {st.get("longest_streak", 0)}d',
                f'{st.get("active_days", 0)} active days']
        if best.get("count"):
            bits.append(f'best day {best["count"]} ({dt.date.fromisoformat(best["date"]):%b %d})')
        line2 = " · ".join(bits)
    else:
        line1 = f'<tspan fill="{MUTED}">waiting for the first daily refresh…</tspan>'
        line2 = ""
    o.append(f'<g class="f" {fd}><text x="{x0:.1f}" y="{fy + 11}" font-size="13">{line1}</text>'
             f'<text x="{x0:.1f}" y="{fy + 33}" font-size="11.5" fill="{MUTED}">{line2}</text></g>')
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    data = None
    if os.path.exists(src):
        with open(src, encoding="utf-8") as f:
            data = json.load(f)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(build(data))
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
