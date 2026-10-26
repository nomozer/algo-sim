# -*- coding: utf-8 -*-
"""B3 slice: canonical V2 `measurement` goals with `goal_type: "distance"` reach the ONE planner/engine.

The target keys are the ones `adapter3_simulation` already reads (`{point, plane}`, `{segment}`, `{line1, line2}`); the
bridge only renames them into the planner's existing distance/length questions. Expected values are closed-form from the
stated facts of a triangular prism ABC.A'B'C' with a right angle at A, AB = x, AC = y (independent of engine layout):

- right prism, AA' = h: d(A', (ABC))² = h², d(A, (BCC'B'))² = d(AA', BC)² = x²y²/(x²+y²), B'C² = x²+y²+h²;
- oblique prism whose top vertex A' projects onto the midpoint H of BC, AA' = l: d(A', (ABC))² = l² − (x²+y²)/4.

Authored development cases — not a holdout, not an extraction-quality measurement.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
from math import isqrt

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.simulation.geometry_functions import TuChoi
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge, bridge_v2


def _prism(labels="ABC", x=6, y=8, h=12, oblique=False, ask=None):
    a, b, c = labels
    base, top = list(labels), [v + "'" for v in labels]
    name = labels + "." + "".join(top)
    solid = f"Cho lăng trụ {'' if oblique else 'đứng '}{name}."
    shape = f"Đáy {labels} là tam giác vuông tại {a}."
    qs = [solid, shape, f"{a}{b} = {x}.", f"{a}{c} = {y}."]
    premises = [{"kind": "right_angle", "args": {"vertex": a, "rays": [b, c]}, "quote": shape},
                {"kind": "segment_length", "args": {"segment": [a, b], "value": str(x)}, "quote": qs[2]},
                {"kind": "segment_length", "args": {"segment": [a, c], "value": str(y)}, "quote": qs[3]}]
    if oblique:
        l2 = F(h * h) + F(x * x + y * y, 4)
        lv = isqrt(l2.numerator) // isqrt(l2.denominator)
        assert lv * lv == l2, "choose dimensions with a rational lateral edge"
        q1, q2, q3 = (f"Gọi H là trung điểm của {b}{c}.", f"Hình chiếu vuông góc của {a}' lên ({labels}) là H.",
                      f"{a}{a}' = {lv}.")
        premises += [{"kind": "midpoint", "args": {"point": "H", "segment": [b, c]}, "quote": q1},
                     {"kind": "orthogonal_projection", "args": {"point": a + "'", "image": "H", "plane": base},
                      "quote": q2},
                     {"kind": "segment_length", "args": {"segment": [a, a + "'"], "value": str(lv)}, "quote": q3}]
        qs += [q1, q2, q3]
    else:
        q = f"{a}{a}' = {h}."
        premises += [{"kind": "right_prism", "args": {"base": base, "top": top}, "quote": solid},
                     {"kind": "segment_length", "args": {"segment": [a, a + "'"], "value": str(h)}, "quote": q}]
        qs.append(q)
    quote, target = ask or (f"Tính khoảng cách từ {a}' đến mặt phẳng ({labels}).",
                            {"point": a + "'", "plane": base})
    qs.append(quote)
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join(qs), "length_unit": "1",
            "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": name, "quote": solid}],
            "premises": premises,
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pr", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "distance", "target": target,
                            "quote": quote}]}


def _square(r) -> F:
    v = r.exec_result.final_memory["kq_q"]
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


def _served(p) -> F:
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "SERVED", (r.code, r.reason)
    return _square(r)


# ── served: every target form adapter3 reads, against the closed-form oracle ─────────────────────────────

@pytest.mark.parametrize("labels,x,y,h", [("ABC", 6, 8, 12), ("DEF", 6, 8, 12), ("KLM", 3, 4, 5), ("RST", 12, 16, 7)])
def test_point_to_base_plane_of_a_right_prism_is_its_height(labels, x, y, h):
    assert _served(_prism(labels, x, y, h)) == h * h


def test_point_to_lateral_face_is_the_base_altitude():
    p = _prism(ask=("Tính khoảng cách từ A đến mặt phẳng (BCC'B').", {"point": "A", "plane": ["B", "C", "C'"]}))
    assert _served(p) == F(36 * 64, 36 + 64)


def test_four_label_plane_target_is_served_with_every_label_checked():
    """A four-label target used to be cut to its first three labels by the planner, so a non-coplanar fourth label was
    never checked (review I-1); this slice refused it. Since `hybrid-v2-backend-generalization` the planner hands every
    label to the engine's coplanarity check (`KeHoach.named_planes`), so the face (BCC'B') is served; non-coplanar and
    collinear-leading names are refused there (`test_typed_fact_next_v2_named_plane.py`)."""
    p = _prism(ask=("Tính khoảng cách từ A đến mặt phẳng (BCC'B').", {"point": "A", "plane": ["B", "C", "C'", "B'"]}))
    assert _served(p) == F(36 * 64, 36 + 64)


def test_segment_target_is_a_length():
    p = _prism(ask=("Tính độ dài đoạn thẳng B'C.", {"segment": ["B'", "C"]}))
    assert _served(p) == 36 + 64 + 144


def test_skew_lines_distance_is_the_base_altitude():
    p = _prism(ask=("Tính khoảng cách giữa hai đường thẳng AA' và BC.", {"line1": ["A", "A'"], "line2": ["B", "C"]}))
    assert _served(p) == F(36 * 64, 36 + 64)


@pytest.mark.parametrize("labels,x,y,h", [("ABC", 6, 8, 12), ("DEF", 12, 16, 24)])
def test_oblique_prism_uses_the_normal_component_not_the_lateral_edge(labels, x, y, h):
    p = _prism(labels, x, y, h, oblique=True)
    lateral2 = F(h * h) + F(x * x + y * y, 4)
    assert _served(p) == h * h != lateral2


def test_equivalent_plane_order_and_qualified_refs_give_the_same_answer():
    p = _prism(ask=("Tính khoảng cách từ A' đến mặt phẳng (ABC).", {"point": "pr::A'", "plane": ["C", "pr::B", "A"]}))
    assert _served(p) == 144


def test_uniform_scale_multiplies_the_squared_distance():
    assert _served(_prism(x=12, y=16, h=24)) == 4 * _served(_prism(x=6, y=8, h=12))


def test_adapter4_envelope_is_served():
    p = _prism()
    r = run_typed_fact_next_v2_route(p)
    rd = build_adapter4_response(r, p["problem_text"])["route_d"]
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q"]["coef"] == "12"
    prov = next(x for x in rd["source_provenance"] if x["id"] == "q")
    assert (prov["fn"], prov["args"], prov["quotes"]) == (
        "ask_distance_point_plane", {"point": "A'", "plane": ["A", "B", "C"]}, [p["math_goals"][0]["quote"]])


# ── refusals: fail closed, never an approximate or synthesized answer ──────────────────────────────────────

@pytest.mark.parametrize("target", [{"point": "A'"}, {"plane": ["A", "B", "C"]}, {"point": "A'", "plane": ["A", "B"]},
                                    {"segment": ["A"]}, {"line1": ["A", "A'"]}, {"line1": ["A"], "line2": ["B", "C"]},
                                    {"point": ["A'"], "plane": ["A", "B", "C"]}, {"solid": "pr"},
                                    {"point": "A'", "plane": ["A", "B", "C"], "solid": "pr"},
                                    {"segment": ["A", "B", "C"]},
                                    # review I-1 / M-1 / M-2: no silent truncation, no degenerate operands
                                    # (4 labels, not coplanar: refused by the engine — test below)
                                    {"point": "A'", "plane": ["A", "B", "C", "pr::A"]},    # 4 labels, one repeated
                                    {"point": "A'", "plane": ["A", "A", "B"]},
                                    {"segment": ["A", "A"]}, {"segment": ["A", "pr::A"]},
                                    {"line1": ["A", "A"], "line2": ["B", "C"]}, {"line1": ["A", "A'"], "line2": ["C", "C"]}])
def test_malformed_distance_target_is_refused(target):
    p = _prism(ask=("Tính khoảng cách từ A' đến mặt phẳng (ABC).", target))
    r = run_typed_fact_next_v2_route(p)
    assert (r.status, r.code) == ("REFUSED", "INVALID_MATH_GOAL")


def test_non_coplanar_fourth_plane_label_is_refused_by_the_engine():
    """Well-formed (four distinct labels) but not one plane: A' is off (ABC). Not truncated to (ABC) and served."""
    p = _prism(ask=("Tính khoảng cách từ A' đến mặt phẳng (ABC).", {"point": "A'", "plane": ["A", "B", "C", "A'"]}))
    r = run_typed_fact_next_v2_route(p)
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH")


def test_unknown_qualified_vertex_is_refused():
    p = _prism(ask=("Tính khoảng cách từ A' đến mặt phẳng (ABC).", {"point": "pr::Z", "plane": ["A", "B", "C"]}))
    assert run_typed_fact_next_v2_route(p).status == "REFUSED"


def _without(p, pred):
    gone = [x for x in p["premises"] if pred(x)]
    assert gone
    p["premises"] = [x for x in p["premises"] if not pred(x)]
    for x in gone:
        p["problem_text"] = p["problem_text"].replace(x["quote"], "")
    return p


@pytest.mark.parametrize("case,code", [("missing_height", "MISSING_DIMENSION"),
                                       ("missing_base_angle", "MISSING_DIMENSION"),
                                       ("zero_height", "NON_POSITIVE_LENGTH"),
                                       ("contradictory_height", "INCONSISTENT_FACTS"),
                                       ("collinear_plane", "SOURCE_OBJECT_MISMATCH"),
                                       ("quote_not_in_source", "QUOTE_NOT_IN_SOURCE"),
                                       ("unknown_point", "UNKNOWN_LABEL")])
def test_underdetermined_degenerate_or_ungrounded_inputs_are_refused(case, code):
    p = _prism()
    if case == "missing_height":
        _without(p, lambda x: x["kind"] == "segment_length" and x["args"]["segment"] == ["A", "A'"])
    elif case == "missing_base_angle":
        _without(p, lambda x: x["kind"] == "right_angle")
    elif case == "zero_height":
        p["problem_text"] = p["problem_text"].replace("AA' = 12.", "AA' = 0.")
        x = next(x for x in p["premises"] if x["kind"] == "segment_length" and x["args"]["segment"] == ["A", "A'"])
        x["args"]["value"], x["quote"] = "0", "AA' = 0."
    elif case == "contradictory_height":
        p["problem_text"] += " AA' = 13."
        p["premises"].append({"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "13"},
                              "quote": "AA' = 13."})
    elif case == "collinear_plane":
        q, ask = "Gọi M là trung điểm của AB.", "Tính khoảng cách từ C' đến mặt phẳng (AMB)."
        p["problem_text"] = p["problem_text"].replace(p["math_goals"][0]["quote"], f"{q} {ask}")
        p["premises"].append({"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": q})
        p["math_goals"][0].update(quote=ask, target={"point": "C'", "plane": ["A", "M", "B"]})
    elif case == "quote_not_in_source":
        p["math_goals"][0]["quote"] = "Tính khoảng cách từ A' đến mặt phẳng (ABD)."
    else:
        p["math_goals"][0]["target"] = {"point": "Z", "plane": ["A", "B", "C"]}
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED" and r.code != "ROUTE_INTERNAL_ERROR", (case, r.code, r.reason)
    if code:
        assert r.code == code, (case, r.code, r.reason)


def test_curved_solids_stay_refused_before_the_distance_mapping():
    q = "Cho mặt cầu tâm O bán kính 5. Tính khoảng cách từ O đến mặt phẳng (P)."
    p = {"schema_version": "typed-fact-next/2", "problem_text": q,
         "solids": [{"solid_id": "s", "solid_type": "sphere", "notation": "(S)", "center": "O", "radius": "5", "quote": q}],
         "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "s", "quote": q}],
         "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "distance",
                         "target": {"point": "O", "plane": ["A", "B", "C"]}, "quote": q}]}
    r = run_typed_fact_next_v2_route(p)
    assert (r.status, r.code) == ("REFUSED", "BRIDGE_UNSUPPORTED_CURVED")


@pytest.mark.parametrize("ask,question", [
    (("Tính khoảng cách từ A' đến mặt phẳng (ABC).", {"point": "A'", "plane": ["A", "B", "C"]}),
     {"quantity": "distance", "points_a": ["A'"], "points_b": ["A", "B", "C"]}),
    (("Tính độ dài đoạn thẳng B'C.", {"segment": ["B'", "C"]}), {"quantity": "length", "points": ["B'", "C"]}),
    (("Tính khoảng cách giữa hai đường thẳng AA' và BC.", {"line1": ["A", "A'"], "line2": ["B", "C"]}),
     {"quantity": "distance", "points_a": ["A", "A'"], "points_b": ["B", "C"]}),
])
def test_bridge_is_a_pure_rename(ask, question):
    p = _prism(ask=ask)
    q = [f for f in bridge_v2(deepcopy(p))["facts"] if f["id"] == "q"]
    assert q == [{"id": "q", "kind": "question", "role": "question", "quotes": [ask[0]], **question}]


def test_v1_bridge_still_refuses_distance_goals():
    v1 = deepcopy(_prism())
    v1["schema_version"] = "typed-fact-next/1"
    with pytest.raises(TuChoi) as e:
        bridge(v1)
    assert e.value.code == "BRIDGE_UNSUPPORTED_MEASUREMENT"
