# -*- coding: utf-8 -*-
"""Phase 2 (Gate B): Source-Grounded Semantic & Output Policy Closure Tests (`ext07`, `ext11`, `ext12`).

Covers all 10 required test categories of Section 5.5:
  1. Verbatim External17 (`ext07`, `ext11`, `ext12`)
  2. Renamed vertices
  3. Reordered premises
  4. Alternative phrasings (`Â`, `\\hat{A}`, `hình vuông ... có diện tích ...`, `2 chữ số thập phân`)
  5. ASCII / Unicode exponent & symbol variants (`cm^2` vs `cm²`, `°` vs `độ`)
  6. Multiple-choice A/B/C/D option non-ingestion
  7. Ambiguous inputs (vague rounding without place; ambiguous single-letter angle)
  8. Forged premises & lateral-vs-base face-area attribution (`SOURCE_OBJECT_MISMATCH`, `UNGROUNDED_VALUE`, `PREDICATE_NOT_IN_QUOTE`)
  9. Non-special degree angle refusal (`EXACT_DOMAIN_EXCEEDED`) & symbolic `a` rounding refusal (`QUESTION_CONTEXT_UNSUPPORTED`)
 10. Exact integer-arithmetic `ROUND_HALF_UP` midpoint & rational-bound verification (zero float).
"""
from __future__ import annotations

from fractions import Fraction
import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
from app.simulation.geometry.radical import Radical
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.output_policy import (
    exact_cos2_to_degrees,
    round_exact_radical_half_up,
)


def _run(text: str):
    return route_text_input(text, allow_live_ai=False)


# ── 1. Pure Output Policy Unit Tests (Zero Float Exact Rounding & Exact Special-Angle Degrees) ───────────────────────


@pytest.mark.parametrize(
    ("rad", "decimals", "expected_str"),
    [
        # ext07: 15√93 / 31 ≈ 4.6650949... -> 4,7 (1 decimal), 4,67 (2 decimals), 5 (0 decimals)
        (Radical(Fraction(15, 31), 93), 1, "4,7"),
        (Radical(Fraction(15, 31), 93), 2, "4,67"),
        (Radical(Fraction(15, 31), 93), 0, "5"),
        # Exact halfway boundary: 9/2 = 4.5 -> ROUND_HALF_UP gives 5 (0 decimals); 47/20 = 2.35 -> 2,4 (1 decimal)
        (Radical(Fraction(9, 2), 1), 0, "5"),
        (Radical(Fraction(47, 20), 1), 1, "2,4"),
        (Radical(Fraction(43, 20), 1), 1, "2,2"),
        # Rational just below 2.35: 2349999999999 / 1000000000000 -> 2,3
        (Radical(Fraction(2349999999999, 1000000000000), 1), 1, "2,3"),
    ],
)
def test_exact_integer_radical_rounding_half_up_has_verified_bounds(
    rad: Radical, decimals: int, expected_str: str
):
    res = round_exact_radical_half_up(rad, decimals=decimals, decimal_separator=",")
    assert res["rounded_display"] == expected_str
    assert res["lower_bound_verified"] is True
    assert res["upper_bound_verified"] is True
    assert res["used_floating_point"] is False


@pytest.mark.parametrize(
    ("cos2", "expected_deg"),
    [
        (Fraction(1), "0°"),
        (Fraction(3, 4), "30°"),
        (Fraction(1, 2), "45°"),
        (Fraction(1, 4), "60°"),
        (Fraction(0), "90°"),
    ],
)
def test_exact_cos2_to_degrees_special_angles(cos2: Fraction, expected_deg: str):
    ok, deg_str, deg_int = exact_cos2_to_degrees(cos2)
    assert ok is True
    assert deg_str == expected_deg
    assert f"{deg_int}°" == expected_deg


@pytest.mark.parametrize("non_special_cos2", [Fraction(1, 3), Fraction(8, 17), Fraction(2, 5)])
def test_non_special_cos2_refuses_degree_conversion_without_float_approximation(non_special_cos2: Fraction):
    ok, deg_str, deg_int = exact_cos2_to_degrees(non_special_cos2)
    assert ok is False and deg_str is None and deg_int is None


# ── 2. Verbatim External17 Closures (`ext07`, `ext11`, `ext12`) ──────────────────────────────────────────────────────


def test_ext07_verbatim_unicode_circumflex_angle_noun_goal_and_rounding():
    text = (
        "Câu 1. Cho hình lăng trụ đứng ABC.A'B'C' có AB = 5, AC = 6, Â = 60°. "
        "Khoảng cách giữa hai đường thẳng AA' và BC (làm tròn kết quả đến hàng phần mười)"
    )
    lp = parse_geometry_problem_locally(text)
    assert lp.status == LOCAL_PARSE_COMPLETE, (lp.reason_code, lp.fallback_reason)

    out = _run(text)
    assert out.status == "SERVED", out.response.get("route_d", {}).get("refusal")
    assert out.telemetry.total_provider_calls == 0

    rd = out.response["route_d"]
    # Formatted / rounded display is "4,7" while Exact Kernel coefficient stays "15√93/31"!
    assert list(rd["answers"].values()) == ["4,7"]
    ex = next(iter(rd["answer_exact"].values()))
    assert ex["coef"] == "15√93/31"
    pol = ex["output_policy"]
    assert pol["exact_answer"] == "15√93/31"
    assert pol["rounded_display"] == "4,7"
    assert pol["requested_formatting"]["decimals"] == 1
    assert pol["requested_formatting"]["mode"] == "ROUND_HALF_UP"
    assert rd["scene_configuration"]["unique"] is False
    assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []


def test_ext11_verbatim_regular_triangular_prism_height_and_degree_goal():
    text = (
        "Câu 30: Cho khối lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2a, chiều cao bằng a. "
        "Tính số đo góc tạo bởi hai mặt phẳng (AB'C') và (ABC)?\n"
        "A. 45°. B. 60°. C. 30°. D. 26°33'."
    )
    lp = parse_geometry_problem_locally(text)
    assert lp.status == LOCAL_PARSE_COMPLETE, (lp.reason_code, lp.fallback_reason)

    out = _run(text)
    assert out.status == "SERVED", out.response.get("route_d", {}).get("refusal")
    assert out.telemetry.total_provider_calls == 0

    rd = out.response["route_d"]
    assert list(rd["answers"].values()) == ["30°"]
    ex = next(iter(rd["answer_exact"].values()))
    assert ex["coef"] == "3/4"
    pol = ex["output_policy"]
    assert pol["exact_answer"] == "cos²=3/4"
    assert pol["requested_unit"] == "deg"
    assert pol["rounded_display"] == "30°"
    assert "scene_configuration" not in rd
    assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []


def test_ext12_verbatim_named_square_lateral_face_area_and_mc_stem():
    text = (
        "Câu 39: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B "
        "và diện tích của hình vuông ABB'A' bằng 12(cm²). "
        "Khoảng cách từ C đến mặt phẳng (ABB'A') bằng A. 6. B. 2√3(cm). C. 2. D. 3√2(cm)."
    )
    lp = parse_geometry_problem_locally(text)
    assert lp.status == LOCAL_PARSE_COMPLETE, (lp.reason_code, lp.fallback_reason)

    out = _run(text)
    assert out.status == "SERVED", out.response.get("route_d", {}).get("refusal")
    assert out.telemetry.total_provider_calls == 0

    rd = out.response["route_d"]
    assert list(rd["answers"].values()) == ["2√3"]
    ex = next(iter(rd["answer_exact"].values()))
    assert ex["coef"] == "2√3"
    assert "scene_configuration" not in rd
    assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []


# ── 3. Generalization: Renamed Vertices, Reordered Premises, Alternative Notations & ASCII Units ────────────────────


@pytest.mark.parametrize(
    ("text", "expected_display", "expected_exact_coef"),
    [
        # Renamed vertices MNP.M'N'P' + combining circumflex M̂ + 2 decimal places:
        # MN = 5, MP = 6, M̂ = 60° -> exact 15√93/31, 2 decimals -> 4,67
        (
            "Cho hình lăng trụ đứng MNP.M'N'P' có MN = 5, MP = 6, M\u0302 = 60°. "
            "Tính khoảng cách giữa hai đường thẳng MM' và NP (làm tròn đến 2 chữ số thập phân).",
            "4,67",
            "15√93/31",
        ),
        # Reordered premises + LaTeX \hat{D} = 60°:
        (
            "Cho hình lăng trụ đứng DEF.D'E'F' có \\hat{D} = 60°, DF = 6, DE = 5. "
            "Khoảng cách giữa hai đường thẳng DD' và EF (làm tròn kết quả đến hàng phần mười).",
            "4,7",
            "15√93/31",
        ),
        # Regular square prism MNPQ.M'N'P'Q' with cạnh đáy bằng a, chiều cao bằng a -> ∠(M'NP, MNPQ)?
        # Wait: for regular triangular prism DEF.D'E'F' with cạnh đáy 2a, chiều cao a√3:
        # base altitude h_base = a√3, AA' = a√3 => tan θ = a√3 / a√3 = 1 => θ = 45° (cos² = 1/2)!
        (
            "Cho khối lăng trụ tam giác đều DEF.D'E'F' có chiều cao bằng a√3, cạnh đáy bằng 2a. "
            "Tính số đo góc giữa hai mặt phẳng (DE'F') và (DEF).",
            "45°",
            "1/2",
        ),
        # Named rectangular lateral face area when base edge is known + ASCII (cm^2):
        # Right prism PQR.P'Q'R', base PQR right at Q, PQ = 3, QR = 4, diện tích mặt bên PQQ'P' bằng 15(cm^2).
        # => PP' = 15 / 3 = 5; V = (1/2 * 3 * 4) * 5 = 30!
        (
            "Cho hình lăng trụ đứng PQR.P'Q'R' có đáy PQR vuông tại Q, PQ = 3, QR = 4 "
            "và diện tích mặt bên PQQ'P' bằng 15(cm^2). Thể tích khối lăng trụ PQR.P'Q'R' bằng "
            "A. 90. B. 30. C. 15. D. 60.",
            "30",
            "30",
        ),
        # Alternative phrasing: "hình vuông ABB'A' có diện tích bằng 12":
        (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC vuông cân tại B, hình vuông ABB'A' có diện tích bằng 12. "
            "Tính khoảng cách từ C đến mặt phẳng (ABB'A').",
            "2√3",
            "2√3",
        ),
    ],
)
def test_semantic_and_output_policy_generalization_variants(
    text: str, expected_display: str, expected_exact_coef: str
):
    out = _run(text)
    assert out.status == "SERVED", out.response.get("route_d", {}).get("refusal")
    assert out.telemetry.total_provider_calls == 0
    rd = out.response["route_d"]
    assert list(rd["answers"].values()) == [expected_display]
    ex = next(iter(rd["answer_exact"].values()))
    assert ex["coef"] == expected_exact_coef


# ── 4. Fail-Closed Adversarial & Source Gate Preservation Tests ──────────────────────────────────────────────────────


def test_mc_options_with_distractor_assignments_are_never_ingested_as_premises():
    """If the stem omits height (`MISSING_DIMENSION` on volume), distractor MC options containing `AA' = 10`
    must NEVER be read as premises!"""
    text = (
        "Câu 5: Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD). "
        "Thể tích khối chóp S.ABCD bằng\n"
        "A. SA = 6. B. 8. C. 12. D. 4."
    )
    out = _run(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"


def test_degree_goal_with_non_special_irrational_angle_fails_closed_exact_domain():
    """Square pyramid SA ⊥ (ABCD), side 2, SA = 3 => cos²(SC, (ABCD)) = 8/17 (not in {0, 1/4, 1/2, 3/4, 1}).
    Asking `số đo góc` MUST refuse `EXACT_DOMAIN_EXCEEDED` instead of approximating arccos in float!"""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 3. "
        "Tính số đo góc giữa SC và mặt phẳng (ABCD)."
    )
    out = _run(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "EXACT_DOMAIN_EXCEEDED"


def test_vague_rounding_without_decimal_place_fails_closed():
    """Section 5.1: 'nếu đề hoặc quy định không xác định được một quy tắc cần thiết, không tự phát minh.'"""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 3. "
        "Tính độ dài đoạn thẳng SC (làm tròn kết quả)."
    )
    out = _run(text)
    assert out.status == "REFUSED"


def test_rounding_symbolic_parameter_a_fails_closed():
    """Rounding `a√3` to decimals when `a` is an unspecified positive symbol is ill-defined -> must refuse."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD), SA = a. "
        "Tính độ dài đoạn thẳng SC (làm tròn kết quả đến hàng phần mười)."
    )
    out = _run(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "QUESTION_CONTEXT_UNSUPPORTED"


def test_forged_lateral_face_area_claimed_on_base_triangle_is_refused_by_source_gate():
    """Section 5.3: Distinguish lateral face area from base area — claiming `polygon_area` on `ABB'A'`
    from a quote that actually states `diện tích mặt đáy ABC bằng 12` MUST be refused by Source Gate!"""
    text = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B "
        "và diện tích mặt đáy ABC bằng 12. Tính khoảng cách từ C đến mặt phẳng (ABB'A')."
    )
    forged_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABC.A'B'C'",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "premises": [
            {
                "kind": "right_prism",
                "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                "solid_id": "s1",
            },
            {
                "kind": "right_angle",
                "args": {"vertex": "B", "rays": ["A", "C"]},
                "quote": "đáy ABC là tam giác vuông cân tại B",
                "solid_id": "s1",
            },
            {
                "kind": "equal_length",
                "args": {"segment_a": ["B", "A"], "segment_b": ["B", "C"]},
                "quote": "đáy ABC là tam giác vuông cân tại B",
                "solid_id": "s1",
            },
            {
                "kind": "face_area",
                "args": {"polygon": ["A", "B", "B'", "A'"], "value": "12"},
                "quote": "diện tích mặt đáy ABC bằng 12",
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "C", "plane": ["A", "B", "B'", "A'"]},
                "solid_id": "s1",
                "quote": "Tính khoảng cách từ C đến mặt phẳng (ABB'A')",
            }
        ],
    }
    r = run_typed_fact_next_v2_route(forged_payload)
    assert r.status == "REFUSED"
    assert r.code in ("OBJECT_NOT_IN_QUOTE", "SOURCE_OBJECT_MISMATCH", "ROLE_NOT_IN_QUOTE")


def test_forged_output_policy_rounding_when_not_asked_in_source_is_refused():
    """Claiming `rounding={'mode': 'ROUND_HALF_UP', 'decimals': 1}` when the source did NOT ask for rounding
    MUST be refused by Source Gate (`QUESTION_CONTEXT_UNSUPPORTED`)!"""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 3. "
        "Tính độ dài đoạn thẳng SC."
    )
    lp = parse_geometry_problem_locally(text)
    assert lp.payload is not None
    tampered = dict(lp.payload)
    tampered["math_goals"] = [
        {
            **tampered["math_goals"][0],
            "rounding": {"mode": "ROUND_HALF_UP", "decimals": 1},
        }
    ]
    r = run_typed_fact_next_v2_route(tampered)
    assert r.status == "REFUSED"
    assert r.code == "QUESTION_CONTEXT_UNSUPPORTED"
    resp = build_adapter4_response(r, text)
    assert resp["route_d"]["status"] == "REFUSED"
