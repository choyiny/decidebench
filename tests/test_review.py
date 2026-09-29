import json

from decidebench.fewshot import load_examples
from decidebench.paths import ROOT
from decidebench.report import markers
from decidebench.registry import ENTRIES
from decidebench.review import REVIEWERS, REVIEW_DIR, load_answers, summary


def test_summary_counts_agreement_and_flags_examples_both_models_reject():
    gold = {"a": "x", "b": "y", "c": "z"}
    answers = {"m1": {"a": "x", "b": "y", "c": "q"}, "m2": {"a": "x", "b": "q", "c": "q"}}
    lines = summary(gold, answers, labels={"m1": "Model One", "m2": "Model Two"})
    text = "\n".join(lines)
    assert "| Model One agrees with the label | 2 / 3 |" in text
    assert "| Model Two agrees with the label | 1 / 3 |" in text
    assert "| Both models disagree with the label | 1 (`c`) |" in text


def test_committed_review_covers_every_example_and_matches_review_md():
    gold = {e.id: e.gold for e in load_examples()}
    answers = load_answers()
    assert set(answers) == set(REVIEWERS)
    for model, got in answers.items():
        assert set(got) == set(gold), model
    start, end = markers("review")
    doc = (ROOT / "data" / "v1" / "examples" / "REVIEW.md").read_text()
    block = doc.split(start, 1)[1].split(end, 1)[0].strip()
    assert block == "\n".join(summary(gold, answers))
    assert all(p.suffix == ".jsonl" for p in REVIEW_DIR.iterdir())


def test_reviewers_are_not_benchmark_entries():
    assert not set(REVIEWERS) & set(ENTRIES)
    models = {r.model for r in REVIEWERS.values()}
    assert models == {"zai-org/GLM-5.3", "kimi-k3"}
