#!/usr/bin/env bash
# Bespoke-Nimble-9B: tools/nimble/serve.py on :8770.
set -euo pipefail
pip install -q "transformers==5.17.0" "peft==0.21.0" "accelerate==1.15.0" "sentencepiece==0.2.2" safetensors
exec python3 /work/repo/tools/nimble/serve.py --model-dir /work/nimble-model --revision bd792f4 --port 8770
