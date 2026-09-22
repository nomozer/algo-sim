# -*- coding: utf-8 -*-
"""Test Suite cho Wave SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.

Kiểm chứng 12 tiêu chí bắt buộc theo đặc tả Section 14 và điều kiện phê duyệt ràng buộc:
1. Bắt sai điểm lịch sử 94.0 vs 95.5.
2. Bắt lỗi trộn 2 registry khác tầng (6 compiler primitives vs phantom 7-entry list).
3. Bắt relation kind không tồn tại trong hợp đồng hiện hành.
4. Chứng minh Semantic IR hiện tại đủ (construct_solid), không cần IR statement mới.
5. Chứng minh measurement kernel (the_tich_da_dien) dùng được nguyên trạng cho prism (30 và 5/4).
6. Chứng minh generic mesh của frontend Three.js render đủ cấu trúc lăng trụ.
7. Chứng minh định tuyến sản phẩm không cần đổi trong vertical slice cô lập (LLM_ONLY).
8. Ngăn chặn đưa optional enhancement vào minimal slice.
9. Khẳng định phân định 4 tầng ngữ nghĩa và chữ ký chuẩn của construct_prism.
10. Kiểm tra tính đầy đủ của 12 tầng, RequestContract = CHANGE_REQUIRED, và 5 kinds của SourceInvariant.
11. Kiểm tra tính bất biến của các artifact lịch sử (SHA-256 match).
12. Khóa final decision là INCOMPLETE vì data path RequestContract -> FactGraph chưa giải quyết khép kín (Direction A vs B).
"""
from __future__ import annotations

import pathlib
import sys
from fractions import Fraction
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from scripts import reconcile_second_family_source_scope as RECONCILE


def test_01_historical_score_correction_reporting_error():
    """1. Bắt sai điểm lịch sử 94.0 thay vì 95.5."""
    res = RECONCILE.audit_historical_score_correction()
    assert res["HISTORICAL_SCORE_B_CORRECT"] == 95.5
    assert res["EVIDENCE_REPAIR_REPORTED_SCORE"] == 94.0
    assert res["CLASSIFICATION"] == "REPORTING_ERROR"
    assert res["HISTORY_DRIFT"] == "NO"
    assert res["CORRECTED_SELECTION_SCORE"] == "75.5 / 80"
    assert res["NORMALIZED_SCORE"] == 94.375
    assert res["WINNER"] == "right_triangle_base_right_prism_volume"


def test_02_primitive_registry_separation():
    """2. Bắt lỗi trộn 2 registry khác tầng (6 compiler primitives vs phantom 7-entry list)."""
    res = RECONCILE.audit_registry_identity()
    comp = res["compiler_primitive_registry"]
    assert comp["version"] == "geometry-primitives/1"
    assert comp["member_count"] == 6
    assert comp["members"] == [
        "assign_final_memory",
        "construct_pyramid",
        "construct_triangle",
        "declare_point",
        "measure_quantity",
        "memory_declaration",
    ]
    phantom = res["phantom_inventory_b"]
    assert phantom["member_count"] == 7
    assert phantom["exists_in_backend_code"] is False
    assert phantom["polygon_regular_in_backend"] is False
    assert res["registry_identity_conflicts"] == 0


def test_03_structured_relations_kinds_closed():
    """3. Bắt relation kind không tồn tại nhưng bị báo current; xác nhận 2 relation hiện hữu đủ cho prism."""
    res = RECONCILE.audit_structured_relations_identity()
    current_kinds = res["current_relation_kinds"]
    assert "perpendicular_lines" in current_kinds
    assert "perpendicular_line_plane" in current_kinds
    assert len(current_kinds) == 2

    # Các loại không tồn tại trong hợp đồng
    cls = res["classifications"]
    assert cls["perpendicular_to_base"]["status"] == "PROPOSED_FUTURE_KIND"
    assert cls["face_perpendicular_to_base"]["status"] == "PROPOSED_FUTURE_KIND"
    assert cls["lateral_edge_perpendicular_to_base"]["status"] == "PROPOSED_FUTURE_KIND"

    # Đủ cho lăng trụ
    prism = res["prism_reuse_sufficiency"]
    assert prism["right_triangle_base"] == "perpendicular_lines"
    assert prism["right_prism_vertical_edge"] == "perpendicular_line_plane"
    assert prism["new_relation_kind_required"] is False


def test_04_semantic_ir_construct_solid_reuse():
    """4. Chứng minh Semantic IR hiện tại đủ (construct_solid), không cần IR statement mới."""
    res = RECONCILE.audit_ir_reuse_proof()
    assert res["SEMANTIC_PROGRAM_IR"] == "REUSE_AS_IS"
    assert res["NEW_IR_STATEMENT_REQUIRED"] is False
    assert res["ir_statement_kind_used"] == "construct_solid"
    assert res["sample_vertices_count"] == 6
    assert res["sample_faces_count"] == 5


def test_05_measurement_kernel_polyhedron_volume_reuse():
    """5. Chứng minh measurement kernel (the_tich_da_dien) dùng được nguyên trạng cho prism (30 và 5/4)."""
    res = RECONCILE.audit_measurement_kernel_reuse_proof()
    assert res["MEASUREMENT_KERNEL"] == "REUSE_AS_IS"
    assert res["PRISM_SPECIFIC_VOLUME_FORMULA_REQUIRED"] is False
    assert res["integer_probe"]["measured_volume"] == "30"
    assert res["integer_probe"]["matches"] is True
    assert res["fractional_probe"]["measured_volume"] == "5/4"
    assert res["fractional_probe"]["matches"] is True


def test_06_scene_frontend_mesh_rendering_reuse():
    """6. Chứng minh generic mesh của frontend Three.js render đủ cấu trúc lăng trụ."""
    res = RECONCILE.audit_scene_frontend_reuse_proof()
    assert res["FRONTEND_RENDERER"] == "REUSE_AS_IS"
    assert res["PRISM_SPECIFIC_SHADER"] == "OPTIONAL_FUTURE_ENHANCEMENT"
    assert res["solid_render_hint"] == "mesh"
    assert res["supports_arbitrary_polyhedron"] is True
    assert res["frontend_modification_required"] is False


def test_07_routing_isolation_default_llm_only():
    """7. Chứng minh định tuyến sản phẩm không cần đổi trong vertical slice cô lập (LLM_ONLY)."""
    res = RECONCILE.audit_routing_isolation_proof()
    assert res["ROUTING_CHANGE_FOR_VERTICAL_SLICE"] == "NOT_REQUIRED"
    assert res["DEFAULT_MODE"] == "LLM_ONLY"
    assert res["semantic_route_mode"] == "off"
    assert res["compiler_isolation_verified"] is True


def test_08_optional_enhancements_excluded_from_minimal_slice():
    """8. Ngăn chặn đưa optional enhancement vào minimal slice."""
    allowlist = RECONCILE.audit_minimal_vertical_slice_allowlist()
    opt = allowlist["OPTIONAL_FUTURE_FILES"]
    assert "frontend/src/simulations/domains/geometry/scene3d-view.tsx" in opt
    assert "backend/app/simulation/geometry_compiler/general_spatial_layout.py" in opt


def test_09_four_tier_semantic_ownership_data_path():
    """9. Khẳng định phân định 4 tầng ngữ nghĩa và chữ ký chuẩn xác của construct_prism."""
    res = RECONCILE.audit_semantic_source_of_truth()
    tiers = res["architecture_tiers"]
    assert tiers["tier_1_external_source"]["component"] == "RequestContract"
    assert tiers["tier_1_external_source"]["role"] == "EXTERNAL_SEMANTIC_SOURCE"
    assert tiers["tier_2_normalization_boundary"]["component"] == "contract_adapter"
    assert tiers["tier_2_normalization_boundary"]["role"] == "NORMALIZATION_BOUNDARY"
    assert tiers["tier_3_canonical_internal_owner"]["component"] == "FactGraph"
    assert tiers["tier_3_canonical_internal_owner"]["role"] == "CANONICAL_INTERNAL_NORMALIZED_OWNER"
    assert tiers["tier_4_derived_projection"]["component"] == "primitive arguments"
    assert tiers["tier_4_derived_projection"]["role"] == "DERIVED_PROJECTION"

    # Chữ ký không có nhan
    sig = res["preregistered_primitive_signature"]
    assert sig["name"] == "construct_prism"
    assert sig["parameters"] == ["name", "base_cycle", "top_cycle", "correspondence"]
    assert sig["nhan_parameter_present"] is False


def test_10_layer_classification_and_request_contract_change_required():
    """10. Kiểm tra tính đầy đủ của 12 tầng, RequestContract = CHANGE_REQUIRED, và 5 kinds của SourceInvariant."""
    res = RECONCILE.audit_layer_classification()
    assert res["total_layers"] == 12
    counts = res["counts"]
    assert counts["CHANGE_REQUIRED"] == 6
    assert counts["REUSE_AS_IS"] == 5
    assert counts["NOT_REQUIRED_FOR_ISOLATED_VERTICAL_SLICE"] == 1
    assert counts["OPTIONAL_FUTURE_ENHANCEMENT"] == 0
    assert counts["NOT_ESTABLISHED"] == 0

    # Kiểm tra 5 kinds của SourceInvariant
    assert res["source_invariant_kinds"] == [
        "segment_length",
        "segment_division",
        "segment_division_unresolved",
        "point_coordinate",
        "plane_equation",
    ]

    # Kiểm tra tầng RequestContract là CHANGE_REQUIRED
    req_layer = next(l for l in res["layers"] if l["layer_id"] == "request_contract")
    assert req_layer["classification"] == "CHANGE_REQUIRED"
    assert "No field or JSON pointer exists for prism identity" in req_layer["controlled_probe"]


def test_11_historical_artifacts_immutability():
    """11. Kiểm tra tính bất biến của các artifact lịch sử (SHA-256 match)."""
    res = RECONCILE.audit_historical_integrity()
    assert res["historical_integrity"] == "PASS"
    for fname, finfo in res["files"].items():
        assert finfo["matches"] is True, f"File {fname} hash drifted!"


def test_12_final_decision_incomplete_due_to_unresolved_data_path():
    """12. Khóa final decision là INCOMPLETE vì data path RequestContract -> FactGraph chưa giải quyết khép kín (Direction A vs B)."""
    res = RECONCILE.audit_final_decision()
    assert res["SOURCE_IDENTITY_CONFLICTS"] == 0
    assert res["CRITICAL_NOT_ESTABLISHED_COUNT"] == 1
    assert res["MINIMAL_SCOPE_ESTABLISHED"] == "NO"
    assert res["SINGLE_SEMANTIC_SOURCE_OF_TRUTH"] == "YES"
    assert res["PRODUCT_CODE_CHANGED"] == "NO"
    assert res["FINAL_DECISION"] == "INCOMPLETE"
    assert res["VERTICAL_SLICE_ALLOWED"] == "NO"
    assert res["NEXT_ACTION"] == "SECOND_FAMILY_SOURCE_SCOPE_REAUDIT"
