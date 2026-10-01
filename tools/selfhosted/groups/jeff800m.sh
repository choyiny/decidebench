#!/usr/bin/env bash
# Jeff Qwen3.5-0.8B (0f212b3, tag v1.1): jeff-serve on :8750.
set -euo pipefail
pip install -q --no-deps -e /work/jeff
pip install -q "transformers==5.17.0" fastapi uvicorn pillow safetensors flash-linear-attention
JEFF_CHECKPOINT=/work/jeff-models/800m JEFF_DEVICE=cuda JEFF_HOST=127.0.0.1 PORT=8750 exec jeff-serve
