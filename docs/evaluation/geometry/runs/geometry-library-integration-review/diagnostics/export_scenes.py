"""Export reviewer scenes (fake provider, 0 network) to argv[1]; also checks A and B scenes are byte-identical."""
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, sys.argv[2])
import probe as P  # noqa: E402  (runs the probe suite on import; exits non-zero on mismatch)
T = P.T

CASES = [
    ("square", "base-intersect-AC-BD", [P.ill("O", "AC", "BD")], "S.ABCD"),
    ("square", "base-proj-D-to-SBC", [P.proj("H", "D", "SBC")], "S.ABCD"),
    ("square", "compose-M-P-H", [P.mid("M", "S", "A"), P.ilp("P", "SD", "MBC"), P.proj("H", "P", "BD")], "S.ABCD"),
    ("square", "compose-SO-AM", [P.ill("O", "AC", "BD"), P.mid("M", "S", "C"), P.ill("K", "SO", "AM")], "S.ABCD"),
    ("square", "proj-A-to-SO", [P.ill("O", "AC", "BD"), P.proj("H", "A", "SO")], "S.ABCD"),
    ("square", "BN-AD-outside-segment", [P.mid("N", "C", "D"), P.ill("X", "BN", "AD")], "S.ABCD"),
    ("triangle", "gram-proj-A-to-SBC", [P.proj("K", "A", "SBC")], "S.ABC"),
]
rows = []
for base, name, extra, solid in CASES:
    (P.use_square if base == "square" else P.use_triangle)()
    ra, _ = T.run("A", extra, solid=solid)
    rb, _ = T.run("B", extra, solid=solid)
    assert ra.status == rb.status == "SERVED", (name, ra.code, rb.code)
    same = json.dumps(ra.scene3d, sort_keys=True) == json.dumps(rb.scene3d, sort_keys=True)
    rows.append({"id": name, "scene": ra.scene3d, "a_equals_b": same})
    print(name, "A==B scene:", same, "objects:", len(ra.scene3d["objects"]))
out = sys.argv[1]
with open(out, "x", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False)
print("wrote", out)
