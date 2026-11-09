#!/usr/bin/env bash
# pplx-decider-v1.2: tools/pplx/serve.py (Perplexity's pplx_decider package, fast path) on :8790.
set -euo pipefail
pip install -q -r /work/pplx-model/requirements-fast.txt
exec python3 /work/repo/tools/pplx/serve.py --model /work/pplx-model --name pplx-decider-v1.2 --port 8790
