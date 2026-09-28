#!/usr/bin/env bash
# CLM-v0.1-8B: vLLM pooling Qwen3-8B on :8090, clm-serve on :8700.
set -euo pipefail
pip install -q --no-deps /work/CLM
pip install -q fastapi uvicorn
vllm serve Qwen/Qwen3-8B --runner pooling --served-model-name qwen3-8b --max-model-len 2048 --port 8090 \
  --gpu-memory-utilization 0.4 > /work/clm-vllm.log 2>&1 &
until curl -sf http://127.0.0.1:8090/v1/models > /dev/null; do sleep 5; done
exec clm-serve --host 127.0.0.1 --port 8700 --emb-url http://127.0.0.1:8090/v1/embeddings --device cuda --no-ui
