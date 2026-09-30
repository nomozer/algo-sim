# -*- coding: utf-8 -*-
"""W12 — a GIVEN measurement must be evidenced by the SOURCE, 0 model calls.

`ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED`: `build_request_contract`
already marks an analyze value that the problem text does not contain as
`provenance="claimed"` with `unproven_values`, "so that a later gate has
something to refuse" — and no gate read it. The length invariants were also
built from analyze facts, not only from the text, so the w11 invariant channel
was not text-grounded either. The w11 probe copied an already-built contract,
so it never crossed the production boundary; these tests do.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline as PL
from app.learner_messages import attach_learner_reason
from app.simulation.geometry_compiler.compiler import bien_dich
from app.simulation.geometry_compiler.contract_adapter import build_fact_graph
from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen
from app.simulation.semantic_program import grounding_gate as G
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.validator import validate_semantic_program

PRISM_TEXT = (
    "Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, "
    "AB = 3, AC = 4. Cạnh bên AD = 5. Tính thể tích khối lăng trụ ABC.DEF."
)
#: The same problem with the height sentence removed — nothing says AD = 5.
PRISM_WITHOUT_AD = PRISM_TEXT.replace(" Cạnh bên AD = 5.", "")


def _prism_payload(ad_value: str = "5") -> dict:
    """What a fake analyze transport returns: the height is still there."""
    return {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
            {"id": "fact_len_AD", "kind": "float", "label": "AD", "value": [ad_value]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "fact_perp_base", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["A", "D"], "plane": ["A", "B", "C"],
             "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        "obligations": [
            {"kind": "volume", "container": "solid_ABCDEF", "witness": "the_tich_lang_tru"},
        ],
        "solid_topology": {
            "solid_kind": "prism", "base_cycle": ["A", "B", "C"], "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
        },
    }


def _contract(text: str, payload: dict):
    return build_request_contract(payload, problem_text=text, domain="hinh_hoc")


def _program_with_height_5() -> dict:
    """The program a model writes when it believes AD = 5 (compiled from the full text)."""
    graph = build_fact_graph(_contract(PRISM_TEXT, _prism_payload())).graph
    return {"spec_version": "1.0", **bien_dich(graph).program}


def _spec(program: dict):
    val = validate_semantic_program(program)
    assert val.ok and val.spec is not None, val.error
    return val.spec


# ── Task test 7 + the mandatory probe: the PRODUCTION boundary refuses ────────

def test_production_route_refuses_a_height_the_problem_does_not_state(monkeypatch):
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)  # default LLM_ONLY
    responses = [json.dumps(_prism_payload()), json.dumps(_program_with_height_5(), default=str)]
    calls: list[str] = []

    async def fake_transport(*_args, **_kwargs):
        calls.append("call")
        return responses[len(calls) - 1]

    monkeypatch.setattr(PL, "call_gemini", fake_transport)
    env = attach_learner_reason(asyncio.run(PL.run_pipeline(PRISM_WITHOUT_AD, "fake_key")))

    assert env["status"] == "unsupported", env
    assert "scene3d" not in env and "final_memory" not in env
    assert env["error_code"] == "input_not_grounded"
    assert env["stage_reached"] == "grounding"
    assert env["reason_code"] == G.ERR_GIVEN_KHONG_CO_TRONG_DE
    # A source defect is not a writing defect: no repair round is spent on it.
    assert len(calls) == 2
    msg = env["learner_reason"]
    assert "đề" in msg and "_" not in msg and "GIVEN" not in msg


def test_compiler_route_never_turns_a_claimed_length_into_a_given_fact():
    contract = _contract(PRISM_WITHOUT_AD, _prism_payload())
    assert contract.fact("fact_len_AD").provenance == "claimed"
    # The length invariants come from the SOURCE, not from an unproven analyze value.
    assert not any(set(b.points) == {"A", "D"} for b in contract.source_invariants)
    decision = quyet_dinh_dinh_tuyen(contract, {"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"})
    assert decision.decision != "USE_COMPILER"
    assert decision.reason_code == "REQUIRED_FACT_MISSING"


def test_the_same_height_stated_in_the_text_is_accepted_with_its_evidence():
    contract = _contract(PRISM_TEXT, _prism_payload())
    ground = G.check_grounding(contract, _spec(_program_with_height_5()))
    assert ground.ok, ground.unresolved
    ev = {e["name"]: e for e in ground.given_evidence}
    assert set(ev) == {"AB_length", "AC_length", "AD_length"}
    ad = ev["AD_length"]
    assert ad["source_kind"] == "problem_text" and ad["provenance"] == "confirmed"
    assert ad["source_fact_id"] == "fact_len_AD" and ad["value"] == "5" and ad["unit"] is None
    s, e = ad["span"]
    assert PRISM_TEXT[s:e] == ad["span_text"] and "5" in ad["span_text"]


# ── Task test 8: a span that does not map onto the text ──────────────────────

def test_source_span_that_does_not_match_the_problem_text_is_refused():
    contract = _contract(PRISM_TEXT, _prism_payload())
    ad = contract.fact("fact_len_AD")
    four = PRISM_TEXT.index("4")
    moved = ad.model_copy(update={"source_start": four, "source_end": four + 1})
    facts = tuple(moved if f.fact_id == ad.fact_id else f for f in contract.input_facts)
    ground = G.check_grounding(contract.model_copy(update={"input_facts": facts}),
                               _spec(_program_with_height_5()))
    assert not ground.ok and ground.error_code == G.ERR_SPAN_LECH_DE


# ── Task test 9: value / segment / unit in the evidence contradict the fact ──

@pytest.mark.parametrize("text", [
    # The text states a DIFFERENT length for the same segment.
    "Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, "
    "AB = 3, AC = 4, BC = 5. Cạnh bên AD = 6. Tính thể tích khối lăng trụ ABC.DEF.",
    # The only 5 in the text belongs to ANOTHER segment.
    "Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, "
    "AB = 3, AC = 4, BC = 5. Tính thể tích khối lăng trụ ABC.DEF.",
])
def test_evidence_that_names_another_value_or_segment_is_a_conflict(text):
    contract = _contract(text, _prism_payload())
    assert contract.fact("fact_len_AD").provenance == "confirmed"  # 5 is SOMEWHERE in the text
    ground = G.check_grounding(contract, _spec(_program_with_height_5()))
    assert not ground.ok and ground.error_code == G.ERR_BANG_CHUNG_MAU_THUAN
    assert any("AD_length" in u for u in ground.unresolved)


def test_unit_in_the_evidence_contradicting_the_fact_is_a_conflict():
    text = ("Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, "
            "AB = 3 cm, AC = 4 cm. Cạnh bên AD = 5 cm. Tính thể tích khối lăng trụ ABC.DEF.")
    contract = _contract(text, _prism_payload(ad_value="5 m"))
    ground = G.check_grounding(contract, _spec(_program_with_height_5()))
    assert not ground.ok and ground.error_code == G.ERR_BANG_CHUNG_MAU_THUAN


# ── Task tests 10–11: legitimate derivations and layout are not GIVEN ────────

def test_cube_equal_edges_are_derived_and_not_refused_as_ungrounded():
    from tests.geometry.test_cuboid_cube_production_route import _cube_p01_payload

    text, payload = _cube_p01_payload()
    contract = _contract(text, payload)
    spec = _spec({"spec_version": "1.0", **bien_dich(build_fact_graph(contract).graph).program})
    outcome = verify_and_compile(contract, spec)
    assert outcome.servable, outcome.details
    ground = G.check_grounding(contract, spec)
    given = {e["name"] for e in ground.given_evidence}
    # "có cạnh bằng 4": ONE given edge; the other edges are computed from it.
    assert given == {"AB_length"}
    assert {"AD_length", "AA_prime_length"}.isdisjoint(given)


def test_layout_derived_coordinates_are_never_given_evidence():
    contract = _contract(PRISM_TEXT, _prism_payload())
    ground = G.check_grounding(contract, _spec(_program_with_height_5()))
    assert all(e["name"].endswith("_length") for e in ground.given_evidence)
    assert {"A|point3|A|layout_derived_vertex"} <= set(ground.justified_literals)


# ── Task test 12: the refusal carries a stable, structured code ──────────────

def test_grounding_refusal_codes_are_a_closed_stable_set():
    assert G.MA_LOI_NGUON == frozenset({
        "GIVEN_VALUE_NOT_IN_SOURCE", "SOURCE_SPAN_MISMATCH", "SOURCE_EVIDENCE_CONFLICT"})
    # A source defect is never sent back to the model to "repair".
    assert G.MA_LOI_NGUON <= PL.KHONG_SUA_NGUON
    contract = _contract(PRISM_WITHOUT_AD, _prism_payload())
    outcome = verify_and_compile(contract, _spec(_program_with_height_5()))
    assert not outcome.servable and outcome.scene3d is None
    assert outcome.error_code == "input_not_grounded"
    assert outcome.reason_code == G.ERR_GIVEN_KHONG_CO_TRONG_DE


# ── Non-integer lengths: a stated fraction, decimal or radical is evidence ───
# Found by the compiler A/B benchmark (case B03: `DE = 3/2`): the first cut
# looked the value up in the literal extractor, which reads integers and
# decimals only, so a STATED fraction looked absent. The segment reader had
# the opposite defect: it cut `2.5` to `2` and `2√3` to `2`.

def _program_with_height(value: str) -> dict:
    program = _program_with_height_5()
    for d in program["memory_declarations"]:
        if d["name"] == "AD_length":
            d["initial_value"] = value
    return program


@pytest.mark.parametrize("value,written", [
    ("3/2", "3/2"), ("2.5", "2.5"), ("2.5", "2,5"), ("2√3", "2√3"), ("2√3", "2 √3"),
])
def test_a_stated_non_integer_height_is_evidenced_by_the_text(value, written):
    text = PRISM_TEXT.replace("AD = 5", f"AD = {written}")
    contract = _contract(text, _prism_payload(ad_value=value))
    ground = G.check_grounding(contract, _spec(_program_with_height(value)))
    assert ground.ok, ground.unresolved
    ad = {e["name"]: e for e in ground.given_evidence}["AD_length"]
    s, e = ad["span"]
    assert text[s:e] == ad["span_text"]
    assert ad["span_text"].replace(" ", "") == written.replace(" ", "")


@pytest.mark.parametrize("value", ["3/2", "2.5", "2√3"])
def test_an_unstated_non_integer_height_is_refused(value):
    contract = _contract(PRISM_WITHOUT_AD, _prism_payload(ad_value=value))
    ground = G.check_grounding(contract, _spec(_program_with_height(value)))
    assert not ground.ok and ground.error_code == G.ERR_GIVEN_KHONG_CO_TRONG_DE


@pytest.mark.parametrize("text,expected", [
    ("AB = 2.5", {"AB": "5/2"}),
    ("AB = 1,5 cm", {"AB": "3/2"}),
    ("DE = 3/2, DF = 8/3", {"DE": "3/2", "DF": "8/3"}),
    ("AB = 3, AC = 4", {"AB": "3", "AC": "4"}),
    ("SA = 2√3", {}),
    ("AB = 3√2/2", {}),
    ("đoạn AB có độ dài 2√3", {}),
])
def test_the_source_length_reader_never_truncates_a_number(text, expected):
    from app.simulation.semantic_program.segment_relation import do_dai_trong_de

    got = {"".join(sorted(k)): str(v) for k, v in do_dai_trong_de(text).items()}
    assert got == expected


# ── A GIVEN point whose coordinates only an analyze claim states ────────────
# Found while building the w12 negatives: the cross-section text WITHOUT the
# apex "S(0;0;6)" was still served (V = 72). The apex is declared from the
# analyze fact `S_coords = "S(0;0;6)"`; a coordinate string is not a rational,
# so the gate read the fact as RELATIONAL (no numbers to compare) and accepted
# the coordinates, and the claim no longer builds a coordinate invariant.

def test_a_point_pinned_to_an_unstated_coordinate_claim_is_refused(monkeypatch):
    from scripts import replay_negative_boundaries as RNB

    case = "p1_chop_thiet_dien_khoang_cach"
    raw = RNB.doc_raw_theo_thu_tu(case)
    text = RNB.doc_de_bai()[case]
    cut = text.replace(" và đỉnh S(0;0;6)", "")
    assert cut != text
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    responses = [raw["semantic_analyze"][0], raw["semantic_program"][0]]
    calls: list[str] = []

    async def fake_transport(*_args, **_kwargs):
        calls.append("call")
        return responses[len(calls) - 1]

    monkeypatch.setattr(PL, "call_gemini", fake_transport)
    env = attach_learner_reason(asyncio.run(PL.run_pipeline(cut, "fake_key")))
    assert env["status"] == "unsupported", env.get("status")
    assert "scene3d" not in env
    assert env["reason_code"] == G.ERR_GIVEN_KHONG_CO_TRONG_DE
    assert len(calls) == 2


def test_a_paraphrased_relation_without_numbers_still_grounds_coordinates():
    # The same case WITH the apex stated is served: the coordinate facts are
    # in the text, and relation facts carry no numbers to prove.
    from scripts import replay_negative_boundaries as RNB

    case = "p1_chop_thiet_dien_khoang_cach"
    raw = RNB.doc_raw_theo_thu_tu(case)
    text = RNB.doc_de_bai()[case]
    contract = _contract(text, json.loads(raw["semantic_analyze"][0]))
    ground = G.check_grounding(contract, _spec(json.loads(raw["semantic_program"][0])))
    assert ground.ok, ground.unresolved


def test_the_refusal_names_a_point_as_a_point_not_as_a_length():
    from app.learner_messages import learner_reason

    point = {"status": "unsupported", "reason_code": G.ERR_GIVEN_KHONG_CO_TRONG_DE,
             "reason_subjects": ["S"]}
    segment = {**point, "reason_subjects": ["AA′"]}
    unknown = {**point, "reason_subjects": []}
    assert "toạ độ điểm S" in learner_reason(point)
    assert "độ dài" not in learner_reason(point)
    assert "độ dài AA′" in learner_reason(segment)
    assert "một số liệu" in learner_reason(unknown)
