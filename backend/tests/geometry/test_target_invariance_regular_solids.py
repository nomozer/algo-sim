# -*- coding: utf-8 -*-
"""Run `target-invariant-regular-solid-semantics`: target invariance under a free shape, and the regular tetrahedron.

Agent-written development texts; no dataset case id or exact problem text is used by the product.
"""
from __future__ import annotations

import copy

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry_functions import planner
from app.simulation.geometry_functions.registry import doc_ke_hoach
from app.simulation.geometry_functions.target_invariance import prove_plane_angle, verify_target_invariance_certificate
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

RIGHT_B = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
PLANES = "Tính góc giữa hai mặt phẳng (SBC) và (ABC)."


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _rd(text):
    return (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}


def _calls(text):
    lp = parse_geometry_problem_locally(text, use_cache=False)
    pl = planner.lap_ke_hoach({"facts": bridge_v2(lp.parsed_contract)["facts"]}, text)
    return doc_ke_hoach({"calls": pl.calls})


def _cert(text):
    calls = _calls(text)
    ask = next(c for c in calls if c.fn == "ask_angle_plane_plane")
    return prove_plane_angle(calls, ask.id, ask.args.plane1, ask.args.plane2), calls


# ── target invariance with a free shape ────────────────────────────────────────────────────────────────────────────
def test_an_angle_fixed_by_a_fixed_triangle_is_served_on_an_illustrative_non_unique_figure():
    rd = _rd(RIGHT_B + PLANES)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == "1/2"          # ∠SBA of SAB right isosceles at A
    cfg = rd["scene_configuration"]
    assert cfg["kind"] == "TARGET_INVARIANT_ILLUSTRATIVE" and cfg["unique"] is False and cfg["source_length_supplied"] is False
    cert = cfg["invariance_certificate"]
    assert cert["certification_level"] == "MATHEMATICALLY_PROVEN" and cert["representative_level"] == "ENGINE_DOMAIN_CERTIFIED"
    assert [g["independent_verification"]["verified"] for g in cert["goals"]] == [True]
    assert all(w["same_exact_answers"] for w in cert["witnesses"] if w["status"] == "SERVED")


def test_the_proof_is_the_synthetic_one():
    cert, _ = _cert(RIGHT_B + PLANES)
    rules = [s["rule"] for s in cert["steps"]]
    assert {"RIGHT_ANGLE", "SOURCE_LINE_PERP_PLANE", "PERP_PLANE_TO_LINE", "PERP_TWO_LINES", "PLANE_ANGLE",
            "TRIANGLE_SHAPE_FIXED"} <= set(rules)
    pa = next(s for s in cert["steps"] if s["rule"] == "PLANE_ANGLE")["conclusion"]
    assert pa["intersection"] == ["B", "C"] and set(pa["equals_angle"]) == {"S", "A", "B"}


@pytest.mark.parametrize("text", [
    "Cho hình chóp T.XYZ có đáy là tam giác vuông tại Y, TX vuông góc với đáy và TX = XY. Tính góc giữa hai mặt phẳng (TYZ) và (XYZ).",
    RIGHT_B + "Tang của góc giữa hai mặt phẳng (SBC) và (ABC) bằng",
])
def test_renamed_and_trigonometric_forms(text):
    rd = _rd(text)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == "1/2"


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với đáy. " + PLANES,            # height free: angle varies
    RIGHT_B + "Tính góc giữa đường thẳng SC và mặt phẳng (ABC).",                                       # varies with BC
    RIGHT_B + "Tính góc giữa hai mặt phẳng (SAC) và (ABC).",                                             # invariant but unproven here
    "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. Tính thể tích khối chóp S.ABC.",
])
def test_unproven_or_varying_goals_are_refused(text):
    assert _rd(text)["status"] != "SERVED"


def test_no_proof_without_the_equal_legs():
    cert, _ = _cert("Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với đáy. " + PLANES)
    assert cert is None


@pytest.mark.parametrize("mutate, where", [
    (lambda c: c["steps"].__setitem__(0, {**c["steps"][0], "rule": "PARALLEL"}), "unknown rule"),
    (lambda c: next(s for s in c["steps"] if s["rule"] == "PLANE_ANGLE")["conclusion"].__setitem__("intersection", ["A", "C"]), "common line"),
    (lambda c: next(s for s in c["steps"] if s["rule"] == "PLANE_ANGLE")["conclusion"].__setitem__("equals_angle", ["B", "C", "A"]), "arms"),
    (lambda c: next(s for s in c["steps"] if s["rule"] == "TRIANGLE_SHAPE_FIXED")["conclusion"].__setitem__("by", "RIGHT_ISOSCELES_AT_B"), "right angle"),
    (lambda c: c["steps"].pop(next(i for i, s in enumerate(c["steps"]) if s["rule"] == "PERP_TWO_LINES")), "earlier"),
    (lambda c: next(s for s in c["steps"] if s["rule"] == "PERP_PLANE_TO_LINE")["conclusion"].__setitem__("perpendicular", [["A", "S"], ["S", "C"]]), "plane"),
    (lambda c: next(s for s in c["steps"] if s["rule"] == "TRIANGLE_SHAPE_FIXED")["premises"].__setitem__(1, "nope"), "stated equal"),
])
def test_the_independent_verifier_catches_every_mutated_step(mutate, where):
    cert, calls = _cert(RIGHT_B + PLANES)
    assert verify_target_invariance_certificate(cert, calls)["verified"] is True
    bad = copy.deepcopy(cert)
    mutate(bad)
    assert verify_target_invariance_certificate(bad, calls)["verified"] is False


def test_a_changed_source_fact_breaks_the_certificate():
    cert, _ = _cert(RIGHT_B + PLANES)
    other = _calls("Cho hình chóp S.ABC có đáy là tam giác vuông tại C, SA vuông góc với đáy và SA = AB. " + PLANES)
    assert verify_target_invariance_certificate(cert, other)["verified"] is False   # the right angle is now at C


# ── the regular tetrahedron ────────────────────────────────────────────────────────────────────────────────────────
TETRA = "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM."


def test_a_regular_tetrahedron_without_side_is_fixed_up_to_scale():
    rd = _rd(TETRA)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == "1/12"     # cos(AC, BM) = √3/6
    assert rd["scene_configuration"]["kind"] == "SIMILARITY_SCALE_ILLUSTRATIVE"


def test_the_six_equal_edges_are_one_definitional_equality_quoting_the_definition():
    lp = parse_geometry_problem_locally(TETRA, use_cache=False)
    eq = [p for p in lp.payload["premises"] if p["kind"] == "equal_length"]
    assert len(eq) == 1 and eq[0]["quote"] == "tứ diện đều ABCD"
    assert {"A", "B"} == set(eq[0]["args"]["segment_a"]) and {"B", "C"} == set(eq[0]["args"]["segment_b"])


@pytest.mark.parametrize("text", [
    "Cho tứ diện đều ABCD cạnh a. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM.",
    "Cho tứ diện đều PQRS. Gọi K là trung điểm của RS. Tính góc giữa hai đường thẳng PR và QK.",
])
def test_side_and_renaming_give_the_same_angle(text):
    assert _rd(text)["answer_exact"]["q1"]["coef"] == "1/12"


@pytest.mark.parametrize("text", [
    "Cho tứ diện ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM.",                       # not regular
    "Cho hình chóp tam giác đều S.ABC. Gọi M là trung điểm của BC. Tính góc giữa hai đường thẳng SA và BM.",        # lateral free
])
def test_figures_that_are_not_regular_tetrahedra_are_not_treated_as_one(text):
    assert _rd(text)["status"] != "SERVED"


def test_the_gate_reads_the_equality_only_from_a_regular_tetrahedron_phrase():
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    for quote, ok in (("tứ diện đều ABCD", True), ("tứ diện ABCD", False), ("tam giác đều BCD", False)):
        lp = parse_geometry_problem_locally(TETRA, use_cache=False)
        pay = copy.deepcopy(lp.payload)
        for p in pay["premises"]:
            if p["kind"] == "equal_length":
                p["quote"] = quote if quote in pay["problem_text"] else p["quote"]
                if not ok:
                    pay["problem_text"] = pay["problem_text"].replace("tứ diện đều ABCD", quote)
                    p["quote"] = quote
        r = run_typed_fact_next_v2_route(pay)
        assert (r.status == "SERVED") is ok, (quote, r.code)


def test_a_conflicting_edge_length_is_refused():
    assert _rd("Cho tứ diện đều ABCD cạnh 2 và AB = 3. Tính góc giữa hai đường thẳng AC và BD.")["status"] != "SERVED"
