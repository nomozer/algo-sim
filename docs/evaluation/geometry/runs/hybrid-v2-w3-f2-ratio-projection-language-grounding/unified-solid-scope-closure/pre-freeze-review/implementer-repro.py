"""Implementer re-reproduction of pre-freeze review findings N1-N3 (offline, 0 provider calls)."""
import copy, json, socket, sys
from pathlib import Path
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline"))
sys.path.insert(0, ".")
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route
from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2, TypedFactNextValidationError

RUNS = Path(sys.argv[1])
SUP = json.loads((RUNS / "hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json").read_text(encoding="utf-8"))["control"]
A3 = {c["case_id"]: c["payload"] for c in json.loads((RUNS / "typedfact-next-adapter3-simulation/corpus-dev.json").read_text(encoding="utf-8"))["cases"]}
def a4(p):
    try: q = convert_v1_to_v2(copy.deepcopy(p), "adapter3") if p.get("derived_sections") else {**copy.deepcopy(p), "schema_version": "typed-fact-next/2"}
    except TypedFactNextValidationError as e: return f"REFUSED:{e.code}"
    r = run_typed_fact_next_v2_route(q); return f"{r.status}:{r.code}"
def show(name, p):
    r3 = run_typed_fact_next_route(copy.deepcopy(p)); pl = run_typed_fact_next_planner_route(copy.deepcopy(p))
    print(json.dumps({"case": name, "a3": f"{r3.status}:{r3.code}", "pl": f"{pl.status}:{pl.code}", "a4": a4(p),
                      "a3_answer": getattr(r3, "answer_exact", None)}, ensure_ascii=False))

q = "Tính khoảng cách giữa T và A."
p = copy.deepcopy(SUP); p["math_goals"].append({"goal_id": "g2", "kind": "measurement", "goal_type": "distance",
                                                "target": {"solid_id": "s1", "segment": "TA"}, "quote": q}); p["problem_text"] += " " + q
show("N1 string-chain segment TA under target.solid_id s1", p)
p = copy.deepcopy(A3["A3-DEV-02"]); qm = "M là trung điểm của SB."; p["problem_text"] += " " + qm
p["premises"].append({"kind": "point_is_midpoint", "solid_id": "pyr1", "args": {"point": "M", "segment": ["S", "B"]}, "quote": qm})
qg = "Tính độ dài MB."; p["problem_text"] += " " + qg
p["math_goals"].append({"goal_id": "g3", "kind": "measurement", "goal_type": "distance", "target": {"solid_id": "pyr2", "segment": ["M", "B"]}, "quote": qg})
show("N2 legacy fallback: constructed M of pyr1 under pyr2", p)
p = copy.deepcopy(SUP); p["math_goals"][0]["parent_solid_id"] = "s2"
show("N3 measurement with parent_solid_id of another solid", p)
