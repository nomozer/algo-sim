"""Measure run `hybrid-semantic-grounding-reliability`: corpus + unseen cases through the REAL fact route (offline,
authored Typed Facts, 0 model calls), classified against `oracle.json` and the preregistered labels.

    python measure.py --label BASE --out results/base-<sha>.json [--code-root <worktree>]
    python measure.py --compare results/a.json results/b.json

Classes: CORRECT_SERVED · WRONG_SERVED · CORRECT_REFUSAL · WRONG_CODE_REFUSAL · FALSE_REFUSAL. Never overwrites.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def squared(v):
    from app.simulation.geometry.radical import Radical
    return Fraction(v.he) ** 2 * v.can if isinstance(v, Radical) else Fraction(v) ** 2


def classify(case, r, want):
    served = r.status == "SERVED"
    if case["expect"] == "SERVE":
        if not served:
            return "FALSE_REFUSAL", None
        if set(r.answers) != set(want):
            return "WRONG_SERVED", f"answers {sorted(r.answers)} ≠ requests {sorted(want)}"
        for qid, v in want.items():
            got = r.exec_result.final_memory[f"kq_{qid}"]
            val = Fraction(got) if str(r.answers[qid]).startswith("cos²") else squared(got)
            if val != Fraction(v):
                return "WRONG_SERVED", f"{qid}: {val} ≠ oracle {v}"
        return "CORRECT_SERVED", None
    if case["expect"] == "NO_VALUE" and served and not r.answers:
        return "CORRECT_REFUSAL", "served without a value"
    if served:
        return "WRONG_SERVED", f"served {r.answers}"
    if case["refuse_codes"] and r.code not in case["refuse_codes"]:
        return "WRONG_CODE_REFUSAL", r.code
    return "CORRECT_REFUSAL", None


def run(label: str, out: Path) -> None:
    if out.exists():
        raise SystemExit(f"{out} exists — measurements are never overwritten")
    sys.path.insert(0, str(ROOT / "backend"))
    from app.ai.function_route import run_fact_route
    oracle = json.loads((HERE / "oracle.json").read_text(encoding="utf-8"))["values"]
    cases = (json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))["cases"]
             + json.loads((HERE / "unseen" / "cases.json").read_text(encoding="utf-8"))["cases"])
    rows = []
    for c in cases:
        r = run_fact_route(c["text"], deepcopy(c["payload"]))
        cls, why = classify(c, r, oracle.get(c["id"], {}))
        rows.append({"id": c["id"], "group": c["group"], "mechanism": c["mechanism"], "extraction": c["extraction"],
                     "expect": c["expect"], "source_requests": c["source_requests"], "status": r.status, "code": r.code,
                     "answers": r.answers, "class": cls, "why": why})
    sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "backend/app"],
                           capture_output=True, text=True).stdout.strip()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": label, "head": sha, "product_dirty": bool(dirty), "model_calls": 0,
                               "summary": summary(rows), "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary(rows), ensure_ascii=False, indent=1))


def summary(rows):
    def count(sel):
        return dict(Counter(r["class"] for r in rows if sel(r)))
    served = [r for r in rows if r["status"] == "SERVED"]
    tp = sum(r["expect"] == "SERVE" for r in served)
    fp = sum(r["class"] == "WRONG_SERVED" and r["expect"] != "SERVE" for r in served)
    fn = sum(r["class"] == "FALSE_REFUSAL" for r in rows)
    multi = [r for r in rows if r["source_requests"] >= 2]
    gap = [r for r in rows if r["extraction"] == "schema_gap"]
    return {
        "all": count(lambda r: True),
        "by_group": {g: count(lambda r, g=g: r["group"] == g) for g in sorted({r["group"] for r in rows})},
        "by_mechanism": {m: count(lambda r, m=m: r["mechanism"] == m) for m in sorted({r["mechanism"] for r in rows})},
        "source_certification": {"accepted_licensed": tp, "accepted_unlicensed": fp, "refused_licensed": fn,
                                 "precision": f"{tp}/{tp + fp}", "recall": f"{tp}/{tp + fn}"},
        "multi_goal": {"cases": len(multi), "silent_omission": sum(r["class"] == "WRONG_SERVED" for r in multi),
                       "complete": sum(r["class"] in ("CORRECT_SERVED", "CORRECT_REFUSAL") for r in multi),
                       "false_refusal": sum(r["class"] == "FALSE_REFUSAL" for r in multi)},
        "schema_gap_items": {"cases": len(gap), "wrong_served": sum(r["class"] == "WRONG_SERVED" for r in gap)},
        "not_measured_offline": ["intent accuracy", "entity/reference grounding accuracy of an extractor",
                                 "goal interpretation accuracy of an extractor"],
    }


def compare(a: Path, b: Path) -> None:
    ra, rb = (json.loads(p.read_text(encoding="utf-8")) for p in (a, b))
    xa, xb = ({r["id"]: r for r in x["rows"]} for x in (ra, rb))
    for cid in xa:
        if (xa[cid]["class"], xa[cid]["code"]) != (xb[cid]["class"], xb[cid]["code"]):
            print(f"{cid:42} {xa[cid]['class']:20} {xa[cid]['code'] or '':28} → {xb[cid]['class']:20} {xb[cid]['code'] or ''}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--compare", type=Path, nargs=2)
    a = ap.parse_args()
    if a.compare:
        compare(*a.compare)
    else:
        run(a.label, a.out)
