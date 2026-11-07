"""Long-run retention check of `POST /api/analyze` (staging-replay, offline): live parsed payloads after gc, per round.

R rounds of the same 60 texts (served ones hit the cache after round 0, refused ones re-run extraction every round).
A bounded cache plateaus; a leak grows by a constant per round. Before commit cb79848f: +3 payloads per round.
Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out.json> [rounds]
"""
from __future__ import annotations

import gc
import json
import random
import sys
import tracemalloc
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5] / "backend"))
import http_e2e_replay as H  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1])
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    from app.simulation.geometry_functions.typed_fact_next import TypedFactNextPayloadV2, TypedFactNextValidationError

    corpus = H.collect()
    texts = random.Random(1).sample(sorted(corpus), 60)
    client = H.make_client(corpus)
    for t in texts:                                           # warm: fill the product cache once
        client.post("/api/analyze", json={"input": {"type": "text", "content": t}})
    tracemalloc.start()
    payloads, errors, traced = [], [], []
    for _ in range(rounds):
        for t in texts:
            client.post("/api/analyze", json={"input": {"type": "text", "content": t}})
        gc.collect()
        traced.append(tracemalloc.get_traced_memory()[0])    # BEFORE the object census: its list is itself megabytes
        objs = gc.get_objects()
        payloads.append(sum(isinstance(o, TypedFactNextPayloadV2) for o in objs))
        errors.append(sum(isinstance(o, TypedFactNextValidationError) for o in objs))
        del objs
    tracemalloc.stop()
    result = {"rounds": rounds, "requests_per_round": len(texts), "live_payloads": payloads,
              "live_validation_errors": errors, "traced_bytes_after_gc": traced,
              "traced_growth_last_half_bytes": traced[-1] - traced[rounds // 2]}
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "traced_bytes_after_gc"}))


if __name__ == "__main__":
    main()
