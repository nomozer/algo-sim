# -*- coding: utf-8 -*-
"""Tests for P1–P4 of TypedFactNext (`typed-fact-next/1`) and Adapter /3 (`hybrid-simulation-adapter/3`)."""

from __future__ import annotations

from fractions import Fraction
import pytest

from app.ai.adapter3_simulation import (
    ADAPTER_V3_VERSION,
    ROUTE_D_SIMULATION_SCHEMA_VERSION,
    build_adapter3_simulation_response,
    run_typed_fact_next_route,
)
from app.ai.hybrid_preview import ADAPTER_VERSION as ADAPTER_V2_VERSION
from app.simulation.geometry_functions.planner import PLANNER_VERSION, TypedFact
from app.simulation.geometry_functions.typed_fact_next import (
    TYPED_FACT_NEXT_SCHEMA_VERSION,
    TypedFactNextValidationError,
    parse_qualified_ref,
    parse_typed_fact_next,
    split_vertex_chain,
)


# ─────────────────────────────────────────────────────────────────────────────
# P1: Versioned TypedFactNext Contract & Coexistence Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_coexistence_with_original_typed_fact_and_adapter2() -> None:
    assert PLANNER_VERSION == "geometry-fact-planner/13"   # /13: hybrid-contract-v2 (owner D5)
    assert ADAPTER_V2_VERSION == "hybrid-preview-adapter/2"
    assert TYPED_FACT_NEXT_SCHEMA_VERSION == "typed-fact-next/1"
    assert ADAPTER_V3_VERSION == "hybrid-simulation-adapter/3"
    tf = TypedFact(
        id="f1",
        kind="solid",
        role="premise",
        quotes=["S.ABC"],
        solid="S.ABC",
        solid_type="pyramid",
    )
    assert tf.kind == "solid"


def test_parse_qualified_ref_and_vertex_chain() -> None:
    assert split_vertex_chain("ABCD") == ("A", "B", "C", "D")
    assert split_vertex_chain("A'B'C'D1") == ("A'", "B'", "C'", "D1")
    assert parse_qualified_ref("pyr1::D") == ("pyr1", "D")
    assert parse_qualified_ref("A'") == (None, "A'")
    with pytest.raises(TypedFactNextValidationError) as exc:
        parse_qualified_ref("bad::ref::X")
    assert exc.value.code == "INVALID_QUALIFIED_REF"


def test_schema_version_mismatch_and_closed_model_refusal() -> None:
    res = run_typed_fact_next_route({"schema_version": "typed-facts/2", "problem_text": "Cho S.ABC"})
    assert res.status == "REFUSED"
    assert res.code == "SCHEMA_VERSION_MISMATCH"

    res_extra = run_typed_fact_next_route(
        {
            "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
            "problem_text": "Cho hình chóp S.ABC.",
            "solids": [{"solid_id": "s1", "notation": "S.ABC", "quote": "S.ABC"}],
            "simulation_goals": [
                {"goal_id": "g1", "kind": "construct_object", "target_solid_id": "s1", "quote": "S.ABC"}
            ],
            "unexpected_field": 123,
        }
    )
    assert res_extra.status == "REFUSED"
    assert res_extra.code == "INVALID_TYPED_FACT_NEXT"


def test_empty_solids_or_simulation_goals_refused() -> None:
    r1 = run_typed_fact_next_route(
        {
            "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
            "problem_text": "Cho hình chóp S.ABC.",
            "solids": [],
            "simulation_goals": [],
        }
    )
    assert r1.status == "REFUSED"
    assert r1.code == "EMPTY_SOLIDS"

    r2 = run_typed_fact_next_route(
        {
            "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
            "problem_text": "Cho hình chóp S.ABC.",
            "solids": [{"solid_id": "s1", "notation": "S.ABC", "quote": "S.ABC"}],
            "simulation_goals": [],
        }
    )
    assert r2.status == "REFUSED"
    assert r2.code == "EMPTY_SIMULATION_GOALS"


# ─────────────────────────────────────────────────────────────────────────────
# P3 Slice A: Unnamed Section Vertices & Derived Sub-Solid Tests
# ─────────────────────────────────────────────────────────────────────────────


def _slice_a_square_pyramid_payload() -> dict:
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


def test_slice_a_unnamed_section_vertices_and_derived_solid() -> None:
    payload = _slice_a_square_pyramid_payload()
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Unexpected refusal: {res.code} - {res.reason}"
    assert res.kernel_check is True
    assert res.scene3d is not None

    # 1. Verify auto-derived unnamed section vertex identities on SB, SC, SD
    vtx_identities = [d for d in res.derived_identities if d["kind"] == "section_vertex"]
    assert len(vtx_identities) == 3
    derived_ids = [d["derived_id"] for d in vtx_identities]
    assert derived_ids == [
        "sec:sec_alpha:edge:S-B",
        "sec:sec_alpha:edge:S-C",
        "sec:sec_alpha:edge:S-D",
    ]
    for d in vtx_identities:
        assert d["anonymous_in_source"] is True
        assert d["notation"] is None
        sym = d["internal_symbol"]
        assert sym in res.points
        # Since M is midpoint of SA (z=1) and (α) || (ABCD), all section vertices lie at z = 1/2 of S (z_S=1 in chart)
        assert res.points[sym][2] == Fraction(1, 2)

    # 2. Verify exact volume ratio (1/2)^3 = 1/8 and residual volume = 7/8 * (2/3 a^3) = 7a^3/12
    assert res.answers["math_vol_ratio"] == "1/8"
    assert res.answer_exact["math_vol_ratio"] == {"coef": "1/8", "dim": 0, "unit": None}
    assert res.answers["math_res_vol"] == "7a³/12"
    assert res.answer_exact["math_res_vol"] == {"coef": "7/12", "dim": 3, "unit": "a"}
    # Section area is (1/2)^2 * a^2 = a^2/4
    assert res.answers["math_sec_area"] == "a²/4"
    assert res.answer_exact["math_sec_area"] == {"coef": "1/4", "dim": 2, "unit": "a"}

    # 3. P4 Scene3D verification: no leaked internal symbol I1/I2/I3 in user-facing notation/label
    objects_by_id = {o["id"]: o for o in res.scene3d["objects"]}
    for d in vtx_identities:
        pid = d["internal_symbol"]
        assert pid in objects_by_id
        p_obj = objects_by_id[pid]
        assert p_obj["notation"] is None
        assert p_obj["synthetic"] is False
        assert "Giao điểm của" in p_obj["label"]
        assert p_obj["source"]["binding"] == "DERIVED_SECTION_VERTEX"
        assert p_obj["source"]["derived_id"] == d["derived_id"]

    # Derived sub-pyramid has notation=None and descriptive Vietnamese label
    derived_solid_desc = next(s for s in res.solids if s["solid_id"] == "top_pyramid")
    top_solid_obj = objects_by_id[derived_solid_desc["scene_object_id"]]
    assert top_solid_obj["notation"] is None
    assert top_solid_obj["label"] == "Hình chóp cắt bởi (α) chứa đỉnh S"
    assert len(top_solid_obj["vertices"]) == 5
    assert len(top_solid_obj["faces"]) == 5

    # Section object exists, is closed, and has 4 vertices
    sec_goal = next(g for g in res.simulation_goals if g["goal_id"] == "sim_section")
    sec_obj = objects_by_id[sec_goal["section_object_id"]]
    assert sec_obj["type"] == "section"
    assert sec_obj["closed"] is True
    assert len(sec_obj["polygon"]) == 4
    assert sec_obj["surface_role"] == "SECTION_REGION"
    assert sec_obj["occludes_edges"] is False

    # Formation steps match events 1-to-1
    events = res.scene3d["events"]
    steps = res.scene3d["formation"]["steps"]
    assert len(events) == len(steps)
    for idx, (ev, st) in enumerate(zip(events, steps)):
        assert ev["step_index"] == st["step_index"] == idx


def test_slice_a_perpendicular_plane_unnamed_section() -> None:
    problem_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) "
        "và SA = a. Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và vuông góc với SA cắt "
        "SB, SC. Dựng thiết diện của hình chóp cắt bởi (α) và tính tỉ số thể tích."
    )
    payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": problem_text,
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
                "kind": "point_is_midpoint",
                "args": {"point": "M", "segment": ["S", "A"]},
                "quote": "Gọi M là trung điểm của SA",
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
        "simulation_goals": [
            {
                "goal_id": "g_sec",
                "kind": "construct_plane_section",
                "target_section_id": "sec_perp",
                "quote": "Dựng thiết diện của hình chóp cắt bởi (α)",
            },
            {
                "goal_id": "g_dsolid",
                "kind": "construct_derived_solid",
                "derived_solid_id": "top_sabc",
                "parent_solid_id": "pyr_sabc",
                "target_section_id": "sec_perp",
                "apex_ref": "S",
                "quote": "Dựng thiết diện của hình chóp cắt bởi (α)",
            },
        ],
        "math_goals": [
            {
                "goal_id": "m_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "top_sabc",
                "denominator_solid_id": "pyr_sabc",
                "quote": "tính tỉ số thể tích",
            }
        ],
    }
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Unexpected refusal: {res.code} - {res.reason}"
    assert res.answers["m_ratio"] == "1/8"


def test_slice_a_refuses_plane_coincident_with_base() -> None:
    payload = _slice_a_square_pyramid_payload()
    # Change through_point from M to A (which lies on the base ABCD)
    payload["derived_sections"][0]["through_point"] = "A"
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code in {"DERIVED_PLANE_IS_REFERENCE", "SECTION_PLANE_IS_FACE", "DEGENERATE_DERIVED_SOLID"}


# ─────────────────────────────────────────────────────────────────────────────
# P3 Slice B: Multi-Solid Identity & Shared Geometry Tests
# ─────────────────────────────────────────────────────────────────────────────


def _slice_b_multi_solid_payload() -> dict:
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
                "target_refs": ["pyr1::D", "pyr2::D"],
                "style_role": "shared_geometry",
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


def test_slice_b_multi_solid_qualified_identity_and_shared_geometry() -> None:
    payload = _slice_b_multi_solid_payload()
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Unexpected refusal: {res.code} - {res.reason}"
    assert res.kernel_check is True
    assert res.scene3d is not None

    # Both solids exist in Scene3D with distinct canonical IDs
    objects_by_id = {o["id"]: o for o in res.scene3d["objects"]}
    assert "khoi_S_ABC" in objects_by_id
    assert "khoi_D1_ABC" in objects_by_id
    assert "D" in objects_by_id
    assert "D1" in objects_by_id
    assert objects_by_id["D1"]["source"]["qualified_ref"] == "pyr2::D"
    assert objects_by_id["D1"]["notation"] == "D1"

    # Verify relations were certified
    rel_ids = {r["relation_id"] for r in res.verified_relations if r["verified"]}
    assert {"rel_shared_v", "rel_shared_face", "rel_frame_1", "rel_frame_2"} <= rel_ids

    # V(pyr2) / V(pyr1) = DA / SA = 1 / 2, V(pyr1) = 1/3 * (1/2 * a * a) * 2a = a^3/3
    assert res.answers["m_vol_ratio"] == "1/2"
    assert res.answers["m_vol_pyr1"] == "a³/3"


def test_slice_b_refuses_ambiguous_unqualified_vertex_reference() -> None:
    payload = _slice_b_multi_solid_payload()
    # Replace qualified "pyr2::D" in highlight_geometry with unqualified "D" (ambiguous between D and D1)
    payload["simulation_goals"][2]["target_refs"] = ["D"]
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code == "AMBIGUOUS_REFERENCE"


def test_slice_b_refuses_shared_entity_mismatch() -> None:
    payload = _slice_b_multi_solid_payload()
    # Claim pyr1::A is shared with pyr2::B
    payload["relations"][0]["pairs"] = [["pyr1::A", "pyr2::B"]]
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code == "SHARED_ENTITY_MISMATCH"


def test_adapter3_preview_envelope_compatibility() -> None:
    envelope = build_adapter3_simulation_response(_slice_a_square_pyramid_payload())
    assert envelope["schema_version"] == "hybrid-Flat-preview/1"
    assert envelope["adapter_version"] == ADAPTER_V3_VERSION
    assert envelope["contract_version"] == TYPED_FACT_NEXT_SCHEMA_VERSION
    assert envelope["route_d"]["schema_version"] == ROUTE_D_SIMULATION_SCHEMA_VERSION
    assert envelope["route_d"]["status"] == "SERVED"
    assert envelope["route_b"]["status"] == "SERVED"
    assert envelope["route_b"]["scene3d"] is not None
    assert envelope["comparison"]["scene3d_bucket"] == "ROUTE_B_ONLY"



def test_slice_a_parallel_two_lines_unnamed_section() -> None:
    problem_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A với AB = AC = a, "
        "SA vuông góc với (ABC) và SA = 2a. Gọi M thuộc SA sao cho SM/SA = 1/3. "
        "Mặt phẳng (P) qua M và song song với hai đường thẳng AB, AC cắt SB, SC. "
        "Dựng thiết diện, khối chóp đỉnh S cắt bởi (P), tính tỉ số thể tích và thể tích phần còn lại."
    )
    payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": problem_text,
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
    res = run_typed_fact_next_route(payload)
    assert res.status == "SERVED", f"Unexpected refusal: {res.code} - {res.reason}"
    # V(top_p) / V(sabc) = (1/3)^3 = 1/27; V(sabc) = 1/3 * (a^2/2) * 2a = a^3/3 => V_res = 26/27 * a^3/3 = 26a^3/81
    assert res.answers["m_ratio_p"] == "1/27"
    assert res.answers["m_res_p"] == "26a³/81"


def test_slice_a_refuses_plane_not_unique_parallel_lines() -> None:
    payload = _slice_a_square_pyramid_payload()
    payload["derived_sections"][0] = {
        "section_id": "sec_alpha",
        "plane_name": "α",
        "target_solid_id": "main_pyramid",
        "plane_kind": "through_point_parallel_two_lines",
        "through_point": "M",
        "parallel_line_a": ["A", "B"],
        "parallel_line_b": ["C", "D"],  # AB || CD in square ABCD -> non-unique / collinear plane span!
        "quote": "Mặt phẳng (α) đi qua M và song song với đáy (ABCD) cắt các cạnh SB, SC, SD",
    }
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code in {"PLANE_NOT_UNIQUE", "COLLINEAR_POINTS"}


def test_slice_a_refuses_plane_missing_lateral_edges() -> None:
    payload = _slice_a_square_pyramid_payload()
    # Plane through M parallel to (SAB) contains SA and SB, so cannot cut SB at a point!
    payload["derived_sections"][0]["parallel_plane"] = ["S", "A", "B"]
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code in {
        "CONTAINED_INFINITE_INTERSECTION",
        "DERIVED_PLANE_IS_REFERENCE",
        "PARALLEL_LINE_AND_PLANE",
        "SECTION_PLANE_IS_FACE",
        "SECTION_NOT_CLOSED_ON_LATERAL_EDGES",
    }


def test_slice_b_refuses_disconnected_coordinate_frame() -> None:
    payload = _slice_b_multi_solid_payload()
    payload["relations"][3]["frame_id"] = "disconnected_frame"
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code == "COORDINATE_FRAME_DISCONNECTED"


def test_p2_refuses_ungrounded_quote_and_mismatched_number() -> None:
    payload = _slice_a_square_pyramid_payload()
    payload["premises"][2]["quote"] = "SA = 99a không có trong đề"
    r1 = run_typed_fact_next_route(payload)
    assert r1.status == "REFUSED"
    assert r1.code == "SOURCE_QUOTE_NOT_FOUND"

    payload2 = _slice_a_square_pyramid_payload()
    payload2["premises"][2]["args"]["value"] = "5a"  # quote says "SA = 2a"
    r2 = run_typed_fact_next_route(payload2)
    assert r2.status == "REFUSED"
    assert r2.code == "SOURCE_NUMBER_MISMATCH"


def test_p2_refuses_underdetermined_solid() -> None:
    problem_text = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA = 2a."
    payload = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": problem_text,
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
        ],
        "simulation_goals": [
            {
                "goal_id": "sim_solid",
                "kind": "construct_object",
                "target_solid_id": "main_pyramid",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
    }
    res = run_typed_fact_next_route(payload)
    assert res.status == "REFUSED"
    assert res.code == "UNDERDETERMINED_POINT"


def test_p4_scene3d_topology_edges_surfaces_and_timeline() -> None:
    res = run_typed_fact_next_route(_slice_a_square_pyramid_payload())
    assert res.status == "SERVED"
    scene = res.scene3d
    assert scene is not None
    objs = {o["id"]: o for o in scene["objects"]}

    # Root solid topology
    root_solid = objs["khoi_S_ABCD"]
    assert root_solid["shape_class"] == "PYRAMID_LIKE"
    assert len(root_solid["edge_ownership"]) == 8
    assert len(root_solid["surfaces"]) == 5
    assert all(s["occludes_edges"] is True for s in root_solid["surfaces"])

    # Derived sub-solid topology
    top_solid_id = next(s["scene_object_id"] for s in res.solids if s["solid_id"] == "top_pyramid")
    top_solid = objs[top_solid_id]
    assert top_solid["shape_class"] == "PYRAMID_LIKE"
    assert len(top_solid["edge_ownership"]) == 8
    assert len(top_solid["surfaces"]) == 5

    # Section endpoint entities & boundary edges
    sec_goal = next(g for g in res.simulation_goals if g["goal_id"] == "sim_section")
    sec_obj = objs[sec_goal["section_object_id"]]
    assert len(sec_obj["endpoint_entities"]) == 4
    assert len(sec_obj["boundary_edge_ids"]) == 4
    assert sec_obj["identity_diagnostics"] == []

    # Highlighted targets have "target" in display_group
    assert "target" in objs["M"]["display_group"]
    assert "target" in top_solid["display_group"]
    assert "target" in sec_obj["display_group"]

    # Construction sequence goal contains ordered steps
    seq_goal = next(g for g in res.simulation_goals if g["goal_id"] == "sim_sequence")
    assert seq_goal["status"] == "SEQUENCED"
    assert len(seq_goal["construction_steps"]) == len(scene["events"])



def test_p5_p6_development_corpus_and_demos_oracle() -> None:
    import hashlib
    import json
    from pathlib import Path

    run_dir = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "evaluation"
        / "geometry"
        / "runs"
        / "typedfact-next-adapter3-simulation"
    )
    corpus = json.loads((run_dir / "corpus-dev.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "eval-summary.json").read_text(encoding="utf-8"))

    assert corpus["measurement_class"] == "DEVELOPMENT_EVALUATION_NOT_BLIND"
    assert summary["measurement_class"] == "DEVELOPMENT_EVALUATION_NOT_BLIND"
    assert summary["wrong_serves"] == 0
    assert summary["positive_passed"] == summary["positive_total"] == 10
    assert summary["negative_passed"] == summary["negative_total"] == 6

    for demo_meta in summary["demos"]:
        demo_path = run_dir / demo_meta["file"]
        assert demo_path.exists()
        raw_bytes = demo_path.read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw_bytes).hexdigest() == demo_meta["sha256"]

    # Correction layer (run `backend-hybrid-contract-unification`, CORRECTED_BY in EVIDENCE_INDEX): the frozen corpus stays
    # byte-identical; the shared Source Gate now decides these. A3-DEV-07 / -08 ask "tính tỉ số thể tích" without naming the
    # two solids, so the ratio's orientation is not in the source (a source defect the frozen run served). A3-DEV-11 still
    # refuses; the gate now speaks first (code order only). A3-DEV-10 is a FALSE refusal of the gate grammar — locked as a
    # strict xfail below, not as an expected result.
    corrected = {"A3-DEV-07": ("REFUSED", {"SOURCE_OBJECT_MISMATCH"}), "A3-DEV-08": ("REFUSED", {"SOURCE_OBJECT_MISMATCH"}),
                 "A3-DEV-11": ("REFUSED", {"SOURCE_OBJECT_MISMATCH"})}
    for case in corpus["cases"]:
        if case["case_id"] == "A3-DEV-10":
            continue
        res = run_typed_fact_next_route(case["payload"])
        if case["case_id"] in corrected:
            status, codes = corrected[case["case_id"]]
            assert (res.status, res.code in codes, res.scene3d) == (status, True, None), (case["case_id"], res.code)
            continue
        assert res.status == case["expected_status"], f"Case {case['case_id']} failed: {res.code}"
        if case["expected_status"] == "SERVED":
            assert res.scene3d is not None
            assert res.kernel_check is True
            for k, expected_exact in case["oracle_exact"].items():
                assert res.answer_exact.get(k) == expected_exact, f"Case {case['case_id']} goal {k} mismatch"
        else:
            assert res.scene3d is None
            assert res.code in set(case["expected_codes"])


@pytest.mark.xfail(strict=True, reason="gate grammar false refusal (owner decision D3): 'thiết diện bởi (α)' not bound")
@pytest.mark.parametrize("case_id,complete_boundary", [("A3-DEV-10", False), ("A3-DEV-03", True), ("A3-DEV-04", True),
                                                       ("A3-DEV-06", True), ("A3-DEV-09", True)])
def test_gate_grammar_false_refusals_are_known_not_expected(case_id, complete_boundary) -> None:
    """Run `backend-hybrid-contract-unification`, independent review: these sections are geometrically valid (with the gate
    stubbed they serve with a closure certificate) but the shared Source Gate refuses them (SOURCE_OBJECT_MISMATCH) because
    its closed grammar does not bind "Dựng …, thiết diện bởi (α)" to the solid. -03/-04/-06/-09 serve today only because
    they omit `cut_edges` (no gate verdict, legacy authority); given their complete boundary they are refused. Strict xfail:
    this turns red the day the gate grammar covers the wording — then it must become a passing test."""
    import copy
    import json
    import re
    from pathlib import Path

    corpus = json.loads((Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation"
                         / "corpus-dev.json").read_text(encoding="utf-8"))
    p = copy.deepcopy(next(c["payload"] for c in corpus["cases"] if c["case_id"] == case_id))
    if complete_boundary:
        sec = p["derived_sections"][0]
        apex, base = next(s for s in p["solids"] if s["solid_id"] == sec["target_solid_id"])["notation"].split(".")
        sec["cut_edges"] = [[apex, v] for v in re.findall(r"[A-Z]'?", base)]
    res = run_typed_fact_next_route(p)
    assert res.status == "SERVED", (res.code, res.reason)
