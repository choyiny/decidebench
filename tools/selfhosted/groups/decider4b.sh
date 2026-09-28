#!/usr/bin/env bash
# Decider-4B: decider.serve on :8721.
set -euo pipefail
pip install -q fastapi uvicorn pydantic flash-linear-attention
cd /work/decider4b-model
DECIDER_MODEL=/work/decider4b-model DECIDER_DEVICE=cuda exec uvicorn decider.serve:app --host 127.0.0.1 --port 8721
