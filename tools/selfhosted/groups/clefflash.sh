#!/usr/bin/env bash
# Clef-Flash 9B: Cloudflare's SGLang image serves /v1/systemone on :30001.
set -euo pipefail
exec sglang serve --model-path /work/clef-flash-model --served-model-name clef-flash --host 127.0.0.1 --port 30001
