"""Full classification of every TypedFactNext /2 payload in the repo on the CURRENT backend (0 model calls).

Usage (from backend/): python <this> <fresh out.json>
Classes:
  SERVED_CERTIFIED       SERVED, every math goal has an exact answer and kernel_check is True
  SERVED_CONSTRUCTION    SERVED, no math goal asked (construction only)
  SERVED_UNCERTIFIED     SERVED but a math goal has no exact answer or kernel_check is not True
  REFUSED_CONTRACT       REFUSED with a contract category (insufficient / invalid / capability / verification gap)
  REFUSED_INTERNAL       REFUSED with an internal/unknown code (engine self-check, route internal, no category)
  ERROR                  the route raised
Where the source file stores an expectation next to the payload (`expect`/`expected` with `status`/`code`), the
current outcome is compared with it (historic expectations may predate later capability work: listed, not judged).
Every row keeps its Adapter /4 response for the frontend replay (`tools/classified_audit.vitest.ts.txt`).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402

CONTRACT = {"insufficient_specification", "geometry_generation_failed", "capability_gap", "verification_gap"}
INTERNAL = {"ENGINE_SELF_CHECK_FAILED", "ROUTE_INTERNAL_ERROR", "INTERNAL_ERROR"}


def walk(node, parent=None):
    if isinstance(node, dict):
        if node.get("schema_version") == "typed-fact-next/2" and isinstance(node.get("problem_text"), str):
            yield node, parent
            return
        for v in node.values():
            yield from walk(v, node)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v, parent)


#: Expectation vocabularies found next to payloads in the repo (`expected_disposition`, `expected_status`, `expect`).
_EXPECT = {"SERVE": {"SERVED"}, "SERVED": {"SERVED"}, "REFUSE": {"REFUSED"}, "REFUSED": {"REFUSED"},
           "SERVE_OR_CAPABILITY": {"SERVED", "REFUSED:capability_gap"}}


def expectation(parent):
    if not isinstance(parent, dict):
        return None
    for k in ("expected_disposition", "expected_status", "expect"):
        v = parent.get(k)
        if isinstance(v, str) and v in _EXPECT:
            return {"key": k, "value": v}
    return None


def meets(expect, status, category) -> bool:
    allowed = _EXPECT[expect["value"]]
    return status in allowed or f"{status}:{category}" in allowed


def main() -> None:
    out, seen, rows = Path(sys.argv[1]), set(), []
    for base in (ROOT / "docs/evaluation", ROOT / "backend/tests"):
        for f in sorted(base.rglob("*.json")):
            if "/perf/" in f.as_posix():
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for p, parent in walk(data):
                key = hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                row = {"key": key[:16], "source": f.relative_to(ROOT).as_posix(), "problem_text": p["problem_text"],
                       "expect": expectation(parent)}
                try:
                    r = run_typed_fact_next_v2_route(p)
                    resp = build_adapter4_response(r, p["problem_text"])
                except Exception as e:  # noqa: BLE001 — reported as a class, never hidden
                    rows.append({**row, "class": "ERROR", "error": type(e).__name__})
                    continue
                cat = resp["envelope"].get("failure_category")
                goals = [g.get("goal_id") for g in p.get("math_goals") or []]
                if r.status == "SERVED":
                    answered = all(g in (r.answer_exact or {}) for g in goals)
                    cls = ("SERVED_CONSTRUCTION" if not goals else
                           "SERVED_CERTIFIED" if answered and r.kernel_check is True else "SERVED_UNCERTIFIED")
                else:
                    cls = "REFUSED_CONTRACT" if cat in CONTRACT and r.code not in INTERNAL else "REFUSED_INTERNAL"
                row.update({"class": cls, "status": r.status, "code": r.code, "category": cat,
                            "answers": r.answer_exact or {}, "kernel_check": r.kernel_check})
                if row["expect"] is not None:
                    row["expect_match"] = meets(row["expect"], r.status, cat)
                row["response"] = resp
                rows.append(row)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    exp = [r for r in rows if r.get("expect") is not None]
    summary = {"unique_payloads": len(rows), "classes": counts, "with_expectation": len(exp),
               "expectation_mismatch": sum(not r["expect_match"] for r in exp)}
    with out.open("x", encoding="utf-8") as s:
        json.dump({"summary": summary, "rows": rows}, s, ensure_ascii=False)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
