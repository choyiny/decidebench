#!/usr/bin/env bash
# yev1-4b: vLLM sidecar on :8100 (flags from yev's scripts/aws/serve_engine.sh), yev serve --backend vllm on :8781.
set -euo pipefail
pip install -q --no-deps -e /work/yev1
vllm serve /work/yev1-model --host 127.0.0.1 --port 8100 --served-model-name yev --dtype bfloat16 \
  --max-model-len 16385 --enable-prefix-caching --generation-config vllm --logprobs-mode processed_logprobs \
  --max-logprobs 26 --gpu-memory-utilization ${GPU_MEM_UTIL:-0.85} --trust-remote-code &
for _ in $(seq 360); do curl -fsS --max-time 5 http://127.0.0.1:8100/health >/dev/null 2>&1 && break; sleep 5; done
exec python3 -c '
import uvicorn
from transformers import AutoTokenizer
from yev.serve.app import create_app
from yev.serve.backends import make_backend
from yev.serve.remote import RemoteEngine
engine = RemoteEngine(AutoTokenizer.from_pretrained("/work/yev1-model"), make_backend("vllm", "http://127.0.0.1:8100"),
                      "/work/yev1-model/calibration.json", max_len=16384)
uvicorn.run(create_app(engine, model_name="yev1-4b"), host="127.0.0.1", port=8781)'
