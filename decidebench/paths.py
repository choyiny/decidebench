"""Where DecideBench keeps its data and results, per benchmark version."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "v1.0"
DATA_DIR = ROOT / "data" / VERSION
RESULTS_DIR = ROOT / "results" / VERSION


def results_path(spec: str, results_dir: Path = RESULTS_DIR) -> Path:
    """`tev` → <results>/tev.jsonl; variants such as `tev.zero_shot` go under <results>/variants/."""
    return (results_dir / "variants" if "." in spec else results_dir) / f"{spec}.jsonl"


def meta_dir(results_dir: Path = RESULTS_DIR) -> Path:
    return results_dir / "meta"



def load_env(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
