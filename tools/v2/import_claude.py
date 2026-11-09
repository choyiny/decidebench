"""Turn a tools/v2/eval_claude.py run into a benchmark result (results/<set>/<entry>.jsonl and meta).

    uv run python tools/v2/import_claude.py --model claude-opus-4-8 --src results/v2/claude-raw --dest results/v2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from decidebench.meta import build_meta, write_meta  # noqa: E402
from decidebench.types import Prediction  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--dest", type=Path, required=True)
    a = ap.parse_args()
    rows = [json.loads(l) for l in (a.src / f"{a.model}.jsonl").read_text().splitlines() if l.strip()]
    rows = list({r["id"]: r for r in rows}.values())
    a.dest.mkdir(parents=True, exist_ok=True)
    with (a.dest / f"{a.model}.jsonl").open("w") as f:
        for r in rows:
            refused = r.get("stop_reason") == "refusal"
            p = Prediction(item_id=r["id"], provider=a.model, model=a.model, key=r.get("pred"),
                           latency_ms=r.get("latency_ms", 0.0), input_tokens=r.get("input_tokens", 0),
                           output_tokens=r.get("output_tokens", 0), raw=r.get("raw", ""),
                           error=None if r.get("pred") else ("refusal" if refused else "unparseable reply"),
                           extra={"stop_reason": r.get("stop_reason")})
            f.write(json.dumps(p.to_json()) + "\n")
    write_meta(build_meta(a.model, a.model, concurrency=4, warmup=0, status="verified", items=len(rows)), a.dest)
    print(f"imported {len(rows)} rows of {a.model} into {a.dest}")


if __name__ == "__main__":
    main()
