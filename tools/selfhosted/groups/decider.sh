#!/usr/bin/env bash
# Decider-2B: decider.serve on :8720.
set -euo pipefail
pip install -q fastapi uvicorn pydantic flash-linear-attention
cd /work/decider-model
DECIDER_MODEL=/work/decider-model DECIDER_DEVICE=cuda exec uvicorn decider.serve:app --host 127.0.0.1 --port 8720
