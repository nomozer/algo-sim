"""C17 constraint-to-witness planes on Hybrid /4 (registry /30, planner /25, engine /21): a plane the source defines only
by relations is built through witness points the planner FINDS, the gate grounds, the engine proves. Hand oracles:
pyramid S.ABCD, square side 2, SA ⊥ (ABCD), SA = 2: A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2); M = mid AB = (1,0,0),
N = mid CD = (1,2,0).
- (P) ∋ M, N, ⊥ (ABCD): x = 1 ⇒ section (1,0,0) (1,2,0) (1,1,1) (1,0,1), a trapezoid of bases 2 and 1, height 1 ⇒ 3/2.
- (P) ∋ M, N, ⊥ (SBC) (x + z = 2): x − z = 1 ⇒ (1,0,0) (3/2,0,1/2) (3/2,3/2,1/2) (1,2,0), bases 2 and 3/2 at distance
  √2/2 ⇒ 7√2/8.
"""
from __future__ import annotations

import re
from dataclasses import replace

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions import planner, registry
from app.simulation.geometry_functions.typed_fact_next import DerivedPlaneSectionSpec, TypedFactNextValidationError
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
AQ = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
BASE = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. ")
PREM = [{"kind": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2",
         "solid_id": "s1"},
        {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")},
         "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"},
        {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"},
        {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
        {"kind": "midpoint", "args": {"point": "N", "segment": ["C", "D"]}, "quote": "Gọi N là trung điểm của CD", "solid_id": "s1"}]


def _case(sentence, constraints, text_sentence=None):
    text = BASE + (text_sentence or sentence) + ". " + AQ + "."
    payload = {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
               "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
               "premises": PREM, "relations": [],
               "derived_sections": [{"section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "quote": sentence,
                                     "plane_kind": "constrained", "constraints": constraints, "stated_intersections": []}],
               "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                                     "quote": "Cho hình chóp S.ABCD"}],
               "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"},
                               "quote": AQ, "solid_id": "s1"}]}
    return text, payload


def _run(sentence, constraints, text_sentence=None):
    text, payload = _case(sentence, constraints, text_sentence)
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    return text, out.response["route_d"], out.response["envelope"]


def _qua_vuong(pts, q):
    return (f"Mặt phẳng (P) đi qua {', '.join(pts)} và vuông góc với ({''.join(q)})",
            [{"kind": "contains_points", "operands": list(pts)}, {"kind": "perpendicular_to_plane", "operands": list(q)}])


def test_c17_a_stated_normal_is_reused_and_the_answer_is_exact():
    _text, route, env = _run(*_qua_vuong("MN", "ABCD"))
    assert route["status"] == "SERVED", env.get("reason_code")
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "3/2"}
    aux = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))
    assert aux["witnesses"][0]["producer"] == "premise" and aux["witnesses"][0]["vector"] == ["A", "S"]
    assert aux["search"]["subgoals"][0]["selected"]["cost"] == 0 and aux["search"]["subgoals"][0]["candidates"] >= 2


def test_c17_a_normal_no_premise_gives_is_constructed_by_the_planner_and_the_answer_is_exact():
    text, route, env = _run(*_qua_vuong("MN", "SBC"))
    assert route["status"] == "SERVED", env.get("reason_code")
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "7√2/8"}
    aux = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))
    w = aux["witnesses"][0]
    sub = aux["search"]["subgoals"][0]
    # S, B, C lie on (SBC) and are rejected structurally; A and D remain; A first in the solid's own order
    assert {r["point"] for r in sub["rejected"]} == {"S", "B", "C"} and sub["selected"]["point"] == "A"
    assert w["producer"] == "orthogonal_projection" and w["point"] == "A"
    assert not re.search(rf"(?<![\w']){re.escape(w['foot'])}(?![\w'])", text)        # an intermediate the source never names
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION" and w["call"] in tel["search_generated_steps"]
    plane = next(s for s in route["construction_trace"] if s.get("rule", "").startswith("section(plane defined"))
    assert plane["existence"] == plane["uniqueness"] == "VERIFIED" and w["label"] in plane["span"]   # necessary witness


@pytest.mark.parametrize("pts,q,code", [
    ("AS", "ABCD", "PLANE_NOT_UNIQUE"),           # AS is itself ⊥ (ABCD): every plane through AS qualifies
    ("ABC", "SBC", "INCONSISTENT_FACTS"),         # (ABC) is not ⊥ (SBC): no plane holds all three relations
    ("ABD", "SAD", "SECTION_PLANE_IS_FACE"),      # (ABD) ⊥ (SAD) but it is the base face itself
])
def test_c17_existence_and_uniqueness_are_proved_from_every_stated_relation(pts, q, code):
    _text, route, env = _run(*_qua_vuong(pts, q))
    assert route["status"] == "REFUSED" and env.get("reason_code") == code


def test_c17_a_parallel_line_inside_the_plane_is_refused():
    s = "Mặt phẳng (P) chứa AC và song song với AB"
    _text, route, env = _run(s, [{"kind": "contains_points", "operands": ["A", "C"]},
                                 {"kind": "parallel_to_line", "operands": ["A", "B"]}])
    assert route["status"] == "REFUSED" and env.get("reason_code") == "LINE_CONTAINED_IN_PLANE"


def test_c17_a_relation_the_text_does_not_state_is_refused_at_the_source_gate():
    s, cons = _qua_vuong("MN", "SBC")
    _text, route, env = _run(s, cons, text_sentence="Mặt phẳng (P) đi qua M, N và vuông góc với (SCD)")
    assert route["status"] == "REFUSED"


def test_c17_a_type_correct_but_degenerate_producer_never_serves(monkeypatch):
    """Fault injection: the normal taken from a vertex ON the plane (its foot is itself): the engine refuses."""
    real = planner._phap_tuyen

    def on_plane(q_mat, kh, k):
        out = real(q_mat, kh, k)
        if out["selected"]["producer"] != "premise":
            out["selected"] = dict(out["selected"], point=q_mat[0])
        return out
    monkeypatch.setattr(planner, "_phap_tuyen", on_plane)
    _text, route, _env = _run(*_qua_vuong("MN", "SBC"))
    assert route["status"] == "REFUSED"


def test_c17_three_points_with_a_normal_along_two_of_them_build_through_the_independent_triple():
    """Found by the systematic probe: A, S, N ⊥ (ABCD) — AS ∥ the normal; the plane (ASN) is unique (x = y)."""
    _text, route, env = _run(*_qua_vuong("ASN", "ABCD"))
    assert route["status"] == "SERVED", env.get("reason_code")
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "REGISTERED_DECOMPOSITION" and tel["verification_witness_steps"]


def test_c17_a_function_known_only_by_its_normal_contract_is_selected_without_dispatch_code(monkeypatch):
    """§VIII planner level (the clone has no IR of its own): no planner line names it."""
    src = registry.REGISTRY["orthogonal_projection"]
    monkeypatch.setitem(registry.REGISTRY, "a_foot_on_plane", replace(src, name="a_foot_on_plane", planning=None))
    text, payload = _case(*_qua_vuong("MN", "SBC"))
    k = planner.lap_ke_hoach(bridge_v2(payload), text)
    assert any(c["fn"] == "a_foot_on_plane" for c in k.calls)


def test_c17_without_a_normal_producer_the_refusal_is_a_missing_primitive_not_a_guess(monkeypatch):
    real = planner.planning_contracts
    monkeypatch.setattr(planner, "planning_contracts", lambda s: tuple(c for c in real(s) if c.effect.kind != "Normal"))
    text, payload = _case(*_qua_vuong("MN", "SBC"))
    with pytest.raises(registry.TuChoi) as e:
        planner.lap_ke_hoach(bridge_v2(payload), text)
    assert e.value.code == "UNSUPPORTED_CAPABILITY" and e.value.data.get("outcome") == "MISSING_PRIMITIVE"


def test_c17_the_search_budget_is_enforced_and_reported_as_exhaustion_not_impossibility(monkeypatch):
    monkeypatch.setattr(planner, "MAX_NORMAL_CANDIDATES", 1)
    text, payload = _case(*_qua_vuong("MN", "SBC"))
    with pytest.raises(registry.TuChoi) as e:
        planner.lap_ke_hoach(bridge_v2(payload), text)
    assert e.value.code == "PLAN_TOO_LARGE" and e.value.data.get("outcome") == "SEARCH_EXHAUSTED"


def test_c17_the_constrained_kind_is_typed_fact_next_2_only():
    with pytest.raises((TypedFactNextValidationError, ValueError)):
        DerivedPlaneSectionSpec(section_id="x", target_solid_id="s1", plane_kind="constrained", quote="q")


def test_c17_a_described_point_inside_a_constraint_is_refused_by_the_bridge():
    s, cons = _qua_vuong("MN", "SBC")
    cons[0]["operands"] = ["M", "@m1"]
    text, payload = _case(s, cons)
    payload["described_points"] = [{"described_id": "m1", "kind": "midpoint", "quote": "trung điểm của CD",
                                    "segment": ["C", "D"]}]
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY).response
    assert out["route_d"]["status"] == "REFUSED"
