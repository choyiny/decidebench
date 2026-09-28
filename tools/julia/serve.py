"""Julia-1 behind JEV's /v1/systemone protocol.

    python3 tools/julia/serve.py --model <Julia-1 snapshot> --port 8740
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from julia import load_model

SERVED = "SupersonicLabs/Julia-1@a85b127"


def make_handler(engine, lock: threading.Lock):
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
                return self._send(200, {"models": [{"name": "julia-1", "revision": SERVED}]})
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path.rstrip("/") != "/v1/systemone":
                return self._send(404, {"error": "not found"})
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            try:
                with lock:
                    out = engine.predict(state=req["state"], questions=req["questions"])
            except ValueError as e:
                return self._send(422, {"error": str(e)})
            self._send(200, {"model": SERVED, "answers": out["answers"], "usage": out.get("usage", {})})

        def log_message(self, *args) -> None:
            pass

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="local snapshot of SupersonicLabs/Julia-1")
    ap.add_argument("--port", type=int, default=8740)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    engine = load_model(args.model, device=args.device, strict_encoding=True, max_length=8192, head_length=512)
    print(f"serving {SERVED} on :{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(engine, threading.Lock())).serve_forever()


if __name__ == "__main__":
    main()
