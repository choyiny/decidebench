"""Pareto frontiers: which entries no other entry beats on both axes at once."""

from __future__ import annotations

import math


def pareto_front(points: dict[str, tuple[float, float]]) -> set[str]:
    """Names of non-dominated points. Each point is (cost-like, accuracy-like): lower first value is better,
    higher second value is better. A point is dominated if another is at least as good on both and strictly
    better on one, so identical points are both kept. Points with a NaN coordinate are left out."""
    ok = {n: p for n, p in points.items() if not any(math.isnan(v) for v in p)}
    front = set()
    for n, (c, a) in ok.items():
        dominated = any(c2 <= c and a2 >= a and (c2 < c or a2 > a) for m, (c2, a2) in ok.items() if m != n)
        if not dominated:
            front.add(n)
    return front
