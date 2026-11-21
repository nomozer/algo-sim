# -*- coding: utf-8 -*-
"""Development corpora for Wave 3B evaluation of run `dimension-aware-verified-construction`.

Strictly DEVELOPMENT / EXPOSED data only (never a locked W2/W3 row, never sealed H-1):
1. `COMP112`: the 112-item compositional development corpus from `grounded-vietnamese-geometry-understanding`,
   recording both the pre-v140 (`expect_v139`) and v140 (`expect_v140`) expectations for the 2 items whose
   prior `REFUSE` expectations were superseded by v140 capabilities (`gv_unread_area_in_a` -> `a√6/3`,
   `goal_cos_given_premise_neg` -> `a√3`).
2. `STAGE_P1_WAVE_PROBES`: 24 Phase 3–8 probes covering typed expressions (`a²`, `a³`, `(2a)²`, `a√3`, `3,5`),
   role-ordered segment ratios, metric unit consistency vs wrong-dimension/mixed-base unit refusals,
   certified area/volume derivations, trigonometric height & right-triangle leg constructions,
   non-special angle domain boundaries, and dimensional/geometric metamorphics.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
RUNS_DIR = THIS_DIR.parents[1]


def load_comp112() -> dict[str, dict[str, Any]]:
    prior_path = RUNS_DIR / "grounded-vietnamese-geometry-understanding/tools/compositional_dev_corpus.py"
    spec = importlib.util.spec_from_file_location("_prior_comp112", prior_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out: dict[str, dict[str, Any]] = {}
    for cid, entry in mod.CORPUS.items():
        item = deepcopy(entry)
        item["expect_v139"] = item["expect"]
        item["expect_v140"] = item["expect"]
        out[cid] = item

    # Superseded in v140 by Phase 3–6 capabilities (prior run's file on disk remains untouched):
    out["gv_unread_area_in_a"].update(
        expect="SERVE",
        expect_v140="SERVE",
        goal="distance",
        oracle_exact="a√6/3",
        superseded="REFUSE in v139 (doc_so held lengths only; v140 parses face_area=a² + certified SQUARE_AREA_TO_SIDE)",
    )
    out["goal_cos_given_premise_neg"].update(
        expect="SERVE",
        expect_v140="SERVE",
        goal="length",
        oracle_exact="a√3",
        superseded=(
            "REFUSE in v139 (trig-ratio premises were unsupported; v140 parses line_plane_angle cos=1/2 -> "
            "certified altitude SA = AB*tan(60°) = a√3)"
        ),
    )
    return out


STAGE_P1_WAVE_PROBES: dict[str, dict[str, Any]] = {
    # ── Positive Phase 3–5 Expression, Dimension & Certified Derivation Probes ──────────────────
    "wp_area_square_base_dist": {
        "group": "p1b_area_derivation",
        "expect": "SERVE",
        "goal": "distance",
        "oracle_exact": "a√6/3",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². "
            "Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    "wp_area_alpha_renamed_x": {
        "group": "p1b_metamorphic",
        "expect": "SERVE",
        "goal": "distance",
        "same_as": "wp_area_square_base_dist",
        "oracle_exact": "x√6/3",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng x và diện tích đáy bằng x². "
            "Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    "wp_area_vertex_renamed_T_MNPQ": {
        "group": "p1b_metamorphic",
        "expect": "SERVE",
        "goal": "distance",
        "same_as": "wp_area_square_base_dist",
        "oracle_exact": "a√6/3",
        "text": (
            "Cho hình chóp tứ giác đều T.MNPQ có diện tích đáy bằng a² và độ dài cạnh bên bằng a. "
            "Tính khoảng cách từ M đến mặt phẳng (TNP)."
        ),
    },
    "wp_area_parenthesized_2a_sq": {
        "group": "p1b_expression_precedence",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "4a³√7/3",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3a và diện tích đáy bằng (2a)². "
            "Tính thể tích khối chóp S.ABCD."
        ),
    },
    "wp_area_equilateral_tri_base": {
        "group": "p1b_area_derivation",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "a³√3/12",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều, diện tích tam giác ABC bằng a²√3/4, "
            "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABC."
        ),
    },
    "wp_volume_pyramid_to_height": {
        "group": "p1b_volume_derivation",
        "expect": "SERVE",
        "goal": "length",
        "oracle_exact": "a√2",
        "text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy "
            "và thể tích khối chóp S.ABCD bằng a³/3. Tính độ dài cạnh SB."
        ),
    },
    "wp_role_ordered_ratio": {
        "group": "p1b_ratio_expression",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "a³√7/6",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và tỉ số giữa cạnh bên và cạnh đáy bằng 3/2. "
            "Tính thể tích khối chóp S.ABCD."
        ),
    },
    "wp_consistent_metric_units_cm": {
        "group": "p1b_unit_consistency",
        "expect": "SERVE",
        "goal": "distance",
        "oracle_exact": "√6",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². "
            "Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    # ── Positive Phase 6 Trig & Right-Triangle Verified Construction Probes ─────────────────────
    "wp_trig_tan_line_plane_height": {
        "group": "p1c_trig_height",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "a³√3/6",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC), "
            "tan của góc giữa SB và mặt phẳng (ABC) bằng 2. Tính thể tích khối chóp S.ABC."
        ),
    },
    "wp_trig_angle_coupled_square_base": {
        "group": "p1c_trig_height",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "8a³/3",
        "text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng (ABCD), "
            "SA = 2a và góc giữa SB và mặt phẳng (ABCD) bằng 45°. Tính thể tích khối chóp S.ABCD."
        ),
    },
    "wp_right_isosceles_hypotenuse_to_legs": {
        "group": "p1c_right_triangle",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "a³√2/3",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AC = 2a, "
            "SA vuông góc với mặt phẳng (ABC) và tam giác SAB cân. Tính thể tích khối chóp S.ABC."
        ),
    },
    "wp_rhombus_prism_angle_volume": {
        "group": "p1c_rhombus_trig",
        "expect": "SERVE",
        "goal": "volume",
        "oracle_exact": "12a³",
        "text": (
            "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình thoi, góc BAD = 120°, "
            "BD = 2a√3 và góc giữa AC' và mặt phẳng (ABCD) bằng 60°. Tính thể tích khối lăng trụ ABCD.A'B'C'D'."
        ),
    },
    "wp_trig_goal_withheld_numeric_policy": {
        "group": "p1c_output_policy",
        "expect": "SERVE",
        "goal": "angle",
        "numeric": "NOT_ANSWERED",
        "oracle_exact": "cos²=1/5",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) "
            "và tan của góc giữa SB và mặt phẳng (ABC) bằng 2. Tính côsin của góc giữa SC và mặt phẳng (ABC)."
        ),
    },
    # ── Negative Soundness, Dimension, Unit, Source-Gate & Domain Probes ────────────────────────
    "wp_neg_area_assigned_linear_4a": {
        "group": "p1b_dimension_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng 4a. "
            "Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    "wp_neg_length_assigned_a_squared": {
        "group": "p1b_dimension_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng a². "
            "Tính thể tích khối chóp S.ABCD."
        ),
    },
    "wp_neg_wrong_dim_unit_area_9cm": {
        "group": "p1b_unit_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm. "
            "Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    "wp_neg_mixed_metric_units_3km_9cm2": {
        "group": "p1b_unit_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3km và diện tích đáy bằng 9cm². "
            "Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    "wp_neg_wrong_unit_trig_ratio_2cm": {
        "group": "p1c_unit_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy, "
            "tan của góc giữa SB và mặt phẳng đáy bằng 2cm. Tính thể tích khối chóp S.ABC."
        ),
    },
    "wp_neg_wrong_unit_length_60deg": {
        "group": "p1c_unit_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy và SA = 60°. "
            "Tính thể tích khối chóp S.ABC."
        ),
    },
    "wp_neg_uncertified_quad_area": {
        "group": "p1b_derivation_negative",
        "expect": "REFUSE",
        "expected_code": "MISSING_DIMENSION",
        "text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, SA vuông góc với mặt phẳng đáy, "
            "SA = a và diện tích đáy bằng 2a². Tính khoảng cách từ A đến mặt phẳng (SBC)."
        ),
    },
    "wp_neg_unordered_two_side_ratio": {
        "group": "p1b_ambiguity_negative",
        "expect": "REFUSE",
        "expected_code": "AMBIGUOUS_FACT",
        "text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2a, tỉ số hai cạnh bằng 2/3, "
            "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD."
        ),
    },
    "wp_neg_uncoupled_square_base_missing_dim": {
        "group": "p1c_coupling_guard_negative",
        "expect": "REFUSE",
        "expected_code": "AMBIGUOUS_FACT",
        "text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng (ABCD) và SA = 2a. "
            "Tính thể tích khối chóp S.ABCD."
        ),
    },
    "wp_neg_non_special_angle_37deg": {
        "group": "p1c_domain_boundary_negative",
        "expect": "REFUSE",
        "expected_code": "EXACT_DOMAIN_EXCEEDED",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC), "
            "góc giữa SB và mặt phẳng (ABC) bằng 37°. Tính thể tích khối chóp S.ABC."
        ),
    },
    "wp_neg_impossible_cos_gt_1": {
        "group": "p1c_contradiction_negative",
        "expect": "REFUSE",
        "expected_code": "INCONSISTENT_FACTS",
        "text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC), "
            "cosin của góc giữa SB và mặt phẳng (ABC) bằng 3/2. Tính thể tích khối chóp S.ABC."
        ),
    },
}


CORPUS = load_comp112()
