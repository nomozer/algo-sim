# -*- coding: utf-8 -*-
"""Comprehensive regression tests for `slm_math_evaluator_v2` (axo-math-evaluator/2)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from slm_math_evaluator_v2 import (  # noqa: E402
    compare_math_expressions,
    infer_goal_kind_from_text,
    same_value_v2,
)


@pytest.mark.parametrize(
    "actual,oracle",
    [
        # Historical /7 `v7h_p7_06..10` cases that failed EVI.same_value
        ("cos²=2/3", "cos²=2/3"),
        ("cos²=1/2", "cos²=1/2"),
        ("cos²=2/5", "cos²=2/5"),
        ("cos²=4/6", "cos²=2/3"),
        # Rationalized vs unrationalized exact radicals & symbolic `a`
        ("3a/√22", "3a√22/22"),
        ("2a/√3", "2a√3/3"),
        ("(a√3)/2", "a√3/2"),
        ("√12", "2√3"),
        ("√2 + √8", "3√2"),
        ("2a√15/√25", "2a√15/5"),
        ("(√6+√2)/4", "(√2+√6)/4"),
        ("4πa³/3", "4/3*πa^3"),
        ("0,5", "1/2"),
        ("V = 2a³", "2a³"),
        ("50 cm", "0.5 m"),
        ("25 cm²", "0,25 dm²"),
        # Symmetric trig <-> angle conversions on acute angles
        ("cos²=1/2", "45°"),
        ("45°", "cos²=1/2"),
        ("cos²=3/4", "30°"),
        ("30°", "cos²=3/4"),
        ("cos²=1/4", "60°"),
        ("60°", "cos²=1/4"),
        ("cos²=0", "90°"),
        ("90°", "cos²=0"),
        ("cos=1/2", "cos²=1/4"),
        ("sin=√3/2", "cos²=1/4"),
        ("tan=1", "cos²=1/2"),
        ("cos(2x)=1/2", "cos²=3/4"),
        ("cos(2x)=0", "45°"),
        ("cos²=(2+√3)/4", "15°"),
        ("75°", "cos²=(2-√3)/4"),
        ("π/3 rad", "60°"),
    ],
)
def test_exact_equivalences_positive(actual: str, oracle: str) -> None:
    assert same_value_v2(actual, oracle) is True


@pytest.mark.parametrize(
    "actual,oracle,expected_code",
    [
        # Strict distinction of cos(x), cos²(x), cos(2x) and scalar
        ("cos=1/2", "cos²=1/2", "MISMATCH_WRONG_TRIG_FUNCTION"),
        ("cos(2x)=1/2", "cos²=1/2", "MISMATCH_WRONG_TRIG_FUNCTION"),
        ("cos(2x)=0", "cos²=0", "MISMATCH_WRONG_TRIG_FUNCTION"),
        ("cos²=1/2", "1/2", "MISMATCH_SCALAR_VS_TRIG"),
        ("1/2", "cos²=1/2", "MISMATCH_SCALAR_VS_TRIG"),
        ("cos=1/2", "45°", "MISMATCH_ANGLE_VALUE"),
        ("cos²=2/3", "cos²=1/3", "MISMATCH_ANGLE_VALUE"),
        ("cos²=1/4", "30°", "MISMATCH_ANGLE_VALUE"),
        # Dimension & near-miss string similarity traps
        ("2a²", "2a³", "MISMATCH_DIMENSION_POWER"),
        ("2a√3", "2√3", "MISMATCH_DIMENSION_POWER"),
        ("2a√5/5", "2a√5/3", "MISMATCH_VALUE"),
        ("50 cm", "50 cm²", "MISMATCH_UNIT_DIMENSION"),
        ("50 cm", "5 m", "MISMATCH_VALUE"),
    ],
)
def test_strict_negatives_and_near_misses(actual: str, oracle: str, expected_code: str) -> None:
    res = compare_math_expressions(actual, oracle)
    assert res.matched is False
    assert res.verdict_code == expected_code


def test_goal_kind_enforcement() -> None:
    # Explicit trig goal rejects raw wrong trig kind even if same acute angle!
    r1 = compare_math_expressions("cos²=1/2", "√2/2", goal_kind="trig_cos")
    assert r1.matched is False
    assert r1.verdict_code == "MISMATCH_WRONG_TRIG_FUNCTION"

    # Explicit trig_cos2 goal allows matching numeric scalar oracle `2/3` when question explicitly asked cos²
    r2 = compare_math_expressions("cos²=2/3", "2/3", goal_kind="trig_cos2")
    assert r2.matched is True
    assert r2.verdict_code == "EXACT_EQUIVALENT_EXPLICIT_TRIG_GOAL"

    # Dimensional goal typing
    assert compare_math_expressions("cos²=1/2", "45°", goal_kind="length").matched is False
    assert compare_math_expressions("2a²", "2a²", goal_kind="volume").matched is False
    assert compare_math_expressions("2a³", "2a³", goal_kind="volume").matched is True
    assert compare_math_expressions("1/2", "45°", goal_kind="angle").matched is False

    # Obtuse oriented angle safety
    assert compare_math_expressions("cos=-1/2", "120°", goal_kind="angle_oriented").matched is True
    assert compare_math_expressions("cos=1/2", "120°", goal_kind="angle_oriented").matched is False
    assert compare_math_expressions("cos²=1/4", "120°", goal_kind="angle_oriented").matched is False


@pytest.mark.parametrize(
    "actual,oracle",
    [
        ("", "2a"),
        ("NaN", "2a"),
        ("abc_xyz", "2a"),
        ("cos² 1/2", "45°"),
        ("cos²=3/2", "cos²=3/2"),
        ("cos=2", "30°"),
        ("√(3a)", "3a"),
        ("2/0", "2"),
        ("cos=-1/2", "60°"),
    ],
)
def test_unparseable_and_out_of_domain_fail_closed(actual: str, oracle: str) -> None:
    assert same_value_v2(actual, oracle) is None


def test_infer_goal_kind_ignores_premise_keywords() -> None:
    text = (
        "Cho lăng trụ đứng UVW.U'V'W' có đáy UVW là tam giác vuông cân tại U với UV=2a. "
        "Biết góc giữa (U'VW) và mặt đáy (UVW) bằng 45°. Tính khoảng cách từ U đến (U'VW)."
    )
    assert infer_goal_kind_from_text(text) == "length"
    assert infer_goal_kind_from_text("Cho chóp S.ABC có đáy diện tích 4a². Tính góc giữa SA và (ABC).") == "angle"
    assert infer_goal_kind_from_text("Tính cos² của góc giữa SC và (ABCD).") == "trig_cos2"

