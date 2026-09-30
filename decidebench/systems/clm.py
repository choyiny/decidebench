"""CLM-v0.1-8B, self-hosted with clm-serve."""

from __future__ import annotations

import os

from decidebench.systems.jev import JevSystem
from decidebench.types import L4


class ClmSystem(JevSystem):
    label = "CLM-v0.1-8B (self-hosted)"
    kind = "system"
    pricing = L4
    endpoint = "clm-serve @ Contrastive-LM/CLM bb42c6c over vLLM pooling (Qwen3-8B) on an NVIDIA L4 (CUDA)"
    gateway_hop = False
    latency_comparable = False
    takes_examples = False

    def __init__(self) -> None:
        self.variant = "default"
        self.name = "clm"
        self.model = os.environ.get("CLM_MODEL", "clm-latest")
        self.url = os.environ.get("CLM_BASE_URL", "http://127.0.0.1:8700/v1").rstrip("/") + "/systemone"
        self.headers = {}
