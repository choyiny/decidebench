"""Bespoke-Nimble-9B behind JEV's /v1/systemone protocol.

    python3 tools/nimble/serve.py --model-dir <Bespoke-Nimble-9B snapshot> --port 8770
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def schema(question: dict) -> dict:
    criteria = {k: (v.get("what", "") if isinstance(v, dict) else v) for k, v in question["criteria"].items()}
    return {"type": "enum", "choices": list(criteria), "description": question.get("instructions", ""),
            "choice_descriptions": criteria}


def make_handler(model, served: str, lock: threading.Lock):
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
                return self._send(200, {"models": [{"name": "nimble-9b", "revision": served}]})
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path.rstrip("/") != "/v1/systemone":
                return self._send(404, {"error": "not found"})
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            answers = {}
            try:
                with lock:
                    for qid, question in req["questions"].items():
                        field = model.score(req["state"], {qid: schema(question)})["fields"][qid]
                        answers[qid] = {"type": "choice", "choice": field["prediction"],
                                        "probabilities": field["probabilities"]}
            except ValueError as e:
                return self._send(422, {"error": str(e)})
            self._send(200, {"model": served, "answers": answers, "usage": {}})

        def log_message(self, *args) -> None:
            pass

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--revision", default="bd792f4")
    ap.add_argument("--port", type=int, default=8770)
    args = ap.parse_args()
    sys.path.insert(0, args.model_dir)
    from inference import NimbleModel

    model = NimbleModel(args.model_dir)
    served = f"bespokelabs/Bespoke-Nimble-9B@{args.revision}"
    print(f"serving {served} on :{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(model, served, threading.Lock())).serve_forever()


if __name__ == "__main__":
    main()
