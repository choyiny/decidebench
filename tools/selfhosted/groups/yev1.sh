#!/usr/bin/env bash
# yev1-4b: yev's server (yev/serve, transformers engine) on :8781, started directly like yev0-4b.
set -euo pipefail
pip install -q --no-deps -e /work/yev1
pip install -q fastapi uvicorn pydantic flash-linear-attention
exec python3 -c '
import uvicorn
from yev.serve.app import create_app
from yev.serve.engine import Engine
engine = Engine("/work/yev1-model", None, "/work/yev1-model/calibration.json", max_len=16384)
uvicorn.run(create_app(engine, model_name="yev1-4b"), host="127.0.0.1", port=8781)'
