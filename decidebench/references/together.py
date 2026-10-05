"""General LLMs on Together AI, at its list prices."""

from __future__ import annotations

import os

from decidebench.references.frontier import FrontierSystem
from decidebench.types import Pricing

TOGETHER_MODELS = "https://api.together.ai/v1/models"


class TogetherChatSystem(FrontierSystem):
    endpoint = "Together AI serverless /v1/chat/completions"
    gateway_hop = False
    params = {"temperature": 0, "max_tokens": 4096}

    def __init__(self) -> None:
        self.url = "https://api.together.ai/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {os.environ['TOGETHER_API_KEY']}"}


class DeepSeekSystem(TogetherChatSystem):
    name = "deepseek"
    model = "deepseek-ai/DeepSeek-V4-Flash-0731"
    label = "DeepSeek-V4-Flash (Together)"
    pricing = Pricing(0.14, 0.28, TOGETHER_MODELS, "2026-09-28")


class GlmFlashSystem(TogetherChatSystem):
    name = "glm-flash"
    model = "zai-org/GLM-5.3-Flash"
    label = "GLM-5.3-Flash (Together)"
    pricing = Pricing(0.15, 0.50, TOGETHER_MODELS, "2026-09-28")


class DeepSeek41System(TogetherChatSystem):
    name = "deepseek-41"
    model = "deepseek-ai/DeepSeek-V4.1-Flash"
    label = "DeepSeek-V4.1-Flash (Together)"
    pricing = Pricing(0.30, 1.20, TOGETHER_MODELS, "2026-09-28")

