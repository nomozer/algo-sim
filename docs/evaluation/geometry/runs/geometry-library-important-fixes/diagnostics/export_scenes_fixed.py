"""Export post-fix review scenes (fake provider, 0 network) to argv[1]; argv[2] = dir holding probe.py.

Checks A and B scenes are byte-identical and prints the skeleton labels + witness owners for each scene.
"""
import json
import sys

sys.path.insert(0, ".")
sys.path.insert(0, sys.argv[2])
import probe as P  # noqa: E402  (runs the probe suite on import; exits non-zero on mismatch)

T = P.T
CASES = [
    ("triangle", "tetra-S.ABC-no-projection", [], "S.ABC"),
    ("triangle", "tetra-A-to-SBC", [P.proj("K", "A", "SBC")], "S.ABC"),
    ("triangle", "tetra-B-to-SAC", [P.proj("K", "B", "SAC")], "S.ABC"),
    ("triangle", "tetra-C-to-SAB", [P.proj("K", "C", "SAB")], "S.ABC"),
    ("square", "square-intersect-AC-BD", [P.ill("O", "AC", "BD")], "S.ABCD"),
    ("square", "square-proj-D-to-SBC", [P.proj("H", "D", "SBC")], "S.ABCD"),
    ("square", "square-compose-SO-AM", [P.ill("O", "AC", "BD"), P.mid("M", "S", "C"), P.ill("K", "SO", "AM")], "S.ABCD"),
    ("square", "square-proj-A-to-SO", [P.ill("O", "AC", "BD"), P.proj("H", "A", "SO")], "S.ABCD"),
    ("square", "square-BN-AD-outside", [P.mid("N", "C", "D"), P.ill("X", "BN", "AD")], "S.ABCD"),
]
rows = []
for base, name, extra, solid in CASES:
    (P.use_square if base == "square" else P.use_triangle)()
    ra, _ = T.run("A", extra, solid=solid)
    rb, _ = T.run("B", extra, solid=solid)
    assert ra.status == rb.status == "SERVED", (name, ra.code, rb.code)
    same = json.dumps(ra.scene3d, sort_keys=True) == json.dumps(rb.scene3d, sort_keys=True)
    drawn = sorted(o["display_label"] for o in ra.scene3d["objects"] if o["type"] in ("polygon3", "segment3"))
    wit = {o["id"]: (o["perpendicular_witness"]["from"], o["perpendicular_witness"]["foot"])
           for o in ra.scene3d["objects"] if "perpendicular_witness" in o}
    rows.append({"id": name, "scene": ra.scene3d, "a_equals_b": same})
    print(name, "A==B:", same, "| drawn:", drawn, "| witness:", wit)
with open(sys.argv[1], "x", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False)
print("wrote", sys.argv[1])
