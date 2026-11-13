"""Locked internal holdout evaluation of run `independent-geometry-plane-constraints`, exactly as preregistered in
evaluation_preregistration.json (commit 60ce483cc): problem text only → route_text_input(allow_live_ai=False), once for
the start product (archive of ea4b2a197) and once for the frozen candidate; geometry scored against the curators'
rational oracle with id-independent descriptors. Prints ids, counts and codes only — never a problem text.

  python eval_locked.py <before_backend_dir>          # from the worktree root
  python eval_locked.py --child                       # internal
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
RUNS = RUN.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
SETS = {"LOCKED_W2": (RUNS / "hybrid-v2-independent-vietnamese-section-holdout-wave2", "holdout-wave2"),
        "LOCKED_W3": (RUNS / "hybrid-v2-independent-vietnamese-geometry-holdout-wave3", "holdout-wave3")}


def child() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input
    out = {}
    for cid, text in json.loads(sys.stdin.read()).items():
        try:
            r = route_text_input(text, allow_live_ai=False).response
            rd = r.get("route_d") or {}
            sc = (r.get("envelope") or {}).get("scene3d")
            out[cid] = {"status": rd.get("status"), "reason": r.get("reason_code") or (rd.get("refusal") or {}).get("code"),
                        "scene": {"objects": sc["objects"], "chart_metric": sc["chart_metric"]} if sc and rd.get("status") == "SERVED" else None}
        except Exception as e:                                  # noqa: BLE001 — recorded, counts as a failure
            out[cid] = {"status": "ROUTE_ERROR", "reason": type(e).__name__, "scene": None}
    print(json.dumps(out, ensure_ascii=False))


def run(backend: Path, texts: dict) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--child"], input=json.dumps(texts, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def lab(x: str) -> str:
    return str(x).replace("′", "'").replace("’", "'").strip()


def oracle_ring(exp: dict) -> list[tuple]:
    ring = []
    for b in exp["boundary"]:
        if "vertex" in b:
            ring.append(("VERTEX", lab(b["vertex"])))
        else:
            u, v = lab(b["edge"][0]), lab(b["edge"][1])
            t = F(str(b["t"]))
            a, c = sorted((u, v))
            ring.append(("EDGE", a, c, t if u == a else 1 - t))
    return ring


def cyclic_equal(a: list, b: list) -> bool:
    if len(a) != len(b):
        return False
    for r in (b, b[::-1]):
        for i in range(len(r)):
            if a == r[i:] + r[:i]:
                return True
    return False


def score(case: dict, exp: dict | None, got: dict) -> dict:
    import verify_plane_constraints as V
    served = got["status"] == "SERVED" and got["scene"] is not None
    row = {"id": case["id"], "expected": case["expected_disposition"], "status": got["status"] or "REFUSED", "reason": got["reason"]}
    if case["expected_disposition"] == "REFUSE":
        row["outcome"] = "WRONG_SERVED" if served else "CORRECT_REFUSAL"
        return row
    if exp is None or not exp.get("boundary"):
        row["outcome"] = "ORACLE_UNAVAILABLE" if served else "NOT_SERVED"
        return row
    if not served:
        row["outcome"] = "NOT_SERVED" if got["status"] != "ROUTE_ERROR" else "ROUTE_ERROR"
        return row
    sc = got["scene"]
    secs = [o for o in sc["objects"] if o["type"] == "section"]
    if len(secs) != 1:
        row.update(outcome="WRONG_SERVED" if secs else "NOT_SERVED_GOAL_MISSING", sections=len(secs))
        return row
    checks = [c for c in V.VC.check("x", sc) if c["check"].startswith("section")]
    got_ring = [tuple(x if not isinstance(x, F) else x for x in b) for b in (V.boundary(sc) or [])]
    want = oracle_ring(exp)
    a2 = V.area_sq(sc)
    fails = [c["check"] for c in checks if not c["ok"]]
    if Counter(got_ring) != Counter(want):
        fails.append("boundary_multiset")
    elif not cyclic_equal(got_ring, want):
        fails.append("cyclic_order")
    if len(got_ring) != exp["vertex_count"]:
        fails.append("vertex_count")
    if exp.get("area_squared") is not None and a2 != F(str(exp["area_squared"])):
        fails.append("area_squared")
    row.update(outcome="SERVED_CORRECT" if not fails else "WRONG_SERVED", failed=fails, vertices=len(got_ring))
    return row


def ngrams(t: str, n: int = 5) -> set:
    t = " ".join(t.lower().split())
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def main(before: Path) -> int:
    from plane_constraint_probes import PROBES
    pre = json.loads((RUN / "evaluation_preregistration.json").read_text(encoding="utf-8"))
    dev = [ngrams(t) for _c, _e, t in PROBES.values()]
    dev += [ngrams(x) for x in __import__("re").findall(r'"([^"]{60,})"', (ROOT / "backend/tests/geometry/test_plane_constraint_sections.py").read_text(encoding="utf-8"))]
    result, dedup = {"sets": {}}, {}
    for tag, (d, name) in SETS.items():
        inp_p, exp_p = d / f"inputs/{name}.json", d / "oracle/expected.json"
        assert hashlib.sha256(inp_p.read_bytes()).hexdigest() == pre["sets"][tag]["input_sha256"], tag
        assert hashlib.sha256(exp_p.read_bytes()).hexdigest() == pre["sets"][tag]["oracle_sha256"], tag
        cases = json.loads(inp_p.read_text(encoding="utf-8"))["cases"]
        exp_all = json.loads(exp_p.read_text(encoding="utf-8"))
        exp_all = exp_all.get("cases", exp_all) if isinstance(exp_all, dict) else {e.get("case_id") or e.get("id"): e for e in exp_all}
        if isinstance(exp_all, list):
            exp_all = {e.get("case_id") or e.get("id"): e for e in exp_all}
        jac = {c["id"]: max((len(ngrams(c["problem_text"]) & g) / max(1, len(ngrams(c["problem_text"]) | g)) for g in dev), default=0) for c in cases}
        dedup[tag] = {"max_jaccard": round(max(jac.values()), 4), "cases_over_0_5": sorted(k for k, v in jac.items() if v > 0.5),
                      "top5": sorted(((k, round(v, 4)) for k, v in jac.items()), key=lambda x: -x[1])[:5]}
        texts = {c["id"]: c["problem_text"] for c in cases}
        per = {}
        for side, backend in (("before", before), ("after", ROOT / "backend")):
            got = run(backend, texts)
            rows = [score(c, exp_all.get(c["id"]), got[c["id"]]) for c in cases]
            for r, c in zip(rows, cases):
                r.update({k: c.get(k) for k in ("stratum", "family", "solid_family", "plane_relation", "plane_kind", "question_type",
                                                 "representability", "negative_class") if c.get(k) is not None})
            per[side] = rows
        def summ(rows):
            s = [r for r in rows if r["expected"] == "SERVE"]
            n = [r for r in rows if r["expected"] == "REFUSE"]
            by = lambda key, rs: {str(k): Counter(r["outcome"] for r in rs if r.get(key) == k) for k in sorted({str(r.get(key)) for r in rs})}  # noqa: E731
            return {"serve_cases": len(s), "served_correct": sum(r["outcome"] == "SERVED_CORRECT" for r in s),
                    "wrong_served": sum(r["outcome"] == "WRONG_SERVED" for r in rows),
                    "not_served": sum(r["outcome"].startswith("NOT_SERVED") for r in s), "route_errors": sum(r["outcome"] == "ROUTE_ERROR" for r in rows),
                    "oracle_unavailable": sum(r["outcome"] == "ORACLE_UNAVAILABLE" for r in s),
                    "refuse_cases": len(n), "correct_refusal": sum(r["outcome"] == "CORRECT_REFUSAL" for r in n),
                    "serve_by_relation": {k: dict(v) for k, v in by("plane_relation", s).items()},
                    "serve_by_family": {k: dict(v) for k, v in by("family", s).items()},
                    "not_served_reasons": dict(Counter(r["reason"] for r in s if r["outcome"].startswith("NOT_SERVED")).most_common()),
                    "wrong_served_ids": [r["id"] for r in rows if r["outcome"] == "WRONG_SERVED"],
                    "wrong_served_failed_checks": {r["id"]: r.get("failed") for r in rows if r["outcome"] == "WRONG_SERVED"}}
        result["sets"][tag] = {"before": summ(per["before"]), "after": summ(per["after"]),
                               "rows_after": [{k: v for k, v in r.items()} for r in per["after"]],
                               "rows_before": [{"id": r["id"], "outcome": r["outcome"], "reason": r["reason"]} for r in per["before"]]}
        print(tag, json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("serve_cases", "served_correct", "wrong_served", "not_served", "refuse_cases", "correct_refusal", "route_errors", "oracle_unavailable")}
                                for k, v in (("before", result["sets"][tag]["before"]), ("after", result["sets"][tag]["after"]))}))
    out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
           "preregistration": "evaluation_preregistration.json (registered at commit 60ce483cc, before any product change)",
           "claim_class": pre["claim_class"], "executions": "exactly one per product side; no product change after",
           "deduplication": dedup, **result}
    (RUN / "unseen_evaluation_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child()
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1])))
