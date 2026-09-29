#!/usr/bin/env bash
# Jeff Gemma4-E2B (v1.0): jeff-serve on :8752.
set -euo pipefail
pip install -q --no-deps -e /work/jeff
pip install -q "transformers==5.17.0" fastapi uvicorn pillow safetensors flash-linear-attention
JEFF_CHECKPOINT=/work/jeff-models/gemma4 JEFF_DEVICE=cuda JEFF_HOST=127.0.0.1 PORT=8752 exec jeff-serve
