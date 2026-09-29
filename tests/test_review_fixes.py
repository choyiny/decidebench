"""Regression tests for the final-review findings: meta provenance, status defaults, resume, chart robustness."""

import asyncio
import json
import math

from decidebench import registry
from decidebench import charts
from decidebench.meta import build_meta, load_meta, write_meta
from decidebench.run import run_system
from tests.test_run import ten_items


def test_noop_rerun_leaves_meta_untouched(tmp_path):
    items = ten_items()
    asyncio.run(run_system("random", items, 2, 0, True, tmp_path))
    meta = load_meta("random", tmp_path) | {"run_date": "2026-09-25", "harness_commit": "jev-vs-tev@f8dc0b1"}
    write_meta(meta, tmp_path)
    asyncio.run(run_system("random", items, 2, 0, False, tmp_path))
    assert load_meta("random", tmp_path) == meta


def test_api_entries_default_to_self_reported():
    assert build_meta("jev", "jev-1", concurrency=4, warmup=3)["status"] == "self_reported"
    assert build_meta("jev", "jev-1", concurrency=4, warmup=3, status="verified")["status"] == "verified"
    assert build_meta("random", "r", concurrency=4, warmup=0)["status"] == "computed"


def test_resume_keeps_unusable_output_but_retries_failed_calls(tmp_path):
    items = ten_items()
    asyncio.run(run_system("random", items, 2, 0, True, tmp_path))
    path = tmp_path / "random.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines()]
    rows[0] |= {"key": None, "error": "unparseable reply 'maybe'"}
    rows[1] |= {"key": None, "error": "ConnectTimeout: timed out", "extra": {"call_failed": True}}
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    asyncio.run(run_system("random", items, 2, 0, False, tmp_path))
    after = {r["item_id"]: r for r in map(json.loads, path.read_text().splitlines())}
    assert len(after) == len(items)
    assert after[rows[0]["item_id"]]["key"] is None
    assert after[rows[1]["item_id"]]["key"] is not None


SUMM = {"tev": {"cost_task": 1e-5, "p50": math.nan, "acc": 0.90},
        "jev": {"cost_task": 0.0, "p50": 459.0, "acc": 0.972},
        "deepseek-41": {"cost_task": 1.7e-3, "p50": 2477.0, "acc": 0.992}}


def test_frontier_scatter_skips_points_it_cannot_place():
    for x_of in (lambda v: v["p50"], lambda v: v["cost_task"] * 1e6):
        html, _ = charts.frontier_scatter("s", "t", SUMM, set(SUMM), x_of, "X (log scale)", 1, 10000, (10, 100),
                                   str, lambda v: f"{v:,.0f}")
        assert "DeepSeek-V4.1-Flash" in html and "Not plotted" in html


def test_frontier_scatter_draws_entries_added_to_the_registry(monkeypatch):
    class Acme:
        label, kind = "Acme Decide (Acme API)", "system"

    monkeypatch.setitem(registry.CLASSES, "acme", Acme)
    summ = {"deepseek-41": SUMM["deepseek-41"], "acme": {"cost_task": 2e-5, "p50": 300.0, "acc": 0.95}}
    html, _ = charts.frontier_scatter("s", "t", summ, set(summ), lambda v: v["p50"], "X (log scale)", 100, 10000,
                               (100, 1000), str, str)
    assert "Acme Decide" in html


def test_plots_admit_only_verified_or_computed_entries(tmp_path):
    for entry in ("tev", "jev", "deepseek", "random"):
        (tmp_path / f"{entry}.jsonl").write_text("{}\n")
    for entry, status in (("tev", "verified"), ("jev", "self-reported"), ("random", "computed")):
        write_meta(build_meta(entry, "m", concurrency=4, warmup=0, status=status, harness_commit="x"), tmp_path)
    assert [e for e in ("tev", "jev", "deepseek", "random") if charts.plottable(e, tmp_path)] == ["tev", "random"]
