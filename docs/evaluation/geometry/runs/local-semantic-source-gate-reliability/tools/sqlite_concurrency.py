"""SQLite concurrency before/after on a private loopback server and database. No provider call.

Starts `measured_app` (previous run's loopback wrapper: sanitized exception capture + process sampling) on its own
port and SQLite file, then for 1/2/4/8 simultaneous uploads × N rounds sends real /api/input/prepare requests, each
from a NEW guest session (GET /api/auth/me first, as the browser does). While uploads run, a probe thread times
GET /api/health every 100 ms: a blocked event loop shows up as health latency of whole seconds.
Run from backend/:  python <tools>/sqlite_concurrency.py --label before|after [--rounds 5]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "real-image-ocr-vision-comparative-acceptance/tools"
MANIFEST = RUN.parent / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json"
PORT = 8770
URL = f"http://127.0.0.1:{PORT}"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def start_server(db: Path) -> subprocess.Popen:
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": "", "HYBRID_ROUTE_MODE": "local-first", "PYTHONUTF8": "1",
           "PYTHONDONTWRITEBYTECODE": "1", "LOCAL_OCR_PYTHON": str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"),
           "LOCAL_OCR_TESSDATA": str(ROOT / ".superpowers/tessdata_fast"), "DATABASE_URL": "sqlite:///" + db.as_posix(),
           "PYTHONPATH": os.pathsep.join((str(ROOT / "backend"), str(PRIOR)))}
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "measured_app:app", "--host", "127.0.0.1", "--port", str(PORT),
                             "--log-level", "warning"], cwd=ROOT / "backend", env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 120:
        try:
            if httpx.get(URL + "/api/health", timeout=5, trust_env=False).status_code == 200:
                return proc
        except httpx.TransportError:
            time.sleep(0.3)
    proc.kill()
    raise SystemExit("server did not start")


def upload(path: Path) -> dict:
    """One browser-like upload. A dropped connection is a measured outcome (status 0), not a harness crash."""
    me_status, status, body, t0 = 0, 0, {}, time.perf_counter()
    try:
        with httpx.Client(base_url=URL, timeout=180, trust_env=False) as c:
            me_status = c.get("/api/auth/me").status_code
            t0 = time.perf_counter()
            r = c.post("/api/input/prepare", json={"content": base64.b64encode(path.read_bytes()).decode(), "filename": "problem.png"})
            status = r.status_code
            try:
                body = r.json()
            except ValueError:
                body = {}
    except httpx.TransportError as exc:
        body = {"transport_error": type(exc).__name__}
    return {"auth_me_status": me_status, "prepare_status": status, "ms": (time.perf_counter() - t0) * 1000,
            "reason_code": body.get("reason_code") if isinstance(body, dict) else None,
            "result": body.get("status") if isinstance(body, dict) else None,
            "transport_error": body.get("transport_error") if isinstance(body, dict) else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--rounds", type=int, default=5)
    args = ap.parse_args()
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    paths = [ROOT / i["cache_path"] for i in items]
    db = ROOT / f".superpowers/offline-logs/lsg-sqlite-{args.label}.db"
    if db.exists():
        db.unlink()
    server = start_server(db)
    levels = []
    try:
        upload(paths[0])  # load OCR models once: cold-model cost is measured elsewhere
        for n in (1, 2, 4, 8):
            rows, health = [], []
            for r_i in range(args.rounds):
                httpx.post(URL + "/__evaluation/reset", trust_env=False, timeout=30)
                before = len(httpx.get(URL + "/__evaluation/failures", trust_env=False, timeout=30).json()["events"])
                stop = threading.Event()

                def probe():
                    while not stop.is_set():
                        t = time.perf_counter()
                        try:
                            httpx.get(URL + "/api/health", timeout=60, trust_env=False)
                            health.append((time.perf_counter() - t) * 1000)
                        except httpx.TransportError:
                            health.append(None)
                        time.sleep(0.1)
                th = threading.Thread(target=probe, daemon=True)
                th.start()
                chosen = [paths[(r_i * n + k) % len(paths)] for k in range(n)]
                t0 = time.perf_counter()
                with ThreadPoolExecutor(max_workers=n) as pool:
                    res = list(pool.map(upload, chosen))
                wall = (time.perf_counter() - t0) * 1000
                stop.set()
                th.join()
                events = httpx.get(URL + "/__evaluation/failures", trust_env=False, timeout=30).json()["events"][before:]
                rows.append({"round": r_i, "wall_ms": wall, "requests": res, "server_exceptions": events})
            flat = [x for row in rows for x in row["requests"]]
            ok_health = [h for h in health if h is not None]
            levels.append({
                "simultaneous": n, "rounds": rows, "requests": len(flat),
                "prepare_200": sum(x["prepare_status"] == 200 for x in flat),
                "auth_me_5xx": sum(x["auth_me_status"] >= 500 for x in flat),
                "prepare_5xx": sum(x["prepare_status"] >= 500 for x in flat),
                "prepare_401": sum(x["prepare_status"] == 401 for x in flat),
                "prepare_401_after_auth_me_5xx": sum(x["prepare_status"] == 401 and x["auth_me_status"] >= 500 for x in flat),
                "transport_errors": sum(bool(x["transport_error"]) for x in flat),
                "server_exceptions": [{k: e.get(k) for k in ("path", "exception_type", "sqlite_errorname", "database_locked")}
                                      for row in rows for e in row["server_exceptions"]],
                "prepare_ms_p50": statistics.median(x["ms"] for x in flat),
                "health_probe_ms": {"n": len(health), "p50": statistics.median(ok_health) if ok_health else None,
                                    "max": max(ok_health) if ok_health else None, "over_1000ms": sum(h > 1000 for h in ok_health),
                                    "failed": sum(h is None for h in health)}})
            lv = levels[-1]
            print(args.label, n, f"{lv['prepare_200']}/{lv['requests']}", "auth5xx", lv["auth_me_5xx"], "prep5xx", lv["prepare_5xx"],
                  "401", lv["prepare_401"], "dropped", lv["transport_errors"], "health max", round(lv["health_probe_ms"]["max"] or 0), flush=True)
    finally:
        subprocess.run(["taskkill", "/PID", str(server.pid), "/T", "/F"], capture_output=True)
        server.wait(timeout=30)
    out = RUN / f"sqlite_concurrency_{args.label}.json"
    out.write_text(json.dumps({"run_id": RUN.name, "label": args.label, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                               "head": git("rev-parse", "HEAD"), "working_tree_dirty_paths": git("status", "--porcelain", "--", "backend/app").splitlines(),
                               "database": "SQLite file, fresh per run", "rounds_per_level": args.rounds, "images": "controlled-vision manifest, distinct per request",
                               "levels": levels}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
