# -*- coding: utf-8 -*-
"""SL-2 (tenth continuation): the `typed-fact-next/2` honest exit and the `route-d-clarification/1` record.

The flat contract lets an extractor say `ambiguous` / `unsupported`; `/2` had no such exit, so "Mô phỏng điểm S là góc
chiếu của hình lăng trụ xiên." could only be guessed or rejected as malformed. An `unresolved` entry is never a fact: any
entry refuses the payload with an existing code, and the server — not the model — writes the clarification record from
closed vocabularies and the verbatim quote.
"""
from __future__ import annotations

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions.typed_fact_next import (
    TypedFactNextValidationError, parse_typed_fact_next, parse_typed_fact_next_v2,
)

GOC_CHIEU = "Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên."
STD = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
       "Tính thể tích khối chóp S.ABCD.")


def _u(kind="ambiguous", quote="S là góc chiếu của hình lăng trụ xiên", missing=("source_point", "target_line_or_plane"),
       candidates=("orthogonal_projection",), subject="S", **extra):
    u = {"unresolved_id": "u1", "kind": kind, "quote": quote, "missing_roles": list(missing),
         "candidate_relations": list(candidates), **extra}
    if subject:
        u["subject_ref"] = subject
    return u


def _only(text=GOC_CHIEU, *entries):
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "unresolved": list(entries or [_u()])}


def _servable(*entries, text=STD):
    def p(kind, quote, **args):
        return {"kind": kind, "args": args, "quote": quote, "solid_id": "s1"}
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
            "premises": [p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
                         p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABCD)", line=["S", "A"],
                           plane=list("ABCD")),
                         p("segment_length", "SA = 2", segment=["S", "A"], value="2")],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                                  "quote": "Cho hình chóp S.ABCD"}],
            "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"},
                            "quote": "Tính thể tích khối chóp S.ABCD", "solid_id": "s1"}],
            **({"unresolved": list(entries)} if entries else {})}


# --- schema -----------------------------------------------------------------------------------------------------------
def test_an_unresolved_only_payload_is_valid_without_solids_or_goals():
    p = parse_typed_fact_next_v2(_only())
    assert p.unresolved[0].kind == "ambiguous" and not p.solids and not p.simulation_goals


def test_without_unresolved_the_simulation_first_rules_still_hold():
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next_v2({"schema_version": "typed-fact-next/2", "problem_text": GOC_CHIEU})
    assert e.value.code == "EMPTY_SOLIDS"


def test_v1_never_reads_the_v2_exit():
    raw = {**_servable(_u(quote="SA = 2", subject=None)), "schema_version": "typed-fact-next/1"}
    with pytest.raises(TypedFactNextValidationError):
        parse_typed_fact_next(raw)


@pytest.mark.parametrize("bad", [
    {"kind": "guess"},
    {"missing_roles": ["coordinates"]},
    {"candidate_relations": ["tangent_line"]},
    {"candidate_relations": ["angle", "distance", "midpoint", "intersection"]},   # at most three readings
    {"subject_ref": "s"},                                                           # not a label
    {"subject_ref": "B"},                                                           # not in its own quote
    {"unresolved_id": ""},
    {"reason": "free prose"},                                                       # closed model
])
def test_the_exit_is_a_closed_vocabulary(bad):
    with pytest.raises(TypedFactNextValidationError):
        parse_typed_fact_next_v2(_only(GOC_CHIEU, {**_u(), **bad}))


def test_unresolved_ids_are_unique():
    with pytest.raises(TypedFactNextValidationError):
        parse_typed_fact_next_v2(_only(GOC_CHIEU, _u(), _u()))


# --- route ------------------------------------------------------------------------------------------------------------
def test_goc_chieu_is_refused_with_a_server_built_clarification():
    r = run_typed_fact_next_v2_route(_only())
    assert (r.status, r.code) == ("REFUSED", "AMBIGUOUS_FACT")
    clar = r.route_d["refusal"]["clarification"]
    start = GOC_CHIEU.index("S là góc chiếu")
    assert clar == {
        "schema_version": "route-d-clarification/1", "unresolved_id": "u1", "kind": "ambiguous", "nlu_class": "AMBIGUOUS",
        "quote": "S là góc chiếu của hình lăng trụ xiên",
        "spans": [[start, start + len("S là góc chiếu của hình lăng trụ xiên")]],
        "subject_ref": "S", "missing_roles": ["source_point", "target_line_or_plane"],
        "candidate_relations": ["orthogonal_projection"],
        "question": "Trong “S là góc chiếu của hình lăng trụ xiên”, bạn muốn S là hình chiếu của điểm nào và lên đường "
                    "thẳng hoặc mặt phẳng nào?",
    }
    assert r.route_d["answers"] == {} and r.route_d["construction_trace"] == [] and r.scene3d is None


@pytest.mark.parametrize("kind,code,nlu", [
    ("ambiguous", "AMBIGUOUS_FACT", "AMBIGUOUS"),
    ("missing_operand", "AMBIGUOUS_FACT", "MISSING_DATA"),
    ("unrecognized_term", "AMBIGUOUS_FACT", "UNRECOGNIZED_WORDING"),
    ("unsupported", "OUT_OF_SCOPE", "VALID_BUT_UNSUPPORTED"),
])
def test_each_kind_maps_to_an_existing_code(kind, code, nlu):
    r = run_typed_fact_next_v2_route(_only(GOC_CHIEU, _u(kind=kind)))
    assert (r.status, r.code) == ("REFUSED", code)
    assert r.route_d["refusal"]["clarification"]["nlu_class"] == nlu


def test_unsupported_has_no_clarifying_question():
    r = run_typed_fact_next_v2_route(_only(GOC_CHIEU, _u(kind="unsupported", missing=(), candidates=(), subject=None)))
    assert r.route_d["refusal"]["clarification"]["question"] is None


def test_question_without_candidates_names_what_is_missing():
    r = run_typed_fact_next_v2_route(_only("Mô phỏng hình lăng trụ.", _u(kind="missing_operand", quote="Mô phỏng hình lăng trụ",
                                                                         missing=("solid_notation", "dimension"),
                                                                         candidates=(), subject=None)))
    assert r.route_d["refusal"]["clarification"]["question"] == (
        "Trong “Mô phỏng hình lăng trụ”, bạn hãy nói rõ tên các đỉnh của hình và các số đo cần thiết.")


def test_an_unresolved_entry_blocks_an_otherwise_servable_payload():
    assert run_typed_fact_next_v2_route(_servable()).status == "SERVED"
    r = run_typed_fact_next_v2_route(_servable(_u(kind="ambiguous", quote="SA = 2", missing=("dimension",), candidates=(),
                                                  subject=None)))
    assert (r.status, r.code) == ("REFUSED", "AMBIGUOUS_FACT")
    assert r.route_d["answers"] == {} and r.route_d["relation_certificates"] == []


def test_every_occurrence_of_a_repeated_quote_is_a_span():
    text = "Mô phỏng hình lăng trụ. Mô phỏng hình lăng trụ."
    r = run_typed_fact_next_v2_route(_only(text, _u(kind="missing_operand", quote="Mô phỏng hình lăng trụ",
                                                    missing=("solid_notation",), candidates=(), subject=None)))
    assert r.route_d["refusal"]["clarification"]["spans"] == [[0, 22], [24, 46]]


def test_other_refusals_carry_no_clarification_key():
    r = run_typed_fact_next_v2_route({**_servable(), "premises": _servable()["premises"][:1]})
    assert r.status == "REFUSED" and "clarification" not in r.route_d["refusal"]


# --- the production offline boundary (extraction validation + Adapter /4 wrapper) -------------------------------------
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def test_wrapper_keeps_the_frontend_envelope_and_adds_the_record_to_route_d():
    out = run_hybrid_offline(GOC_CHIEU, ReplayExtractor({GOC_CHIEU: _only()}), policy=POLICY).response
    env, route = out["envelope"], out["route_d"]
    assert env["status"] == "unsupported" and env["reason_code"] == "AMBIGUOUS_FACT"
    assert env["failure_category"] == "insufficient_specification" and "clarification" not in env
    assert route["refusal"]["code"] == env["reason_code"]
    assert route["refusal"]["clarification"]["kind"] == "ambiguous"


def test_a_non_verbatim_unresolved_quote_is_refused_at_extraction():
    raw = _only(GOC_CHIEU, _u(quote="S là hình chiếu của A'"))
    out = run_hybrid_offline(GOC_CHIEU, ReplayExtractor({GOC_CHIEU: raw}), policy=POLICY).response
    assert out["envelope"]["reason_code"] == "QUOTE_NOT_IN_SOURCE"
    assert "clarification" not in out["route_d"]["refusal"]


def test_other_wrapper_refusals_are_unchanged():
    raw = {**_servable(), "premises": _servable()["premises"][:1]}
    out = run_hybrid_offline(STD, ReplayExtractor({STD: raw}), policy=POLICY).response
    assert out["route_d"]["refusal"] == {"code": out["envelope"]["reason_code"]}
