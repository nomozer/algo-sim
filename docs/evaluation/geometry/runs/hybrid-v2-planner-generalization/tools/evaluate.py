"""Score the preregistered authored corpus on the current checkout; never calls a provider."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions import planner
from app.simulation.geometry_functions.registry import TuChoi


def main(name: str) -> None:
    out = RUN / "results" / f"{name}.json"
    if out.exists():
        raise SystemExit("Refusing overwrite of measurement")
    data = RUN / "inputs/development.json"
    rows = json.loads(data.read_text(encoding="utf-8"))["cases"]
    results = []
    counts = Counter()
    for row in rows:
        start = perf_counter()
        try:
            plan = planner.lap_ke_hoach(deepcopy(row["payload"]), row["text"])
            plan_code = None
        except TuChoi as exc:
            plan, plan_code = None, exc.code
        elapsed = round((perf_counter() - start) * 1000, 3)
        r = run_fact_route(row["text"], deepcopy(row["payload"]))
        square = None
        if r.status == "SERVED":
            v = r.exec_result.final_memory["kq_q"]
            square = str(Fraction(v.he) ** 2 * v.can if hasattr(v, "can") else Fraction(v) ** 2)
        positive = row["expected_status"] == "SERVED"
        agreement = square == row["expected_area_squared"] if positive and r.status == "SERVED" else None
        outcome = ("correctly_served" if agreement else "wrongly_served") if r.status == "SERVED" else (
            "false_refusal" if positive else "correctly_refused")
        counts[outcome] += 1
        code_match = r.code in row["expected_codes"] if not positive else None
        if code_match is False:
            counts["negative_reason_mismatches"] += 1
        metrics = None
        if plan:
            depth = {}
            pending = {c["id"]: set(c.get("depends_on", [])) for c in plan.calls}
            while pending:
                ready = [cid for cid, deps in pending.items() if deps <= depth.keys()]
                assert ready, "Unclosed dependency graph in served plan"
                for cid in ready:
                    deps = pending.pop(cid)
                    depth[cid] = 1 + max((depth[d] for d in deps), default=0)
            functions = Counter(c["fn"] for c in plan.calls)
            metrics = {"function_calls": len(plan.calls), "dependency_depth": max(depth.values()),
                       "functions": dict(functions), "derived_planes": len(plan.derived_planes),
                       "reused_intermediate_constructions": sum(len(d["constructs"]) * (len(d["targets"]) - 1)
                                                                   for d in plan.derived_planes.values()),
                       "anchor_labels": [d["anchors"] for d in plan.derived_planes.values()],
                       "effect_search": "NOT_APPLICABLE: existing structural plane decomposition; no effect search invoked"}
        results.append({"id": row["id"], "expected_status": row["expected_status"], "status": r.status,
                        "code": r.code, "planner_code": plan_code, "outcome": outcome,
                        "area_squared": square, "oracle_area_squared": row["expected_area_squared"],
                        "exact_agreement": agreement, "negative_reason_match": code_match,
                        "planner_ms": elapsed, "plan_metrics": metrics})
    summary = {k: counts[k] for k in ("correctly_served", "correctly_refused", "wrongly_served", "false_refusal",
                                    "negative_reason_mismatches")}
    summary.update(exact_mathematical_agreement=sum(r["exact_agreement"] is True for r in results),
                   novel_compositions_served=sum(r["outcome"] == "correctly_served" for r in results))
    artifact = {"classification": "AUTHORED_DEVELOPMENT_NOT_HOLDOUT", "name": name,
                "head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
                "planner_version": planner.PLANNER_VERSION,
                "planner_sha256_lf": hashlib.sha256((ROOT / "backend/app/simulation/geometry_functions/planner.py")
                                                    .read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                "input_sha256_lf": hashlib.sha256(data.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                "oracle_sha256_lf": hashlib.sha256((RUN / "inputs/oracle.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                "summary": summary, "cases": results, "live_provider_calls": 0}
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main(sys.argv[1])
