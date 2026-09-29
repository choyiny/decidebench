#!/usr/bin/env bash
# GLiNER2.5-Decide: tools/gliner/serve.py on :8760.
set -euo pipefail
pip install -q "gliner2==2.0.0" "transformers>=4.38,<5" peft safetensors
exec python3 /work/repo/tools/gliner/serve.py --revision 5a7adf7 --port 8760
