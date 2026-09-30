#!/usr/bin/env bash
# Kev-9B: kev.serve on :8010.
set -euo pipefail
pip install -q --no-deps -e /work/kev
pip install -q "transformers>=5.17,<6" peft fastapi uvicorn typesafe-sdk flash-linear-attention
mem=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
case $mem in *[!0-9]*|"") ;; *) [ "$mem" -ge 40000 ] || export KEV_CUDA_GRAPHS=0 ;; esac
exec python3 -m kev.serve --run jaredpalmer/kev-9b@2629c06 --host 127.0.0.1 --port 8010
