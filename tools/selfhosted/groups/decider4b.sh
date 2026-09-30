#!/usr/bin/env bash
# Decider-4B: decider.serve on :8721.
set -euo pipefail
pip install -q fastapi uvicorn pydantic flash-linear-attention
cd /work/decider4b-model
mem=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
case $mem in *[!0-9]*|"") ;; *) [ "$mem" -ge 40000 ] || export DECIDER_GRAPH_TOKEN_BUDGET=16384 ;; esac
DECIDER_MODEL=/work/decider4b-model DECIDER_DEVICE=cuda exec uvicorn decider.serve:app --host 127.0.0.1 --port 8721
