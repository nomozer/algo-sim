"""Hybrid /4: section of a solid by the plane through three named points, end to end (TypedFactNext /2 → bridge_v2 →
Source Gate → planner → engine → Adapter /4 → Scene3D), checked against an INDEPENDENT oracle.

The oracle below is written separately from the engine and uses a different algorithm: hand-entered Euclidean
coordinates, exact edge–plane intersections over the solid's finite edges, de-duplication, then the polygon area from
the vector cross-sum. It never reads engine output. Cases differ in vertex names, base shape, solid kind, which edges the
plane cuts (interior point, a vertex of the solid), section size (3–6 vertices) and wording; refusals cover collinear,
repeated and unknown points and contradictory data. No case is selected by name in product code: the bridge rule is
"a `constrained` plane whose ONLY constraint is `contains_points` of three labels".
"""
from __future__ import annotations

import math
import re
from fractions import Fraction as F

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
AREA_Q = "Tính diện tích thiết diện đó"


# ── independent oracle ────────────────────────────────────────────────────────────────────────────────────────────────
def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def oracle_section(vertices: dict, edges: list, plane: tuple) -> dict:
    """Exact section of a convex solid (given by its finite edges) by the plane through three points."""
    p1, p2, p3 = (tuple(F(x) for x in q) for q in plane)
    n = _cross(_sub(p2, p1), _sub(p3, p1))
    if n == (0, 0, 0):
        return {"collinear": True}
    pts = []
    for a, b in edges:
        A, B = (tuple(F(x) for x in vertices[a]), tuple(F(x) for x in vertices[b]))
        da, db = _dot(n, _sub(A, p1)), _dot(n, _sub(B, p1))
        cand = ([A] if da == 0 else []) + ([B] if db == 0 else [])
        if da * db < 0:
            t = da / (da - db)
            cand.append(tuple(x + t * (y - x) for x, y in zip(A, B)))
        pts += [c for c in cand if c not in pts]
    if len(pts) < 3:
        return {"vertices": len(pts), "area2": F(0)}
    k = max(range(3), key=lambda i: abs(n[i]))                     # drop the dominant axis to order the polygon
    u, v = [i for i in range(3) if i != k]
    cx, cy = (sum(p[u] for p in pts) / len(pts), sum(p[v] for p in pts) / len(pts))
    pts.sort(key=lambda p: math.atan2(float(p[v] - cy), float(p[u] - cx)))
    s = (0, 0, 0)
    for i in range(len(pts)):
        s = tuple(x + y for x, y in zip(s, _cross(pts[i], pts[(i + 1) % len(pts)])))
    return {"vertices": len(pts), "area2": _dot(s, s) / 4}


def coef_squared(coef: str) -> F:
    m = re.fullmatch(r"(\d+)?(?:√(\d+))?(?:/(\d+))?", coef)
    assert m and coef, f"unexpected exact form {coef!r}"
    a, r, d = int(m[1] or 1), int(m[2] or 1), int(m[3] or 1)
    return F(a * a * r, d * d)


def pyramid_edges(apex, base):
    return [(base[i], base[(i + 1) % len(base)]) for i in range(len(base))] + [(apex, b) for b in base]


def prism_edges(base, top):
    n = len(base)
    return ([(base[i], base[(i + 1) % n]) for i in range(n)] + [(top[i], top[(i + 1) % n]) for i in range(n)]
            + [(base[i], top[i]) for i in range(n)])


def mid(a, b):
    return tuple(F(x + y, 2) for x, y in zip(a, b))


def at(a, b, t):
    return tuple(F(x) + F(t) * (F(y) - F(x)) for x, y in zip(a, b))


# ── payload ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _payload(solid: dict, prem: list[tuple[str, dict | None]], plane: list[str], *, area: bool = True) -> tuple[str, dict]:
    sec_q = f"Xác định thiết diện của {solid['word']} {solid['notation']} cắt bởi mặt phẳng ({''.join(plane)})"
    sentences = [s for s, _ in prem if s] + [sec_q] + ([AREA_Q] if area else [])
    text = ". ".join(sentences) + "."
    premises = [{**p, "quote": p.get("quote", s), "solid_id": "s1"} for s, p in prem if p is not None]
    payload = {
        "schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": solid["type"], "notation": solid["notation"], "quote": solid["quote"]}],
        "premises": premises, "relations": [],
        "derived_sections": [{"section_id": "sec1", "target_solid_id": "s1", "quote": sec_q, "plane_kind": "constrained",
                              "constraints": [{"kind": "contains_points", "operands": plane}], "stated_intersections": []}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": solid["quote"]},
                             {"goal_id": "sg2", "kind": "construct_plane_section", "target_section_id": "sec1", "quote": sec_q}],
        "math_goals": ([{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"},
                         "quote": AREA_Q, "solid_id": "s1"}] if area else []),
    }
    return text, payload


def run(solid, prem, plane, **kw):
    text, payload = _payload(solid, prem, plane, **kw)
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    return out.response["envelope"], out.response["route_d"]


def seg(a, b, v):
    return (f"{a}{b} = {v}", {"kind": "segment_length", "args": {"segment": [a, b], "value": str(v)}})


def midpoint(p, a, b):
    return (f"Gọi {p} là trung điểm của {a}{b}", {"kind": "midpoint", "args": {"point": p, "segment": [a, b]}})


def divide(p, a, b, ratio, wording):
    return (f"Gọi {p} là điểm thuộc cạnh {a}{b} sao cho {wording}",
            {"kind": "divide_segment", "args": {"point": p, "segment": [a, b], "ratio": ratio}})


def square_pyramid(apex, base, side, h, word_extra=""):
    a = base[0]
    q = f"Cho hình chóp {apex}.{''.join(base)}"
    return ({"type": "pyramid", "notation": f"{apex}.{''.join(base)}", "quote": q, "word": "hình chóp"},
            [(f"{q} có đáy {''.join(base)} là hình vuông cạnh {side}",
              {"kind": "regular_polygon", "args": {"vertices": list(base), "side": str(side)},
               "quote": f"đáy {''.join(base)} là hình vuông cạnh {side}"}),
             (f"{apex}{a} vuông góc với mặt phẳng ({''.join(base)})",
              {"kind": "perpendicular_line_plane", "args": {"line": [apex, a], "plane": list(base)}}),
             seg(apex, a, h)])


def right_prism(base, ab, ac, h):
    a, b, c = base
    top = [x + "'" for x in base]
    name = "".join(base) + "." + "".join(top)
    q = f"Cho lăng trụ đứng {name}"
    shape = f"Đáy {''.join(base)} là tam giác vuông tại {a}"
    return ({"type": "prism", "notation": name, "quote": q, "word": "lăng trụ"},
            [(q, {"kind": "right_prism", "args": {"base": list(base), "top": top}}),
             (shape, {"kind": "right_angle", "args": {"vertex": a, "rays": [b, c]}}),
             seg(a, b, ab), seg(a, c, ac), seg(a, a + "'", h)])


# ── cases with hand coordinates ───────────────────────────────────────────────────────────────────────────────────────
def _case_c():
    solid, prem = square_pyramid("S", "ABCD", 2, 4)
    prem += [divide("M", "S", "A", "3/4", "SM = 3MA"), divide("N", "S", "B", "3/8", "SN = 3/5 NB"), midpoint("P", "S", "C")]
    V = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 4)}
    plane = (at(V["S"], V["A"], F(3, 4)), at(V["S"], V["B"], F(3, 8)), mid(V["S"], V["C"]))
    return solid, prem, ["M", "N", "P"], V, pyramid_edges("S", "ABCD"), plane


def _renamed_square_pyramid():
    solid, prem = square_pyramid("T", "EFGH", 3, 6)
    prem += [midpoint("I", "T", "E"), divide("J", "T", "F", "2/3", "TJ = 2JF"), midpoint("K", "T", "G")]
    V = {"E": (0, 0, 0), "F": (3, 0, 0), "G": (3, 3, 0), "H": (0, 3, 0), "T": (0, 0, 6)}
    plane = (mid(V["T"], V["E"]), at(V["T"], V["F"], F(2, 3)), mid(V["T"], V["G"]))
    return solid, prem, ["I", "J", "K"], V, pyramid_edges("T", "EFGH"), plane


def _rectangle_pyramid():
    q = "Cho hình chóp S.ABCD"
    solid = {"type": "pyramid", "notation": "S.ABCD", "quote": q, "word": "hình chóp"}
    prem = [(f"{q} có đáy ABCD là hình chữ nhật", {"kind": "rectangle", "args": {"vertices": list("ABCD")},
                                                   "quote": "đáy ABCD là hình chữ nhật"}),
            seg("A", "B", 4), seg("A", "D", 2),
            ("SA vuông góc với mặt phẳng (ABCD)", {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")}}),
            seg("S", "A", 2), midpoint("M", "S", "A"), midpoint("N", "S", "B"), midpoint("P", "S", "C")]
    V = {"A": (0, 0, 0), "B": (4, 0, 0), "C": (4, 2, 0), "D": (0, 2, 0), "S": (0, 0, 2)}
    return solid, prem, ["M", "N", "P"], V, pyramid_edges("S", "ABCD"), (mid(V["S"], V["A"]), mid(V["S"], V["B"]), mid(V["S"], V["C"]))


def _triangular_pyramid_triangle_section():
    q = "Cho hình chóp S.ABC"
    solid = {"type": "pyramid", "notation": "S.ABC", "quote": q, "word": "hình chóp"}
    prem = [(f"{q} có đáy ABC là tam giác vuông tại A", {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]},
                                                          "quote": "đáy ABC là tam giác vuông tại A"}),
            seg("A", "B", 3), seg("A", "C", 4),
            ("SA vuông góc với mặt phẳng (ABC)", {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABC")}}),
            seg("S", "A", 2), midpoint("M", "S", "A"), divide("N", "S", "B", "1/3", "SN = 1/2 NB"),
            divide("P", "S", "C", "3/4", "SP = 3PC")]
    V = {"A": (0, 0, 0), "B": (3, 0, 0), "C": (0, 4, 0), "S": (0, 0, 2)}
    return solid, prem, ["M", "N", "P"], V, pyramid_edges("S", "ABC"), (
        mid(V["S"], V["A"]), at(V["S"], V["B"], F(1, 3)), at(V["S"], V["C"], F(3, 4)))


def _plane_through_two_solid_vertices():
    solid, prem = square_pyramid("S", "ABCD", 2, 2)
    prem += [midpoint("M", "S", "A")]
    V = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 2)}
    return solid, prem, ["M", "B", "D"], V, pyramid_edges("S", "ABCD"), (mid(V["S"], V["A"]), V["B"], V["D"])


def _right_prism_mixed():
    solid, prem = right_prism("ABC", 3, 4, 2)
    prem += [midpoint("M", "A", "A'")]
    V = {"A": (0, 0, 0), "B": (3, 0, 0), "C": (0, 4, 0), "A'": (0, 0, 2), "B'": (3, 0, 2), "C'": (0, 4, 2)}
    return solid, prem, ["M", "B", "C'"], V, prism_edges(["A", "B", "C"], ["A'", "B'", "C'"]), (mid(V["A"], V["A'"]), V["B"], V["C'"])


def _oblique_prism():
    q = "Cho lăng trụ ABC.A'B'C'"
    solid = {"type": "prism", "notation": "ABC.A'B'C'", "quote": q, "word": "lăng trụ"}
    prem = [(q, None),
            ("Đáy ABC là tam giác vuông tại A", {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}}),
            seg("A", "B", 6), seg("A", "C", 8), midpoint("H", "B", "C"),
            ("Hình chiếu vuông góc của A' lên (ABC) là H",
             {"kind": "orthogonal_projection", "args": {"point": "A'", "image": "H", "plane": list("ABC")}}),
            seg("A", "A'", 13), midpoint("M", "A", "A'"), midpoint("N", "B", "B'")]
    V = {"A": (0, 0, 0), "B": (6, 0, 0), "C": (0, 8, 0), "A'": (3, 4, 12), "B'": (9, 4, 12), "C'": (3, 12, 12)}
    return solid, prem, ["M", "N", "C"], V, prism_edges(["A", "B", "C"], ["A'", "B'", "C'"]), (
        mid(V["A"], V["A'"]), mid(V["B"], V["B'"]), V["C"])


def _cube_hexagon():
    q = "Cho lăng trụ đứng ABCD.A'B'C'D'"
    top = ["A'", "B'", "C'", "D'"]
    solid = {"type": "prism", "notation": "ABCD.A'B'C'D'", "quote": q, "word": "lăng trụ"}
    prem = [(f"{q} có đáy ABCD là hình vuông cạnh 2", {"kind": "right_prism", "args": {"base": list("ABCD"), "top": top}, "quote": q}),
            (None, {"kind": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2"}),
            seg("A", "A'", 2), midpoint("U", "A", "B"), midpoint("V", "B", "C"), midpoint("W", "C", "C'")]
    V = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0),
         "A'": (0, 0, 2), "B'": (2, 0, 2), "C'": (2, 2, 2), "D'": (0, 2, 2)}
    return solid, prem, ["U", "V", "W"], V, prism_edges(list("ABCD"), top), (mid(V["A"], V["B"]), mid(V["B"], V["C"]), mid(V["C"], V["C'"]))


SERVED_CASES = {
    "case_c_pentagon_exterior_q_on_line": _case_c,
    "renamed_square_pyramid": _renamed_square_pyramid,
    "rectangle_base_quadrilateral": _rectangle_pyramid,
    "triangular_pyramid_triangle": _triangular_pyramid_triangle_section,
    "plane_through_two_solid_vertices": _plane_through_two_solid_vertices,
    "right_prism_mixed_points": _right_prism_mixed,
    "oblique_prism": _oblique_prism,
    "cube_hexagon": _cube_hexagon,
}


@pytest.mark.parametrize("name", sorted(SERVED_CASES))
def test_three_point_section_matches_the_independent_oracle(name: str) -> None:
    solid, prem, plane, V, edges, plane_xyz = SERVED_CASES[name]()
    oracle = oracle_section(V, edges, plane_xyz)
    env, route = run(solid, prem, plane)
    assert (env["status"], route["status"]) == ("ok", "SERVED"), (name, env.get("reason_code"), route.get("refusal"))
    secs = route["sections"]
    assert len(secs) == 1 and len(secs[0]["vertices"]) == oracle["vertices"], (name, secs, oracle)
    assert secs[0].get("plane_label") == f"({''.join(plane)})"
    assert coef_squared(route["answer_exact"]["q1"]["coef"]) == oracle["area2"], (name, route["answer_exact"], oracle)
    objs = env["scene3d"]["objects"]
    poly = next(o for o in objs if o["type"] == "section")["polygon"]
    assert len(poly) == oracle["vertices"]


# ── refusals ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_collinear_points_refused() -> None:
    solid, prem = square_pyramid("S", "ABCD", 2, 4)
    prem += [midpoint("M", "S", "A")]
    env, route = run(solid, prem, ["S", "M", "A"])
    assert (route["status"], route["refusal"]["code"]) == ("REFUSED", "COLLINEAR_POINTS") and not env.get("scene3d")


def test_repeated_point_refused() -> None:
    solid, prem = square_pyramid("S", "ABCD", 2, 4)
    prem += [midpoint("M", "S", "A"), midpoint("N", "S", "B")]
    env, route = run(solid, prem, ["M", "M", "N"])
    assert (route["status"], route["refusal"]["code"]) == ("REFUSED", "INVALID_DERIVED_SECTION") and not env.get("scene3d")


def test_unknown_point_refused() -> None:
    solid, prem = square_pyramid("S", "ABCD", 2, 4)
    prem += [midpoint("M", "S", "A"), midpoint("N", "S", "B")]
    env, route = run(solid, prem, ["M", "N", "K"])
    assert (route["status"], route["refusal"]["code"]) == ("REFUSED", "UNDERDETERMINED_POINT") and not env.get("scene3d")


def test_contradictory_premises_refused() -> None:
    solid, prem = square_pyramid("S", "ABCD", 2, 4)
    prem += [seg("A", "B", 3), midpoint("M", "S", "A"), midpoint("N", "S", "B"), midpoint("P", "S", "C")]
    env, route = run(solid, prem, ["M", "N", "P"])
    assert (route["status"], route["refusal"]["code"]) == ("REFUSED", "INCONSISTENT_FACTS"), route


def test_stated_intersections_on_a_three_point_plane_are_refused_not_dropped() -> None:
    solid, prem, plane, *_ = _case_c()
    text, payload = _payload(solid, prem, plane)
    payload["derived_sections"][0]["stated_intersections"] = [{"edge": ["C", "D"], "quote": payload["derived_sections"][0]["quote"]}]
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    assert out.response["route_d"]["status"] == "REFUSED"
    assert out.response["route_d"]["refusal"]["code"] in ("UNSUPPORTED_CAPABILITY", "INVALID_DERIVED_SECTION")


def test_oracle_self_check_rejects_its_own_wrong_answers() -> None:
    """The oracle is not the engine: on Case C it finds 5 vertices and area² = 363/32 (= (11√6/8)²) by hand."""
    _s, _p, _pl, V, edges, plane_xyz = _case_c()
    o = oracle_section(V, edges, plane_xyz)
    assert o == {"vertices": 5, "area2": F(363, 32)} and coef_squared("11√6/8") == F(363, 32)
    assert oracle_section(V, edges, ((0, 0, 4), (0, 0, 2), (0, 0, 0))) == {"collinear": True}


# ── wording of the plane through three named points (held-out finding of run axo-final-educational-viewer-readiness) ──
def _wording_case(phrase: str, plane=("U", "V", "W")):
    solid, prem = square_pyramid("O", "KLMN", 6, 3)
    prem += [midpoint(p, "O", b) for p, b in zip("UVW", "KLM")]
    q = f"Xác định thiết diện của hình chóp O.KLMN {phrase}"
    _t, p = _payload(solid, prem, list(plane))
    text = ". ".join([s for s, _ in prem] + [q, AREA_Q]) + "."
    p["problem_text"] = text
    p["derived_sections"][0]["quote"] = q
    p["simulation_goals"][1]["quote"] = q
    out = run_hybrid_offline(text, ReplayExtractor({text: p}), policy=POLICY)
    return out.response["envelope"], out.response["route_d"]


@pytest.mark.parametrize("phrase", [
    "cắt bởi mặt phẳng (UVW)",
    "cắt bởi mặt phẳng đi qua ba điểm U, V, W",
    "cắt bởi mặt phẳng qua U, V và W",
    "cắt bởi mặt phẳng (UVW) đi qua ba điểm U, V, W",
])
def test_plane_through_three_points_is_grounded_in_every_standard_wording(phrase: str) -> None:
    V = {"K": (0, 0, 0), "L": (6, 0, 0), "M": (6, 6, 0), "N": (0, 6, 0), "O": (0, 0, 3)}
    oracle = oracle_section(V, pyramid_edges("O", "KLMN"), (mid(V["O"], V["K"]), mid(V["O"], V["L"]), mid(V["O"], V["M"])))
    env, route = _wording_case(phrase)
    assert (env["status"], route["status"]) == ("ok", "SERVED"), (phrase, route.get("refusal"))
    assert len(route["sections"][0]["vertices"]) == oracle["vertices"]
    assert coef_squared(route["answer_exact"]["q1"]["coef"]) == oracle["area2"]


@pytest.mark.parametrize("phrase", [
    "cắt bởi mặt phẳng (UVW) đi qua ba điểm U, V, K",     # the appositive names other points than the plane
    "cắt bởi mặt phẳng đi qua ba điểm U, V, K",           # the stated points are not the extracted plane
])
def test_wording_that_names_other_points_is_refused(phrase: str) -> None:
    env, route = _wording_case(phrase)
    assert route["status"] == "REFUSED" and not env.get("scene3d"), route
