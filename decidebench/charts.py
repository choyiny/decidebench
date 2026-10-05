"""Frontier charts for the README, generated from results/.

    uv run python -m decidebench.charts      # docs/diagrams/*.html and docs/img/*.png (needs Google Chrome)
"""

from __future__ import annotations

import math
import subprocess
import textwrap
from html import escape
from pathlib import Path

from decidebench.dataset import load_items
from decidebench.meta import load_meta
from decidebench.paths import RESULTS_DIR, ROOT, load_env, results_path
from decidebench.registry import ENTRIES, info
from decidebench.report import fronts, label, prepare, short

DIAGRAMS = ROOT / "docs" / "diagrams"
IMG = ROOT / "docs" / "img"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W = 880

PAPER, INK, MUTED, SOFT = "#f5f5f5", "#2d3142", "#4f5d75", "#7a8399"
ACCENT = "#eb6c36"
GRID, AXIS = "rgba(45,49,66,0.08)", "rgba(45,49,66,0.25)"
SANS, MONO = "'Geist', system-ui, sans-serif", "'Geist Mono', ui-monospace, monospace"
FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
         "&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap")
SHORT = {"tev": "TEV (self-hosted)", "tev-together": "TEV (Together)", "jev": "JEV",
         "clef": "Clef", "clef-flash": "Clef-Flash", "drex": "Drex 1.5",
         "deepseek": "DeepSeek-V4-Flash", "deepseek-41": "DeepSeek-V4.1-Flash", "glm-flash": "GLM-5.3-Flash",
         "arize-qwen2": "Qwen2-1.5B (Arize)", "qwen3-8b": "Qwen3-8B (self-hosted)",
         "clm": "CLM-v0.1-8B", "laya-typed": "Laya typed-decisions", "decider-2b": "Decider-2B", "kev-4b": "Kev-4B",
         "decider-4b": "Decider-4B", "kev-9b": "Kev-9B", "jevk5": "JevK5", "imajev-4b": "imajev-4b", "yev0-4b": "yev0-4b",
         "julia-1": "Julia-1", "jeff-800m": "Jeff-0.8B", "jeff-2b": "Jeff-2B", "jeff-gemma4": "Jeff-Gemma4",
         "gliner-decide": "GLiNER2.5-Decide", "nimble-9b": "Nimble-9B"}


def text(x, y, s, size=12, fill=INK, family=SANS, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-family="{family}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


def header(slug: str, title: str, desc: str, h: int, dy: int) -> list[str]:
    """Open the SVG. No visible heading: the README supplies context, so the drawing starts at the top.
    Content is laid out in the original coordinates and shifted up by `dy`; the SVG is `h` tall."""
    return [
        f'<svg viewBox="0 {dy} {W} {h}" width="{W}" height="{h}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{slug}-title {slug}-desc">',
        f'<title id="{slug}-title">{escape(title)}</title>',
        f'<desc id="{slug}-desc">{escape(desc)}</desc>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>'
        '<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        f'<polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker></defs>',
        f'<rect y="{dy}" width="100%" height="100%" fill="{PAPER}"/>',
    ]


def page(slug: str, svg: list[str]) -> str:
    body = "\n".join(svg + ["</svg>"])
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{slug}</title>'
            f'<link href="{FONTS}" rel="stylesheet"><style>*{{margin:0;padding:0}}'
            f'body{{background:{PAPER}}}svg{{display:block}}</style></head><body>\n{body}\n</body></html>\n')




PLACE = {"jev": (16, 32, "start")}
PLOTTED_STATUSES = ("verified", "computed")
CANDIDATES = [(dx, dy, anchor) for dy in (4, -12, 20, -28, 36, -44, 52, -60, 68, -76, 84, 100, 116)
              for dx, anchor in ((12, "start"), (-12, "end"))] + [(0, -16, "middle"), (0, 28, "middle")]
CANDIDATES += [(dx, dy, anchor) for dy in (-28, 36, -44, 52, -60, 68, 84, 100) for dx, anchor in
               ((48, "start"), (-48, "end"), (96, "start"), (-96, "end"))]


LINE = 3


def baseline(y, ly, title, sub, size):
    """Baseline of a label's first line. Labels below or beside a point hang from `ly`; labels above it (ly < 0)
    stand on it, so a stacked title or a subtitle grows upward, away from the point."""
    if ly >= 0:
        return y + ly
    return y + ly - title.count("\n") * (size + LINE) - (18 if sub else 0)


def _box(x, y, dx, ly, anchor, title, sub, size):
    """Bounding box of a label: title lines (at `size` px; several when merged) and an optional 12px mono subtitle."""
    pad = 4
    lines = title.split("\n")
    w = max(max(len(t) for t in lines) * size * 0.62, len(sub) * 12 * 0.62)
    left = {"start": x + dx, "end": x + dx - w, "middle": x + dx - w / 2}[anchor]
    top = baseline(y, ly, title, sub, size)
    extra = (len(lines) - 1) * (size + LINE)
    return (left - pad, top - size + 2 - pad, left + w + pad, top + extra + (22 if sub else 4) + pad)


def merge_close(points: dict, names: dict, radius: float = 14, keep=()) -> tuple[dict, dict]:
    """Dots closer than `radius` can't each carry a readable label, so they share one: the names stacked in the
    dots' top-to-bottom order, placed from the group's centre. Entries in `keep` are never merged."""
    groups: list[list] = []
    for p in points:
        if p in keep:
            groups.append([p])
            continue
        near = [g for g in groups if g[0] not in keep and any(math.dist(points[p], points[q]) < radius for q in g)]
        for g in near:
            groups.remove(g)
        groups.append(sum(near, []) + [p])
    out_points, out_names = {}, {}
    for g in groups:
        g = sorted(g, key=lambda q: points[q][1])
        out_points[g[0]] = (sum(points[q][0] for q in g) / len(g), sum(points[q][1] for q in g) / len(g))
        out_names[g[0]] = "\n".join(names[q] for q in g)
    return out_points, out_names


def _overlap(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _outside(box, bounds):
    inside = (max(box[0], bounds[0]), max(box[1], bounds[1]), min(box[2], bounds[2]), min(box[3], bounds[3]))
    area = (box[2] - box[0]) * (box[3] - box[1])
    return area - _overlap(box, inside) if inside[0] < inside[2] and inside[1] < inside[3] else area


def leader(x, y, offset, box):
    """Where the leader from a point meets its label (the nearest edge), or None for a label level with its point."""
    if offset[1] == 4:
        return None
    return min(max(x, box[0]), box[2]), (box[1] if box[1] > y else box[3])


def _gap(box, x, y):
    """Distance from a point to the nearest part of a box (0 inside it)."""
    return math.hypot(max(box[0] - x, 0, x - box[2]), max(box[1] - y, 0, y - box[3]))


def _dots(a, b, r=2, steps=12):
    """A segment as a run of small boxes, so it can be scored like any other obstacle."""
    return [(a[0] + (b[0] - a[0]) * t / steps - r, a[1] + (b[1] - a[1]) * t / steps - r,
             a[0] + (b[0] - a[0]) * t / steps + r, a[1] + (b[1] - a[1]) * t / steps + r) for t in range(steps + 1)]


def place_labels(points: dict, texts: dict, preferred: dict, bounds=(0, 0, 10**6, 10**6), obstacles=(), rounds=6) -> dict:
    """Place each label at its first candidate offset that avoids other labels, leaders and points."""
    clear = 8
    dots = {p: (x - clear, y - clear, x + clear, y + clear) for p, (x, y) in points.items()}
    options = {p: ([preferred[p]] if p in preferred else []) + CANDIDATES for p in points}

    def geometry(p, o):
        x, y = points[p]
        box = _box(x, y, *o, *texts[p])
        end = leader(x, y, o, box)
        return box, ([] if end is None else _dots((x, y), end))

    def cost(p, o, fixed):
        x, y = points[p]
        box, segment = geometry(p, o)
        mine = (x - 7, y - 7, x + 7, y + 7)
        labels = [b for q, (b, _) in fixed.items() if q != p]
        lines = list(obstacles) + [d for q, (_, seg) in fixed.items() if q != p for d in seg]
        others = [d for q, d in dots.items() if q != p]
        crossing = sum(_overlap(d, t) for d in segment if not _overlap(mine, d) for t in labels + lines + others)
        reach = _gap(box, x, y)
        misread = sum(1 for q, (u, v) in points.items() if q != p and _gap(box, u, v) < reach + 8)
        return (10**5 * _outside(box, bounds) + 100 * sum(_overlap(box, t) for t in labels + others + [mine])
                + 20 * sum(_overlap(box, t) for t in lines) + 2000 * misread + 20 * crossing + 3 * reach)

    def layout(order):
        placed: dict = {}

        def best(p):
            fixed = {q: geometry(q, o) for q, o in placed.items()}
            return min(options[p], key=lambda o: cost(p, o, fixed)), fixed

        for p in order:
            placed[p] = best(p)[0]
        for _ in range(rounds):
            moved = False
            for p in order:
                choice, fixed = best(p)
                if cost(p, choice, fixed) < cost(p, placed[p], fixed):
                    placed[p], moved = choice, True
            if not moved:
                break
        fixed = {q: geometry(q, o) for q, o in placed.items()}
        return sum(cost(p, o, fixed) for p, o in placed.items()), placed

    crowded = {p: sum(math.dist(points[p], points[q]) < 60 for q in points) for p in points}
    orders = [list(points), sorted(points, key=lambda p: -crowded[p]), sorted(points, key=lambda p: points[p]),
              sorted(points, key=lambda p: (-points[p][0], points[p][1])), sorted(points, key=lambda p: points[p][::-1])]
    placed = min((layout(o) for o in orders), key=lambda r: r[0])[1]
    return {p: placed[p] for p in points}


def label_boxes(points: dict, texts: dict, placed: dict) -> dict:
    return {p: _box(*points[p], *placed[p], *texts[p]) for p in points}


def latency_view(summ: dict) -> dict:
    """Self-hosted latency has no network in it, so it is left off the latency axis next to hosted APIs."""
    return {p: v if getattr(info(p), "latency_comparable", True) else {**v, "p50": math.nan} for p, v in summ.items()}


def plottable(entry: str, results_dir: Path = RESULTS_DIR) -> bool:
    """Frontier plots show only entries the maintainers measured (or computed); latency from elsewhere isn't comparable."""
    return results_path(entry, results_dir).exists() and (load_meta(entry, results_dir) or {}).get("status") in PLOTTED_STATUSES


def frontier_scatter(slug, title, summ, front, x_of, x_label, x_lo, x_hi, x_ticks, x_tick_fmt, x_point_fmt):
    """Accuracy against a log-scaled cost or latency axis. API entries are points; the dashed line joins the ones
    on the Pareto frontier. Baselines cost nothing and take no time, so they are listed under the plot."""
    dy = 76
    h = 528 - dy
    a_lo, a_hi = 85.0, 100.0

    def placeable(p):
        v, acc = x_of(summ[p]), summ[p]["acc"]
        return math.isfinite(v) and v > 0 and math.isfinite(acc)

    base = [p for p in summ if info(p).kind == "baseline"]
    others = [p for p in summ if p not in base]
    skipped = [p for p in others if not placeable(p)]
    below = sorted((p for p in others if p not in skipped and 100 * summ[p]["acc"] < a_lo), key=lambda p: -summ[p]["acc"])
    api = [p for p in others if p not in skipped and p not in below]
    name = {p: SHORT.get(p) or short(p) for p in api}
    desc = (f"Scatter plot of accuracy against {x_label.lower()}: "
            + ", ".join(f"{name[p]} {100 * summ[p]['acc']:.1f}% at {x_point_fmt(x_of(summ[p]))}" for p in api)
            + ". A dashed line joins the entries on the Pareto frontier.")
    notes = []
    if base:
        notes.append("Off scale (no API calls): " + ", ".join(f"{label(b)} {100 * summ[b]['acc']:.1f}%" for b in base) + ".")
    if below:
        notes.append(f"Below the {a_lo:.0f}% axis: " + ", ".join(
            f"{SHORT.get(p) or short(p)} {100 * summ[p]['acc']:.1f}%" for p in below) + ".")
    if skipped:
        notes.append("Not plotted on this axis (self-hosted latency, or no usable answers): " + ", ".join(SHORT.get(p) or short(p) for p in skipped) + ".")
    footer = [line for note in notes + ["Dashed line: Pareto frontier."]
              for line in textwrap.wrap(note, int((W - 16 - 112) / (12 * 0.55)), break_on_hyphens=False)]
    h += 18 * (len(footer) - 1)
    s = header(slug, title, desc, h, dy)
    x0, x1, y0, y1 = 112, 824, 416, 136
    lo, hi = math.log10(x_lo), math.log10(x_hi)

    def X(v):
        return round((x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)) / 4) * 4

    def Y(acc):
        return round((y0 - (acc - a_lo) / (a_hi - a_lo) * (y0 - y1)) / 4) * 4

    s.append(text(24, 276, "ACCURACY", 12, MUTED, MONO, 500, "middle", 'letter-spacing="0.14em" transform="rotate(-90 24 276)"'))
    s.append(text((x0 + x1) // 2, 484, x_label.upper(), 12, MUTED, MONO, 500, "middle", 'letter-spacing="0.14em"'))
    for acc in (85, 90, 95, 100):
        y = Y(acc)
        s.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{GRID}" stroke-width="0.8"/>')
        s.append(text(x0 - 12, y + 4, f"{acc}%", 12, MUTED, MONO, 400, "end"))
    for t in x_ticks:
        x = X(t)
        s.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y0}" stroke="{GRID}" stroke-width="0.8"/>')
        s.append(text(x, y0 + 24, x_tick_fmt(t), 12, MUTED, MONO, 400, "middle"))
    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}" stroke="{AXIS}" stroke-width="1"/>')
    s.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{AXIS}" stroke-width="1"/>')

    on = sorted((p for p in api if p in front), key=lambda p: x_of(summ[p]))
    if len(on) > 1:
        pts = " ".join(f"{X(x_of(summ[p]))},{Y(100 * summ[p]['acc'])}" for p in on)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{ACCENT}" stroke-width="1.2" stroke-dasharray="4 4"/>')
    xy = {p: (X(x_of(summ[p])), Y(100 * summ[p]["acc"])) for p in api}
    systems = [p for p in api if info(p).kind == "system"]
    at, names = merge_close(xy, name, keep=systems)
    texts = {p: (names[p], f"{100 * summ[p]['acc']:.1f}% · {x_point_fmt(x_of(summ[p]))}", 16)
             if p in systems else (names[p], "", 13) for p in at}
    order = sorted(at, key=lambda p: p not in systems)
    frontier_line = sorted((xy[p] for p in api if p in front), key=lambda q: q[0])
    line_boxes = [(ax + (bx - ax) * t / 20 - 2, ay + (by - ay) * t / 20 - 2, ax + (bx - ax) * t / 20 + 2,
                   ay + (by - ay) * t / 20 + 2)
                  for (ax, ay), (bx, by) in zip(frontier_line, frontier_line[1:]) for t in range(21)]
    where = place_labels({p: at[p] for p in order}, texts, PLACE, bounds=(8, dy + 8, W - 8, y0 + 40),
                         obstacles=line_boxes)
    dots_at = len(s)
    for p in sorted(api, key=lambda p: p in systems):
        x, y = xy[p]
        r, fill, stroke = (6, "rgba(235,108,54,0.15)", ACCENT) if p in systems else (5, "rgba(79,93,117,0.20)", MUTED)
        s += [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{PAPER}"/>',
              f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>']
    for p in sorted(at, key=lambda p: p in systems):
        x, y = at[p]
        dx, ly, anchor = where[p]
        title, sub, size = texts[p]
        box = _box(x, y, dx, ly, anchor, title, sub, size)
        end = leader(x, y, where[p], box)
        if end is not None:
            lx, ly_edge = end
            s.insert(dots_at, f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{lx:.0f}" y2="{ly_edge:.0f}" stroke="{AXIS}" stroke-width="0.8"/>')
        top = baseline(y, ly, title, sub, size)
        for i, line in enumerate(title.split("\n")):
            s.append(text(x + dx, top + i * (size + LINE), line, size, INK, SANS, 600 if size == 16 else 500, anchor))
        if sub:
            s.append(text(x + dx, top + title.count("\n") * (size + LINE) + 18, sub, 12, MUTED, MONO, 400, anchor))
    for i, line in enumerate(footer):
        s.append(text(x0, 516 + 18 * i, line, 12, SOFT, SANS))
    return page(slug, s), h




def render_png(html: Path, png: Path, height: int) -> None:
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
         f"--window-size={W},{height}", "--virtual-time-budget=8000", f"--screenshot={png}", html.as_uri()],
        check=True, capture_output=True,
    )


def main() -> None:
    load_env()
    items = load_items()
    specs = [e for e in ENTRIES if plottable(e)]
    by_id, common, _, summ = prepare(specs, items)
    fr = fronts(summ)
    DIAGRAMS.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    charts = {
        "cost-vs-accuracy": frontier_scatter(
            "cost-vs-accuracy", "Cost vs accuracy", summ, fr["cost"], lambda v: v["cost_task"] * 1e6,
            "Cost per 1M tasks (log scale)", 2, 1000, (10, 100, 1000), lambda c: f"${c:,}", lambda c: f"${c:,.0f}"),
        "latency-vs-accuracy": frontier_scatter(
            "latency-vs-accuracy", "Latency vs accuracy", latency_view(summ), fr["latency"], lambda v: v["p50"],
            "Median latency per call (log scale)", 100, 10000, (100, 1000, 10000),
            lambda ms: f"{ms:,} ms", lambda ms: f"{ms:,.0f} ms"),
    }
    for name, (html, h) in charts.items():
        src = DIAGRAMS / f"{name}.html"
        src.write_text(html)
        render_png(src, IMG / f"{name}.png", h)
        print(f"docs/img/{name}.png")


if __name__ == "__main__":
    main()
