"""Build the Hugging Face dataset directory.

    uv run python -m decidebench.hf_export      # writes build/hf/
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from decidebench.dataset import CANARY
from decidebench.paths import DATA_DIR, ROOT

REPO = "https://github.com/choyiny/decidebench"

HEADER = """---
license: cc-by-4.0
language:
- en
pretty_name: DecideBench
size_categories:
- n<1K
task_categories:
- text-classification
- multiple-choice
tags:
- decision-models
- benchmark
- cost
- latency
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test.jsonl
- config_name: examples
  data_files:
  - split: train
    path: data/examples.jsonl
---

"""


def _jsonl(paths) -> list[str]:
    return [line for p in paths for line in p.read_text().splitlines() if line.strip()]


def card(readme: str) -> str:
    """The README as a dataset card: generated-block markers dropped, charts local, repository links absolute."""
    text = re.sub(r"<!-- GEN:\w+:(START|END) -->\n", "", readme)
    text = text.replace("](docs/img/", "](img/")
    return re.sub(r"\]\((?!https?://|img/|#)([^)]+)\)", lambda m: f"]({REPO}/tree/main/{m.group(1)})", text)


def export(out_dir: Path = ROOT / "build" / "hf", data_dir: Path = DATA_DIR) -> Path:
    (out_dir / "data").mkdir(parents=True, exist_ok=True)
    (out_dir / "img").mkdir(exist_ok=True)
    (out_dir / "data" / "test.jsonl").write_text("\n".join(_jsonl(sorted(data_dir.glob("*.jsonl")))) + "\n")
    (out_dir / "data" / "examples.jsonl").write_text(
        "\n".join(_jsonl(sorted((data_dir / "examples").glob("*.jsonl")))) + "\n")
    for png in (ROOT / "docs" / "img").glob("*.png"):
        shutil.copy(png, out_dir / "img" / png.name)
    body = card((ROOT / "README.md").read_text())
    assert CANARY in body, "the README must carry the canary"
    (out_dir / "README.md").write_text(HEADER + body)
    return out_dir


if __name__ == "__main__":
    print(export())
