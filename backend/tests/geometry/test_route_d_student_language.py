# -*- coding: utf-8 -*-
"""Route D (/4) student wording (tenth continuation, `student-language-probe.json`).

SL-1: a simulation request ("Vẽ / Dựng / Mô phỏng / Cho mình xem hình chóp …", "Hãy mô phỏng hình và điểm M.") is read by
ONE closed reader: it may open a solid clause like "Cho", or only mention objects the validated calls already build. It
adds no fact, so smuggled givens, unbuilt objects and other requests stay unread. Same-givens oracle: V = 8/3, SC² = 12,
AM² = 3 on S.ABCD (square side 2, SA ⊥ (ABCD), SA = 2).
"""
from __future__ import annotations

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route

C1 = "có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2"
STD = f"Cho hình chóp S.ABCD {C1}."
VOL = "Tính thể tích khối chóp S.ABCD"


def _p(kind, quote, **args):
    return {"kind": kind, "args": args, "quote": quote, "solid_id": "s1"}


def _payload(text, solid_quote, goals=(), sim=None, extra=(), perp="SA vuông góc với mặt phẳng (ABCD)",
             length="SA = 2", premises=None):
    prem = premises if premises is not None else [
        _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
        _p("perpendicular_line_plane", perp, line=["S", "A"], plane=list("ABCD")),
        _p("segment_length", length, segment=["S", "A"], value="2"), *extra]
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": solid_quote}],
            "premises": prem, "derived_sections": [], "relations": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                                  "quote": sim or solid_quote}],
            "math_goals": list(goals)}


def _vol(quote=VOL):
    return {"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"},
            "quote": quote, "solid_id": "s1"}


def _len(seg, quote):
    return {"goal_id": "mg1", "kind": "measurement", "goal_type": "distance", "target": {"segment": seg},
            "quote": quote, "solid_id": "s1"}


MID_M = _p("midpoint", "Gọi M là trung điểm của SC", point="M", segment=["S", "C"])


@pytest.mark.parametrize("verb", ["Vẽ", "Dựng", "Mô phỏng", "Cho mình xem", "Hãy vẽ", "Hãy mô phỏng", "Vẽ giúp mình"])
def test_simulation_verb_opens_the_solid_clause(verb):
    text = f"{verb} hình chóp S.ABCD {C1}."
    r = run_typed_fact_next_v2_route(_payload(text, "hình chóp S.ABCD", sim=f"{verb} hình chóp S.ABCD"))
    assert (r.status, r.code) == ("SERVED", None), r.reason


def test_simulation_opener_still_binds_the_question():
    text = f"Vẽ hình chóp S.ABCD {C1}. {VOL}."
    r = run_typed_fact_next_v2_route(_payload(text, "hình chóp S.ABCD", [_vol()], sim="Vẽ hình chóp S.ABCD"))
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] == "8/3"


@pytest.mark.parametrize("tail,sim", [
    ("Vẽ hình chóp S.ABCD.", "Vẽ hình chóp S.ABCD"),
    ("Hãy mô phỏng hình.", "Hãy mô phỏng hình"),
    ("Mô phỏng hình chóp.", "Mô phỏng hình chóp"),
    ("Cho mình xem hình chóp S.ABCD và đường thẳng SC.", "Cho mình xem hình chóp S.ABCD"),
])
def test_trailing_simulation_request_mentions_only_built_objects(tail, sim):
    text = f"{STD} {tail}"
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD", sim=sim))
    assert (r.status, r.code) == ("SERVED", None), r.reason


def test_simulation_request_names_a_constructed_point():
    text = f"{STD} Gọi M là trung điểm của SC. Hãy mô phỏng hình và điểm M."
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD", sim="Hãy mô phỏng hình và điểm M",
                                              extra=[MID_M]))
    assert (r.status, r.code) == ("SERVED", None), r.reason


@pytest.mark.parametrize("ask,goal", [
    ("Vẽ hình rồi tính thể tích khối chóp S.ABCD.", _vol("tính thể tích khối chóp S.ABCD")),
    ("Mô phỏng hình chóp và tính độ dài SC.", _len(["S", "C"], "tính độ dài SC")),
    ("Không cần vẽ hình, tính thể tích khối chóp S.ABCD.", _vol("tính thể tích khối chóp S.ABCD")),
])
def test_simulation_clause_before_a_question_in_one_sentence(ask, goal):
    text = f"{STD} {ask}"
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD", [goal]))
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] in ("8/3", "2√3")


def test_student_chain_with_simulation_opener_and_request():
    text = f"Vẽ hình chóp S.ABCD {C1}. Gọi M là trung điểm SC. Mô phỏng hình và tính độ dài AM."
    r = run_typed_fact_next_v2_route(_payload(
        text, "hình chóp S.ABCD", [_len(["A", "M"], "tính độ dài AM")], sim="Vẽ hình chóp S.ABCD",
        extra=[_p("midpoint", "Gọi M là trung điểm SC", point="M", segment=["S", "C"])]))
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] == "√3"


# --- adversarial locks: the reader adds no fact, so these stay unread -------------------------------------------------
@pytest.mark.parametrize("tail", [
    "Vẽ hình chóp với SC = 5.",                    # a smuggled given
    "Vẽ hình và điểm M.",                          # an object no call builds
    "Vẽ hình chóp S.ABC.",                         # another solid
    "Vẽ hình lăng trụ.",                           # another kind of solid
    "Vẽ hình vuông ABCD có cạnh 3.",               # a shape claim with a number
    "Vẽ hình rồi chỉ ra đường cao của hình chóp.",  # a request the backend cannot certify
    "Vẽ đường cao SH của hình chóp.",              # a new object with a role claim
    "Nếu vẽ hình chóp S.ABCD thì SA = 3.",          # conditional
])
def test_simulation_request_never_reads_unbuilt_or_new_content(tail):
    text = f"{STD} {tail}"
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD"))
    assert r.status == "REFUSED", tail


def test_simulation_request_does_not_answer_a_dropped_question():
    text = f"{STD} Vẽ hình rồi tính thể tích khối chóp S.ABCD."
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD"))
    assert (r.status, r.code) == ("REFUSED", "REQUEST_NOT_ANSWERED")


def test_simulation_verb_does_not_open_a_solid_with_a_new_name():
    text = f"Vẽ hình chóp S.ABCD {C1}. Vẽ thêm hình chóp S.MNPQ."
    r = run_typed_fact_next_v2_route(_payload(text, "hình chóp S.ABCD", sim="Vẽ hình chóp S.ABCD"))
    assert r.status == "REFUSED"


# --- givens wording (S02, S08) ----------------------------------------------------------------------------------------
def test_perpendicular_without_preposition_keeps_the_sentence_readable():
    text = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc đáy và SA = 2. {VOL}."
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD", [_vol()], perp="SA vuông góc đáy"))
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] == "8/3"


def _altitude(text, apex_foot=("S", "A")):
    return _payload(text, "Cho hình chóp S.ABCD", [_vol()], premises=[
        _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
        # the altitude function's own contract wants its solid in the quote ("chóp")
        _p("altitude", f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường cao {''.join(apex_foot)}",
           apex=apex_foot[0], foot=apex_foot[1]),
        _p("segment_length", f"{''.join(apex_foot)} = 2", segment=list(apex_foot), value="2")])


def test_altitude_role_before_a_labelled_length():
    r = run_typed_fact_next_v2_route(_altitude(f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường cao SA = 2. {VOL}."))
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] == "8/3"


def test_altitude_role_claim_on_an_unproved_segment_stays_unread():
    # "đường cao SB = 2" while the validated altitude is SA: the role claim is not proved, so the sentence binds nothing
    text = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA là đường cao, đường cao SB = 2. {VOL}."
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD", [_vol()], premises=[
        _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
        _p("altitude", "SA là đường cao", apex="S", foot="A"),
        _p("segment_length", "SB = 2", segment=["S", "B"], value="2")]))
    assert r.status == "REFUSED"


# --- D02: a base no source constrains is missing data, not an unsupported shape -----------------------------------------
@pytest.mark.parametrize("text,sim", [("Vẽ hình chóp S.ABCD.", "Vẽ hình chóp S.ABCD"),
                                      ("Cho hình chóp S.ABCD.", "Cho hình chóp S.ABCD")])
def test_a_base_without_any_length_is_missing_dimension(text, sim):
    r = run_typed_fact_next_v2_route(_payload(text, sim if text.startswith("Cho") else "hình chóp S.ABCD", sim=sim,
                                              premises=[]))
    assert (r.status, r.code) == ("REFUSED", "MISSING_DIMENSION"), r.reason


def test_a_base_with_lengths_but_no_layout_rule_stays_an_unsupported_shape():
    text = "Cho hình chóp S.ABCD có AB = 2, BC = 3, CD = 4 và DA = 5."
    r = run_typed_fact_next_v2_route(_payload(text, "Cho hình chóp S.ABCD", premises=[
        _p("segment_length", f"{s} = {v}", segment=list(s), value=v)
        for s, v in (("AB", "2"), ("BC", "3"), ("CD", "4"), ("DA", "5"))]))
    assert (r.status, r.code) == ("REFUSED", "UNSUPPORTED_BASE_SHAPE"), r.reason
