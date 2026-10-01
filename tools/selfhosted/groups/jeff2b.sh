#!/usr/bin/env bash
# Jeff Qwen3.5-2B (2b1055e, tag v1.1): jeff-serve on :8751.
set -euo pipefail
pip install -q --no-deps -e /work/jeff
pip install -q "transformers==5.17.0" fastapi uvicorn pillow safetensors flash-linear-attention
JEFF_CHECKPOINT=/work/jeff-models/2b JEFF_DEVICE=cuda JEFF_HOST=127.0.0.1 PORT=8751 exec jeff-serve
