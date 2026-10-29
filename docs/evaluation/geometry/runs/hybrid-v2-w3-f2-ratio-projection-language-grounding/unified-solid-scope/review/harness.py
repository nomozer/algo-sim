"""Shared harness: load committed fixtures, run payloads through the three TypedFactNext routes."""
import json, copy, os, sys
from pathlib import Path
WT = Path(r"D:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f2-ratio-projection-language-grounding")
RUNS = WT / "docs/evaluation/geometry/runs"
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2, TypedFactNextValidationError

def walk(o):
    if isinstance(o, dict):
        if o.get("schema_version") == "typed-fact-next/1" and "solids" in o:
            yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)

def fixtures():
    out = []
    for rel in ["hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/development.json",
                "hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json",
                "typedfact-next-adapter3-simulation/corpus-dev.json",
                "simulation-coverage-visual-validation/corpus-dev.json"]:
        data = json.loads((RUNS / rel).read_text(encoding="utf-8"))
        for i, p in enumerate(walk(data)):
            out.append((f"{rel.split('/')[0][:20]}#{i}", p))
    return out

def short(r):
    st = getattr(r, "status", None)
    code = getattr(r, "code", None)
    return f"{st}:{code}" if st != "SERVED" else "SERVED"

def run3(p):
    res = {}
    for name, fn in (("A3", run_typed_fact_next_route), ("PL", run_typed_fact_next_planner_route)):
        try:
            res[name] = short(fn(copy.deepcopy(p)))
        except Exception as e:  # escaped exception = boundary defect
            res[name] = f"EXC:{type(e).__name__}:{e}"[:160]
    try:
        v2 = convert_v1_to_v2(copy.deepcopy(p), "adapter3")
    except TypedFactNextValidationError as e:
        res["A4"] = f"REFUSED:{e.code}(conv)"
    except Exception as e:
        res["A4"] = f"EXC(conv):{type(e).__name__}:{e}"[:160]
    else:
        try:
            res["A4"] = short(run_typed_fact_next_v2_route(v2))
        except Exception as e:
            res["A4"] = f"EXC:{type(e).__name__}:{e}"[:160]
    return res
