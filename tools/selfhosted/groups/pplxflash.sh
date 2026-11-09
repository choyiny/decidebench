#!/usr/bin/env bash
# pplx-decider-flash-v1.2: tools/pplx/serve.py (Perplexity's pplx_decider package, fast path) on :8791.
set -euo pipefail
pip install -q -r /work/pplx-flash-model/requirements-fast.txt
exec python3 /work/repo/tools/pplx/serve.py --model /work/pplx-flash-model --name pplx-decider-flash-v1.2 --port 8791
