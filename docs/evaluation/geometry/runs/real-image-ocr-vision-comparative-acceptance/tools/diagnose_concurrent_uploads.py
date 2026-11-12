"""Bounded actual-HTTP concurrency check with sanitized server-side exception metadata."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import time

import httpx
import evaluate_acceptance as evaluation

phase = sys.argv[1]
assert phase in ("before", "after")
rows = []
with httpx.Client(base_url=evaluation.BASE_URL, timeout=120, trust_env=False) as client:
    for index in range(5):
        client.post("/__evaluation/reset", params={"cold": False})
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(evaluation.request_prepare, evaluation.bench_paths()))
        rows.append({"round": index, "elapsed_ms": (time.perf_counter() - started) * 1000,
                     "requests": [{"http_status": r["http_status"], "elapsed_ms": r["elapsed_ms"],
                                   "prepare_status": r["result"].get("status"), "reason_code": r["result"].get("reason_code")}
                                  for r in results]})
        print(index, [r["http_status"] for r in results], flush=True)
    events = client.get("/__evaluation/failures").json()
    resources = client.get("/__evaluation/resources").json()
result = {**evaluation.header(), "phase": phase, "endpoint": evaluation.BASE_URL, "rounds": rows,
          "exception_events": events, "current_resources": resources["current"],
          "provider_calls": 0, "raw_error_messages_recorded": False}
evaluation.write(f"concurrent_upload_diagnosis_{phase}.json", result)
