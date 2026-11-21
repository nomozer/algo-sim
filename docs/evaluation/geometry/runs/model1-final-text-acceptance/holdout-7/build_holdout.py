# -*- coding: utf-8 -*-
"""Holdout-7 (AXO HYBRID /19): hand-written prospective INTERNAL text set for candidate 158.

Provenance: written by the /19 agent from the sampling plan below, before any case was run on candidate 158; not
generated from the /14–/16 `build_holdout.py` templates; not learner or teacher data ⇒ EXTERNAL_INDEPENDENCE =
NOT_MEASURED. Gold is NOT taken from Axo: every metric is computed twice — a closed form written with the case and an
independent coordinate model built here — and the build fails unless both agree.

Pre-run exposure check (check_exposure.py) found T06 string-exposed and T03/T06/T12/T14/T16 template-exposed;
those five were reworded (same geometry, same stratum) BEFORE any case ran on candidate 158.

Sampling plan (fixed before writing): positives in four strata — textbook canonical (17), exam wording (16), teacher
wording (15), learner colloquial (10); negatives (22) — missing data (6), contradiction (5), negation/condition/
unsupported request (6), other subject (5). In-scope rule (from CAPABILITY_MATRIX.json SUPPORTED families): convex
polyhedra (pyramid, right prism, cuboid, cube, tetrahedron) with volume / length / distance / line–plane angle / polygon
area / midpoint / draw-only requests; curved solids (FOUNDATION_ONLY) are not used.

usage: python build_holdout.py <out_dir>   (refuses to overwrite)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

R3 = math.sqrt(3)
R2 = math.sqrt(2)

# ── independent coordinate model ─────────────────────────────────────────────────────────────────────────────────────


def sub(p, q):
    return tuple(a - b for a, b in zip(p, q))


def dot(p, q):
    return sum(a * b for a, b in zip(p, q))


def cross(p, q):
    return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])


def norm(p):
    return math.sqrt(dot(p, p))


def area(P, pts):
    o = P[pts[0]]
    s = (0.0, 0.0, 0.0)
    for i in range(1, len(pts) - 1):
        c = cross(sub(P[pts[i]], o), sub(P[pts[i + 1]], o))
        s = tuple(a + b for a, b in zip(s, c))
    return norm(s) / 2


def plane_n(P, pl):
    return cross(sub(P[pl[1]], P[pl[0]]), sub(P[pl[2]], P[pl[0]]))


def dist_pp(P, p, pl):
    n = plane_n(P, pl)
    return abs(dot(n, sub(P[p], P[pl[0]]))) / norm(n)


def measure(P, goal):
    kind = goal[0]
    if kind == "vol_pyr":
        apex, base = goal[1], goal[2]
        return area(P, base) * dist_pp(P, apex, base) / 3
    if kind == "vol_prism":
        base, top_pt = goal[1], goal[2]
        return area(P, base) * dist_pp(P, top_pt, base)
    if kind == "len":
        return norm(sub(P[goal[1]], P[goal[2]]))
    if kind == "dist":
        return dist_pp(P, goal[1], goal[2])
    if kind == "angle":
        d = sub(P[goal[2]], P[goal[1]])
        n = plane_n(P, goal[3])
        return math.degrees(math.asin(abs(dot(d, n)) / (norm(d) * norm(n))))
    if kind == "area":
        return area(P, goal[1])
    raise KeyError(kind)


# ── families: coordinates + gold relations (scene_oracle vocabulary) ─────────────────────────────────────────────────


def pyr_rect(S, A, B, C, D, ab, ad, h):
    """S.ABCD, ABCD rectangle (AB ⊥ AD), SA ⊥ (ABCD) with SA = h (lengths in units; symbolic a ⇒ a = 1)."""
    P = {A: (0, 0, 0), B: (ab, 0, 0), C: (ab, ad, 0), D: (0, ad, 0), S: (0, 0, h)}
    rel = [["perp_lp", S + A, A + B + C], ["perp_ll", A + B, A + D], ["par_ll", A + B, D + C], ["par_ll", A + D, B + C],
           ["len2", A + B, r2(ab)], ["len2", A + D, r2(ad)], ["len2", S + A, r2(h)]]
    return P, rel, [S, A, B, C, D], {"vertices": 5, "faces": 5}, "pyramid_quad"


def pyr_tri_right(S, A, B, C, at, p, q, h, foot):
    """S.ABC, base right at vertex `at` (legs p, q in the order of the other two labels), S above `foot` at height h."""
    others = [x for x in (A, B, C) if x != at]
    P = {at: (0, 0, 0), others[0]: (p, 0, 0), others[1]: (0, q, 0)}
    P[S] = P[foot][:2] + (h,)
    rel = [["perp_ll", at + others[0], at + others[1]], ["perp_lp", S + foot, A + B + C],
           ["len2", at + others[0], r2(p)], ["len2", at + others[1], r2(q)], ["len2", S + foot, r2(h)]]
    return P, rel, [S, A, B, C], {"vertices": 4, "faces": 4}, "pyramid_tri"


def pyr_tri_equil(S, A, B, C, s, h):
    """S.ABC, ABC equilateral side s, SA ⊥ (ABC), SA = h."""
    P = {A: (0, 0, 0), B: (s, 0, 0), C: (s / 2, s * R3 / 2, 0), S: (0, 0, h)}
    rel = [["perp_lp", S + A, A + B + C], ["len2", A + B, r2(s)], ["len2", A + C, r2(s)], ["len2", B + C, r2(s)],
           ["len2", S + A, r2(h)]]
    return P, rel, [S, A, B, C], {"vertices": 4, "faces": 4}, "pyramid_tri"


def pyr_quad_regular(S, A, B, C, D, s, h):
    P = {A: (0, 0, 0), B: (s, 0, 0), C: (s, s, 0), D: (0, s, 0), S: (s / 2, s / 2, h)}
    lat2 = r2(h) + r2(s) / 2
    rel = [["perp_ll", A + B, A + D], ["par_ll", A + B, D + C], ["len2", A + B, r2(s)], ["len2", A + D, r2(s)],
           ["eq", S + A, S + B], ["eq", S + A, S + C], ["eq", S + A, S + D], ["len2", S + A, lat2]]
    return P, rel, [S, A, B, C, D], {"vertices": 5, "faces": 5}, "pyramid_quad"


def pyr_tri_regular(S, A, B, C, s, h):
    P = {A: (0, 0, 0), B: (s, 0, 0), C: (s / 2, s * R3 / 2, 0), S: (s / 2, s * R3 / 6, h)}
    lat2 = r2(h) + r2(s) / 3
    rel = [["len2", A + B, r2(s)], ["len2", A + C, r2(s)], ["len2", B + C, r2(s)], ["eq", S + A, S + B],
           ["eq", S + A, S + C], ["len2", S + A, lat2]]
    return P, rel, [S, A, B, C], {"vertices": 4, "faces": 4}, "pyramid_tri"


def prism_tri_right(A, B, C, A1, B1, C1, at, p, q, h):
    """Right prism ABC.A'B'C' (A1 = A' …), base right at `at` with legs p, q (order of the other two labels)."""
    base = {A: A1, B: B1, C: C1}
    others = [x for x in (A, B, C) if x != at]
    P = {at: (0, 0, 0), others[0]: (p, 0, 0), others[1]: (0, q, 0)}
    for x, y in base.items():
        P[y] = P[x][:2] + (h,)
    rel = [["perp_ll", at + others[0], at + others[1]], ["perp_lp", A + A1, A + B + C], ["par_ll", A + A1, B + B1],
           ["par_ll", A + A1, C + C1], ["len2", at + others[0], r2(p)], ["len2", at + others[1], r2(q)], ["len2", A + A1, r2(h)]]
    return P, rel, [A, B, C, A1, B1, C1], {"vertices": 6, "faces": 5}, "prism_tri"


def prism_tri_equil(A, B, C, A1, B1, C1, s, h):
    P = {A: (0, 0, 0), B: (s, 0, 0), C: (s / 2, s * R3 / 2, 0)}
    for x, y in ((A, A1), (B, B1), (C, C1)):
        P[y] = P[x][:2] + (h,)
    rel = [["perp_lp", A + A1, A + B + C], ["par_ll", A + A1, B + B1], ["par_ll", A + A1, C + C1], ["len2", A + B, r2(s)],
           ["len2", A + C, r2(s)], ["len2", B + C, r2(s)], ["len2", A + A1, r2(h)]]
    return P, rel, [A, B, C, A1, B1, C1], {"vertices": 6, "faces": 5}, "prism_tri"


def box(A, B, C, D, A1, B1, C1, D1, ab, ad, h, family="box"):
    P = {A: (0, 0, 0), B: (ab, 0, 0), C: (ab, ad, 0), D: (0, ad, 0)}
    for x, y in ((A, A1), (B, B1), (C, C1), (D, D1)):
        P[y] = P[x][:2] + (h,)
    rel = [["perp_ll", A + B, A + D], ["perp_lp", A + A1, A + B + C], ["par_ll", A + A1, B + B1], ["par_ll", A + B, D + C],
           ["len2", A + B, r2(ab)], ["len2", A + D, r2(ad)], ["len2", A + A1, r2(h)]]
    return P, rel, [A, B, C, D, A1, B1, C1, D1], {"vertices": 8, "faces": 6}, family


def tetra_corner(O, A, B, C, a, b, c):
    P = {O: (0, 0, 0), A: (a, 0, 0), B: (0, b, 0), C: (0, 0, c)}
    rel = [["perp_ll", O + A, O + B], ["perp_ll", O + B, O + C], ["perp_ll", O + C, O + A], ["len2", O + A, r2(a)],
           ["len2", O + B, r2(b)], ["len2", O + C, r2(c)]]
    return P, rel, [O, A, B, C], {"vertices": 4, "faces": 4}, "tetrahedron"


def r2(x):
    """Squared length as an exact-looking rational for the oracle (inputs here are integers or k·√m)."""
    v = x * x
    return int(round(v)) if abs(v - round(v)) < 1e-9 else round(v, 12)


CUBE = lambda *v, s: box(*v, s, s, s, family="cube")  # noqa: E731
L = ("A", "B", "C", "D", "A'", "B'", "C'", "D'")


def pos(cid, stratum, text, fam, goal=None, gold=None, intent=None, aux=None, extra_rel=None):
    P, rel, verts, counts, family = fam
    rel = rel + (extra_rel or [])
    if aux:
        for name, (x, y) in aux.items():  # midpoint auxiliaries
            P[name] = tuple((a + b) / 2 for a, b in zip(P[x], P[y]))
            rel.append(["mid", name, x + y])
    if goal is not None:
        got = measure(P, goal)
        assert abs(got - gold) < 1e-9 * max(1, abs(gold)), (cid, got, gold)
    return {
        "case_id": cid, "phrase_family": stratum, "input_type": "text", "original_input": text,
        "simulation_intent": intent or ("QUERY_WITH_SCENE" if goal is not None else "SIMULATE_ONLY"),
        "geometric_family": family,
        "gold_entities": {"solid_vertices": verts, "auxiliary_points": list((aux or {}).keys())},
        "gold_relations": rel, "metric_oracle": None if goal is None else [gold],
        "preregistered_slm_target": False, "expected_counts": counts, "expected_behavior": "SERVE",
        "geometry_determinacy": "UNIQUE_GEOMETRY", "validation_method": "EXACT_SCENE_ORACLE+BROWSER",
    }


def neg(cid, stratum, text, determinacy):
    return {
        "case_id": cid, "phrase_family": stratum, "input_type": "text", "original_input": text,
        "simulation_intent": "NEGATIVE", "geometric_family": "negative_control",
        "gold_entities": {"solid_vertices": [], "auxiliary_points": []}, "gold_relations": [], "metric_oracle": None,
        "preregistered_slm_target": False, "expected_counts": {}, "expected_behavior": "SAFE_REFUSE",
        "geometry_determinacy": determinacy, "validation_method": "REFUSAL+BROWSER",
    }


T, E, G, C = "textbook_canonical", "exam_wording", "teacher_wording", "learner_colloquial"
V = []
# ── textbook canonical ───────────────────────────────────────────────────────────────────────────────────────────────
V.append(pos("T01", T, "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 3, AD = 4, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 6. Tính thể tích khối chóp S.ABCD.",
             pyr_rect("S", "A", "B", "C", "D", 3, 4, 6), ("vol_pyr", "S", ["A", "B", "C", "D"]), 24.0))
V.append(pos("T02", T, "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, SA vuông góc với mặt phẳng (ABC) và SA = 5. Tính thể tích khối chóp S.ABC.",
             pyr_tri_right("S", "A", "B", "C", "B", 3, 4, 5, "A"), ("vol_pyr", "S", ["A", "B", "C"]), 10.0))
V.append(pos("T03", T, "Hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác ABC vuông tại A, cạnh AB = 6, cạnh AC = 8, cạnh bên AA' = 10. Tính thể tích của khối lăng trụ này.",
             prism_tri_right("A", "B", "C", "A'", "B'", "C'", "A", 6, 8, 10), ("vol_prism", ["A", "B", "C"], "A'"), 240.0))
V.append(pos("T04", T, "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 5. Tính thể tích khối lập phương đó.",
             CUBE(*L, s=5), ("vol_prism", ["A", "B", "C", "D"], "A'"), 125.0))
V.append(pos("T05", T, "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3 và AA' = 4. Tính độ dài đường chéo AC'.",
             box(*L, 2, 3, 4), ("len", "A", "C'"), math.sqrt(29)))
V.append(pos("T06", T, "Cho tứ diện OABC, trong đó ba cạnh OA, OB, OC đôi một vuông góc; OA = 2, OB = 3, OC = 6. Tính thể tích của khối tứ diện.",
             tetra_corner("O", "A", "B", "C", 2, 3, 6), ("vol_pyr", "O", ["A", "B", "C"]), 6.0))
V.append(pos("T07", T, "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 4, SA vuông góc với đáy và SA = 4. Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
             pyr_rect("S", "A", "B", "C", "D", 4, 4, 4), ("angle", "S", "C", ["A", "B", "C"]), math.degrees(math.atan(1 / R2))))
V.append(pos("T08", T, "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 6, SA vuông góc với mặt phẳng (ABC) và SA = 4. Tính thể tích khối chóp S.ABC.",
             pyr_tri_equil("S", "A", "B", "C", 6, 4), ("vol_pyr", "S", ["A", "B", "C"]), 12 * R3))
V.append(pos("T09", T, "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh 4 và cạnh bên AA' = 3. Tính thể tích khối lăng trụ ABC.A'B'C'.",
             prism_tri_equil("A", "B", "C", "A'", "B'", "C'", 4, 3), ("vol_prism", ["A", "B", "C"], "A'"), 12 * R3))
V.append(pos("T10", T, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 6, SA ⊥ (ABCD), SA = 8. Tính độ dài SC.",
             pyr_rect("S", "A", "B", "C", "D", 6, 6, 8), ("len", "S", "C"), math.sqrt(136)))
V.append(pos("T11", T, "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), tam giác ABC vuông tại B, AB = 4, BC = 3, SA = 3. Tính diện tích tam giác ABC.",
             pyr_tri_right("S", "A", "B", "C", "B", 4, 3, 3, "A"), ("area", ["A", "B", "C"]), 6.0))
V.append(pos("T12", T, "Một hình hộp chữ nhật ABCD.A'B'C'D' có ba kích thước AB = 3, BC = 4, CC' = 5. Tính thể tích của khối hộp chữ nhật đó.",
             box(*L, 3, 4, 5), ("vol_prism", ["A", "B", "C", "D"], "A'"), 60.0))
V.append(pos("T13", T, "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2, BC = 5, SA vuông góc với đáy, SA = 3. Vẽ hình chóp S.ABCD.",
             pyr_rect("S", "A", "B", "C", "D", 2, 5, 3)))
V.append(pos("T14", T, "Cho tứ diện ABCD với các cạnh AB, AC, AD vuông góc với nhau từng đôi một. Biết AB = 3, AC = 4, AD = 12, hãy tính độ dài cạnh BC.",
             tetra_corner("A", "B", "C", "D", 3, 4, 12), ("len", "B", "C"), 5.0))
V.append(pos("T15", T, "Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A với AB = AC = 4, SA vuông góc với đáy và SA = 6. Tính thể tích khối chóp S.ABC.",
             pyr_tri_right("S", "A", "B", "C", "A", 4, 4, 6, "A"), ("vol_pyr", "S", ["A", "B", "C"]), 16.0))
V.append(pos("T16", T, "Cho khối chóp tứ giác đều S.ABCD với cạnh đáy 4 và đường cao bằng 6. Tính thể tích khối chóp này.",
             pyr_quad_regular("S", "A", "B", "C", "D", 4, 6), ("vol_pyr", "S", ["A", "B", "C", "D"]), 32.0))
V.append(pos("T17", T, "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 3 và cạnh bên bằng 2√3. Tính thể tích khối chóp S.ABC.",
             pyr_tri_regular("S", "A", "B", "C", 3, 3), ("vol_pyr", "S", ["A", "B", "C"]), 9 * R3 / 4))
# ── exam wording (symbolic a ⇒ gold is the coefficient with a = 1) ───────────────────────────────────────────────────
V.append(pos("E01", E, "Cho khối chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = 3a. Thể tích của khối chóp đã cho bằng",
             pyr_rect("S", "A", "B", "C", "D", 1, 1, 3), ("vol_pyr", "S", ["A", "B", "C", "D"]), 1.0))
V.append(pos("E02", E, "Cho khối lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = a, BC = 2a và AA' = 3a. Thể tích khối lăng trụ đã cho bằng",
             prism_tri_right("A", "B", "C", "A'", "B'", "C'", "B", 1, 2, 3), ("vol_prism", ["A", "B", "C"], "A'"), 3.0))
V.append(pos("E03", E, "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a√3, SA vuông góc với mặt phẳng (ABC) và SA = 2a. Tính thể tích khối chóp S.ABC theo a.",
             pyr_tri_right("S", "A", "B", "C", "B", 1, R3, 2, "A"), ("vol_pyr", "S", ["A", "B", "C"]), R3 / 3))
V.append(pos("E04", E, "Cho khối lập phương ABCD.A'B'C'D' có cạnh bằng 3. Thể tích của khối lập phương đã cho bằng A. 9. B. 27. C. 81. D. 18.",
             CUBE(*L, s=3), ("vol_prism", ["A", "B", "C", "D"], "A'"), 27.0))
V.append(pos("E05", E, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a√2. Góc giữa đường thẳng SC và mặt phẳng (ABCD) bằng",
             pyr_rect("S", "A", "B", "C", "D", 1, 1, R2), ("angle", "S", "C", ["A", "B", "C"]), 45.0))
V.append(pos("E06", E, "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, AD = 2a, AA' = 2a. Tính thể tích khối hộp chữ nhật đã cho.",
             box(*L, 1, 2, 2), ("vol_prism", ["A", "B", "C", "D"], "A'"), 4.0))
V.append(pos("E07", E, "Cho khối chóp S.ABC có SA ⊥ (ABC), SA = 2, tam giác ABC đều cạnh bằng 2. Thể tích khối chóp S.ABC bằng",
             pyr_tri_equil("S", "A", "B", "C", 2, 2), ("vol_pyr", "S", ["A", "B", "C"]), 2 * R3 / 3))
V.append(pos("E08", E, "Cho khối lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh 2a và AA' = a√3. Thể tích của khối lăng trụ đã cho bằng",
             prism_tri_equil("A", "B", "C", "A'", "B'", "C'", 2, R3), ("vol_prism", ["A", "B", "C"], "A'"), 3.0))
V.append(pos("E09", E, "Cho hình chóp S.ABC có đáy là tam giác vuông tại A, AB = 3, AC = 4, SA vuông góc với đáy và SA = 12. Khoảng cách từ A đến mặt phẳng (SBC) bằng",
             pyr_tri_right("S", "A", "B", "C", "A", 3, 4, 12, "A"), ("dist", "A", ["S", "B", "C"]), 12 / math.sqrt(26)))
V.append(pos("E10", E, "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc với nhau và OA = OB = OC = a. Thể tích khối tứ diện OABC bằng",
             tetra_corner("O", "A", "B", "C", 1, 1, 1), ("vol_pyr", "O", ["A", "B", "C"]), 1 / 6))
V.append(pos("E11", E, "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Góc giữa đường thẳng A'C và mặt phẳng (ABCD) bằng",
             CUBE(*L, s=1), ("angle", "A'", "C", ["A", "B", "C"]), math.degrees(math.atan(1 / R2))))
V.append(pos("E12", E, "Cho khối chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = a, AD = a√3, SA vuông góc với mặt phẳng đáy và SA = 2a. Thể tích khối chóp S.ABCD bằng A. 2a³√3/3. B. a³√3. C. 2a³√3. D. a³√3/3.",
             pyr_rect("S", "A", "B", "C", "D", 1, R3, 2), ("vol_pyr", "S", ["A", "B", "C", "D"]), 2 * R3 / 3))
V.append(pos("E13", E, "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2a, SA vuông góc với đáy và góc giữa SC với mặt phẳng đáy bằng 45°. Tính thể tích khối chóp S.ABCD.",
             pyr_rect("S", "A", "B", "C", "D", 2, 2, 2 * R2), ("vol_pyr", "S", ["A", "B", "C", "D"]), 8 * R2 / 3))
V.append(pos("E14", E, "Cho khối lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại A, AB = 2 và AA' = 3. Thể tích khối lăng trụ đã cho bằng",
             prism_tri_right("A", "B", "C", "A'", "B'", "C'", "A", 2, 2, 3), ("vol_prism", ["A", "B", "C"], "A'"), 6.0))
V.append(pos("E15", E, "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 4, AD = 3, AA' = 12. Độ dài đường chéo BD' bằng",
             box(*L, 4, 3, 12), ("len", "B", "D'"), 13.0))
V.append(pos("E16", E, "Cho khối chóp S.ABC có đáy là tam giác vuông cân tại B, AB = a, SA vuông góc với đáy và SA = a. Khoảng cách từ A đến mặt phẳng (SBC) bằng",
             pyr_tri_right("S", "A", "B", "C", "B", 1, 1, 1, "A"), ("dist", "A", ["S", "B", "C"]), 1 / R2))
# ── teacher wording ──────────────────────────────────────────────────────────────────────────────────────────────────
V.append(pos("G01", G, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3. Biết rằng cạnh bên SA vuông góc với mặt phẳng đáy và SA = 3. Hãy vẽ hình chóp và tính thể tích của nó.",
             pyr_rect("S", "A", "B", "C", "D", 3, 3, 3), ("vol_pyr", "S", ["A", "B", "C", "D"]), 9.0))
V.append(pos("G02", G, "Xét hình lăng trụ đứng ABC.A'B'C' với đáy ABC vuông tại C, CA = 5, CB = 12. Chiều cao của lăng trụ bằng 4. Tính thể tích khối lăng trụ ABC.A'B'C'.",
             prism_tri_right("A", "B", "C", "A'", "B'", "C'", "C", 5, 12, 4), ("vol_prism", ["A", "B", "C"], "A'"), 120.0))
V.append(pos("G03", G, "Trong không gian, cho tứ diện ABCD có ba cạnh AB, AC, AD đôi một vuông góc với nhau. Cho biết AB = 1, AC = 2 và AD = 3. Em hãy dựng tứ diện ABCD.",
             tetra_corner("A", "B", "C", "D", 1, 2, 3)))
V.append(pos("G04", G, "Cho hình chóp S.ABC, đáy ABC là tam giác vuông tại B với BA = 6, BC = 8. Đường thẳng SA vuông góc với mặt phẳng (ABC) và SA = 10. Gọi M là trung điểm của SC. Hãy dựng hình chóp và điểm M.",
             pyr_tri_right("S", "A", "B", "C", "B", 6, 8, 10, "A"), aux={"M": ("S", "C")}))
V.append(pos("G05", G, "Cho hình hộp chữ nhật ABCD.A'B'C'D'. Biết AB = 6, AD = 8 và AA' = 5. Tính độ dài đoạn AC'.",
             box(*L, 6, 8, 5), ("len", "A", "C'"), math.sqrt(125)))
V.append(pos("G06", G, "Cho hình chóp S.ABCD có đáy là hình chữ nhật ABCD, trong đó AB = 4 và AD = 6. Cạnh bên SA = 5 và vuông góc với mặt phẳng đáy. Hãy tính thể tích khối chóp.",
             pyr_rect("S", "A", "B", "C", "D", 4, 6, 5), ("vol_pyr", "S", ["A", "B", "C", "D"]), 40.0))
V.append(pos("G07", G, "Cho hình lập phương ABCD.A'B'C'D' có cạnh 4. Tính diện tích tam giác A'BD.",
             CUBE(*L, s=4), ("area", ["A'", "B", "D"]), 8 * R3))
V.append(pos("G08", G, "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, biết AB = 5 và AC = 12. Hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với điểm A, SA = 6. Tính thể tích khối chóp S.ABC.",
             pyr_tri_right("S", "A", "B", "C", "A", 5, 12, 6, "A"), ("vol_pyr", "S", ["A", "B", "C"]), 60.0))
V.append(pos("G09", G, "Cho lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình vuông cạnh 3 và cạnh bên bằng 7. Tính thể tích khối lăng trụ.",
             box(*L, 3, 3, 7), ("vol_prism", ["A", "B", "C", "D"], "A'"), 63.0))
V.append(pos("G10", G, "Cho tứ diện SABC có SA, SB, SC vuông góc với nhau từng đôi một, SA = 4, SB = 4, SC = 2. Tính khoảng cách từ S đến mặt phẳng (ABC).",
             tetra_corner("S", "A", "B", "C", 4, 4, 2), ("dist", "S", ["A", "B", "C"]), 4 / math.sqrt(6)))
V.append(pos("G11", G, "Cho hình chóp S.ABCD đáy ABCD là hình chữ nhật, AB = 3, AD = 4. SA vuông góc với (ABCD) và SA = 5. Tính khoảng cách giữa hai điểm S và C.",
             pyr_rect("S", "A", "B", "C", "D", 3, 4, 5), ("len", "S", "C"), math.sqrt(50)))
V.append(pos("G12", G, "Bài toán: Cho hình lăng trụ đứng ABC.A'B'C' có tam giác ABC vuông tại B, BA = 3, BC = 4, AA' = 6. Yêu cầu: tính độ dài A'C.",
             prism_tri_right("A", "B", "C", "A'", "B'", "C'", "B", 3, 4, 6), ("len", "A'", "C"), math.sqrt(61)))
V.append(pos("G13", G, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy, SA = 2√3. Hãy xác định và tính góc giữa SB và mặt phẳng (ABCD).",
             pyr_rect("S", "A", "B", "C", "D", 2, 2, 2 * R3), ("angle", "S", "B", ["A", "B", "C"]), 60.0))
V.append(pos("G14", G, "Cho hình hộp chữ nhật MNPQ.M'N'P'Q' có MN = 3, MQ = 5 và MM' = 4. Vẽ hình hộp chữ nhật đó.",
             box("M", "N", "P", "Q", "M'", "N'", "P'", "Q'", 3, 5, 4)))
V.append(pos("G15", G, "Cho hình chóp S.ABC có SA ⊥ (ABC). Tam giác ABC đều cạnh 3 và SA = 3. Gọi M là trung điểm BC. Tính độ dài SM.",
             pyr_tri_equil("S", "A", "B", "C", 3, 3), ("len", "S", "M"), math.sqrt(63) / 2, aux={"M": ("B", "C")}))
# ── learner colloquial ───────────────────────────────────────────────────────────────────────────────────────────────
V.append(pos("C01", C, "Mình có bài: hình chóp S.ABCD đáy là hình vuông cạnh 5, SA vuông góc đáy, SA = 6. Tính thể tích giúp mình với.",
             pyr_rect("S", "A", "B", "C", "D", 5, 5, 6), ("vol_pyr", "S", ["A", "B", "C", "D"]), 50.0))
V.append(pos("C02", C, "Cho em hỏi: lăng trụ đứng ABC.A'B'C' đáy vuông tại A, AB = 3, AC = 4, AA' = 5 thì thể tích là bao nhiêu ạ?",
             prism_tri_right("A", "B", "C", "A'", "B'", "C'", "A", 3, 4, 5), ("vol_prism", ["A", "B", "C"], "A'"), 30.0))
V.append(pos("C03", C, "Vẽ giúp mình hình lập phương ABCD.A'B'C'D' cạnh 6 nhé.", CUBE(*L, s=6)))
V.append(pos("C04", C, "cho hinh chop S.ABC co day ABC vuong tai B, AB = 2, BC = 3, SA vuong goc voi day va SA = 4. tinh the tich khoi chop",
             pyr_tri_right("S", "A", "B", "C", "B", 2, 3, 4, "A"), ("vol_pyr", "S", ["A", "B", "C"]), 4.0))
V.append(pos("C05", C, "Tứ diện OABC có OA, OB, OC vuông góc đôi một nha, OA = 1, OB = 2, OC = 3. Thể tích bằng mấy vậy?",
             tetra_corner("O", "A", "B", "C", 1, 2, 3), ("vol_pyr", "O", ["A", "B", "C"]), 1.0))
V.append(pos("C06", C, "Bạn ơi, hình hộp chữ nhật ABCD.A'B'C'D' có AB = 1, AD = 2, AA' = 2 thì đường chéo AC' dài bao nhiêu?",
             box(*L, 1, 2, 2), ("len", "A", "C'"), 3.0))
V.append(pos("C07", C, "Thầy cho bài này: chóp S.ABCD đáy chữ nhật AB = 2, AD = 3, SA vuông góc (ABCD), SA = 4. Em muốn xem hình 3D của nó.",
             pyr_rect("S", "A", "B", "C", "D", 2, 3, 4)))
V.append(pos("C08", C, "Em cần tính góc giữa SC và đáy (ABC), biết hình chóp S.ABC có SA vuông góc với đáy, đáy ABC là tam giác vuông tại B với AB = 3, BC = 4 và SA = 5.",
             pyr_tri_right("S", "A", "B", "C", "B", 3, 4, 5, "A"), ("angle", "S", "C", ["A", "B", "C"]), 45.0))
V.append(pos("C09", C, "hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh 2, cạnh bên AA' = 5. tính thể tích lăng trụ",
             prism_tri_equil("A", "B", "C", "A'", "B'", "C'", 2, 5), ("vol_prism", ["A", "B", "C"], "A'"), 5 * R3))
V.append(pos("C10", C, "Khối lập phương ABCD.A'B'C'D' có đường chéo AC' bằng 3√3. Tính thể tích khối lập phương.",
             CUBE(*L, s=3), ("vol_prism", ["A", "B", "C", "D"], "A'"), 27.0))

M, X, Q, O = "missing_data", "contradiction", "negation_condition_unsupported", "other_subject"
N = [
    neg("N01", M, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4 và SA vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.", "MISSING_DATA"),
    neg("N02", M, "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A với AB = 3. Biết AA' = 5. Tính thể tích khối lăng trụ.", "MISSING_DATA"),
    neg("N03", M, "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2 và AD = 3. Tính thể tích khối hộp.", "MISSING_DATA"),
    neg("N04", M, "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 2, OB = 3. Tính thể tích khối tứ diện.", "MISSING_DATA"),
    neg("N05", M, "Cho hình chóp S.ABC có đáy là tam giác đều cạnh 3 và SA = 4. Tính thể tích khối chóp S.ABC.", "MISSING_DATA"),
    neg("N06", M, "Cho hình chóp S.ABCD có đáy là hình chữ nhật, SA vuông góc với đáy, SA = 3, AB = 4. Tính thể tích khối chóp.", "MISSING_DATA"),
    neg("N07", X, "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 5, BC = 4 và AC = 3, SA vuông góc với đáy, SA = 2. Tính thể tích khối chóp.", "CONTRADICTION"),
    neg("N08", X, "Cho hình lập phương ABCD.A'B'C'D' có AB = 2 và AA' = 3. Tính thể tích khối lập phương.", "CONTRADICTION"),
    neg("N09", X, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông với AB = 3 và BC = 5, SA vuông góc với đáy và SA = 4. Tính thể tích khối chóp S.ABCD.", "CONTRADICTION"),
    neg("N10", X, "Cho tứ diện ABCD có AB, AC, AD đôi một vuông góc, AB = 3, AC = 4 và BC = 6. Tính thể tích khối tứ diện ABCD.", "CONTRADICTION"),
    neg("N11", X, "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh 2, AB = 3 và AA' = 4. Tính thể tích khối lăng trụ.", "CONTRADICTION"),
    neg("N12", Q, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2. Nếu SA vuông góc với mặt phẳng đáy và SA = 3 thì thể tích khối chóp bằng bao nhiêu?", "CONDITIONAL_PREMISE"),
    neg("N13", Q, "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, AB = 3, BC = 4, SA = 5 nhưng SA không vuông góc với mặt phẳng (ABC). Tính thể tích khối chóp S.ABC.", "NEGATED_PREMISE"),
    neg("N14", Q, "Cho tứ diện OABC có OA = 1, OB = 2, OC = 3 và OA, OB, OC không đôi một vuông góc. Tính thể tích khối tứ diện OABC.", "NEGATED_PREMISE"),
    neg("N15", Q, "Cho hình hộp ABCD.A'B'C'D' có AB = 2, AD = 3, AA' = 4, các mặt bên không phải hình chữ nhật. Tính thể tích khối hộp.", "NEGATED_PREMISE"),
    neg("N16", Q, "Giả sử hình chóp S.ABCD có đáy là hình vuông cạnh 4 và SA vuông góc với đáy. Khi SA thay đổi, tìm giá trị lớn nhất của thể tích khối chóp.", "UNSUPPORTED_REQUEST"),
    neg("N17", Q, "Cho hình chóp S.ABC có SA vuông góc với (ABC) và SA = 2. Chứng minh rằng tam giác SAB vuông tại A.", "UNSUPPORTED_REQUEST"),
    neg("N18", O, "Trong không gian Oxyz, cho hai điểm A(1; 2; 3) và B(3; 0; −1). Tính độ dài đoạn thẳng AB.", "OUT_OF_DOMAIN"),
    neg("N19", O, "Tính đạo hàm của hàm số y = x³ − 3x² + 2.", "OUT_OF_DOMAIN"),
    neg("N20", O, "Một hộp có 5 viên bi đỏ và 3 viên bi xanh. Lấy ngẫu nhiên 2 viên. Tính xác suất để lấy được 2 viên bi đỏ.", "OUT_OF_DOMAIN"),
    neg("N21", O, "Viết chương trình Python tính diện tích hình tròn bán kính r.", "OUT_OF_DOMAIN"),
    neg("N22", O, "Cho hàm số f(x) = 2x + 1. Tính tích phân của f(x) từ 0 đến 1.", "OUT_OF_DOMAIN"),
]

if __name__ == "__main__":
    out = Path(sys.argv[1])
    for name in ("ACCEPTANCE_MANIFEST.json",):
        if (out / name).exists():
            raise SystemExit(f"refusing to overwrite {out / name}")
    ids = [c["case_id"] for c in V + N]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    strata = {}
    for c in V:
        strata[c["phrase_family"]] = strata.get(c["phrase_family"], 0) + 1
    manifest = {
        "schema": "axo-acceptance-manifest/2", "run_id": "model1-final-text-acceptance", "set": "holdout-7",
        "dataset_provenance": ("hand-written by the AXO HYBRID /19 agent from a fixed sampling plan before any case ran on "
                               "candidate 158; not from earlier generators; prospective INTERNAL; EXTERNAL_INDEPENDENCE "
                               "NOT_MEASURED; gold computed twice (closed form + independent coordinates), never from Axo"),
        "valid_cases": V, "negative_cases": N, "attachment_cases": [],
        "counts": {"text_positive": len(V), "text_negative": len(N), "positive_by_stratum": strata},
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "ACCEPTANCE_MANIFEST.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(len(V), len(N), strata)
