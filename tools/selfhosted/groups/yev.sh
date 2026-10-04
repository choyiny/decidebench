#!/usr/bin/env bash
# yev0-4b: yev's server (yev/serve) on :8780, started directly: the yev CLI imports the training stack.
set -euo pipefail
pip install -q --no-deps -e /work/yev
pip install -q fastapi uvicorn pydantic flash-linear-attention
exec python3 -c '
import uvicorn
from yev.serve.app import create_app
from yev.serve.engine import Engine
engine = Engine("/work/yev-model", None, "/work/yev-model/calibration.json", max_len=16384)
uvicorn.run(create_app(engine, model_name="yev0-4b"), host="127.0.0.1", port=8780)'
