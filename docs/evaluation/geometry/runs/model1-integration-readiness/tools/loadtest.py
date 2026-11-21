"""AXO /17 P4 — runtime reliability & concurrency on the dev host (real uvicorn + real llama-server, local-only-scoped).

usage (cwd = <worktree>/backend): python loadtest.py <out_dir> <rows_of_P_all.jsonl> <manifest_list.txt>
Writes requests.jsonl, phases.json, server*.log, stack.csv into <out_dir> (refuses a non-empty dir). 0 external calls.
"""
from __future__ import annotations

import json
import os
import random
import secrets
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

OUT = Path(sys.argv[1])
P_ROWS = Path(sys.argv[2])
MANIFESTS = [Path(p) for p in Path(sys.argv[3]).read_text().strip().split(",")]
if OUT.exists() and any(OUT.iterdir()):
    raise SystemExit(f"refusing to write into non-empty {OUT}")
OUT.mkdir(parents=True, exist_ok=True)
PY = sys.executable
PORT = 8000
BASE = f"http://127.0.0.1:{PORT}"
DB = f"sqlite:///{(OUT / 'load.db').as_posix()}"
SAMPLER = Path("../docs/evaluation/geometry/harness/live-acceptance/stack_memory_sampler.ps1").resolve()
SLM_CACHE = os.environ["LOCAL_SLM_CACHE_DIR"]

# ── text pools (classified by the deterministic-only arm P on candidate 157) ─────────────────────────────────────────
texts = {}
for mp in MANIFESTS:
    m = json.loads(mp.read_text(encoding="utf-8"))
    for c in (m.get("valid_cases") or []) + (m.get("negative_cases") or []):
        texts[(mp.parent.name + "/" + mp.name, c["case_id"])] = c["original_input"]
pools = {"det": [], "slm": [], "neg_fast": [], "neg_slm": []}
seen = set()
for line in P_ROWS.read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    t = texts[(r["source"], r["case_id"])]
    if t in seen:
        continue
    seen.add(t)
    escalates = r["reason_code"] == "LIVE_AI_DISABLED"
    if r["group"] == "valid_cases":
        if r["route_status"] == "SERVED":
            pools["det"].append(t)
        elif escalates:
            pools["slm"].append(t)
    else:
        (pools["neg_slm"] if escalates else pools["neg_fast"]).append(t)
rnd = random.Random(17)
for v in pools.values():
    rnd.shuffle(v)
print({k: len(v) for k, v in pools.items()}, flush=True)


def take(pool, n):
    out, pools[pool] = pools[pool][:n], pools[pool][n:]
    if len(out) < n:
        raise SystemExit(f"pool {pool} exhausted")
    return out


# ── seed accounts with a high custom daily limit (same mechanism as tests/route_client.py) ───────────────────────────
os.environ["DATABASE_URL"] = DB
sys.path.insert(0, os.getcwd())
import app.main as M  # noqa: E402
from app.accounts import service  # noqa: E402
from app.accounts.policy import Role  # noqa: E402
from app.accounts.router import _ensure_user_meta_row  # noqa: E402

TOKENS = []
with M.SessionLocal() as s:
    for i in range(24):
        u = service.create_user(s, email=f"load-{i}-{secrets.token_hex(4)}@algosim.test", display_name=f"Load {i}",
                                password="r" + secrets.token_hex(8), role=Role.STUDENT)
        s.flush()
        _ensure_user_meta_row(s, u.id).custom_daily_limit = 100_000
        TOKENS.append(service.new_session(s, user_id=u.id).token)
    s.commit()
M.engine.dispose() if hasattr(M, "engine") else None
from app.persistence import db as _db  # noqa: E402
_db.engine.dispose()
COOKIE = service.SESSION_COOKIE

# ── server lifecycle ─────────────────────────────────────────────────────────────────────────────────────────────────
server = {"proc": None, "n": 0}


def port_owner() -> int | None:
    out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
    for ln in out.splitlines():
        p = ln.split()
        if len(p) >= 5 and p[1].endswith(f":{PORT}") and p[3] == "LISTENING":
            return int(p[4])
    return None


def pids_named(name: str) -> list[int]:
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    return [int(ln.split('","')[1]) for ln in out.splitlines() if ln.startswith(f'"{name}"')]


def start_server(slm_cache: str = SLM_CACHE) -> float:
    if port_owner() is not None:
        raise SystemExit(f"port {PORT} busy — refusing to touch a process this task does not own")
    env = {**os.environ, "DATABASE_URL": DB, "HYBRID_ROUTE_MODE": "local-only-scoped", "ALLOW_LIVE_AI": "0",
           "LOCAL_SLM_CACHE_DIR": slm_cache, "PYTHONIOENCODING": "utf-8"}
    env.pop("GEMINI_API_KEY", None)
    server["n"] += 1
    log = (OUT / f"server{server['n']}.log").open("wb")
    t0 = time.perf_counter()
    server["proc"] = subprocess.Popen([PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
                                      cwd=os.getcwd(), env=env, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(240):
        try:
            if httpx.get(f"{BASE}/api/health", timeout=2, trust_env=False).status_code == 200:
                return round((time.perf_counter() - t0) * 1000, 1)
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit("server did not become healthy")


def stop_server():
    owner = port_owner()
    llama_before = pids_named("llama-server.exe")
    for pid in [owner] if owner else []:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    if server["proc"] is not None:
        try:
            server["proc"].kill()
        except Exception:
            pass
    time.sleep(1.5)
    # llama-server children of OUR server only (started after this task began; the host had none at task start)
    for pid in set(pids_named("llama-server.exe")) & set(llama_before):
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)


# ── request plumbing ─────────────────────────────────────────────────────────────────────────────────────────────────
REQ_F = (OUT / "requests.jsonl").open("w", encoding="utf-8")
LOCK = threading.Lock()


def client(i: int, timeout: float = 180.0) -> httpx.Client:
    c = httpx.Client(base_url=BASE, timeout=timeout, trust_env=False)
    c.cookies.set(COOKIE, TOKENS[i % len(TOKENS)])
    return c


def send(c: httpx.Client, phase: str, text: str, kind: str, headers: dict | None = None) -> dict:
    t0 = time.perf_counter()
    rec = {"phase": phase, "kind": kind, "t_start": round(t0, 3)}
    try:
        r = c.post("/api/analyze", json={"input": {"type": "text", "content": text}}, headers=headers or {})
        rec["http"] = r.status_code
        rec["cache_control"] = r.headers.get("cache-control")
        rec["replayed"] = r.headers.get("idempotent-replayed")
        try:
            b = r.json()
        except Exception:
            b = {}
        rd = b.get("route_d") or {}
        tel = rd.get("adaptive_telemetry") or {}
        st = ((rd.get("slm_grounding_envelope") or {}).get("stage_timings") or rd.get("stage_timings") or {})
        rec.update(route_status=rd.get("status"), extraction_mode=rd.get("extraction_mode"),
                   reason_code=(rd.get("refusal") or {}).get("reason_code") or b.get("reason_code"),
                   failure_kind=b.get("failure_kind"), chosen_route=tel.get("chosen_route"),
                   slm_queue_wait_ms=st.get("queue_wait_ms"), slm_inference_ms=st.get("slm_inference_ms"),
                   server_load_time_ms=st.get("server_load_time_ms"))
    except Exception as e:
        rec["http"] = None
        rec["client_error"] = type(e).__name__
    rec["ms"] = round((time.perf_counter() - t0) * 1000, 1)
    with LOCK:
        REQ_F.write(json.dumps(rec, ensure_ascii=False) + "\n")
        REQ_F.flush()
    return rec


def pct(v, q):
    if not v:
        return None
    s = sorted(v)
    return round(s[min(len(s) - 1, int(round((len(s) - 1) * q)))], 1)


PHASES = []


def run_phase(name: str, items: list[tuple[str, str]], conc: int, health_probe: bool = False) -> dict:
    clients = [client(i) for i in range(conc)]
    probe = {"stop": False, "ms": []}

    def _probe():
        with httpx.Client(base_url=BASE, timeout=30, trust_env=False) as hc:
            while not probe["stop"]:
                t0 = time.perf_counter()
                try:
                    hc.get("/api/health")
                    probe["ms"].append((time.perf_counter() - t0) * 1000)
                except Exception:
                    probe["ms"].append(None)
                time.sleep(0.5)

    th = threading.Thread(target=_probe, daemon=True) if health_probe else None
    if th:
        th.start()
    idx = {"i": 0}
    ilock = threading.Lock()

    def worker(w: int):
        out = []
        while True:
            with ilock:
                if idx["i"] >= len(items):
                    return out
                kind, text = items[idx["i"]]
                idx["i"] += 1
            out.append(send(clients[w], name, text, kind))

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=conc) as ex:
        recs = [r for f in [ex.submit(worker, w) for w in range(conc)] for r in f.result()]
    wall = time.perf_counter() - t0
    probe["stop"] = True
    if th:
        th.join()
    for c in clients:
        c.close()
    ok = [r["ms"] for r in recs if r.get("http") == 200]
    by_status = {}
    for r in recs:
        k = f"{r.get('http')}:{r.get('route_status') or r.get('reason_code') or r.get('client_error')}"
        by_status[k] = by_status.get(k, 0) + 1
    qw = [r["slm_queue_wait_ms"] for r in recs if isinstance(r.get("slm_queue_wait_ms"), (int, float))]
    inf = [r["slm_inference_ms"] for r in recs if isinstance(r.get("slm_inference_ms"), (int, float))]
    summ = {
        "phase": name, "concurrency": conc, "n": len(recs), "wall_s": round(wall, 2),
        "throughput_rps": round(len(recs) / wall, 3) if wall else None,
        "http_200": len(ok), "by_status": by_status,
        "busy_503": sum(1 for r in recs if r.get("reason_code") == "LOCAL_SLM_BUSY"),
        "no_store_on_errors": all((r.get("cache_control") or "").find("no-store") >= 0 for r in recs if (r.get("http") or 0) >= 500),
        "e2e_ms_200": {"n": len(ok), "p50": round(statistics.median(ok), 1) if ok else None, "p95": pct(ok, 0.95),
                        "p99": pct(ok, 0.99) if len(ok) >= 100 else "NOT_COMPUTED_n<100", "max": max(ok) if ok else None},
        "slm_queue_wait_ms": {"n": len(qw), "p50": round(statistics.median(qw), 1) if qw else None, "max": max(qw) if qw else None},
        "slm_inference_ms": {"n": len(inf), "p50": round(statistics.median(inf), 1) if inf else None, "p95": pct(inf, 0.95)},
    }
    if health_probe:
        hp = [x for x in probe["ms"] if x is not None]
        summ["health_probe_ms"] = {"n": len(probe["ms"]), "failed": probe["ms"].count(None),
                                   "p50": round(statistics.median(hp), 1) if hp else None, "max": round(max(hp), 1) if hp else None}
    PHASES.append(summ)
    print(json.dumps(summ, ensure_ascii=False), flush=True)
    return summ


def note(name: str, **kw):
    rec = {"phase": name, **kw}
    PHASES.append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


sampler = subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SAMPLER), str(OUT / "stack.csv")],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    note("server_start_1", startup_ms=start_server(), llama_running_before_first_request=bool(pids_named("llama-server.exe")))
    served_texts: list[str] = []

    # F1 cold start: first SLM request pays the llama-server load
    r = run_phase("cold_start_slm", [("slm", t) for t in take("slm", 1)], 1)
    note("after_cold_start", llama_pids=pids_named("llama-server.exe"))
    run_phase("warm_slm_c1", [("slm", t) for t in take("slm", 6)], 1)

    det_all = take("det", 70)
    served_texts += det_all[:10]
    for conc, n in ((1, 10), (2, 10), (5, 20), (10, 30)):
        run_phase(f"det_c{conc}", [("det", t) for t in det_all[:n]], conc)
        det_all = det_all[n:]
    for conc, n in ((2, 8), (5, 10), (10, 20)):
        run_phase(f"slm_c{conc}", [("slm", t) for t in take("slm", n)], conc, health_probe=(conc == 10))
    for conc, n in ((5, 20), (10, 30)):
        mix = [("slm", t) for t in take("slm", n // 2)] + [("det", t) for t in take("det", n - n // 2)]
        rnd.shuffle(mix)
        run_phase(f"mixed_c{conc}", mix, conc, health_probe=True)
    refusal = [("neg_fast", t) for t in take("neg_fast", 10)] + [("neg_slm", t) for t in take("neg_slm", min(10, len(pools["neg_slm"])))]
    rnd.shuffle(refusal)
    run_phase("refusal_c5", refusal, 5)
    run_phase("cache_hit_c5", [("cache", t) for t in served_texts] * 2, 5)

    # F2 llama-server killed while idle → next SLM request
    killed = pids_named("llama-server.exe")
    for pid in killed:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    time.sleep(1)
    with client(0) as c:
        a = send(c, "kill_idle_next", take("slm", 1)[0], "slm")
        b = send(c, "kill_idle_next2", take("slm", 1)[0], "slm")
    note("kill_llama_idle", killed=killed, first_after=a, second_after=b, llama_pids_after=pids_named("llama-server.exe"))

    # F3 llama-server killed mid-inference
    res = {}
    t_mid = take("slm", 1)[0]
    th = threading.Thread(target=lambda: res.setdefault("r", send(client(1), "kill_mid", t_mid, "slm")))
    th.start()
    time.sleep(1.2)
    killed = pids_named("llama-server.exe")
    for pid in killed:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    th.join()
    with client(2) as c:
        after = send(c, "kill_mid_next", take("slm", 1)[0], "slm")
        again = send(c, "kill_mid_resubmit_same_text", t_mid, "slm")
    note("kill_llama_mid_inference", killed=killed, in_flight=res.get("r"), next_request=after, resubmit_same_text=again)

    # F4 client disconnect (client gives up after 1 s) → server keeps serving; re-send of same text
    t_dc = take("slm", 1)[0]
    with client(3, timeout=1.0) as c:
        dc = send(c, "client_disconnect", t_dc, "slm")
    time.sleep(12)
    with client(3) as c:
        h = c.get("/api/health").status_code
        re_send = send(c, "client_disconnect_resend", t_dc, "slm")
    note("client_disconnect", abandoned=dc, health_after=h, resend_same_text=re_send)

    # F5 repeated submission: same key ×2 concurrently (coalesced) vs no key ×2
    t_rep = take("slm", 1)[0]
    key = "axo17-" + secrets.token_hex(12)
    out = []
    ths = [threading.Thread(target=lambda: out.append(send(client(4), "dup_same_key", t_rep, "slm", {"Idempotency-Key": key}))) for _ in range(2)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    t_rep2 = take("slm", 1)[0]
    out2 = []
    ths = [threading.Thread(target=lambda: out2.append(send(client(5), "dup_no_key", t_rep2, "slm"))) for _ in range(2)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    note("repeated_submission", same_key=out, no_key=out2)

    # F6 backend restart: persisted cache survives; model reloads lazily
    stop_server()
    note("server_start_2_after_restart", startup_ms=start_server())
    with client(6) as c:
        hit = send(c, "restart_cache_hit", t_rep, "cache")
        cold2 = send(c, "restart_cold_slm", take("slm", 1)[0], "slm")
    note("backend_restart", cache_hit_after_restart=hit, first_slm_after_restart=cold2)

    # F7 model runtime not provisioned → SLM path fails closed as infrastructure, deterministic path still serves
    stop_server()
    empty = OUT / "empty_slm_cache"
    empty.mkdir()
    note("server_start_3_unprovisioned", startup_ms=start_server(str(empty)))
    with client(7) as c:
        u1 = send(c, "unprovisioned_slm", take("slm", 1)[0], "slm")
        u2 = send(c, "unprovisioned_det", take("det", 1)[0], "det")
    note("runtime_unprovisioned", slm_request=u1, det_request=u2)
finally:
    stop_server()
    sampler.kill()
    REQ_F.close()
    (OUT / "phases.json").write_text(json.dumps(PHASES, ensure_ascii=False, indent=1), encoding="utf-8")
