"""Budgeted live Gemini smoke for /api/analyze (AXO HYBRID /20, D7). Owner-run: it needs GEMINI_API_KEY.

usage (from anywhere, main venv python):
  python -B live_gemini_smoke.py <checkout_backend_dir> <LIVE_SMOKE_PREREGISTRATION.json> <out.json> <dotenv_path>

One process: hard HTTP cap via app.ai.gemini.ApiBudget BEFORE the app is imported, loopback uvicorn on :8020, fresh
SQLite outside the repo, throwaway account with a random runtime password, each case sent once, pre-registered stop
rules. Never prints or writes the key, request bodies or raw responses; out.json carries only classified metadata.
"""
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
cap = prereg["budget"]["max_gemini_http_requests"]

from dotenv import dotenv_values  # noqa: E402  (installed in the backend venv)

key = dotenv_values(dotenv_p).get("GEMINI_API_KEY")
if not key:
    raise SystemExit("GEMINI_API_KEY missing in the given .env")
db_dir = Path(tempfile.mkdtemp(prefix="axo-live-smoke-"))
os.environ.update({"GEMINI_API_KEY": key, "HYBRID_ROUTE_MODE": "live", "ALLOW_LIVE_AI": "1",
                   "DATABASE_URL": f"sqlite:///{(db_dir / 'smoke.db').as_posix()}", "PYTHONDONTWRITEBYTECODE": "1"})
del key
sys.dont_write_bytecode = True
sys.path.insert(0, str(backend))
os.chdir(backend)

from app.ai import gemini  # noqa: E402

budget = gemini.ApiBudget(max_api_calls=cap)
gemini.set_budget(budget)
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

BASE = "http://127.0.0.1:8020"
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def post(path: str, data: dict) -> tuple[int, dict]:
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=180) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


tag = secrets.token_hex(4)
st, _ = post("/api/auth/register", {"email": f"live-smoke-{tag}@example.invalid", "displayName": "Live smoke",
                                    "password": secrets.token_urlsafe(18)})
assert st in (200, 201), f"register HTTP {st}"


def reason(body: dict) -> str | None:
    rd = body.get("route_d") or {}
    ref = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
    env = body.get("envelope") if isinstance(body.get("envelope"), dict) else {}
    return (env.get("reason_code") or rd.get("reason_code") or ref.get("reason_code") or ref.get("code")
            or body.get("error_code") or body.get("reason_code"))


rows, infra, stop = [], 0, None
for case in prereg["cases"]:
    before = budget.http_requests
    t0 = time.perf_counter()
    try:
        st, body = post("/api/analyze", {"input": {"type": "text", "content": case["text"]}})
    except Exception as e:  # a crash of the client/server path is a finding
        st, body = -1, {"client_error": type(e).__name__}
    rd = body.get("route_d") or {}
    answers = sorted(str(v) for v in (rd.get("answers") or {}).values())
    calls = budget.http_requests - before
    status = rd.get("status")
    if case["id"] == "N1":
        cls = "GATE_OK" if (st == 200 and status != "SERVED" and calls == 0) else "GATE_FAIL"
    elif st == 200 and status == "SERVED":
        cls = "MATCH" if answers == case["expected_answer_values"] else "WRONG_ANSWER"
    elif st == 200:
        cls = "SAFE_REFUSAL"
    elif st in (502, 503, 504):
        cls = "INFRA"
    elif st == 429:
        cls = "RATE_LIMITED"
    else:
        cls = "SERVER_ERROR"
    rows.append({"id": case["id"], "http": st, "route_d_status": status, "reason": reason(body),
                 "answer_values": answers, "expected_answer_values": case["expected_answer_values"],
                 "gemini_http_requests": calls, "latency_ms": int((time.perf_counter() - t0) * 1000),
                 "n_scene_objects": len(((body.get("envelope") or {}).get("scene3d") or {}).get("objects") or []),
                 "class": cls})
    print(case["id"], cls, st, status, reason(body), "calls", calls, flush=True)
    infra += cls == "INFRA"
    if cls == "SERVER_ERROR":
        stop = "HTTP_500_OR_CRASH"
    elif infra >= 2:
        stop = "TWO_INFRA_FAILURES"
    elif cls == "RATE_LIMITED" or budget.aborted:
        stop = "RATE_LIMIT_OR_BUDGET"
    if stop:
        break

server.should_exit = True
match = sum(r["class"] == "MATCH" for r in rows)
blockers = [r["id"] for r in rows if r["class"] in ("SERVER_ERROR", "WRONG_ANSWER", "GATE_FAIL")]
n1_ok = any(r["id"] == "N1" and r["class"] == "GATE_OK" for r in rows)
if blockers:
    verdict = "FAIL"
elif n1_ok and match >= 4 and budget.http_requests <= cap and not stop:
    verdict = "PASS"
else:
    verdict = "INCONCLUSIVE"
out = {"schema": "axo-live-gemini-smoke-result/1", "preregistration_sha256": hashlib.sha256(prereg_raw).hexdigest(),
       "checkout_backend": str(backend), "module": M.__file__, "gemini_model": gemini.MODEL,
       "budget": {"cap": cap, "http_requests": budget.http_requests, "logical_calls": budget.logical_calls,
                  "retry_requests": budget.retry_requests, "transient_hits": budget.transient_hits,
                  "aborted": budget.aborted},
       "stop": stop, "match": match, "blockers": blockers, "verdict": verdict, "rows": rows}
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("VERDICT", verdict, "http_requests", budget.http_requests, "match", match, "blockers", blockers)
