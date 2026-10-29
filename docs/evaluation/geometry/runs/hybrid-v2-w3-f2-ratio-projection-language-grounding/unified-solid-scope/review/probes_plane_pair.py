"""D2 key coverage: measurement-goal operand ownership for {plane1, plane2} targets (Adapter /4 only reads them)."""
import sys, json, copy
sys.path.insert(0, sys.argv[1])
from harness import RUNS, run3

C1 = json.loads((RUNS / "hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json").read_text(encoding="utf-8"))["control"]
Q = "Tính góc giữa hai mặt phẳng (SBC) và (ABCD)."
for name, sid, key, ops in [
    ("angle_planes_scope_s1_control", "s1", "angle", (["S", "B", "C"], ["A", "B", "C", "D"])),
    ("angle_planes_scope_s2_S_only_s1", "s2", "angle", (["S", "B", "C"], ["A", "B", "C", "D"])),
    ("angle_planes_scope_s2_qualified_s1", "s2", "angle", (["s1::S", "B", "C"], ["A", "B", "C", "D"])),
    ("angle_line_plane_scope_s2_S_only_s1", "s2", "angle", None),
    ("angle_planes_noscope_control", None, "angle", (["S", "B", "C"], ["A", "B", "C", "D"])),
]:
    p = copy.deepcopy(C1)
    p["problem_text"] += " " + Q
    target = {"plane1": ops[0], "plane2": ops[1]} if ops else {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}
    g = {"goal_id": "ang", "kind": "measurement", "goal_type": key, "target": target, "quote": Q}
    if sid:
        g["solid_id"] = sid
    p["math_goals"] = [g]
    print(json.dumps({"probe": "PP." + name, **run3(p)}, ensure_ascii=False), flush=True)
