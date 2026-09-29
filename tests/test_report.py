import asyncio
import json

import pytest

from decidebench.dataset import load_items
from decidebench.paths import results_path
from decidebench.registry import ENTRIES
from decidebench.report import fronts, markers, render, write_block
from decidebench.run import run_system


def few_items(n_pairs=5):
    items = load_items()
    keep = sorted({it.pair_id for it in items})[:n_pairs]
    return [it for it in items if it.pair_id in keep]


def test_write_block_replaces_between_markers(tmp_path):
    s, e = markers("results")
    doc = tmp_path / "README.md"
    doc.write_text(f"# T\n{s}\nold\n{e}\ntail\n")
    write_block(doc, "results", "new table")
    assert doc.read_text() == f"# T\n{s}\nnew table\n{e}\ntail\n"
    with pytest.raises(SystemExit):
        write_block(doc, "family", "x")


def test_fronts_include_zero_cost_baselines():
    summ = {"jev": {"cost_task": 1e-5, "p50": 170.0, "acc": 0.90},
            "deepseek": {"cost_task": 2e-4, "p50": 1900.0, "acc": 0.99},
            "deepseek-41": {"cost_task": 4.5e-4, "p50": 350.0, "acc": 0.992},
            "random": {"cost_task": 0.0, "p50": 0.0, "acc": 0.45}}
    f = fronts(summ)
    assert f["cost"] == {"jev", "deepseek", "deepseek-41", "random"}
    assert f["latency"] == {"jev", "deepseek-41", "random"}


def test_results_table_sorts_by_accuracy_and_keeps_the_floor_last():
    specs = [e for e in ENTRIES if results_path(e).exists()]
    lines = render(specs, load_items())["results"].splitlines()
    assert lines[0] == ("| Entry | Accuracy | Pair accuracy | Zero-shot accuracy | Cost per 1M tasks | Latency p50 | "
                        "Frontier |")
    rows = [l.split(" | ") for l in lines[2:]]
    assert len(rows) == len(specs) and rows[-1][0] == "| Random"
    acc = [float(r[1].rstrip("%")) for r in rows[:-1]]
    assert acc == sorted(acc, reverse=True)
    assert "Time for all" not in lines[0]


def test_zero_shot_column_shows_the_variant_run_or_the_exception(tmp_path):
    items = few_items()
    asyncio.run(run_system("random", items, 2, 0, True, tmp_path))
    rows = [json.loads(l) for l in (tmp_path / "random.jsonl").read_text().splitlines()]
    gold = {it.id: it.gold for it in items}
    (tmp_path / "tev.jsonl").write_text("".join(json.dumps(r | {"key": gold[r["item_id"]], "model": "t"}) + "\n" for r in rows))
    (tmp_path / "variants").mkdir()
    half = {r["item_id"] for r in rows[: len(rows) // 2]}
    (tmp_path / "variants" / "tev.zero_shot.jsonl").write_text("".join(
        json.dumps(r | {"key": gold[r["item_id"]] if r["item_id"] in half else None, "model": "t"}) + "\n" for r in rows))
    zero_shot = {"extra": {"examples_shown": 0, "examples_total": 0}, "model": "l"}
    (tmp_path / "laya-typed.jsonl").write_text("".join(json.dumps(r | zero_shot) + "\n" for r in rows))
    lines = render(["tev", "laya-typed", "random"], items, tmp_path)["results"].splitlines()
    cell = {l.split(" | ")[0].lstrip("| "): l.split(" | ")[3] for l in lines[2:]}
    assert cell["TEV (self-hosted)"] == "50.0%" and cell["Random"] == "–"
    assert cell["Laya typed-decisions 421M (self-hosted)"].endswith("(runs zero-shot)")


def test_family_table_has_one_column_per_family(tmp_path):
    items = few_items(40)
    asyncio.run(run_system("random", items, 2, 0, True, tmp_path))
    lines = render(["random"], items, tmp_path)["family"].splitlines()
    fams = sorted({it.category for it in items})
    assert lines[0] == "| Entry | " + " | ".join(f"`{c}`" for c in fams) + " |" and len(lines) == 3
