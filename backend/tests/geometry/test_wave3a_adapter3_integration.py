# -*- coding: utf-8 -*-
"""Combined integration & cross-route equivalence tests for Wave 3A (`volume-reasoning`)
and `TypedFactNext` + `Adapter /3` (`typedfact-next-adapter3-simulation`).

Verifies:
1. Single mathematical authority (`engine.py` `geometry-function-engine/9`) across both routes.
2. Wave 3A capabilities (`ask_volume_ratio`, `ask_residual_volume`, 3D SAT disjointness, source gate).
3. Adapter /3 capabilities (unnamed section intersections, `solid_id::label` qualified identity,
   shared geometry, timeline steps, and unified volume/containment certificates).
4. Cross-route mathematical & Scene3D equivalence on identical geometric configurations.
"""

from __future__ import annotations

import copy
from fractions import Fraction

from app.ai.adapter3_simulation import (
    ADAPTER_V3_VERSION,
    ROUTE_D_SIMULATION_SCHEMA_VERSION,
    run_typed_fact_next_route,
)
from app.ai.function_route import run_fact_route, run_function_route
from app.ai.hybrid_preview import ADAPTER_VERSION as ADAPTER_V2_VERSION
from app.simulation.geometry_functions.engine import ENGINE_VERSION
from app.simulation.geometry_functions.planner import PLANNER_VERSION
from app.simulation.geometry_functions.registry import REGISTRY_VERSION
from app.simulation.geometry_functions.typed_fact_next import (
    TYPED_FACT_NEXT_SCHEMA_VERSION,
)


def test_combined_version_identities_and_governance() -> None:
    """Verify version identities of Registry /13, Planner /13 (hybrid-contract-v2, owner D5), Engine /12
    (claude-to-codex-takeover skew-claim refusal), Adapter /2 and /3."""
    assert REGISTRY_VERSION == "geometry-functions/16"
    assert PLANNER_VERSION == "geometry-fact-planner/16"
    assert ENGINE_VERSION == "geometry-function-engine/14"
    assert ADAPTER_V2_VERSION == "hybrid-preview-adapter/2"
    assert TYPED_FACT_NEXT_SCHEMA_VERSION == "typed-fact-next/1"
    assert ADAPTER_V3_VERSION == "hybrid-simulation-adapter/3"
    assert ROUTE_D_SIMULATION_SCHEMA_VERSION == "hybrid-route-d-simulation/3"


def _square_pyramid_parallel_cut_adapter3_payload() -> dict:
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
        ],
    }


def test_adapter3_unified_self_ratio_and_self_residual_refusal() -> None:
    """Adapter /3 enforces the same self-ratio (`UNSUPPORTED_VOLUME_RATIO`) and self-subtraction
    (`NON_POSITIVE_RESIDUAL_VOLUME`) refusals as Wave 3A `engine.py`."""
    p_self_ratio = _square_pyramid_parallel_cut_adapter3_payload()
    p_self_ratio["math_goals"] = [
        {
            "goal_id": "m_self_ratio",
            "kind": "volume_ratio",
            "numerator_solid_id": "main_pyramid",
            "denominator_solid_id": "main_pyramid",
            "quote": "tính tỉ số thể tích",
        }
    ]
    r_ratio = run_typed_fact_next_route(p_self_ratio)
    assert r_ratio.status == "REFUSED"
    assert r_ratio.code == "UNSUPPORTED_VOLUME_RATIO"

    p_self_res = _square_pyramid_parallel_cut_adapter3_payload()
    p_self_res["math_goals"] = [
        {
            "goal_id": "m_self_res",
            "kind": "residual_volume",
            "parent_solid_id": "main_pyramid",
            "cut_solid_id": "main_pyramid",
            "quote": "thể tích phần còn lại",
        }
    ]
    r_res = run_typed_fact_next_route(p_self_res)
    assert r_res.status == "REFUSED"
    assert r_res.code == "NON_POSITIVE_RESIDUAL_VOLUME"


def test_adapter3_unified_halfspace_containment_refusal() -> None:
    """Adapter /3 delegates `residual_volume` containment to `engine.py::_mat_ngoai_khoi` and refuses
    with `RESIDUAL_CONTAINMENT_UNPROVED` when the subtracted solid has a vertex outside the parent solid."""
    problem_text = (
        "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC là tam giác vuông cân tại A "
        "với AB = AC = a. Biết SA vuông góc với mặt phẳng (ABC) và SA = a. Đỉnh D của hình chóp "
        "D.ABC có DA vuông góc với (ABC) và DA = 2a. Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ "
        "khối chóp D.ABC."
    )
    # Run `backend-hybrid-contract-unification`: the shared Source Gate now runs first, and the bare "Tính thể tích phần
    # còn lại" names neither the parent nor the cut solid (SOURCE_OBJECT_MISMATCH). The question names both, so the
    # refusal under test is again the engine's containment certificate.
    payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": problem_text,
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "pyr_small",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
                "vertex_bindings": {"S": "S", "A": "A", "B": "B", "C": "C"},
            },
            {
                "solid_id": "pyr_tall",
                "solid_type": "pyramid",
                "notation": "D.ABC",
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
                "vertex_bindings": {"D": "D", "A": "A", "B": "B", "C": "C"},
            },
        ],
        "premises": [
            {
                "kind": "base_is_right_triangle",
                "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
                "quote": "chung mặt đáy ABC là tam giác vuông cân tại A",
                "solid_id": "pyr_small",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "B"], "value": "a"},
                "quote": "AB = AC = a",
                "solid_id": "pyr_small",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "C"], "value": "a"},
                "quote": "AB = AC = a",
                "solid_id": "pyr_small",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                "quote": "SA vuông góc với mặt phẳng (ABC)",
                "solid_id": "pyr_small",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "a"},
                "quote": "SA = a",
                "solid_id": "pyr_small",
            },
            {
                "kind": "line_perp_plane",
                "args": {"line": ["D", "A"], "plane": ["A", "B", "C"]},
                "quote": "DA vuông góc với (ABC)",
                "solid_id": "pyr_tall",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["D", "A"], "value": "2a"},
                "quote": "DA = 2a",
                "solid_id": "pyr_tall",
            },
        ],
        "relations": [
            {
                "relation_id": "rel_shared_face",
                "kind": "shared_faces",
                "solid_a": "pyr_small",
                "face_a": ["A", "B", "C"],
                "solid_b": "pyr_tall",
                "face_b": ["A", "B", "C"],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
            {
                "relation_id": "rel_frame_1",
                "kind": "coordinate_frame",
                "solid_id": "pyr_small",
                "frame_id": "root",
                "anchor_refs": ["A", "B", "C"],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
            {
                "relation_id": "rel_frame_2",
                "kind": "coordinate_frame",
                "solid_id": "pyr_tall",
                "frame_id": "root",
                "anchor_refs": ["A", "B", "C"],
                "quote": "Cho hai hình chóp S.ABC và D.ABC có chung mặt đáy ABC",
            },
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_small",
                "kind": "construct_object",
                "target_solid_id": "pyr_small",
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
            },
            {
                "goal_id": "sim_tall",
                "kind": "construct_object",
                "target_solid_id": "pyr_tall",
                "quote": "Cho hai hình chóp S.ABC và D.ABC",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_bad_res",
                "kind": "residual_volume",
                "parent_solid_id": "pyr_small",
                "cut_solid_id": "pyr_tall",
                "quote": "Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ khối chóp D.ABC",
            }
        ],
    }
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code == "RESIDUAL_CONTAINMENT_UNPROVED"


def test_cross_route_equivalence_square_pyramid_parallel_cut() -> None:
    """Case 1: Square pyramid S.ABCD cut at midpoints M, N, P, Q (parallel to base ABCD).
    Verify identical exact answers, dimensional metadata, and volume-squared certificates across
    Wave 3A (`run_fact_route`) and Adapter /3 (`run_typed_fact_next_route`)."""
    # 1. Run via Adapter /3 (with unnamed section intersections on SB, SC, SD)
    a3_res = run_typed_fact_next_route(_square_pyramid_parallel_cut_adapter3_payload())
    assert a3_res.status == "SERVED", f"Adapter /3 refused: {a3_res.code} - {a3_res.reason}"

    # 2. Run the equivalent geometric configuration via Wave 3A (`run_fact_route`)
    w3a_text = (
        "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh a. SA vuông góc với (ABCD). "
        "SA = 2a. Gọi M là trung điểm của SA. Gọi N là trung điểm của SB. "
        "Gọi P là trung điểm của SC. Gọi Q là trung điểm của SD. Xét hình chóp S.MNPQ. "
        "Tính tỉ số thể tích của hai khối chóp S.MNPQ và S.ABCD. "
        "Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bỏ khối chóp S.MNPQ."
    )
    w3a_facts = [
        {
            "id": "f_root",
            "kind": "solid",
            "role": "premise",
            "quotes": ["Cho hình chóp S.ABCD."],
            "solid": "S.ABCD",
            "solid_type": "pyramid",
        },
        {
            "id": "f_base",
            "kind": "polygon_shape",
            "role": "premise",
            "quotes": ["Đáy ABCD là hình vuông cạnh a."],
            "shape": "square",
            "points": ["A", "B", "C", "D"],
            "value": "a",
        },
        {
            "id": "f_perp",
            "kind": "perpendicular",
            "role": "premise",
            "quotes": ["SA vuông góc với (ABCD)."],
            "points_a": ["S", "A"],
            "points_b": ["A", "B", "C", "D"],
        },
        {
            "id": "f_sa",
            "kind": "length",
            "role": "premise",
            "quotes": ["SA = 2a."],
            "measure": "segment",
            "points": ["S", "A"],
            "value": "2a",
        },
        {
            "id": "f_m",
            "kind": "point_def",
            "role": "premise",
            "quotes": ["Gọi M là trung điểm của SA."],
            "point_kind": "midpoint",
            "point": "M",
            "points": ["S", "A"],
        },
        {
            "id": "f_n",
            "kind": "point_def",
            "role": "premise",
            "quotes": ["Gọi N là trung điểm của SB."],
            "point_kind": "midpoint",
            "point": "N",
            "points": ["S", "B"],
        },
        {
            "id": "f_p",
            "kind": "point_def",
            "role": "premise",
            "quotes": ["Gọi P là trung điểm của SC."],
            "point_kind": "midpoint",
            "point": "P",
            "points": ["S", "C"],
        },
        {
            "id": "f_q",
            "kind": "point_def",
            "role": "premise",
            "quotes": ["Gọi Q là trung điểm của SD."],
            "point_kind": "midpoint",
            "point": "Q",
            "points": ["S", "D"],
        },
        {
            "id": "f_sub",
            "kind": "solid",
            "role": "premise",
            "quotes": ["Xét hình chóp S.MNPQ."],
            "solid": "S.MNPQ",
            "solid_type": "pyramid",
        },
        {
            "id": "g_ratio",
            "kind": "question",
            "role": "question",
            "quotes": ["Tính tỉ số thể tích của hai khối chóp S.MNPQ và S.ABCD."],
            "quantity": "volume_ratio",
            "points_a": ["S", "M", "N", "P", "Q"],
            "points_b": ["S", "A", "B", "C", "D"],
        },
        {
            "id": "g_res",
            "kind": "question",
            "role": "question",
            "quotes": [
                "Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bỏ khối chóp S.MNPQ."
            ],
            "quantity": "residual_volume",
            "solid": "S.ABCD",
            "points_a": ["S", "M", "N", "P", "Q"],
        },
    ]
    w3a_res = run_fact_route(w3a_text, {"facts": w3a_facts})
    assert w3a_res.status == "SERVED", f"Wave 3A refused: {w3a_res.code} - {w3a_res.reason}"

    # 3. Verify cross-route mathematical equivalence
    assert a3_res.answers["math_vol_ratio"] == w3a_res.answers["g_ratio"] == "1/8"
    assert a3_res.answers["math_res_vol"] == w3a_res.answers["g_res"] == "7a³/12"
    assert a3_res.answer_exact["math_vol_ratio"] == {
        "coef": "1/8",
        "dim": 0,
        "unit": None,
    }
    assert a3_res.answer_exact["math_res_vol"] == {
        "coef": "7/12",
        "dim": 3,
        "unit": "a",
    }
    assert w3a_res.answer_exact["g_ratio"]["coef"] == "1/8"
    assert w3a_res.answer_exact["g_ratio"]["dim"] == 0
    assert w3a_res.answer_exact["g_res"]["coef"] == "7/12"
    assert w3a_res.answer_exact["g_res"]["dim"] == 3

    # 4. Verify identical squared-volume certificates from the single mathematical authority (`engine.py`)
    a3_ratio_cert = next(m["certificate"] for m in a3_res.math_goals if m["goal_id"] == "math_vol_ratio")
    a3_res_cert = next(m["certificate"] for m in a3_res.math_goals if m["goal_id"] == "math_res_vol")
    w3a_ratio_trace = next(t for t in w3a_res.trace if t.get("step") == "certify_volume_ratio")
    w3a_res_trace = next(t for t in w3a_res.trace if t.get("step") == "certify_residual_volume")

    assert a3_ratio_cert["v2_numerator"] == w3a_ratio_trace["numerator_volume_squared"] == "1/144"
    assert a3_ratio_cert["v2_denominator"] == w3a_ratio_trace["denominator_volume_squared"] == "4/9"
    assert a3_ratio_cert["ratio_exact"] == w3a_ratio_trace["ratio"] == "1/8"

    assert a3_res_cert["residual_volume_squared"] == w3a_res_trace["residual_volume_squared"] == "49/144"
    assert a3_res_cert["complement_ratio"] == w3a_res_trace["residual_fraction"] == "7/8"
    assert a3_res_cert["containment_verified"] is w3a_res_trace["containment_verified"] is True
    assert a3_res_cert["shared_boundary_verified"] is w3a_res_trace["shared_boundary_verified"] is True

    # 5. Neither route fabricates a fake 3D solid mesh for the residual frustum
    a3_solids = [o for o in a3_res.scene3d["objects"] if o["type"] == "solid"]
    w3a_solids = [o for o in w3a_res.scene3d["objects"] if o["type"] == "solid"]
    assert len(a3_solids) == 2  # root pyramid + top cut pyramid only
    assert len(w3a_solids) == 2  # S.ABCD + S.MNPQ only


def test_cross_route_equivalence_triangular_pyramid_ratio_one_third() -> None:
    """Case 2: Triangular pyramid S.ABC cut by plane parallel to (ABC) at SM/SA = 1/3.
    Verify identical exact ratio 1/27 and residual volume 26a³/81 across both routes."""
    a3_problem = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A với AB = AC = a, "
        "SA vuông góc với (ABC) và SA = 2a. Gọi M thuộc SA sao cho SM/SA = 1/3. "
        "Mặt phẳng (P) qua M và song song với hai đường thẳng AB, AC cắt SB, SC. "
        "Dựng thiết diện, khối chóp đỉnh S cắt bởi (P), tính tỉ số thể tích và thể tích phần còn lại."
    )
    a3_payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": a3_problem,
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "sabc",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp S.ABC",
            }
        ],
        "premises": [
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
        ],
        "derived_sections": [
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
        ],
        "simulation_goals": [
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
        ],
        "math_goals": [
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
        ],
    }
    a3_res = run_typed_fact_next_route(a3_payload)
    assert a3_res.status == "SERVED"

    w3a_text = (
        "Cho hình chóp S.ABC. Đáy ABC là tam giác vuông tại A. AB = a. AC = a. "
        "SA vuông góc với (ABC). SA = 2a. Gọi M là điểm thuộc cạnh SA sao cho MA = 2SM. "
        "Gọi N là điểm thuộc cạnh SB sao cho NB = 2SN. Gọi P là điểm thuộc cạnh SC sao cho PC = 2SP. "
        "Xét hình chóp S.MNP. Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC. "
        "Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ khối chóp S.MNP."
    )
    w3a_calls = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC."]}},
        {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "source": {"quotes": ["Đáy ABC là tam giác vuông tại A."]}},
        {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "source": {"quotes": ["AB = a."]}},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "a"}, "source": {"quotes": ["AC = a."]}},
        {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["SA vuông góc với (ABC)."]}},
        {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "source": {"quotes": ["SA = 2a."]}},
        {"id": "c7", "fn": "divide_segment", "args": {"point": "M", "segment": ["S", "A"], "ratio": "1/3"}, "source": {"quotes": ["Gọi M là điểm thuộc cạnh SA sao cho MA = 2SM."]}},
        {"id": "c8", "fn": "divide_segment", "args": {"point": "N", "segment": ["S", "B"], "ratio": "1/3"}, "source": {"quotes": ["Gọi N là điểm thuộc cạnh SB sao cho NB = 2SN."]}},
        {"id": "c9", "fn": "divide_segment", "args": {"point": "P", "segment": ["S", "C"], "ratio": "1/3"}, "source": {"quotes": ["Gọi P là điểm thuộc cạnh SC sao cho PC = 2SP."]}},
        {"id": "c10", "fn": "pyramid", "args": {"apex": "S", "base": ["M", "N", "P"]}, "source": {"quotes": ["Xét hình chóp S.MNP."]}},
        {"id": "g1", "fn": "ask_volume_ratio", "args": {"numerator_solid": "S.MNP", "denominator_solid": "S.ABC"}, "source": {"quotes": ["Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC."]}},
        {"id": "g2", "fn": "ask_residual_volume", "args": {"original_solid": "S.ABC", "subtracted_solids": ["S.MNP"]}, "source": {"quotes": ["Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ khối chóp S.MNP."]}},
    ]
    w3a_res = run_function_route(w3a_text, {"calls": w3a_calls})
    assert w3a_res.status == "SERVED", f"Wave 3A refused: {w3a_res.code} - {w3a_res.reason}"

    assert a3_res.answers["m_ratio_p"] == w3a_res.answers["g1"] == "1/27"
    assert a3_res.answers["m_res_p"] == w3a_res.answers["g2"] == "26a³/81"
    assert a3_res.answer_exact["m_ratio_p"] == {"coef": "1/27", "dim": 0, "unit": None}
    assert a3_res.answer_exact["m_res_p"] == {"coef": "26/81", "dim": 3, "unit": "a"}


def test_wave3a_two_subtracted_solids_sat_disjoint_vs_overlapping() -> None:
    """Verify Wave 3A multi-solid residual volume (2 interior-disjoint subtracted pyramids vs
    2 overlapping subtracted pyramids refused by 3D SAT)."""
    text_disjoint = (
        "Cho hình chóp S.ABC. Đáy ABC là tam giác vuông tại A. AB = 6. AC = 8. "
        "SA vuông góc với (ABC). SA = 9. Gọi M là điểm thuộc cạnh BC sao cho MC = 2BM. "
        "Gọi N là điểm thuộc cạnh BC sao cho NB = 2NC. Xét hình chóp S.ABM. Xét hình chóp S.ANC. "
        "Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ hai khối chóp S.ABM và S.ANC."
    )
    calls_disjoint = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC."]}},
        {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "source": {"quotes": ["Đáy ABC là tam giác vuông tại A."]}},
        {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "6"}, "source": {"quotes": ["AB = 6."]}},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "8"}, "source": {"quotes": ["AC = 8."]}},
        {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["SA vuông góc với (ABC)."]}},
        {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "9"}, "source": {"quotes": ["SA = 9."]}},
        {"id": "c7", "fn": "divide_segment", "args": {"point": "M", "segment": ["B", "C"], "ratio": "1/3"}, "source": {"quotes": ["Gọi M là điểm thuộc cạnh BC sao cho MC = 2BM."]}},
        {"id": "c8", "fn": "divide_segment", "args": {"point": "N", "segment": ["B", "C"], "ratio": "2/3"}, "source": {"quotes": ["Gọi N là điểm thuộc cạnh BC sao cho NB = 2NC."]}},
        {"id": "c9", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "M"]}, "source": {"quotes": ["Xét hình chóp S.ABM."]}},
        {"id": "c10", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "N", "C"]}, "source": {"quotes": ["Xét hình chóp S.ANC."]}},
        {"id": "g1", "fn": "ask_residual_volume", "args": {"original_solid": "S.ABC", "subtracted_solids": ["S.ABM", "S.ANC"]}, "source": {"quotes": ["Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ hai khối chóp S.ABM và S.ANC."]}},
    ]
    res_ok = run_function_route(text_disjoint, {"calls": calls_disjoint})
    assert res_ok.status == "SERVED", f"Unexpected refusal: {res_ok.code} - {res_ok.reason}"
    # V(S.ABC) = 1/3 * (1/2 * 6 * 8) * 9 = 72; V(S.ABM) = 24; V(S.ANC) = 24 => V_res = 24
    assert res_ok.answers["g1"] == "24"

    # Now replace S.ANC with S.ABN, which overlaps S.ABM on [0, 1/3] of BC!
    text_overlap = (
        "Cho hình chóp S.ABC. Đáy ABC là tam giác vuông tại A. AB = 6. AC = 8. "
        "SA vuông góc với (ABC). SA = 9. Gọi M là điểm thuộc cạnh BC sao cho MC = 2BM. "
        "Gọi N là điểm thuộc cạnh BC sao cho NB = 2NC. Xét hình chóp S.ABM. Xét hình chóp S.ABN. "
        "Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ hai khối chóp S.ABM và S.ABN."
    )
    calls_overlap = copy.deepcopy(calls_disjoint)
    calls_overlap[9] = {"id": "c10", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "N"]}, "source": {"quotes": ["Xét hình chóp S.ABN."]}}
    calls_overlap[10] = {"id": "g1", "fn": "ask_residual_volume", "args": {"original_solid": "S.ABC", "subtracted_solids": ["S.ABM", "S.ABN"]}, "source": {"quotes": ["Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ hai khối chóp S.ABM và S.ABN."]}}
    res_ov = run_function_route(text_overlap, {"calls": calls_overlap})
    assert res_ov.status == "REFUSED"
    assert res_ov.code == "OVERLAPPING_SUBTRACTED_SOLIDS"


def test_cross_route_equivalence_shared_base_multi_pyramid_ratio() -> None:
    """Case 3: Shared-base multi-pyramid (S.ABC and D.ABC sharing base ABC, with D midpoint of SA).
    Verify identical exact forward ratio (1/2) and inverse ratio (2) across Adapter /3 (`solid_id::label`)
    and Wave 3A (`run_function_route`)."""
    a3_payload = {
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
        ],
        "math_goals": [
            {
                "goal_id": "m_vol_ratio_fwd",
                "kind": "volume_ratio",
                "numerator_solid_id": "pyr2",
                "denominator_solid_id": "pyr1",
                "quote": "tính tỉ số thể tích",
            },
            {
                "goal_id": "m_vol_ratio_inv",
                "kind": "volume_ratio",
                "numerator_solid_id": "pyr1",
                "denominator_solid_id": "pyr2",
                "quote": "tính tỉ số thể tích",
            },
        ],
    }
    a3_res = run_typed_fact_next_route(a3_payload)
    assert a3_res.status == "SERVED"

    w3a_text = (
        "Cho hình chóp S.ABC. Đáy ABC là tam giác vuông tại A. AB = a. AC = a. "
        "SA vuông góc với (ABC). SA = 2a. Gọi D là trung điểm của SA. Xét hình chóp D.ABC. "
        "Tính tỉ số thể tích của hai khối chóp D.ABC và S.ABC. "
        "Tính tỉ số V_{S.ABC} / V_{D.ABC}."
    )
    w3a_calls = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC."]}},
        {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "source": {"quotes": ["Đáy ABC là tam giác vuông tại A."]}},
        {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "source": {"quotes": ["AB = a."]}},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "a"}, "source": {"quotes": ["AC = a."]}},
        {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["SA vuông góc với (ABC)."]}},
        {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "source": {"quotes": ["SA = 2a."]}},
        {"id": "c7", "fn": "midpoint", "args": {"point": "D", "segment": ["S", "A"]}, "source": {"quotes": ["Gọi D là trung điểm của SA."]}},
        {"id": "c8", "fn": "pyramid", "args": {"apex": "D", "base": ["A", "B", "C"]}, "source": {"quotes": ["Xét hình chóp D.ABC."]}},
        {"id": "g_fwd", "fn": "ask_volume_ratio", "args": {"numerator_solid": "D.ABC", "denominator_solid": "S.ABC"}, "source": {"quotes": ["Tính tỉ số thể tích của hai khối chóp D.ABC và S.ABC."]}},
        {"id": "g_inv", "fn": "ask_volume_ratio", "args": {"numerator_solid": "S.ABC", "denominator_solid": "D.ABC"}, "source": {"quotes": ["Tính tỉ số V_{S.ABC} / V_{D.ABC}."]}},
    ]
    w3a_res = run_function_route(w3a_text, {"calls": w3a_calls})
    assert w3a_res.status == "SERVED"

    assert a3_res.answers["m_vol_ratio_fwd"] == w3a_res.answers["g_fwd"] == "1/2"
    assert a3_res.answers["m_vol_ratio_inv"] == w3a_res.answers["g_inv"] == "2"
    a3_fwd_cert = next(m["certificate"] for m in a3_res.math_goals if m["goal_id"] == "m_vol_ratio_fwd")
    w3a_fwd_trace = next(t for t in w3a_res.trace if t.get("step") == "certify_volume_ratio" and t["object"] == "g_fwd")
    assert a3_fwd_cert["v2_numerator"] == w3a_fwd_trace["numerator_volume_squared"] == "1/36"
    assert a3_fwd_cert["v2_denominator"] == w3a_fwd_trace["denominator_volume_squared"] == "1/9"

