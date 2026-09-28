#!/usr/bin/env bash
# TEV (Tev1-4B-experimental): vLLM on :8092.
exec vllm serve togethercomputer/Tev1-4B-experimental --revision 0b7becf --served-model-name togethercomputer/Tev1-4B-experimental \
  --port 8092 --max-model-len 16384 --gpu-memory-utilization 0.4
