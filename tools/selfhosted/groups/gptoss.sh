#!/usr/bin/env bash
# gpt-oss-120b (MXFP4): vLLM on :8093.
exec vllm serve openai/gpt-oss-120b --revision b5c939de8f754692c1647ca79fbf85e8c1e70f8a \
  --port 8093 --max-model-len 16384 --gpu-memory-utilization 0.85
