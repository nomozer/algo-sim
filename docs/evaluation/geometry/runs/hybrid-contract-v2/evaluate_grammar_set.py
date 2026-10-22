# -*- coding: utf-8 -*-
"""Run the LOCKED grammar / contract-v2 set (`grammar-set.json`, sha256 in `grammar-set.lock.json`) on Adapter /4.

Observed class of a refusal comes from the PRODUCT's own refusal taxonomy (`app.ai.hybrid_preview.classify_refusal`):
SOURCE_UNVERIFIED / MISSING_DATA → REFUSE_SOURCE, INVALID_DATA → REFUSE_GEOMETRY, CAPABILITY → REFUSE_KERNEL, anything
else → REFUSE_OTHER. A SERVE counts as correct only if every oracle answer matches exactly (squared coefficients).
0 provider calls. Run from `backend/`:  python <this file> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
HERE = Path(__file__).resolve().parent
LOCK_SHA = json.loads((HERE / "grammar-set.lock.json").read_text(encoding="utf-8"))["sha256_lf_normalised"]
_GROUP = {"SOURCE_UNVERIFIED": "REFUSE_SOURCE", "MISSING_DATA": "REFUSE_SOURCE", "INVALID_DATA": "REFUSE_GEOMETRY",
          "CAPABILITY": "REFUSE_KERNEL"}


def square_of(coef: str) -> Fraction:
    m = re.fullmatch(r"(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?", coef or "")
    if not m or not (m["p"] or m["r"]):
        raise ValueError(coef)
    p, r, q = Fraction(m["p"] or 1), Fraction(m["r"] or 1), Fraction(m["q"] or 1)
    return p * p * r / (q * q)


def load_lock() -> list[dict]:
    raw = (HERE / "grammar-set.json").read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != LOCK_SHA:
        raise SystemExit("grammar-set.json differs from its lock — refusing to evaluate an edited set")
    return json.loads(raw)["cases"]


def run_case(case: dict) -> dict:
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.hybrid_preview import classify_refusal

    t0 = time.perf_counter()
    r = run_typed_fact_next_v2_route(json.loads(json.dumps(case["payload"])))
    row = {"id": case["id"], "category": case["category"], "expected": case["expected"], "status": r.status,
           "code": r.code, "seconds": round(time.perf_counter() - t0, 4)}
    if r.status == "SERVED":
        got = {k: str(square_of(v["coef"])) for k, v in (r.answer_exact or {}).items()}
        row["answers"] = got
        row["answers_correct"] = all(got.get(k) == v for k, v in case["answers"].items())
        row["observed"] = "SERVE"
        row["source_authority"] = (r.route_d or {}).get("source_verification")
        row["derived_vertices"] = sum(v["provenance"] == "DERIVED_FRESH" for s in (r.route_d or {}).get("sections", [])
                                      for v in s["vertices"])
    else:
        row["observed"] = _GROUP.get(classify_refusal(r.code).group, "REFUSE_OTHER")
        row["reason"] = (r.reason or "")[:200]
    row["wrong_served"] = r.status == "SERVED" and (case["expected"] != "SERVE" or not row["answers_correct"])
    row["match"] = row["observed"] == case["expected"] and not row["wrong_served"]
    return row


def main(out: Path) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rows = [run_case(c) for c in load_lock()]
    agg = {"lock_sha256": LOCK_SHA, "cases": len(rows), "match": sum(r["match"] for r in rows),
           "wrong_served": [r["id"] for r in rows if r["wrong_served"]],
           "by_expected": {e: f"{sum(r['match'] for r in rows if r['expected'] == e)}/{sum(r['expected'] == e for r in rows)}"
                           for e in ("SERVE", "REFUSE_SOURCE", "REFUSE_GEOMETRY", "REFUSE_KERNEL")},
           "confusion": dict(Counter(f"{r['expected']} -> {r['observed']}" for r in rows)),
           "mismatches": [{k: r.get(k) for k in ("id", "expected", "observed", "code", "reason")} for r in rows if not r["match"]],
           "served_without_gate": [r["id"] for r in rows if r["status"] == "SERVED"
                                   and r.get("source_authority") != {"authority": "registry.kiem_nguon"}]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"classification": "DEVELOPMENT_EVALUATION_NOT_BLIND (preregistered)", "provider_calls": 0,
                               "aggregate": agg, "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in agg.items() if k != "mismatches"}, ensure_ascii=False, indent=1))
    for m in agg["mismatches"]:
        print(" ", m["id"], m["expected"], "->", m["observed"], m["code"], "|", (m.get("reason") or "")[:110])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
