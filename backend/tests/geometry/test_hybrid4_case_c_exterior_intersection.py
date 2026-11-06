"""Case C on Hybrid /4: a line–plane intersection point outside the solid is NOT part of the bounded section.

Ported from the retired Axo test `test_hybrid_e2e_generalization.py::test_case_c_…` (it already drove
`function_route.run_fact_route`, the Hybrid engine; it was retired only because its module imported Adapter /3).
Strengthened: besides "Q is not a polygon vertex", the checks below are exact and affine-invariant (they do not depend
on the scene's Gram metric): Q lies on the cutting plane and on line SD with parameter t = 3/2 (outside segment SD),
every section vertex lies on an edge of the solid, the pentagon is planar, convex and cyclically ordered, and Q is
outside the finite polygon. A polluted copy of the scene (Q spliced into the polygon — the old failure mode) must be
rejected by the same checks.

Two layers: the shared planner/engine serves the full section (via the /1 TypedFact route, same `planner.py`/`engine.py`);
the product envelope (TypedFactNext /2 → /4) serves Q exactly, but /2 has no plane kind for "the plane through three named
points", so the section question is refused there (contract capability gap, owner decision — not a geometry fault).

Independent hand computation (A=(0,0,0), B=(2,0,0), C=(2,2,0), D=(0,2,0), S=(0,0,4)):
M=(0,0,1) (SM=3MA), N=(3/4,0,5/2) (SN=3/5 NB), P=(1,1,2); (MNP): −2x+y+z=1; Q=SD∩(MNP)=(0,3,−2), t=3/2;
section = M, N, P, (1/2,2,0)∈CD, (0,1,0)∈AD.
"""
from __future__ import annotations

import copy
from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from tests.geometry import construction_sequencing as CS
from tests.geometry import hybrid_compiler_benchmark as HB


@pytest.fixture(autouse=True)
def _offline_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)


def _div(fid: str, p: str, a: str, b: str, ratio: str, eq_text: str) -> dict:
    q = f"Gọi {p} là điểm thuộc cạnh {a}{b} sao cho {eq_text}."
    return HB._f(fid, "point_def", q, point=p, point_kind="divide_segment", points=[a, b], value=ratio)


def _case_c_facts() -> list[dict]:
    return [
        HB._f("c1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("c2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("c3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("c4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        _div("c5", "M", "S", "A", "3/4", "SM = 3MA"),
        _div("c6", "N", "S", "B", "3/8", "SN = 3/5 NB"),
        HB._mid("c7", "P", "S", "C"),
        HB._ilp("c8", "Q", "SD", "MNP"),
        HB._f("c9", "section", "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MNP).", role="question", solid="S.ABCD", points=["M", "N", "P"]),
    ]


Vec = tuple[F, F, F]


def _v(xyz) -> Vec:
    return (F(str(xyz[0])), F(str(xyz[1])), F(str(xyz[2])))


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a: Vec, b: Vec) -> F:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _point(scene: dict, sym: str) -> Vec:
    return _v(next(o for o in scene["objects"] if o["type"] == "point3" and (o.get("notation") or o.get("label")) == sym)["xyz"])


def _on_segment_param(p: Vec, a: Vec, b: Vec) -> F | None:
    """t with p = a + t (b − a) if p is on LINE ab, else None (exact)."""
    d = _sub(b, a)
    if _cross(_sub(p, a), d) != (0, 0, 0):
        return None
    i = next(k for k in range(3) if d[k] != 0)
    return (p[i] - a[i]) / d[i]


def _check_exterior_point_outside_section(scene: dict, q_sym: str, line: tuple[str, str]) -> dict:
    """Raises AssertionError if `q_sym` is presented as part of the bounded section or the section is malformed."""
    sec = next(o for o in scene["objects"] if o["type"] == "section")
    poly = [_v(p) for p in sec["polygon"]]
    q = _point(scene, q_sym)
    a, b = (_point(scene, s) for s in line)
    # Q is the intersection with the LINE through the segment, outside the segment.
    t = _on_segment_param(q, a, b)
    assert t is not None, "Q is not on the line"
    assert not (0 <= t <= 1), f"Q lies on segment {line} (t={t}); Case C requires an exterior intersection"
    # Planar polygon, Q on its plane.
    n = _cross(_sub(poly[1], poly[0]), _sub(poly[2], poly[0]))
    assert n != (0, 0, 0)
    assert all(_dot(n, _sub(p, poly[0])) == 0 for p in poly), "section not planar"
    assert _dot(n, _sub(q, poly[0])) == 0, "Q not on the cutting plane"
    # Every section vertex lies on an edge (segment) of the solid.
    solid = next(o for o in scene["objects"] if o["type"] == "solid")
    verts = [_v(p) for p in solid["vertices"]]
    edges = {tuple(sorted((f[i], f[(i + 1) % len(f)]))) for f in solid["faces"] for i in range(len(f))}
    for p in poly:
        assert any((tt := _on_segment_param(p, verts[i], verts[j])) is not None and 0 <= tt <= 1 for i, j in edges), \
            f"section vertex {p} is not on an edge of the solid"
    # Convex, cyclically ordered: all consecutive turn normals point the same way as n.
    turns = [_dot(n, _cross(_sub(poly[(i + 1) % len(poly)], poly[i]), _sub(poly[(i + 2) % len(poly)], poly[(i + 1) % len(poly)])))
             for i in range(len(poly))]
    assert all(s > 0 for s in turns) or all(s < 0 for s in turns), f"section not convex/cyclic: {turns}"
    # Q strictly outside the finite convex polygon (some edge has Q on the outer side), and not a vertex.
    assert q not in poly, "Q presented as a section vertex"
    sides = [_dot(n, _cross(_sub(poly[(i + 1) % len(poly)], poly[i]), _sub(q, poly[i]))) for i in range(len(poly))]
    inside = all(s >= 0 for s in sides) or all(s <= 0 for s in sides)
    assert not inside, "Q inside the bounded section"
    return {"t": t, "vertices": len(poly)}


def test_case_c_exterior_q_outside_bounded_pentagon_on_the_hybrid_engine() -> None:
    """Shared planner + engine (/1 TypedFact route — the same `planner.py`/`engine.py` that /4 runs after bridge_v2)."""
    facts = _case_c_facts()
    text = " ".join(f["quotes"][0] for f in facts)
    r = run_fact_route(text, {"facts": facts})
    assert r.status == "SERVED", (r.status, getattr(r, "code", None))
    assert CS.check(r.scene3d) == {"O1": [], "O2": [], "O3": [], "O4": []}
    res = _check_exterior_point_outside_section(r.scene3d, "Q", ("S", "D"))
    assert res == {"t": F(3, 2), "vertices": 5}
    # Hand-computed values (affine chart, A=(0,0,0)… S=(0,0,4) up to the scene's chart scale).
    assert _on_segment_param(_point(r.scene3d, "M"), _point(r.scene3d, "S"), _point(r.scene3d, "A")) == F(3, 4)
    assert _on_segment_param(_point(r.scene3d, "N"), _point(r.scene3d, "S"), _point(r.scene3d, "B")) == F(3, 8)
    assert _on_segment_param(_point(r.scene3d, "P"), _point(r.scene3d, "S"), _point(r.scene3d, "C")) == F(1, 2)



# ── Hybrid /4 envelope (POST /api/analyze's route: TypedFactNext /2 → bridge_v2 → Source Gate → planner → engine → /4) ──
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
_SENT = ["Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2", "SA vuông góc với mặt phẳng (ABCD)", "SA = 4",
         "Gọi M là điểm thuộc cạnh SA sao cho SM = 3MA", "Gọi N là điểm thuộc cạnh SB sao cho SN = 3/5 NB",
         "Gọi P là trung điểm của SC", "Gọi Q là giao điểm của SD với mặt phẳng (MNP)"]
_SECTION_Q = "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP)"


def _v2_payload(text: str, *, derived_sections: list, math_goals: list) -> dict:
    prem = [{"kind": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")}, "quote": _SENT[1]},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "4"}, "quote": _SENT[2]},
            {"kind": "divide_segment", "args": {"point": "M", "segment": ["S", "A"], "ratio": "3/4"}, "quote": _SENT[3]},
            {"kind": "divide_segment", "args": {"point": "N", "segment": ["S", "B"], "ratio": "3/8"}, "quote": _SENT[4]},
            {"kind": "midpoint", "args": {"point": "P", "segment": ["S", "C"]}, "quote": _SENT[5]},
            {"kind": "intersect_line_plane", "args": {"point": "Q", "line": ["S", "D"], "plane": ["M", "N", "P"]}, "quote": _SENT[6]}]
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
            "premises": [{**x, "solid_id": "s1"} for x in prem], "relations": [], "derived_sections": derived_sections,
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
            "math_goals": math_goals}


def _run_v2(text: str, payload: dict) -> tuple[dict, dict]:
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    return out.response["envelope"], out.response["route_d"]


def test_case_c_exterior_q_is_served_exactly_on_the_hybrid4_envelope() -> None:
    """Q = SD ∩ (MNP) on the product envelope: on line SD with t = 3/2 (outside the segment), SQ = 3/2·SD = 3√5."""
    text = ". ".join(_SENT) + ". Tính độ dài SQ."
    env, route = _run_v2(text, _v2_payload(text, derived_sections=[], math_goals=[
        {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["S", "Q"]},
         "quote": "Tính độ dài SQ", "solid_id": "s1"}]))
    assert (env["status"], route["status"]) == ("ok", "SERVED"), (env.get("reason_code"), route.get("refusal"))
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "3√5"}
    sc = env["scene3d"]
    t = _on_segment_param(_point(sc, "Q"), _point(sc, "S"), _point(sc, "D"))
    assert t == F(3, 2)
    assert _on_segment_param(_point(sc, "M"), _point(sc, "S"), _point(sc, "A")) == F(3, 4)
    assert _on_segment_param(_point(sc, "N"), _point(sc, "S"), _point(sc, "B")) == F(3, 8)
    assert not any(o["type"] == "section" for o in sc["objects"])      # no section was asked, none is drawn


def test_case_c_section_by_three_named_points_is_served_end_to_end_without_q_as_a_vertex() -> None:
    """TypedFactNext /2 `constrained` with ONLY `contains_points=M,N,P` = the plane (MNP) (bridge → the planner's
    three-point section). Served through the full /4 route: exact pentagon, Q on line SD outside the segment and never
    a section vertex, plane label (MNP), area 11√6/8 (hand: |Σ vᵢ×vᵢ₊₁|²/4 = 363/32)."""
    q_area = "Tính diện tích thiết diện đó"
    text = ". ".join(_SENT + [_SECTION_Q, q_area]) + "."
    payload = _v2_payload(text, math_goals=[
        {"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": q_area,
         "solid_id": "s1"}], derived_sections=[
        {"section_id": "sec1", "target_solid_id": "s1", "quote": _SECTION_Q, "plane_kind": "constrained",
         "constraints": [{"kind": "contains_points", "operands": ["M", "N", "P"]}], "stated_intersections": []}])
    payload["simulation_goals"].append({"goal_id": "sg2", "kind": "construct_plane_section", "target_section_id": "sec1",
                                        "quote": _SECTION_Q})
    env, route = _run_v2(text, payload)
    assert (env["status"], route["status"]) == ("ok", "SERVED"), (env.get("reason_code"), route.get("refusal"))
    assert _check_exterior_point_outside_section(env["scene3d"], "Q", ("S", "D")) == {"t": F(3, 2), "vertices": 5}
    assert CS.check(env["scene3d"]) == {"O1": [], "O2": [], "O3": [], "O4": []}
    (sec,) = route["sections"]
    assert sec["plane_label"] == "(MNP)" and sec["certificate_category"] == "ENGINE_DERIVED_SECTION"
    assert len(sec["vertices"]) == 5 and all(v["label"] != "Q" for v in sec["vertices"])
    assert route["answer_exact"]["q1"]["coef"] == "11√6/8"


def test_case_c_checks_reject_the_old_failure_mode() -> None:
    """Guard window: the same checks must fail when Q is spliced into the section (exterior point treated as vertex)."""
    facts = _case_c_facts()
    r = run_fact_route(" ".join(f["quotes"][0] for f in facts), {"facts": facts})
    polluted = copy.deepcopy(r.scene3d)
    sec = next(o for o in polluted["objects"] if o["type"] == "section")
    q = next(o for o in polluted["objects"] if o["type"] == "point3" and (o.get("notation") or o.get("label")) == "Q")
    sec["polygon"] = sec["polygon"][:2] + [q["xyz"]] + sec["polygon"][2:]
    with pytest.raises(AssertionError):
        _check_exterior_point_outside_section(polluted, "Q", ("S", "D"))


def test_case_c_parallel_line_refused_and_contradictory_lengths_refused() -> None:
    fc2 = [
        HB._f("cp1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("cp2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("cp3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("cp4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        HB._mid("cp5", "M", "S", "A"),
        HB._mid("cp6", "N", "S", "B"),
        HB._mid("cp7", "P", "S", "C"),
        HB._ilp("cp8", "K", "AB", "MNP"),
        HB._ask("cp9", "Tính độ dài MK.", "length", points=["M", "K"]),
    ]
    r2 = run_fact_route(" ".join(f["quotes"][0] for f in fc2), {"facts": fc2})
    assert (r2.status, r2.code) == ("REFUSED", "PARALLEL_NO_INTERSECTION")
    fc3 = [
        HB._f("cd1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("cd2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("cd3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("cd4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3"),
        HB._f("cd5", "length", "SB = 5.", points=["S", "B"], measure="segment", value="5"),
        HB._ask("cd6", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD"),
    ]
    r3 = run_fact_route(" ".join(f["quotes"][0] for f in fc3), {"facts": fc3})
    assert (r3.status, r3.code) == ("REFUSED", "INCONSISTENT_FACTS")
