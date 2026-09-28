#!/usr/bin/env bash
# Pinned model code and weights under /work (~/decidebench-tmp on the box).
set -euo pipefail
cd /work
[ -d CLM ] || git clone -q https://github.com/Contrastive-LM/CLM.git; git -C CLM checkout -q bb42c6c
[ -d laya-upstream ] || git clone -q https://github.com/NandhaKishorM/laya.git laya-upstream; git -C laya-upstream checkout -q 573e5b62696ba441230cd6be71d593331b5d23af
[ -d kev ] || git clone -q https://github.com/jaredpalmer/kev.git; git -C kev checkout -q 3e1cd3b
[ -d imajev ] || git clone -q https://github.com/mohit67890/imajev.git; git -C imajev checkout -q e7dadcf
[ -d jevk5 ] || git clone -q https://github.com/allebee/jevk5.git; git -C jevk5 checkout -q 6c6522f
python3 - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('Mapika/decider-2b', revision='533964d', local_dir='/work/decider-model')
snapshot_download('Mapika/decider-4b', revision='eb5fbdf', local_dir='/work/decider4b-model')
snapshot_download('alibiserikbay/JevK5', revision='c4f7fdb', local_dir='/work/jevk5-model')
snapshot_download('mohit67890/imajev-4b', revision='ef646e0', local_dir='/work/imajev/adapters/imajev-4b')
snapshot_download('SupersonicLabs/Julia-1', revision='a85b127', local_dir='/work/julia-model')
PY
echo "setup ok: CLM $(git -C CLM rev-parse --short HEAD), laya $(git -C laya-upstream rev-parse --short HEAD), kev $(git -C kev rev-parse --short HEAD), imajev $(git -C imajev rev-parse --short HEAD), jevk5 $(git -C jevk5 rev-parse --short HEAD); decider-2b, decider-4b, JevK5, imajev-4b, Julia-1 fetched"
