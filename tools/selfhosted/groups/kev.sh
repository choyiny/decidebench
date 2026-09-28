#!/usr/bin/env bash
# Kev-4B: kev.serve on :8009.
set -euo pipefail
pip install -q --no-deps -e /work/kev
pip install -q "transformers>=5.17,<6" peft fastapi uvicorn typesafe-sdk flash-linear-attention
exec python3 -m kev.serve --run jaredpalmer/kev-4b@139fdd9 --port 8009
