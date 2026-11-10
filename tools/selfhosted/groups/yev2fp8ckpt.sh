#!/usr/bin/env bash
# yev2-35b-a3b-fp8: the published FP8_DYNAMIC checkpoint with a 45 GiB cap (a 48 GB GPU); :8105 and :8785.
set -euo pipefail
pip install -q --no-deps -e /work/yev2
vllm serve /work/yev2-qwen-fp8 --host 127.0.0.1 --port 8105 --served-model-name yev \
  --max-model-len 16385 --enable-prefix-caching --generation-config vllm --logprobs-mode processed_logprobs \
  --max-logprobs 26 --max-num-seqs 64 --gpu-memory-utilization 0.46 --trust-remote-code &
for _ in $(seq 360); do curl -fsS --max-time 5 http://127.0.0.1:8105/health >/dev/null 2>&1 && break; sleep 5; done
curl -fsS --max-time 5 http://127.0.0.1:8105/health >/dev/null || { echo "vLLM did not come up" >&2; exit 1; }
exec python3 -c '
import uvicorn
from transformers import AutoTokenizer
from yev.serve.app import create_app
from yev.serve.backends import make_backend
from yev.serve.remote import RemoteEngine
engine = RemoteEngine(AutoTokenizer.from_pretrained("/work/yev2-qwen-fp8"), make_backend("vllm", "http://127.0.0.1:8105"),
                      "/work/yev2-qwen-fp8/calibration.json", max_len=16384)
uvicorn.run(create_app(engine, model_name="yev2-35b-a3b-fp8"), host="127.0.0.1", port=8785)'
