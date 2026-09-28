#!/usr/bin/env bash
# imajev-4b: imajev's server on :8765.
set -euo pipefail
cd /work/imajev
pip install -q --no-deps -e .
pip install -q fastapi uvicorn python-multipart peft accelerate safetensors flash-linear-attention
python3 scripts/download_model.py --model 4b
PYTHONPATH=src:scripts exec python3 scripts/playground/server.py --backend torch --model-bundle artifacts/model-qwen4b.json \
  --adapter adapters/imajev-4b --calibration adapters/imajev-4b/calibration.json --model-name imajev-4b \
  --rotations 1 --fast --merge-lora --host 127.0.0.1 --port 8765 --max-input-tokens 16384
