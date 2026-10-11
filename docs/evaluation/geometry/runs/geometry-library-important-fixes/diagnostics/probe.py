"""Independent reviewer probes (0 network). Oracles hand-derived in Euclidean coords, no kernel call.

Run from the worktree backend/:  python <this> ; prints one line per probe, exit 1 if any mismatch.
"""
import json, sys
from fractions import Fraction as F
sys.path.insert(0, ".")
import tests.geometry.test_geometry_library_expansion as T

SQ = (T.CALLS, T.FACTS, T.BASE)
TRI_BASE = ["Cho hình chóp S.ABC.", "Đáy ABC là tam giác đều cạnh 2.", "SA vuông góc với (ABC).", "SA = 3."]


def use_triangle():
    T.CALLS = [("pyramid", {"apex": "S", "base": list("ABC")}, TRI_BASE[0]),
               ("regular_polygon", {"vertices": list("ABC"), "side": "2"}, TRI_BASE[1]),
               ("perpendicular_line_plane", {"line": list("SA"), "plane": list("ABC")}, TRI_BASE[2]),
               ("segment_length", {"segment": list("SA"), "value": "3"}, TRI_BASE[3])]
    T.FACTS = [{"kind": "solid", "solid": "S.ABC", "solid_type": "pyramid"},
               {"kind": "polygon_shape", "points": list("ABC"), "shape": "equilateral_triangle", "value": "2"},
               {"kind": "perpendicular", "points_a": list("SA"), "points_b": list("ABC")},
               {"kind": "length", "points": list("SA"), "measure": "segment", "value": "3"}]
    T.BASE = TRI_BASE


def use_square():
    T.CALLS, T.FACTS, T.BASE = SQ


def mid(p, a, b):
    return ("midpoint", {"point": p, "segment": [a, b]},
            {"kind": "point_def", "point": p, "point_kind": "midpoint", "points": [a, b]}, f"Gọi {p} là trung điểm {a}{b}.")


def ill(p, l1, l2):
    return ("intersect_line_line", {"point": p, "line1": list(l1), "line2": list(l2)},
            {"kind": "point_def", "point": p, "point_kind": "intersect_line_line", "points_a": list(l1), "points_b": list(l2)},
            f"Gọi {p} là giao điểm của {l1} và {l2}.")


def ilp(p, l, pl):
    return ("intersect_line_plane", {"point": p, "line": list(l), "plane": list(pl)},
            {"kind": "point_def", "point": p, "point_kind": "intersect_line_plane", "points_a": list(l), "points_b": list(pl)},
            f"Gọi {p} là giao điểm của {l} và ({pl}).")


def proj(img, p, tgt):
    fn = "orthogonal_projection_line" if len(tgt) == 2 else "orthogonal_projection"
    key = "line" if len(tgt) == 2 else "plane"
    words = tgt if len(tgt) == 2 else f"({tgt})"
    return (fn, {"point": p, key: list(tgt), "image": img},
            {"kind": "projection", "point": p, "points": list(tgt), "at": img},
            f"Gọi {img} là hình chiếu vuông góc của {p} lên {words}.")


bad = 0


def check(name, extra, label=None, xyz=None, code=None, solid="S.ABCD", reverse=False):
    global bad
    for arm in "AB":
        r, _ = T.run(arm, extra, solid=solid, reverse=reverse)
        if code:
            ok = r.status == "REFUSED" and r.code == code
            got = f"{r.status}/{r.code}"
        else:
            ok = r.status == "SERVED"
            got = f"{r.status}/{r.code}"
            if ok:
                o = T.scene_point(r, label)
                got = o["xyz"]
                ok = tuple(map(F, o["xyz"])) == tuple(map(F, xyz)) and o["origin"] == "derived"
        bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {arm} {name}: expect {code or xyz} got {got}" + ("" if ok else f" reason={r.reason}"))


use_square()
# Two-derived-operand composition: K = SO ∩ AM (centroid of SAC) = (1/3,1/3,1/3), also reversed order.
comp = [ill("O", "AC", "BD"), mid("M", "S", "C"), ill("K", "SO", "AM")]
check("SO∩AM via derived O,M", comp, "K", ("1/3", "1/3", "1/3"))
check("SO∩AM reversed order", comp, "K", ("1/3", "1/3", "1/3"), reverse=True)
# Projection chained onto an intersection-derived line: foot of A on SO.
# Euclid: S=(0,0,3), O=(1,1,0); t=(A-S)·(O-S)/|O-S|² = 9/11 ⇒ (9/11,9/11,6/11) ⇒ affine (9/22,9/22,2/11)
check("proj A→SO (derived O)", [ill("O", "AC", "BD"), proj("H", "A", "SO")], "H", ("9/22", "9/22", "2/11"))
# Line intersection outside the segments (line semantics): BN ∩ AD, N mid CD ⇒ (0,2,0)
check("BN∩AD outside segment", [mid("N", "C", "D"), ill("X", "BN", "AD")], "X", ("0", "2", "0"))
# Fail-closed
check("skew SB,CD", [ill("X", "SB", "CD")], code="SKEW_NO_INTERSECTION")
check("parallel AB,CD", [ill("X", "AB", "CD")], code="PARALLEL_NO_INTERSECTION")
check("coincident AC,CA", [ill("X", "AC", "CA")], code="CONTAINED_INFINITE_INTERSECTION")
check("line in plane AC,(ABD)", [ilp("X", "AC", "ABD")], code="CONTAINED_INFINITE_INTERSECTION")
check("line ∥ plane AB,(SCD)", [ilp("X", "AB", "SCD")], code="PARALLEL_NO_INTERSECTION")
check("non-coplanar plane (SABC)", [ilp("X", "SC", "SABC")], code="NON_COPLANAR_POINTS")
check("collinear plane (AOC)", [ill("O", "AC", "BD"), ilp("X", "SB", "AOC")], code="COLLINEAR_POINTS")
check("cycle P from line through P", [ill("P", "AP", "BD")], code="UNDERDETERMINED_POINT")
# Contradiction: O defined as AC∩BD and as midpoint of AB
check("contradictory O", [ill("O", "AC", "BD"), mid("O", "A", "B")], code="INCONSISTENT_FACTS")

use_triangle()
# Non-diagonal Gram, PLANE projection (not covered by branch tests):
# K = proj A→(SBC); Euclid AK=3/2 on SM, SK/SM=3/4 ⇒ affine (3/8,3/8,1/4)
check("Gram plane proj A→(SBC)", [proj("K", "A", "SBC")], "K", ("3/8", "3/8", "1/4"), solid="S.ABC")
# B→(SAC) = midpoint of AC ⇒ affine (0,1/2,0)
check("Gram plane proj B→(SAC)", [proj("H", "B", "SAC")], "H", ("0", "1/2", "0"), solid="S.ABC")
# Three perpendiculars: S→BC lands on midpoint of BC ⇒ (1/2,1/2,0)
check("Gram line proj S→BC", [proj("H", "S", "BC")], "H", ("1/2", "1/2", "0"), solid="S.ABC")
print("MISMATCHES:", bad)
if bad:
    sys.exit(1)
