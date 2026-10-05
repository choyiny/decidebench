import asyncio
from dataclasses import replace

import pytest

from decidebench.baselines.random import RandomBaseline
from decidebench.dataset import Option, load_items
from decidebench.registry import ENTRIES, get_system, info
from tests.helpers import ITEM


def predict(system, item):
    return asyncio.run(system.predict(None, item))


def test_get_system_specs(monkeypatch):
    monkeypatch.setenv("TOGETHER_API_KEY", "x")
    monkeypatch.setenv("AISPACE_API_KEY", "x")
    assert get_system("tev.zero_shot").name == "tev.zero_shot"
    assert get_system("jev").name == "jev"
    assert get_system("random").name == "random"
    for bad in ("tev.shouty", "tev.careful", "deepseek.zero_shot", "random.zero_shot", "nope"):
        with pytest.raises(ValueError):
            get_system(bad, [ITEM])


def test_info_needs_no_api_keys(monkeypatch):
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    monkeypatch.delenv("AISPACE_API_KEY", raising=False)
    assert [info(e).kind for e in ENTRIES] == ["system"] * 21 + ["reference"] * 3 + ["baseline"]
    assert info("tev.zero_shot") is info("tev")
    assert info("random").pricing.cost(10**6, 10**6) == 0


def test_random_baseline_is_deterministic_per_seed():
    a, b, c = RandomBaseline(0), RandomBaseline(0), RandomBaseline(1)
    items = load_items()[:40]
    ka = [predict(a, it).key for it in items]
    assert ka == [predict(b, it).key for it in items]
    assert ka != [predict(c, it).key for it in items]
    p = predict(a, ITEM)
    assert p.key in ITEM.keys and p.latency_ms == 0 and p.input_tokens == 0
    assert p.probs == pytest.approx({k: 1 / 3 for k in ITEM.keys})


def test_registry_lists_decision_models_then_references(monkeypatch):
    monkeypatch.setenv("TOGETHER_API_KEY", "x")
    assert ENTRIES == ("jev", "clef", "clef-flash", "drex", "tev", "tev-together", "imajev-4b", "yev0-4b", "decider-4b", "jevk5", "kev-4b", "kev-9b",
                       "decider-2b", "laya-typed", "clm", "julia-1", "jeff-800m", "jeff-2b", "jeff-gemma4",
                       "gliner-decide", "nimble-9b", "deepseek", "deepseek-41", "glm-flash", "random")
    assert info("deepseek").kind == "reference"
    with pytest.raises(ValueError):
        get_system("deepseek.zero_shot")