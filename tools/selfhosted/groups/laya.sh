#!/usr/bin/env bash
# Laya typed-decisions: tools/laya/serve.py on :8710.
set -euo pipefail
pip install -q --no-deps /work/laya-upstream
exec python3 /work/repo/tools/laya/serve.py --port 8710 --device cuda
