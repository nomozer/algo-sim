# -*- coding: utf-8 -*-
"""P6 & P8 — Interactive Demonstration Suite & Simulation-Centered Development Evaluation.

Generates:
1. `demos/demo1..demo7*.json` + `demos/browser_demos_scenes.json` (for P6 & P7 real-browser visual acceptance)
2. `corpus-dev.json` (labeled `DEVELOPMENT_EVALUATION_NOT_BLIND`)
3. `eval-summary.json` measuring all 10 simulation-centered criteria with independent exact mathematical oracle verification.
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.adapter3_simulation import (  # noqa: E402
    ADAPTER_V3_VERSION,
    build_adapter3_simulation_response,
    run_typed_fact_next_route,
)
from app.simulation.geometry.radical import parse_exact  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next import (  # noqa: E402
    TYPED_FACT_NEXT_SCHEMA_VERSION,
)
def validate_geometry_v2(scene3d: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(scene3d.get("objects"), list) or not scene3d.get("objects"):
        errors.append("missing_objects")
    if not isinstance(scene3d.get("events"), list):
        errors.append("missing_events")
    if not isinstance(scene3d.get("formation"), dict) or not isinstance(scene3d["formation"].get("steps"), list):
        errors.append("missing_formation")
    return errors

DEMOS_DIR = HERE / "demos"
CORPUS_PATH = HERE / "corpus-dev.json"
SUMMARY_PATH = HERE / "eval-summary.json"


def build_demos_and_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Construct the P6 interactive demonstration payloads and the P8 development evaluation corpus."""
    demo1_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy và SA = 2. "
            "Gọi M là trung điểm của SA. Mặt phẳng (α) đi qua M và song song với mặt phẳng (ABCD) "
            "cắt SB, SC, SD. Tính diện tích thiết diện và tỉ số thể tích khối chóp cắt bởi (α) so với S.ABCD."
        ),
        "solids": [
            {
                "solid_id": "s_abcd",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2",
            }
        ],
        "premises": [
            {
                "kind": "base_is_square",
                "solid_id": "s_abcd",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "2"},
                "quote": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "s_abcd",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "quote": "SA vuông góc với đáy",
            },
            {
                "kind": "segment_length",
                "solid_id": "s_abcd",
                "args": {"segment": ["S", "A"], "value": "2"},
                "quote": "SA = 2",
            },
            {
                "kind": "point_is_midpoint",
                "solid_id": "s_abcd",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_alpha",
                "plane_name": "α",
                "target_solid_id": "s_abcd",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "Mặt phẳng (α) đi qua M và song song với mặt phẳng (ABCD) cắt SB, SC, SD",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_solid",
                "kind": "construct_object",
                "target_solid_id": "s_abcd",
                "quote": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2",
            },
            {
                "goal_id": "sim_sec",
                "kind": "construct_plane_section",
                "target_section_id": "sec_alpha",
                "quote": "Mặt phẳng (α) đi qua M và song song với mặt phẳng (ABCD) cắt SB, SC, SD",
            },
            {
                "goal_id": "sim_sub",
                "kind": "construct_derived_solid",
                "derived_solid_id": "s_top",
                "parent_solid_id": "s_abcd",
                "target_section_id": "sec_alpha",
                "apex_ref": "S",
                "quote": "khối chóp cắt bởi (α) so với S.ABCD",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_sec_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_alpha"},
                "quote": "Tính diện tích thiết diện",
            },
            {
                "goal_id": "m_vol_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "s_top",
                "denominator_solid_id": "s_abcd",
                "quote": "tỉ số thể tích khối chóp cắt bởi (α) so với S.ABCD",
            },
        ],
    }

    demo2_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2, BC = 4, SA vuông góc với đáy và SA = 3. "
            "Điểm M thuộc cạnh SA sao cho SM/SA = 1/3. Mặt phẳng (α) qua M song song với (ABCD) cắt SB, SC, SD. "
            "Dựng thiết diện, khối chóp đỉnh S phía trên (α) và tính thể tích phần khối đa diện còn lại."
        ),
        "solids": [
            {
                "solid_id": "main_pyr",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật",
            }
        ],
        "premises": [
            {
                "kind": "base_is_rectangle",
                "solid_id": "main_pyr",
                "args": {"vertices": ["A", "B", "C", "D"]},
                "quote": "đáy ABCD là hình chữ nhật với AB = 2, BC = 4",
            },
            {
                "kind": "segment_length",
                "solid_id": "main_pyr",
                "args": {"segment": ["A", "B"], "value": "2"},
                "quote": "AB = 2",
            },
            {
                "kind": "segment_length",
                "solid_id": "main_pyr",
                "args": {"segment": ["B", "C"], "value": "4"},
                "quote": "BC = 4",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "main_pyr",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "quote": "SA vuông góc với đáy",
            },
            {
                "kind": "segment_length",
                "solid_id": "main_pyr",
                "args": {"segment": ["S", "A"], "value": "3"},
                "quote": "SA = 3",
            },
            {
                "kind": "point_divides_segment",
                "solid_id": "main_pyr",
                "args": {"point": "M", "segment": ["S", "A"], "ratio": "1/3"},
                "quote": "Điểm M thuộc cạnh SA sao cho SM/SA = 1/3",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_unnamed",
                "plane_name": "α",
                "target_solid_id": "main_pyr",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "Mặt phẳng (α) qua M song song với (ABCD) cắt SB, SC, SD",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_sec_unnamed",
                "kind": "construct_plane_section",
                "target_section_id": "sec_unnamed",
                "quote": "Dựng thiết diện",
            },
            {
                "goal_id": "sim_upper_pyr",
                "kind": "construct_derived_solid",
                "derived_solid_id": "upper_pyr",
                "parent_solid_id": "main_pyr",
                "target_section_id": "sec_unnamed",
                "apex_ref": "S",
                "quote": "khối chóp đỉnh S phía trên (α)",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_sec_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_unnamed"},
                "quote": "Dựng thiết diện",
            },
            {
                "goal_id": "m_residual",
                "kind": "residual_volume",
                "parent_solid_id": "main_pyr",
                "cut_solid_id": "upper_pyr",
                "quote": "tính thể tích phần khối đa diện còn lại",
            },
        ],
    }

    demo3_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC là tam giác vuông cân tại A "
            "với AB = AC = 2. Biết SA vuông góc với mặt phẳng (ABC) và SA = 6. Gọi D trên "
            "cạnh SA sao cho D là trung điểm của SA ở khối thứ nhất, còn đỉnh D của hình chóp "
            "D.ABC có DA vuông góc với (ABC) trên cùng nửa không gian và DA = 2. Dựng hai khối "
            "chóp và tính thể tích khối thứ nhất, thể tích khối thứ hai cùng tỉ số thể tích."
        ),
        "solids": [
            {
                "solid_id": "pyr1",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "vertex_bindings": {"S": "S", "A": "A", "B": "B", "C": "C"},
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
            },
            {
                "solid_id": "pyr2",
                "solid_type": "pyramid",
                "notation": "D.ABC",
                "vertex_bindings": {"D": "D1", "A": "A", "B": "B", "C": "C"},
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
            },
        ],
        "premises": [
            {
                "kind": "base_is_right_triangle",
                "solid_id": "pyr1",
                "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
                "quote": "chung mặt đáy ABC là tam giác vuông cân tại A",
            },
            {
                "kind": "segment_length",
                "solid_id": "pyr1",
                "args": {"segment": ["A", "B"], "value": "2"},
                "quote": "AB = AC = 2",
            },
            {
                "kind": "segment_length",
                "solid_id": "pyr1",
                "args": {"segment": ["A", "C"], "value": "2"},
                "quote": "AB = AC = 2",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "pyr1",
                "args": {"line": ["pyr1::S", "pyr1::A"], "plane": ["A", "B", "C"]},
                "quote": "SA vuông góc với mặt phẳng (ABC)",
            },
            {
                "kind": "segment_length",
                "solid_id": "pyr1",
                "args": {"segment": ["pyr1::S", "pyr1::A"], "value": "6"},
                "quote": "SA = 6",
            },
            {
                "kind": "point_is_midpoint",
                "solid_id": "pyr1",
                "args": {"point": "pyr1::D", "segment": ["pyr1::S", "pyr1::A"]},
                "quote": "D là trung điểm của SA ở khối thứ nhất",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "pyr2",
                "args": {"line": ["pyr2::D", "pyr2::A"], "plane": ["A", "B", "C"]},
                "quote": "DA vuông góc với (ABC)",
            },
            {
                "kind": "segment_length",
                "solid_id": "pyr2",
                "args": {"segment": ["pyr2::D", "pyr2::A"], "value": "2"},
                "quote": "DA = 2",
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
        ],
        "math_goals": [
            {
                "goal_id": "m_v_pyr1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "pyr1"},
                "quote": "tính thể tích khối thứ nhất",
            },
            {
                "goal_id": "m_v_pyr2",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "pyr2"},
                "quote": "thể tích khối thứ hai",
            },
            {
                "goal_id": "m_v_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "pyr2",
                "denominator_solid_id": "pyr1",
                "quote": "tỉ số thể tích",
            },
        ],
    }

    demo4_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A với AB = 3, AC = 4. "
            "Cạnh bên SA vuông góc với đáy và SA = 3. Gọi M là trung điểm của SA. "
            "Mặt phẳng (α) qua M vuông góc với SA cắt SB, SC. Mô phỏng trình tự dựng hình từng bước."
        ),
        "solids": [
            {
                "solid_id": "s_abc",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A",
            }
        ],
        "premises": [
            {
                "kind": "base_is_right_triangle",
                "solid_id": "s_abc",
                "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
                "quote": "đáy ABC là tam giác vuông tại A",
            },
            {
                "kind": "segment_length",
                "solid_id": "s_abc",
                "args": {"segment": ["A", "B"], "value": "3"},
                "quote": "AB = 3",
            },
            {
                "kind": "segment_length",
                "solid_id": "s_abc",
                "args": {"segment": ["A", "C"], "value": "4"},
                "quote": "AC = 4",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "s_abc",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                "quote": "Cạnh bên SA vuông góc với đáy",
            },
            {
                "kind": "segment_length",
                "solid_id": "s_abc",
                "args": {"segment": ["S", "A"], "value": "3"},
                "quote": "SA = 3",
            },
            {
                "kind": "point_is_midpoint",
                "solid_id": "s_abc",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_perp",
                "plane_name": "α",
                "target_solid_id": "s_abc",
                "plane_kind": "through_point_perpendicular_line",
                "through_point": "M",
                "perpendicular_line": ["S", "A"],
                "quote": "Mặt phẳng (α) qua M vuông góc với SA cắt SB, SC",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_seq",
                "kind": "construction_sequence",
                "quote": "Mô phỏng trình tự dựng hình từng bước",
            },
            {
                "goal_id": "sim_sec_perp",
                "kind": "construct_plane_section",
                "target_section_id": "sec_perp",
                "quote": "Mặt phẳng (α) qua M vuông góc với SA cắt SB, SC",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_vol_sabc",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "s_abc"},
                "quote": "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A",
            },
            {
                "goal_id": "m_area_perp",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_perp"},
                "quote": "Mặt phẳng (α) qua M vuông góc với SA cắt SB, SC",
            },
        ],
    }

    demo5_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hai hình chóp S.ABCD và T.ABCD có chung đáy ABCD là hình vuông cạnh 2. "
            "SA vuông góc với đáy, SA = 2; TC vuông góc với đáy, TC = 4. "
            "Gọi M là trung điểm của SA, mặt phẳng (α) qua M song song với (ABCD) cắt SB, SC, SD. "
            "Làm nổi bật khối chóp S.ABCD, thiết diện (α) và các đỉnh giao điểm dẫn xuất."
        ),
        "solids": [
            {
                "solid_id": "pyr_s",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hai hình chóp S.ABCD và T.ABCD có chung đáy ABCD là hình vuông cạnh 2",
            },
            {
                "solid_id": "pyr_t",
                "solid_type": "pyramid",
                "notation": "T.ABCD",
                "quote": "Cho hai hình chóp S.ABCD và T.ABCD có chung đáy ABCD là hình vuông cạnh 2",
            },
        ],
        "premises": [
            {
                "kind": "base_is_square",
                "solid_id": "pyr_s",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "2"},
                "quote": "có chung đáy ABCD là hình vuông cạnh 2",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "pyr_s",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "quote": "SA vuông góc với đáy",
            },
            {
                "kind": "segment_length",
                "solid_id": "pyr_s",
                "args": {"segment": ["S", "A"], "value": "2"},
                "quote": "SA = 2",
            },
            {
                "kind": "line_perp_plane",
                "solid_id": "pyr_t",
                "args": {"line": ["T", "C"], "plane": ["A", "B", "C", "D"]},
                "quote": "TC vuông góc với đáy",
            },
            {
                "kind": "segment_length",
                "solid_id": "pyr_t",
                "args": {"segment": ["T", "C"], "value": "4"},
                "quote": "TC = 4",
            },
            {
                "kind": "point_is_midpoint",
                "solid_id": "pyr_s",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec_hl",
                "plane_name": "α",
                "target_solid_id": "pyr_s",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "quote": "mặt phẳng (α) qua M song song với (ABCD) cắt SB, SC, SD",
            }
        ],
        "relations": [
            {
                "relation_id": "rel_shared_base",
                "kind": "shared_faces",
                "solid_a": "pyr_s",
                "face_a": ["pyr_s::A", "pyr_s::B", "pyr_s::C", "pyr_s::D"],
                "solid_b": "pyr_t",
                "face_b": ["pyr_t::A", "pyr_t::B", "pyr_t::C", "pyr_t::D"],
                "quote": "có chung đáy ABCD là hình vuông cạnh 2",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_hl",
                "kind": "highlight_geometry",
                "target_solid_id": "pyr_s",
                "target_refs": ["pyr_s", "sec_hl", "M"],
                "style_role": "section",
                "quote": "Làm nổi bật khối chóp S.ABCD, thiết diện (α) và các đỉnh giao điểm dẫn xuất",
            }
        ],
        "math_goals": [
            {
                "goal_id": "m_ratio_st",
                "kind": "volume_ratio",
                "numerator_solid_id": "pyr_s",
                "denominator_solid_id": "pyr_t",
                "quote": "Cho hai hình chóp S.ABCD và T.ABCD có chung đáy ABCD",
            }
        ],
    }

    demo6a_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', điểm A trên đường tròn đáy dưới, "
            "bán kính đáy R = 2 và chiều cao h = 3. Mặt phẳng (α) song song với đáy cách đáy một khoảng 1 "
            "cắt hình trụ theo thiết diện đường tròn, và xét thêm thiết diện qua trục qua A. "
            "Tính thể tích, diện tích xung quanh hình trụ, diện tích thiết diện tròn và thiết diện qua trục."
        ),
        "solids": [
            {
                "solid_id": "cyl",
                "solid_type": "cylinder",
                "notation": "O.O'",
                "center": "O",
                "apex_or_top": "O'",
                "rim_point": "A",
                "radius": "2",
                "height": "3",
                "quote": "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', điểm A trên đường tròn đáy dưới, bán kính đáy R = 2 và chiều cao h = 3",
            }
        ],
        "derived_sections": [
            {
                "section_id": "sec_parallel",
                "plane_name": "α",
                "target_solid_id": "cyl",
                "plane_kind": "parallel_to_base_at_distance",
                "distance_from_base": "1",
                "section_shape": "circle",
                "quote": "Mặt phẳng (α) song song với đáy cách đáy một khoảng 1 cắt hình trụ theo thiết diện đường tròn",
            },
            {
                "section_id": "sec_axial",
                "plane_name": "β",
                "target_solid_id": "cyl",
                "plane_kind": "axial_section",
                "section_shape": "polygon",
                "quote": "xét thêm thiết diện qua trục qua A",
            },
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_cyl",
                "kind": "construct_object",
                "target_solid_id": "cyl",
                "quote": "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O'",
            },
            {
                "goal_id": "sim_sec_par",
                "kind": "construct_plane_section",
                "target_section_id": "sec_parallel",
                "quote": "Mặt phẳng (α) song song với đáy cách đáy một khoảng 1 cắt hình trụ theo thiết diện đường tròn",
            },
            {
                "goal_id": "sim_sec_ax",
                "kind": "construct_plane_section",
                "target_section_id": "sec_axial",
                "quote": "xét thêm thiết diện qua trục qua A",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_vol",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "cyl"},
                "quote": "Tính thể tích",
            },
            {
                "goal_id": "m_lat",
                "kind": "measurement",
                "goal_type": "lateral_area",
                "target": {"solid": "cyl"},
                "quote": "diện tích xung quanh hình trụ",
            },
            {
                "goal_id": "m_par_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_parallel"},
                "quote": "diện tích thiết diện tròn",
            },
            {
                "goal_id": "m_ax_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_axial"},
                "quote": "thiết diện qua trục",
            },
        ],
    }

    demo6b_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình nón tròn xoay đỉnh S, tâm đáy O, điểm A thuộc đường tròn đáy, bán kính đáy R = 3, "
            "chiều cao h = 4. Mặt phẳng (α) song song với đáy cắt trục SO theo tỉ lệ 1/2 tính từ đỉnh S, "
            "chia hình nón thành hình nón nhỏ đỉnh S và hình nón cụt. Xét thêm thiết diện qua trục SAB. "
            "Tính thể tích, diện tích xung quanh hình nón, diện tích thiết diện qua trục, tỉ số thể tích "
            "và thể tích khối nón cụt."
        ),
        "solids": [
            {
                "solid_id": "cone_main",
                "solid_type": "cone",
                "notation": "S.O",
                "center": "O",
                "apex_or_top": "S",
                "rim_point": "A",
                "radius": "3",
                "height": "4",
                "quote": "Cho hình nón tròn xoay đỉnh S, tâm đáy O, điểm A thuộc đường tròn đáy, bán kính đáy R = 3, chiều cao h = 4",
            }
        ],
        "derived_sections": [
            {
                "section_id": "sec_cut",
                "plane_name": "α",
                "target_solid_id": "cone_main",
                "plane_kind": "parallel_to_base_at_ratio",
                "ratio_from_apex": "1/2",
                "section_shape": "circle",
                "quote": "Mặt phẳng (α) song song với đáy cắt trục SO theo tỉ lệ 1/2 tính từ đỉnh S",
            },
            {
                "section_id": "sec_axial",
                "plane_name": "β",
                "target_solid_id": "cone_main",
                "plane_kind": "axial_section",
                "section_shape": "polygon",
                "quote": "Xét thêm thiết diện qua trục SAB",
            },
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_cone",
                "kind": "construct_object",
                "target_solid_id": "cone_main",
                "quote": "Cho hình nón tròn xoay đỉnh S, tâm đáy O",
            },
            {
                "goal_id": "sim_cut",
                "kind": "construct_plane_section",
                "target_section_id": "sec_cut",
                "quote": "Mặt phẳng (α) song song với đáy cắt trục SO theo tỉ lệ 1/2 tính từ đỉnh S",
            },
            {
                "goal_id": "sim_upper_cone",
                "kind": "construct_derived_solid",
                "derived_solid_id": "cone_upper",
                "parent_solid_id": "cone_main",
                "target_section_id": "sec_cut",
                "apex_ref": "S",
                "quote": "chia hình nón thành hình nón nhỏ đỉnh S và hình nón cụt",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_vol",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "cone_main"},
                "quote": "Tính thể tích",
            },
            {
                "goal_id": "m_lat",
                "kind": "measurement",
                "goal_type": "lateral_area",
                "target": {"solid": "cone_main"},
                "quote": "diện tích xung quanh hình nón",
            },
            {
                "goal_id": "m_axial_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_axial"},
                "quote": "diện tích thiết diện qua trục",
            },
            {
                "goal_id": "m_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "cone_upper",
                "denominator_solid_id": "cone_main",
                "quote": "tỉ số thể tích",
            },
            {
                "goal_id": "m_frustum",
                "kind": "residual_volume",
                "parent_solid_id": "cone_main",
                "cut_solid_id": "cone_upper",
                "quote": "thể tích khối nón cụt",
            },
        ],
    }

    demo6c_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho mặt cầu (S) tâm I bán kính R = 5. Mặt phẳng (α) có phương trình z - 3 = 0 cắt mặt cầu "
            "theo một đường tròn giao tuyến. Tính thể tích khối cầu, diện tích mặt cầu, bán kính và diện tích "
            "đường tròn giao tuyến."
        ),
        "solids": [
            {
                "solid_id": "sph",
                "solid_type": "sphere",
                "notation": "(S)",
                "center": "I",
                "radius": "5",
                "quote": "Cho mặt cầu (S) tâm I bán kính R = 5",
            }
        ],
        "derived_sections": [
            {
                "section_id": "sec_sph",
                "plane_name": "α",
                "target_solid_id": "sph",
                "plane_kind": "plane_equation",
                "equation_coeffs": ["0", "0", "1", "-3"],
                "section_shape": "circle",
                "quote": "Mặt phẳng (α) có phương trình z - 3 = 0 cắt mặt cầu theo một đường tròn giao tuyến",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_sph",
                "kind": "construct_object",
                "target_solid_id": "sph",
                "quote": "Cho mặt cầu (S) tâm I bán kính R = 5",
            },
            {
                "goal_id": "sim_sec",
                "kind": "construct_plane_section",
                "target_section_id": "sec_sph",
                "quote": "Mặt phẳng (α) có phương trình z - 3 = 0 cắt mặt cầu theo một đường tròn giao tuyến",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_vol",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid": "sph"},
                "quote": "Tính thể tích khối cầu",
            },
            {
                "goal_id": "m_surf",
                "kind": "measurement",
                "goal_type": "lateral_area",
                "target": {"solid": "sph"},
                "quote": "diện tích mặt cầu",
            },
            {
                "goal_id": "m_rad",
                "kind": "measurement",
                "goal_type": "radius",
                "target": {"section_id": "sec_sph"},
                "quote": "bán kính",
            },
            {
                "goal_id": "m_area",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec_sph"},
                "quote": "diện tích đường tròn giao tuyến",
            },
        ],
    }

    demo7_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho mặt cầu (S) tâm I bán kính R = 5 và mặt phẳng (α) có phương trình z - 7 = 0. "
            "Hãy dựng đường tròn giao tuyến của mặt phẳng (α) và mặt cầu (S)."
        ),
        "solids": [
            {
                "solid_id": "sph_refused",
                "solid_type": "sphere",
                "notation": "(S)",
                "center": "I",
                "radius": "5",
                "quote": "Cho mặt cầu (S) tâm I bán kính R = 5",
            }
        ],
        "derived_sections": [
            {
                "section_id": "sec_noncut",
                "plane_name": "α",
                "target_solid_id": "sph_refused",
                "plane_kind": "plane_equation",
                "equation_coeffs": ["0", "0", "1", "-7"],
                "section_shape": "circle",
                "quote": "mặt phẳng (α) có phương trình z - 7 = 0",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_noncut",
                "kind": "construct_plane_section",
                "target_section_id": "sec_noncut",
                "quote": "Hãy dựng đường tròn giao tuyến của mặt phẳng (α) và mặt cầu (S)",
            }
        ],
    }

    demos = [
        ("demo1-pyramid-derived-section", "Demo 1 — Pyramid + Derived Plane Section", demo1_payload, "SERVED", None),
        ("demo2-unnamed-section-intersections", "Demo 2 — Unnamed Section Intersections (I1..I3)", demo2_payload, "SERVED", None),
        ("demo3-multi-solid-shared-geometry", "Demo 3 — Multi-Solid Shared Geometry (Prism + Pyramid)", demo3_payload, "SERVED", None),
        ("demo4-step-by-step-construction", "Demo 4 — Step-by-Step Construction Timeline", demo4_payload, "SERVED", None),
        ("demo5-selection-and-highlighting", "Demo 5 — Selection & Highlighting", demo5_payload, "SERVED", None),
        ("demo6a-curved-cylinder-sections", "Demo 6A — Curved Cylinder + Parallel Circle & Axial Section", demo6a_payload, "SERVED", None),
        ("demo6b-curved-cone-frustum-cut", "Demo 6B — Curved Cone + Parallel Cut + Cone Frustum", demo6b_payload, "SERVED", None),
        ("demo6c-curved-sphere-plane-cut", "Demo 6C — Curved Sphere + Plane Cut Circle", demo6c_payload, "SERVED", None),
        ("demo7-invalid-geometry-safe-refusal", "Demo 7 — Invalid Geometry Safe Refusal (Non-cutting Plane)", demo7_payload, "REFUSED", "CURVED_PLANE_DOES_NOT_CUT"),
    ]

    # Additional positive & negative cases for the P8 development evaluation corpus
    extra_cases = [
        (
            "pos_09_cylinder_oblique_ellipse",
            "Cylinder + oblique plane ellipse section",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": (
                    "Cho hình trụ tròn xoay tâm đáy O bán kính R = 3, chiều cao h = 20. "
                    "Mặt phẳng (α) có phương trình x - z + 10 = 0 cắt hình trụ theo thiết diện elip. "
                    "Tính diện tích thiết diện elip."
                ),
                "solids": [
                    {
                        "solid_id": "cyl_el",
                        "solid_type": "cylinder",
                        "notation": "O",
                        "center": "O",
                        "radius": "3",
                        "height": "20",
                        "quote": "Cho hình trụ tròn xoay tâm đáy O bán kính R = 3, chiều cao h = 20",
                    }
                ],
                "derived_sections": [
                    {
                        "section_id": "sec_el",
                        "plane_name": "α",
                        "target_solid_id": "cyl_el",
                        "plane_kind": "plane_equation",
                        "equation_coeffs": ["1", "0", "-1", "10"],
                        "section_shape": "ellipse",
                        "quote": "Mặt phẳng (α) có phương trình x - z + 10 = 0 cắt hình trụ theo thiết diện elip",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "sim_el",
                        "kind": "construct_plane_section",
                        "target_section_id": "sec_el",
                        "quote": "Mặt phẳng (α) có phương trình x - z + 10 = 0 cắt hình trụ theo thiết diện elip",
                    }
                ],
                "math_goals": [
                    {
                        "goal_id": "m_el_area",
                        "kind": "measurement",
                        "goal_type": "area",
                        "target": {"section_id": "sec_el"},
                        "quote": "Tính diện tích thiết diện elip",
                    }
                ],
            },
            "SERVED",
            None,
            {"m_el_area": "9π√2"},
        ),
        (
            "pos_10_cone_oblique_ellipse",
            "Cone + oblique plane ellipse section",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": (
                    "Cho hình nón tròn xoay đỉnh S, tâm đáy O, bán kính R = 6, chiều cao h = 8. "
                    "Mặt phẳng (α) có phương trình x - 3z + 9 = 0 cắt hình nón theo thiết diện elip. "
                    "Tính diện tích thiết diện elip."
                ),
                "solids": [
                    {
                        "solid_id": "cone_el",
                        "solid_type": "cone",
                        "notation": "S.O",
                        "center": "O",
                        "apex_or_top": "S",
                        "radius": "6",
                        "height": "8",
                        "quote": "Cho hình nón tròn xoay đỉnh S, tâm đáy O, bán kính R = 6, chiều cao h = 8",
                    }
                ],
                "derived_sections": [
                    {
                        "section_id": "sec_cone_el",
                        "plane_name": "α",
                        "target_solid_id": "cone_el",
                        "plane_kind": "plane_equation",
                        "equation_coeffs": ["1", "0", "-3", "9"],
                        "section_shape": "ellipse",
                        "quote": "Mặt phẳng (α) có phương trình x - 3z + 9 = 0 cắt hình nón theo thiết diện elip",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "sim_cone_el",
                        "kind": "construct_plane_section",
                        "target_section_id": "sec_cone_el",
                        "quote": "Mặt phẳng (α) có phương trình x - 3z + 9 = 0 cắt hình nón theo thiết diện elip",
                    }
                ],
                "math_goals": [
                    {
                        "goal_id": "m_cone_el_area",
                        "kind": "measurement",
                        "goal_type": "area",
                        "target": {"section_id": "sec_cone_el"},
                        "quote": "Tính diện tích thiết diện elip",
                    }
                ],
            },
            "SERVED",
            None,
            {"m_cone_el_area": "20π√6/3"},
        ),
        (
            "neg_02_sphere_tangent_plane",
            "Refusal: Sphere tangent plane (d = R)",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": "Cho mặt cầu (S) tâm I bán kính R = 5 và mặt phẳng (α): z - 5 = 0.",
                "solids": [
                    {
                        "solid_id": "sph",
                        "solid_type": "sphere",
                        "notation": "(S)",
                        "center": "I",
                        "radius": "5",
                        "quote": "Cho mặt cầu (S) tâm I bán kính R = 5",
                    }
                ],
                "derived_sections": [
                    {
                        "section_id": "sec",
                        "plane_name": "α",
                        "target_solid_id": "sph",
                        "plane_kind": "plane_equation",
                        "equation_coeffs": ["0", "0", "1", "-5"],
                        "section_shape": "circle",
                        "quote": "mặt phẳng (α): z - 5 = 0",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_plane_section",
                        "target_section_id": "sec",
                        "quote": "mặt phẳng (α): z - 5 = 0",
                    }
                ],
            },
            "REFUSED",
            "CURVED_PLANE_TANGENT",
            {},
        ),
        (
            "neg_03_cone_parabolic_section",
            "Refusal: Cone plane parallel to generator (parabolic section)",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": "Cho hình nón đỉnh S, tâm đáy O, bán kính R = 3, chiều cao h = 4 và mặt phẳng (α): 4x - 3z + 6 = 0.",
                "solids": [
                    {
                        "solid_id": "cone1",
                        "solid_type": "cone",
                        "notation": "S.O",
                        "center": "O",
                        "apex_or_top": "S",
                        "radius": "3",
                        "height": "4",
                        "quote": "Cho hình nón đỉnh S, tâm đáy O, bán kính R = 3, chiều cao h = 4",
                    }
                ],
                "derived_sections": [
                    {
                        "section_id": "sec_p",
                        "plane_name": "α",
                        "target_solid_id": "cone1",
                        "plane_kind": "plane_equation",
                        "equation_coeffs": ["4", "0", "-3", "6"],
                        "section_shape": "ellipse",
                        "quote": "mặt phẳng (α): 4x - 3z + 6 = 0",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_plane_section",
                        "target_section_id": "sec_p",
                        "quote": "mặt phẳng (α): 4x - 3z + 6 = 0",
                    }
                ],
            },
            "REFUSED",
            "CURVED_CONE_SECTION_PARABOLIC",
            {},
        ),
        (
            "neg_04_standalone_cone_frustum",
            "Refusal: Standalone cone frustum without parent cone",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": "Cho hình nón cụt có tâm hai đáy O và O', bán kính đáy lớn R = 4, chiều cao h = 3.",
                "solids": [
                    {
                        "solid_id": "frust",
                        "solid_type": "cone_frustum",
                        "notation": "O.O'",
                        "center": "O",
                        "apex_or_top": "O'",
                        "radius": "4",
                        "height": "3",
                        "quote": "Cho hình nón cụt có tâm hai đáy O và O', bán kính đáy lớn R = 4, chiều cao h = 3",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_object",
                        "target_solid_id": "frust",
                        "quote": "Cho hình nón cụt có tâm hai đáy O và O'",
                    }
                ],
            },
            "REFUSED",
            "CURVED_PRIMITIVE_BLOCKED_BY_KERNEL",
            {},
        ),
        (
            "neg_05_ambiguous_multi_solid_ref",
            "Refusal: Ambiguous unqualified vertex reference across multiple solids",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": (
                    "Cho hình lăng trụ đứng ABCD.EFGH có đáy ABCD là hình vuông cạnh 2, AE = 3. "
                    "Xét thêm hình chóp S.ABCD có đỉnh A trùng E, B trùng F, C trùng G, D trùng H và SA = 2."
                ),
                "solids": [
                    {
                        "solid_id": "s1",
                        "solid_type": "prism",
                        "notation": "ABCD.EFGH",
                        "quote": "Cho hình lăng trụ đứng ABCD.EFGH có đáy ABCD là hình vuông cạnh 2",
                    },
                    {
                        "solid_id": "s2",
                        "solid_type": "pyramid",
                        "notation": "S.ABCD",
                        "vertex_bindings": {"S": "S", "A": "E", "B": "F", "C": "G", "D": "H"},
                        "quote": "Xét thêm hình chóp S.ABCD có đỉnh A trùng E, B trùng F, C trùng G, D trùng H",
                    },
                ],
                "premises": [
                    {
                        "kind": "right_prism",
                        "solid_id": "s1",
                        "args": {"base": ["A", "B", "C", "D"], "top": ["E", "F", "G", "H"]},
                        "quote": "Cho hình lăng trụ đứng ABCD.EFGH",
                    },
                    {
                        "kind": "base_is_square",
                        "solid_id": "s1",
                        "args": {"vertices": ["A", "B", "C", "D"], "side": "2"},
                        "quote": "đáy ABCD là hình vuông cạnh 2",
                    },
                    {
                        "kind": "segment_length",
                        "solid_id": "s1",
                        "args": {"segment": ["A", "E"], "value": "3"},
                        "quote": "AE = 3",
                    },
                    {
                        "kind": "segment_length",
                        "args": {"segment": ["S", "A"], "value": "2"},
                        "quote": "SA = 2",
                    },
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_object",
                        "target_solid_id": "s1",
                        "quote": "Cho hình lăng trụ đứng ABCD.EFGH",
                    }
                ],
            },
            "REFUSED",
            "AMBIGUOUS_REFERENCE",
            {},
        ),
    ]

    expected_demo_answers = {
        "demo1-pyramid-derived-section": {"m_sec_area": "1", "m_vol_ratio": "1/8"},
        "demo2-unnamed-section-intersections": {"m_sec_area": "8/9", "m_residual": "208/27"},
        "demo3-multi-solid-shared-geometry": {"m_v_pyr1": "4", "m_v_pyr2": "4/3", "m_v_ratio": "1/3"},
        "demo4-step-by-step-construction": {"m_vol_sabc": "6", "m_area_perp": "3/2"},
        "demo5-selection-and-highlighting": {"m_ratio_st": "1/2"},
        "demo6a-curved-cylinder-sections": {"m_vol": "12π", "m_lat": "12π", "m_par_area": "4π", "m_ax_area": "12"},
        "demo6b-curved-cone-frustum-cut": {"m_vol": "12π", "m_lat": "15π", "m_axial_area": "12", "m_ratio": "1/8", "m_frustum": "21π/2"},
        "demo6c-curved-sphere-plane-cut": {"m_vol": "500π/3", "m_surf": "100π", "m_rad": "4", "m_area": "16π"},
        "demo7-invalid-geometry-safe-refusal": {},
    }

    corpus_cases = []
    for demo_id, title, payload, exp_status, exp_code in demos:
        corpus_cases.append(
            {
                "case_id": demo_id,
                "category": title,
                "is_demo": True,
                "expected_status": exp_status,
                "expected_refusal_code": exp_code,
                "expected_answers": expected_demo_answers[demo_id],
                "payload": payload,
            }
        )
    for cid, title, payload, exp_status, exp_code, exp_ans in extra_cases:
        corpus_cases.append(
            {
                "case_id": cid,
                "category": title,
                "is_demo": False,
                "expected_status": exp_status,
                "expected_refusal_code": exp_code,
                "expected_answers": exp_ans,
                "payload": payload,
            }
        )

    return demos, corpus_cases


def main() -> None:
    DEMOS_DIR.mkdir(parents=True, exist_ok=True)
    demos, corpus_cases = build_demos_and_corpus()

    browser_scenes: list[dict[str, Any]] = []
    case_results: list[dict[str, Any]] = []

    metrics = {
        "total_cases": len(corpus_cases),
        "positive_cases": 0,
        "negative_cases": 0,
        "positive_served": 0,
        "negative_refused": 0,
        "wrong_serves": 0,
        "scene3d_valid_v2": 0,
        "solid_topology_complete": 0,
        "derived_section_correct": 0,
        "derived_point_provenance_ok": 0,
        "multi_solid_identity_ok": 0,
        "curved_solid_render_ok": 0,
        "timeline_dependency_order_ok": 0,
        "math_certificate_consistent": 0,
    }

    for entry in corpus_cases:
        cid = entry["case_id"]
        payload = entry["payload"]
        exp_status = entry["expected_status"]
        exp_code = entry["expected_refusal_code"]
        exp_answers = entry["expected_answers"]

        env = build_adapter3_simulation_response(payload)
        res = run_typed_fact_next_route(payload)

        if entry["is_demo"]:
            demo_path = DEMOS_DIR / f"{cid}.json"
            demo_path.write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            browser_scenes.append(
                {
                    "id": cid,
                    "category": entry["category"],
                    "source": f"demos/{cid}.json",
                    "served": res.status == "SERVED",
                    "refusal": {"code": res.code, "reason": res.reason} if res.status != "SERVED" else None,
                    "scene3d": res.scene3d,
                }
            )

        if exp_status == "SERVED":
            metrics["positive_cases"] += 1
            served_ok = res.status == "SERVED" and res.scene3d is not None
            if served_ok:
                metrics["positive_served"] += 1
            v2_errors = validate_geometry_v2(res.scene3d) if res.scene3d else ["missing_scene3d"]
            v2_ok = len(v2_errors) == 0
            if v2_ok:
                metrics["scene3d_valid_v2"] += 1

            objs = res.scene3d["objects"] if res.scene3d else []
            events = res.scene3d.get("events", []) if res.scene3d else []
            steps = (res.scene3d.get("formation") or {}).get("steps", []) if res.scene3d else []

            # Solid topology check
            has_solid = any(o["type"] in ("solid", "curved_solid") for o in objs)
            if has_solid:
                metrics["solid_topology_complete"] += 1

            # Derived section check
            sec_ok = all(
                g["status"] in ("CONSTRUCTED", "HIGHLIGHTED", "SEQUENCED")
                for g in res.simulation_goals
            )
            if sec_ok:
                metrics["derived_section_correct"] += 1

            # Derived point provenance check (no raw I1..Ik leakage in user labels/notations)
            leak = any(
                o.get("notation") in {"I1", "I2", "I3", "I4"}
                for o in objs
                if (o.get("source") or {}).get("anonymous_in_source")
            )
            if not leak:
                metrics["derived_point_provenance_ok"] += 1

            # Multi-solid identity check
            if len(res.solids) >= 1 and len({s["scene_object_id"] for s in res.solids}) == len(res.solids):
                metrics["multi_solid_identity_ok"] += 1

            # Curved solid render check
            curved_objs = [o for o in objs if o["type"] == "curved_solid"]
            curved_ok = all(
                bool(o.get("anchor")) and bool(o.get("rim_point") or o.get("radius_sq"))
                for o in curved_objs
            )
            if curved_ok:
                metrics["curved_solid_render_ok"] += 1

            # Step timeline dependency order check
            first_step: dict[str, int] = {}
            for s_idx, st in enumerate(steps):
                for oid in st.get("objects_at_step", []):
                    first_step.setdefault(oid, s_idx)
            dep_violations = [
                (o["id"], dep)
                for o in objs
                for dep in (o.get("depends") or [])
                if o["id"] in first_step and dep in first_step and first_step[dep] > first_step[o["id"]]
            ]
            if not dep_violations and len(events) >= 1:
                metrics["timeline_dependency_order_ok"] += 1

            # Mathematical certificate & exact oracle check
            ans_ok = all(
                res.answers.get(k) == v and parse_exact(res.answers.get(k)) == parse_exact(v)
                for k, v in exp_answers.items()
            )
            if ans_ok:
                metrics["math_certificate_consistent"] += 1
            else:
                metrics["wrong_serves"] += 1

            case_results.append(
                {
                    "case_id": cid,
                    "expected_status": exp_status,
                    "actual_status": res.status,
                    "scene3d_v2_ok": v2_ok,
                    "answers": res.answers,
                    "expected_answers": exp_answers,
                    "answers_match": ans_ok,
                    "dep_violations": dep_violations,
                    "passed": served_ok and v2_ok and sec_ok and not leak and curved_ok and not dep_violations and ans_ok,
                }
            )
        else:
            metrics["negative_cases"] += 1
            refused_ok = res.status == "REFUSED" and res.code == exp_code and res.scene3d is None
            if refused_ok:
                metrics["negative_refused"] += 1
            if res.status == "SERVED":
                metrics["wrong_serves"] += 1
            case_results.append(
                {
                    "case_id": cid,
                    "expected_status": exp_status,
                    "actual_status": res.status,
                    "expected_code": exp_code,
                    "actual_code": res.code,
                    "scene3d_is_none": res.scene3d is None,
                    "passed": refused_ok,
                }
            )

    browser_scenes_path = DEMOS_DIR / "browser_demos_scenes.json"
    browser_scenes_path.write_text(json.dumps(browser_scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    corpus_doc = {
        "schema_version": "simulation-coverage-dev-corpus/1",
        "evaluation_scope": "DEVELOPMENT_EVALUATION_NOT_BLIND",
        "adapter_version": ADAPTER_V3_VERSION,
        "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "cases": corpus_cases,
    }
    CORPUS_PATH.write_text(json.dumps(corpus_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    all_passed = all(c["passed"] for c in case_results) and metrics["wrong_serves"] == 0
    summary_doc = {
        "schema_version": "simulation-coverage-eval-summary/1",
        "evaluation_scope": "DEVELOPMENT_EVALUATION_NOT_BLIND",
        "adapter_version": ADAPTER_V3_VERSION,
        "contract_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "all_passed": all_passed,
        "metrics": metrics,
        "cases": case_results,
    }
    SUMMARY_PATH.write_text(json.dumps(summary_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(demos)} demos and evaluated {len(corpus_cases)} development corpus cases: all_passed={all_passed}")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
