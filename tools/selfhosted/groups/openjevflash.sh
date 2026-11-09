#!/usr/bin/env bash
# OpenJev Flash 9B, as its model card serves it: vLLM 0.29 in FP8 on :8801, and its helper/shim.py on :8800.
set -euo pipefail
pip install -q "openai==3.26.0" "httpx==0.28.1"
vllm serve /work/openjev-flash-model --host 127.0.0.1 --served-model-name qwen --port 8801 \
  --enable-prefix-caching --max-model-len 16384 --gpu-memory-utilization ${GPU_MEM_UTIL:-0.90} \
  --limit-mm-per-prompt '{"image":1}' --trust-remote-code --max-num-seqs 16 \
  --max-logprobs 64 --gdn-prefill-backend triton --quantization fp8 &
for _ in $(seq 360); do curl -fsS --max-time 5 http://127.0.0.1:8801/health >/dev/null 2>&1 && break; sleep 5; done
VLLM=http://127.0.0.1:8801/v1 TOKENIZER=/work/openjev-flash-model \
READOUT_T=1.07 READOUT_NOUL_T=1.074766 READOUT_NOUL_BIAS=0 \
READOUT_TARGETED=1 READOUT_INSTR_STYLE=pyrepr SHIM_STAGGER=1 \
exec python3 /work/openjev-flash-model/helper/shim.py --host 127.0.0.1 --port 8800
