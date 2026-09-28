#!/usr/bin/env bash
# Llama-3.3-70B-Instruct (FP8): vLLM on :8094.
exec vllm serve RedHatAI/Llama-3.3-70B-Instruct-FP8-dynamic --revision f50dbad2c84590ca17dc51e207c34321b65ff14b \
  --port 8094 --max-model-len 16384 --gpu-memory-utilization 0.85
