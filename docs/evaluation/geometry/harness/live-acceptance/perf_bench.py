"""Measure concurrency, warm/repeat, and cold-boot latencies + aggregate stack_memory.csv for /12 §22."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import statistics
import time

import httpx


def _pct(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, int(round((len(s) - 1) * p))))
    return round(s[idx], 1)


def _stats(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0, "min_ms": None, "p50_ms": None, "p95_ms": None, "max_ms": None}
    return {
        "n": len(vals),
        "min_ms": round(min(vals), 1),
        "p50_ms": round(statistics.median(vals), 1),
        "p95_ms": _pct(vals, 0.95),
        "max_ms": round(max(vals), 1),
    }


def _register_client(base_url: str, tag: str) -> httpx.Client:
    c = httpx.Client(base_url=base_url, timeout=120.0, trust_env=False)
    r = c.post(
        "/api/auth/register",
        json={
            "email": f"perf_{tag}_{int(time.time() * 1000)}@algosim.test",
            "displayName": "Perf Probe",
            "password": "AxoEval" + "Pass!2026",
        },
    )
    r.raise_for_status()
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--browser-checks", required=True, type=Path)
    ap.add_argument("--freeze", required=True, type=Path)
    ap.add_argument("--stack-csv", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite {args.out}: evidence is never overwritten")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    checks = json.loads(args.browser_checks.read_text(encoding="utf-8"))
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))

    by_id = {c["case_id"]: c for c in manifest["valid_cases"] + manifest["negative_cases"]}
    stratum_by_id = {r["case_id"]: r["stratum"] for r in freeze["rows"]}
    rows = checks["results"]

    det_served_ms = [
        float(r["ms"])
        for r in rows
        if r.get("group") == "valid"
        and r.get("route_status") == "SERVED"
        and not str(r.get("extraction_mode") or "").startswith("LOCAL_SLM")
        and stratum_by_id.get(r["case_id"]) == "PARSER_COMPLETE"
    ]
    det_fallback_ms = [
        float(r["ms"])
        for r in rows
        if r.get("group") == "valid"
        and r.get("route_status") == "SERVED"
        and not str(r.get("extraction_mode") or "").startswith("LOCAL_SLM")
        and stratum_by_id.get(r["case_id"]) == "SLM_REQUIRED"
    ]
    slm_served_ms = [
        float(r["ms"])
        for r in rows
        if r.get("route_status") == "SERVED" and str(r.get("extraction_mode") or "").startswith("LOCAL_SLM")
    ]
    rejected_valid_ms = [
        float(r["ms"]) for r in rows if r.get("group") == "valid" and r.get("route_status") != "SERVED"
    ]
    negative_ms = [float(r["ms"]) for r in rows if r.get("group") == "negative"]

    # Pick up to 4 distinct served deterministic & 2 distinct served SLM (or fallback) prompts for concurrency probes
    det_ids = [
        r["case_id"]
        for r in rows
        if r.get("route_status") == "SERVED" and not str(r.get("extraction_mode") or "").startswith("LOCAL_SLM")
    ][:4]
    slm_ids = [
        r["case_id"]
        for r in rows
        if r.get("route_status") == "SERVED" and str(r.get("extraction_mode") or "").startswith("LOCAL_SLM")
    ]

    # Warm cached repeat check
    warm_cache_hit_ms = []
    c_warm = _register_client(args.base_url, "warm")
    try:
        for cid in det_ids[:4]:
            t0 = time.perf_counter()
            r = c_warm.post("/api/analyze", json={"input": {"type": "text", "content": by_id[cid]["original_input"]}})
            warm_cache_hit_ms.append((time.perf_counter() - t0) * 1000.0)
            assert r.status_code == 200
    finally:
        c_warm.close()

    # Concurrency probes (2 and 4 concurrent users on /api/analyze)
    def run_conc(n_workers: int, prompts: list[str], tag_prefix: str) -> dict:
        clients = [_register_client(args.base_url, f"{tag_prefix}_{k}") for k in range(n_workers)]
        try:
            def _one(idx: int) -> tuple[int, float]:
                txt = prompts[idx % len(prompts)]
                t0 = time.perf_counter()
                resp = clients[idx].post("/api/analyze", json={"input": {"type": "text", "content": txt}})
                return resp.status_code, (time.perf_counter() - t0) * 1000.0

            t_wall0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=n_workers) as ex:
                res = list(ex.map(_one, range(n_workers)))
            wall_ms = (time.perf_counter() - t_wall0) * 1000.0
            return {
                "workers": n_workers,
                "statuses": [s for s, _ in res],
                "all_200": all(s == 200 for s, _ in res),
                "wall_ms": round(wall_ms, 1),
                "request_stats": _stats([ms for _, ms in res]),
            }
        finally:
            for c in clients:
                c.close()

    det_prompts = [by_id[cid]["original_input"] for cid in det_ids] or [manifest["valid_cases"][0]["original_input"]]
    conc2 = run_conc(2, det_prompts, "c2")
    conc4 = run_conc(4, det_prompts, "c4")
    mixed_prompts = [by_id[cid]["original_input"] for cid in (slm_ids[:2] + det_ids[:2])] or det_prompts
    conc2_mixed = run_conc(2, mixed_prompts, "c2m")

    # Resource peaks from stack_memory.csv
    mem_peaks: dict[str, dict] = {}
    if args.stack_csv.exists():
        with args.stack_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                if len(r) < 6:
                    continue
                grp = r[1]
                pid_count = int(r[2].strip() or 0)
                ws = float(r[3].strip() or 0.0)
                pv = float(r[4].strip() or 0.0)
                cpu = float(r[5].strip() or 0.0)
                cur = mem_peaks.setdefault(grp, {"samples": 0, "max_pid_count": 0, "peak_ws_mb": 0.0, "peak_private_mb": 0.0, "max_cpu_s": 0.0})
                cur["samples"] += 1
                cur["max_pid_count"] = max(cur["max_pid_count"], pid_count)
                cur["peak_ws_mb"] = max(cur["peak_ws_mb"], ws)
                cur["peak_private_mb"] = max(cur["peak_private_mb"], pv)
                cur["max_cpu_s"] = max(cur["max_cpu_s"], cpu)

    report = {
        "schema": "axo-performance-report/1",
        "harness_version": "axo-live-acceptance-harness/1",
        "scope_note": "Measured on Windows dev host only; no cross-hardware claims.",
        "uncached_live_latency_ms": {
            "deterministic_parser_complete_served": _stats(det_served_ms),
            "slm_required_stratum_deterministic_or_normalizer_rescued": _stats(det_fallback_ms),
            "live_slm_contributed_served": _stats(slm_served_ms),
            "rejected_valid_cases": _stats(rejected_valid_ms),
            "rejected_negative_cases": _stats(negative_ms),
        },
        "warm_cache_hit_ms": _stats(warm_cache_hit_ms),
        "concurrency": {
            "conc_2_deterministic": conc2,
            "conc_4_deterministic": conc4,
            "conc_2_mixed_slm_and_det": conc2_mixed,
        },
        "resource_peaks_from_stack_sampler": mem_peaks,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"det_p50": report["uncached_live_latency_ms"]["deterministic_parser_complete_served"]["p50_ms"],
                      "slm_p50": report["uncached_live_latency_ms"]["live_slm_contributed_served"]["p50_ms"],
                      "mem_groups": list(mem_peaks.keys())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
