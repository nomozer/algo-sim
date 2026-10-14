"""Small offline diagnostic adapter; consumer: goal-directed-planner-generalization-audit run.

No model call, product mutation or proposed resolver implementation. Register inputs before run; refuse overwrite.
Proposed line_ref fields intentionally test today's schema boundary, not today's valid TypedFact transport.
The separate IR witness does not claim source-grounded serving of the unsupported requested goal.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from fractions import Fraction as F
from pathlib import Path

os.environ["ALLOW_LIVE_AI"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from app.simulation.geometry_functions.registry import TuChoi
from tests.geometry import hybrid_compiler_benchmark as HB
from tests.geometry.test_two_line_plane_section import problem


def rows():
    out = []
    def add(cid, group, text, payload, status="SERVED", code=None, squared=None, **extra):
        out.append(dict(id=cid, group=group, text=text, payload=payload, expected_status=status,
                        expected_code=code, expected_squared=squared, **extra))
    base = dict(mid=("A", "B"), lines=(("B", "C"), ("A", "S")))
    t, p = problem(**base)
    add("same-structure", 1, t, p, squared="81/16")
    t, p = problem(mid=("B", "A"), lines=(("S", "A"), ("C", "B")))
    add("reverse-operands", 1, t, p, squared="81/16")
    t, p = problem(**base); old = p["facts"][4]["quotes"][0]
    p["facts"][4]["quotes"] = ["M là trung điểm của đoạn AB."]
    add("wording-control", 1, t.replace(old, p["facts"][4]["quotes"][0]), p, squared="81/16")
    t, p = problem(**base); p["facts"] = p["facts"][::-1]
    add("reordered-source-facts", 2, t, p, squared="81/16")
    t, p = problem(mid=("T", "B"), lines=(("B", "C"), ("A", "S")))
    f = HB._mid("ft", "T", "S", "B"); p["facts"].insert(4, f)
    add("nested-midpoints", 2, " ".join(f["quotes"]) + " " + t, p, squared="441/256")
    for family, squared in (("prism", "9"), ("cuboid", "144")):
        t, p = problem(family, mid=("A", "B"), lines=(("B", "C"), ("B", "B'")))
        add("family-" + family, 3, t, p, squared=squared)
    # Proposed reference transport: a REAL mathematical request, intentionally not today's schema.
    for family, planes, squared in (("pyramid", ("SAC", "SBD"), "10/11"),
                                    ("cuboid", (["A", "B", "B'"], ["B", "C", "C'"]), "5"),
                                    ("prism", (["A", "B", "B'"], ["B", "C", "C'"]), "3")):
        t, p = problem(family, mid=("A", "B"), lines=(("B", "C"), ("A", "S"))) if family == "pyramid" else problem(family)
        facts = [f for f in p["facts"] if f["id"] not in ("fm", "sec", "q")]
        mid = HB._mid("fm", "M", "A", "B" if family == "pyramid" else "C")
        a, b = map(list, planes); gq = f"Tìm giao tuyến của ({''.join(a)}) và ({''.join(b)})."
        q = f"Tính khoảng cách từ M đến giao tuyến của ({''.join(a)}) và ({''.join(b)})."
        text = " ".join(dict.fromkeys(x for f in facts + [mid] for x in f["quotes"]))
        payload = {"facts": facts + [mid, HB._f("g", "intersection_line", gq, points_a=a, points_b=b),
                   HB._ask("q", q, "distance", points_a=["M"], line_ref="g")]}
        add("derived-line-" + family, 2 if family == "pyramid" else 3,
            text + " " + gq + " " + q, payload, "REFUSED", "SCHEMA_INVALID", squared,
            transport="PROPOSED_FIELD_SCHEMA_DIAGNOSTIC", mathematical_goal="SERVED", witness=True)
    t, p = problem(lines=(("A", "B"), ("C", "D")))
    add("dependent-directions", 4, t, p, "REFUSED", "PLANE_NOT_UNIQUE")
    t, p = problem(**base); p["facts"][4]["quotes"] = ["Gọi M là trung điểm SD."]
    add("missing-source-quote", 4, t, p, "REFUSED", "QUOTE_NOT_IN_SOURCE")
    t, p = problem(**base); p["facts"][4]["role"] = "condition"
    add("conditional-anchor", 4, t, p, "REFUSED", "CONDITIONAL_FACT")
    t, p = problem(**base); q = "SA = 4."; p["facts"].append(HB._f("contradiction", "length", q,
                                                   points=["S", "A"], measure="segment", value="4"))
    add("contradictory-height", 4, t + " " + q, p, "REFUSED", "INCONSISTENT_FACTS")
    return out


def witness(row):
    from app.simulation.geometry import metric, measure
    from app.simulation.semantic_program import ir_builders as P
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    fs = copy.deepcopy(row["payload"]["facts"][:-1]); quote = "Tính độ dài AM."
    fs.append(HB._ask("control", quote, "length", points=["A", "M"]))
    text = " ".join(dict.fromkeys(q for f in fs for q in f["quotes"]))
    r = run_fact_route(text, {"facts": fs}); assert r.status == "SERVED", r.code
    spec = r.spec.model_dump(mode="json")
    spec["memory_declarations"] += [P.memory_declaration("probe_foot", "point3"),
                                     P.memory_declaration("probe_distance", P.KIEU_DAI_LUONG)]
    spec["statements"] += [{"kind": "construct_point", "target_var": "probe_foot",
                           "expr": {"kind": "project_onto", "point": "M", "target": "gt_g"}},
                           P.measure_quantity("probe_distance", "distance", "M", "probe_foot")]
    with metric.using(r.chart_metric):
        result = SemanticProgramInterpreter().execute(SemanticProgramSpec.model_validate(spec))
        sq = measure.distance_sq(result.final_memory["M"], result.final_memory["probe_foot"])
    assert sq == F(row["expected_squared"]), (row["id"], sq)
    return {"classification": "IR_ONLY_CAPABILITY_WITNESS_NOT_FULL_SOURCE_GROUNDED_SERVE",
            "existing_producer": "intersection_line→intersect_plane_plane(gt_g)",
            "existing_consumers": ["project_onto", "measure_quantity(distance)"], "distance_squared": str(sq),
            "oracle": "independent analytic result for source dimensions; Gram context retained",
            "source_route_control": "SERVED on a separate supported length question"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--register", action="store_true"); args = ap.parse_args()
    run = Path(__file__).resolve().parents[2] / "docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit"
    path = run / ("probes.json" if args.register else "baseline.json")
    if path.exists(): raise SystemExit("refusing overwrite of research evidence")
    if args.register:
        path.write_text(json.dumps({"class": "DIAGNOSTIC_NOT_HELD_OUT", "live_calls": 0, "cases": rows()},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); return
    inp = run / "probes.json"; data = json.loads(inp.read_text(encoding="utf-8")); results = []
    for row in data["cases"]:
        r = run_fact_route(row["text"], row["payload"]); plan = None
        try: plan = lap_ke_hoach(row["payload"], row["text"])
        except TuChoi: pass
        squared = HB.answer_square(r.answers["q"]) if r.status == "SERVED" else None
        matches = r.status == row["expected_status"] and (not row["expected_code"] or r.code == row["expected_code"])
        correct = squared == F(row["expected_squared"]) if squared is not None else None
        stage = "typed_fact_schema" if r.code == "SCHEMA_INVALID" else ("planner" if plan is None else
                "engine_or_kernel" if r.code in ("PLANE_NOT_UNIQUE", "INCONSISTENT_FACTS") else
                "grounding" if r.status == "REFUSED" else "served")
        results.append({"id": row["id"], "group": row["group"], "status": r.status, "code": r.code,
                        "first_stop": stage, "matches_preregistered_current_expectation": matches,
                        "squared": str(squared) if squared is not None else None, "served_mathematically_correct": correct,
                        "calls": [c["fn"] for c in plan.calls] if plan else [],
                        "witness": witness(row) if row.get("witness") else None})
    out = {"input_sha256": hashlib.sha256(inp.read_bytes()).hexdigest(), "measurement_class": "OFFLINE_FIXTURE_DIAGNOSTIC",
           "held_out": False, "live_calls": 0, "cases": results}
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k:v for k,v in r.items() if k not in ("calls", "witness")} for r in results], ensure_ascii=False))


if __name__ == "__main__": main()
