import json

from decidebench.paths import V2_RESULTS_DIR, results_path
from decidebench.registry import ENTRIES
from decidebench.space import export


def test_space_carries_every_entry_with_its_numbers(tmp_path):
    out = export(tmp_path / "space")
    card = (out / "README.md").read_text()
    assert card.startswith("---\n") and "sdk: static" in card and "app_file: index.html" in card
    rows = json.loads((out / "leaderboard-v1.json").read_text())
    specs = [e for e in ENTRIES if results_path(e).exists()]
    assert [r["entry"] for r in rows["entries"]] == specs
    jev = next(r for r in rows["entries"] if r["entry"] == "jev")
    assert jev["kind"] == "decision model" and jev["hosting"] == "API" and 0.97 < jev["accuracy"] < 0.99
    assert jev["zero_shot"] is not None and set(jev["families"]) == set(rows["families"]) and len(rows["families"]) == 8
    gemma = next(r for r in rows["entries"] if r["entry"] == "jeff-gemma4")
    assert gemma["hosting"] == "self-hosted" and gemma["cost_per_1m"] > 0
    fast = next(r for r in rows["entries"] if r["entry"] == "s1-fast")
    assert fast["hosting"] == "API" and "cost" in fast["frontier"]
    html = (out / "index.html").read_text()
    assert "leaderboard.json" in html and "img/cost-vs-accuracy.png" in html
    assert (out / "img" / "cost-vs-accuracy.png").exists()


def test_space_prints_percentages_exactly_as_the_readme(tmp_path):
    rows = json.loads((export(tmp_path / "space") / "leaderboard-v1.json").read_text())["entries"]
    ds41 = next(r for r in rows if r["entry"] == "deepseek-41")
    assert ds41["shown"]["accuracy"] == "99.2%"
    assert "pct(" not in (tmp_path / "space" / "index.html").read_text()


def test_space_defaults_to_v2_with_the_reference_and_gpu_pricing(tmp_path):
    out = export(tmp_path / "space")
    rows = json.loads((out / "leaderboard.json").read_text())
    assert rows["version"] == "v2.0" and rows["items"] == 450 and len(rows["families"]) == 9
    assert [r["entry"] for r in rows["entries"]] == [e for e in ENTRIES if results_path(e, V2_RESULTS_DIR).exists()]
    opus = next(r for r in rows["entries"] if r["entry"] == "claude-opus-4-8")
    assert opus["kind"] == "chat LLM" and opus["company"] == "Anthropic" and opus["accuracy"] > 0.99
    yev1 = next(r for r in rows["entries"] if r["entry"] == "yev1-4b")
    assert yev1["hosting"] == "self-hosted" and "self-hosted cost" in yev1["frontier"] and 60 < yev1["cost_per_1m"] < 80
    html = (out / "index.html").read_text()
    assert 'load("v2")' in html and "leaderboard-v1.json" in html
