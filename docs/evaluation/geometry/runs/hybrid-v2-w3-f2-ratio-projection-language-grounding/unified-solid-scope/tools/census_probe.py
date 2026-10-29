"""Census probe: suspected scope fail-open paths beyond the review's six findings (offline, 0 provider calls)."""
import copy, json, socket, sys
from pathlib import Path
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline"))
sys.path.insert(0, ".")
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route

RUNS = Path("../docs/evaluation/geometry/runs")
SUP = json.loads((RUNS / "hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json").read_text(encoding="utf-8"))["control"]
def corpus(run):
    return {c.get("case_id", c.get("id")): c["payload"] for c in json.loads((RUNS / run / "corpus-dev.json").read_text(encoding="utf-8"))["cases"]}
SIM = corpus("simulation-coverage-visual-validation"); A3 = corpus("typedfact-next-adapter3-simulation")

def show(name, p, v4=False):
    r3 = run_typed_fact_next_route(copy.deepcopy(p)); out = {"case": name, "a3": [r3.status, r3.code]}
    if v4:
        r4 = run_typed_fact_next_v2_route({**copy.deepcopy(p), "schema_version": "typed-fact-next/2"}); out["a4"] = [r4.status, r4.code]
    print(json.dumps(out, ensure_ascii=False))

def derived_goal(p):
    return next(g for g in p["simulation_goals"] if g["kind"] == "construct_derived_solid")

for name in ("demo1-pyramid-derived-section", "demo6b-curved-cone-frustum-cut"):
    show(f"{name} control", SIM[name])
    for parent in ("foreign", "other"):
        p = copy.deepcopy(SIM[name]); g = derived_goal(p)
        if parent == "other":
            s = copy.deepcopy(p["solids"][0]); s["solid_id"] = "zz"; p["solids"].append(s); g["parent_solid_id"] = "zz"
        else:
            g["parent_solid_id"] = "foreign"
        show(f"NEW parent_solid_id={parent} ({name})", p)
p = copy.deepcopy(A3["A3-DEV-02"]); hl = next(g for g in p["simulation_goals"] if g["kind"] == "highlight_geometry")
hl["target_refs"] = ["foreign::D"]; show("NEW highlight target_refs foreign::D (A3-DEV-02)", p)
p = copy.deepcopy(SUP); q = "Cho hình chóp S.ABCD."
p["relations"] = [{"relation_id": "r", "kind": "shared_faces", "solid_a": "s1", "solid_b": "s2", "face_a": ["S", "A", "B"],
                   "face_b": ["S", "A", "B"], "quote": q}]
show("NEW shared_faces s1/s2 face SAB (not a face of T.ABCD)", p, v4=True)
p = copy.deepcopy(SUP); p["relations"] = [{"relation_id": "r", "kind": "coordinate_frame", "solid_id": "s1", "frame_id": "root",
                                         "anchor_refs": ["s2::T"], "quote": q}]
show("NEW coordinate_frame s1 anchors s2::T", p, v4=True)
p = copy.deepcopy(SUP); p["premises"][0]["args"]["vertices"] = ["s2::A", "B", "C", "D"]
show("NEW premise solid_id=s1 with qualified s2::A", p, v4=True)
p = copy.deepcopy(SUP); p["math_goals"][0]["target"] = {"solid": "s1", "solid_id": "foreign"}
show("MINOR6 target.solid_id foreign", p, v4=True)
cyl = copy.deepcopy(SIM["demo6a-curved-cylinder-sections"]); sid = cyl["solids"][0]["solid_id"]
cyl["premises"] = [{"kind": "segment_length", "solid_id": "foreign", "args": {"segment": ["A", "B"], "value": "1"}, "quote": cyl["solids"][0]["quote"]}]
show("MAJOR2 curved premise solid_id=foreign", cyl)
cyl = copy.deepcopy(SIM["demo6a-curved-cylinder-sections"])
cyl["relations"] = [{"relation_id": "r", "kind": "coordinate_frame", "solid_id": "foreign", "frame_id": "root", "quote": cyl["solids"][0]["quote"]}]
show("MAJOR2 curved relation coordinate_frame foreign", cyl)
cyl = copy.deepcopy(SIM["demo6a-curved-cylinder-sections"]); cyl["math_goals"][0]["target"] = {"solid": "foreign"}
show("MAJOR2 curved target.solid foreign", cyl)
