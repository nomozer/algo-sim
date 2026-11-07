"""Per-stage latency profile of `POST /api/analyze` (staging-replay, offline, 0 provider calls).

Wraps the real stage functions in place (every module attribute bound to the original is rebound, so top-level and
call-time imports both hit the wrapper) and records INCLUSIVE wall time per request. Nesting (inclusive, not additive):
  http_total ⊃ orchestrator(run_hybrid_offline) ⊃ { extraction_validation, bridge_v2, planner, engine, adapter4 }
  engine(dung_tu_loi_goi) ⊃ { source_gate, ir_validate, interpreter_exec }
  run_function_route ⊃ engine + { scene3d_build, continuity_enrich, continuity_validate }
`json_dumps` is measured outside the request on the returned body (the handler's JSONResponse render is inside http).

Passes, same process, same data: (1) cold — first request of each distinct text after import, (2) warm miss — the
same texts on a fresh DB so every request misses the cache again with modules warm, (3) cache hit, (4) tracemalloc
peak per request on the served subset (separate pass: tracing distorts time).
Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out.json> [limit]
"""
from __future__ import annotations

import gc
import json
import statistics
import sys
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5] / "backend"))
import http_e2e_replay as H  # noqa: E402

TIMES: dict[str, float] = defaultdict(float)
STAGES = {
    "orchestrator": ("app.ai.hybrid_offline", "run_hybrid_offline"),
    "extraction_validation": ("app.ai.typed_fact_next_extraction", "extract_typed_fact_next_v2"),
    "bridge_v2": ("app.simulation.geometry_functions.typed_fact_next_bridge", "bridge_v2"),
    "planner": ("app.simulation.geometry_functions.planner", "lap_ke_hoach"),
    "engine": ("app.simulation.geometry_functions.engine", "dung_tu_loi_goi"),
    "source_gate": ("app.simulation.geometry_functions.registry", "kiem_nguon"),
    "ir_validate": ("app.simulation.semantic_program.validator", "validate_semantic_program"),
    "scene3d_build": ("app.simulation.semantic_program.scene3d", "build_scene3d"),
    "continuity_enrich": ("app.simulation.geometry_functions.construction_continuity", "enrich_construction_continuity"),
    "continuity_validate": ("app.simulation.geometry_functions.construction_continuity", "validate_construction_continuity"),
    "adapter4": ("app.ai.adapter4_route", "build_adapter4_response"),
    # HTTP layer around the route (not Hybrid work): ledger reserve/finalize, staging prepare, cache read/write.
    "usage_reserve": ("app.accounts.router", "reserve_analysis_usage"),
    "usage_finalize": ("app.accounts.router", "finalize_analysis_usage"),
    "prepare_replay": ("app.ai.hybrid_offline", "prepare_staging_replay"),
    "cache_lookup": ("app.main", "_cache_lookup"),
    "cache_store": ("app.main", "_store_route_d"),
    # Background task: TestClient waits for it, a deployed server sends the response first (not learner latency).
    "telemetry_background": ("app.accounts.router", "record_analyze_telemetry"),
}


def _wrap(name, fn):
    def timed(*a, **k):
        t = time.perf_counter()
        try:
            return fn(*a, **k)
        finally:
            TIMES[name] += time.perf_counter() - t
    timed.__wrapped__ = fn
    return timed


def install() -> None:
    import importlib

    for name, (mod, attr) in STAGES.items():
        m = importlib.import_module(mod)
        orig = getattr(m, attr)
        w = _wrap(name, orig)
        for other in list(sys.modules.values()):
            d = getattr(other, "__dict__", None)
            if d is not None:
                for k, v in list(d.items()):
                    if v is orig:
                        setattr(other, k, w)
    from app.simulation.semantic_program import interpreter as I

    orig_exec = I.SemanticProgramInterpreter.execute
    I.SemanticProgramInterpreter.execute = _wrap("interpreter_exec", orig_exec)


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(p * len(xs)))] * 1000, 2) if xs else None


def summary(rows):
    keys = sorted({k for r in rows for k in r})
    return {k: {"n": sum(1 for r in rows if k in r), "p50_ms": pct([r[k] for r in rows if k in r], .5),
                "p95_ms": pct([r[k] for r in rows if k in r], .95), "p99_ms": pct([r[k] for r in rows if k in r], .99),
                "mean_ms": round(statistics.mean([r[k] for r in rows if k in r]) * 1000, 2)} for k in keys}


def run_pass(client, texts):
    rows, served = [], []
    for t in texts:
        TIMES.clear()
        c0, w0 = time.process_time(), time.perf_counter()
        r = client.post("/api/analyze", json={"input": {"type": "text", "content": t}})
        row = {"http_total": time.perf_counter() - w0, "cpu_total": time.process_time() - c0, **TIMES}
        body = r.json()
        j0 = time.perf_counter()
        json.dumps(body, ensure_ascii=False)
        row["json_dumps"] = time.perf_counter() - j0
        st = (body.get("route_d") or {}).get("status", "DOMAIN_GATE")
        row["_status"], row["_cache"], row["_bytes"] = st, r.headers.get("X-Algosim-Cache"), len(r.content)
        rows.append(row)
        if st == "SERVED":
            served.append(t)
    return rows, served


def main() -> None:
    out = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    corpus = H.collect()
    texts = list(corpus)[:limit] if limit else list(corpus)
    install()
    client = H.make_client(corpus)
    cold, served = run_pass(client, texts)                     # pass 1: cold (first time in this process)
    hit, _ = run_pass(client, served)                          # pass 3: cache hit of served texts
    client2 = H.make_client(corpus)                            # fresh DB ⇒ every request misses again
    warm, _ = run_pass(client2, texts)                         # pass 2: warm modules, cache miss
    gc.collect()
    tracemalloc.start()
    peaks = []
    client3 = H.make_client(corpus)
    for t in served:                                           # pass 4: memory (miss path, separate: tracing is slow)
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        client3.post("/api/analyze", json={"input": {"type": "text", "content": t}})
        peaks.append(tracemalloc.get_traced_memory()[1] - base)
    tracemalloc.stop()

    def split(rows, status):
        return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows if (r["_status"] == "SERVED") == status]

    result = {
        "environment": {"python": sys.version.split()[0], "platform": sys.platform, "mode": "staging-replay",
                        "provider_calls": 0, "texts": len(texts), "served": len(served),
                        "note": "inclusive stage times; see module docstring for nesting"},
        "cold_miss_served": summary(split(cold, True)), "cold_refused": summary(split(cold, False)),
        "warm_miss_served": summary(split(warm, True)), "warm_refused": summary(split(warm, False)),
        "cache_hit_served": summary(split(hit, True)),
        "cache_states": {p: dict(sorted({s: sum(1 for r in rows if r["_cache"] == s) for s in
                                         {r["_cache"] for r in rows}}.items(), key=str)) for p, rows in
                         (("cold", cold), ("hit", hit), ("warm", warm))},
        "hit_rate_second_request_of_served": round(sum(1 for r in hit if r["_cache"] == "hit") / max(1, len(hit)), 4),
        "response_bytes_served": {"p50": int(statistics.median([r["_bytes"] for r in warm if r["_status"] == "SERVED"])),
                                  "max": max(r["_bytes"] for r in warm if r["_status"] == "SERVED")},
        "memory_peak_bytes_served_miss": {"p50": int(statistics.median(peaks)), "p95": sorted(peaks)[int(.95 * len(peaks))],
                                          "max": max(peaks)},
    }
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    w = result["warm_miss_served"]
    print(json.dumps({k: (w[k]["p50_ms"], w[k]["p95_ms"]) for k in w}, ensure_ascii=False))


if __name__ == "__main__":
    main()
