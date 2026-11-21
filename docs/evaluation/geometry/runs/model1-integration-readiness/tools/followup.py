"""AXO /17 P4 follow-up: unprovisioned runtime on a text that truly needs AxoV9, and served-cache persistence across a
backend restart. usage (cwd = <worktree>/backend): python followup.py <out_dir> <manifest.json> <case_id>"""
import json, os, secrets, subprocess, sys, time
from pathlib import Path
import httpx

OUT, MAN, CID = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
if OUT.exists() and any(OUT.iterdir()):
    raise SystemExit("refusing non-empty out dir")
OUT.mkdir(parents=True, exist_ok=True)
text = next(c["original_input"] for c in json.loads(MAN.read_text(encoding="utf-8"))["valid_cases"] if c["case_id"] == CID)
DB = f"sqlite:///{(OUT / 'f.db').as_posix()}"
os.environ["DATABASE_URL"] = DB
sys.path.insert(0, os.getcwd())
import app.main as M  # noqa: E402
from app.accounts import service  # noqa: E402
from app.accounts.policy import Role  # noqa: E402
from app.accounts.router import _ensure_user_meta_row  # noqa: E402
from app.persistence import db as _db  # noqa: E402
with M.SessionLocal() as s:
    u = service.create_user(s, email=f"f-{secrets.token_hex(4)}@algosim.test", display_name="F", password="r" + secrets.token_hex(8), role=Role.STUDENT)
    s.flush(); _ensure_user_meta_row(s, u.id).custom_daily_limit = 100_000
    tok = service.new_session(s, user_id=u.id).token; s.commit()
_db.engine.dispose()


def owner():
    for ln in subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout.splitlines():
        p = ln.split()
        if len(p) >= 5 and p[1].endswith(":8000") and p[3] == "LISTENING":
            return int(p[4])


def start(cache, n):
    if owner():
        raise SystemExit("port 8000 busy")
    env = {**os.environ, "DATABASE_URL": DB, "HYBRID_ROUTE_MODE": "local-only-scoped", "ALLOW_LIVE_AI": "0", "LOCAL_SLM_CACHE_DIR": cache}
    env.pop("GEMINI_API_KEY", None)
    subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], env=env,
                     stdout=(OUT / f"server{n}.log").open("wb"), stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            h = httpx.get("http://127.0.0.1:8000/api/health", timeout=2, trust_env=False)
            if h.status_code == 200:
                return h.json()
        except Exception:
            pass
        time.sleep(0.5)


def stop():
    o = owner()
    if o:
        subprocess.run(["taskkill", "/PID", str(o), "/T", "/F"], capture_output=True)
    time.sleep(2)


def post():
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=180, trust_env=False) as c:
        c.cookies.set(service.SESSION_COOKIE, tok)
        t0 = time.perf_counter()
        r = c.post("/api/analyze", json={"input": {"type": "text", "content": text}})
        b = r.json()
        rd = b.get("route_d") or {}
        return {"http": r.status_code, "ms": round((time.perf_counter() - t0) * 1000, 1), "cache_control": r.headers.get("cache-control"),
                "route_status": rd.get("status"), "extraction_mode": rd.get("extraction_mode"), "reason_code": b.get("reason_code"),
                "failure_kind": b.get("failure_kind"), "learner_error": b.get("error")}


res = {"case_id": CID}
empty = OUT / "empty"; empty.mkdir()
try:
    h = start(str(empty), 1)
    res["health_unprovisioned"] = {k: h.get(k) for k in ("routeMode", "localOnlyMode", "localSlmReady", "aiAvailable")}
    res["unprovisioned_request"] = post()
    stop()
    h = start(os.environ["LOCAL_SLM_CACHE_DIR"], 2)
    res["health_provisioned"] = {k: h.get(k) for k in ("routeMode", "localOnlyMode", "localSlmReady", "aiAvailable")}
    res["first_request_cold_model"] = post()
    res["second_request_same_server"] = post()
    stop()
    start(os.environ["LOCAL_SLM_CACHE_DIR"], 3)
    res["after_restart_same_db"] = post()
finally:
    stop()
(OUT / "followup.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
