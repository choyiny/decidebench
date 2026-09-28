"""Metrics: accuracy with a pair bootstrap CI, pair accuracy, per-label P/R/F1 with family-weighted macros,
calibration, latency percentiles and cost per task. Rendering lives in report.py."""

from __future__ import annotations

import json
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from decidebench.dataset import Item
from decidebench.paths import RESULTS_DIR, results_path
from decidebench.registry import info
from decidebench.types import Pricing


@dataclass
class Row:
    item: Item
    key: str | None
    probs: dict[str, float] | None
    latency_ms: float
    input_tokens: int
    output_tokens: int
    model: str
    extra: dict = field(default_factory=dict)

    @property
    def correct(self) -> bool:
        return self.key == self.item.gold


def load_rows(path: Path, items: dict[str, Item]) -> dict[str, Row]:
    rows: dict[str, Row] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["item_id"] in items:
            rows[r["item_id"]] = Row(
                items[r["item_id"]], r["key"], r.get("probs"), r["latency_ms"],
                r["input_tokens"], r["output_tokens"], r["model"], r.get("extra") or {},
            )
    return rows


def pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = (len(xs) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def pair_bootstrap_ci(rows: list[Row], n: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% CI for accuracy, resampling whole pairs since the two halves aren't independent."""
    by_pair: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        by_pair[r.item.pair_id].append(r.correct)
    groups = list(by_pair.values())
    rng = random.Random(seed)
    accs = []
    for _ in range(n):
        sample = [rng.choice(groups) for _ in groups]
        accs.append(sum(sum(g) for g in sample) / sum(len(g) for g in sample))
    return pct(accs, 0.025), pct(accs, 0.975)


def ece(rows: list[Row], bins: int = 10) -> float | None:
    """Expected calibration error of the top-choice probability."""
    pts = [(max(r.probs.values()), r.correct) for r in rows if r.probs and r.key]
    if len(pts) < len(rows) * 0.9:
        return None
    total = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [(p, c) for p, c in pts if lo < p <= hi or (b == 0 and p == 0)]
        if bucket:
            conf = statistics.fmean(p for p, _ in bucket)
            acc = statistics.fmean(c for _, c in bucket)
            total += len(bucket) / len(pts) * abs(conf - acc)
    return total


def brier(rows: list[Row]) -> float | None:
    scored = [r for r in rows if r.probs]
    if len(scored) < len(rows) * 0.9:
        return None
    return statistics.fmean(
        sum((r.probs.get(k, 0.0) - (k == r.item.gold)) ** 2 for k in r.item.keys) for r in scored
    )


def label_metrics(rows: list[Row]) -> dict[tuple[str, str], dict]:
    """One-vs-rest precision, recall and F1 per (family, label); unusable output counts as a miss."""
    counts: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        cat, gold = r.item.category, r.item.gold
        if r.key == gold:
            counts[(cat, gold)][0] += 1
        else:
            counts[(cat, gold)][2] += 1
            if r.key is not None:
                counts[(cat, r.key)][1] += 1
    out = {}
    for label, (tp, fp, fn) in counts.items():
        p = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        out[label] = {"support": tp + fn, "predicted": tp + fp, "precision": p, "recall": rec,
                      "f1": 2 * p * rec / (p + rec) if p + rec else 0.0}
    return out


def macro(metrics: dict[tuple[str, str], dict], category: str | None = None) -> dict[str, float]:
    """Unweighted mean over labels, then over families, so rare labels and small families count equally."""
    keys = ("precision", "recall", "f1")
    if category is None:
        fams = [macro(metrics, c) for c in sorted({c for c, _ in metrics})]
        return {k: statistics.fmean(f[k] for f in fams) for k in keys}
    ms = [m for (cat, _), m in metrics.items() if cat == category]
    return {k: statistics.fmean(m[k] for m in ms) for k in keys}


def summarize(spec: str, rows: list[Row], pricing: Pricing, wall_seconds: float | None = None,
              items: int | None = None) -> dict:
    n = len(rows)
    by_pair: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        by_pair[r.item.pair_id].append(r.correct)
    full_pairs = [v for v in by_pair.values() if len(v) == 2]
    lat = [r.latency_ms for r in rows if r.key]
    per_label = label_metrics(rows)
    mac = macro(per_label)
    shown = [r.extra["examples_shown"] for r in rows if "examples_shown" in r.extra]
    total = [r.extra["examples_total"] for r in rows if "examples_total" in r.extra]
    return {
        "entry": spec,
        "model": statistics.mode(r.model for r in rows),
        "n": n,
        "acc": sum(r.correct for r in rows) / n,
        "ci": pair_bootstrap_ci(rows),
        "pair_acc": sum(all(v) for v in full_pairs) / len(full_pairs) if full_pairs else float("nan"),
        "labels": per_label,
        "macro_p": mac["precision"],
        "macro_r": mac["recall"],
        "macro_f1": mac["f1"],
        "unusable": sum(r.key is None for r in rows) / n,
        "p50": pct(lat, 0.5),
        "p95": pct(lat, 0.95),
        "avg_in": statistics.fmean(r.input_tokens for r in rows),
        "avg_out": statistics.fmean(r.output_tokens for r in rows),
        "cost_task": (
            (wall_seconds * pricing.hourly_usd / 3600 / items if wall_seconds is not None and items else math.nan)
            if pricing.basis == "gpu_hours"
            else statistics.fmean(pricing.cost(r.input_tokens, r.output_tokens) for r in rows)
        ),
        "ece": ece(rows),
        "brier": brier(rows),
        "examples_shown": statistics.fmean(shown) if shown else None,
        "examples_total": statistics.fmean(total) if total else None,
    }


def prepare(specs: list[str], items: list[Item], results_dir: Path = RESULTS_DIR):
    """Load every spec's results and score only the items all of them answered (or failed on)."""
    by_id = {it.id: it for it in items}
    all_rows = {s: load_rows(results_path(s, results_dir), by_id) for s in specs}
    common = sorted(set.intersection(*(set(r) for r in all_rows.values())))
    rows = {s: [all_rows[s][i] for i in common] for s in specs}
    from decidebench.meta import load_meta

    summ = {}
    for s in specs:
        m = load_meta(s, results_dir) or {}
        summ[s] = summarize(s, rows[s], info(s).pricing, wall_seconds=m.get("wall_seconds"), items=m.get("items"))
    return by_id, common, rows, summ
