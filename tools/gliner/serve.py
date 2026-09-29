"""GLiNER2.5-Decide behind JEV's /v1/systemone protocol.

    python3 tools/gliner/serve.py --revision 5a7adf7 --port 8760
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gliner2 import AutoExtractor

REPO = "fastino/GLiNER2.5-Decide"


def task(question: dict) -> dict:
    labels, examples = {}, []
    for key, value in question["criteria"].items():
        if isinstance(value, dict):
            labels[key] = value.get("what", "")
            examples += [(text, key) for text in value.get("examples", [])]
        else:
            labels[key] = value
    spec = {"labels": labels, "prompt": question.get("instructions", ""), "multi_label": True,
            "class_act": "softmax", "cls_threshold": 0.0}
    if examples:
        spec["examples"] = examples
    return spec


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
                return self._send(200, {"models": [{"name": "gliner-decide", "revision": served}]})
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path.rstrip("/") != "/v1/systemone":
                return self._send(404, {"error": "not found"})
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            answers = {}
            with lock:
                for qid, question in req["questions"].items():
                    out = model.classify_text(req["state"], {qid: task(question)}, include_confidence=True)[qid]
                    probs = {o["label"]: float(o["confidence"]) for o in out}
                    answers[qid] = {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs}
            self._send(200, {"model": served, "answers": answers, "usage": {}})

        def log_message(self, *args) -> None:
            pass

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--port", type=int, default=8760)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    model = AutoExtractor.from_pretrained(REPO, revision=args.revision, map_location=args.device)
    served = f"{REPO}@{args.revision}"
    print(f"serving {served} on :{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(model, served, threading.Lock())).serve_forever()


if __name__ == "__main__":
    main()
