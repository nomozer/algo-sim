"""Measure the Hybrid B compiler benchmark (`tests/geometry/hybrid_compiler_benchmark.py`) — 0 model calls.

    python scripts/measure_hybrid_compiler_benchmark.py --out <NEW directory>

Writes `metrics.json` (per case × evaluation outcome, code, diagnosis; aggregate counts). Refuses an existing directory:
historical results are never overwritten.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ALLOW_LIVE_AI", "0")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    from tests.geometry import hybrid_compiler_benchmark as HB

    rows, totals = [], {arm: Counter() for arm in ("facts", "pipeline")}
    for c in HB.cases():
        for arm in totals:
            k = HB.classify(c, HB.run(c, arm))
            totals[arm][k["outcome"]] += 1
            if k.get("diagnosis"):
                totals[arm]["diagnosis:" + k["diagnosis"]] += 1
            if k["outcome"] == "correct_refusal":
                totals[arm]["refusal:" + k["class"]] += 1
            rows.append({"id": c["id"], "tier": c["tier"], "arm": arm, **{x: k.get(x) for x in ("outcome", "code", "class",
                                                                                                   "diagnosis")},
                         "gap": c.get("gap")})
    out.mkdir(parents=True)
    (out / "metrics.json").write_text(json.dumps({"cases": len(HB.cases()), "live_model_calls": 0,
                                                   "totals": {a: dict(sorted(t.items())) for a, t in totals.items()},
                                                   "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({a: dict(sorted(t.items())) for a, t in totals.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
