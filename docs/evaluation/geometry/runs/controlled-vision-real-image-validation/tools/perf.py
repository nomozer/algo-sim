"""Performance, memory and concurrency on the frozen candidate. Reuses the previous run's harness for the
cold/warm/cache, cold-process and stage measurements (same two images, same server states) so the numbers are
comparable with that run; adds a concurrency ladder, duplicate uploads, client abort and OCR-cache capacity.

Needs measured_app on the loopback port (HYBRID_ROUTE_MODE=local-first, own SQLite file). No provider call.
Run from backend/:  python <tools>/perf.py all
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / "docs/evaluation/geometry/runs/real-image-ocr-vision-comparative-acceptance/tools")]
import evaluate_acceptance as E  # noqa: E402
import httpx  # noqa: E402

E.RUN = RUN
PRIOR = ROOT / "docs/evaluation/geometry/runs/real-image-ocr-vision-comparative-acceptance"


def host() -> dict:
    ps = lambda cmd: subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True).stdout.strip()
    return {"cpu_model": ps("(Get-CimInstance Win32_Processor).Name"), "physical_cores": ps("(Get-CimInstance Win32_Processor).NumberOfCores"),
            "logical_cpus": os.cpu_count(), "total_ram_mib": round(int(ps("(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory")) / 1048576),
            "os": platform.platform(), "process_count": int(ps("(Get-Process).Count")),
            "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED (no 2-4 core / 4 GB machine available)"}


def corpus_paths() -> list[Path]:
    items = json.loads((RUN / "new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    return [ROOT / i["cache_path"] for i in items]


def failures(client) -> int:
    return len(client.get("/__evaluation/failures").json()["events"])


def ladder(rounds: int) -> dict:
    """n simultaneous uploads of DIFFERENT images, each from a new guest session; worker warm, caches cleared."""
    paths, levels = corpus_paths(), []
    with httpx.Client(base_url=E.BASE_URL, timeout=300, trust_env=False) as client:
        client.post("/__evaluation/reset")
        E.request_prepare(paths[0])  # warm the worker models once
        for n in (1, 2, 4, 8):
            rows = []
            for r in range(rounds):
                client.post("/__evaluation/reset")
                before = failures(client)
                chosen = [paths[(r * n + k) % len(paths)] for k in range(n)]
                start = time.perf_counter()
                with ThreadPoolExecutor(max_workers=n) as pool:
                    results = list(pool.map(E.request_prepare, chosen))
                wall = (time.perf_counter() - start) * 1000
                resources = client.get("/__evaluation/resources").json()
                rows.append({"round": r, "wall_ms": wall, "per_request_ms": [x["elapsed_ms"] for x in results],
                             "statuses": [x["http_status"] for x in results], "prepare_status": [x["result"].get("status") for x in results],
                             "server_exceptions": failures(client) - before, **E.peaks(resources.pop("samples"))})
            flat = [s for row in rows for s in row["statuses"]]
            latencies = [ms for row in rows for ms in row["per_request_ms"]]
            levels.append({"simultaneous": n, "rounds": rows, "requests": len(flat), "http_200": flat.count(200),
                           "http_5xx": sum(s >= 500 for s in flat), "server_exceptions": sum(row["server_exceptions"] for row in rows),
                           "per_request_ms": E.summary(latencies), "wall_ms": E.summary([row["wall_ms"] for row in rows]),
                           "combined_peak_rss_mib": E.summary([row["combined_process_tree_peak_rss_mib"] for row in rows if row["combined_process_tree_peak_rss_mib"]])})
            print("ladder", n, levels[-1]["http_200"], "/", levels[-1]["requests"], round(levels[-1]["per_request_ms"]["p50"]), flush=True)

        # Same image n times at once: one OCR, the others must wait for the lock and then hit the cache.
        client.post("/__evaluation/reset")
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as pool:
            same = list(pool.map(E.request_prepare, [paths[1]] * 4))
        duplicate = {"simultaneous": 4, "wall_ms": (time.perf_counter() - start) * 1000, "statuses": [x["http_status"] for x in same],
                     "per_request_ms": [x["elapsed_ms"] for x in same],
                     "ocr_cached_flags": [(((x["result"].get("provenance") or {}).get("local_ocr") or {}).get("timing") or {}).get("ocr_cached") for x in same]}

        # Client gives up after 0.3 s; the next upload measures whether the abandoned OCR still holds the worker.
        client.post("/__evaluation/reset")
        aborted = None
        try:
            with httpx.Client(base_url=E.BASE_URL, timeout=0.3, trust_env=False) as quick:
                quick.get("/api/auth/me")
                quick.post("/api/input/prepare", json=E.payload(paths[2]))
        except httpx.TimeoutException:
            aborted = True
        after = E.request_prepare(paths[3])
        client.post("/__evaluation/reset")
        alone = E.request_prepare(paths[3])
        cancel = {"client_aborted_after_ms": 300, "aborted": aborted, "next_request_ms": after["elapsed_ms"], "same_request_alone_ms": alone["elapsed_ms"],
                  "server_side_cancellation": "NOT_IMPLEMENTED: the abandoned OCR keeps the worker; the next upload waits for it" if after["elapsed_ms"] > alone["elapsed_ms"] * 1.3 else "NO_MEASURABLE_WAIT"}
    return {"levels": levels, "duplicate_uploads": duplicate, "client_abort": cancel}


def cache_capacity(count: int) -> dict:
    """Prepare `count` different images, then repeat the first: is its OCR (and its reread) still cached?"""
    paths = corpus_paths()[:count]
    with httpx.Client(base_url=E.BASE_URL, timeout=300, trust_env=False) as client:
        client.post("/__evaluation/reset")
        first = E.request_prepare(paths[0])
        for path in paths[1:]:
            E.request_prepare(path)
        entries = client.get("/__evaluation/resources").json()["ocr_cache_entries"]
        again = E.request_prepare(paths[0])
    timing = lambda r: (((r["result"].get("provenance") or {}).get("local_ocr") or {}).get("timing") or {})
    return {"distinct_images_before_repeat": count, "ocr_cache_entries_after": entries,
            "first_ms": first["elapsed_ms"], "repeat_ms": again["elapsed_ms"], "repeat_ocr_cached": timing(again).get("ocr_cached"),
            "repeat_reread_ms": timing(again).get("reread_ms"),
            "policy": "single OrderedDict: normal OCR inserts trim to 16 entries, reread inserts trim to 64; reread entries therefore count against the 16 OCR slots"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["benchmark", "coldprocess", "stages", "ladder", "cache", "all"])
    args = parser.parse_args()
    steps = ["benchmark", "coldprocess", "stages", "ladder", "cache"] if args.step == "all" else [args.step]
    if "benchmark" in steps:
        E.benchmark(10)
    if "coldprocess" in steps:
        E.cold_process(5)
    if "stages" in steps:
        E.stages(5)
    extra = json.loads((RUN / "concurrent_upload_reliability.json").read_text(encoding="utf-8")) if (RUN / "concurrent_upload_reliability.json").exists() else {}
    if "ladder" in steps:
        extra["ladder"] = ladder(3)
    if "cache" in steps:
        extra["cache_capacity"] = [cache_capacity(n) for n in (8, 20)]
    if "ladder" in steps or "cache" in steps:
        extra.update({**E.header(), "host": host(), "database": "SQLite file (development default); PostgreSQL NOT_MEASURED",
                      "production_concurrency_claim": "NONE: a single developer workstation with SQLite cannot establish production concurrency"})
        E.write("concurrent_upload_reliability.json", extra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
