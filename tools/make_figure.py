#!/usr/bin/env python3
"""Generate src/figure.svg: resource-planning mention rates with 95% intervals.
Data is copied from audits/teamwork-pm/report.html (n=80 answers per brand,
resource-planning theme). Stdlib only."""
from pathlib import Path

ROWS = [  # brand, rate, low, high (percent, as printed in the report)
    ("Asana", 85, 76, 91),
    ("monday.com", 68, 57, 77),
    ("Teamwork.com", 25, 17, 35),
    ("ClickUp", 20, 13, 30),
    ("Trello", 3.8, 1.3, 10),
    ("Notion", 0, 0, 4.6),
]
X0, X1, W, H, STEP, TOP = 108, 356, 480, 276, 36, 22


def x(v):
    return round(X0 + (X1 - X0) * v / 100, 1)


def fmt(v):
    return f"{v:g}"


out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
    'aria-labelledby="fig-t fig-d" class="fig">',
    '<title id="fig-t">Resource planning: mention rate by brand, with 95% intervals</title>',
    '<desc id="fig-d">ChatGPT answers to resource-planning questions, 80 per brand. '
    + "; ".join(f"{b} {fmt(r)}%, interval {fmt(lo)}% to {fmt(hi)}%" for b, r, lo, hi in ROWS)
    + ".</desc>",
]
bottom = TOP + STEP * len(ROWS) - 8
out.append('<g stroke="#d8e0e6" stroke-width="1">')
for v in (0, 50, 100):
    out.append(f'<line x1="{x(v)}" y1="{TOP-8}" x2="{x(v)}" y2="{bottom}"/>')
out.append("</g>")
out.append('<g class="ax" font-size="13" fill="#4a5d73" text-anchor="middle">')
for v in (0, 50, 100):
    out.append(f'<text x="{x(v)}" y="{bottom+20}">{v}%</text>')
out.append("</g>")
for i, (b, r, lo, hi) in enumerate(ROWS):
    y = TOP + STEP * i + 8
    hl = b == "Teamwork.com"
    col = "#1b6e63" if hl else "#6b7b8d"
    wt = "700" if hl else "400"
    out.append(f'<text x="0" y="{y+5}" font-size="15" font-weight="{wt}" fill="#0f2742">{b}</text>')
    out.append(
        f'<text x="{W}" y="{y+5}" font-size="14" text-anchor="end" fill="{"#14584f" if hl else "#4a5d73"}" '
        f'font-weight="{wt}">{fmt(r)}% ({fmt(lo)} to {fmt(hi)})</text>'
    )
    out.append(f'<g stroke="{col}" stroke-width="3" fill="{col}">')
    out.append(f'<line class="iv" pathLength="1" x1="{x(lo)}" y1="{y}" x2="{x(hi)}" y2="{y}"/>')
    out.append(f'<line class="cap" x1="{x(lo)}" y1="{y-6}" x2="{x(lo)}" y2="{y+6}"/>')
    out.append(f'<line class="cap" x1="{x(hi)}" y1="{y-6}" x2="{x(hi)}" y2="{y+6}"/>')
    out.append(f'<circle cx="{x(r)}" cy="{y}" r="{7 if hl else 6}" stroke="none"/>')
    out.append("</g>")
out.append("</svg>")
Path(__file__).resolve().parent.parent.joinpath("src/figure.svg").write_text("\n".join(out) + "\n")
