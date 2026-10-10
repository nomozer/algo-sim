"""Independent adversarial oracles for hybrid pre-pilot safety. No provider/network calls."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.ai import function_route as FR
from app.simulation.geometry_functions import planner as PL
from app.simulation.geometry_functions import registry as RG

FX = Path(__file__).parent / "fixtures"
ORACLE = json.loads((FX / "hybrid_safety_oracles.json").read_text(encoding="utf-8"))
CASES = {c["id"]: c for c in ORACLE["grounding_cases"]}
HOLD = {c["id"]: c for c in json.loads((FX / "hybrid_holdout_cases.json").read_text(encoding="utf-8"))["cases"]}


def _ground_a(c: dict) -> str:
    try:
        RG.kiem_nguon(RG.doc_ke_hoach({"calls": [c["call"]]}), c["text"])
    except RG.TuChoi as exc:
        return exc.code
    return "PASS"


def _ground_b(c: dict) -> str:
    try:
        plan = PL.lap_ke_hoach({"facts": [c["fact"]]})
        if c["fact"]["role"] == "prove":
            assert not plan.calls and [x["fact"] for x in plan.goals] == ["f1"]
            return "GOAL_NOT_PREMISE"
        calls = list(plan.calls) + [x["call"] for x in plan.negated]
        RG.kiem_nguon(RG.doc_ke_hoach({"calls": calls}), c["text"])
    except RG.TuChoi as exc:
        return exc.code
    return "PASS"


@pytest.mark.parametrize("cid", sorted(CASES))
def test_grounding_oracle_is_literal_and_shared_by_both_arms(cid):
    """Catches substring-only grounding or a B plan bypassing the shared source gate."""
    c = CASES[cid]
    assert _ground_a(c) == c["expect_a"], cid
    assert _ground_b(c) == c["expect_b"], cid


@pytest.mark.parametrize("cid", ["MULTIPLE_OBJECTS_CUBE", "MULTIPLE_OBJECTS_RECTANGLE", "FACT_OUTSIDE_QUOTE"])
def test_real_routes_reject_shape_keyword_borrowed_from_another_object(cid):
    """Catches accepting a call merely because its labels and a shape keyword occur somewhere in the source."""
    c = CASES[cid]
    a = FR.run_function_route(c["text"], {"calls": [c["call"]]})
    b = FR.run_fact_route(c["text"], {"facts": [c["fact"]]})
    assert (a.status, a.code) == ("REFUSED", "OBJECT_NOT_IN_QUOTE")
    assert (b.status, b.code) == ("REFUSED", "OBJECT_NOT_IN_QUOTE")


@pytest.mark.parametrize("fn", ["regular_polygon", "rectangle"])
def test_structural_phrase_binds_either_named_face_but_not_a_mixed_face(fn):
    """Catches checking only the first face, accepting any four labels, or combining labels across faces."""
    phrase = "hình lập phương ABCD.EFGH" if fn == "regular_polygon" else "hình hộp chữ nhật ABCD.EFGH"
    text = f"Cho {phrase}."
    for vertices, expected in [(["A", "B", "C", "D"], "PASS"), (["E", "F", "G", "H"], "PASS"),
                               (["A", "B", "G", "H"], "OBJECT_NOT_IN_QUOTE")]:
        call = {"id": "c1", "fn": fn, "args": {"vertices": vertices}, "source": {"quotes": [phrase]}}
        assert _ground_a({"text": text, "call": call}) == expected


def _facts(cid: str) -> list[dict]:
    return copy.deepcopy(HOLD[cid]["b_facts"])


@pytest.mark.parametrize("fn,phrase", [("regular_polygon", "hình lập phương"),
                                    ("rectangle", "hình hộp chữ nhật")])
def test_unnamed_solid_cue_cannot_capture_polygon_in_next_clause(fn, phrase):
    text = f"Cho {phrase}. Tứ giác KLMN là hình thoi."
    call = {"id": "c1", "fn": fn, "args": {"vertices": ["K", "L", "M", "N"]},
            "source": {"quotes": [text]}}
    assert _ground_a({"text": text, "call": call}) == "OBJECT_NOT_IN_QUOTE"


def test_true_on_configuration_is_not_reported_as_proof():
    """Catches mapping a Boolean check on one constructed layout to HOLDS/proved."""
    c = HOLD["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"]
    r = FR.run_fact_route(c["text"], {"facts": _facts(c["id"])})
    check = r.planner["goal_checks"]["f7"]
    assert check == {
        "evidence_state": "TRUE_ON_CONFIGURATION",
        "proof_status": "UNVERIFIABLE",
        "can_present_as_proven": False,
    }
    assert "HOLDS" not in json.dumps(r.planner, ensure_ascii=False)


def test_false_on_configuration_is_not_reported_as_disproved_theorem():
    """Catches promoting one counter-layout observation to PROOF_GOAL_FALSE."""
    c = HOLD["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"]
    facts = _facts(c["id"])
    facts[6].update(points_a=["A", "C"], quotes=["BC vuông góc với (SAB)"])
    r = FR.run_fact_route(c["text"], {"facts": facts})
    assert r.status == "SERVED"
    assert r.planner["goal_checks"]["f7"]["evidence_state"] == "FALSE_ON_CONFIGURATION"
    assert r.planner["goal_checks"]["f7"]["can_present_as_proven"] is False


def test_proof_only_request_without_certificate_refuses():
    """Catches a proof-only request being marked served from a configuration check."""
    c = HOLD["H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED"]
    facts = [f for f in _facts(c["id"]) if f["kind"] != "question"]
    r = FR.run_fact_route(c["text"], {"facts": facts})
    assert (r.status, r.code, r.scene3d) == ("REFUSED", "PROOF_UNVERIFIABLE", None)
    assert r.planner["goal_checks"]["f7"]["can_present_as_proven"] is False


def test_negated_configuration_observation_does_not_claim_global_inconsistency():
    """Catches declaring all hypotheses inconsistent from one selected configuration."""
    c = HOLD["H13_NEGATED_RELATION_CONTRADICTS"]
    r = FR.run_fact_route(c["text"], {"facts": _facts(c["id"])})
    assert (r.status, r.code, r.scene3d) == ("REFUSED", "NEGATED_CLAUSE", None)
    assert r.planner["negated_checks"]["f6"] == {
        "evidence_state": "TRUE_ON_CONFIGURATION",
        "proof_status": "UNVERIFIABLE",
        "can_present_as_proven": False,
    }
    assert "mâu thuẫn" not in r.reason.lower()
