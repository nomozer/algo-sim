# -*- coding: utf-8 -*-
"""Unit tests for P4 Curved Solid Expansion in TypedFactNext (`typed-fact-next/1`) and Adapter /3 (`hybrid-simulation-adapter/3`)."""

from __future__ import annotations

import pytest

from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_SCHEMA_VERSION


def test_cylinder_with_parallel_circle_and_axial_section() -> None:
    """Right circular cylinder: base/top circles, axis OO', parallel circle cut, axial rectangle section, exact V & S_xq."""
    payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": (
            "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O', điểm A trên đường tròn đáy dưới, "
            "bán kính đáy R = 2 và chiều cao h = 3. Mặt phẳng (α) song song với đáy cách đáy một khoảng 1 "
            "cắt hình trụ theo thiết diện đường tròn, và thiết diện qua trục qua A. "
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
                "quote": "thiết diện qua trục qua A",
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
                "quote": "thiết diện qua trục qua A",
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
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Expected SERVED, got {res.code}: {res.reason}"
    assert res.answers["m_vol"] == "12π"
    assert res.answers["m_lat"] == "12π"
    assert res.answers["m_par_area"] == "4π"
    assert res.answers["m_ax_area"] == "12"
    assert res.scene3d is not None
    types = {o["type"] for o in res.scene3d["objects"]}
    assert {"curved_solid", "circle3", "polygon3", "segment3", "plane3"} <= types


def test_cone_and_cone_frustum_parallel_cut_and_axial_section() -> None:
    """Right circular cone + parallel plane cut -> upper cone + cone frustum residual volume + axial triangle."""
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
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Expected SERVED, got {res.code}: {res.reason}"
    assert res.answers["m_vol"] == "12π"
    assert res.answers["m_lat"] == "15π"
    assert res.answers["m_axial_area"] == "12"
    assert res.answers["m_ratio"] == "1/8"
    assert res.answers["m_frustum"] == "21π/2"


def test_sphere_plane_section_circle_and_measurements() -> None:
    """Sphere (I, R=5) cut by plane z - 3 = 0 -> section circle of radius 4, area 16*pi, V=500*pi/3, S=100*pi."""
    payload = {
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
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Expected SERVED, got {res.code}: {res.reason}"
    assert res.answers["m_vol"] == "500π/3"
    assert res.answers["m_surf"] == "100π"
    assert res.answers["m_rad"] == "4"
    assert res.answers["m_area"] == "16π"


def test_oblique_ellipse_section_on_cylinder() -> None:
    """Cylinder (R=3, h=20) cut by oblique plane x - z + 10 = 0 -> Ellipse3 with area 9*sqrt(2)*pi."""
    payload = {
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
    }
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Expected SERVED, got {res.code}: {res.reason}"
    assert res.answers["m_el_area"] == "9π√2"
    assert res.scene3d is not None
    assert any(o["type"] == "ellipse3" for o in res.scene3d["objects"])


@pytest.mark.parametrize(
    ("case_id", "payload", "expected_code"),
    [
        (
            "sphere_plane_does_not_cut",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": "Cho mặt cầu (S) tâm I bán kính R = 5 và mặt phẳng (α): z - 6 = 0.",
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
                        "equation_coeffs": ["0", "0", "1", "-6"],
                        "section_shape": "circle",
                        "quote": "mặt phẳng (α): z - 6 = 0",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_plane_section",
                        "target_section_id": "sec",
                        "quote": "mặt phẳng (α): z - 6 = 0",
                    }
                ],
            },
            "CURVED_PLANE_DOES_NOT_CUT",
        ),
        (
            "sphere_plane_tangent",
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
            "CURVED_PLANE_TANGENT",
        ),
        (
            "cone_parabolic_section_refused",
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
            "CURVED_CONE_SECTION_PARABOLIC",
        ),
        (
            "standalone_cone_frustum_blocked",
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
            "CURVED_PRIMITIVE_BLOCKED_BY_KERNEL",
        ),
        (
            "cylinder_oblique_circle_refused",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": "Cho hình trụ tâm đáy O bán kính R = 3, chiều cao h = 20 và mặt phẳng (α): x - z + 10 = 0.",
                "solids": [
                    {
                        "solid_id": "cyl_ob",
                        "solid_type": "cylinder",
                        "notation": "O",
                        "center": "O",
                        "radius": "3",
                        "height": "20",
                        "quote": "Cho hình trụ tâm đáy O bán kính R = 3, chiều cao h = 20",
                    }
                ],
                "derived_sections": [
                    {
                        "section_id": "sec_ob",
                        "plane_name": "α",
                        "target_solid_id": "cyl_ob",
                        "plane_kind": "plane_equation",
                        "equation_coeffs": ["1", "0", "-1", "10"],
                        "section_shape": "circle",
                        "quote": "mặt phẳng (α): x - z + 10 = 0",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_plane_section",
                        "target_section_id": "sec_ob",
                        "quote": "mặt phẳng (α): x - z + 10 = 0",
                    }
                ],
            },
            "CURVED_SECTION_OUTSIDE_V1_CLOSURE",
        ),
        (
            "non_positive_radius_refused",
            {
                "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
                "problem_text": "Cho mặt cầu (S) tâm I bán kính R = -3.",
                "solids": [
                    {
                        "solid_id": "sph_bad",
                        "solid_type": "sphere",
                        "notation": "(S)",
                        "center": "I",
                        "radius": "-3",
                        "quote": "Cho mặt cầu (S) tâm I bán kính R = -3",
                    }
                ],
                "simulation_goals": [
                    {
                        "goal_id": "g1",
                        "kind": "construct_object",
                        "target_solid_id": "sph_bad",
                        "quote": "Cho mặt cầu (S) tâm I bán kính R = -3",
                    }
                ],
            },
            "CURVED_RADIUS_OUTSIDE_DOMAIN",
        ),
    ],
)
def test_curved_solid_fail_closed_refusals(
    case_id: str, payload: dict, expected_code: str
) -> None:
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED", f"Case {case_id} should be REFUSED"
    assert res.code == expected_code, f"Case {case_id}: expected {expected_code}, got {res.code} ({res.reason})"
