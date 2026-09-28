#!/usr/bin/env bash
# JevK5 v0.3: jevk5-serve on :8730.
set -euo pipefail
pip install -q --no-deps -e /work/jevk5
pip install -q "transformers>=5.17,<6" accelerate jinja2 fastapi uvicorn flash-linear-attention
exec jevk5-serve --model /work/jevk5-model --host 127.0.0.1 --port 8730
