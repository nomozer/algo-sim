"""Backend Deterministic Certification Tests (G1 - G5).

Kiểm định tính đúng đắn về mặt ngữ nghĩa (Semantics), kiểu dữ liệu (Types),
liên kết trạng thái (Visual Bindings), tính nhất quán văn bản (Text-State Consistency),
và vệ sinh nội dung (Content Hygiene) trước khi phát hành mô phỏng ra trình duyệt.
"""

from __future__ import annotations
import pytest
from typing import Any

from app.simulation.dsl.semantic_types import (
    infer_semantic_type,
    validate_visual_binding_types,
    SemanticType,
    BindingTypeViolation,
)
from app.simulation.dsl.hygiene import (
    check_content_hygiene,
    HygieneViolation,
)


class TestG1SemanticDataFidelity:
    """G1: SEMANTIC DATA FIDELITY & TYPE CONSISTENCY."""

    def test_sequence_string_binding_with_dummy_zero_fails(self):
        """Mô phỏng chuỗi ký tự nhưng visual object lại gán value = 0 hoặc items rỗng -> Bắt buộc FAIL."""
        spec_obj = {
            "id": "char_strip",
            "type": "array_strip",
            "label": "Chuỗi đầu vào",
            "value": 0,  # Lỗi: dummy 0 thay vì chuỗi ký tự
        }
        canonical_state = {
            "input_symbols": ["(", ")", "[", "]"]
        }
        
        violations = validate_visual_binding_types(
            objects=[spec_obj],
            state=canonical_state,
            expected_bindings={"char_strip": "input_symbols"}
        )
        assert len(violations) > 0
        assert any(v.violation_code == "TYPE_MISMATCH_COERCION" for v in violations)

    def test_integer_binding_with_zero_passes(self):
        """Số nguyên có giá trị 0 (ví dụ count = 0, index = 0) là hoàn toàn hợp lệ -> PASS."""
        spec_obj = {
            "id": "count_box",
            "type": "value_box",
            "label": "Biến đếm",
            "value": 0,
        }
        canonical_state = {
            "count": 0
        }
        
        violations = validate_visual_binding_types(
            objects=[spec_obj],
            state=canonical_state,
            expected_bindings={"count_box": "count"}
        )
        assert len(violations) == 0

    def test_sequence_of_characters_passes(self):
        """Mảng chuỗi ký tự đầy đủ -> PASS."""
        spec_obj = {
            "id": "bracket_strip",
            "type": "array_strip",
            "label": "Chuỗi ngoặc",
            "items": ["(", "{", "[", "]", "}", ")"],
        }
        canonical_state = {
            "brackets": ["(", "{", "[", "]", "}", ")"]
        }
        
        violations = validate_visual_binding_types(
            objects=[spec_obj],
            state=canonical_state,
            expected_bindings={"bracket_strip": "brackets"}
        )
        assert len(violations) == 0


class TestG2VisualBindingIntegrity:
    """G2: VISUAL BINDING INTEGRITY."""

    def test_orphan_target_reference_fails(self):
        """Visual object hoặc Pointer trỏ đến một ID không tồn tại -> FAIL."""
        spec_obj = {
            "id": "ptr_1",
            "type": "pointer",
            "target": "non_existent_array",
            "target_index": 0,
        }
        objects = [
            {"id": "real_array", "type": "array_strip", "items": [1, 2, 3]},
            spec_obj,
        ]
        violations = validate_visual_binding_types(
            objects=objects,
            state={"real_array": [1, 2, 3]},
            expected_bindings={}
        )
        assert any(v.violation_code == "ORPHAN_TARGET_REFERENCE" for v in violations)


class TestG4ContentHygiene:
    """G4: CONTENT HYGIENE GATE."""

    def test_duplicate_heading_in_canvas_fails(self):
        """Canvas chứa heading trùng lặp với tiêu đề bên ngoài -> FAIL."""
        objects = [
            {
                "id": "h1",
                "type": "heading",
                "text": "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
            },
            {
                "id": "strip_1",
                "type": "array_strip",
                "items": ["(", ")"],
            }
        ]
        envelope_title = "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack"
        report = check_content_hygiene(objects=objects, envelope_title=envelope_title)
        assert not report.ok
        assert any(v.code == "DUPLICATE_CANVAS_HEADING" for v in report.violations)

    def test_orphan_empty_labels_fail(self):
        """Label rỗng vô nghĩa hoặc label độc lập trùng tên với component label -> FAIL."""
        objects = [
            {"id": "lbl_1", "type": "label", "text": ""},
            {"id": "lbl_2", "type": "label", "text": "   "},
            {"id": "box_1", "type": "value_box", "label": "Kết quả", "value": "HỢP LỆ"},
            {"id": "lbl_3", "type": "label", "text": "Kết quả"},  # Trùng lặp với box_1
        ]
        report = check_content_hygiene(objects=objects, envelope_title="Demo")
        assert not report.ok
        assert any(v.code == "EMPTY_LABEL" for v in report.violations)
        assert any(v.code == "REDUNDANT_STANDALONE_LABEL" for v in report.violations)
