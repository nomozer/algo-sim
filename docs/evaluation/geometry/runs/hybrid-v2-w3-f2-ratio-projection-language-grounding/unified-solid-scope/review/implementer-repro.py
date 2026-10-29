"""Independent re-reproduction of review2 findings F1-F3 (offline, 0 provider calls)."""
import copy, json, socket, sys
from pathlib import Path
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline"))
sys.path.insert(0, ".")
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_typed_fact_next_planner_route

SUP = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["control"]
def show(name, p):
    r3 = run_typed_fact_next_route(copy.deepcopy(p)); pl = run_typed_fact_next_planner_route(copy.deepcopy(p))
    r4 = run_typed_fact_next_v2_route({**copy.deepcopy(p), "schema_version": "typed-fact-next/2"})
    print(json.dumps({"case": name, "a3": [r3.status, r3.code], "pl": [pl.status, pl.code], "a4": [r4.status, r4.code]}))

p = json.loads(json.dumps(SUP).replace('"s1"', '"pyr-1"').replace('"s2"', '"pyr-2"'))
p["premises"][2]["args"]["segment"] = ["pyr-1::S", "pyr-1::A"]
show("F1 hyphenated ids (valid control)", p)
q = "Cho hình chóp S.ABCD."
p = copy.deepcopy(SUP); p["relations"] = [{"relation_id": "r", "kind": "perpendicular", "solid_id": "s2", "entity_a": ["S", "A"],
                                          "entity_b": list("ABCD"), "quote": "SA vuông góc với (ABCD)."}]
show("F2 perpendicular solid_id s2 with s1-only S", p)
p = copy.deepcopy(SUP); p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "s2",
                                                     "target_refs": ["s1::S"], "quote": q})
show("F3 highlight target_solid_id s2 refs s1::S", p)
