"""Paired live diagnosis, capture half (AXO HYBRID /20, D7 follow-up). One checkout per process.

usage: python -B live_pair_capture.py <checkout_backend_dir> <LIVE_PAIR_DIAGNOSIS_PREREGISTRATION.json> <out.json> <dotenv_path>

Same live path as tools/live_gemini_smoke.py (loopback :8020, POST /api/analyze, fresh SQLite outside the repo, throwaway
account with a random runtime password, hard HTTP cap via app.ai.gemini.ApiBudget). Only addition: an observer on
TransportExtractor.extract keeps the dict it returns (the exact input of TypedFactNext validation, derived from public
test text) so tools/cross_replay.py can replay it offline through both checkouts. The observer returns the same object
and re-raises the same exception: behaviour is unchanged. Never prints or writes the key.
"""
import copy
import hashlib
import http.cookiejar
import json
import os
import secrets
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

backend, prereg_p, out_p, dotenv_p = (Path(a).resolve() for a in sys.argv[1:5])
if out_p.exists():
    raise SystemExit(f"refusing to overwrite {out_p}")
prereg_raw = prereg_p.read_bytes()
prereg = json.loads(prereg_raw)
cap = prereg["budget"]["max_gemini_http_requests_per_checkout"]
cases = [c for c in prereg["cases"]]

from dotenv import dotenv_values  # noqa: E402

key = dotenv_values(dotenv_p).get("GEMINI_API_KEY")
if not key:
    raise SystemExit("GEMINI_API_KEY missing in the given .env")
db_dir = Path(tempfile.mkdtemp(prefix="axo-live-pair-"))
os.environ.update({"GEMINI_API_KEY": key, "HYBRID_ROUTE_MODE": "live", "ALLOW_LIVE_AI": "1",
                   "DATABASE_URL": f"sqlite:///{(db_dir / 'pair.db').as_posix()}", "PYTHONDONTWRITEBYTECODE": "1"})
del key
sys.dont_write_bytecode = True
sys.path.insert(0, str(backend))
os.chdir(backend)

from app.ai import gemini  # noqa: E402

budget = gemini.ApiBudget(max_api_calls=cap)
gemini.set_budget(budget)
import app.ai.typed_fact_next_extraction as X  # noqa: E402

captured: list[dict] = []
_orig_extract = X.TransportExtractor.extract


def _observed_extract(self, source_text):
    try:
        out = _orig_extract(self, source_text)
    except Exception as e:
        captured.append({"text_sha16": hashlib.sha256(source_text.encode()).hexdigest()[:16],
                         "raised": getattr(e, "code", type(e).__name__)})
        raise
    captured.append({"text_sha16": hashlib.sha256(source_text.encode()).hexdigest()[:16],
                     "payload": copy.deepcopy(out)})
    return out


X.TransportExtractor.extract = _observed_extract
import app.main as M  # noqa: E402
import uvicorn  # noqa: E402

assert Path(M.__file__).resolve().is_relative_to(backend), M.__file__
server = uvicorn.Server(uvicorn.Config(M.app, host="127.0.0.1", port=8020, log_level="warning"))
threading.Thread(target=server.run, daemon=True).start()
for _ in range(200):
    if server.started:
        break
    time.sleep(0.1)
assert server.started, "server did not start"
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def post(path: str, data: dict) -> tuple[int, dict]:
    req = urllib.request.Request("http://127.0.0.1:8020" + path, data=json.dumps(data).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=180) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


st, _ = post("/api/auth/register", {"email": f"live-pair-{secrets.token_hex(4)}@example.invalid",
                                    "displayName": "Live pair", "password": secrets.token_urlsafe(18)})
assert st in (200, 201), f"register HTTP {st}"

rows = []
for case in cases:
    before, t0 = budget.http_requests, time.perf_counter()
    st, body = post("/api/analyze", {"input": {"type": "text", "content": case["text"]}})
    rd = body.get("route_d") or {}
    ref = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
    rows.append({"id": case["id"], "http": st, "route_d_status": rd.get("status"),
                 "reason": ref.get("code") or ref.get("reason_code") or rd.get("reason_code") or body.get("reason_code"),
                 "answer_values": sorted(str(v) for v in (rd.get("answers") or {}).values()),
                 "gemini_http_requests": budget.http_requests - before,
                 "latency_ms": int((time.perf_counter() - t0) * 1000)})
    print(case["id"], st, rd.get("status"), rows[-1]["reason"], "calls", rows[-1]["gemini_http_requests"], flush=True)
    if st == 500 or budget.aborted:
        break

server.should_exit = True
out = {"schema": "axo-live-pair-capture/1", "preregistration_sha256": hashlib.sha256(prereg_raw).hexdigest(),
       "checkout_backend": str(backend), "module": M.__file__, "gemini_model": gemini.MODEL,
       "budget": {"cap": cap, "http_requests": budget.http_requests, "logical_calls": budget.logical_calls,
                  "retry_requests": budget.retry_requests, "aborted": budget.aborted},
       "rows": rows, "captured": captured}
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("http_requests", budget.http_requests, "captured", len(captured))
