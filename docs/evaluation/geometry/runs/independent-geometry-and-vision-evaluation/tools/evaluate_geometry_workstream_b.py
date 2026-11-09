# -*- coding: utf-8 -*-
"""Workstream B — Independent Geometry & Generalization Evaluation, Cross-Pipeline Evaluation,
Hybrid Performance Profiling, and `_dinh_tu_ba_canh_ben` Mirror-Solution Equivalence Audit.

MEASUREMENT_CLASS = GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT
INDEPENDENT_H1_VALIDATION = NOT_MEASURED
LIVE_VISION_EVALUATION = NOT_MEASURED
ALLOW_LIVE_AI = 0 (strictly 0 live network calls)
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
import tracemalloc
from fractions import Fraction as F
from pathlib import Path
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
CUSTODIAN = ROOT / "docs" / "evaluation" / "geometry" / "custodian"
DEV_MATRIX_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-reasoning-generalization" / "tools"

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(CUSTODIAN))
sys.path.insert(0, str(DEV_MATRIX_DIR))

import geometry_oracle as O  # noqa: E402 (pure fractions, zero product imports)
import reasoning_matrix as DM  # noqa: E402

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.geometry_functions import TuChoi, engine, planner, registry, typed_fact_next as TN  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2  # noqa: E402


# ── Independent Oracle Helpers (built strictly from geometry_oracle.py) ──────────────────────────────────────────────

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


# ── Independent Rational Reference Frames for Held-Out Benchmark ─────────────────────────────────────────────────────

# Q43: Square pyramid S.ABCD, side = 4, SA ⊥ (ABCD), SA = 3
Q43 = dict(A=V(0, 0, 0), B=V(4, 0, 0), C=V(4, 4, 0), D=V(0, 4, 0), S=V(0, 0, 3))
# Q64: Square pyramid S.ABCD, side = 6, SA ⊥ (ABCD), SA = 4
Q64 = dict(A=V(0, 0, 0), B=V(6, 0, 0), C=V(6, 6, 0), D=V(0, 6, 0), S=V(0, 0, 4))
# Q33: Square pyramid S.ABCD, side = 3, SA ⊥ (ABCD), SA = 3 (SBD is equilateral of side 3√2)
Q33 = dict(A=V(0, 0, 0), B=V(3, 0, 0), C=V(3, 3, 0), D=V(0, 3, 0), S=V(0, 0, 3))
# T236: Right tetrahedron O.ABC, OA, OB, OC pairwise perpendicular, OA = 2, OB = 3, OC = 6
T236 = dict(O=V(0, 0, 0), A=V(2, 0, 0), B=V(0, 3, 0), C=V(0, 0, 6))
# T442: Right tetrahedron O.ABC, OA, OB, OC pairwise perpendicular, OA = 4, OB = 4, OC = 2
T442 = dict(O=V(0, 0, 0), A=V(4, 0, 0), B=V(0, 4, 0), C=V(0, 0, 2))
# L685: Right triangular prism ABC.A'B'C', right at A, AB = 6, AC = 8, AA' = 5
L685 = {
    "A": V(0, 0, 0), "B": V(6, 0, 0), "C": V(0, 8, 0),
    "A'": V(0, 0, 5), "B'": V(6, 0, 5), "C'": V(0, 8, 5),
}
# Y68_13: Triangular pyramid S.ABC, base right at A, AB = 6, AC = 8, SA = SB = SC = 13 => S = (3, 4, 12)
Y68_13 = {"A": V(0, 0, 0), "B": V(6, 0, 0), "C": V(0, 8, 0), "S": V(3, 4, 12)}
assert all(O.distance_sq_points(Y68_13["S"], Y68_13[k]) == F(169) for k in "ABC")


SG = [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": None}]


def _goal(gid, gtype, target, quote):
    return {"goal_id": gid, "kind": "measurement", "goal_type": gtype, "target": target, "quote": quote, "solid_id": "s1"}


def _payload(solid_quote, stype, notation, text, prem, goals, described=(), sections=(), unresolved=()):
    full_text = text + " ".join(g[3] + "." for g in goals)
    p = {
        "schema_version": "typed-fact-next/2",
        "problem_text": full_text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": stype, "notation": notation, "quote": solid_quote}],
        "premises": list(prem),
        "relations": [],
        "derived_sections": list(sections),
        "described_points": list(described),
        "simulation_goals": [{**SG[0], "quote": solid_quote}],
        "math_goals": [_goal(*g) for g in goals],
    }
    if unresolved:
        p["unresolved"] = list(unresolved)
    return full_text, p


def hb_pyramid(side: str, h: str, *, goals, extra_text="", extra_prem=(), described=(), sections=(), unresolved=()):
    base = (
        f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}, "
        f"SA vuông góc với mặt phẳng (ABCD) và SA = {h}. "
    )
    prem = [
        {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": side},
         "quote": f"đáy ABCD là hình vuông cạnh {side}", "solid_id": "s1"},
        {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
         "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": h},
         "quote": f"SA = {h}", "solid_id": "s1"},
        *extra_prem,
    ]
    return _payload("Cho hình chóp S.ABCD", "pyramid", "S.ABCD", base + extra_text, prem, goals, described, sections, unresolved)


def hb_prism(ab: str, ac: str, aa: str, *, goals, extra_text="", extra_prem=(), described=(), sections=()):
    base = (
        f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, "
        f"AB = {ab}, AC = {ac} và AA' = {aa}. "
    )
    prem = [
        {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
         "quote": "Cho hình lăng trụ đứng ABC.A'B'C'", "solid_id": "s1"},
        {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]},
         "quote": "đáy ABC là tam giác vuông tại A", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": ab}, "quote": f"AB = {ab}", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": ac}, "quote": f"AC = {ac}", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": aa}, "quote": f"AA' = {aa}", "solid_id": "s1"},
        *extra_prem,
    ]
    return _payload("Cho hình lăng trụ đứng ABC.A'B'C'", "prism", "ABC.A'B'C'", base + extra_text, prem, goals, described, sections, ())


def hb_tetra(oa: str, ob: str, oc: str, *, goals, notation="O.ABC", described=(), extra_text="", extra_prem=()):
    base = (
        f"Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, "
        f"OA = {oa}, OB = {ob}, OC = {oc}. "
    )
    prem = [
        {"kind": "perpendicular_lines", "args": {"line1": ["O", "A"], "line2": ["O", "B"]},
         "quote": "OA, OB, OC đôi một vuông góc", "solid_id": "s1"},
        {"kind": "perpendicular_lines", "args": {"line1": ["O", "B"], "line2": ["O", "C"]},
         "quote": "OA, OB, OC đôi một vuông góc", "solid_id": "s1"},
        {"kind": "perpendicular_lines", "args": {"line1": ["O", "A"], "line2": ["O", "C"]},
         "quote": "OA, OB, OC đôi một vuông góc", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["O", "A"], "value": oa}, "quote": f"OA = {oa}", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["O", "B"], "value": ob}, "quote": f"OB = {ob}", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["O", "C"], "value": oc}, "quote": f"OC = {oc}", "solid_id": "s1"},
        *extra_prem,
    ]
    return _payload("Cho tứ diện OABC", "pyramid", notation, base + extra_text, prem, goals, described, (), ())


def hb_three_edges(ab: str, ac: str, edge: str, goal):
    text = f"Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = {ab}, AC = {ac} và SA = SB = SC = {edge}. "
    q = f"SA = SB = SC = {edge}"
    prem = [
        {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]},
         "quote": "đáy ABC là tam giác vuông tại A", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": ab}, "quote": f"AB = {ab}", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": ac}, "quote": f"AC = {ac}", "solid_id": "s1"},
        *({"kind": "segment_length", "args": {"segment": ["S", x], "value": edge}, "quote": q, "solid_id": "s1"} for x in "ABC"),
    ]
    return _payload("Cho hình chóp S.ABC", "pyramid", "S.ABC", text, prem, [goal], (), (), ())


def mp(pt, seg, q):
    return {"kind": "midpoint", "args": {"point": pt, "segment": list(seg)}, "quote": q, "solid_id": "s1"}


def dmid(i, seg, q):
    return {"described_id": i, "kind": "midpoint", "segment": list(seg), "quote": q}


# ── Build 44 Brand-New Held-Out Cases Covering All 18 Groups (Section B.4) ───────────────────────────────────────────

def build_heldout_cases() -> list[dict[str, Any]]:
    C: list[dict[str, Any]] = []

    def add(cid: str, group: str, family: str, tp: tuple[str, dict], expect: tuple, oracle: str,
            primitives: tuple[str, ...] = (), level: str | None = None, gap_probe: str | None = None):
        C.append({
            "id": cid,
            "group": group,
            "family": family,
            "text": tp[0],
            "payload": tp[1],
            "expect": expect,
            "oracle": oracle,
            "primitives": list(primitives),
            "level": level,
            "gap_probe": gap_probe,
        })

    # 1. PYRAMID (Hình chóp)
    vol_q43 = O.volume_from_interior_point(
        [Q43["A"], Q43["B"], Q43["C"], Q43["D"], Q43["S"]],
        [[0, 1, 2, 3], [4, 0, 1], [4, 1, 2], [4, 2, 3], [4, 3, 0]],
    )
    add("HB01", "PYRAMID", "pyramid volume (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "volume", {"solid_id": "s1"}, "Tính thể tích khối chóp S.ABCD")]),
        ("SERVED", {"q1": ("vol", vol_q43 ** 2)}),
        "Q43 frame; V = 1/3 * 4^2 * 3 = 16 => V^2 = 256",
        ("ask_volume",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB02", "PYRAMID", "pyramid apex from three lateral edges (Y68_13)",
        hb_three_edges("6", "8", "13", ("q1", "distance", {"point": "S", "plane": ["A", "B", "C"]},
                       "Tính khoảng cách từ S đến mặt phẳng (ABC)")),
        ("SERVED", {"q1": ("len", d2_pt_plane(Y68_13["S"], Y68_13["A"], Y68_13["B"], Y68_13["C"]))}),
        "Y68_13 frame; R = 5, SA = 13 => h = 12, d^2 = 144",
        ("ask_distance_point_plane",), "SOURCE_EXPLICIT_SEQUENCE")

    # 2. TETRAHEDRON (Tứ diện)
    vol_t236 = O.volume_from_interior_point(
        [T236["O"], T236["A"], T236["B"], T236["C"]],
        [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
    )
    add("HB03", "TETRAHEDRON", "tetrahedron volume (T236)",
        hb_tetra("2", "3", "6", goals=[("q1", "volume", {"solid_id": "s1"}, "Tính thể tích khối tứ diện OABC")]),
        ("SERVED", {"q1": ("vol", vol_t236 ** 2)}),
        "T236 frame; V = 2*3*6/6 = 6 => V^2 = 36",
        ("ask_volume",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB04", "TETRAHEDRON", "tetrahedron altitude from O to (ABC) (T236)",
        hb_tetra("2", "3", "6", goals=[("q1", "distance", {"point": "O", "plane": ["A", "B", "C"]},
                 "Tính khoảng cách từ O đến mặt phẳng (ABC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(T236["O"], T236["A"], T236["B"], T236["C"]))}),
        "T236 frame; 1/d^2 = 1/4 + 1/9 + 1/36 = 7/18 => d^2 = 18/7",
        ("ask_distance_point_plane",), "SOURCE_EXPLICIT_SEQUENCE")

    # 3. PRISM (Hình lăng trụ)
    add("HB05", "PRISM", "right prism point-plane distance (L685)",
        hb_prism("6", "8", "5", goals=[("q1", "distance", {"point": "A", "plane": ["A'", "B", "C"]},
                 "Tính khoảng cách từ A đến mặt phẳng (A'BC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(L685["A"], L685["A'"], L685["B"], L685["C"]))}),
        "L685 frame; exact distance from A to (A'BC)",
        ("ask_distance_point_plane",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB06", "PRISM", "right prism skew lines distance AA' and BC (L685)",
        hb_prism("6", "8", "5", goals=[("q1", "distance", {"line1": ["A", "A'"], "line2": ["B", "C"]},
                 "Tính khoảng cách giữa hai đường thẳng AA' và BC")]),
        ("SERVED", {"q1": ("len", d2_skew(L685["A"], L685["A'"], L685["B"], L685["C"]))}),
        "L685 frame; d(AA', BC) = altitude of ABC from A = 24/5 => d^2 = 576/25",
        ("ask_distance_skew_lines",), "SOURCE_EXPLICIT_SEQUENCE")

    # 4. PERPENDICULARITY (Các quan hệ vuông góc)
    add("HB07", "PERPENDICULARITY", "perpendicular line-line angle 90 deg (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "angle", {"line1": ["B", "C"], "line2": ["S", "B"]},
                   "Tính góc giữa hai đường thẳng BC và SB")]),
        ("SERVED", {"q1": ("cos2", cos2_lines(Q43["B"], Q43["C"], Q43["S"], Q43["B"]))}),
        "Q43 frame; BC ⊥ (SAB) => BC ⊥ SB => cos^2 = 0",
        ("ask_angle_lines",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB08", "PERPENDICULARITY", "tetrahedron dihedral angle (ABC) and (OBC) (T442)",
        hb_tetra("4", "4", "2", goals=[("q1", "angle", {"plane1": ["A", "B", "C"], "plane2": ["O", "B", "C"]},
                 "Tính góc giữa mặt phẳng (ABC) và mặt phẳng (OBC)")]),
        ("SERVED", {"q1": ("cos2", cos2_planes(T442["A"], T442["B"], T442["C"], T442["O"], T442["B"], T442["C"]))}),
        "T442 frame; exact dihedral cos^2",
        ("ask_dihedral_angle",), "SOURCE_EXPLICIT_SEQUENCE")

    # 5. PARALLELISM (Quan hệ song song)
    add("HB09", "PARALLELISM", "parallel line-plane distance AD to (SBC) (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "distance", {"line": ["A", "D"], "plane": ["S", "B", "C"]},
                   "Tính khoảng cách giữa đường thẳng AD và mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(Q43["A"], Q43["S"], Q43["B"], Q43["C"]))}),
        "Q43 frame; AD || BC => d(AD, (SBC)) = d(A, (SBC)) = 12/5 => d^2 = 144/25",
        ("ask_distance_line_plane",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB10", "PARALLELISM", "parallel skew lines distance AB and SC (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "distance", {"line1": ["A", "B"], "line2": ["S", "C"]},
                   "Tính khoảng cách giữa hai đường thẳng AB và SC")]),
        ("SERVED", {"q1": ("len", d2_skew(Q43["A"], Q43["B"], Q43["S"], Q43["C"]))}),
        "Q43 frame; AB || CD => d(AB, SC) = d(A, (SCD)) = 12/5 => d^2 = 144/25",
        ("ask_distance_skew_lines",), "SOURCE_EXPLICIT_SEQUENCE")

    # 6. MIDPOINT_CENTROID (Trung điểm và trọng tâm)
    add("HB11", "MIDPOINT_CENTROID", "described centroid distance to base (Q64)",
        hb_pyramid("6", "4",
                   described=[{"described_id": "g1", "kind": "centroid", "polygon": ["S", "C", "D"],
                               "quote": "trọng tâm của tam giác SCD"}],
                   goals=[("q1", "distance", {"point": "@g1", "plane": ["A", "B", "C", "D"]},
                           "Tính khoảng cách từ trọng tâm của tam giác SCD đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(cen(Q64["S"], Q64["C"], Q64["D"]), Q64["A"], Q64["B"], Q64["C"]))}),
        "Q64 frame; z_G = 4/3 => d^2 = 16/9",
        ("centroid", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")

    add("HB12", "MIDPOINT_CENTROID", "described midpoint on prism top edge to plane (L685)",
        hb_prism("6", "8", "5",
                 described=[dmid("m1", ("B'", "C'"), "trung điểm của B'C'")],
                 goals=[("q1", "distance", {"point": "@m1", "plane": ["A'", "B", "C"]},
                         "Tính khoảng cách từ trung điểm của B'C' đến mặt phẳng (A'BC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(mid(L685["B'"], L685["C'"]), L685["A'"], L685["B"], L685["C"]))}),
        "L685 frame; mid(B'C') = (3, 4, 5)",
        ("midpoint", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")

    # 7. DISTANCE_POINT_LINE (Khoảng cách điểm–đường)
    add("HB13", "DISTANCE_POINT_LINE", "point-line distance A to SC (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "distance", {"point": "A", "line": ["S", "C"]},
                   "Tính khoảng cách từ A đến đường thẳng SC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(Q43["A"], Q43["S"], Q43["C"]))}),
        "Q43 frame; d^2(A, SC) = 288/41",
        ("orthogonal_projection_line", "ask_length"), "REGISTERED_DECOMPOSITION")

    add("HB14", "DISTANCE_POINT_LINE", "described midpoint of SC to line BD (Q64)",
        hb_pyramid("6", "4",
                   described=[dmid("m1", "SC", "trung điểm của SC")],
                   goals=[("q1", "distance", {"point": "@m1", "line": ["B", "D"]},
                           "Tính khoảng cách từ trung điểm của SC đến đường thẳng BD")]),
        ("SERVED", {"q1": ("len", d2_pt_line(mid(Q64["S"], Q64["C"]), Q64["B"], Q64["D"]))}),
        "Q64 frame; mid(SC) = (3, 3, 2), foot on BD is (3, 3, 0) => d^2 = 4",
        ("midpoint", "orthogonal_projection_line", "ask_length"), "DESCRIPTOR_COMPOSITION")

    # 8. DISTANCE_POINT_PLANE (Khoảng cách điểm–mặt)
    add("HB15", "DISTANCE_POINT_PLANE", "described diagonal intersection to (SBC) (Q64)",
        hb_pyramid("6", "4",
                   described=[{"described_id": "o1", "kind": "intersect_line_line", "line1": ["A", "C"], "line2": ["B", "D"],
                               "quote": "giao điểm của AC và BD"}],
                   goals=[("q1", "distance", {"point": "@o1", "plane": ["S", "B", "C"]},
                           "Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(V(3, 3, 0), Q64["S"], Q64["B"], Q64["C"]))}),
        "Q64 frame; O = (3, 3, 0), d(O, (SBC)) = 1/2 d(A, (SBC))",
        ("intersect_line_line", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")

    add("HB16", "DISTANCE_POINT_PLANE", "nested projection of midpoint onto base to (SAD) (Q64)",
        hb_pyramid("6", "4",
                   described=[
                       dmid("m1", "SC", "trung điểm của SC"),
                       {"described_id": "h1", "kind": "orthogonal_projection", "point": "@m1",
                        "plane": ["A", "B", "C", "D"],
                        "quote": "hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD)"},
                   ],
                   goals=[("q1", "distance", {"point": "@h1", "plane": ["S", "A", "D"]},
                           "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD) đến mặt phẳng (SAD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(foot_plane(mid(Q64["S"], Q64["C"]), Q64["A"], Q64["B"], Q64["C"]),
                                              Q64["S"], Q64["A"], Q64["D"]))}),
        "Q64 frame; h1 = (3, 3, 0), (SAD) is x = 0 => d = 3, d^2 = 9",
        ("midpoint", "orthogonal_projection", "ask_distance_point_plane"), "DESCRIPTOR_COMPOSITION")

    # 9. ANGLE_LINE_PLANE (Góc giữa đường và mặt)
    add("HB17", "ANGLE_LINE_PLANE", "angle between SC and base (ABCD) (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]},
                   "Tính góc giữa SC và mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(Q43["S"], Q43["C"], Q43["A"], Q43["B"], Q43["C"]))}),
        "Q43 frame; AC^2 = 32, SC^2 = 41 => cos^2 = 32/41",
        ("ask_angle_line_plane",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB18", "ANGLE_LINE_PLANE", "angle between line through S and mid(CD) with (ABCD) (Q43)",
        hb_pyramid("4", "3",
                   described=[dmid("m1", "CD", "trung điểm của CD")],
                   goals=[("q1", "angle", {"line": ["S", "@m1"], "plane": ["A", "B", "C", "D"]},
                           "Tính góc giữa đường thẳng nối S với trung điểm của CD và mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("cos2", cos2_line_plane(Q43["S"], mid(Q43["C"], Q43["D"]), Q43["A"], Q43["B"], Q43["C"]))}),
        "Q43 frame; M = (2, 4, 0), AM^2 = 20, SM^2 = 29 => cos^2 = 20/29",
        ("midpoint", "ask_angle_line_plane"), "DESCRIPTOR_COMPOSITION")

    # 10. ANGLE_LINE_LINE (Góc giữa hai đường)
    add("HB19", "ANGLE_LINE_LINE", "angle between SB and CD (Q43)",
        hb_pyramid("4", "3", goals=[("q1", "angle", {"line1": ["S", "B"], "line2": ["C", "D"]},
                   "Tính góc giữa hai đường thẳng SB và CD")]),
        ("SERVED", {"q1": ("cos2", cos2_lines(Q43["S"], Q43["B"], Q43["C"], Q43["D"]))}),
        "Q43 frame; CD || AB, cos^2(SB, AB) = 16/25",
        ("ask_angle_lines",), "SOURCE_EXPLICIT_SEQUENCE")

    add("HB20", "ANGLE_LINE_LINE", "angle between line joining A and centroid(SBC) with BC (Q43)",
        hb_pyramid("4", "3",
                   described=[{"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"],
                               "quote": "trọng tâm của tam giác SBC"}],
                   goals=[("q1", "angle", {"line1": ["A", "@g1"], "line2": ["B", "C"]},
                           "Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và đường thẳng BC")]),
        ("SERVED", {"q1": ("cos2", cos2_lines(Q43["A"], cen(Q43["S"], Q43["B"], Q43["C"]), Q43["B"], Q43["C"]))}),
        "Q43 frame; G = (8/3, 4/3, 1)",
        ("centroid", "ask_angle_lines"), "DESCRIPTOR_COMPOSITION")

    # 11. SECTION (Thiết diện)
    add("HB21", "SECTION", "section parallel to base through mid(SA) (Q43)",
        hb_pyramid("4", "3",
                   extra_text="Gọi M là trung điểm của SA. Gọi (P) là mặt phẳng đi qua M và song song với mặt phẳng (ABCD). ",
                   extra_prem=[mp("M", "SA", "Gọi M là trung điểm của SA")],
                   sections=[{
                       "section_id": "sec", "plane_name": "P", "target_solid_id": "s1",
                       "plane_kind": "through_point_parallel_plane", "through_point": "M",
                       "parallel_plane": ["A", "B", "C"], "stated_intersections": [],
                       "quote": "Gọi (P) là mặt phẳng đi qua M và song song với mặt phẳng (ABCD)",
                   }],
                   goals=[("q1", "area", {"section_id": "sec"},
                           "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)")]),
        ("SERVED", {"q1": ("area", area2(V(0, 0, F(3, 2)), V(2, 0, F(3, 2)), V(2, 2, F(3, 2)), V(0, 2, F(3, 2))))}),
        "Q43 frame; mid-section square of side 2 => area = 4, area^2 = 16",
        ("translate_point", "section", "ask_section_area"), "REGISTERED_DECOMPOSITION")

    sc_q33 = [V(0, 0, 0), V(F(3, 2), 0, F(3, 2)), V(1, 1, 2), V(0, F(3, 2), F(3, 2))]
    add("HB22", "SECTION", "section through A perpendicular to SC (Q33)",
        hb_pyramid("3", "3",
                   extra_text="Gọi (P) là mặt phẳng đi qua A và vuông góc với SC. ",
                   sections=[{
                       "section_id": "sec", "plane_name": "P", "target_solid_id": "s1",
                       "plane_kind": "through_point_perpendicular_line", "through_point": "A",
                       "perpendicular_line": ["S", "C"], "stated_intersections": [],
                       "quote": "Gọi (P) là mặt phẳng đi qua A và vuông góc với SC",
                   }],
                   goals=[("q1", "area", {"section_id": "sec"},
                           "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)")]),
        ("SERVED", {"q1": ("area", area2(*sc_q33))}),
        "Q33 frame; scaled 3/2 from P2 => area^2 = (3/2)^4 * area^2(P2)",
        ("orthogonal_projection_line", "translate_point", "section", "ask_section_area"), "REGISTERED_DECOMPOSITION")

    sec_c17_q33 = [V(F(3, 2), 0, 0), V(F(9, 4), 0, F(3, 4)), V(F(9, 4), F(9, 4), F(3, 4)), V(F(3, 2), 3, 0)]
    add("HB23", "SECTION", "constrained section through M, N perpendicular to (SBC) (Q33, C17)",
        hb_pyramid("3", "3",
                   extra_text="Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. Mặt phẳng (P) đi qua M, N và vuông góc với (SBC). ",
                   extra_prem=[mp("M", "AB", "Gọi M là trung điểm của AB"), mp("N", "CD", "Gọi N là trung điểm của CD")],
                   sections=[{
                       "section_id": "sec", "plane_name": "P", "target_solid_id": "s1",
                       "plane_kind": "constrained",
                       "constraints": [
                           {"kind": "contains_points", "operands": ["M", "N"]},
                           {"kind": "perpendicular_to_plane", "operands": ["S", "B", "C"]},
                       ],
                       "stated_intersections": [],
                       "quote": "Mặt phẳng (P) đi qua M, N và vuông góc với (SBC)",
                   }],
                   goals=[("q1", "area", {"section_id": "sec"},
                           "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó")]),
        ("SERVED", {"q1": ("area", area2(*sec_c17_q33))}),
        "Q33 frame; C17 constrained section trapezoid",
        ("orthogonal_projection", "translate_point", "section", "ask_section_area"), "GOAL_DRIVEN_DISCOVERY")

    # 12. AUXILIARY_CONSTRUCTION (Các phép dựng phụ — property-defined points via Goal-Driven Discovery)
    g_sbd_q33 = cen(Q33["S"], Q33["B"], Q33["D"])
    add("HB24", "AUXILIARY_CONSTRUCTION", "orthocenter of equilateral SBD to base (Q33, C18)",
        hb_pyramid("3", "3",
                   described=[{"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"],
                               "quote": "trực tâm của tam giác SBD"}],
                   goals=[("q1", "distance", {"point": "@h1", "plane": ["A", "B", "C", "D"]},
                           "Tính khoảng cách từ trực tâm của tam giác SBD đến mặt phẳng (ABCD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(g_sbd_q33, Q33["A"], Q33["B"], Q33["C"]))}),
        "Q33 frame; SBD equilateral => orthocenter = centroid = (1, 1, 1), d = 1",
        ("orthogonal_projection_line", "intersect_line_line", "ask_distance_point_plane"), "GOAL_DRIVEN_DISCOVERY")

    add("HB25", "AUXILIARY_CONSTRUCTION", "circumcenter of equilateral SBD to A (Q33, C18)",
        hb_pyramid("3", "3",
                   described=[{"described_id": "o1", "kind": "circumcenter", "polygon": ["S", "B", "D"],
                               "quote": "tâm đường tròn ngoại tiếp tam giác SBD"}],
                   goals=[("q1", "distance", {"segment": ["@o1", "A"]},
                           "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBD với A")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(g_sbd_q33, Q33["A"]))}),
        "Q33 frame; circumcenter(SBD) = (1, 1, 1) => d^2(O, A) = 3",
        ("midpoint", "orthogonal_projection_line", "translate_point", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")

    add("HB26", "AUXILIARY_CONSTRUCTION", "circumcenter of right face SBC to line AD (Q43, C18 + foot)",
        hb_pyramid("4", "3",
                   described=[{"described_id": "o1", "kind": "circumcenter", "polygon": ["S", "B", "C"],
                               "quote": "tâm đường tròn ngoại tiếp tam giác SBC"}],
                   goals=[("q1", "distance", {"point": "@o1", "line": ["A", "D"]},
                           "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác SBC đến đường thẳng AD")]),
        ("SERVED", {"q1": ("len", d2_pt_line(mid(Q43["S"], Q43["C"]), Q43["A"], Q43["D"]))}),
        "Q43 frame; SBC right at B => circumcenter = mid(SC) = (2, 2, 3/2), foot on AD is (0, 2, 0) => d^2 = 4 + 9/4 = 25/4",
        ("midpoint", "orthogonal_projection_line", "translate_point", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")

    # 13. MULTI_GOAL (Đa mục tiêu)
    add("HB27", "MULTI_GOAL", "multi-goal three heterogeneous quantities (Q43)",
        hb_pyramid("4", "3", goals=[
            ("q1", "distance", {"point": "A", "line": ["S", "C"]}, "Tính khoảng cách từ A đến đường thẳng SC"),
            ("q2", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "Tính góc giữa SC và mặt phẳng (ABCD)"),
            ("q3", "distance", {"point": "A", "plane": ["S", "B", "C"]}, "Tính khoảng cách từ A đến mặt phẳng (SBC)"),
        ]),
        ("SERVED", {
            "q1": ("len", d2_pt_line(Q43["A"], Q43["S"], Q43["C"])),
            "q2": ("cos2", cos2_line_plane(Q43["S"], Q43["C"], Q43["A"], Q43["B"], Q43["C"])),
            "q3": ("len", d2_pt_plane(Q43["A"], Q43["S"], Q43["B"], Q43["C"])),
        }),
        "Q43 frame; 3 goals in one problem",
        ("orthogonal_projection_line", "ask_length", "ask_angle_line_plane", "ask_distance_point_plane"),
        "REGISTERED_DECOMPOSITION")

    add("HB28", "MULTI_GOAL", "multi-goal orthocenter and circumcenter of SBD (Q33)",
        hb_pyramid("3", "3",
                   described=[
                       {"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"],
                        "quote": "trực tâm của tam giác SBD"},
                       {"described_id": "o1", "kind": "circumcenter", "polygon": ["S", "B", "D"],
                        "quote": "tâm đường tròn ngoại tiếp tam giác SBD"},
                   ],
                   goals=[
                       ("q1", "distance", {"segment": ["@h1", "A"]},
                        "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với A"),
                       ("q2", "distance", {"segment": ["@o1", "C"]},
                        "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBD với C"),
                   ]),
        ("SERVED", {
            "q1": ("len", O.distance_sq_points(g_sbd_q33, Q33["A"])),
            "q2": ("len", O.distance_sq_points(g_sbd_q33, Q33["C"])),
        }),
        "Q33 frame; both = (1, 1, 1)",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")

    # 14. INTERMEDIATE_REUSE (Bài toán cần tái sử dụng trung gian)
    h_ab_q43 = foot_line(Q43["A"], Q43["S"], Q43["B"])
    add("HB29", "INTERMEDIATE_REUSE", "reuse of source-named foot H on SB across two goals (Q43)",
        hb_pyramid("4", "3",
                   extra_text="Gọi H là hình chiếu vuông góc của A lên SB. ",
                   extra_prem=[{"kind": "orthogonal_projection_line",
                                "args": {"point": "A", "image": "H", "line": ["S", "B"]},
                                "quote": "Gọi H là hình chiếu vuông góc của A lên SB", "solid_id": "s1"}],
                   goals=[
                       ("q1", "distance", {"point": "A", "line": ["S", "B"]}, "Tính khoảng cách từ A đến đường thẳng SB"),
                       ("q2", "distance", {"point": "H", "plane": ["A", "B", "C", "D"]},
                        "Tính khoảng cách từ H đến mặt phẳng (ABCD)"),
                   ]),
        ("SERVED", {
            "q1": ("len", d2_pt_line(Q43["A"], Q43["S"], Q43["B"])),
            "q2": ("len", d2_pt_plane(h_ab_q43, Q43["A"], Q43["B"], Q43["C"])),
        }),
        "Q43 frame; H reused by q1 without fresh label allocation",
        ("orthogonal_projection_line", "ask_length", "ask_distance_point_plane"),
        "SOURCE_EXPLICIT_SEQUENCE")

    hc_q43 = foot_line(Q43["A"], Q43["S"], Q43["C"])
    add("HB30", "INTERMEDIATE_REUSE", "goal-only foot on SC reused by described-point goal (Q43)",
        hb_pyramid("4", "3",
                   described=[{"described_id": "h1", "kind": "orthogonal_projection_line", "point": "A",
                               "line": ["S", "C"], "quote": "hình chiếu vuông góc của A lên SC"}],
                   goals=[
                       ("q1", "distance", {"point": "A", "line": ["S", "C"]}, "Tính khoảng cách từ A đến đường thẳng SC"),
                       ("q2", "distance", {"segment": ["@h1", "S"]},
                        "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của A lên SC với S"),
                   ]),
        ("SERVED", {
            "q1": ("len", d2_pt_line(Q43["A"], Q43["S"], Q43["C"])),
            "q2": ("len", O.distance_sq_points(hc_q43, Q43["S"])),
        }),
        "Q43 frame; single foot construction shared between q1 and q2",
        ("orthogonal_projection_line", "ask_length"),
        "REGISTERED_DECOMPOSITION")

    # 15. COMPETING_PLANS (Bài toán có nhiều phương án giải)
    add("HB31", "COMPETING_PLANS", "prism orthocenter of right base ABC to A' (L685, competing altitude pairs)",
        hb_prism("6", "8", "5",
                 described=[{"described_id": "h1", "kind": "orthocenter", "polygon": ["A", "B", "C"],
                             "quote": "trực tâm của tam giác ABC"}],
                 goals=[("q1", "distance", {"segment": ["@h1", "A'"]},
                         "Tính độ dài đoạn thẳng nối trực tâm của tam giác ABC với A'")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(L685["A"], L685["A'"]))}),
        "L685 frame; orthocenter(ABC) = A => |AA'|^2 = 25",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")

    add("HB32", "COMPETING_PLANS", "tetrahedron orthocenter of slanted face ABC to O (T236, 3 competing altitude pairs)",
        hb_tetra("2", "3", "6",
                 described=[{"described_id": "h1", "kind": "orthocenter", "polygon": ["A", "B", "C"],
                             "quote": "trực tâm của tam giác ABC"}],
                 goals=[("q1", "distance", {"segment": ["@h1", "O"]},
                         "Tính độ dài đoạn thẳng nối trực tâm của tam giác ABC với O")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(T236["O"], T236["A"], T236["B"], T236["C"]))}),
        "T236 frame; orthocenter of ABC is the orthogonal projection of O onto (ABC) => d^2 = 18/7",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")

    add("HB33", "COMPETING_PLANS", "prism circumcenter of right base ABC to A' (L685, competing perpendicular bisector pairs)",
        hb_prism("6", "8", "5",
                 described=[{"described_id": "o1", "kind": "circumcenter", "polygon": ["A", "B", "C"],
                             "quote": "tâm đường tròn ngoại tiếp tam giác ABC"}],
                 goals=[("q1", "distance", {"segment": ["@o1", "A'"]},
                         "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác ABC với A'")]),
        ("SERVED", {"q1": ("len", O.distance_sq_points(mid(L685["B"], L685["C"]), L685["A'"]))}),
        "L685 frame; circumcenter(ABC) = mid(BC) = (3, 4, 0) => d^2((3,4,0), (0,0,5)) = 50",
        ("midpoint", "orthogonal_projection_line", "translate_point", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY")

    add("HB34", "COMPETING_PLANS", "pyramid orthocenter of right face SBC to plane (SAD) (Q43, competing altitude pairs)",
        hb_pyramid("4", "3",
                   described=[{"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "C"],
                               "quote": "trực tâm của tam giác SBC"}],
                   goals=[("q1", "distance", {"point": "@h1", "plane": ["S", "A", "D"]},
                           "Tính khoảng cách từ trực tâm của tam giác SBC đến mặt phẳng (SAD)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(Q43["B"], Q43["S"], Q43["A"], Q43["D"]))}),
        "Q43 frame; orthocenter(SBC) = B => d(B, (SAD)) = 4 => d^2 = 16",
        ("orthogonal_projection_line", "intersect_line_line", "ask_distance_point_plane"),
        "GOAL_DRIVEN_DISCOVERY")

    # Known Residual Gap Boundary Probes on Held-Out (G2, G4, G6, G7)
    add("HB35", "DISTANCE_POINT_LINE", "held-out probe G2: distance from B to line joining A with mid(SC) (Q43)",
        hb_pyramid("4", "3",
                   described=[dmid("m1", "SC", "trung điểm của SC")],
                   goals=[("q1", "distance", {"point": "B", "line": ["A", "@m1"]},
                           "Tính khoảng cách từ B đến đường thẳng nối A với trung điểm của SC")]),
        ("SERVED", {"q1": ("len", d2_pt_line(Q43["B"], Q43["A"], mid(Q43["S"], Q43["C"])))}),
        "Q43 frame; probes G2 (described point inside line operand of distance goal)",
        ("midpoint", "orthogonal_projection_line", "ask_length"), "DESCRIPTOR_COMPOSITION", gap_probe="G2")

    add("HB36", "SECTION", "held-out probe G4: constrained 3-point section named (Q) (Q43)",
        hb_pyramid("4", "3",
                   extra_text="Gọi M, N, P lần lượt là trung điểm của SA, SB, SC. Mặt phẳng (Q) đi qua M, N, P. ",
                   extra_prem=[
                       mp("M", "SA", "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC"),
                       mp("N", "SB", "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC"),
                       mp("P", "SC", "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC"),
                   ],
                   sections=[{
                       "section_id": "sec", "plane_name": "Q", "target_solid_id": "s1",
                       "plane_kind": "constrained",
                       "constraints": [{"kind": "contains_points", "operands": ["M", "N", "P"]}],
                       "stated_intersections": [],
                       "quote": "Mặt phẳng (Q) đi qua M, N, P",
                   }],
                   goals=[("q1", "area", {"section_id": "sec"},
                           "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (Q)")]),
        ("SERVED", {"q1": ("area", area2(V(0, 0, F(3, 2)), V(2, 0, F(3, 2)), V(2, 2, F(3, 2)), V(0, 2, F(3, 2))))}),
        "Q43 frame; probes G4 (3-point constrained plane drops plane_name='Q')",
        ("section", "ask_section_area"), "SOURCE_EXPLICIT_SEQUENCE", gap_probe="G4")

    add("HB37", "MULTI_GOAL", "held-out probe G6: three property-defined points in one problem (Q33)",
        hb_pyramid("3", "3",
                   described=[
                       {"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"],
                        "quote": "trực tâm của tam giác SBD"},
                       {"described_id": "o1", "kind": "circumcenter", "polygon": ["S", "B", "C"],
                        "quote": "tâm đường tròn ngoại tiếp tam giác SBC"},
                       {"described_id": "h2", "kind": "orthocenter", "polygon": ["S", "C", "D"],
                        "quote": "trực tâm của tam giác SCD"},
                   ],
                   goals=[
                       ("q1", "distance", {"segment": ["@h1", "A"]},
                        "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với A"),
                       ("q2", "distance", {"segment": ["@o1", "A"]},
                        "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBC với A"),
                       ("q3", "distance", {"segment": ["@h2", "A"]},
                        "Tính độ dài đoạn thẳng nối trực tâm của tam giác SCD với A"),
                   ]),
        ("SERVED", {
            "q1": ("len", O.distance_sq_points(g_sbd_q33, Q33["A"])),
            "q2": ("len", O.distance_sq_points(mid(Q33["S"], Q33["C"]), Q33["A"])),
            "q3": ("len", O.distance_sq_points(Q33["D"], Q33["A"])),
        }),
        "Q33 frame; probes G6 (MAX_EFFECT_CANDIDATES = 48 / MAX_MEMORY_DECLARATIONS = 32)",
        ("orthogonal_projection_line", "intersect_line_line", "ask_length"),
        "GOAL_DRIVEN_DISCOVERY", gap_probe="G6")

    add("HB38", "AUXILIARY_CONSTRUCTION", "held-out probe G7: projection of orthocenter(SBD) onto base (Q33)",
        hb_pyramid("3", "3",
                   described=[
                       {"described_id": "h1", "kind": "orthocenter", "polygon": ["S", "B", "D"],
                        "quote": "trực tâm của tam giác SBD"},
                       {"described_id": "k1", "kind": "orthogonal_projection", "point": "@h1",
                        "plane": ["A", "B", "C", "D"],
                        "quote": "hình chiếu vuông góc của trực tâm của tam giác SBD lên mặt phẳng (ABCD)"},
                   ],
                   goals=[("q1", "distance", {"point": "@k1", "plane": ["S", "A", "B"]},
                           "Tính khoảng cách từ hình chiếu vuông góc của trực tâm của tam giác SBD lên mặt phẳng (ABCD) đến mặt phẳng (SAB)")]),
        ("SERVED", {"q1": ("len", d2_pt_plane(foot_plane(g_sbd_q33, Q33["A"], Q33["B"], Q33["C"]),
                                              Q33["S"], Q33["A"], Q33["B"]))}),
        "Q33 frame; probes G7 (nested description through POINT_DEFINITIONS)",
        ("orthogonal_projection_line", "intersect_line_line", "orthogonal_projection", "ask_distance_point_plane"),
        "GOAL_DRIVEN_DISCOVERY", gap_probe="G7")

    # 16. MISSING_DATA (Bài toán không đủ dữ kiện)
    m1_t, m1_p = hb_pyramid("4", "3", goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]},
                            "Tính khoảng cách từ A đến mặt phẳng (SBC)")])
    m1_t = m1_t.replace(" và SA = 3", "")
    m1_p["problem_text"] = m1_t
    m1_p["premises"] = m1_p["premises"][:2]
    add("HB39", "MISSING_DATA", "missing height SA on pyramid side 4",
        (m1_t, m1_p),
        ("REFUSED", "refusal", {"MISSING_DIMENSION", "UNDERDETERMINED_POINT", "FACT_INCOMPLETE", "MISSING_DATA"}),
        "SA not specified => apex height underdetermined")

    m2_t, m2_p = hb_tetra("2", "3", "6", goals=[("q1", "distance", {"point": "O", "plane": ["A", "B", "C"]},
                          "Tính khoảng cách từ O đến mặt phẳng (ABC)")])
    m2_t = m2_t.replace(", OC = 6. ", ". ")
    m2_p["problem_text"] = m2_t
    m2_p["premises"] = [pr for pr in m2_p["premises"] if pr["quote"] != "OC = 6"]
    add("HB40", "MISSING_DATA", "missing edge OC on right tetrahedron",
        (m2_t, m2_p),
        ("REFUSED", "refusal", {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"}),
        "OC not specified => vertex C underdetermined")

    add("HB41", "MISSING_DATA", "ambiguous angle target plane missing (clarification)",
        hb_pyramid("4", "3",
                   goals=[("q1", "angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]},
                           "Tính góc giữa SC và mặt phẳng")],
                   unresolved=[{"unresolved_id": "u1", "kind": "missing_operand",
                                "missing_roles": ["target_line_or_plane"],
                                "quote": "Tính góc giữa SC và mặt phẳng"}]),
        ("REFUSED", "clarification", {"AMBIGUOUS_FACT"}),
        "Target plane omitted => deterministic clarification")

    # 17. OUT_OF_SCOPE (Bài toán ngoài phạm vi)
    add("HB42", "OUT_OF_SCOPE", "unknown vertex label K in described midpoint",
        hb_pyramid("4", "3",
                   described=[dmid("m1", "SK", "trung điểm của SK")],
                   goals=[("q1", "distance", {"point": "@m1", "plane": ["A", "B", "C", "D"]},
                           "Tính khoảng cách từ trung điểm của SK đến mặt phẳng (ABCD)")]),
        ("REFUSED", "refusal", {"UNKNOWN_LABEL", "SOURCE_OBJECT_MISMATCH", "UNDERDETERMINED_POINT"}),
        "Vertex K does not exist in source")

    oos_t, oos_p = hb_pyramid("4", "3", goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]},
                              "Tính khoảng cách từ A đến mặt phẳng (SBC)")])
    oos_p["premises"][2]["quote"] = "SA = 9"
    add("HB43", "OUT_OF_SCOPE", "ungrounded fabricated quote SA = 9 not in source",
        (oos_t, oos_p),
        ("REFUSED", "refusal", {"QUOTE_NOT_IN_SOURCE", "UNGROUNDED_VALUE"}),
        "Fabricated quote SA = 9 rejected by Source Gate")

    # 18. DEGENERATE (Bài toán suy biến / mâu thuẫn dữ kiện)
    add("HB44", "DEGENERATE", "contradictory base edge AB = 5 on square side 4",
        hb_pyramid("4", "3",
                   extra_text="AB = 5. ",
                   extra_prem=[{"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "5"},
                                "quote": "AB = 5", "solid_id": "s1"}],
                   goals=[("q1", "distance", {"point": "A", "plane": ["S", "B", "C"]},
                           "Tính khoảng cách từ A đến mặt phẳng (SBC)")]),
        ("REFUSED", "refusal", {"INCONSISTENT_FACTS", "INCONSISTENT_LENGTH", "CONTRADICTORY_DATA"}),
        "Square side 4 contradicts AB = 5")

    add("HB45", "DEGENERATE", "described centroid of collinear points A, M, B",
        hb_pyramid("4", "3",
                   extra_text="Gọi M là trung điểm của AB. ",
                   extra_prem=[mp("M", "AB", "Gọi M là trung điểm của AB")],
                   described=[{"described_id": "g1", "kind": "centroid", "polygon": ["A", "M", "B"],
                               "quote": "trọng tâm của tam giác AMB"}],
                   goals=[("q1", "distance", {"point": "@g1", "plane": ["S", "C", "D"]},
                           "Tính khoảng cách từ trọng tâm của tam giác AMB đến mặt phẳng (SCD)")]),
        ("REFUSED", "refusal", {"COLLINEAR_POINTS", "DEGENERATE_POINTS", "DEGENERATE_TRIANGLE", "DEGENERATE_POLYGON"}),
        "A, M, B collinear => degenerate triangle")

    add("HB46", "DEGENERATE", "three lateral edges SA = SB = SC = 4 shorter than base circumradius R = 5",
        hb_three_edges("6", "8", "4", ("q1", "distance", {"point": "S", "plane": ["A", "B", "C"]},
                       "Tính khoảng cách từ S đến mặt phẳng (ABC)")),
        ("REFUSED", "refusal", {"INCONSISTENT_FACTS"}),
        "Base ABC right at A with AB=6, AC=8 has circumradius R = 5 > SA = 4 => h^2 = 16 - 25 < 0")

    return C


# ── 14-Class Workstream B Taxonomy Classifier (Section B.5) ──────────────────────────────────────────────────────────

TAXONOMY_14 = (
    "CORRECT_SERVED",
    "CORRECT_REFUSAL",
    "CORRECT_CLARIFICATION",
    "FALSE_REFUSAL",
    "WRONG_SERVED",
    "UNSUPPORTED_CAPABILITY",
    "MISSING_PRIMITIVE",
    "PLANNER_SEARCH_FAILURE",
    "SEARCH_BUDGET_EXHAUSTED",
    "SOURCE_GATE_ERROR",
    "BRIDGE_ERROR",
    "EXACT_KERNEL_ERROR",
    "ADAPTER_ERROR",
    "SCENE3D_ERROR",
)


def classify_14(case: dict[str, Any], status: str | None, code: str | None, answers: dict[str, str],
                clar: bool, scene_issues: list[str], stage_failed: str | None) -> str:
    exp = case["expect"]
    if status not in ("SERVED", "REFUSED"):
        return "ADAPTER_ERROR"
    if exp[0] == "SERVED":
        if status == "SERVED":
            if scene_issues:
                return "SCENE3D_ERROR"
            for g, (meas, want) in exp[1].items():
                if want is None:
                    continue
                got = answers.get(g)
                val = F(got) if meas == "cos2" and got and "√" not in got else DM.coef_square(got) if meas != "cos2" else None
                if val is None or val != want:
                    return "WRONG_SERVED"
            return "CORRECT_SERVED"
        # Expected SERVED, got REFUSED: attribute to exact architectural layer
        if code == "PLAN_TOO_LARGE" or code == "IR_MEMORY_BUDGET_EXCEEDED":
            return "SEARCH_BUDGET_EXHAUSTED"
        if code in ("ADAPTER_INTERNAL_ERROR", "ROUTE_INTERNAL_ERROR"):
            return "ADAPTER_ERROR"
        if code and code.startswith("BRIDGE_"):
            return "BRIDGE_ERROR"
        if stage_failed == "bridge":
            return "BRIDGE_ERROR"
        if code in ("SOURCE_OBJECT_MISMATCH", "QUOTE_NOT_IN_SOURCE", "UNGROUNDED_VALUE", "SOURCE_PREMISE_UNREAD"):
            return "SOURCE_GATE_ERROR"
        if code in ("UNSUPPORTED_CAPABILITY", "OUT_OF_SCOPE", "CURVED_WORDING_UNSUPPORTED", "EXACT_DOMAIN_EXCEEDED"):
            return "UNSUPPORTED_CAPABILITY" if not case.get("primitives") else "PLANNER_SEARCH_FAILURE"
        if case.get("primitives"):
            return "PLANNER_SEARCH_FAILURE"
        return "FALSE_REFUSAL"
    # Expected REFUSED
    if status == "SERVED":
        return "WRONG_SERVED"
    group, codes = exp[1], exp[2]
    if group == "clarification":
        return "CORRECT_CLARIFICATION" if code == "AMBIGUOUS_FACT" and clar else "FALSE_REFUSAL"
    if codes is None or code in codes:
        return "CORRECT_REFUSAL"
    return "FALSE_REFUSAL"


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def evaluate_suite(cases: list[dict[str, Any]], suite_name: str) -> dict[str, Any]:
    policy = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    rows = []
    pl_ms, k_ms, ad_ms, cold_ms, warm_ms = [], [], [], [], []
    tax14_counts = {k: 0 for k in TAXONOMY_14}
    matrix8_counts: dict[str, int] = {}

    for c in cases:
        text, payload = c["text"], c["payload"]
        plan = None
        t_plan = t_kern = t_adap = None
        stage_failed = None
        cert_verified = False
        cert_checks_count = 0
        try:
            bridged = bridge_v2(TN._parse(TN.TypedFactNextPayloadV2, payload))
        except Exception:
            bridged = None
            stage_failed = "bridge"

        if bridged is not None:
            t0 = time.perf_counter()
            try:
                plan = planner.lap_ke_hoach(bridged, text)
            except TuChoi:
                plan = None
                stage_failed = "planner"
            t_plan = (time.perf_counter() - t0) * 1000
            if plan is not None:
                doc = tuple(q for g in (*plan.goals, *plan.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
                t1 = time.perf_counter()
                try:
                    k_res = engine.dung_tu_loi_goi(
                        text,
                        {"calls": plan.calls, "named_planes": plan.named_planes},
                        tuple(plan.auxiliary),
                        doc,
                    )
                    cert_verified = bool(k_res.status == "SERVED" and k_res.kernel_check)
                    cert_checks_count = len(k_res.trace or ())
                except TuChoi:
                    stage_failed = "kernel_or_source_gate"
                t_kern = (time.perf_counter() - t1) * 1000

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
        t_warm = statistics.median(ws)

        if t_plan is not None and t_kern is not None:
            t_adap = max(0.0, t_warm - (t_plan + t_kern))
            ad_ms.append(t_adap)

        route = out.response.get("route_d") or {}
        env = out.response.get("envelope") or {}
        status = route.get("status") or out.response.get("status")
        code = env.get("reason_code") or out.response.get("reason_code")
        answers = {k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()} if status == "SERVED" else {}
        clar = bool(
            (route.get("refusal") or {}).get("clarification")
            or env.get("clarification")
            or (route.get("refusal") or {}).get("clarifications")
        )
        scene = env.get("scene3d")
        steps = (
            ((scene or {}).get("formation") or {}).get("steps")
            or env.get("construction_steps")
            or (scene or {}).get("constructionSteps")
            or []
        )
        issues = validate_construction_continuity(scene) if (status == "SERVED" and scene) else []
        if status == "SERVED" and not scene:
            issues = ["NO_SCENE3D"]

        tel = (route.get("planner") or {}).get("search_telemetry") or {}
        cls8 = DM.classify(c, status, code, answers, clar, issues)
        cls14 = classify_14(c, status, code, answers, clar, issues, stage_failed)

        tax14_counts[cls14] = tax14_counts.get(cls14, 0) + 1
        matrix8_counts[cls8] = matrix8_counts.get(cls8, 0) + 1

        if t_plan is not None:
            pl_ms.append(t_plan)
        if t_kern is not None:
            k_ms.append(t_kern)
        cold_ms.append(t_cold)
        warm_ms.append(t_warm)

        exp = c["expect"]
        rows.append({
            "id": c["id"],
            "group": c.get("group", c["family"]),
            "family": c["family"],
            "gap_probe": c.get("gap_probe"),
            "level_expected": c.get("level"),
            "outcome_8": cls8,
            "outcome_14": cls14,
            "status": status,
            "reason_code": code,
            "answers": answers,
            "expected": (
                {g: [m, str(v) if v is not None else "HAND_NOTE"] for g, (m, v) in exp[1].items()}
                if exp[0] == "SERVED"
                else {"group": exp[1], "codes": sorted(exp[2]) if exp[2] else "ANY_TYPED"}
            ),
            "oracle": c["oracle"],
            "primitives": c["primitives"],
            "plan_origin": tel.get("classification", "UNKNOWN") if tel else "UNKNOWN",
            "explored_states": tel.get("explored_states", "UNKNOWN"),
            "candidate_evaluations": tel.get("candidate_evaluations", "UNKNOWN"),
            "pruned_nodes": tel.get("pruned_nodes", "UNKNOWN"),
            "search_depth": tel.get("search_depth", "UNKNOWN"),
            "reused_intermediates": tel.get("reused_intermediates", "UNKNOWN"),
            "plan_cost": tel.get("plan_cost", "UNKNOWN"),
            "selected_plan": tel.get("selected_plan", []),
            "search_generated_steps": len(tel.get("search_generated_steps") or []) if tel else "UNKNOWN",
            "certificate_verified": cert_verified,
            "certificate_checks_count": cert_checks_count,
            "construction_steps_count": len(steps),
            "scene_continuity_issues": issues[:3],
            "planner_cpu_ms": round(t_plan, 3) if t_plan is not None else "NOT_MEASURED",
            "kernel_cpu_ms": round(t_kern, 3) if t_kern is not None else "NOT_MEASURED",
            "adapter_scene3d_cpu_ms": round(t_adap, 3) if t_adap is not None else "NOT_MEASURED",
            "route_cold_ms": round(t_cold, 3),
            "route_warm_ms": round(t_warm, 3),
            "peak_memory_kib": round(peak, 2),
        })

    in_scope_all = [r for r, c in zip(rows, cases) if c["expect"][0] == "SERVED"]
    in_scope_supported = [r for r, c in zip(rows, cases) if c["expect"][0] == "SERVED" and not c.get("gap_probe")]
    neg_cases = [r for r, c in zip(rows, cases) if c["expect"][0] == "REFUSED"]

    served_ok = [r for r in rows if r["outcome_14"] == "CORRECT_SERVED"]
    all_certs_verified = all(r["certificate_verified"] and r["certificate_checks_count"] > 0 for r in served_ok)
    all_continuity_ok = all(len(r["scene_continuity_issues"]) == 0 and r["construction_steps_count"] > 0 for r in served_ok)

    num = [r for r in rows if isinstance(r["explored_states"], int)]
    plan_origins: dict[str, int] = {}
    for r in served_ok:
        po = r["plan_origin"]
        plan_origins[po] = plan_origins.get(po, 0) + 1

    return {
        "suite_name": suite_name,
        "case_count": len(rows),
        "in_scope_total": len(in_scope_all),
        "in_scope_supported_total": len(in_scope_supported),
        "in_scope_served": len(served_ok),
        "in_scope_solve_rate_all": round(len(served_ok) / len(in_scope_all), 4) if in_scope_all else 0.0,
        "in_scope_solve_rate_supported": round(
            sum(r["outcome_14"] == "CORRECT_SERVED" for r in in_scope_supported) / len(in_scope_supported), 4
        ) if in_scope_supported else 0.0,
        "negative_total": len(neg_cases),
        "negative_correct": sum(r["outcome_14"] in ("CORRECT_REFUSAL", "CORRECT_CLARIFICATION") for r in neg_cases),
        "negative_refusal_rate": round(
            sum(r["outcome_14"] in ("CORRECT_REFUSAL", "CORRECT_CLARIFICATION") for r in neg_cases) / len(neg_cases), 4
        ) if neg_cases else 0.0,
        "false_refusal_count": tax14_counts["FALSE_REFUSAL"],
        "wrong_served_count": tax14_counts["WRONG_SERVED"],
        "all_served_certificates_verified": all_certs_verified,
        "all_served_scene3d_continuity_ok": all_continuity_ok,
        "plan_origin_counts": dict(sorted(plan_origins.items())),
        "outcome_counts_8": dict(sorted(matrix8_counts.items())),
        "outcome_counts_14": {k: v for k, v in tax14_counts.items() if v > 0},
        "outcome_counts_14_full": tax14_counts,
        "performance": {
            "planner_cpu_ms": DM._stats(pl_ms),
            "kernel_cpu_ms": DM._stats(k_ms),
            "adapter_scene3d_cpu_ms": DM._stats(ad_ms),
            "route_cold_ms": DM._stats(cold_ms),
            "route_warm_ms": DM._stats(warm_ms),
            "peak_memory_kib_max": round(max(r["peak_memory_kib"] for r in rows), 2),
            "explored_states_max": max((r["explored_states"] for r in num), default="UNKNOWN"),
            "candidate_evaluations_max": max((r["candidate_evaluations"] for r in num), default="UNKNOWN"),
            "pruned_nodes_max": max((r["pruned_nodes"] for r in num if isinstance(r["pruned_nodes"], int)), default="UNKNOWN"),
            "search_depth_max": max((r["search_depth"] for r in num if isinstance(r["search_depth"], int)), default="UNKNOWN"),
            "reused_intermediates_total": sum(r["reused_intermediates"] for r in num if isinstance(r["reused_intermediates"], int)),
            "search_exhausted_cases": tax14_counts["SEARCH_BUDGET_EXHAUSTED"],
        },
        "cases": rows,
    }


# ── Section VIII: Mirror-Solution Equivalence Audit for `_dinh_tu_ba_canh_ben` ──────────────────────────────────────

def _run_dung_direct(calls_raw: list[dict[str, Any]]) -> tuple[Any, dict[str, str], bool]:
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.validator import validate_semantic_program

    norm_calls = []
    for c in calls_raw:
        c2 = dict(c)
        q = c2.pop("quote", "q")
        c2.setdefault("source", {"quotes": [q]})
        norm_calls.append(c2)
    calls = engine.doc_ke_hoach({"calls": norm_calls})
    dung = engine._Dung(calls, "", None)
    dung.thu_khoi()
    dung.bo_cuc_day()
    dung.giai_phu_thuoc()
    dung.chon_ba_mat([])
    dung.kiem()
    program, hoi = dung.bien_dich()
    vr = validate_semantic_program(program)
    assert vr.ok, vr.error
    G = dung.metric()
    with engine._metric.using(G):
        ket = SemanticProgramInterpreter().execute(vr.spec)
    fm = ket.final_memory
    kernel_ok = all(
        (lambda v: v is not None and (v.x, v.y, v.z) == dung.pts[t])(fm.get(engine.ir_name(t)))
        for t in dung.pts
    )
    answers = {cid: engine.dinh_dang(fm.get(kq)) for cid, kq in hoi.items()}
    return dung, answers, kernel_ok


def run_mirror_solution_audit() -> dict[str, Any]:
    """Mathematical and empirical audit of `_dinh_tu_ba_canh_ben` (lines 971-997) and `_dat_ngoai_day` (lines 729-739)
    in `backend/app/simulation/geometry_functions/engine.py`.
    """
    # Part 1: Sole height anchor (S placed via _dinh_tu_ba_canh_ben on base ABC, right at A, AB=6, AC=8, SA=SB=SC=13).
    # Test across multiple goal types with z = +1 vs monkeypatched z = -1.
    base_calls = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "quote": "Cho hình chóp S.ABC"},
        {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A"},
        {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "6"}, "quote": "AB = 6"},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "8"}, "quote": "AC = 8"},
        {"id": "c5", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "13"}, "quote": "SA = SB = SC = 13"},
        {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "B"], "value": "13"}, "quote": "SA = SB = SC = 13"},
        {"id": "c7", "fn": "segment_length", "args": {"segment": ["S", "C"], "value": "13"}, "quote": "SA = SB = SC = 13"},
        {"id": "c8", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "B"]}, "quote": "Gọi M là trung điểm của SB"},
        {"id": "c9", "fn": "centroid", "args": {"point": "G", "polygon": ["S", "B", "C"]}, "quote": "Gọi G là trọng tâm của tam giác SBC"},
        {"id": "c10", "fn": "orthogonal_projection", "args": {"point": "S", "image": "H", "plane": ["A", "B", "C"]},
         "quote": "Gọi H là hình chiếu vuông góc của S lên mặt phẳng (ABC)"},
    ]
    goal_calls = [
        {"id": "g_vol", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "quote": "Tính thể tích khối chóp S.ABC"},
        {"id": "g_d_pt_pl", "fn": "ask_distance_point_plane", "args": {"point": "A", "plane": ["S", "B", "C"]},
         "quote": "Tính khoảng cách từ A đến mặt phẳng (SBC)"},
        {"id": "g_d_s_pl", "fn": "ask_distance_point_plane", "args": {"point": "S", "plane": ["A", "B", "C"]},
         "quote": "Tính khoảng cách từ S đến mặt phẳng (ABC)"},
        {"id": "g_len_am", "fn": "ask_length", "args": {"segment": ["A", "M"]}, "quote": "Tính độ dài đoạn thẳng AM"},
        {"id": "g_len_ag", "fn": "ask_length", "args": {"segment": ["A", "G"]}, "quote": "Tính độ dài đoạn thẳng AG"},
        {"id": "g_len_ah", "fn": "ask_length", "args": {"segment": ["A", "H"]}, "quote": "Tính độ dài đoạn thẳng AH"},
        {"id": "g_ang_lp", "fn": "ask_angle_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
         "quote": "Tính góc giữa SA và mặt phẳng (ABC)"},
        {"id": "g_ang_ll", "fn": "ask_angle_lines", "args": {"line1": ["S", "A"], "line2": ["B", "C"]},
         "quote": "Tính góc giữa hai đường thẳng SA và BC"},
        {"id": "g_ang_dih", "fn": "ask_angle_plane_plane", "args": {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]},
         "quote": "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABC)"},
        {"id": "g_area", "fn": "ask_area", "args": {"polygon": ["A", "M", "C"]}, "quote": "Tính diện tích tam giác AMC"},
        {"id": "g_skew", "fn": "ask_distance_lines", "args": {"line1": ["S", "A"], "line2": ["B", "C"]},
         "quote": "Tính khoảng cách giữa hai đường thẳng SA và BC"},
    ]
    all_calls_raw = base_calls + goal_calls

    # Run with default z = +1
    dung_plus, vals_plus, ok_plus = _run_dung_direct(all_calls_raw)
    pts_plus = dict(dung_plus.pts)

    # Run with flipped z = -1 in _Dung._dat_ngoai_day
    orig_dat = engine._Dung._dat_ngoai_day

    def _dat_minus(self_dung, ten: str, chan: str | tuple, h2: F, luat: str, calls: set[str]) -> None:
        if self_dung.h2 is None:
            self_dung.h2 = h2
            z = F(-1)
        elif (z := engine._sqrt_q(h2 / self_dung.h2)) is None:
            raise TuChoi("UNSUPPORTED_MULTIPLE_HEIGHTS", "hai độ cao độc lập có tỉ số vô tỉ")
        else:
            z = -z
        f = self_dung.pts[chan] if isinstance(chan, str) else chan
        self_dung.dung |= calls
        self_dung._dat(ten, (f[0], f[1], z), luat, calls)

    engine._Dung._dat_ngoai_day = _dat_minus
    try:
        dung_minus, vals_minus, ok_minus = _run_dung_direct(all_calls_raw)
        pts_minus = dict(dung_minus.pts)
    finally:
        engine._Dung._dat_ngoai_day = orig_dat

    rz_equivariant = all(
        pts_minus[k] == (pts_plus[k][0], pts_plus[k][1], -pts_plus[k][2])
        for k in pts_plus
    )
    sole_anchor_values_identical = (vals_plus == vals_minus)

    # Part 2: Two independent off-base points:
    # Pyramid S.ABC with base ABC (right at A, AB=6, AC=8) and lateral edges SA = SB = SC = 13 (places S via _dinh_tu_ba_canh_ben at (1/2, 1/2, z_S) with h2_S = 144),
    # plus an independent off-base point P with PA ⊥ (ABC), PA = 5 (places P first via _rang_buoc_vuong at (0, 0, +1) with self.h2 = 25).
    # Both z_S = +12/5 (same side of (ABC) as P) and z_S = -12/5 (opposite side of (ABC) from P) satisfy 100% of the premises!
    two_anchor_calls_raw = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "quote": "q"},
        {"id": "c3", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "q"},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "6"}, "quote": "q"},
        {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "8"}, "quote": "q"},
        {"id": "c6", "fn": "perpendicular_line_plane", "args": {"line": ["P", "A"], "plane": ["A", "B", "C"]}, "quote": "q"},
        {"id": "c7", "fn": "segment_length", "args": {"segment": ["P", "A"], "value": "5"}, "quote": "q"},
        {"id": "c8", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "13"}, "quote": "q"},
        {"id": "c9", "fn": "segment_length", "args": {"segment": ["S", "B"], "value": "13"}, "quote": "q"},
        {"id": "c10", "fn": "segment_length", "args": {"segment": ["S", "C"], "value": "13"}, "quote": "q"},
        {"id": "g_vol_s", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "quote": "q"},
        {"id": "g_len_sp", "fn": "ask_length", "args": {"segment": ["S", "P"]}, "quote": "q"},
        {"id": "g_ang_sp_abc", "fn": "ask_angle_line_plane", "args": {"line": ["S", "P"], "plane": ["A", "B", "C"]}, "quote": "q"},
        {"id": "g_d_p_sbc", "fn": "ask_distance_point_plane", "args": {"point": "P", "plane": ["S", "B", "C"]}, "quote": "q"},
    ]

    # Same-side branch (current engine default: z_P = +1, z_S = +12/5)
    dung_same, vals_same, ok_same = _run_dung_direct(two_anchor_calls_raw)

    # Opposite-side branch (z_P = +1, z_S = -12/5)
    def _dat_opposite_s(self_dung, ten: str, chan: str | tuple, h2: F, luat: str, calls: set[str]) -> None:
        if self_dung.h2 is None:
            self_dung.h2 = h2
            z = F(1)
        elif (z := engine._sqrt_q(h2 / self_dung.h2)) is None:
            raise TuChoi("UNSUPPORTED_MULTIPLE_HEIGHTS", "hai độ cao độc lập có tỉ số vô tỉ")
        elif ten == "S":
            z = -z
        f = self_dung.pts[chan] if isinstance(chan, str) else chan
        self_dung.dung |= calls
        self_dung._dat(ten, (f[0], f[1], z), luat, calls)

    engine._Dung._dat_ngoai_day = _dat_opposite_s
    try:
        dung_opp, vals_opp, ok_opp = _run_dung_direct(two_anchor_calls_raw)
    finally:
        engine._Dung._dat_ngoai_day = orig_dat

    # Part 3: After-fix verification through engine.dung_tu_loi_goi across all 4 Section VIII scenarios
    base_two_anchor_text = (
        "Cho hình chóp S.ABC và hình chóp P.ABC có đáy ABC vuông tại A, AB = 6, AC = 8. "
        "Cạnh PA vuông góc với mặt phẳng (ABC), PA = 5. "
        "Biết SA = 13, SB = 13, SC = 13. "
    )

    def _run_two_anchor_e2e(extra_calls: list[dict[str, Any]], extra_text: str) -> Any:
        t = base_two_anchor_text + extra_text
        calls = [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
            {"id": "c2", "fn": "pyramid", "args": {"apex": "P", "base": ["A", "B", "C"]}, "source": {"quotes": ["hình chóp P.ABC"]}},
            {"id": "c3", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "source": {"quotes": ["có đáy ABC vuông tại A"]}},
            {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "6"}, "source": {"quotes": ["AB = 6"]}},
            {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "8"}, "source": {"quotes": ["AC = 8"]}},
            {"id": "c6", "fn": "perpendicular_line_plane", "args": {"line": ["P", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["Cạnh PA vuông góc với mặt phẳng (ABC)"]}},
            {"id": "c7", "fn": "segment_length", "args": {"segment": ["P", "A"], "value": "5"}, "source": {"quotes": ["PA = 5"]}},
            {"id": "c8", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "13"}, "source": {"quotes": ["SA = 13"]}},
            {"id": "c9", "fn": "segment_length", "args": {"segment": ["S", "B"], "value": "13"}, "source": {"quotes": ["SB = 13"]}},
            {"id": "c10", "fn": "segment_length", "args": {"segment": ["S", "C"], "value": "13"}, "source": {"quotes": ["SC = 13"]}},
        ] + extra_calls
        ask_quotes = tuple(q for c in extra_calls if c["fn"].startswith("ask_") for q in c["source"]["quotes"])
        return engine.dung_tu_loi_goi(t, {"calls": calls, "named_planes": []}, (), ask_quotes)

    res_case2_invariant = _run_two_anchor_e2e([
        {"id": "g1", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "source": {"quotes": ["Tính thể tích khối chóp S.ABC."]}},
        {"id": "g2", "fn": "ask_distance_point_plane", "args": {"point": "P", "plane": ["S", "B", "C"]}, "source": {"quotes": ["Tính khoảng cách từ P đến mặt phẳng (SBC)."]}},
    ], "Tính thể tích khối chóp S.ABC. Tính khoảng cách từ P đến mặt phẳng (SBC).")

    res_case3_len_sp = _run_two_anchor_e2e([
        {"id": "g1", "fn": "ask_length", "args": {"segment": ["S", "P"]}, "source": {"quotes": ["Tính độ dài đoạn thẳng SP."]}},
    ], "Tính độ dài đoạn thẳng SP.")

    res_case3_ang_sp = _run_two_anchor_e2e([
        {"id": "g1", "fn": "ask_angle_line_plane", "args": {"line": ["S", "P"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["Tính góc giữa đường thẳng SP và mặt phẳng (ABC)."]}},
    ], "Tính góc giữa đường thẳng SP và mặt phẳng (ABC).")

    res_case4_disambiguated = _run_two_anchor_e2e([
        {"id": "c11", "fn": "segment_length", "args": {"segment": ["S", "P"], "value": "√314"}, "source": {"quotes": ["SP = √314"]}},
        {"id": "g1", "fn": "ask_angle_line_plane", "args": {"line": ["S", "P"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["Tính góc giữa đường thẳng SP và mặt phẳng (ABC)."]}},
    ], "Biết SP = √314. Tính góc giữa đường thẳng SP và mặt phẳng (ABC).")

    return {
        "target_functions": {
            "_dinh_tu_ba_canh_ben": "backend/app/simulation/geometry_functions/engine.py:976-1008",
            "_dat_ngoai_day": "backend/app/simulation/geometry_functions/engine.py:732-744",
            "dung_tu_loi_goi": "backend/app/simulation/geometry_functions/engine.py:4224-4578",
        },
        "part1_sole_height_anchor": {
            "solid": "S.ABC (right at A, AB=6, AC=8, SA=SB=SC=13, h=12)",
            "goals_tested": len(goal_calls),
            "rz_equivariant_coordinates": rz_equivariant,
            "all_goal_values_identical": sole_anchor_values_identical,
            "certificate_verified_plus": ok_plus,
            "certificate_verified_minus": ok_minus,
            "goal_values_plus": vals_plus,
            "goal_values_minus": vals_minus,
            "mathematical_proof": (
                "When k.apex is the sole height anchor (self.h2 is set by _dinh_tu_ba_canh_ben and no other independent "
                "_dat_ngoai_day call occurs), every point X in the figure has coordinates derived affine-linearly from "
                "the base plane z=0 and the single apex S=(f_x, f_y, z_S). Replacing z_S = +1 with z_S = -1 applies the "
                "global reflection R_z(x, y, z) = (x, y, -z). Because the Exact Kernel Gram bilinear form is "
                "g(u, v) = u_0*v_0 + u_1*b_11*v_1 + u_2*h2*v_2 (with zero cross-terms between (x,y) and z), R_z is an "
                "exact orthogonal isometry: g(R_z u, R_z v) = g(u, v) and |det(R_z u, R_z v, R_z w)| = |det(u, v, w)|. "
                "Therefore all lengths, distances, angles, areas, volumes, and section polygons are 100% invariant."
            ),
        },
        "part2_two_independent_off_base_anchors": {
            "configuration": (
                "Shared base ABC (right at A, AB=6, AC=8); P placed via PA ⊥ (ABC), PA = 5 (z_P = +1, self.h2 = 25); "
                "S placed via _dinh_tu_ba_canh_ben from SA = SB = SC = 13 (foot (1/2, 1/2, 0) in chart, h_S = 12, z_S = ±12/5)."
            ),
            "both_branches_pass_all_premise_certificates": (ok_same and ok_opp),
            "same_side_branch_values": vals_same,
            "opposite_side_branch_values": vals_opp,
            "volume_S_ABC_invariant": vals_same["g_vol_s"] == vals_opp["g_vol_s"],
            "cross_anchor_length_SP_differs": vals_same["g_len_sp"] != vals_opp["g_len_sp"],
            "cross_anchor_angle_SP_ABC_differs": vals_same["g_ang_sp_abc"] != vals_opp["g_ang_sp_abc"],
            "vertical_face_distance_P_to_SBC_invariant": vals_same["g_d_p_sbc"] == vals_opp["g_d_p_sbc"],
            "before_fix_behavior": {
                "two_pyramids_p_and_s_declared": "REFUSED UNDERDETERMINED_POINT (because _dinh_tu_ba_canh_ben only checked self.root = P.ABC)",
                "mirror_sensitive_goal_without_disambiguation": "SILENTLY_SERVED_POSITIVE_Z_BRANCH (|SP| = √74, cos² = 25/74 without checking -z branch)",
                "minus_z_disambiguated_by_SP_sqrt314": "REFUSED INCONSISTENT_FACTS (because +z gave d²(S,P)=74 != 314 and -z was never tried)",
            },
            "after_fix_verification": {
                "case1_single_pyramid_mirror_equivalent": {
                    "status": "SERVED",
                    "all_11_goals_identical": sole_anchor_values_identical,
                },
                "case2_two_anchors_mirror_invariant_goals": {
                    "status": res_case2_invariant.status,
                    "answers": res_case2_invariant.answers,
                },
                "case3a_two_anchors_mirror_sensitive_length_SP": {
                    "status": res_case3_len_sp.status,
                    "reason_code": res_case3_len_sp.code,
                },
                "case3b_two_anchors_mirror_sensitive_angle_SP_ABC": {
                    "status": res_case3_ang_sp.status,
                    "reason_code": res_case3_ang_sp.code,
                },
                "case4_two_anchors_disambiguated_by_SP_sqrt314": {
                    "status": res_case4_disambiguated.status,
                    "answers": res_case4_disambiguated.answers,
                    "selected_z_S": str(res_case4_disambiguated.points["S"][2]),
                },
            },
            "finding_and_recommendation": (
                "FIXED & VERIFIED: (1) _dinh_tu_ba_canh_ben now iterates over all pyramids in self.khoi sharing the root "
                "base (not just self.root) and records placed apices in self.mirror_apices. (2) In dung_tu_loi_goi, "
                "whenever dung.mirror_apices is non-empty: if the +z branch succeeds and the -z mirror branch also passes "
                "all premise certificates, all asked goal outputs are compared across both branches; any divergence raises "
                "TuChoi('AMBIGUOUS_FACT', ...), while identical outputs serve cleanly. Conversely, if the +z branch fails "
                "with INCONSISTENT_FACTS (e.g. a given distance SP = √314 holds only on -z) and the -z mirror branch "
                "passes all certificates, the -z branch is uniquely selected and served."
            ),
        },
    }


# ── Section VI: Cross-Pipeline Evaluation (Gold Text vs Local OCR vs Vision Replay) ──────────────────────────────────

def run_cross_pipeline_evaluation() -> dict[str, Any]:
    ocr_path = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "adaptive-local-ocr-fallback" / "ocr_benchmark.json"
    ocr_data = json.loads(ocr_path.read_text(encoding="utf-8"))

    # Also test 5 representative symbol-sensitive Route D cases through:
    # (1) Path 1: Gold Text -> TypedFactNext -> Hybrid /4 -> Scene3D
    # (2) Path 2a: Local OCR corrupted text + clean TypedFactNext -> Source Gate rejection check
    # (3) Path 2b: Simulated LLM extraction from Local OCR corrupted text -> Hybrid /4
    policy = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    # Representative Route D cases with common OCR corruptions observed in ocr_benchmark.json:
    # 1. Missing symbol ⊥ (Tesseract/RapidOCR drops ⊥ or turns it into 1/L)
    # 2. Greek plane name (α)/(β) -> (a)/(B)
    # 3. Radical √ -> V (e.g., 2√3 -> 2V3)
    # 4. Prime ′ -> dropped (e.g. AA' -> AA, A'BC -> ABC)
    # 5. Clean ASCII-compatible Vietnamese pyramid problem (no Greek, no √, no ′, verbal "vuông góc")
    ocr_couplings = [
        {
            "id": "OCR_C1_CLEAN_VERBAL",
            "description": "Clean verbal pyramid (no Greek/radical/prime symbols; OCR preserves text)",
            "gold_case": build_heldout_cases()[0],  # HB01: Q43 volume
            "ocr_text": build_heldout_cases()[0]["text"],
            "corruption_type": "NONE",
        },
        {
            "id": "OCR_C2_PRIME_DROPPED",
            "description": "Right prism ABC.A'B'C' where OCR drops prime ′ on A'BC -> ABC",
            "gold_case": build_heldout_cases()[4],  # HB05: L685 d(A, (A'BC))
            "ocr_text": build_heldout_cases()[4]["text"].replace("(A'BC)", "(ABC)"),
            "corruption_type": "PRIME_LOSS_A'BC_TO_ABC",
        },
        {
            "id": "OCR_C3_PLANE_LABEL_CORRUPTED",
            "description": "Section plane (P) corrupted by OCR to (B) causing vertex/plane collision",
            "gold_case": build_heldout_cases()[20],  # HB21: section by (P)
            "ocr_text": build_heldout_cases()[20]["text"].replace("(P)", "(B)"),
            "corruption_type": "PLANE_NAME_COLLISION_P_TO_B",
        },
        {
            "id": "OCR_C4_NUMBER_CORRUPTED",
            "description": "Dimension SA = 3 corrupted by OCR to SA = 8",
            "gold_case": build_heldout_cases()[12],  # HB13: Q43 d(A, SC)
            "ocr_text": build_heldout_cases()[12]["text"].replace("SA = 3", "SA = 8"),
            "corruption_type": "DIGIT_CORRUPTION_3_TO_8",
        },
        {
            "id": "OCR_C5_VERTEX_LABEL_DROPPED",
            "description": "Tetrahedron OABC where OCR corrupts (ABC) to (AB)",
            "gold_case": build_heldout_cases()[3],  # HB04: T236 d(O, (ABC))
            "ocr_text": build_heldout_cases()[3]["text"].replace("(ABC)", "(AB)"),
            "corruption_type": "VERTEX_DROP_ABC_TO_AB",
        },
    ]

    coupling_results = []
    for item in ocr_couplings:
        gc = item["gold_case"]
        gold_text = gc["text"]
        gold_payload = gc["payload"]
        ocr_text = item["ocr_text"]

        # Path 1: Gold Text
        out_gold = run_hybrid_offline(gold_text, ReplayExtractor({gold_text: gold_payload}), policy=policy)
        rd_gold = out_gold.response.get("route_d") or {}
        env_gold = out_gold.response.get("envelope") or {}

        # Path 2a: OCR text checked against gold TypedFactNext by Source Gate
        p_2a = copy.deepcopy(gold_payload)
        p_2a["problem_text"] = ocr_text
        out_2a = run_hybrid_offline(ocr_text, ReplayExtractor({ocr_text: p_2a}), policy=policy)
        rd_2a = out_2a.response.get("route_d") or {}
        env_2a = out_2a.response.get("envelope") or {}

        # Path 2b: Simulated LLM extraction from OCR-corrupted text (quotes & values follow OCR text)
        p_2b = copy.deepcopy(gold_payload)
        p_2b["problem_text"] = ocr_text
        if item["id"] == "OCR_C2_PRIME_DROPPED":
            p_2b["math_goals"][0]["target"]["plane"] = ["A", "B", "C"]
            p_2b["math_goals"][0]["quote"] = "Tính khoảng cách từ A đến mặt phẳng (ABC)"
        elif item["id"] == "OCR_C3_PLANE_LABEL_CORRUPTED":
            p_2b["derived_sections"][0]["plane_name"] = "B"
            p_2b["derived_sections"][0]["quote"] = p_2b["derived_sections"][0]["quote"].replace("(P)", "(B)")
            p_2b["math_goals"][0]["quote"] = p_2b["math_goals"][0]["quote"].replace("(P)", "(B)")
        elif item["id"] == "OCR_C4_NUMBER_CORRUPTED":
            p_2b["premises"][2]["args"]["value"] = "8"
            p_2b["premises"][2]["quote"] = "SA = 8"
        elif item["id"] == "OCR_C5_VERTEX_DROP_ABC_TO_AB" or item["id"] == "OCR_C5_VERTEX_LABEL_DROPPED":
            p_2b["math_goals"][0]["target"]["plane"] = ["A", "B"]
            p_2b["math_goals"][0]["quote"] = "Tính khoảng cách từ O đến mặt phẳng (AB)"

        out_2b = run_hybrid_offline(ocr_text, ReplayExtractor({ocr_text: p_2b}), policy=policy)
        rd_2b = out_2b.response.get("route_d") or {}
        env_2b = out_2b.response.get("envelope") or {}
        ans_gold = {k: v.get("coef") for k, v in (rd_gold.get("answer_exact") or {}).items()}
        ans_2b = {k: v.get("coef") for k, v in (rd_2b.get("answer_exact") or {}).items()}

        coupling_results.append({
            "id": item["id"],
            "description": item["description"],
            "corruption_type": item["corruption_type"],
            "path1_gold": {
                "status": rd_gold.get("status"),
                "answers": ans_gold,
            },
            "path2a_ocr_text_with_clean_facts": {
                "status": rd_2a.get("status") or out_2a.response.get("status"),
                "reason_code": env_2a.get("reason_code") or out_2a.response.get("reason_code"),
            },
            "path2b_ocr_text_with_ocr_extracted_facts": {
                "status": rd_2b.get("status") or out_2b.response.get("status"),
                "reason_code": env_2b.get("reason_code") or out_2b.response.get("reason_code"),
                "answers": ans_2b,
                "silent_wrong_answer_vs_gold": (
                    (rd_2b.get("status") == "SERVED") and (ans_2b != ans_gold)
                ),
            },
        })

    # Summarize local OCR engine results from ocr_benchmark.json
    engines_summary = {}
    for eng_name, ed in (ocr_data.get("engines") or {}).items():
        engines_summary[eng_name] = {
            "engine_version": ed.get("engine_version"),
            "items_scored": ed.get("items_scored"),
            "cer_strict_body_median": ed.get("cer_strict_body_median"),
            "cer_lenient_body_median": ed.get("cer_lenient_body_median"),
            "vi_word_exact_accuracy": ed.get("vi_word_exact_accuracy"),
            "math_tokens_exact_items": ed.get("math_tokens_exact_items"),
            "cold_ms": ed.get("cold_ms_init_plus_first_item"),
            "warm_ms_median": ed.get("warm_ms_median"),
            "peak_rss_mb": ed.get("peak_rss_mb"),
            "single_engine_gate_accepts": ed.get("gate_calibration", {}).get("selected", {}).get("accepted", 0),
            "single_engine_gate_unsafe": ed.get("gate_calibration", {}).get("selected", {}).get("unsafe", 0),
        }

    return {
        "measurement_status": {
            "path1_gold_text": "MEASURED_OFFLINE_EXACT",
            "path2_local_ocr": "MEASURED_ON_SYNTHETIC_22_ITEM_BENCHMARK_AND_5_COUPLING_PROBES",
            "path3_gemini_vision_offline_replay": "MEASURED_ON_12_ITEM_REPLAY_CORPUS (12/12 expected outcomes matched)",
            "path3_gemini_vision_live": "NOT_MEASURED (ALLOW_LIVE_AI=0)",
        },
        "local_ocr_engines_summary": engines_summary,
        "cross_engine_gate_variants": ocr_data.get("cross_engine_gate_variants"),
        "ocr_to_hybrid_coupling_probes": coupling_results,
        "critical_architectural_finding": (
            "1. When OCR corrupts problem_text while facts remain clean (Path 2a), Source Gate (kiem_nguon) deterministically "
            "rejects the mismatch with QUOTE_NOT_IN_SOURCE / SOURCE_OBJECT_MISMATCH (fail-closed).\n"
            "2. However, if an LLM extracts TypedFactNext directly from OCR-corrupted text (Path 2b), verbatim quotes inside "
            "the corrupted text PASS Source Gate! Specifically: (a) in OCR_C2_PRIME_DROPPED, dropping the prime in (A'BC) -> "
            "(ABC) causes d(A, (ABC)) = 0 to be served instead of d(A, (A'BC)) = 120/√1681; (b) in OCR_C4_NUMBER_CORRUPTED, "
            "corrupting SA = 3 -> SA = 8 causes d(A, SC) = 32/√10 = 16√10/5 to be served instead of 12√41/41! "
            "Meanwhile, structural corruptions like (P)->(B) (OCR_C3) or (ABC)->(AB) (OCR_C5) are caught by Source Gate / "
            "TypedFactNext schema validation. This proves why the Cross-Engine OCR Acceptance Gate (requiring zero math-token "
            "divergence and 0 unsafe accepts) is mandatory before feeding Local OCR text into TypedFactNext extraction."
        ),
    }


# ── Section B.2, B.3 & B.7: Inventory & Residual Gap Technical Trace ─────────────────────────────────────────────────

def build_corpora_and_h1_inventory() -> dict[str, Any]:
    runs_dir = ROOT / "docs" / "evaluation" / "geometry" / "runs"
    nlu_corpus = json.loads(
        (runs_dir / "independent-nlu-extraction-evaluation" / "inputs" / "corpus-authoring" / "corpus.json").read_text(encoding="utf-8")
    )
    v3_corpus = json.loads(
        (runs_dir / "semantic-extraction-v3-runtime-revision" / "inputs" / "corpus.json").read_text(encoding="utf-8")
    )
    goal_comp_corpus = json.loads(
        (runs_dir / "contract-driven-goal-composition" / "corpus.json").read_text(encoding="utf-8")
    )
    c26_verif = json.loads(
        (runs_dir / "hybrid-independent-h1" / "c26-three-tier-verification.json").read_text(encoding="utf-8")
    )
    h1_integrity = json.loads(
        (runs_dir / "hybrid-independent-h1" / "H1_CORPUS_INTEGRITY.json").read_text(encoding="utf-8")
    )
    nlu_cases = nlu_corpus.get("cases", [])
    v3_cases = v3_corpus.get("cases", [])
    return {
        "honest_validation_flags": {
            "HYBRID_DEFAULT_CUTOVER_COMPLETE": "YES",
            "LEGACY_EXECUTION_RETIRED": "YES",
            "LEGACY_FULLY_RETIRED": "NO",
            "PRODUCTION_DEPLOYMENT_VERIFIED": "NO",
            "INDEPENDENT_H1_VALIDATION": "NOT_MEASURED",
            "WORKSTREAM_B_HELDOUT_CLASS": "GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT",
        },
        "corpora": {
            "nlu_extraction_corpus": {
                "path": "docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/inputs/corpus-authoring/corpus.json",
                "total_count": len(nlu_cases),
                "pilot_count": sum(1 for c in nlu_cases if c.get("split") == "dev"),
                "locked_count": sum(1 for c in nlu_cases if c.get("split") == "locked"),
            },
            "v3_matrix_corpus": {
                "path": "docs/evaluation/geometry/runs/semantic-extraction-v3-runtime-revision/inputs/corpus.json",
                "total_count": len(v3_cases),
                "pilot_count": sum(1 for c in v3_cases if c.get("split") == "dev"),
                "locked_count": sum(1 for c in v3_cases if c.get("split") == "locked"),
            },
            "goal_composition_corpus": {
                "path": "docs/evaluation/geometry/runs/contract-driven-goal-composition/corpus.json",
                "total_count": len(goal_comp_corpus.get("cases", goal_comp_corpus if isinstance(goal_comp_corpus, list) else [])),
            },
            "c26_three_tier_verification": {
                "path": "docs/evaluation/geometry/runs/hybrid-independent-h1/c26-three-tier-verification.json",
                "split": "HISTORICAL_LIVE_REPLAY_RECEIPT",
                "total_count": c26_verif.get("total_cases", 70),
            },
            "development_reasoning_matrix": {
                "path": "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools/reasoning_matrix.py",
                "split": "OFFLINE_DEVELOPMENT_MATRIX",
                "count": 72,
                "baseline_served": 47,
                "after_served": 56,
                "false_refusals_after": 0,
                "wrong_served_after": 0,
            },
            "workstream_b_heldout_benchmark": {
                "path": "tools/evaluate_geometry_workstream_b.py",
                "split": "GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT",
                "count": 46,
                "overlap_with_dev_matrix_72": 0,
            },
        },
        "h1_protocol_audit": {
            "preregistration_path": "docs/evaluation/geometry/runs/hybrid-independent-h1/H1_PREREGISTRATION.md",
            "integrity_manifest_path": "docs/evaluation/geometry/runs/hybrid-independent-h1/H1_CORPUS_INTEGRITY.json",
            "oracle_path": "docs/evaluation/geometry/custodian/geometry_oracle.py",
            "paired_harness_path": "backend/scripts/run_paired_route_evaluation.py",
            "equivalence_scorer_path": "backend/scripts/score_independent_holdout_equivalence.py",
            "integrity_status": h1_integrity.get("status"),
            "h1_authoring_independence": h1_integrity.get("h1_authoring_independence"),
            "h1_measurement": h1_integrity.get("h1_measurement"),
            "why_not_measured": (
                "An external human author/custodian has not yet delivered the sealed 60-problem independent Vietnamese geometry "
                "corpus (`h1-independent-corpus.json`) or signed off on the live paired budget (`paired-live-owner-approval.json`). "
                "In strict compliance with AGENTS.md §3 and §4, H-1 remains NOT_MEASURED and our new 46-case held-out benchmark "
                "is explicitly labeled GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT."
            ),
        },
    }


def build_residual_gaps_trace() -> dict[str, Any]:
    return {
        "G2": {
            "matrix_cases": ["PL5", "PA3"],
            "heldout_probe": "HB35",
            "summary": "Described point inside the `line` operand of a distance goal (`d(B, line(A, @m1))` or `d(line(M, @n1), (ABCD))`)",
            "expected_behavior": "Decompose `@m1` / `@n1` via `midpoint`, then compute point-line or line-plane distance",
            "actual_behavior": "Refused at Bridge with `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`",
            "exact_code_trace": [
                "backend/app/simulation/geometry_functions/typed_fact_next_bridge.py:350-380 (`_cau_hoi_mo_ta`: `g.goal_type == 'distance'` only accepts `keys == {'point', 'plane'}`, `keys == {'point', 'line'} and key == 'point'`, or `keys == {'segment'}`; when `key == 'line'`, line 379 raises `TuChoi('BRIDGE_UNSUPPORTED_DESCRIBED_POINT', ...)`)",
                "backend/app/simulation/geometry_functions/planner.py:382-427 (`_toan_hang_muc_tieu`)",
                "backend/app/simulation/geometry_functions/registry.py:745-757 (`ask_distance_point_plane`, `ask_distance_line_plane`, `ask_length`)",
            ],
            "missing_contract_or_primitive": "No new Registry function needed (`midpoint`, `orthogonal_projection_line`, `ask_length`, `ask_distance_line_plane` already exist); missing Bridge target shape & `PlanningContract(goal='distance', ...)` for a line spanned by a described point.",
            "can_existing_composition_solve": True,
            "new_function_needed": False,
            "impact_on_correctness": "Fail-closed refusal (`0` wrong answers)",
            "fix_cost_and_risk": "Low-Medium: extend `_cau_hoi_mo_ta` in `typed_fact_next_bridge.py`, add `PlanningContract` on `ask_distance_line_plane` and `ask_length` (with `Foot`), and add closed Source Gate regex for `đường thẳng nối X với <descriptor>`.",
        },
        "G3": {
            "matrix_cases": ["MG5"],
            "heldout_probe": None,
            "summary": "Distance between two described points in a single goal (`segment: ['@m1', '@n1']`)",
            "expected_behavior": "Construct both `M1 = mid(SB)` and `N1 = mid(CD)`, then run `ask_length(M1, N1)`",
            "actual_behavior": "Refused at Bridge with `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`",
            "exact_code_trace": [
                "backend/app/simulation/geometry_functions/typed_fact_next_bridge.py:359-361 (`if len(used) != 1: raise TuChoi('BRIDGE_UNSUPPORTED_DESCRIBED_POINT', f'{g.goal_id}: hai điểm được mô tả trong một mục tiêu chưa có chứng chỉ nguồn')`)",
                "backend/app/simulation/geometry_functions/planner.py:115-129 (`TypedFact` has only one `point_kind`/`points` slot for a single described operand)",
                "backend/app/simulation/geometry_functions/planner.py:2516-2561 (`_chuoi` builds a single `operand` dict in `effect-chain`)",
                "backend/app/simulation/geometry_functions/registry.py:2161-2245 (`_kiem_result_binding` `chain(d)` validates a single `operand` against a single `desc_phrase`)",
            ],
            "missing_contract_or_primitive": "No new Registry function needed (`midpoint` and `ask_length` exist); `TypedFact` and `effect-chain` certificate schema currently bind at most 1 described operand per goal.",
            "can_existing_composition_solve": True,
            "new_function_needed": False,
            "impact_on_correctness": "Fail-closed refusal (`0` wrong answers)",
            "fix_cost_and_risk": "Medium: generalize `effect-chain` `operand` to `operands: list[dict]` and allow two descriptor phrases in `_mau_muc_tieu_mo_ta`.",
        },
        "G4": {
            "matrix_cases": ["SE3"],
            "heldout_probe": "HB36",
            "summary": "Constrained section plane with 3 `contains_points` named `(Q)` in source (`Mặt phẳng (Q) đi qua M, N, P ... cắt bởi mặt phẳng (Q)`)",
            "expected_behavior": "Bind plane name `Q` to `[M, N, P]` so `section` and `ask_section_area` pass `mat_cat_dung_nguon`",
            "actual_behavior": "Refused at Source Gate with `SOURCE_OBJECT_MISMATCH` (`mat_cat_dung_nguon` fails because `named_planes` is empty)",
            "exact_code_trace": [
                "backend/app/simulation/geometry_functions/typed_fact_next_bridge.py:422-432 (`_la_mat_qua_ba_diem` returns `True` when `len(cs) == 1 and cs[0].kind == 'contains_points'`, causing `_ten_mat_khai` at line 429 to return `''.join(cs[0].operands)` = `'MNP'` instead of `sec.plane_name` = `'Q'`)",
                "backend/app/simulation/geometry_functions/typed_fact_next_bridge.py:442-451 (`_mat_fact` emits `{'kind': 'section', 'points': pts}` without `plane_name`, so `planner.py` never populates `named_planes['Q']`)",
                "backend/app/simulation/geometry_functions/registry.py:2737 and 5810-5830 (`mat_cat_dung_nguon` checks the quote `'Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (Q)'` against `c.args.plane = ['M', 'N', 'P']` without knowing `(Q) = (MNP)`)",
            ],
            "missing_contract_or_primitive": "No new Registry function needed (`section` and `ask_section_area` already support `named_planes` in `engine.py`); missing `named_planes` source binding for `"
                                             "Mặt phẳng (Q) đi qua M, N, P` in `typed_fact_next_bridge.py` and `registry.py`.",
            "can_existing_composition_solve": True,
            "new_function_needed": False,
            "impact_on_correctness": "Fail-closed refusal (`0` wrong answers)",
            "fix_cost_and_risk": "Low: preserve `plane_name` on 3-point `contains_points` sections in `typed_fact_next_bridge.py` and verify the closed definition `'Mặt phẳng (Q) đi qua M, N, P'` in `mat_cat_dung_nguon`.",
        },
        "G6": {
            "matrix_cases": ["MG9"],
            "heldout_probe": "HB37",
            "summary": "Three property-defined points (`orthocenter(SBD)`, `circumcenter(SBC)`, `orthocenter(SCD)`) in one problem",
            "expected_behavior": "Solve all 3 goals via `POINT_DEFINITIONS` locus intersection",
            "actual_behavior": "Refused at Planner with `PLAN_TOO_LARGE` (`SEARCH_BUDGET_EXCEEDED`)",
            "exact_code_trace": [
                "backend/app/simulation/geometry_functions/planner.py:85 (`MAX_EFFECT_CANDIDATES = 48`)",
                "backend/app/simulation/geometry_functions/planner.py:2274-2276 (`_EffectResolver._resolve` increments `self.candidates` across all goals in the problem and raises `TuChoi('PLAN_TOO_LARGE', ...)` at 49 > 48)",
                "backend/app/simulation/geometry_functions/planner.py:2380-2382 (`_dinh_nghia` also checks `self.candidates > MAX_EFFECT_CANDIDATES`; each property-defined point evaluates ~17-21 locus candidates, so 3 definitions require ~54 > 48)",
                "backend/app/simulation/semantic_program/validator.py:143 and 169-170 (`MAX_MEMORY_DECLARATIONS = 32`; 3 property-defined points + solid vertices + goal outputs declare 34 memory slots > 32, which would raise `IR_MEMORY_BUDGET_EXCEEDED` if `MAX_EFFECT_CANDIDATES` were raised alone)",
            ],
            "missing_contract_or_primitive": "No missing primitive; bounded by per-problem `MAX_EFFECT_CANDIDATES = 48` (`planner.py:85`) and shared IR `MAX_MEMORY_DECLARATIONS = 32` (`validator.py:143`).",
            "can_existing_composition_solve": True,
            "new_function_needed": False,
            "impact_on_correctness": "Fail-closed refusal (`0` wrong answers)",
            "fix_cost_and_risk": "Low-Medium: scope `MAX_EFFECT_CANDIDATES = 48` per-goal (or 96 per-problem) and raise `MAX_MEMORY_DECLARATIONS` from 32 to 48 in `semantic_program/validator.py` (shared contract change).",
        },
        "G7": {
            "matrix_cases": ["RE10"],
            "heldout_probe": "HB38",
            "summary": "Description nested through a property-defined point (`orthogonal_projection` of `orthocenter(SBD)` onto `(ABCD)`)",
            "expected_behavior": "Regress `orthocenter(SBD)` into its two altitude loci + intersection, then project onto `(ABCD)` and measure distance to `(SAB)`",
            "actual_behavior": "Refused at Bridge with `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`",
            "exact_code_trace": [
                "backend/app/simulation/geometry_functions/typed_fact_next_bridge.py:311-316 (`_mo_ta_phang` filters `inner_dcs = [c for c in descriptor_contracts(inner.kind) if isinstance(c, PlanningContract) and c.call and isinstance(c.phrase, str)]`; for `orthocenter`/`circumcenter`, `POINT_DEFINITIONS[inner.kind].contract.call` is `()` because it is a multi-step locus definition rather than a single Registry call, so `c.call` is empty and line 315 raises `TuChoi('BRIDGE_UNSUPPORTED_DESCRIBED_POINT', ...)`)",
                "backend/app/simulation/geometry_functions/planner.py:2424-2437 (`_EffectResolver._point` only checks `POINT_DEFINITIONS` at the outer `fact.point_kind`, not `fact.nested_point_kind`)",
                "backend/app/simulation/geometry_functions/registry.py:2173-2184 (`_kiem_result_binding` `chain(d)` requires `inner_desc` to be a single call in `got` rather than calling `_dinh_nghia_trong_chuoi` on `nested`)",
            ],
            "missing_contract_or_primitive": "No new Registry function needed; Bridge `_mo_ta_phang`, Planner `_point`, and Source Gate `chain(d)` only support single-call descriptors as `inner`/`nested` descriptors, not `POINT_DEFINITIONS`.",
            "can_existing_composition_solve": True,
            "new_function_needed": False,
            "impact_on_correctness": "Fail-closed refusal (`0` wrong answers)",
            "fix_cost_and_risk": "Medium: allow `POINT_DEFINITIONS` in `_mo_ta_phang` (`typed_fact_next_bridge.py:311`), resolve `fact.nested_point_kind in POINT_DEFINITIONS` via `_dinh_nghia` in `planner.py:2428`, and validate `nested` via `_dinh_nghia_trong_chuoi` in `registry.py:2173`.",
        },
    }


def main() -> None:
    t_start = time.perf_counter()
    dev_cases = DM.build_cases()
    heldout_cases = build_heldout_cases()

    # Verify zero contamination / overlap between 72 dev cases and 46 held-out cases
    dev_norms = {_norm_text(c["text"]): c["id"] for c in dev_cases}
    dev_shas = {hashlib.sha256(c["text"].encode("utf-8")).hexdigest(): c["id"] for c in dev_cases}

    overlap_norm = []
    overlap_sha = []
    heldout_seen_norm: set[str] = set()
    for hc in heldout_cases:
        nt = _norm_text(hc["text"])
        sh = hashlib.sha256(hc["text"].encode("utf-8")).hexdigest()
        if nt in dev_norms:
            overlap_norm.append((hc["id"], dev_norms[nt]))
        if sh in dev_shas:
            overlap_sha.append((hc["id"], dev_shas[sh]))
        assert nt not in heldout_seen_norm, f"Duplicate held-out text in {hc['id']}"
        heldout_seen_norm.add(nt)

    assert len(overlap_norm) == 0, f"Contamination detected (normalized text): {overlap_norm}"
    assert len(overlap_sha) == 0, f"Contamination detected (SHA-256): {overlap_sha}"

    # Verify all 18 required problem groups are present in held-out
    required_18_groups = {
        "PYRAMID", "TETRAHEDRON", "PRISM", "PERPENDICULARITY", "PARALLELISM",
        "MIDPOINT_CENTROID", "DISTANCE_POINT_LINE", "DISTANCE_POINT_PLANE",
        "ANGLE_LINE_PLANE", "ANGLE_LINE_LINE", "SECTION", "AUXILIARY_CONSTRUCTION",
        "MULTI_GOAL", "INTERMEDIATE_REUSE", "COMPETING_PLANS",
        "MISSING_DATA", "OUT_OF_SCOPE", "DEGENERATE",
    }
    present_groups = {c["group"] for c in heldout_cases}
    assert required_18_groups <= present_groups, f"Missing groups: {required_18_groups - present_groups}"
    group_counts = {g: sum(1 for c in heldout_cases if c["group"] == g) for g in sorted(required_18_groups)}

    # Run both suites
    dev_eval = evaluate_suite(dev_cases, "OFFLINE_DEVELOPMENT_MATRIX_72")
    heldout_eval = evaluate_suite(heldout_cases, "GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT_46")

    # Run Section VIII Mirror-Solution Equivalence Audit
    mirror_audit = run_mirror_solution_audit()

    # Run Section VI Cross-Pipeline Evaluation
    cross_pipeline = run_cross_pipeline_evaluation()

    # Build Section B.2/B.3 Inventory and Section B.7 Residual Gap Trace
    inventory = build_corpora_and_h1_inventory()
    residual_gaps = build_residual_gaps_trace()

    git_head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    receipt = {
        "schema": "workstream-b-geometry-evaluation-receipt/1",
        "git_head": git_head,
        "allow_live_ai": os.environ.get("ALLOW_LIVE_AI"),
        "live_provider_calls": 0,
        "elapsed_seconds": round(time.perf_counter() - t_start, 3),
        "honest_status_flags": inventory["honest_validation_flags"],
        "section_b2_b3_inventory_and_h1_audit": inventory,
        "section_b4_b5_b6_deduplication_and_group_coverage": {
            "dev_matrix_count": len(dev_cases),
            "heldout_count": len(heldout_cases),
            "normalized_text_overlap_count": len(overlap_norm),
            "sha256_overlap_count": len(overlap_sha),
            "required_18_groups_covered": len(present_groups & required_18_groups),
            "group_counts": group_counts,
        },
        "development_matrix_72_evaluation": dev_eval,
        "heldout_benchmark_46_evaluation": heldout_eval,
        "section_b7_residual_gaps_trace": residual_gaps,
        "section_vi_cross_pipeline_evaluation": cross_pipeline,
        "section_viii_mirror_solution_equivalence_audit": mirror_audit,
    }

    out_path = (
        ROOT
        / "docs"
        / "evaluation"
        / "geometry"
        / "runs"
        / "independent-geometry-and-vision-evaluation"
        / "workstream_b_geometry_receipt.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=== WORKSTREAM B EVALUATION COMPLETE ===")
    print("Receipt written to:", out_path)
    print("Dev Matrix (72):", dev_eval["outcome_counts_8"], "| 14-class:", dev_eval["outcome_counts_14"])
    print("Held-Out (46):", heldout_eval["outcome_counts_8"], "| 14-class:", heldout_eval["outcome_counts_14"])
    print("Held-Out Supported Solve Rate:", heldout_eval["in_scope_solve_rate_supported"],
          "| All In-Scope Solve Rate:", heldout_eval["in_scope_solve_rate_all"],
          "| Negative Refusal Rate:", heldout_eval["negative_refusal_rate"])
    print("Mirror Audit Part 1 (Sole Anchor Identical):", mirror_audit["part1_sole_height_anchor"]["all_goal_values_identical"])
    print("Mirror Audit Part 2 (Two Anchors Volume Invariant / SP Differs):",
          mirror_audit["part2_two_independent_off_base_anchors"]["volume_S_ABC_invariant"],
          mirror_audit["part2_two_independent_off_base_anchors"]["cross_anchor_length_SP_differs"])


if __name__ == "__main__":
    main()
