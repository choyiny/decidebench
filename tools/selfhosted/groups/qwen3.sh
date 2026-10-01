#!/usr/bin/env bash
# Qwen3-8B: vLLM on :8091.
exec vllm serve Qwen/Qwen3-8B --port 8091 --max-model-len 16384 --gpu-memory-utilization ${GPU_MEM_UTIL:-0.45}
