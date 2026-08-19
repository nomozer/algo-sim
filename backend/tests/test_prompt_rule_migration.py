# -*- coding: utf-8 -*-
"""GENERATIVE_CORE_REFACTOR_V1 (Phase 5) — Migration Regression Tests.

Kiểm chứng các rule atom đã được di chuyển từ prompt (analyze.md, simulate.md)
sang code tất định (semantic_types.py, hygiene.py, anchor-resolver, computation_gate, validator).
Mỗi test ghi rõ Rule ID gốc và code owner đảm nhiệm.
"""

import pytest
from app.simulation.dsl.validator import validate_generic_config, validate_pedagogical_quality
from app.simulation.dsl.semantic_types import validate_visual_binding_types
from app.simulation.dsl.hygiene import check_content_hygiene
from app.simulation.computation_gate import check_computation_ownership


# ── RULE-SIM015A (Category F: Data Fidelity / No Dummy Zero Coercion) ───────
class TestRuleF_DataFidelity:
    """Trước: simulate.md L15 'BẮT BUỘC khai báo array_strip với items [...] TUYỆT ĐỐI KHÔNG để trống hoặc gán value = 0'
    Sau: semantic_types.py validate_visual_binding_types() (Gate G1 & G2)."""

    def test_array_strip_dummy_zero_rejected(self):
        """array_strip không có items và bị gán dummy value=0 → TYPE_MISMATCH_COERCION."""
        objects = [
            {"id": "bracket_strip", "type": "array_strip", "value": 0}
        ]
        violations = validate_visual_binding_types(objects=objects, state={})
        assert len(violations) > 0
        assert violations[0].violation_code == "TYPE_MISMATCH_COERCION"
        assert "array_strip" in violations[0].message

    def test_array_strip_with_valid_items_accepted(self):
        """array_strip có items là danh sách ký tự → hợp lệ, không vi phạm."""
        objects = [
            {"id": "bracket_strip", "type": "array_strip", "items": ["{", "[", "(", ")", "]", "}"]}
        ]
        violations = validate_visual_binding_types(objects=objects, state={})
        assert len(violations) == 0

    def test_numeric_zero_on_scalar_value_box_accepted(self):
        """Số 0 hợp lệ trên value_box (đếm=0, tổng=0) KHÔNG bị cấm."""
        objects = [
            {"id": "counter", "type": "value_box", "label": "Đếm", "value": 0}
        ]
        violations = validate_visual_binding_types(objects=objects, state={"counter": 0})
        assert len(violations) == 0

    def test_stack_view_dummy_zero_rejected(self):
        """stack_view bị ép thành dummy 0 thay vì danh sách phần tử → TYPE_MISMATCH_COERCION."""
        objects = [
            {"id": "stk", "type": "stack_view", "value": 0}
        ]
        violations = validate_visual_binding_types(objects=objects, state={})
        assert len(violations) > 0
        assert violations[0].violation_code == "TYPE_MISMATCH_COERCION"


# ── RULE-SIM016A (Category E: Semantic Anchor System / Target Reference) ─────
class TestRuleE_SemanticAnchor:
    """Trước: simulate.md L16 'Đối tượng pointer BẮT BUỘC khai báo target và target_index'
    Sau: semantic_types.py Target Integrity + anchor-resolver.ts resolveSemanticAnchor()."""

    def test_pointer_orphan_target_rejected(self):
        """pointer trỏ vào target không tồn tại → ORPHAN_TARGET_REFERENCE."""
        objects = [
            {"id": "arr", "type": "array_strip", "items": [1, 2, 3]},
            {"id": "ptr", "type": "pointer", "target": "non_existent_arr", "target_index": 0}
        ]
        violations = validate_visual_binding_types(objects=objects, state={})
        assert len(violations) > 0
        assert violations[0].violation_code == "ORPHAN_TARGET_REFERENCE"
        assert "non_existent_arr" in violations[0].message

    def test_pointer_valid_target_accepted(self):
        """pointer trỏ đúng target tồn tại → PASS."""
        objects = [
            {"id": "arr", "type": "array_strip", "items": [1, 2, 3]},
            {"id": "ptr", "type": "pointer", "target": "arr", "target_index": 0}
        ]
        violations = validate_visual_binding_types(objects=objects, state={})
        assert len(violations) == 0


# ── RULE-SIM017A (Category E: Content Hygiene) ──────────────────────────────
class TestRuleE_ContentHygiene:
    """Trước: simulate.md L17 'TUYỆT ĐỐI KHÔNG sinh heading bên trong canvas, KHÔNG sinh label rỗng/mồ côi'
    Sau: hygiene.py check_content_hygiene() (Gate G4)."""

    def test_duplicate_canvas_heading_rejected(self):
        """heading trùng tiêu đề envelope ngoài trang → DUPLICATE_CANVAS_HEADING."""
        objects = [
            {"id": "hd", "type": "heading", "text": "Kiểm tra chuỗi ngoặc"}
        ]
        report = check_content_hygiene(objects=objects, envelope_title="Kiểm tra chuỗi ngoặc")
        assert not report.ok
        assert report.violations[0].code == "DUPLICATE_CANVAS_HEADING"

    def test_empty_label_rejected(self):
        """label rỗng → EMPTY_LABEL."""
        objects = [
            {"id": "lb_empty", "type": "label", "text": "   "}
        ]
        report = check_content_hygiene(objects=objects)
        assert not report.ok
        assert report.violations[0].code == "EMPTY_LABEL"

    def test_redundant_standalone_label_rejected(self):
        """label rời trùng chữ với label inline của node/component → REDUNDANT_STANDALONE_LABEL."""
        objects = [
            {"id": "node1", "type": "node", "label": "Máy chủ A"},
            {"id": "lb_dup", "type": "label", "label": "Máy chủ A"}
        ]
        report = check_content_hygiene(objects=objects)
        assert not report.ok
        assert report.violations[0].code == "REDUNDANT_STANDALONE_LABEL"


# ── RULE-ANA015A / RULE-ANA017A (Category C: Result Ownership / Computation Gate)
class TestRuleC_ComputationOwnership:
    """Trước: analyze.md L15/L17 'BẮT BUỘC chọn provided...', 'TUYỆT ĐỐI KHÔNG chọn algorithmic...'
    Sau: computation_gate.py check_computation_ownership()."""

    def test_provided_and_rule_derivable_allowed_on_generic(self):
        """provided và rule_derivable đều được phép tiếp tục trên generic path."""
        plan = {"unsupported_capabilities": []}
        assert check_computation_ownership({"result_ownership": "provided"}, plan) is None
        assert check_computation_ownership({"result_ownership": "rule_derivable"}, plan) is None

    def test_algorithmic_rejected_on_generic_path(self):
        """algorithmic trên generic path mà không engine nào sở hữu → từ chối trung thực."""
        plan = {"unsupported_capabilities": []}
        err = check_computation_ownership({"result_ownership": "algorithmic"}, plan)
        assert err is not None
        assert "không engine tất định nào của hệ sở hữu" in err

    def test_unsupported_gap_role_rejected_immediately(self):
        """Vai trò gap chưa có engine → từ chối ngay trước khi dựng spec."""
        plan = {"unsupported_capabilities": ["arbitrary_algorithm"]}
        err = check_computation_ownership({"result_ownership": "provided"}, plan)
        assert err is not None
        assert "arbitrary_algorithm" in err
