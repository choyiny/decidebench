import json

from decidebench.paths import results_path
from decidebench.registry import ENTRIES
from decidebench.space import export


def test_space_carries_every_entry_with_its_numbers(tmp_path):
    out = export(tmp_path / "space")
    card = (out / "README.md").read_text()
    assert card.startswith("---\n") and "sdk: static" in card and "app_file: index.html" in card
    rows = json.loads((out / "leaderboard.json").read_text())
    specs = [e for e in ENTRIES if results_path(e).exists()]
    assert [r["entry"] for r in rows["entries"]] == specs
    jev = next(r for r in rows["entries"] if r["entry"] == "jev")
    assert jev["kind"] == "decision model" and jev["hosting"] == "API" and 0.97 < jev["accuracy"] < 0.99
    assert jev["zero_shot"] is not None and set(jev["families"]) == set(rows["families"]) and len(rows["families"]) == 8
    imajev = next(r for r in rows["entries"] if r["entry"] == "imajev-4b")
    assert imajev["hosting"] == "self-hosted" and imajev["cost_per_1m"] > 0 and "cost" in imajev["frontier"]
    html = (out / "index.html").read_text()
    assert "leaderboard.json" in html and "img/cost-vs-accuracy.png" in html
    assert (out / "img" / "cost-vs-accuracy.png").exists()


def test_space_prints_percentages_exactly_as_the_readme(tmp_path):
    rows = json.loads((export(tmp_path / "space") / "leaderboard.json").read_text())["entries"]
    ds41 = next(r for r in rows if r["entry"] == "deepseek-41")
    assert ds41["shown"]["accuracy"] == "99.2%"
    assert "pct(" not in (tmp_path / "space" / "index.html").read_text()
