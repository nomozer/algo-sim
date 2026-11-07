"""Bounded concurrency and input-robustness check of `POST /api/analyze` (staging-replay, offline, 0 provider calls).

1. Isolation: a sequential baseline body for K texts (served + refused), then the same texts plus malformed requests
   shuffled across W worker threads on ONE entered client. Every concurrent body must equal its sequential body; no 5xx.
2. Stampede: W threads post the SAME not-yet-cached served text at once — identical bodies, exactly one cache row.
3. Bad input: malformed JSON, wrong types, image type, empty/short/oversized text — a typed 4xx, never 5xx, no traceback.
4. Memory: R rounds of the mixed workload; traced Python memory after gc must not grow round over round.
Bounded by construction (K, W, R fixed below). Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out.json>
"""
from __future__ import annotations

import gc
import json
import random
import sys
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5] / "backend"))
import http_e2e_replay as H  # noqa: E402

K, W, R = 60, 8, 4
LEAK = ("Traceback", "File \"", "sqlalchemy", "GEMINI_API_KEY", "x-goog-api-key")


def main() -> None:
    out = Path(sys.argv[1])
    corpus = H.collect()
    rng = random.Random(20261107)
    texts = rng.sample(sorted(corpus), K)
    client = H.make_client(corpus)
    post = lambda body: client.post("/api/analyze", json=body)          # noqa: E731
    as_text = lambda t: {"input": {"type": "text", "content": t}}       # noqa: E731

    base = {t: post(as_text(t)).content for t in texts}
    bad = {
        "not_json": lambda: client.post("/api/analyze", content=b"{not json", headers={"content-type": "application/json"}),
        "missing_input": lambda: post({}),
        "wrong_type": lambda: post({"input": {"type": "video", "content": "x"}}),
        "content_not_string": lambda: post({"input": {"type": "text", "content": 12}}),
        "image_direct": lambda: post({"input": {"type": "image", "content": "aGVsbG8="}}),
        "empty": lambda: post(as_text("")),
        "too_short": lambda: post(as_text("chóp")),
        "oversized_2mb": lambda: post(as_text("Cho hình chóp S.ABC. " * 100_000)),
        "unknown_geometry_text": lambda: post(as_text("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 7. Tính thể tích.")),
    }
    bad_results = {}
    for name, fn in bad.items():
        r = fn()
        bad_results[name] = {"status": r.status_code, "leak": any(s in r.text for s in LEAK),
                             "reason_code": (r.json() if r.headers.get("content-type", "").startswith("application/json")
                                             else {}).get("reason_code")}

    def job(item):
        kind, t = item
        if kind == "bad":
            r = bad[t]()
            return kind, t, r.status_code, None
        r = post(as_text(t))
        return kind, t, r.status_code, r.content

    rounds, mismatches, five_xx, mem = [], 0, 0, []
    gc.collect()
    tracemalloc.start()
    for i in range(R):
        work = [("ok", t) for t in texts] + [("bad", b) for b in bad if b != "oversized_2mb"] * 2
        rng.shuffle(work)
        with ThreadPoolExecutor(W) as ex:
            res = list(ex.map(job, work))
        m = sum(1 for k, t, s, c in res if k == "ok" and c != base[t])
        f = sum(1 for _, _, s, _ in res if s >= 500)
        mismatches, five_xx = mismatches + m, five_xx + f
        gc.collect()
        mem.append(tracemalloc.get_traced_memory()[0])
        rounds.append({"round": i, "requests": len(res), "body_mismatch": m, "5xx": f})
    tracemalloc.stop()

    # Stampede on a served text that is not cached yet (fresh DB ⇒ nothing is).
    served = [t for t in texts if json.loads(base[t]).get("route_d", {}).get("status") == "SERVED"]
    client2 = H.make_client(corpus)
    from app.main import SessionLocal as S
    from app.persistence.db import SimulationCache

    target = served[0]
    with ThreadPoolExecutor(W) as ex:
        res = list(ex.map(lambda _: client2.post("/api/analyze", json=as_text(target)), range(W)))
    with S() as s:
        rows = s.query(SimulationCache).count()
    stampede = {"threads": W, "statuses": sorted({r.status_code for r in res}),
                "identical_bodies": len({r.content for r in res}) == 1, "cache_rows": rows,
                "cache_states": sorted(r.headers.get("X-Algosim-Cache") for r in res)}

    result = {"environment": {"mode": "staging-replay", "provider_calls": 0, "workers": W, "texts": K, "rounds": R},
              "isolation": {"rounds": rounds, "total_body_mismatch": mismatches, "total_5xx": five_xx,
                            "served_texts": len(served), "refused_texts": K - len(served)},
              "bad_input": bad_results, "stampede": stampede,
              "traced_memory_after_gc_bytes": mem,
              "memory_growth_last_vs_second_round_bytes": mem[-1] - mem[1]}
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "bad_input"}, ensure_ascii=False))
    print(json.dumps(bad_results, ensure_ascii=False))


if __name__ == "__main__":
    main()
