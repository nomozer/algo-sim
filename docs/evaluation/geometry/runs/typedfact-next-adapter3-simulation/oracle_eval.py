# -*- coding: utf-8 -*-
"""Development Evaluation Corpus & Independent Mathematical Oracle for Adapter /3 (`typed-fact-next/1`).

Measurement Class: DEVELOPMENT_EVALUATION_NOT_BLIND
Generates:
  - 4 executable simulation demo envelopes under `demos/`
  - `corpus-dev.json` (16 cases: 10 positive + 6 negative)
  - `eval-summary.json` (independent oracle verification results, verifying 0 wrong serves)
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

RUN_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUN_DIR.parents[4]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.adapter3_simulation import (  # noqa: E402
    ADAPTER_V3_VERSION,
    ROUTE_D_SIMULATION_SCHEMA_VERSION,
    build_adapter3_simulation_response,
    run_typed_fact_next_route,
)
from app.simulation.geometry_functions.typed_fact_next import (  # noqa: E402
    TYPED_FACT_NEXT_SCHEMA_VERSION,
)

MEASUREMENT_CLASS = "DEVELOPMENT_EVALUATION_NOT_BLIND"


# ─────────────────────────────────────────────────────────────────────────────
# Independent First-Principles Mathematical Oracle
# ─────────────────────────────────────────────────────────────────────────────


def oracle_pyramid_similarity_section(
    base_area_coef: Fraction,
    base_area_rad: int,
    height_coef: Fraction,
    cut_ratio: Fraction,
    unit: str | None = "a",
) -> dict[str, dict[str, Any]]:
    """Independent Euclidean oracle for a pyramid cut by a plane parallel to its base at apex ratio `t = cut_ratio`.

    - Section area = t^2 * S_base
    - Cut pyramid volume = t^3 * V_root, where V_root = (1/3) * S_base * h
    - Volume ratio V_cut / V_root = t^3
    - Residual frustum volume = (1 - t^3) * V_root
    """
    v_root_coef = Fraction(1, 3) * base_area_coef * height_coef
    vol_ratio = cut_ratio**3
    v_res_coef = (Fraction(1) - vol_ratio) * v_root_coef
    sec_area_coef = (cut_ratio**2) * base_area_coef

    def fmt_coef(c: Fraction, rad: int) -> str:
        if rad == 1:
            return str(c)
        num = "" if c.numerator == 1 else str(c.numerator)
        den = f"/{c.denominator}" if c.denominator != 1 else ""
        return f"{num}√{rad}{den}"

    return {
        "volume_ratio": {"coef": str(vol_ratio), "dim": 0, "unit": None},
        "residual_volume": {
            "coef": fmt_coef(v_res_coef, base_area_rad),
            "dim": 3 if unit else 0,
            "unit": unit,
        },
        "section_area": {
            "coef": fmt_coef(sec_area_coef, base_area_rad),
            "dim": 2 if unit else 0,
            "unit": unit,
        },
        "root_volume": {
            "coef": fmt_coef(v_root_coef, base_area_rad),
            "dim": 3 if unit else 0,
            "unit": unit,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4 Executable Simulation Demo Payloads (P5)
# ─────────────────────────────────────────────────────────────────────────────


def demo1_payload() -> dict[str, Any]:
    """Demo 1: Pyramid with automatically derived unnamed section and derived sub-solid."""
    return {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy (ABCD) "
            "và SA = 2a. Gọi M là trung điểm của SA. Mặt phẳng (α) đi qua M và song song với "
            "đáy (ABCD) cắt các cạnh SB, SC, SD. Dựng thiết diện của hình chóp cắt bởi (α), "
            "khối chóp cắt bởi (α) chứa đỉnh S, tính tỉ số thể tích và thể tích phần còn lại."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "main_pyramid",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "base_is_square",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "a"},
                "quote": "đáy ABCD là hình vuông cạnh a",
                "solid_id": "main_pyramid",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "quote": "SA vuông góc với đáy (ABCD)",
                "solid_id": "main_pyramid",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "2a"},
                "quote": "SA = 2a",
                "solid_id": "main_pyramid",
            },
            {
                "kind": "point_is_midpoint",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
                "solid_id": "main_pyramid",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_alpha",
                "plane_name": "α",
                "target_solid_id": "main_pyramid",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "Mặt phẳng (α) đi qua M và song song với đáy (ABCD) cắt các cạnh SB, SC, SD",
            }
        ],
        "relations": [
            {
                "relation_id": "rel_m_on_sa",
                "kind": "containment",
                "container_ref": "main_pyramid::SA",
                "member_ref": "M",
                "quote": "Gọi M là trung điểm của SA",
            },
            {
                "relation_id": "rel_m_in_sec",
                "kind": "section_membership",
                "section_id": "sec_alpha",
                "member_refs": ["M"],
                "quote": "Mặt phẳng (α) đi qua M và song song với đáy (ABCD)",
            },
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_solid",
                "kind": "construct_object",
                "target_solid_id": "main_pyramid",
                "quote": "Cho hình chóp S.ABCD",
            },
            {
                "goal_id": "sim_section",
                "kind": "construct_plane_section",
                "target_section_id": "sec_alpha",
                "style_role": "section",
                "quote": "Dựng thiết diện của hình chóp cắt bởi (α)",
            },
            {
                "goal_id": "sim_top_pyramid",
                "kind": "construct_derived_solid",
                "derived_solid_id": "top_pyramid",
                "parent_solid_id": "main_pyramid",
                "target_section_id": "sec_alpha",
                "apex_ref": "S",
                "style_role": "derived_solid",
                "quote": "khối chóp cắt bởi (α) chứa đỉnh S",
            },
            {
                "goal_id": "sim_highlight",
                "kind": "highlight_geometry",
                "target_refs": ["sec_alpha", "top_pyramid", "M"],
                "style_role": "section",
                "quote": "Dựng thiết diện của hình chóp cắt bởi (α)",
            },
            {
                "goal_id": "sim_sequence",
                "kind": "construction_sequence",
                "quote": "Dựng thiết diện của hình chóp cắt bởi (α)",
            },
        ],
        "math_goals": [
            {
                "goal_id": "math_vol_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "top_pyramid",
                "denominator_solid_id": "main_pyramid",
                "quote": "tính tỉ số thể tích",
            },
            {
                "goal_id": "math_res_vol",
                "kind": "residual_volume",
                "parent_solid_id": "main_pyramid",
                "cut_solid_id": "top_pyramid",
                "quote": "thể tích phần còn lại",
            },
            {
                "goal_id": "math_sec_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_alpha"},
                "quote": "Dựng thiết diện của hình chóp cắt bởi (α)",
            },
        ],
    }


def demo2_payload() -> dict[str, Any]:
    """Demo 2: Multiple related solids with colliding local vertex names and verified shared geometry."""
    return {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC là tam giác vuông cân tại A "
            "với AB = AC = a. Biết SA vuông góc với mặt phẳng (ABC) và SA = 2a. Gọi D trên "
            "cạnh SA sao cho D là trung điểm của SA ở khối thứ nhất, còn đỉnh D của hình chóp "
            "D.ABC có DA vuông góc với (ABC) trên cùng nửa không gian và DA = a. Dựng hai khối "
            "chóp và tính tỉ số thể tích."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "pyr1",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
                "vertex_bindings": {"S": "S", "A": "A", "B": "B", "C": "C"},
            },
            {
                "solid_id": "pyr2",
                "solid_type": "pyramid",
                "notation": "D.ABC",
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
                "vertex_bindings": {"D": "D1", "A": "A", "B": "B", "C": "C"},
            },
        ],
        "premises": [
            {
                "kind": "base_is_right_triangle",
                "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
                "quote": "chung mặt đáy ABC là tam giác vuông cân tại A",
                "solid_id": "pyr1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "B"], "value": "a"},
                "quote": "AB = AC = a",
                "solid_id": "pyr1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "C"], "value": "a"},
                "quote": "AB = AC = a",
                "solid_id": "pyr1",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["pyr1::S", "pyr1::A"], "plane": ["A", "B", "C"]},
                "quote": "SA vuông góc với mặt phẳng (ABC)",
                "solid_id": "pyr1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["pyr1::S", "pyr1::A"], "value": "2a"},
                "quote": "SA = 2a",
                "solid_id": "pyr1",
            },
            {
                "kind": "point_is_midpoint",
                "args": {"point": "pyr1::D", "segment": ["pyr1::S", "pyr1::A"]},
                "quote": "D là trung điểm của SA ở khối thứ nhất",
                "solid_id": "pyr1",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["pyr2::D", "pyr2::A"], "plane": ["A", "B", "C"]},
                "quote": "DA vuông góc với (ABC)",
                "solid_id": "pyr2",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["pyr2::D", "pyr2::A"], "value": "a"},
                "quote": "DA = a",
                "solid_id": "pyr2",
            },
        ],
        "relations": [
            {
                "relation_id": "rel_shared_v",
                "kind": "shared_vertices",
                "pairs": [
                    ["pyr1::A", "pyr2::A"],
                    ["pyr1::B", "pyr2::B"],
                    ["pyr1::C", "pyr2::C"],
                ],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
            {
                "relation_id": "rel_shared_face",
                "kind": "shared_faces",
                "solid_a": "pyr1",
                "face_a": ["A", "B", "C"],
                "solid_b": "pyr2",
                "face_b": ["A", "B", "C"],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
            {
                "relation_id": "rel_frame_1",
                "kind": "coordinate_frame",
                "solid_id": "pyr1",
                "frame_id": "root",
                "anchor_refs": ["A", "B", "C"],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
            {
                "relation_id": "rel_frame_2",
                "kind": "coordinate_frame",
                "solid_id": "pyr2",
                "frame_id": "root",
                "anchor_refs": ["A", "B", "C"],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_pyr1",
                "kind": "construct_object",
                "target_solid_id": "pyr1",
                "quote": "Dựng hai khối chóp",
            },
            {
                "goal_id": "sim_pyr2",
                "kind": "construct_object",
                "target_solid_id": "pyr2",
                "style_role": "shared_geometry",
                "quote": "Dựng hai khối chóp",
            },
            {
                "goal_id": "sim_hl_d",
                "kind": "highlight_geometry",
                "target_refs": ["pyr1::D", "pyr2::D", "pyr2"],
                "style_role": "shared_geometry",
                "quote": "Dựng hai khối chóp",
            },
            {
                "goal_id": "sim_seq",
                "kind": "construction_sequence",
                "quote": "Dựng hai khối chóp",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_vol_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "pyr2",
                "denominator_solid_id": "pyr1",
                "quote": "tính tỉ số thể tích",
            },
            {
                "goal_id": "m_vol_pyr1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "pyr1"},
                "quote": "tính tỉ số thể tích",
            },
        ],
    }


def demo3_payload() -> dict[str, Any]:
    """Demo 3: Step-by-step construction & highlighting with plane perpendicular to lateral edge SA."""
    return {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) "
            "và SA = a. Gọi M thuộc SA sao cho SM/SA = 1/3. Mặt phẳng (α) qua M và vuông góc với SA "
            "cắt SB, SC. Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), "
            "làm nổi bật thiết diện và tính tỉ số thể tích cùng thể tích phần còn lại."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "pyr_sabc",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp S.ABC",
            }
        ],
        "premises": [
            {
                "kind": "base_is_equilateral_triangle",
                "args": {"vertices": ["A", "B", "C"], "side": "a"},
                "quote": "đáy ABC là tam giác đều cạnh a",
                "solid_id": "pyr_sabc",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                "quote": "SA vuông góc với mặt phẳng (ABC)",
                "solid_id": "pyr_sabc",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "a"},
                "quote": "SA = a",
                "solid_id": "pyr_sabc",
            },
            {
                "kind": "point_divides_segment",
                "args": {"point": "M", "segment": ["S", "A"], "ratio": "1/3"},
                "quote": "Gọi M thuộc SA sao cho SM/SA = 1/3",
                "solid_id": "pyr_sabc",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_perp",
                "plane_name": "α",
                "target_solid_id": "pyr_sabc",
                "plane_kind": "through_point_perpendicular_line",
                "through_point": "M",
                "perpendicular_line": ["S", "A"],
                "quote": "Mặt phẳng (α) qua M và vuông góc với SA cắt SB, SC",
            }
        ],
        "relations": [
            {
                "relation_id": "rel_sa_perp_ab",
                "kind": "perpendicular",
                "entity_a": ["S", "A"],
                "entity_b": ["A", "B"],
                "solid_id": "pyr_sabc",
                "quote": "SA vuông góc với mặt phẳng (ABC)",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "g_solid",
                "kind": "construct_object",
                "target_solid_id": "pyr_sabc",
                "quote": "Dựng từng bước hình chóp",
            },
            {
                "goal_id": "g_sec",
                "kind": "construct_plane_section",
                "target_section_id": "sec_perp",
                "style_role": "section",
                "quote": "thiết diện bởi (α)",
            },
            {
                "goal_id": "g_dsolid",
                "kind": "construct_derived_solid",
                "derived_solid_id": "top_sabc",
                "parent_solid_id": "pyr_sabc",
                "target_section_id": "sec_perp",
                "apex_ref": "S",
                "style_role": "derived_solid",
                "quote": "khối chóp đỉnh S cắt bởi (α)",
            },
            {
                "goal_id": "g_highlight",
                "kind": "highlight_geometry",
                "target_refs": ["sec_perp", "top_sabc", "M"],
                "style_role": "section",
                "quote": "làm nổi bật thiết diện",
            },
            {
                "goal_id": "g_sequence",
                "kind": "construction_sequence",
                "quote": "Dựng từng bước hình chóp",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "top_sabc",
                "denominator_solid_id": "pyr_sabc",
                "quote": "tính tỉ số thể tích",
            },
            {
                "goal_id": "m_res_vol",
                "kind": "residual_volume",
                "parent_solid_id": "pyr_sabc",
                "cut_solid_id": "top_sabc",
                "quote": "thể tích phần còn lại",
            },
        ],
    }


def demo4_payload() -> dict[str, Any]:
    """Demo 4: Negative underdetermined case refused cleanly (apex foot not determined)."""
    return {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a và cạnh bên SA = 2a. "
            "Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SC, SD. "
            "Hãy dựng hình chóp và thiết diện."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "main_pyramid",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "base_is_square",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "a"},
                "quote": "đáy ABCD là hình vuông cạnh a",
                "solid_id": "main_pyramid",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "2a"},
                "quote": "SA = 2a",
                "solid_id": "main_pyramid",
            },
            {
                "kind": "point_is_midpoint",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
                "solid_id": "main_pyramid",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_alpha",
                "plane_name": "α",
                "target_solid_id": "main_pyramid",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SC, SD",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_solid",
                "kind": "construct_object",
                "target_solid_id": "main_pyramid",
                "quote": "Hãy dựng hình chóp và thiết diện",
            },
            {
                "goal_id": "sim_section",
                "kind": "construct_plane_section",
                "target_section_id": "sec_alpha",
                "quote": "Hãy dựng hình chóp và thiết diện",
            },
        ],
    }


def build_development_corpus() -> list[dict[str, Any]]:
    """Build 16 development evaluation cases (10 positive + 6 negative) with independent oracle expectations."""
    c1_oracle = oracle_pyramid_similarity_section(
        base_area_coef=Fraction(1),
        base_area_rad=1,
        height_coef=Fraction(2),
        cut_ratio=Fraction(1, 2),
        unit="a",
    )
    c3_oracle = oracle_pyramid_similarity_section(
        base_area_coef=Fraction(1, 4),
        base_area_rad=3,
        height_coef=Fraction(1),
        cut_ratio=Fraction(1, 3),
        unit="a",
    )
    c4_oracle = oracle_pyramid_similarity_section(
        base_area_coef=Fraction(1, 2),
        base_area_rad=1,
        height_coef=Fraction(2),
        cut_ratio=Fraction(1, 3),
        unit="a",
    )
    c5_oracle = oracle_pyramid_similarity_section(
        base_area_coef=Fraction(4),
        base_area_rad=1,
        height_coef=Fraction(3),
        cut_ratio=Fraction(1, 2),
        unit="a",
    )
    c6_oracle = oracle_pyramid_similarity_section(
        base_area_coef=Fraction(1, 4),
        base_area_rad=3,
        height_coef=Fraction(2),
        cut_ratio=Fraction(2, 3),
        unit="a",
    )

    # Case 4: Parallel two lines cut
    p4 = demo1_payload()
    p4["problem_text"] = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A với AB = AC = a, "
        "SA vuông góc với (ABC) và SA = 2a. Gọi M thuộc SA sao cho SM/SA = 1/3. "
        "Mặt phẳng (P) qua M và song song với hai đường thẳng AB, AC cắt SB, SC. "
        "Dựng thiết diện, khối chóp đỉnh S cắt bởi (P), tính tỉ số thể tích và thể tích phần còn lại."
    )
    p4["solids"] = [
        {
            "solid_id": "sabc",
            "solid_type": "pyramid",
            "notation": "S.ABC",
            "quote": "Cho hình chóp S.ABC",
        }
    ]
    p4["premises"] = [
        {
            "kind": "base_is_right_triangle",
            "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
            "quote": "đáy ABC là tam giác vuông cân tại A",
            "solid_id": "sabc",
        },
        {
            "kind": "segment_length",
            "args": {"segment": ["A", "B"], "value": "a"},
            "quote": "AB = AC = a",
            "solid_id": "sabc",
        },
        {
            "kind": "segment_length",
            "args": {"segment": ["A", "C"], "value": "a"},
            "quote": "AB = AC = a",
            "solid_id": "sabc",
        },
        {
            "kind": "line_perp_plane",
            "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
            "quote": "SA vuông góc với (ABC)",
            "solid_id": "sabc",
        },
        {
            "kind": "segment_length",
            "args": {"segment": ["S", "A"], "value": "2a"},
            "quote": "SA = 2a",
            "solid_id": "sabc",
        },
        {
            "kind": "point_divides_segment",
            "args": {"point": "M", "segment": ["S", "A"], "ratio": "1/3"},
            "quote": "Gọi M thuộc SA sao cho SM/SA = 1/3",
            "solid_id": "sabc",
        },
    ]
    p4["derived_sections"] = [
        {
            "section_id": "sec_p",
            "plane_name": "P",
            "target_solid_id": "sabc",
            "plane_kind": "through_point_parallel_two_lines",
            "through_point": "M",
            "parallel_line_a": ["A", "B"],
            "parallel_line_b": ["A", "C"],
            "quote": "Mặt phẳng (P) qua M và song song với hai đường thẳng AB, AC cắt SB, SC",
        }
    ]
    p4["relations"] = []
    p4["simulation_goals"] = [
        {
            "goal_id": "sim_sec_p",
            "kind": "construct_plane_section",
            "target_section_id": "sec_p",
            "quote": "Dựng thiết diện",
        },
        {
            "goal_id": "sim_top_p",
            "kind": "construct_derived_solid",
            "derived_solid_id": "top_p",
            "parent_solid_id": "sabc",
            "target_section_id": "sec_p",
            "apex_ref": "S",
            "quote": "khối chóp đỉnh S cắt bởi (P)",
        },
    ]
    p4["math_goals"] = [
        {
            "goal_id": "m_ratio_p",
            "kind": "volume_ratio",
            "numerator_solid_id": "top_p",
            "denominator_solid_id": "sabc",
            "quote": "tính tỉ số thể tích",
        },
        {
            "goal_id": "m_res_p",
            "kind": "residual_volume",
            "parent_solid_id": "sabc",
            "cut_solid_id": "top_p",
            "quote": "thể tích phần còn lại",
        },
    ]

    # Case 5: Square pyramid side 2a, height 3a, midpoint section
    p5 = demo1_payload()
    p5["problem_text"] = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với đáy (ABCD) "
        "và SA = 3a. Gọi M là trung điểm của SA. Mặt phẳng (α) đi qua M và song song với "
        "đáy (ABCD) cắt các cạnh SB, SC, SD. Dựng thiết diện của hình chóp cắt bởi (α), "
        "khối chóp cắt bởi (α) chứa đỉnh S, tính tỉ số thể tích và thể tích phần còn lại."
    )
    p5["premises"][0]["args"]["side"] = "2a"
    p5["premises"][0]["quote"] = "đáy ABCD là hình vuông cạnh 2a"
    p5["premises"][2]["args"]["value"] = "3a"
    p5["premises"][2]["quote"] = "SA = 3a"

    # Case 6: Equilateral triangle pyramid side a, SA=2a, M divides SA in ratio 2/3
    p6 = demo3_payload()
    p6["problem_text"] = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) "
        "và SA = 2a. Gọi M thuộc SA sao cho SM/SA = 2/3. Mặt phẳng (α) qua M và song song với (ABC) "
        "cắt SB, SC. Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), "
        "làm nổi bật thiết diện và tính tỉ số thể tích cùng thể tích phần còn lại."
    )
    p6["premises"][2]["args"]["value"] = "2a"
    p6["premises"][2]["quote"] = "SA = 2a"
    p6["premises"][3]["args"]["ratio"] = "2/3"
    p6["premises"][3]["quote"] = "Gọi M thuộc SA sao cho SM/SA = 2/3"
    p6["derived_sections"][0] = {
        "section_id": "sec_perp",
        "plane_name": "α",
        "target_solid_id": "pyr_sabc",
        "plane_kind": "through_point_parallel_plane",
        "through_point": "M",
        "parallel_plane": ["A", "B", "C"],
        "quote": "Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC",
    }

    # Case 7: Named intersections N, P on SB, SC
    p7 = demo3_payload()
    p7["problem_text"] = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) "
        "và SA = a. Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và song song với (ABC) "
        "cắt SB, SC lần lượt tại N, P. Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), "
        "làm nổi bật thiết diện và tính tỉ số thể tích cùng thể tích phần còn lại."
    )
    p7["premises"][3] = {
        "kind": "point_is_midpoint",
        "args": {"point": "M", "segment": ["S", "A"]},
        "quote": "Gọi M là trung điểm của SA",
        "solid_id": "pyr_sabc",
    }
    p7["derived_sections"][0] = {
        "section_id": "sec_perp",
        "plane_name": "α",
        "target_solid_id": "pyr_sabc",
        "plane_kind": "through_point_parallel_plane",
        "through_point": "M",
        "parallel_plane": ["A", "B", "C"],
        "named_intersections": {"S-B": "N", "S-C": "P"},
        "quote": "Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P",
    }
    c7_oracle = oracle_pyramid_similarity_section(
        base_area_coef=Fraction(1, 4),
        base_area_rad=3,
        height_coef=Fraction(1),
        cut_ratio=Fraction(1, 2),
        unit="a",
    )

    # Case 8: Multi-solid adjacent pyramids S.ABC and S.ABM where M is midpoint of BC
    p8 = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SA vuông góc với (ABC) và SA = 3a. "
            "Gọi M là trung điểm của BC. Xét khối chóp S.ABM có chung mặt bên SAB với S.ABC. "
            "Dựng hai khối chóp và tính tỉ số thể tích cùng thể tích phần còn lại."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "root_pyr",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp S.ABC",
            },
            {
                "solid_id": "half_pyr",
                "solid_type": "pyramid",
                "notation": "S.ABM",
                "quote": "Xét khối chóp S.ABM",
            },
        ],
        "premises": [
            {
                "kind": "base_is_equilateral_triangle",
                "args": {"vertices": ["A", "B", "C"], "side": "2a"},
                "quote": "đáy ABC là tam giác đều cạnh 2a",
                "solid_id": "root_pyr",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                "quote": "SA vuông góc với (ABC)",
                "solid_id": "root_pyr",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "3a"},
                "quote": "SA = 3a",
                "solid_id": "root_pyr",
            },
            {
                "kind": "point_is_midpoint",
                "args": {"point": "M", "segment": ["B", "C"]},
                "quote": "Gọi M là trung điểm của BC",
                "solid_id": "root_pyr",
            },
        ],
        "relations": [
            {
                "relation_id": "rel_shared_sab",
                "kind": "shared_faces",
                "solid_a": "root_pyr",
                "face_a": ["S", "A", "B"],
                "solid_b": "half_pyr",
                "face_b": ["S", "A", "B"],
                "quote": "Xét khối chóp S.ABM có chung mặt bên SAB với S.ABC",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_root",
                "kind": "construct_object",
                "target_solid_id": "root_pyr",
                "quote": "Dựng hai khối chóp",
            },
            {
                "goal_id": "sim_half",
                "kind": "construct_object",
                "target_solid_id": "half_pyr",
                "style_role": "shared_geometry",
                "quote": "Dựng hai khối chóp",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_half_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "half_pyr",
                "denominator_solid_id": "root_pyr",
                "quote": "tính tỉ số thể tích",
            },
            {
                "goal_id": "m_half_res",
                "kind": "residual_volume",
                "parent_solid_id": "root_pyr",
                "cut_solid_id": "half_pyr",
                "quote": "thể tích phần còn lại",
            },
        ],
    }

    # Case 9: Regular pyramid S.ABCD with side 2a, height a, section through midpoint M of SA parallel to base
    p9 = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2a và chiều cao bằng a. "
            "Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SC, SD. "
            "Dựng thiết diện, khối chóp đỉnh S cắt bởi (α) và tính tỉ số thể tích."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "reg_pyr",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "regular_pyramid",
                "args": {"apex": "S", "base": ["A", "B", "C", "D"]},
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
                "solid_id": "reg_pyr",
            },
            {
                "kind": "base_is_square",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "2a"},
                "quote": "cạnh đáy bằng 2a",
                "solid_id": "reg_pyr",
            },
            {
                "kind": "height",
                "args": {"solid": "reg_pyr", "value": "a"},
                "quote": "chiều cao bằng a",
                "solid_id": "reg_pyr",
            },
            {
                "kind": "point_is_midpoint",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
                "solid_id": "reg_pyr",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_reg",
                "plane_name": "α",
                "target_solid_id": "reg_pyr",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "Mặt phẳng (α) qua M và song song với (ABCD) cắt SB, SC, SD",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_sec_reg",
                "kind": "construct_plane_section",
                "target_section_id": "sec_reg",
                "quote": "Dựng thiết diện",
            },
            {
                "goal_id": "sim_top_reg",
                "kind": "construct_derived_solid",
                "derived_solid_id": "top_reg",
                "parent_solid_id": "reg_pyr",
                "target_section_id": "sec_reg",
                "apex_ref": "S",
                "quote": "khối chóp đỉnh S cắt bởi (α)",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_reg_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "top_reg",
                "denominator_solid_id": "reg_pyr",
                "quote": "tính tỉ số thể tích",
            }
        ],
    }

    # Case 10: Right triangular prism ABC.A'B'C' with plane through midpoint M of AA' parallel to (ABC)
    p10 = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a và AA' = 2a. "
            "Gọi M là trung điểm của AA'. Mặt phẳng (α) qua M và song song với (ABC) cắt BB', CC'. "
            "Dựng lăng trụ, thiết diện bởi (α) và tính diện tích thiết diện."
        ),
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "prism_abc",
                "solid_type": "prism",
                "notation": "ABC.A'B'C'",
                "quote": "Cho lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "premises": [
            {
                "kind": "right_prism",
                "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                "quote": "Cho lăng trụ đứng ABC.A'B'C'",
                "solid_id": "prism_abc",
            },
            {
                "kind": "base_is_equilateral_triangle",
                "args": {"vertices": ["A", "B", "C"], "side": "a"},
                "quote": "đáy ABC là tam giác đều cạnh a",
                "solid_id": "prism_abc",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "A'"], "value": "2a"},
                "quote": "AA' = 2a",
                "solid_id": "prism_abc",
            },
            {
                "kind": "point_is_midpoint",
                "args": {"point": "M", "segment": ["A", "A'"]},
                "quote": "Gọi M là trung điểm của AA'",
                "solid_id": "prism_abc",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_prism",
                "plane_name": "α",
                "target_solid_id": "prism_abc",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "Mặt phẳng (α) qua M và song song với (ABC) cắt BB', CC'",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_prism",
                "kind": "construct_object",
                "target_solid_id": "prism_abc",
                "quote": "Dựng lăng trụ",
            },
            {
                "goal_id": "sim_sec_prism",
                "kind": "construct_plane_section",
                "target_section_id": "sec_prism",
                "quote": "thiết diện bởi (α)",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_prism_sec_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_prism"},
                "quote": "tính diện tích thiết diện",
            }
        ],
    }

    # Negative Cases 11..16
    n11 = demo4_payload()  # UNDERDETERMINED_POINT

    n12 = demo2_payload()  # AMBIGUOUS_REFERENCE
    n12["simulation_goals"][2]["target_refs"] = ["D"]

    n13 = demo2_payload()  # SHARED_ENTITY_MISMATCH
    n13["relations"][0]["pairs"] = [["pyr1::A", "pyr2::B"]]

    n14 = demo1_payload()  # DERIVED_PLANE_IS_REFERENCE
    n14["derived_sections"][0]["through_point"] = "A"

    n15 = demo1_payload()  # COLLINEAR_POINTS / PLANE_NOT_UNIQUE
    n15["derived_sections"][0] = {
        "section_id": "sec_alpha",
        "plane_name": "α",
        "target_solid_id": "main_pyramid",
        "plane_kind": "through_point_parallel_two_lines",
        "through_point": "M",
        "parallel_line_a": ["A", "B"],
        "parallel_line_b": ["C", "D"],
        "quote": "Mặt phẳng (α) đi qua M và song song với đáy (ABCD) cắt các cạnh SB, SC, SD",
    }

    n16 = demo1_payload()  # SOURCE_NUMBER_MISMATCH
    n16["premises"][2]["args"]["value"] = "9a"

    return [
        {
            "case_id": "A3-DEV-01",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": demo1_payload(),
            "oracle_exact": {
                "math_vol_ratio": c1_oracle["volume_ratio"],
                "math_res_vol": c1_oracle["residual_volume"],
                "math_sec_area": c1_oracle["section_area"],
            },
        },
        {
            "case_id": "A3-DEV-02",
            "slice": "Slice-B",
            "expected_status": "SERVED",
            "payload": demo2_payload(),
            "oracle_exact": {
                "m_vol_ratio": {"coef": "1/2", "dim": 0, "unit": None},
                "m_vol_pyr1": {"coef": "1/3", "dim": 3, "unit": "a"},
            },
        },
        {
            "case_id": "A3-DEV-03",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": demo3_payload(),
            "oracle_exact": {
                "m_ratio": c3_oracle["volume_ratio"],
                "m_res_vol": c3_oracle["residual_volume"],
            },
        },
        {
            "case_id": "A3-DEV-04",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": p4,
            "oracle_exact": {
                "m_ratio_p": c4_oracle["volume_ratio"],
                "m_res_p": c4_oracle["residual_volume"],
            },
        },
        {
            "case_id": "A3-DEV-05",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": p5,
            "oracle_exact": {
                "math_vol_ratio": c5_oracle["volume_ratio"],
                "math_res_vol": c5_oracle["residual_volume"],
                "math_sec_area": c5_oracle["section_area"],
            },
        },
        {
            "case_id": "A3-DEV-06",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": p6,
            "oracle_exact": {
                "m_ratio": c6_oracle["volume_ratio"],
                "m_res_vol": c6_oracle["residual_volume"],
            },
        },
        {
            "case_id": "A3-DEV-07",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": p7,
            "oracle_exact": {
                "m_ratio": c7_oracle["volume_ratio"],
                "m_res_vol": c7_oracle["residual_volume"],
            },
        },
        {
            "case_id": "A3-DEV-08",
            "slice": "Slice-B",
            "expected_status": "SERVED",
            "payload": p8,
            "oracle_exact": {
                "m_half_ratio": {"coef": "1/2", "dim": 0, "unit": None},
                "m_half_res": {"coef": "√3/2", "dim": 3, "unit": "a"},
            },
        },
        {
            "case_id": "A3-DEV-09",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": p9,
            "oracle_exact": {
                "m_reg_ratio": {"coef": "1/8", "dim": 0, "unit": None},
            },
        },
        {
            "case_id": "A3-DEV-10",
            "slice": "Slice-A",
            "expected_status": "SERVED",
            "payload": p10,
            "oracle_exact": {
                "m_prism_sec_area": {"coef": "√3/4", "dim": 2, "unit": "a"},
            },
        },
        {
            "case_id": "A3-DEV-11",
            "slice": "Negative",
            "expected_status": "REFUSED",
            "expected_codes": ["UNDERDETERMINED_POINT"],
            "payload": n11,
        },
        {
            "case_id": "A3-DEV-12",
            "slice": "Negative",
            "expected_status": "REFUSED",
            "expected_codes": ["AMBIGUOUS_REFERENCE"],
            "payload": n12,
        },
        {
            "case_id": "A3-DEV-13",
            "slice": "Negative",
            "expected_status": "REFUSED",
            "expected_codes": ["SHARED_ENTITY_MISMATCH"],
            "payload": n13,
        },
        {
            "case_id": "A3-DEV-14",
            "slice": "Negative",
            "expected_status": "REFUSED",
            "expected_codes": [
                "DERIVED_PLANE_IS_REFERENCE",
                "SECTION_PLANE_IS_FACE",
                "DEGENERATE_DERIVED_SOLID",
            ],
            "payload": n14,
        },
        {
            "case_id": "A3-DEV-15",
            "slice": "Negative",
            "expected_status": "REFUSED",
            "expected_codes": ["COLLINEAR_POINTS", "PLANE_NOT_UNIQUE"],
            "payload": n15,
        },
        {
            "case_id": "A3-DEV-16",
            "slice": "Negative",
            "expected_status": "REFUSED",
            "expected_codes": ["SOURCE_NUMBER_MISMATCH"],
            "payload": n16,
        },
    ]


def main() -> None:
    demos_dir = RUN_DIR / "demos"
    demos_dir.mkdir(parents=True, exist_ok=True)

    demos = [
        ("demo1-unnamed-section-pyramid.json", demo1_payload()),
        ("demo2-multi-solid-shared-geometry.json", demo2_payload()),
        ("demo3-step-by-step-construction-highlight.json", demo3_payload()),
        ("demo4-negative-underdetermined-refusal.json", demo4_payload()),
    ]
    demo_records: list[dict[str, Any]] = []
    for filename, payload in demos:
        envelope = build_adapter3_simulation_response(payload)
        out_path = demos_dir / filename
        out_bytes = (
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        out_path.write_bytes(out_bytes)
        demo_records.append(
            {
                "file": f"demos/{filename}",
                "status": envelope["route_d"]["status"],
                "refusal_code": (envelope["route_d"]["refusal"] or {}).get("code"),
                "sha256": hashlib.sha256(out_bytes).hexdigest(),
            }
        )

    cases = build_development_corpus()
    corpus_doc = {
        "measurement_class": MEASUREMENT_CLASS,
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "adapter_version": ADAPTER_V3_VERSION,
        "route_schema_version": ROUTE_D_SIMULATION_SCHEMA_VERSION,
        "total_cases": len(cases),
        "positive_cases": sum(1 for c in cases if c["expected_status"] == "SERVED"),
        "negative_cases": sum(1 for c in cases if c["expected_status"] == "REFUSED"),
        "cases": cases,
    }
    corpus_path = RUN_DIR / "corpus-dev.json"
    corpus_bytes = (
        json.dumps(corpus_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    corpus_path.write_bytes(corpus_bytes)

    # Evaluate corpus against independent mathematical oracle
    case_results: list[dict[str, Any]] = []
    positive_pass = 0
    negative_pass = 0
    wrong_serves = 0

    for case in cases:
        cid = case["case_id"]
        res = run_typed_fact_next_route(case["payload"])
        if case["expected_status"] == "SERVED":
            oracle_exact = case["oracle_exact"]
            exact_matches = (
                res.status == "SERVED"
                and res.scene3d is not None
                and res.kernel_check is True
                and all(res.answer_exact.get(k) == v for k, v in oracle_exact.items())
            )
            if res.status == "SERVED" and not exact_matches:
                wrong_serves += 1
            if exact_matches:
                positive_pass += 1
            case_results.append(
                {
                    "case_id": cid,
                    "slice": case["slice"],
                    "expected_status": "SERVED",
                    "actual_status": res.status,
                    "oracle_match": exact_matches,
                    "answers": res.answers,
                    "answer_exact": res.answer_exact,
                    "scene3d_objects": len(res.scene3d["objects"]) if res.scene3d else 0,
                }
            )
        else:
            expected_codes = set(case["expected_codes"])
            refusal_ok = (
                res.status == "REFUSED"
                and res.code in expected_codes
                and res.scene3d is None
            )
            if res.status == "SERVED":
                wrong_serves += 1
            if refusal_ok:
                negative_pass += 1
            case_results.append(
                {
                    "case_id": cid,
                    "slice": case["slice"],
                    "expected_status": "REFUSED",
                    "actual_status": res.status,
                    "expected_codes": sorted(expected_codes),
                    "actual_code": res.code,
                    "refusal_match": refusal_ok,
                }
            )

    summary_doc = {
        "measurement_class": MEASUREMENT_CLASS,
        "adapter_version": ADAPTER_V3_VERSION,
        "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "total_cases": len(cases),
        "positive_passed": positive_pass,
        "positive_total": corpus_doc["positive_cases"],
        "negative_passed": negative_pass,
        "negative_total": corpus_doc["negative_cases"],
        "wrong_serves": wrong_serves,
        "demos": demo_records,
        "results": case_results,
    }
    summary_path = RUN_DIR / "eval-summary.json"
    summary_path.write_text(
        json.dumps(summary_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Oracle evaluation complete: positive={positive_pass}/{corpus_doc['positive_cases']}, "
        f"negative={negative_pass}/{corpus_doc['negative_cases']}, wrong_serves={wrong_serves}"
    )
    if (
        positive_pass != corpus_doc["positive_cases"]
        or negative_pass != corpus_doc["negative_cases"]
        or wrong_serves != 0
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()
