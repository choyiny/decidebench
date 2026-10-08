"""OpenAI's Decisions API (`POST /v1/decisions`, gpt-6-luna), asked as one `choice` question.

Reference: https://developers.openai.com/api/docs/guides/decisions. A choice takes only a `value` and a
`description`, so the worked examples go in the question's `instructions`, as for Drex.
"""

from __future__ import annotations

import os
import time

import httpx

from decidebench import fewshot
from decidebench.dataset import Item
from decidebench.types import Prediction, Pricing

QUESTION_NAME = "decision"


def build_body(item: Item, model: str, examples=()) -> dict:
    instructions = item.question
    if examples:
        instructions = f"{instructions}\n\n{fewshot.as_text(list(examples))}"
    return {
        "model": model,
        "input": item.state,
        "questions": [{
            "type": "choice",
            "name": QUESTION_NAME,
            "instructions": instructions,
            "choices": [{"value": o.key, "description": o.description} for o in item.options],
        }],
    }


def parse_response(item: Item, data: dict) -> tuple[str | None, dict[str, float] | None, str | None]:
    """Return (key, probs, error) from a /v1/decisions response."""
    answer = next((a for a in data.get("answers") or [] if isinstance(a, dict) and a.get("name") == QUESTION_NAME),
                  None)
    if answer is None:
        return None, None, "missing answer"
    if answer.get("type") == "refusal":
        return None, None, "refusal"
    probs = answer.get("probabilities")
    probs = ({p["value"]: float(p["probability"]) for p in probs if p.get("value") in item.keys}
             if isinstance(probs, list) else None) or None
    choice = answer.get("choice")
    if choice not in item.keys:
        return None, probs, f"choice {choice!r} not an option"
    return choice, probs, None


class OpenAIDecisionsSystem:
    name = "openai-decisions"
    model = "gpt-6-luna"
    label = "GPT-6 Luna (OpenAI Decisions)"
    kind = "system"
    pricing = Pricing(0.10, 0.0, "https://developers.openai.com/api/docs/guides/decisions", "2026-10-08")
    endpoint = "OpenAI /v1/decisions (public beta)"
    gateway_hop = False
    latency_comparable = True
    takes_examples = True

    def __init__(self) -> None:
        self.model = os.environ.get("OPENAI_DECISIONS_MODEL", self.model)
        self.url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/decisions"
        self.headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}

    async def predict(self, client: httpx.AsyncClient, item: Item) -> Prediction:
        shots = fewshot.for_item(item)
        t0 = time.perf_counter()
        resp = await client.post(self.url, json=build_body(item, self.model, shots), headers=self.headers)
        latency = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()
        key, probs, error = parse_response(item, data)
        usage = data.get("usage") or {}
        answer = next((a for a in data.get("answers") or [] if isinstance(a, dict)), {})
        return Prediction(
            item_id=item.id,
            provider=self.name,
            model=data.get("model", self.model),
            key=key,
            probs=probs,
            latency_ms=latency,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            raw=resp.text[:2000],
            error=error,
            extra={"confidence": answer.get("confidence"), "examples_shown": len(shots), "examples_total": len(shots)},
        )
