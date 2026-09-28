from dataclasses import replace

import pytest

from decidebench.score import Row, ece, label_metrics, macro, prepare, summarize
from decidebench.types import FREE, Pricing
from tests.helpers import ITEM


def test_label_metrics_precision_recall_and_macro():
    cancel = replace(ITEM, id="support_intent-001b", gold="cancel_subscription")
    other = replace(ITEM, id="ticket_triage-001a", category="ticket_triage", gold="none")
    rows = [
        Row(ITEM, "duplicate_charge", None, 1, 1, 1, "m"),
        Row(ITEM, "cancel_subscription", None, 1, 1, 1, "m"),
        Row(cancel, "cancel_subscription", None, 1, 1, 1, "m"),
        Row(cancel, None, None, 1, 1, 1, "m"),
        Row(other, "none", None, 1, 1, 1, "m"),
    ]
    m = label_metrics(rows)
    dup, can = m[("support_intent", "duplicate_charge")], m[("support_intent", "cancel_subscription")]
    assert (dup["precision"], dup["recall"], dup["support"]) == (1.0, 0.5, 2)
    assert (can["precision"], can["recall"], can["predicted"]) == (0.5, 0.5, 2)
    assert dup["f1"] == pytest.approx(2 / 3)
    assert macro(m, "support_intent")["recall"] == pytest.approx(0.5)
    assert macro(m)["recall"] == pytest.approx((0.5 + 1.0) / 2)


def test_ece_perfectly_calibrated_is_zero():
    rows = [Row(ITEM, "duplicate_charge", {"duplicate_charge": 1.0, "cancel_subscription": 0.0, "none": 0.0},
                1, 1, 1, "m")] * 10
    assert ece(rows) == pytest.approx(0.0)


def test_summarize_prices_billed_tokens_and_times_usable_answers():
    rows = [Row(ITEM, "duplicate_charge", None, 10, 1000, 100, "m"),
            Row(ITEM, "none", None, 30, 3000, 0, "m"),
            Row(ITEM, None, None, 999, 0, 0, "m")]
    s = summarize("x", rows, Pricing(1.0, 10.0, "u", "2026-01-01"))
    assert s["cost_task"] == pytest.approx((0.002 + 0.003 + 0.0) / 3)
    assert s["p50"] == pytest.approx(20)
    assert s["entry"] == "x" and s["unusable"] == pytest.approx(1 / 3)
    assert summarize("b", rows, FREE)["cost_task"] == 0


def test_prepare_scores_only_items_every_entry_answered(tmp_path):
    import json

    b = replace(ITEM, id="support_intent-001b", gold="cancel_subscription", state="Cancel it.")
    for spec, ids in (("random", [ITEM.id, b.id]), ("tev", [ITEM.id])):
        (tmp_path / f"{spec}.jsonl").write_text("".join(
            json.dumps({"item_id": i, "key": "none", "probs": None, "latency_ms": 0.0,
                        "input_tokens": 0, "output_tokens": 0, "model": spec}) + "\n" for i in ids))
    _, common, rows, summ = prepare(["random", "tev"], [ITEM, b], tmp_path)
    assert common == [ITEM.id]
    assert summ["random"]["n"] == 1 and summ["random"]["cost_task"] == 0


def test_summarize_averages_examples_shown():
    rows = [Row(ITEM, "none", None, 1, 1, 1, "m", {"examples_shown": 2, "examples_total": 3}),
            Row(ITEM, "none", None, 1, 1, 1, "m", {"examples_shown": 3, "examples_total": 3})]
    s = summarize("x", rows, FREE)
    assert (s["examples_shown"], s["examples_total"]) == (2.5, 3.0)
    assert summarize("x", [Row(ITEM, "none", None, 1, 1, 1, "m")], FREE)["examples_shown"] is None


def test_gpu_hours_cost_comes_from_wall_clock_not_tokens():
    import math

    from decidebench.types import Pricing

    p = Pricing(0.0, 0.0, "u", "2026-09-28", basis="gpu_hours", gpu="NVIDIA L4", hourly_usd=0.81)
    assert math.isnan(p.cost(1000, 10))
    rows = [Row(ITEM, "none", None, 100.0, 500, 0, "m")] * 4
    assert summarize("x", rows, p, wall_seconds=3600.0, items=400)["cost_task"] == pytest.approx(0.81 / 400)
    assert math.isnan(summarize("x", rows, p)["cost_task"])
