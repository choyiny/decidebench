import json
import math

import pytest

from decidebench import prompts
from decidebench.systems import jev, tev
from decidebench.types import Pricing
from tests.helpers import ITEM


def test_pricing_cost_is_usd_per_million_tokens():
    p = Pricing(1.0, 10.0, "https://example.com", "2026-01-01")
    assert p.cost(1000, 100) == pytest.approx(0.002)
    assert p.basis == "list_price"


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("A", "duplicate_charge"),
        (" B.", "cancel_subscription"),
        ("(C)", "none"),
        ('{"label": "B", "key": "cancel_subscription"}', "cancel_subscription"),
        ("none", "none"),
        ("D", None),
        ("I think", None),
        ("", None),
    ],
)
def test_parse_letter(reply, expected):
    assert prompts.parse_letter(ITEM, reply) == expected


def test_tev_body_matches_launch_post_settings():
    body = tev.build_body(ITEM, "together/Tev1-4B-experimental", logprobs=0)
    assert body["temperature"] == 0
    assert body["max_tokens"] == 8
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert "logprobs" not in body
    with_lp = tev.build_body(ITEM, "m", logprobs=5)
    assert (with_lp["logprobs"], with_lp["top_logprobs"]) == (True, 5)
    user = json.loads(body["messages"][1]["content"])
    assert [o["label"] for o in user["options"]] == ["A", "B", "C"]
    assert user["options"][0]["key"] == "duplicate_charge"


def test_tev_letter_probs_from_both_logprob_shapes():
    openai_shape = {"logprobs": {"content": [{"token": "A", "logprob": -0.1, "top_logprobs": [
        {"token": "A", "logprob": math.log(0.6)}, {"token": "B", "logprob": math.log(0.2)},
        {"token": "Hello", "logprob": math.log(0.2)}]}]}}
    together_shape = {"logprobs": {"tokens": ["A"], "token_logprobs": [-0.1],
                                   "top_logprobs": [{"A": math.log(0.6), " B": math.log(0.2)}]}}
    for choice in (openai_shape, together_shape):
        probs = tev.letter_probs(ITEM, tev.first_token_top_logprobs(choice))
        assert probs["duplicate_charge"] == pytest.approx(0.75)
        assert probs["cancel_subscription"] == pytest.approx(0.25)
        assert probs["none"] == 0
    assert tev.letter_probs(ITEM, tev.first_token_top_logprobs({})) is None


def test_jev_body_is_choice_question():
    body = jev.build_body(ITEM, "jev-latest")
    q = body["questions"][jev.QUESTION_ID]
    assert body["state"] == ITEM.state
    assert q["type"] == "choice"
    assert q["criteria"] == {o.key: o.description for o in ITEM.options}


def test_jev_parse_response():
    data = {"answers": {"decision": {"type": "choice", "choice": "none",
                                     "probabilities": {"duplicate_charge": 0.3, "cancel_subscription": 0.1, "none": 0.6},
                                     "confidence": 0.5}}}
    key, probs, err = jev.parse_response(ITEM, data)
    assert (key, err) == ("none", None)
    assert probs["none"] == 0.6
    assert jev.parse_response(ITEM, {"answers": {"decision": {"choice": "bogus"}}})[0] is None
    assert jev.parse_response(ITEM, {})[2] == "missing answer"


def test_adapter_declarations_are_readable_without_api_keys(monkeypatch):
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    monkeypatch.delenv("AISPACE_API_KEY", raising=False)
    assert (tev.TevSystem.kind, jev.JevSystem.kind) == ("system", "system")
    assert tev.TevSystem.pricing.basis == "gpu_hours"
    assert jev.JevSystem.pricing.input_per_mtok == 0.042
    assert jev.JevSystem.gateway_hop and not tev.TevSystem.gateway_hop


def test_together_references_are_declared_and_keyless(monkeypatch):
    from decidebench.references.together import DeepSeekSystem

    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    assert DeepSeekSystem.kind == "reference" and DeepSeekSystem.model == "deepseek-ai/DeepSeek-V4-Flash-0731"
    assert (DeepSeekSystem.pricing.input_per_mtok, DeepSeekSystem.pricing.output_per_mtok) == (0.14, 0.28)
    assert not DeepSeekSystem.gateway_hop and "Together" in DeepSeekSystem.endpoint


def test_together_references_call_together_with_the_tev_prompt(monkeypatch):
    monkeypatch.setattr(fewshot, "for_item", lambda item, pool=None: [])
    import asyncio

    import httpx

    from decidebench.references.together import DeepSeekSystem

    monkeypatch.setenv("TOGETHER_API_KEY", "k")
    seen = {}

    def handler(request):
        seen["url"], seen["auth"], seen["body"] = str(request.url), request.headers["authorization"], json.loads(request.content)
        return httpx.Response(200, json={"model": "deepseek-ai/DeepSeek-V4-Flash-0731",
                                         "choices": [{"message": {"content": "B"}}],
                                         "usage": {"prompt_tokens": 264, "completion_tokens": 245}})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await DeepSeekSystem().predict(client, ITEM)

    pred = asyncio.run(go())
    assert seen["url"] == "https://api.together.ai/v1/chat/completions" and seen["auth"] == "Bearer k"
    assert seen["body"]["messages"] == prompts.build_messages(ITEM)
    assert (seen["body"]["temperature"], seen["body"]["max_tokens"]) == (0, 4096)
    assert (pred.key, pred.input_tokens, pred.output_tokens, pred.provider) == ("cancel_subscription", 264, 245, "deepseek")


TOGETHER_LIST_PRICES = {
    "deepseek": ("deepseek-ai/DeepSeek-V4-Flash-0731", 0.14, 0.28),
    "glm-flash": ("zai-org/GLM-5.3-Flash", 0.15, 0.50),
    "deepseek-41": ("deepseek-ai/DeepSeek-V4.1-Flash", 0.30, 1.20),
}


@pytest.mark.parametrize("entry", sorted(TOGETHER_LIST_PRICES))
def test_every_together_reference_declares_model_and_list_price(entry):
    from decidebench.registry import info

    cls = info(entry)
    model, p_in, p_out = TOGETHER_LIST_PRICES[entry]
    assert (cls.name, cls.model, cls.kind, cls.gateway_hop) == (entry, model, "reference", False)
    assert (cls.pricing.input_per_mtok, cls.pricing.output_per_mtok) == (p_in, p_out)
    assert cls.label.endswith("(Together)")


from dataclasses import replace as _replace

from decidebench import fewshot

SHOTS = [
    _replace(ITEM, id="support_intent-t01-none", pair_id="support_intent-t01", difficulty="example", gold="none",
             state="Where is your nearest store to the harbour district?"),
    _replace(ITEM, id="support_intent-t01-duplicate_charge", pair_id="support_intent-t01", difficulty="example",
             gold="duplicate_charge", state="Two identical charges hit my card yesterday for one order."),
]


def test_chat_examples_are_prior_turns_with_letter_answers():
    msgs = prompts.build_messages(ITEM, examples=SHOTS)
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user", "assistant", "user"]
    assert (msgs[2]["content"], msgs[4]["content"]) == ("C", "A")
    assert json.loads(msgs[1]["content"])["state"] == SHOTS[0].state
    assert json.loads(msgs[-1]["content"])["state"] == ITEM.state
    assert prompts.build_messages(ITEM) == prompts.build_messages(ITEM, examples=())


def test_jev_examples_go_after_the_question_in_instructions():
    body = jev.build_body(ITEM, "m", examples=SHOTS, examples_in="instructions")
    assert body["questions"][jev.QUESTION_ID]["instructions"] == ITEM.question + "\n\n" + fewshot.as_text(SHOTS)
    assert body["state"] == ITEM.state


def test_jev_examples_go_in_each_options_criteria_as_typesafe_documents():
    q = jev.build_body(ITEM, "m", examples=SHOTS, examples_in="criteria")["questions"][jev.QUESTION_ID]
    assert q["instructions"] == ITEM.question
    by_gold = {s.gold: s.state for s in SHOTS}
    for o in ITEM.options:
        entry = q["criteria"][o.key]
        if o.key in by_gold:
            assert entry == {"what": o.description, "examples": [by_gold[o.key]]}
        else:
            assert entry == o.description
    assert jev.JevSystem.examples_in == "criteria"


def test_laya_examples_go_after_the_state_so_truncation_drops_them_first():
    body = jev.build_body(ITEM, "m", examples=SHOTS, examples_in="state")
    assert body["state"] == ITEM.state + "\n\n" + fewshot.as_text(SHOTS, fewshot.LAYA_HEADER)
    assert body["questions"][jev.QUESTION_ID]["instructions"] == ITEM.question


def test_tev_passes_examples_into_messages():
    body = tev.build_body(ITEM, "m", 0, examples=SHOTS)
    assert len(body["messages"]) == 6 and body["max_tokens"] == 8


def test_zero_shot_variant_sends_no_examples(monkeypatch):
    import asyncio

    import httpx

    monkeypatch.setattr(fewshot, "for_item", lambda item, pool=None: SHOTS)
    monkeypatch.setenv("TOGETHER_API_KEY", "k")
    monkeypatch.setenv("AISPACE_API_KEY", "k")
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        if "messages" in bodies[-1]:
            return httpx.Response(200, json={"model": "t", "choices": [{"message": {"content": "A"}}], "usage": {}})
        return httpx.Response(200, json={"answers": {"decision": {"choice": "none"}}, "usage": {}})

    async def go(system):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await system.predict(client, ITEM)

    from decidebench.registry import get_system

    tev_pred = asyncio.run(go(get_system("tev.zero_shot")))
    jev_pred = asyncio.run(go(get_system("jev.zero_shot")))
    assert len(bodies[0]["messages"]) == 2
    assert bodies[1]["questions"][jev.QUESTION_ID]["instructions"] == ITEM.question
    assert tev_pred.extra["examples_total"] == jev_pred.extra["examples_total"] == 0


def test_tev_on_together_is_a_hosted_entry_with_the_same_prompt(monkeypatch):
    from decidebench.registry import get_system, info

    monkeypatch.setenv("TOGETHER_API_KEY", "k")
    hosted, local = get_system("tev-together"), get_system("tev")
    assert hosted.url == "https://api.together.ai/v1/chat/completions"
    assert hosted.headers == {"Authorization": "Bearer k"} and hosted.model == "together/Tev1-4B-experimental"
    assert (hosted.name, info("tev-together").label) == ("tev-together", "TEV (Together)")
    p = info("tev-together").pricing
    assert (p.basis, p.input_per_mtok, p.output_per_mtok) == ("list_price", 0.042, 0.0)
    assert info("tev-together").latency_comparable is True and info("tev-together").kind == "system"
    assert tev.build_body(ITEM, hosted.model, 0)["messages"] == tev.build_body(ITEM, local.model, 0)["messages"]


@pytest.mark.parametrize("entry,price", [("clef", 0.24), ("clef-flash", 0.09)])
def test_clef_calls_ai_space_systemone_with_its_own_model_and_jev_examples(monkeypatch, entry, price):
    import asyncio

    import httpx

    from decidebench.registry import get_system, info

    monkeypatch.setattr(fewshot, "for_item", lambda item, pool=None: SHOTS)
    monkeypatch.setenv("AISPACE_API_KEY", "k")
    monkeypatch.setenv("JEV_MODEL", "jev-latest")
    seen = []

    def handler(request):
        seen.append((str(request.url), json.loads(request.content)))
        return httpx.Response(200, json={"model": entry, "answers": {"decision": {"choice": ITEM.options[0].key}},
                                         "usage": {"input_tokens": 1000, "output_tokens": 0}})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await get_system(entry).predict(client, ITEM)

    pred = asyncio.run(go())
    url, body = seen[0]
    assert url == "https://ai.xyspace.dev/v1/systemone" and body["model"] == entry
    criteria = body["questions"][jev.QUESTION_ID]["criteria"]
    assert any(isinstance(v, dict) and v["examples"] for v in criteria.values())
    assert pred.key == ITEM.options[0].key and pred.extra["examples_total"] == len(SHOTS)
    cls = info(entry)
    assert cls.kind == "system" and cls.latency_comparable and cls.gateway_hop
    assert (cls.pricing.input_per_mtok, cls.pricing.output_per_mtok) == (price, 0.0)
    assert cls.pricing.source.startswith("https://developers.cloudflare.com/")


def test_drex_calls_its_own_systemone_with_examples_in_the_instructions(monkeypatch):
    import asyncio

    import httpx

    from decidebench.registry import get_system, info

    monkeypatch.setattr(fewshot, "for_item", lambda item, pool=None: SHOTS)
    monkeypatch.setenv("DREX_API_KEY", "k")
    seen = []

    def handler(request):
        seen.append((str(request.url), request.headers["authorization"], json.loads(request.content)))
        return httpx.Response(200, json={"model": "drex-v1.5", "answers": {"decision": {"choice": ITEM.options[0].key}},
                                         "usage": {"input_tokens": 1000, "output_tokens": 24}})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await get_system("drex").predict(client, ITEM)

    pred = asyncio.run(go())
    url, auth, body = seen[0]
    assert (url, auth, body["model"]) == ("https://drex.nace.ai/v1/systemone", "Bearer k", "drex-v1.5")
    question = body["questions"][jev.QUESTION_ID]
    assert all(isinstance(v, str) for v in question["criteria"].values())
    assert question["instructions"].startswith(ITEM.question) and len(question["instructions"]) > len(ITEM.question)
    assert pred.key == ITEM.options[0].key and pred.extra["examples_total"] == len(SHOTS)
    cls = info("drex")
    assert cls.kind == "system" and cls.latency_comparable and not cls.gateway_hop
    assert (cls.pricing.input_per_mtok, cls.pricing.output_per_mtok) == (0.05, 0.0)


def test_openai_decisions_asks_one_choice_question_with_examples_in_the_instructions(monkeypatch):
    import asyncio

    import httpx

    from decidebench.registry import get_system, info
    from decidebench.systems import openai_decisions

    monkeypatch.setattr(fewshot, "for_item", lambda item, pool=None: SHOTS)
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    gold = ITEM.options[0].key
    seen = []

    def handler(request):
        seen.append((str(request.url), request.headers["authorization"], json.loads(request.content)))
        return httpx.Response(200, json={
            "model": "gpt-6-luna",
            "answers": [{"type": "choice", "name": "decision", "choice": gold, "confidence": 0.9,
                         "probabilities": [{"value": o.key, "probability": 0.8 if o.key == gold else 0.1}
                                           for o in ITEM.options]}],
            "usage": {"input_tokens": 500, "output_tokens": 0, "total_tokens": 500}})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await get_system("openai-decisions").predict(client, ITEM)

    pred = asyncio.run(go())
    url, auth, body = seen[0]
    assert (url, auth, body["model"], body["input"]) == ("https://api.openai.com/v1/decisions", "Bearer k", "gpt-6-luna",
                                                         ITEM.state)
    [question] = body["questions"]
    assert (question["type"], question["name"]) == ("choice", "decision")
    assert question["choices"] == [{"value": o.key, "description": o.description} for o in ITEM.options]
    assert question["instructions"].startswith(ITEM.question) and len(question["instructions"]) > len(ITEM.question)
    assert pred.key == gold and pred.error is None and pred.probs[gold] == pytest.approx(0.8)
    assert (pred.input_tokens, pred.extra["confidence"], pred.extra["examples_total"]) == (500, 0.9, len(SHOTS))
    cls = info("openai-decisions")
    assert cls.kind == "system" and cls.latency_comparable and not cls.gateway_hop
    assert (cls.pricing.input_per_mtok, cls.pricing.output_per_mtok) == (0.10, 0.0)


def test_openai_decisions_refusal_and_unknown_choice_are_unusable():
    from decidebench.systems.openai_decisions import parse_response

    assert parse_response(ITEM, {"answers": [{"type": "refusal", "name": "decision"}]}) == (None, None, "refusal")
    assert parse_response(ITEM, {"answers": []}) == (None, None, "missing answer")
    key, _, error = parse_response(ITEM, {"answers": [{"type": "choice", "name": "decision", "choice": "nope"}]})
    assert key is None and "not an option" in error


def test_openai_decisions_zero_shot_sends_only_the_question(monkeypatch):
    import asyncio

    import httpx

    from decidebench.registry import get_system

    monkeypatch.setattr(fewshot, "for_item", lambda item, pool=None: SHOTS)
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"answers": [{"type": "choice", "name": "decision", "choice": "none"}]})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await get_system("openai-decisions.zero_shot").predict(client, ITEM)

    pred = asyncio.run(go())
    assert bodies[0]["questions"][0]["instructions"] == ITEM.question
    assert pred.provider == "openai-decisions.zero_shot" and pred.extra["examples_total"] == 0
