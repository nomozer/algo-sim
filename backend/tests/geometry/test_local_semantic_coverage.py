# -*- coding: utf-8 -*-
"""Local semantic coverage (run `local-semantic-source-gate-reliability`): reusable parser rules and one Source Gate
tail rule, each with positive, negative, renamed-vertex, reordered, contradictory and source-span checks.

None of these statements is a case of the evaluated corpora; they exercise the general phrasing the traced failures
showed (regular-solid dimension lists, bare segment equality, volume goal wording, "… theo a bằng" questions).
Answers are hand-derived in the comments. 0 AI calls: ALLOW_LIVE_AI=0 and no key.
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import (
    LOCAL_PARSE_COMPLETE,
    _solid_dimension_items,
    parse_geometry_problem_locally,
)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _solve(text: str) -> tuple[str | None, dict | None, str | None]:
    out = route_text_input(text, allow_live_ai=False)
    rd = out.response.get("route_d") or {}
    env = out.response.get("envelope") or {}
    return rd.get("status"), rd.get("answers"), out.response.get("reason_code") or env.get("reason_code") or rd.get("reason_code")


def _parse(text: str):
    return parse_geometry_problem_locally(text, use_cache=False)


# ── Regular-solid dimension lists, any order, optional "độ dài" ────────────────────────────────────────────────────
@pytest.mark.parametrize("text,answer", [
    # half-diagonal 2√2, h = √(25 − 8)
    ("Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh đáy bằng 4 và độ dài cạnh bên bằng 5. "
     "Tính khoảng cách từ S đến mặt phẳng (ABCD).", "√17"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 5 và cạnh đáy bằng 4. "
     "Tính khoảng cách từ S đến mặt phẳng (ABCD).", "√17"),
    # renamed vertices, same solid
    ("Cho hình chóp tứ giác đều O.MNPQ có độ dài cạnh bên bằng 5, độ dài cạnh đáy bằng 4. "
     "Tính khoảng cách từ O đến mặt phẳng (MNPQ).", "√17"),
    # all edges a: d(A,(SBC)) = 2·d(O,(SBC)) = a√6/3; two equal values must each be grounded once
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và cạnh đáy bằng a. "
     "Tính khoảng cách từ A đến mặt phẳng (SBC).", "a√6/3"),
    # regular prism: lateral edge is the height, V = (√3/4)a²·2a
    ("Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh bên bằng 2a và cạnh đáy bằng a. "
     "Tính thể tích khối lăng trụ ABC.A'B'C'.", "a³√3/2"),
    # plane (ABC') meets the base along AB at tan = CC'/BC = √3 ⇒ 60°
    ("Cho hình lăng trụ tứ giác đều ABCD.A'B'C'D' có cạnh đáy bằng a, cạnh bên bằng a√3. "
     "Tính góc giữa hai mặt phẳng (ABCD) và (ABC').", "cos²=1/4"),
])
def test_regular_solid_dimension_lists_serve_the_hand_derived_answer(text, answer):
    status, answers, reason = _solve(text)
    assert status == "SERVED", reason
    assert list(answers.values()) == [answer]


def test_dimension_items_stop_at_the_first_gap_and_never_repeat_an_attribute():
    t = " có cạnh đáy bằng 4 và cạnh bên bằng 5 và cạnh bên bằng 6, SA ⊥ (ABCD)"
    items = _solid_dimension_items(t, 0)
    assert [(a, v) for a, v, _s, _e in items] == [("base", "4"), ("lateral", "5")]
    assert _solid_dimension_items(" có chiều cao bằng 4", 0) == []
    # every item's quote start lies inside the text and includes its own "độ dài"
    t2 = " có độ dài cạnh đáy bằng 4 và độ dài cạnh bên bằng 5"
    for _a, _v, start, end in _solid_dimension_items(t2, 0):
        assert t2[start:end].startswith("độ dài cạnh")


def test_contradicting_lateral_edge_is_refused_not_served():
    # "cạnh bên bằng a" and "SA = 2a" cannot both hold for a regular pyramid
    status, _answers, reason = _solve(
        "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng a và SA = 2a. "
        "Tính khoảng cách từ S đến mặt phẳng (ABCD).")
    assert status == "REFUSED" and reason == "INCONSISTENT_FACTS"


def test_unsupported_dimension_word_still_fails_closed():
    assert _parse("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². "
                  "Tính khoảng cách từ A đến mặt phẳng (SBC).").status == LOCAL_PARSE_COMPLETE
    for unsupported in (
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích xung quanh bằng 2a². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a²ln2. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",
    ):
        assert _parse(unsupported).status != LOCAL_PARSE_COMPLETE


# ── Bare segment equality ───────────────────────────────────────────────────────────────────────────────────────────
def test_bare_segment_equality_is_read_as_congruence_with_its_own_quote():
    r = _parse("Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
               "Tính góc giữa hai mặt phẳng (SBC) và (ABC).")
    assert r.status == LOCAL_PARSE_COMPLETE, r.fallback_reason
    eq = [p for p in r.payload["premises"] if p["kind"] == "equal_length"]
    assert eq and eq[0]["args"] == {"segment_a": ["S", "A"], "segment_b": ["A", "B"]}
    assert eq[0]["quote"] == "SA = AB"


@pytest.mark.parametrize("bad", ["SA = AA", "SA = AS", "SA = 2AB"])
def test_degenerate_repeated_or_scaled_equalities_are_not_congruences(bad):
    r = _parse(f"Cho hình chóp S.ABC có SA vuông góc với đáy và {bad}. Tính thể tích khối chóp S.ABC.")
    assert not any(p["kind"] == "equal_length" and p.get("quote") == bad for p in (r.payload or {}).get("premises", []))
    assert r.status != LOCAL_PARSE_COMPLETE or bad == "SA = 2AB"


def test_scale_free_equality_problem_refuses_safely_instead_of_inventing_a_length():
    # Never guess a length. Run `target-invariant-regular-solid-semantics`: this figure (no length, BC/AB open) is now
    # served ONLY under a proven, independently verified target-invariance certificate (∠ = ∠SBA of the right isosceles
    # SAB), on an illustrative figure whose lengths are never source data; without the deciding fact SA = AB there is
    # no proof and the kernel still refuses.
    status, _answers, reason = _solve(
        "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với đáy. "
        "Tính góc giữa hai mặt phẳng (SBC) và (ABC).")
    assert status == "REFUSED" and reason == "MISSING_DIMENSION"
    from app.ai.adaptive_input_router import route_text_input
    rd = route_text_input("Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
                          "Tính góc giữa hai mặt phẳng (SBC) và (ABC).", allow_live_ai=False).response["route_d"]
    cfg = rd["scene_configuration"]
    assert rd["status"] == "SERVED" and cfg["kind"] == "TARGET_INVARIANT_ILLUSTRATIVE" and cfg["unique"] is False
    assert cfg["source_length_supplied"] is False
    assert cfg["invariance_certificate"]["certification_level"] == "MATHEMATICALLY_PROVEN"


# ── Volume goal wording ─────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("goal", ["Tính thể tích lăng trụ ABC.A'B'C'.", "Tính thể tích V của khối lăng trụ đó.",
                                  "Tính thể tích V của khối lăng trụ ABC.A'B'C'."])
def test_volume_goal_without_khoi_or_with_named_variable(goal):
    # right isosceles base with legs a, height 2a ⇒ V = a³
    status, answers, reason = _solve(
        f"Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, BC = a, AA' = 2a. {goal}")
    assert status == "SERVED", reason
    assert list(answers.values()) == ["a³"]


def test_volume_goal_naming_an_undeclared_solid_stays_unparsed():
    r = _parse("Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, BC = a, AA' = 2a. "
               "Tính thể tích lăng trụ DEF.D'E'F'.")
    assert r.status != LOCAL_PARSE_COMPLETE


# ── Source Gate: "… theo a bằng" is a question; "… theo a bằng 2" is not ─────────────────────────────────────────────
def test_multiple_choice_question_with_theo_a_tail_is_asked():
    # V = (1/3)·(a²/2)·a
    status, answers, reason = _solve(
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, SA vuông góc với mặt đáy (ABC), "
        "SA = a. Thể tích khối chóp S.ABC theo a bằng")
    assert status == "SERVED", reason
    assert list(answers.values()) == ["a³/6"]


def test_theo_a_tail_with_a_value_is_an_assignment_not_a_question():
    r = _parse("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, SA vuông góc với mặt đáy (ABC), "
               "SA = a. Thể tích khối chóp S.ABC theo a bằng 2a³.")
    assert r.status != LOCAL_PARSE_COMPLETE


# ── Clause diagnostics ──────────────────────────────────────────────────────────────────────────────────────────────
def test_unparsed_clause_reports_the_guard_that_held_it():
    r = _parse("Cho hình chóp S.ABC có SA vuông góc với đáy và SA = AA. Tính thể tích khối chóp S.ABC.")
    notes = [n for c in r.source_coverage.clauses if c["classification"].startswith("UNPARSED") for n in c.get("notes", [])]
    assert notes and notes[0].startswith("UNBACKED_EQUALS@")
    # a fully mapped clause carries no notes key at all
    assert all("notes" not in c for c in r.source_coverage.clauses if c["classification"].startswith("MAPPED"))


# ── "vuông (cân) ở X" ≡ "vuông (cân) tại X" ─────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("at,answer", [("vuông cân ở B, AB = a", "a³/6"), ("vuông ở B, AB = a, BC = 2a", "a³/3"),
                                       ("vuông cân tại B, AB = a", "a³/6")])
def test_right_triangle_vertex_with_o_or_tai(at, answer):
    status, answers, reason = _solve(f"Cho hình chóp S.ABC có đáy ABC là tam giác {at}, SA vuông góc với mặt đáy (ABC), "
                                     "SA = a. Tính thể tích khối chóp S.ABC.")
    assert status == "SERVED", reason
    assert list(answers.values()) == [answer]


# ── A value is closed by a clause opening right after it, even without punctuation ─────────────────────────────────────
def test_value_closed_by_bien_and_by_a_new_capitalised_sentence():
    # BC ⊥ (ABB'A') ⇒ the plane angle is ∠A'BA = 60° ⇒ AA' = a√3, V = (a²/2)·a√3
    status, answers, reason = _solve(
        "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B với BC = a biết mặt phẳng (A'BC) hợp với "
        "đáy (ABC) một góc 60°. Tính thể tích lăng trụ ABC.A'B'C'.")
    assert status == "SERVED", reason
    assert list(answers.values()) == ["a³√3/2"]
    status, answers, reason = _solve("Cho hình hộp chữ nhật ABCD.A'B'C'D' có cạnh AA' = 1, AB = 2, AD = 3 Tính khoảng cách "
                                     "từ điểm A' đến mặt phẳng (ABCD).")
    assert status == "SERVED", reason
    assert list(answers.values()) == ["1"]


@pytest.mark.parametrize("text,code", [
    # a capital letter followed by another capital is a label: "2 BC" is a multiple, never "AB = 2"
    ("Cho hình hộp chữ nhật ABCD.A'B'C'D' có cạnh AA' = 1, AB = 2 BC. Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.",
     "MISSING_DIMENSION"),
    ("Cho hình hộp chữ nhật ABCD.A'B'C'D' có AA' = 1, AB = 2 hoặc AB = 3, AD = 1. Tính thể tích khối hộp chữ nhật "
     "ABCD.A'B'C'D'.", "NEGATED_CLAUSE"),
])
def test_value_boundary_does_not_accept_multiples_or_disjunctions(text, code):
    status, _answers, reason = _solve(text)
    assert status == "REFUSED" and reason == code
