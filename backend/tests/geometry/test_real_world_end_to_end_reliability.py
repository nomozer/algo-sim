# -*- coding: utf-8 -*-
"""Run `real-world-end-to-end-reliability`: regressions for the root causes found on External17.

1. Height-invariant goals (External17 `ext_prt_02`, `ext_prt_03#1` were refused `MISSING_DIMENSION` although the asked
   distance does not depend on the unstated height). The engine now proves invariance (rational-function identity in h²,
   five samples, degree ≤ 3) and serves with an ILLUSTRATIVE scene labelled `scene_configuration.unique = False`.
   Every height-DEPENDENT goal, constructed operand, volume or angle still refuses `MISSING_DIMENSION`.
2. Part-to-part ratio points ("E thuộc cạnh SC sao cho SE = 3EC", External17 `ext_prt_05`): the local parser read only
   "SM = 1/3 SA"; the existing `divide_segment` primitive and Source Gate ratio grammar are now reached.
Expected values are hand-derived (exact coordinates), never product output.
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity


def _run(text: str):
    return route_text_input(text, allow_live_ai=False)


def _rc(out) -> str | None:
    return (out.response.get("envelope") or {}).get("reason_code")


@pytest.mark.parametrize(
    ("text", "answer"),
    [
        # CB ⊥ AB, CB ⊥ BB' ⇒ d(C, (ABB'A')) = CB = AB = 6 (right isosceles at B); MC key D. 6.
        ("Câu 10: Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B và AB = 6. "
         "Tính khoảng cách từ điểm C đến mặt phẳng (ABB'A')\nA. 3. B. 6√2. C. 3√2. D. 6.", "6"),
        # BO ⊥ AC, BO ⊥ SA ⇒ d(B, (SAC)) = BO = a√2/2.
        ("Câu 32: Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
         "Tính khoảng cách từ điểm B đến mp(SAC).", "a√2/2"),
        # AA' ⊥ base ⇒ d(AA', BC) = d(A, BC) = altitude of equilateral side 2a = a√3.
        ("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2a. "
         "Tính khoảng cách giữa hai đường thẳng AA' và BC.", "a√3"),
        # Renamed: d(N, (KMP)) = half diagonal of square side 4 = 2√2.
        ("Cho hình chóp K.MNPQ có đáy MNPQ là hình vuông cạnh 4, KM ⊥ (MNPQ). "
         "Tính khoảng cách từ N đến mặt phẳng (KMP).", "2√2"),
    ],
)
def test_height_invariant_goal_is_served_with_an_illustrative_labelled_scene(text, answer):
    out = _run(text)
    assert out.status == "SERVED", (_rc(out), out.response.get("route_d", {}).get("refusal"))
    assert out.telemetry.total_provider_calls == 0
    rd = out.response["route_d"]
    assert list(rd["answers"].values()) == [answer]
    cfg = rd["scene_configuration"]
    assert cfg["unique"] is False and cfg["kind"] == "HEIGHT_INVARIANT_ILLUSTRATIVE"
    cert = cfg["invariance_certificate"]
    assert cert["method"] == "rational_function_identity_in_h2" and len(set(cert["samples_h2"])) >= 4
    assert any(s.get("step") == "certify_height_invariance" for s in rd["construction_trace"])
    assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []


@pytest.mark.parametrize(
    "goal",
    [
        "Tính khoảng cách từ A đến mặt phẳng (SBC).",          # depends on SA
        "Tính thể tích khối chóp S.ABCD.",                      # volume ∝ SA
        "Tính độ dài đoạn thẳng SC.",                           # length depends on SA
        "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",   # angle depends on SA
        "Tính khoảng cách từ B đến mặt phẳng (SAC) và độ dài đoạn thẳng SC.",   # one invariant + one dependent
    ],
)
def test_height_dependent_goal_still_refuses_missing_dimension_without_scene(goal):
    out = _run(f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). {goal}")
    assert out.status != "SERVED"
    assert _rc(out) == "MISSING_DIMENSION"
    assert not (out.response.get("envelope") or {}).get("scene3d")


def test_constructed_operand_is_outside_the_invariance_proof_and_refuses():
    # M on SB depends on the apex; the degree bound covers solid vertices only ⇒ no invariance claim.
    out = _run("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Gọi M là trung điểm của SB. "
               "Tính khoảng cách từ M đến mặt phẳng (SAD).")
    assert out.status != "SERVED" and _rc(out) == "MISSING_DIMENSION"


def test_missing_base_dimension_is_not_treated_as_a_free_height():
    out = _run("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = a, SA ⊥ (ABCD). "
               "Tính khoảng cách từ B đến mặt phẳng (SAD).")
    assert out.status != "SERVED" and _rc(out) == "MISSING_DIMENSION"


def test_stated_height_keeps_a_unique_scene_without_illustrative_label():
    out = _run("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 6, AA' = 5. "
               "Tính khoảng cách từ C đến mặt phẳng (ABB'A').")
    assert out.status == "SERVED" and list(out.response["route_d"]["answers"].values()) == ["6"]
    assert "scene_configuration" not in out.response["route_d"]


@pytest.mark.parametrize(
    ("text", "answer"),
    [
        # A(0,0,0) B(2,0,0) C(2,2,0) S(0,0,2); M = (1,0,1); E = S + ¾(C − S) = (3/2, 3/2, 1/2) ⇒ ME² = 11/4.
        ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Gọi M là trung điểm của SB. "
         "Gọi E là điểm thuộc cạnh SC sao cho SE = 3EC. Tính độ dài đoạn thẳng ME.", "√11/2"),
        # Reversed parts: AE = 3ES on SA (A at origin, S = (0,0,4)) ⇒ E = (0,0,3); C = (4,4,0) ⇒ EC² = 41.
        ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA ⊥ (ABCD), SA = 4. "
         "Gọi E là điểm thuộc cạnh SA sao cho AE = 3ES. Tính độ dài đoạn thẳng EC.", "√41"),
    ],
)
def test_part_to_part_ratio_point_reaches_divide_segment(text, answer):
    out = _run(text)
    assert out.status == "SERVED", (_rc(out), out.response.get("route_d", {}).get("refusal"))
    assert out.telemetry.total_provider_calls == 0
    assert list(out.response["route_d"]["answers"].values()) == [answer]


def test_ratio_whose_parts_are_not_the_two_halves_of_the_segment_fails_closed():
    out = _run("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA ⊥ (ABCD), SA = 4. "
               "Gọi E là điểm thuộc cạnh SA sao cho SE = 3SC. Tính độ dài đoạn thẳng EC.")
    assert out.status != "SERVED"
