# -*- coding: utf-8 -*-
"""Run `certified-scale-cache-safety`: similarity-scale normalisation only under a certificate.

Served only when PO-1 the source states no length / area / volume, PO-2 every goal is an angle or a ratio, PO-3 fixing
one internal unit segment leaves exactly one configuration (no SHAPE freedom), PO-4 units 2 and 5 give the same exact
answers. The unit is never a call, premise or provenance entry. Agent-written development texts only.
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.simulation.geometry_functions.engine import SCALE_UNIT_ID

ISO = "Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, SA vuông góc với đáy và SA = AB. "
GOAL = "Tính góc giữa hai mặt phẳng (SBC) và (SBA)."


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _rd(text):
    return (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}


def test_a_figure_fixed_up_to_scale_is_served_with_a_certified_illustrative_scale():
    rd = _rd(ISO + GOAL)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == "1/3"      # normals (0,1,0), (1,1,1)
    cfg = rd["scene_configuration"]
    assert cfg["kind"] == "SIMILARITY_SCALE_ILLUSTRATIVE" and cfg["unique"] is False
    assert cfg["source_length_supplied"] is False and cfg["scale_origin"] == "INTERNAL_CONSTRUCTION_CONVENTION"
    po = cfg["invariance_certificate"]["obligations"]
    assert all(po[k] is True for k in ("PO-1_SCALE_FREE_PREMISES", "PO-2_SCALE_FREE_GOALS", "PO-3_UNIQUE_UP_TO_SCALE",
                                       "PO-5_NO_SOURCE_FABRICATION"))
    assert [w["same_exact_answers"] for w in po["PO-4_SCALE_WITNESS"]] == [True, True]


def test_the_unit_is_never_a_source_fact():
    rd = _rd(ISO + GOAL)
    ids = [c.get("id") for c in rd.get("source_provenance") or []]
    assert SCALE_UNIT_ID not in ids
    assert all(SCALE_UNIT_ID not in str(p) for p in rd.get("source_provenance") or [])


@pytest.mark.parametrize("text", [
    "Cho hình chóp T.XYZ có đáy là tam giác vuông cân tại X, TX vuông góc với đáy và TX = XY. Tính góc giữa hai mặt phẳng (TYZ) và (TYX).",
    "Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, SA = AB và SA vuông góc với đáy. " + GOAL,
])
def test_renamed_and_reordered_statements_give_the_same_certified_angle(text):
    rd = _rd(text)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == "1/3"
    assert rd["scene_configuration"]["kind"] == "SIMILARITY_SCALE_ILLUSTRATIVE"


@pytest.mark.xfail(strict=True, reason="pre-existing: with the base shape stated LAST the gate refuses the right angle "
                   "(SOURCE_OBJECT_MISMATCH) even when a length is given — a clause-order limitation, not normalisation")
@pytest.mark.parametrize("length", ["", " = 2"])
def test_base_shape_stated_last(length):
    text = f"Cho hình chóp S.ABC có SA vuông góc với đáy, SA = AB{length} và đáy là tam giác vuông cân tại A. " + GOAL
    assert _rd(text)["status"] == "SERVED"


@pytest.mark.parametrize("text, obligation", [
    # shape freedom with a goal that VARIES with it (BC/AB open; the plane angle case is now served by a
    # target-invariance proof — test_target_invariance_regular_solids.py)
    ("Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
     "Tính góc giữa đường thẳng SC và mặt phẳng (ABC).", "PO-3_UNIQUE_UP_TO_SCALE"),
    # free height: the angle changes with SA
    ("Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A và SA vuông góc với đáy. " + GOAL, None),
    # an absolute quantity is asked
    (ISO + "Tính thể tích khối chóp S.ABC.", "PO-2_SCALE_FREE_GOALS"),
    # a tetrahedron that is NOT regular (a regular one is now served: its definition gives the equal edges)
    ("Cho tứ diện ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM.", "PO-3_UNIQUE_UP_TO_SCALE"),
])
def test_figures_not_fixed_up_to_scale_or_absolute_goals_are_refused(text, obligation):
    rd = _rd(text)
    assert rd["status"] != "SERVED"
    assert rd["refusal"]["code"] == "MISSING_DIMENSION"


def test_a_stated_length_is_never_normalised_away():
    rd = _rd("Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, AB = 2, SA vuông góc với đáy và SA = AB. " + GOAL)
    assert rd["status"] == "SERVED" and "scene_configuration" not in rd               # the source fixes the scale
    assert rd["answer_exact"]["q1"]["coef"] == "1/3"                                   # same angle, no normalisation


def test_a_trigonometric_question_on_a_normalised_figure_still_leaves_the_number_unanswered():
    rd = _rd(ISO + "Tang của góc giữa hai mặt phẳng (SBC) và (SBA) bằng")
    assert rd["status"] == "SERVED" and rd["scene_configuration"]["kind"] == "SIMILARITY_SCALE_ILLUSTRATIVE"
    assert [g["numeric_source_goal"] for g in rd["source_goal_completion"]["goals"]] == ["NOT_ANSWERED"]
