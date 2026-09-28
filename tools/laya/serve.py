"""Laya typed-decisions behind JEV's /v1/systemone protocol.

    python3 tools/laya/serve.py --port 8710
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import laya
from huggingface_hub import model_info, snapshot_download

CHECKPOINTS = {
    "laya-typed": ("convaiinnovations/laya-typed-decisions", "1a793eb"),
}


def load_all(device: str) -> dict[str, tuple[object, str]]:
    agents = {}
    for name, (repo, short) in CHECKPOINTS.items():
        rev = model_info(repo, revision=short).sha
        path = snapshot_download(repo, revision=rev)
        agents[name] = (laya.load(path, device=device), f"{repo}@{rev[:7]}")
        print(f"loaded {name}: {agents[name][1]} on {device}", flush=True)
    return agents


def make_handler(agents: dict, lock: threading.Lock):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path.rstrip("/") == "/v1/models":
                return self._send(200, {"models": [{"name": n, "revision": r} for n, (_, r) in agents.items()]})
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path.rstrip("/") != "/v1/systemone":
                return self._send(404, {"error": "not found"})
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            name = req.get("model") or "laya-typed"
            if name not in agents:
                return self._send(422, {"error": f"unknown model {name!r}; available: {sorted(agents)}"})
            agent, served = agents[name]
            with lock:
                out = agent.system_one(req["state"], req["questions"])
            self._send(200, {"model": served, "answers": out["answers"], "usage": out.get("usage", {})})

        def log_message(self, *args) -> None:
            pass

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8710)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    agents = load_all(args.device)
    print(f"serving {sorted(agents)} on :{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(agents, threading.Lock())).serve_forever()


if __name__ == "__main__":
    main()
