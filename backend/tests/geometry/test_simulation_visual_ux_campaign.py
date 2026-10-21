# -*- coding: utf-8 -*-
"""Backend regression and contract tests for simulation-visual-consistency-learning-ux (Session 1 & Session 2)."""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.adapter3_simulation import build_adapter3_simulation_response
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_SCHEMA_VERSION
from app.simulation.semantic_program.display_names import ten_hien_thi

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = REPO_ROOT / "docs" / "evaluation" / "geometry" / "runs" / "simulation-visual-consistency-learning-ux"


def test_free_quantity_math_symbol_display_names() -> None:
    """Point identifiers with _prime (A_prime, B_prime, O_prime) preserve prime notation via ten_hien_thi."""
    info = {pt: {"type": "point3", "depends": [], "producer": None} for pt in ("A_prime", "B_prime", "O_prime")}
    res = ten_hien_thi(info)
    assert res["A_prime"]["notation"] == "A′"
    assert res["B_prime"]["notation"] == "B′"
    assert res["O_prime"]["notation"] == "O′"


def test_curved_route_emits_base_region_and_section_region_roles_and_clean_labels() -> None:
    """Curved solid Scene3D tags base circles with BASE_REGION, cutting circles with SECTION_REGION, and uses A′, B′, O′, r."""
    payload = {
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
                "goal_id": "m_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "cone_upper",
                "denominator_solid_id": "cone_main",
                "quote": "tỉ số thể tích",
            },
        ],
    }
    resp = build_adapter3_simulation_response(payload)
    assert resp["route_d"]["status"] == "SERVED"
    scene = resp["route_d"]["scene3d"]
    by_id = {o["id"]: o for o in scene["objects"]}

    # Base circles have surface_role == BASE_REGION
    assert by_id["duong_tron_day_cone_main"]["surface_role"] == "BASE_REGION"
    # Parallel cutting circle has surface_role == SECTION_REGION
    assert by_id["td_sec_cut"]["surface_role"] == "SECTION_REGION"
    # Axial triangle section has surface_role == AUXILIARY_SURFACE
    assert by_id["td_sec_axial"]["surface_role"] == "AUXILIARY_SURFACE"
    # Derived upper cone radius uses clean 'r' notation, not 'r_cone_upper'
    assert "r" in by_id
    assert by_id["r"]["notation"] == "r"
    # Midpoint on axis uses clean O′ notation
    assert by_id["O_prime"]["notation"] == "O′"


def test_campaign_evaluation_artifacts_valid() -> None:
    """Verify P11 evaluation artifacts (corpus-dev.json, eval-summary.json, SIMULATION_VISUAL_UX_EVALUATION_REPORT.md)."""
    corpus = json.loads((RUN_DIR / "corpus-dev.json").read_text(encoding="utf-8"))
    summary = json.loads((RUN_DIR / "eval-summary.json").read_text(encoding="utf-8"))
    report_md = (RUN_DIR / "SIMULATION_VISUAL_UX_EVALUATION_REPORT.md").read_text(encoding="utf-8")

    assert corpus["evaluation_label"] == "SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND"
    assert corpus["holdout_exposed"] is False
    assert corpus["live_provider_calls"] == 0
    assert corpus["total_scenes"] == 14
    assert corpus["positive_served_scenes"] == 13
    assert corpus["negative_refusal_scenes"] == 1

    assert summary["evaluation_label"] == "SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND"
    assert summary["holdout_exposed"] is False
    assert summary["live_provider_calls"] == 0
    dims = summary["dimensions"]
    assert dims["D1_scene3d_structural_validity"]["rate"] == 1.0
    assert dims["D2_primary_object_presence"]["rate"] == 1.0
    assert dims["D3_section_visibility_when_expected"]["rate"] == 1.0
    assert dims["D4_camera_framing_adequacy"]["rate"] == 1.0
    assert dims["D5_label_collision_rate"]["collision_rate"] == 0.0
    assert dims["D6_interaction_responsiveness"]["rate"] == 1.0
    assert dims["D7_step_progression_validity"]["rate"] == 1.0
    assert dims["D8_default_simulation_mode_compliance"]["rate"] == 1.0
    assert dims["D9_mathematical_analysis_mode_availability"]["rate"] == 1.0
    assert dims["D10_correct_result_presentation_after_explicit_reveal"]["rate"] == 1.0
    assert "SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND" in report_md
