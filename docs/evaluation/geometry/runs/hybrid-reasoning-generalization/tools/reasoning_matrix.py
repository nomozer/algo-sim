# -*- coding: utf-8 -*-
"""DEVELOPMENT matrix for Hybrid reasoning & generalization (run `hybrid-reasoning-generalization`).

MEASUREMENT_CLASS = OFFLINE_DEVELOPMENT_MATRIX · HELD_OUT_CLAIM = NONE · EVALUATOR_INDEPENDENCE = NONE · live calls 0.
The cases were authored by the same agent that reads the planner; they are a development corpus, never an H-1 result.

Every case is a hand-authored gold TypedFactNext /2 extraction driven through the real offline product path
(`run_hybrid_offline`: verbatim quotes → bridge_v2 → Source Gate → planner → engine → Adapter /4 → Scene3D).
Expected values come from the independent oracle (`docs/evaluation/geometry/custodian/geometry_oracle.py`, which imports
no product code) on hand-written rational coordinates recorded in the case, or from a hand derivation written in the
case's `oracle` note — never from product output.

Usage (from `backend/`, PYTHONIOENCODING=utf-8 ALLOW_LIVE_AI=0):
    python <this file> --label before      # writes results/matrix_before.json
    python <this file> --label after       # writes results/matrix_after.json
    python <this file> --render            # writes results/matrix_tables.md from the JSON receipts
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import time
import tracemalloc
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "docs" / "evaluation" / "geometry" / "custodian"))

import geometry_oracle as O  # noqa: E402  (independent: imports only `fractions`)

# ── oracle helpers (built only from geometry_oracle primitives) ──────────────────────────────────────────────────────


def V(x, y, z):
    return O.V(x, y, z)


def mid(a, b):
    return tuple((x + y) / 2 for x, y in zip(a, b))


def cen(*ps):
    return tuple(sum(c) / len(ps) for c in zip(*ps))


def d2_pt_line(p, a, b):
    u = O.sub(b, a)
    c = O.cross(O.sub(p, a), u)
    return O.dot(c, c) / O.dot(u, u)


def d2_pt_plane(p, a, b, c):
    return O.distance_sq_point_plane(p, O.plane_through(a, b, c))


def cos2_line_plane(p, q, a, b, c):
    n = O.plane_through(a, b, c)[1]
    return 1 - O.cos_sq(O.sub(q, p), n)


def cos2_planes(a1, b1, c1, a2, b2, c2):
    return O.cos_sq(O.plane_through(a1, b1, c1)[1], O.plane_through(a2, b2, c2)[1])


def cos2_lines(p, q, r, s):
    return O.cos_sq(O.sub(q, p), O.sub(s, r))


def area2(*poly):
    acc = (F(0), F(0), F(0))
    for i in range(1, len(poly) - 1):
        acc = O.add(acc, O.cross(O.sub(poly[i], poly[0]), O.sub(poly[i + 1], poly[0])))
    return O.dot(acc, acc) / 4


def d2_skew(p, q, r, s):
    n = O.cross(O.sub(q, p), O.sub(s, r))
    t = O.dot(O.sub(r, p), n)
    return t * t / O.dot(n, n)


def foot_line(p, a, b):
    u = O.sub(b, a)
    t = O.dot(O.sub(p, a), u) / O.dot(u, u)
    return tuple(x + t * y for x, y in zip(a, u))


def foot_plane(p, a, b, c):
    a_, n = O.plane_through(a, b, c)
    t = O.eval_plane((a_, n), p) / O.dot(n, n)
    return tuple(x - t * y for x, y in zip(p, n))


# ── frames (hand-written rational coordinates) ───────────────────────────────────────────────────────────────────────
# P2: square pyramid S.ABCD, side 2, SA ⊥ (ABCD), SA = 2.  P3: same with SA = 3.
P2 = dict(A=V(0, 0, 0), B=V(2, 0, 0), C=V(2, 2, 0), D=V(0, 2, 0), S=V(0, 0, 2))
P3 = {**P2, "S": V(0, 0, 3)}
# R: right prism ABC.A'B'C', right angle at A, AB = 3, AC = 4, AA' = 2.
R = {"A": V(0, 0, 0), "B": V(3, 0, 0), "C": V(0, 4, 0), "A'": V(0, 0, 2), "B'": V(3, 0, 2), "C'": V(0, 4, 2)}
# T: tetrahedron O.ABC, OA, OB, OC pairwise perpendicular, OA = 1, OB = 2, OC = 3.
T = dict(O=V(0, 0, 0), A=V(1, 0, 0), B=V(0, 2, 0), C=V(0, 0, 3))

SG = [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": None}]


def _goal(gid, gtype, target, quote):
    return {"goal_id": gid, "kind": "measurement", "goal_type": gtype, "target": target, "quote": quote, "solid_id": "s1"}


def pyramid(side, h, *, goals, extra_text="", extra_prem=(), described=(), sections=(), unresolved=()):
    base = (f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}, "
            f"SA vuông góc với mặt phẳng (ABCD) và SA = {h}. ")
    prem = [
        {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": side},
         "quote": f"đáy ABCD là hình vuông cạnh {side}", "solid_id": "s1"},
        {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
         "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": h}, "quote": f"SA = {h}", "solid_id": "s1"},
    ]
    prem += list(extra_prem)
    return _payload("Cho hình chóp S.ABCD", "pyramid", "S.ABCD", base + extra_text, prem, goals, described, sections, unresolved)


def prism(*, goals, extra_text="", extra_prem=(), described=(), sections=()):
    base = "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và AA' = 2. "
    prem = [
        {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
         "quote": "Cho hình lăng trụ đứng ABC.A'B'C'", "solid_id": "s1"},
        {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A",
         "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2"}, "quote": "AA' = 2", "solid_id": "s1"},
        *extra_prem,
    ]
    return _payload("Cho hình lăng trụ đứng ABC.A'B'C'", "prism", "ABC.A'B'C'", base + extra_text, prem, goals,
                    described, sections, ())


def tetra(*, goals, notation="O.ABC"):     # extraction convention: "tứ diện OABC" ⇒ O.ABC (typed_fact_next_extraction §1)
    base = "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 1, OB = 2, OC = 3. "
    prem = [
        {"kind": "perpendicular_lines", "args": {"line1": ["O", "A"], "line2": ["O", "B"]},
         "quote": "OA, OB, OC đôi một vuông góc", "solid_id": "s1"},
        {"kind": "perpendicular_lines", "args": {"line1": ["O", "B"], "line2": ["O", "C"]},
         "quote": "OA, OB, OC đôi một vuông góc", "solid_id": "s1"},
        {"kind": "perpendicular_lines", "args": {"line1": ["O", "A"], "line2": ["O", "C"]},
         "quote": "OA, OB, OC đôi một vuông góc", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["O", "A"], "value": "1"}, "quote": "OA = 1", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["O", "B"], "value": "2"}, "quote": "OB = 2", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["O", "C"], "value": "3"}, "quote": "OC = 3", "solid_id": "s1"},
    ]
    return _payload("Cho tứ diện OABC", "pyramid", notation, base, prem, goals, (), (), ())


def _payload(solid_quote, stype, notation, text, prem, goals, described, sections, unresolved):
    text = text + " ".join(g[3] + "." for g in goals)
    p = {
        "schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": stype, "notation": notation, "quote": solid_quote}],
        "premises": prem, "relations": [], "derived_sections": list(sections),
        "described_points": list(described),
        "simulation_goals": [{**SG[0], "quote": solid_quote}],
        "math_goals": [_goal(*g) for g in goals],
    }
    if unresolved:
        p["unresolved"] = list(unresolved)
    return text, p


def mp(pt, seg, q):        # midpoint premise
    return {"kind": "midpoint", "args": {"point": pt, "segment": list(seg)}, "quote": q, "solid_id": "s1"}


def dmid(i, seg, q):      # seg: a 2-tuple of labels, or a string of two single-letter labels
    return {"described_id": i, "kind": "midpoint", "segment": list(seg), "quote": q}


# ── cases ────────────────────────────────────────────────────────────────────────────────────────────────────────────
# expect: ("SERVED", {goal: (measure, Fraction)}) where measure ∈ {"len", "area"} compares SQUARES and "cos2" compares cos²;
#         ("REFUSED", group, {codes}) where group ∈ {"refusal", "clarification"}.
# primitives: for a positive case, the Registry functions the plan needs (all exist ⇒ a refusal is NO_PLAN_DESPITE_PRIMITIVES).

def build_cases() -> list[dict]:
    C = []

    def add(cid, family, tp, expect, oracle, primitives=(), level=None):
        C.append({"id": cid, "family": family, "text": tp[0], "payload": tp[1], "expect": expect, "oracle": oracle,
                  "primitives": list(primitives), "level": level})

    P, R_, T_ = P2, R, T
    # point–plane
    add("PP1", "point-plane distance", pyramid("2", "2", goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]},
        "Tính khoảng cách từ A đến mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(P["A"], P["S"], P["B"], P["C"]))}), "P2 frame; oracle d²(A,(SBC))")
    add("PP2", "point-plane distance", pyramid("2", "2", extra_text="Gọi M là trung điểm của SD. ",
        extra_prem=[mp("M", "SD", "Gọi M là trung điểm của SD")],
        goals=[("q1", "distance", {"point": "M", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ M đến mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(mid(P["S"], P["D"]), P["S"], P["B"], P["C"]))}), "P2; M = mid(SD)")
    add("PP3", "point-plane distance (described centroid)", pyramid("2", "2",
        described=[{"described_id": "g1", "kind": "centroid", "polygon": ["S", "C", "D"], "quote": "trọng tâm của tam giác SCD"}],
        goals=[("q1", "distance", {"point": "@g1", "plane": ["A", "B", "C", "D"]},
                "Tính khoảng cách từ trọng tâm của tam giác SCD đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(cen(P["S"], P["C"], P["D"]), P["A"], P["B"], P["C"]))}), "P2; G = centroid(SCD)",
        ("centroid", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    add("PP4", "point-plane distance (described intersection)", pyramid("2", "2",
        described=[{"described_id": "o1", "kind": "intersect_line_line", "line1": ["A", "C"], "line2": ["B", "D"],
                    "quote": "giao điểm của AC và BD"}],
        goals=[("q1", "distance", {"point": "@o1", "plane": ["S", "B", "C"]},
                "Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(V(1, 1, 0), P["S"], P["B"], P["C"]))}), "P2; O = AC∩BD = (1,1,0)",
        ("intersect_line_line", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    add("PP5", "point-plane distance (nested described)", pyramid("2", "2",
        described=[dmid("m1", "SC", "trung điểm của SC"),
                   {"described_id": "h1", "kind": "orthogonal_projection", "point": "@m1", "plane": ["A", "B", "C", "D"],
                    "quote": "hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD)"}],
        goals=[("q1", "distance", {"point": "@h1", "plane": ["S", "A", "D"]},
                "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD) đến mặt phẳng (SAD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(foot_plane(mid(P["S"], P["C"]), P["A"], P["B"], P["C"]), P["S"], P["A"], P["D"]))}),
        "P2; h = proj_(ABCD)(mid SC)", ("midpoint", "orthogonal_projection", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    add("PP6", "point-plane distance (point on plane)", pyramid("2", "2", goals=[("q1", "distance",
        {"point": "B", "plane": ["S", "C", "D"]}, "Tính khoảng cách từ B đến mặt phẳng (SCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(P["B"], P["S"], P["C"], P["D"]))}), "P2; B ∉ (SCD) (control)")
    # point–line
    add("PL1", "point-line distance", pyramid("2", "2", goals=[("q1", "distance", {"point": "A", "line": ["S", "C"]},
        "Tính khoảng cách từ A đến đường thẳng SC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P["A"], P["S"], P["C"]))}), "P2", ("orthogonal_projection_line", "ask_length"),
        "REGISTERED_DECOMPOSITION")
    add("PL2", "point-line distance", pyramid("2", "2", goals=[("q1", "distance", {"point": "S", "line": ["B", "D"]},
        "Tính khoảng cách từ S đến đường thẳng BD")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P["S"], P["B"], P["D"]))}), "P2", ("orthogonal_projection_line", "ask_length"),
        "REGISTERED_DECOMPOSITION")
    add("PL3", "point-line distance (described point)", pyramid("2", "2", described=[dmid("m1", "SC", "trung điểm của SC")],
        goals=[("q1", "distance", {"point": "@m1", "line": ["B", "D"]},
                "Tính khoảng cách từ trung điểm của SC đến đường thẳng BD")]),
        ("SERVED", {"q1": ("len", d2_pt_line(mid(P["S"], P["C"]), P["B"], P["D"]))}), "P2",
        ("midpoint", "orthogonal_projection_line", "ask_length"), "DESCRIPTOR_COMPOSITION")
    add("PL4", "point-line distance (described intersection)", pyramid("2", "2",
        described=[{"described_id": "o1", "kind": "intersect_line_line", "line1": ["A", "C"], "line2": ["B", "D"],
                    "quote": "giao điểm của AC và BD"}],
        goals=[("q1", "distance", {"point": "@o1", "line": ["S", "C"]},
                "Tính khoảng cách từ giao điểm của AC và BD đến đường thẳng SC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(V(1, 1, 0), P["S"], P["C"]))}), "P2; O = (1,1,0)",
        ("intersect_line_line", "orthogonal_projection_line", "ask_length"), "DESCRIPTOR_COMPOSITION")
    add("PL5", "point-line distance (line through described point)", pyramid("2", "2",
        described=[dmid("m1", "SC", "trung điểm của SC")],
        goals=[("q1", "distance", {"point": "B", "line": ["A", "@m1"]},
                "Tính khoảng cách từ B đến đường thẳng nối A với trung điểm của SC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P["B"], P["A"], mid(P["S"], P["C"])))}), "P2",
        ("midpoint", "orthogonal_projection_line", "ask_length"), "DESCRIPTOR_COMPOSITION")
    add("PL6", "point-line distance (point on line, degenerate)", pyramid("2", "2", extra_text="Gọi M là trung điểm của AB. ",
        extra_prem=[mp("M", "AB", "Gọi M là trung điểm của AB")],
        goals=[("q1", "distance", {"point": "M", "line": ["A", "B"]}, "Tính khoảng cách từ M đến đường thẳng AB")]),
        ("SERVED", {"q1": ("len", d2_pt_line(mid(P["A"], P["B"]), P["A"], P["B"]))}), "P2; M ∈ AB ⇒ 0 (degenerate edge)",
        ("orthogonal_projection_line", "ask_length"), "REGISTERED_DECOMPOSITION")
    add("PL7", "point-line distance (intersection line result)", pyramid("2", "3",
        goals=[("q1", "distance", {"point": "S", "line": ["A", "C"]}, "Tính khoảng cách từ S đến đường thẳng AC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P3["S"], P3["A"], P3["C"]))}), "P3; foot = A (SA ⊥ AC)",
        ("orthogonal_projection_line", "ask_length"), "REGISTERED_DECOMPOSITION")
    # prism
    add("PR1", "prism point-plane", prism(goals=[("q1", "distance", {"point": "A", "plane": ["A'", "B", "C"]},
        "Tính khoảng cách từ A đến mặt phẳng (A'BC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(R_["A"], R_["A'"], R_["B"], R_["C"]))}), "R frame")
    add("PR2", "prism point-line", prism(goals=[("q1", "distance", {"point": "A'", "line": ["B", "C"]},
        "Tính khoảng cách từ A' đến đường thẳng BC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(R_["A'"], R_["B"], R_["C"]))}), "R", ("orthogonal_projection_line", "ask_length"),
        "REGISTERED_DECOMPOSITION")
    add("PR3", "prism angle line-plane", prism(goals=[("q1", "angle", {"line": ["A'", "B"], "plane": ["A", "B", "C"]},
        "Tính góc giữa đường thẳng A'B và mặt phẳng (ABC)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(R_["A'"], R_["B"], R_["A"], R_["B"], R_["C"]))}), "R")
    add("PR4", "prism angle plane-plane", prism(goals=[("q1", "angle", {"plane1": ["A'", "B", "C"], "plane2": ["A", "B", "C"]},
        "Tính góc giữa mặt phẳng (A'BC) và mặt phẳng (ABC)")]),
        ("SERVED", {"q1": ("cos2", cos2_planes(R_["A'"], R_["B"], R_["C"], R_["A"], R_["B"], R_["C"]))}), "R")
    add("PR5", "prism skew lines distance", prism(goals=[("q1", "distance", {"line1": ["A", "A'"], "line2": ["B", "C"]},
        "Tính khoảng cách giữa hai đường thẳng AA' và BC")]),
        ("SERVED", {"q1": ("len", d2_skew(R_["A"], R_["A'"], R_["B"], R_["C"]))}), "R")
    add("PR6", "prism point-plane (described point)", prism(described=[dmid("m1", ("B'", "C'"), "trung điểm của B'C'")],
        goals=[("q1", "distance", {"point": "@m1", "plane": ["A'", "B", "C"]},
                "Tính khoảng cách từ trung điểm của B'C' đến mặt phẳng (A'BC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(mid(R_["B'"], R_["C'"]), R_["A'"], R_["B"], R_["C"]))}), "R",
        ("midpoint", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    add("PR7", "prism circumcenter of right base", prism(described=[{"described_id": "o1", "kind": "circumcenter",
        "polygon": ["A", "B", "C"], "quote": "tâm đường tròn ngoại tiếp tam giác ABC"}],
        goals=[("q1", "distance", {"segment": ["@o1", "A'"]},
                "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác ABC với A'")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(mid(R_["B"], R_["C"]), R_["A'"]))}),
        "R; circumcenter of a right triangle = midpoint of hypotenuse BC", ("orthogonal_projection_line", "intersect_line_line",
                                                                           "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    add("PR8", "prism orthocenter of right base (coincides with A)", prism(described=[{"described_id": "h1",
        "kind": "orthocenter", "polygon": ["A", "B", "C"], "quote": "trực tâm của tam giác ABC"}],
        goals=[("q1", "distance", {"segment": ["@h1", "A'"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác ABC với A'")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(R_["A"], R_["A'"]))}),
        "R; orthocenter of a triangle right at A is A", ("orthogonal_projection_line", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")
    # angles
    add("AN1", "angle line-plane", pyramid("2", "2", goals=[("q1", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]},
        "Tính góc giữa SC và mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(P["S"], P["C"], P["A"], P["B"], P["C"]))}), "P2")
    add("AN2", "angle plane-plane", pyramid("2", "2", goals=[("q1", "angle", {"plane1": ["S", "B", "C"],
        "plane2": ["A", "B", "C", "D"]}, "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("cos2", cos2_planes(P["S"], P["B"], P["C"], P["A"], P["B"], P["C"]))}), "P2")
    add("AN3", "angle line-line", pyramid("2", "2", goals=[("q1", "angle", {"line1": ["S", "B"], "line2": ["C", "D"]},
        "Tính góc giữa hai đường thẳng SB và CD")]),
        ("SERVED", {"q1": ("cos2", cos2_lines(P["S"], P["B"], P["C"], P["D"]))}), "P2")
    add("AN4", "angle line-plane (described point)", pyramid("2", "2", described=[dmid("m1", "CD", "trung điểm của CD")],
        goals=[("q1", "angle", {"line": ["S", "@m1"], "plane": ["A", "B", "C", "D"]},
                "Tính góc giữa đường thẳng nối S với trung điểm của CD và mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(P["S"], mid(P["C"], P["D"]), P["A"], P["B"], P["C"]))}), "P2",
        ("midpoint", "ask_angle_line_plane"), "DESCRIPTOR_COMPOSITION")
    add("AN5", "angle line-plane (lateral face)", pyramid("2", "2", goals=[("q1", "angle", {"line": ["S", "C"],
        "plane": ["S", "A", "B"]}, "Tính góc giữa SC và mặt phẳng (SAB)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(P["S"], P["C"], P["S"], P["A"], P["B"]))}), "P2")
    add("AN6", "angle line-line (described centroid)", pyramid("2", "2",
        described=[{"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"}],
        goals=[("q1", "angle", {"line1": ["A", "@g1"], "line2": ["B", "C"]},
                "Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và đường thẳng BC")]),
        ("SERVED", {"q1": ("cos2", cos2_lines(P["A"], cen(P["S"], P["B"], P["C"]), P["B"], P["C"]))}), "P2",
        ("centroid", "ask_angle_lines"), "DESCRIPTOR_COMPOSITION")
    add("AN7", "angle line-plane (described point, slanted plane)", pyramid("2", "2", described=[dmid("m1", "AD", "trung điểm của AD")],
        goals=[("q1", "angle", {"line": ["B", "@m1"], "plane": ["S", "B", "C"]},
                "Tính góc giữa đường thẳng nối B với trung điểm của AD và mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(P["B"], mid(P["A"], P["D"]), P["S"], P["B"], P["C"]))}), "P2",
        ("midpoint", "ask_angle_line_plane"), "DESCRIPTOR_COMPOSITION")
    # perpendicularity
    add("PE1", "perpendicular (angle 90°)", pyramid("2", "2", goals=[("q1", "angle", {"line1": ["B", "C"], "line2": ["S", "B"]},
        "Tính góc giữa hai đường thẳng BC và SB")]),
        ("SERVED", {"q1": ("cos2", cos2_lines(P["B"], P["C"], P["S"], P["B"]))}), "P2; BC ⊥ (SAB) ⇒ cos² = 0")
    add("PE2", "perpendicular (tetrahedron pairwise ⊥)", tetra(goals=[("q1", "distance", {"point": "O", "plane": ["A", "B", "C"]},
        "Tính khoảng cách từ O đến mặt phẳng (ABC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(T_["O"], T_["A"], T_["B"], T_["C"]))}), "T frame; 1/d² = 1 + 1/4 + 1/9")
    add("PE3", "perpendicular (tetrahedron angle)", tetra(goals=[("q1", "angle", {"plane1": ["A", "B", "C"], "plane2": ["O", "B", "C"]},
        "Tính góc giữa mặt phẳng (ABC) và mặt phẳng (OBC)")]),
        ("SERVED", {"q1": ("cos2", cos2_planes(T_["A"], T_["B"], T_["C"], T_["O"], T_["B"], T_["C"]))}), "T")
    add("PE4", "perpendicular (tetrahedron point-line)", tetra(goals=[("q1", "distance", {"point": "O", "line": ["B", "C"]},
        "Tính khoảng cách từ O đến đường thẳng BC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(T_["O"], T_["B"], T_["C"]))}), "T", ("orthogonal_projection_line", "ask_length"),
        "REGISTERED_DECOMPOSITION")
    add("PE5", "perpendicular (tetrahedron, apex A over right base OBC)", tetra(notation="A.OBC", goals=[("q1", "distance",
        {"point": "O", "plane": ["A", "B", "C"]}, "Tính khoảng cách từ O đến mặt phẳng (ABC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(T_["O"], T_["A"], T_["B"], T_["C"]))}), "T; same solid, other apex reading")
    add("PE6", "perpendicular (tetrahedron volume)", tetra(goals=[("q1", "volume", {"solid_id": "s1"}, "Tính thể tích khối tứ diện OABC")]),
        ("SERVED", {"q1": ("vol", O.volume_from_interior_point([T_["O"], T_["A"], T_["B"], T_["C"]],
                                                                 [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]) ** 2)}),
        "T; oracle interior-point decomposition (V = OA·OB·OC/6 = 1), compared as V²")
    # Y: pyramid S.ABC, base right at A (AB = 3, AC = 4), SA = SB = SC = 13/2 ⇒ apex over the circumcenter mid(BC), h = 6.
    Y = {"A": V(0, 0, 0), "B": V(3, 0, 0), "C": V(0, 4, 0), "S": V(F(3, 2), 2, 6)}
    assert all(O.distance_sq_points(Y["S"], Y[x]) == F(169, 4) for x in "ABC")
    add("PY1", "pyramid apex fixed by three lateral edges", _three_edges("13/2", ("q1", "distance",
        {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)")),
        ("SERVED", {"q1": ("len", d2_pt_plane(Y["A"], Y["S"], Y["B"], Y["C"]))}), "Y frame (asserted SA² = SB² = SC² = 169/4)")
    add("PY2", "pyramid apex fixed by three lateral edges (height)", _three_edges("13/2", ("q1", "distance",
        {"point": "S", "plane": ["A", "B", "C"]}, "Tính khoảng cách từ S đến mặt phẳng (ABC)")),
        ("SERVED", {"q1": ("len", d2_pt_plane(Y["S"], Y["A"], Y["B"], Y["C"]))}), "Y frame; h = 6")
    # parallelism
    add("PA1", "parallel line-plane distance", pyramid("2", "2", goals=[("q1", "distance", {"line": ["A", "D"],
        "plane": ["S", "B", "C"]}, "Tính khoảng cách giữa đường thẳng AD và mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(P["A"], P["S"], P["B"], P["C"]))}), "P2; AD ∥ (SBC)")
    add("PA2", "parallel skew lines (AB ∥ (SCD))", pyramid("2", "2", goals=[("q1", "distance", {"line1": ["A", "B"],
        "line2": ["S", "C"]}, "Tính khoảng cách giữa hai đường thẳng AB và SC")]),
        ("SERVED", {"q1": ("len", d2_skew(P["A"], P["B"], P["S"], P["C"]))}), "P2")
    add("PA3", "parallel line-plane (line through described point)", pyramid("2", "2",
        extra_text="Gọi M là trung điểm của SB. ", extra_prem=[mp("M", "SB", "Gọi M là trung điểm của SB")],
        described=[dmid("n1", "SC", "trung điểm của SC")],
        goals=[("q1", "distance", {"line": ["M", "@n1"], "plane": ["A", "B", "C", "D"]},
                "Tính khoảng cách giữa đường thẳng nối M với trung điểm của SC và mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(mid(P["S"], P["B"]), P["A"], P["B"], P["C"]))}), "P2; MN ∥ BC ⊂ (ABCD)",
        ("midpoint", "ask_distance_line_plane"), "DESCRIPTOR_COMPOSITION")
    # sections
    add("SE1", "section ∥ base", pyramid("2", "2", extra_text="Gọi M là trung điểm của SA. Gọi (P) là mặt phẳng đi qua M và song song với mặt phẳng (ABCD). ",
        extra_prem=[mp("M", "SA", "Gọi M là trung điểm của SA")],
        sections=[{"section_id": "sec", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "through_point_parallel_plane",
                   "through_point": "M", "parallel_plane": ["A", "B", "C"], "stated_intersections": [],
                   "quote": "Gọi (P) là mặt phẳng đi qua M và song song với mặt phẳng (ABCD)"}],
        goals=[("q1", "area", {"section_id": "sec"}, "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)")]),
        ("SERVED", {"q1": ("area", area2(V(0, 0, 1), V(1, 0, 1), V(1, 1, 1), V(0, 1, 1)))}), "P2; square of side 1 at z = 1",
        ("plane_through_point_parallel", "ask_section_area"))
    sc = [V(0, 0, 0), V(1, 0, 1), V(F(2, 3), F(2, 3), F(4, 3)), V(0, 1, 1)]
    plane_ac = (V(0, 0, 0), V(1, 1, -1))
    faces_p = [[0, 1, 2, 3], [4, 0, 1], [4, 1, 2], [4, 2, 3], [4, 3, 0]]
    verts_p = [P["A"], P["B"], P["C"], P["D"], P["S"]]
    assert O.verify_section(verts_p, faces_p, plane_ac, sc) == []
    add("SE2", "section ⊥ line through vertex", pyramid("2", "2",
        extra_text="Gọi (P) là mặt phẳng đi qua A và vuông góc với SC. ",
        sections=[{"section_id": "sec", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "through_point_perpendicular_line",
                   "through_point": "A", "perpendicular_line": ["S", "C"], "stated_intersections": [],
                   "quote": "Gọi (P) là mặt phẳng đi qua A và vuông góc với SC"}],
        goals=[("q1", "area", {"section_id": "sec"}, "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)")]),
        ("SERVED", {"q1": ("area", area2(*sc))}), "P2; plane x+y−z=0, vertices A,(1,0,1),(2/3,2/3,4/3),(0,1,1) "
        "verified by oracle.verify_section", ("plane_through_point_perpendicular", "ask_section_area"))
    add("SE3", "section by three midpoints (constrained)", pyramid("2", "2",
        extra_text="Gọi M, N, P lần lượt là trung điểm của SA, SB, SC. Mặt phẳng (Q) đi qua M, N, P. ",
        extra_prem=[mp("M", "SA", "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC"),
                    mp("N", "SB", "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC"),
                    mp("P", "SC", "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC")],
        sections=[{"section_id": "sec", "plane_name": "Q", "target_solid_id": "s1", "plane_kind": "constrained",
                   "constraints": [{"kind": "contains_points", "operands": ["M", "N", "P"]}], "stated_intersections": [],
                   "quote": "Mặt phẳng (Q) đi qua M, N, P"}],
        goals=[("q1", "area", {"section_id": "sec"}, "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (Q)")]),
        ("SERVED", {"q1": ("area", area2(V(0, 0, 1), V(1, 0, 1), V(1, 1, 1), V(0, 1, 1)))}), "P2; MNP ∥ base at z = 1, square of side 1",
        ("plane_through_points", "ask_section_area"))
    add("SE4", "section constrained ⊥ plane (A3 regression)", pyramid("2", "2",
        extra_text="Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. Mặt phẳng (P) đi qua M, N và vuông góc với (SBC). ",
        extra_prem=[mp("M", "AB", "Gọi M là trung điểm của AB"), mp("N", "CD", "Gọi N là trung điểm của CD")],
        sections=[{"section_id": "sec", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "constrained",
                   "constraints": [{"kind": "contains_points", "operands": ["M", "N"]},
                                   {"kind": "perpendicular_to_plane", "operands": ["S", "B", "C"]}],
                   "stated_intersections": [], "quote": "Mặt phẳng (P) đi qua M, N và vuông góc với (SBC)"}],
        goals=[("q1", "area", {"section_id": "sec"}, "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó")]),
        ("SERVED", {"q1": ("area", area2(V(1, 0, 0), V(F(3, 2), 0, F(1, 2)), V(F(3, 2), F(3, 2), F(1, 2)), V(1, 2, 0)))}),
        "P2; (P): x − z = 1 (contains MN and the normal (1,0,1) of (SBC)); cuts SB at (3/2,0,1/2), SC at (3/2,3/2,1/2): "
        "trapezoid MPQN, area 7√2/8",
        ("orthogonal_projection", "plane_through_points", "ask_section_area"), "GOAL_DRIVEN_DISCOVERY")
    # points defined by relations
    add("RE1", "orthocenter (B1 regression)", pyramid("2", "2", described=[{"described_id": "h1", "kind": "orthocenter",
        "polygon": ["S", "B", "C"], "quote": "trực tâm của tam giác SBC"}],
        goals=[("q1", "distance", {"segment": ["@h1", "A"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBC với A")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(P["B"], P["A"]))}), "P2; SBC right at B ⇒ orthocenter = B",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    add("RE2", "circumcenter (B2 regression)", pyramid("2", "2", described=[{"described_id": "o1", "kind": "circumcenter",
        "polygon": ["S", "B", "C"], "quote": "tâm đường tròn ngoại tiếp tam giác SBC"}],
        goals=[("q1", "distance", {"segment": ["@o1", "A"]}, "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBC với A")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(mid(P["S"], P["C"]), P["A"]))}), "P2; SBC right at B ⇒ circumcenter = mid(SC)",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    add("RE3", "orthocenter of tetrahedron face ABC", _tetra_described(
        {"described_id": "h1", "kind": "orthocenter", "polygon": ["A", "B", "C"], "quote": "trực tâm của tam giác ABC"},
        ("q1", "distance", {"segment": ["@h1", "O"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác ABC với O")),
        ("SERVED", {"q1": ("len", d2_pt_plane(T_["O"], T_["A"], T_["B"], T_["C"]))}),
        "T; for pairwise ⊥ OA,OB,OC the orthocenter of ABC is the foot of O on (ABC)",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    add("RE4", "projection onto line (described) to plane", pyramid("2", "2",
        described=[{"described_id": "h1", "kind": "orthogonal_projection_line", "point": "A", "line": ["S", "B"],
                    "quote": "hình chiếu vuông góc của A lên SB"}],
        goals=[("q1", "distance", {"point": "@h1", "plane": ["S", "C", "D"]},
                "Tính khoảng cách từ hình chiếu vuông góc của A lên SB đến mặt phẳng (SCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(foot_line(P["A"], P["S"], P["B"]), P["S"], P["C"], P["D"]))}), "P2; h = (1,0,1)",
        ("orthogonal_projection_line", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    add("RE5", "orthocenter to plane", pyramid("2", "2", described=[{"described_id": "h1", "kind": "orthocenter",
        "polygon": ["S", "B", "C"], "quote": "trực tâm của tam giác SBC"}],
        goals=[("q1", "distance", {"point": "@h1", "plane": ["S", "A", "D"]}, "Tính khoảng cách từ trực tâm của tam giác SBC đến mặt phẳng (SAD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(P["B"], P["S"], P["A"], P["D"]))}), "P2; orthocenter(SBC) = B",
        ("orthogonal_projection_line", "intersect_line_line", "ask_distance_point_plane"), "GOAL_DRIVEN_DISCOVERY")
    add("RE6", "circumcenter to line (definition + foot)", pyramid("2", "2", described=[{"described_id": "o1",
        "kind": "circumcenter", "polygon": ["S", "B", "C"], "quote": "tâm đường tròn ngoại tiếp tam giác SBC"}],
        goals=[("q1", "distance", {"point": "@o1", "line": ["A", "D"]}, "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác SBC đến đường thẳng AD")]),
        ("SERVED", {"q1": ("len", d2_pt_line(mid(P["S"], P["C"]), P["A"], P["D"]))}), "P2; circumcenter(SBC) = mid(SC) = (1,1,1)",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    g_sbd = cen(P["S"], P["B"], P["D"])
    add("RE7", "circumcenter of an equilateral face", pyramid("2", "2", described=[{"described_id": "o1", "kind": "circumcenter",
        "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"}],
        goals=[("q1", "distance", {"segment": ["@o1", "A"]}, "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBD với A")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(g_sbd, P["A"]))}), "P2; SB = SD = BD = 2√2 ⇒ circumcenter = centroid",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    add("RE8", "orthocenter of an equilateral face to base", pyramid("2", "2", described=[{"described_id": "h1", "kind": "orthocenter",
        "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}],
        goals=[("q1", "distance", {"point": "@h1", "plane": ["A", "B", "C", "D"]}, "Tính khoảng cách từ trực tâm của tam giác SBD đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(g_sbd, P["A"], P["B"], P["C"]))}), "P2; orthocenter = centroid of SBD",
        ("orthogonal_projection_line", "intersect_line_line", "ask_distance_point_plane"), "GOAL_DRIVEN_DISCOVERY")
    add("RE9", "described line–plane intersection", pyramid("2", "2",
        extra_text="Gọi M, N lần lượt là trung điểm của SB, SD. ",
        extra_prem=[mp("M", "SB", "Gọi M, N lần lượt là trung điểm của SB, SD"), mp("N", "SD", "Gọi M, N lần lượt là trung điểm của SB, SD")],
        described=[{"described_id": "i1", "kind": "intersect_line_plane", "line": ["M", "N"], "plane": ["S", "A", "C"],
                    "quote": "giao điểm của MN và mặt phẳng (SAC)"}],
        goals=[("q1", "distance", {"point": "@i1", "plane": ["A", "B", "C", "D"]}, "Tính khoảng cách từ giao điểm của MN và mặt phẳng (SAC) đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", F(1))}), "P2; M=(1,0,1), N=(0,1,1), (SAC): x=y ⇒ I=(1/2,1/2,1), d=1 (hand)",
        ("intersect_line_plane", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    hc = foot_line(P["A"], P["S"], P["C"])
    add("MG7", "goal-only foot reused by a described-point goal", pyramid("2", "2",
        described=[{"described_id": "h1", "kind": "orthogonal_projection_line", "point": "A", "line": ["S", "C"],
                    "quote": "hình chiếu vuông góc của A lên SC"}],
        goals=[("q1", "distance", {"point": "A", "line": ["S", "C"]}, "Tính khoảng cách từ A đến đường thẳng SC"),
               ("q2", "distance", {"segment": ["@h1", "S"]}, "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của A lên SC với S")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P["A"], P["S"], P["C"])), "q2": ("len", O.distance_sq_points(hc, P["S"]))}),
        "P2; the foot of A on SC is ONE construction for both goals", ("orthogonal_projection_line", "ask_length"),
        "REGISTERED_DECOMPOSITION")
    add("MG8", "orthocenter and circumcenter of one triangle", pyramid("2", "2", described=[
        {"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
        {"described_id": "o1", "kind": "circumcenter", "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"}],
        goals=[("q1", "distance", {"segment": ["@h1", "A"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với A"),
               ("q2", "distance", {"segment": ["@o1", "C"]}, "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBD với C")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(g_sbd, P["A"])), "q2": ("len", O.distance_sq_points(g_sbd, P["C"]))}),
        "P2; both = centroid of the equilateral SBD", ("orthogonal_projection_line", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")
    add("RE10", "projection of a defined point (nested definition)", pyramid("2", "2", described=[
        {"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
        {"described_id": "k1", "kind": "orthogonal_projection", "point": "@h1", "plane": ["A", "B", "C", "D"],
         "quote": "hình chiếu vuông góc của trực tâm của tam giác SBD lên mặt phẳng (ABCD)"}],
        goals=[("q1", "distance", {"point": "@k1", "plane": ["S", "A", "B"]},
                "Tính khoảng cách từ hình chiếu vuông góc của trực tâm của tam giác SBD lên mặt phẳng (ABCD) đến mặt phẳng (SAB)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(foot_plane(g_sbd, P["A"], P["B"], P["C"]), P["S"], P["A"], P["B"]))}),
        "P2; orthocenter(SBD) = (2/3,2/3,2/3), its projection (2/3,2/3,0), (SAB): y = 0",
        ("orthogonal_projection_line", "intersect_line_line", "orthogonal_projection", "ask_distance_point_plane"),
        "GOAL_DRIVEN_DISCOVERY")
    add("MG9", "three property-defined points in one problem", pyramid("2", "2", described=[
        {"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
        {"described_id": "o1", "kind": "circumcenter", "polygon": ["S", "B", "C"], "quote": "tâm đường tròn ngoại tiếp tam giác SBC"},
        {"described_id": "h2", "kind": "orthocenter", "polygon": ["S", "C", "D"], "quote": "trực tâm của tam giác SCD"}],
        goals=[("q1", "distance", {"segment": ["@h1", "A"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với A"),
               ("q2", "distance", {"segment": ["@o1", "A"]}, "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBC với A"),
               ("q3", "distance", {"segment": ["@h2", "A"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác SCD với A")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(g_sbd, P["A"])),
                    "q2": ("len", O.distance_sq_points(mid(P["S"], P["C"]), P["A"])),
                    "q3": ("len", O.distance_sq_points(P["D"], P["A"]))}),
        "P2; SCD right at D ⇒ orthocenter = D; SBC right at B ⇒ circumcenter = mid(SC)",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"), "GOAL_DRIVEN_DISCOVERY")
    # multi-goal & reuse
    h = foot_line(P["A"], P["S"], P["B"])
    add("MG1", "multi-goal shared described point", pyramid("2", "2",
        described=[{"described_id": "h1", "kind": "orthogonal_projection_line", "point": "A", "line": ["S", "B"],
                    "quote": "hình chiếu vuông góc của A lên SB"}],
        goals=[("q1", "distance", {"segment": ["@h1", "S"]}, "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của A lên SB với S"),
               ("q2", "distance", {"point": "@h1", "plane": ["A", "B", "C", "D"]},
                "Tính khoảng cách từ hình chiếu vuông góc của A lên SB đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(h, P["S"])), "q2": ("len", d2_pt_plane(h, P["A"], P["B"], P["C"]))}),
        "P2; h = (1,0,1)", ("orthogonal_projection_line", "ask_length", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")
    add("MG2", "multi-goal three quantities", pyramid("2", "2", goals=[
        ("q1", "distance", {"point": "A", "line": ["S", "C"]}, "Tính khoảng cách từ A đến đường thẳng SC"),
        ("q2", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "Tính góc giữa SC và mặt phẳng (ABCD)"),
        ("q3", "distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P["A"], P["S"], P["C"])),
                    "q2": ("cos2", cos2_line_plane(P["S"], P["C"], P["A"], P["B"], P["C"])),
                    "q3": ("len", d2_pt_plane(P["A"], P["S"], P["B"], P["C"]))}), "P2",
        ("orthogonal_projection_line", "ask_length", "ask_angle_line_plane", "ask_distance_point_plane"), "REGISTERED_DECOMPOSITION")
    add("MG3", "reuse of a source-named foot", pyramid("2", "2", extra_text="Gọi H là hình chiếu vuông góc của A lên SB. ",
        extra_prem=[{"kind": "orthogonal_projection_line", "args": {"point": "A", "image": "H", "line": ["S", "B"]},
                     "quote": "Gọi H là hình chiếu vuông góc của A lên SB", "solid_id": "s1"}],
        goals=[("q1", "distance", {"point": "A", "line": ["S", "B"]}, "Tính khoảng cách từ A đến đường thẳng SB"),
               ("q2", "distance", {"point": "H", "plane": ["A", "B", "C", "D"]}, "Tính khoảng cách từ H đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_line(P["A"], P["S"], P["B"])), "q2": ("len", d2_pt_plane(h, P["A"], P["B"], P["C"]))}),
        "P2; H = (1,0,1); the decomposition foot must reuse H", ("orthogonal_projection_line", "ask_length"),
        "SOURCE_EXPLICIT_SEQUENCE")
    add("MG4", "multi-goal two described points sharing an inner point", pyramid("2", "2",
        described=[dmid("m1", "SC", "trung điểm của SC"),
                   {"described_id": "h1", "kind": "orthogonal_projection", "point": "@m1", "plane": ["A", "B", "C", "D"],
                    "quote": "hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD)"}],
        goals=[("q1", "distance", {"point": "@m1", "plane": ["S", "A", "B"]}, "Tính khoảng cách từ trung điểm của SC đến mặt phẳng (SAB)"),
               ("q2", "distance", {"segment": ["@h1", "S"]},
                "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD) với S")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(mid(P["S"], P["C"]), P["S"], P["A"], P["B"])),
                    "q2": ("len", O.distance_sq_points(V(1, 1, 0), P["S"]))}), "P2; m = (1,1,1), h = (1,1,0)",
        ("midpoint", "orthogonal_projection", "ask_distance_point_plane", "ask_length"), "DESCRIPTOR_COMPOSITION")
    add("MG5", "distance between two described points", pyramid("2", "2",
        described=[dmid("m1", "SB", "trung điểm của SB"), dmid("n1", "CD", "trung điểm của CD")],
        goals=[("q1", "distance", {"segment": ["@m1", "@n1"]}, "Tính độ dài đoạn thẳng nối trung điểm của SB với trung điểm của CD")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(mid(P["S"], P["B"]), mid(P["C"], P["D"])))}), "P2",
        ("midpoint", "ask_length"), "DESCRIPTOR_COMPOSITION")
    add("MG6", "triangle area with a described vertex", pyramid("2", "2", described=[dmid("m1", "SC", "trung điểm của SC")],
        goals=[("q1", "area", {"polygon": ["@m1", "A", "B"]}, "Tính diện tích tam giác tạo bởi trung điểm của SC, A và B")]),
        ("SERVED", {"q1": ("area", area2(mid(P["S"], P["C"]), P["A"], P["B"]))}), "P2", ("midpoint", "ask_area"),
        "DESCRIPTOR_COMPOSITION")
    # negatives / clarification
    add("N1", "missing dimension", _missing_height(),
        ("REFUSED", "refusal", {"MISSING_DIMENSION", "UNDERDETERMINED_POINT", "FACT_INCOMPLETE", "MISSING_DATA"}),
        "SA length not given: no unique answer")
    add("N2", "contradictory dimensions", pyramid("2", "2", extra_text="AB = 3. ",
        extra_prem=[{"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3", "solid_id": "s1"}],
        goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)")]),
        ("REFUSED", "refusal", {"INCONSISTENT_FACTS", "INCONSISTENT_LENGTH", "CONTRADICTORY_DATA"}), "square side 2 vs AB = 3")
    n3 = pyramid("2", "2", goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)")])
    n3[1]["premises"][2]["quote"] = "SA = 7"
    add("N3", "quote not in source", n3, ("REFUSED", "refusal", {"QUOTE_NOT_IN_SOURCE", "UNGROUNDED_VALUE"}), "fabricated quote")
    add("N4", "ambiguous wording (clarification)", pyramid("2", "2", goals=[("q1", "angle", {"line": ["S", "B"], "plane": ["A", "B", "C", "D"]},
        "Tính góc giữa SB và mặt phẳng")], unresolved=[{"unresolved_id": "u1", "kind": "missing_operand",
        "missing_roles": ["target_line_or_plane"], "quote": "Tính góc giữa SB và mặt phẳng"}]),
        ("REFUSED", "clarification", {"AMBIGUOUS_FACT"}), "the plane is not named")
    add("N5", "described centroid of a collinear triple", pyramid("2", "2", extra_text="Gọi M là trung điểm của AB. ",
        extra_prem=[mp("M", "AB", "Gọi M là trung điểm của AB")],
        described=[{"described_id": "g1", "kind": "centroid", "polygon": ["A", "M", "B"], "quote": "trọng tâm của tam giác AMB"}],
        goals=[("q1", "distance", {"point": "@g1", "plane": ["S", "C", "D"]}, "Tính khoảng cách từ trọng tâm của tam giác AMB đến mặt phẳng (SCD)")]),
        ("REFUSED", "refusal", {"COLLINEAR_POINTS", "DEGENERATE_POINTS", "DEGENERATE_TRIANGLE", "DEGENERATE_POLYGON"}),
        "A, M, B collinear: no triangle")
    add("N6", "unknown vertex in description", pyramid("2", "2", described=[dmid("m1", "SX", "trung điểm của SX")],
        goals=[("q1", "distance", {"point": "@m1", "plane": ["A", "B", "C", "D"]}, "Tính khoảng cách từ trung điểm của SX đến mặt phẳng (ABCD)")]),
        ("REFUSED", "refusal", None), "X is not a vertex")
    add("N7", "orthocenter of a degenerate (collinear) triangle", pyramid("2", "2", extra_text="Gọi M là trung điểm của AB. ",
        extra_prem=[mp("M", "AB", "Gọi M là trung điểm của AB")],
        described=[{"described_id": "h1", "kind": "orthocenter", "polygon": ["A", "M", "B"], "quote": "trực tâm của tam giác AMB"}],
        goals=[("q1", "distance", {"segment": ["@h1", "S"]}, "Tính độ dài đoạn thẳng nối trực tâm của tam giác AMB với S")]),
        ("REFUSED", "refusal", None), "A, M, B collinear: orthocenter undefined")
    n8 = tetra(goals=[("q1", "distance", {"point": "O", "plane": ["A", "B", "C"]}, "Tính khoảng cách từ O đến mặt phẳng (ABC)")])
    n8 = (n8[0].replace("OC = 3. ", "OC = 3, AB = 3. "), n8[1])
    n8[1]["problem_text"] = n8[0]
    n8[1]["premises"].append({"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3",
                              "solid_id": "s1"})
    add("N8", "tetrahedron: stated AB contradicts OA ⊥ OB", n8,
        ("REFUSED", "refusal", {"INCONSISTENT_FACTS"}), "OA² + OB² = 5 ≠ AB² = 9")
    n9 = tetra(goals=[("q1", "distance", {"point": "O", "plane": ["A", "B", "C"]}, "Tính khoảng cách từ O đến mặt phẳng (ABC)")])
    n9 = (n9[0].replace(", OC = 3. ", ". "), n9[1])
    n9[1]["problem_text"] = n9[0]
    n9[1]["premises"] = [p for p in n9[1]["premises"] if p["quote"] != "OC = 3"]
    add("N9", "tetrahedron: OC not given", n9, ("REFUSED", "refusal", {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"}),
        "OC free: no unique solid")
    add("N10", "three lateral edges too short for the base", _three_edges("2", ("q1", "distance",
        {"point": "S", "plane": ["A", "B", "C"]}, "Tính khoảng cách từ S đến mặt phẳng (ABC)")),
        ("REFUSED", "refusal", {"INCONSISTENT_FACTS"}), "circumradius of ABC is 5/2 > SA = 2: no apex")
    return C


def _three_edges(edge, goal):
    text = (f"Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và SA = SB = SC = {edge}. ")
    q = f"SA = SB = SC = {edge}"
    prem = [
        {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4", "solid_id": "s1"},
        *({"kind": "segment_length", "args": {"segment": ["S", x], "value": edge}, "quote": q, "solid_id": "s1"} for x in "ABC"),
    ]
    return _payload("Cho hình chóp S.ABC", "pyramid", "S.ABC", text, prem, [goal], (), (), ())


def _tetra_described(desc, goal):
    t, p = tetra(goals=[goal])
    p["described_points"] = [desc]
    return t, p


def _missing_height():
    t, p = pyramid("2", "2", goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)")])
    t = t.replace(" và SA = 2", "")
    p["problem_text"] = t
    p["premises"] = p["premises"][:2]
    return t, p


#: Out-of-scope classes: recorded, not run (no representation in TypedFactNext /2, or outside the thesis scope).
OUT_OF_SCOPE = [
    {"class": "plane operand given by a described point", "why": "GOAL_OPERAND_SHAPES['plane'] is refs3 of labels; a described "
     "ref may stand only in point slots (typed_fact_next.DESCRIBED_GOAL_KEYS) — contract change, not a planner gap"},
    {"class": "proof goals (Chứng minh ...)", "why": "MathGoalSpec.kind ∈ {volume_ratio, residual_volume, measurement}; no "
     "prove goal in /2"},
    {"class": "dragging / dynamic loci", "why": "ARCHITECTURE_MAP invariant #31 (frame k ⇔ trace[k]); interaction is select+scrub"},
    {"class": "nesting deeper than MAX_DESCRIBED_DEPTH = 2", "why": "contract bound (typed_fact_next.MAX_DESCRIBED_DEPTH)"},
]


# ── execution ────────────────────────────────────────────────────────────────────────────────────────────────────────

_RAD = re.compile(r"^(?P<a>\d+)?(?:√(?P<r>\d+))?(?:/(?P<d>\d+))?$")


def coef_square(coef: str) -> F | None:
    m = _RAD.match((coef or "").strip())
    if not m or not (m["a"] or m["r"]):
        return None
    a, r, d = F(int(m["a"] or 1)), int(m["r"] or 1), int(m["d"] or 1)
    return a * a * r / (d * d)


def classify(case, status, code, answers, clar, scene_issues):
    exp = case["expect"]
    if status not in ("SERVED", "REFUSED"):
        return "ADAPTER_OR_SCENE3D_ERROR"
    if exp[0] == "SERVED":
        if status == "SERVED":
            if scene_issues:
                return "ADAPTER_OR_SCENE3D_ERROR"
            for g, (meas, want) in exp[1].items():
                if want is None:
                    continue
                got = answers.get(g)
                val = F(got) if meas == "cos2" and got and "√" not in got else coef_square(got) if meas != "cos2" else None
                if val is None or val != want:
                    return "WRONG_SERVED"
            return "EXACT_SERVED"
        if code == "PLAN_TOO_LARGE":
            return "SEARCH_BUDGET_EXCEEDED"
        if code in ("ADAPTER_INTERNAL_ERROR", "ROUTE_INTERNAL_ERROR"):
            return "ADAPTER_OR_SCENE3D_ERROR"
        if case["primitives"]:
            return "NO_PLAN_DESPITE_PRIMITIVES"
        return "FALSE_REFUSAL"
    if status == "SERVED":
        return "WRONG_SERVED"
    group, codes = exp[1], exp[2]
    if group == "clarification":
        return "CORRECT_CLARIFICATION" if code == "AMBIGUOUS_FACT" and clar else "WRONG_REFUSAL_CLASS"
    if codes is None or code in codes:
        return "CORRECT_REFUSAL"
    return "WRONG_REFUSAL_CLASS"


def _stats(vals):
    if not vals:
        return {"p50": "NOT_MEASURED", "p95": "NOT_MEASURED", "max": "NOT_MEASURED", "n": 0}
    s = sorted(vals)
    p95 = s[min(len(s) - 1, max(0, -(-95 * len(s) // 100) - 1))]
    return {"p50": round(statistics.median(s), 3), "p95": round(p95, 3), "max": round(s[-1], 3), "n": len(s)}


def run_matrix() -> dict:
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor
    from app.simulation.geometry_functions import TuChoi, engine, planner, typed_fact_next as TN
    from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
    from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

    policy = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    rows, pl_ms, k_ms, cold_ms, warm_ms = [], [], [], [], []
    for c in build_cases():
        text, payload = c["text"], c["payload"]
        plan = None
        t_plan = t_kern = None
        try:
            bridged = bridge_v2(TN._parse(TN.TypedFactNextPayloadV2, payload))
            t0 = time.perf_counter()
            try:
                plan = planner.lap_ke_hoach(bridged, text)
            except TuChoi:
                plan = None
            t_plan = (time.perf_counter() - t0) * 1000
            if plan is not None:
                doc = tuple(q for g in (*plan.goals, *plan.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
                t1 = time.perf_counter()
                try:
                    engine.dung_tu_loi_goi(text, {"calls": plan.calls, "named_planes": plan.named_planes},
                                           tuple(plan.auxiliary), doc)
                except TuChoi:
                    pass
                t_kern = (time.perf_counter() - t1) * 1000
        except Exception:      # bridge/contract refusal: the route below reports it
            pass
        tracemalloc.start()
        t2 = time.perf_counter()
        out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=policy)
        t_cold = (time.perf_counter() - t2) * 1000
        peak = tracemalloc.get_traced_memory()[1] / 1024
        tracemalloc.stop()
        ws = []
        for _ in range(3):
            t3 = time.perf_counter()
            run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=policy)
            ws.append((time.perf_counter() - t3) * 1000)
        route, env = out.response.get("route_d") or {}, out.response.get("envelope") or {}
        status = route.get("status") or out.response.get("status")
        code = env.get("reason_code") or out.response.get("reason_code")
        answers = {k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()} if status == "SERVED" else {}
        clar = bool((route.get("refusal") or {}).get("clarification") or env.get("clarification")
                    or (route.get("refusal") or {}).get("clarifications"))
        scene = env.get("scene3d")
        issues = validate_construction_continuity(scene) if (status == "SERVED" and scene) else []
        if status == "SERVED" and not scene:
            issues = ["NO_SCENE3D"]
        tel = (route.get("planner") or {}).get("search_telemetry") or {}
        cls = classify(c, status, code, answers, clar, issues)
        if t_plan is not None:
            pl_ms.append(t_plan)
        if t_kern is not None:
            k_ms.append(t_kern)
        cold_ms.append(t_cold)
        warm_ms.append(statistics.median(ws))
        exp = c["expect"]
        rows.append({
            "id": c["id"], "family": c["family"], "level_expected": c["level"], "outcome": cls,
            "status": status, "reason_code": code,
            "answers": answers,
            "expected": ({g: [m, str(v) if v is not None else "HAND_NOTE"] for g, (m, v) in exp[1].items()}
                         if exp[0] == "SERVED" else {"group": exp[1], "codes": sorted(exp[2]) if exp[2] else "ANY_TYPED"}),
            "oracle": c["oracle"], "primitives": c["primitives"],
            "classification": tel.get("classification", "UNKNOWN") if tel else "UNKNOWN",
            "explored_states": tel.get("explored_states", "UNKNOWN"),
            "candidate_evaluations": tel.get("candidate_evaluations", "UNKNOWN"),
            "pruned_nodes": tel.get("pruned_nodes", "UNKNOWN"),
            "search_depth": tel.get("search_depth", "UNKNOWN"),
            "reused_intermediates": tel.get("reused_intermediates", "UNKNOWN"),
            "plan_cost": tel.get("plan_cost", "UNKNOWN"),
            "selected_plan": tel.get("selected_plan", []),
            "search_generated_steps": len(tel.get("search_generated_steps") or []) if tel else "UNKNOWN",
            "scene_issues": issues[:3],
            "planner_cpu_ms": round(t_plan, 3) if t_plan is not None else "NOT_MEASURED",
            "kernel_cpu_ms": round(t_kern, 3) if t_kern is not None else "NOT_MEASURED",
            "route_cold_ms": round(t_cold, 3), "route_warm_ms": round(statistics.median(ws), 3),
            "peak_memory_kib": round(peak, 2),
        })
    counts = {}
    for r in rows:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    num = [r for r in rows if isinstance(r["explored_states"], int)]
    return {
        "schema": "hybrid-reasoning-matrix/1",
        "measurement_class": "OFFLINE_DEVELOPMENT_MATRIX", "held_out_claim": "NONE", "evaluator_independence": "NONE",
        "live_calls": 0,
        "git_head": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "case_count": len(rows), "outcome_counts": dict(sorted(counts.items())),
        "out_of_scope_not_run": OUT_OF_SCOPE,
        "performance": {
            "planner_cpu_ms": _stats(pl_ms), "kernel_cpu_ms": _stats(k_ms),
            "route_cold_ms": _stats(cold_ms), "route_warm_ms": _stats(warm_ms),
            "peak_memory_kib_max": round(max(r["peak_memory_kib"] for r in rows), 2),
            "explored_states_max": max((r["explored_states"] for r in num), default="UNKNOWN"),
            "candidate_evaluations_max": max((r["candidate_evaluations"] for r in num), default="UNKNOWN"),
            "pruned_nodes_max": max((r["pruned_nodes"] for r in num if isinstance(r["pruned_nodes"], int)), default="UNKNOWN"),
            "search_depth_max": max((r["search_depth"] for r in num if isinstance(r["search_depth"], int)), default="UNKNOWN"),
            "reused_intermediates_total": sum(r["reused_intermediates"] for r in num if isinstance(r["reused_intermediates"], int)),
            "search_exhausted_cases": sum(r["outcome"] == "SEARCH_BUDGET_EXCEEDED" for r in rows),
            "note": "cold = first run_hybrid_offline in this process for that case (module caches already warm after the "
                    "first case); warm = median of 3 repeats. Planner/kernel CPU measured outside the route.",
        },
        "cases": rows,
    }


def render() -> str:
    out = []
    for label in ("before", "after"):
        p = RUN / "results" / f"matrix_{label}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        out.append(f"## Matrix `{label}` (HEAD `{d['git_head'][:12]}`, {d['case_count']} cases)\n")
        out.append("| outcome | count |\n|---|---:|")
        out += [f"| `{k}` | {v} |" for k, v in d["outcome_counts"].items()]
        out.append("\n| case | family | outcome | status / code | answers | classification | states | cands | pruned | depth | reuse |")
        out.append("|---|---|---|---|---|---|---:|---:|---:|---:|---:|")
        for r in d["cases"]:
            out.append(f"| {r['id']} | {r['family']} | `{r['outcome']}` | {r['status']} {r['reason_code'] or ''} | "
                       f"{json.dumps(r['answers'], ensure_ascii=False)} | {r['classification']} | {r['explored_states']} | "
                       f"{r['candidate_evaluations']} | {r['pruned_nodes']} | {r['search_depth']} | {r['reused_intermediates']} |")
        pf = d["performance"]
        out.append("\n| metric | p50 | p95 | max |\n|---|---:|---:|---:|")
        for k in ("planner_cpu_ms", "kernel_cpu_ms", "route_cold_ms", "route_warm_ms"):
            out.append(f"| {k} | {pf[k]['p50']} | {pf[k]['p95']} | {pf[k]['max']} |")
        out.append(f"\npeak memory max {pf['peak_memory_kib_max']} KiB · explored_states max {pf['explored_states_max']} · "
                   f"candidates max {pf['candidate_evaluations_max']} · pruned max {pf['pruned_nodes_max']} · depth max "
                   f"{pf['search_depth_max']} · reuse total {pf['reused_intermediates_total']} · exhausted "
                   f"{pf['search_exhausted_cases']}\n")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    if a.render:
        (RUN / "results" / "matrix_tables.md").write_text(render(), encoding="utf-8")
        print("WROTE", RUN / "results" / "matrix_tables.md")
        return
    res = run_matrix()
    p = RUN / "results" / f"matrix_{a.label}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("WROTE", p, res["outcome_counts"])


if __name__ == "__main__":
    main()
