#!/usr/bin/env bash
# Clef 27B: Cloudflare's SGLang image serves /v1/systemone on :30000.
set -euo pipefail
exec sglang serve --model-path /work/clef-model --served-model-name clef --host 127.0.0.1 --port 30000
