#!/usr/bin/env bash
# Julia-1: tools/julia/serve.py on :8740.
set -euo pipefail
pip install -q --no-deps -e /work/julia-model
pip install -q "transformers>=5.0,<5.1" fastapi uvicorn
exec python3 /work/repo/tools/julia/serve.py --model /work/julia-model --port 8740
