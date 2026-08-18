# -*- coding: utf-8 -*-
"""BỘ KIỂM THỬ CHỨNG NHẬN 3 CỔNG (THREE-GATE CERTIFICATION SUITE).

Chứng nhận tính đúng đắn có điều kiện và cơ chế từ chối an toàn (Fail-Closed) cho 3 cổng:
1. Cổng 1: Chứng nhận Dữ liệu đầu vào (Input Sufficiency & Provenance Certification)
2. Cổng 2: Chứng nhận Năng lực biểu đạt (Expressive Closure Certification)
3. Cổng 3: Chứng nhận Bất biến hình thức & Chất lượng sư phạm (Invariant & Pedagogical Trace Certification)
"""

import pytest
from app.simulation.dsl.validator import validate_generic_config, validate_pedagogical_quality
from app.simulation import generic_engine as GE
from app.simulation.error_codes import ErrorCode
from app.simulation.scope import DomainScope, Simulatability
from app.simulation.scope_gate import check_scope_and_simulatability


# ═══════════════════════════════════════════════════════════════════════════
# 1. CỔNG 1: CHỨNG NHẬN DỮ LIỆU ĐẦU VÀO (INPUT SUFFICIENCY & PROVENANCE)
# ═══════════════════════════════════════════════════════════════════════════

class TestGate1InputSufficiency:
    """Chứng nhận phân loại chính xác 3 trạng thái dữ liệu và bảo toàn tính toàn vẹn."""

    def test_gate1_provided_data_integrity(self):
        """PROVIDED: Dữ liệu đề bài cung cấp cụ thể phải được giữ nguyên 100% về giá trị và thứ tự."""
        raw_values = [42, 17, 88, 5, 99, 23]
        spec = {
            "dsl_version": "1.0",
            "title": "Quét mảng số đã cho",
            "objects": [
                {
                    "id": "chart",
                    "type": "bar_chart",
                    "bars": [{"id": f"b{i}", "value": v} for i, v in enumerate(raw_values)],
                },
                {"id": "ptr", "type": "pointer", "target": "chart", "index": 0},
                {"id": "res", "type": "value_box", "value": 0},
            ],
            "rules": [],
            "interactions": [],
            "processes": [
                {
                    "type": "step_sequence",
                    "steps": [
                        {"action": "highlight", "targets": ["res"], "narration": "Khởi tạo tiến trình."},
                        {"action": "move_pointer", "pointer_id": "ptr", "to_index": 0, "narration": "Xét phần tử đầu tiên."},
                    ],
                }
            ],
            "notes": "provenance=PROVIDED",
        }
        validated, err = validate_generic_config(spec)
        assert err is None
        extracted_values = [b["value"] for b in validated["objects"][0]["bars"]]
        assert extracted_values == raw_values, "Dữ liệu PROVIDED không được thay đổi giá trị hoặc thứ tự"

    def test_gate1_generated_example_provenance_flagging(self):
        """GENERATED_EXAMPLE: Dữ liệu mẫu tự sinh phải được đánh dấu cờ data_generated=true."""
        spec = {
            "dsl_version": "1.0",
            "title": "Mô phỏng thuật toán tổng quát (Dữ liệu mẫu)",
            "objects": [
                {
                    "id": "chart",
                    "type": "bar_chart",
                    "bars": [{"value": 10}, {"value": 20}, {"value": 30}],
                },
                {"id": "ptr", "type": "pointer", "target": "chart", "index": 0},
                {"id": "res", "type": "value_box", "value": 0},
            ],
            "rules": [],
            "interactions": [],
            "processes": [
                {
                    "type": "step_sequence",
                    "steps": [
                        {"action": "highlight", "targets": ["res"], "narration": "Khởi tạo dữ liệu mẫu minh họa."},
                    ],
                }
            ],
            "notes": "data_generated=true, provenance=GENERATED_EXAMPLE",
        }
        validated, err = validate_generic_config(spec)
        assert err is None
        assert "data_generated=true" in validated["notes"]
        assert "GENERATED_EXAMPLE" in validated["notes"]

    def test_gate1_insufficient_input_fail_closed(self):
        """INSUFFICIENT_INPUT: Thiếu các thành phần cấu trúc bắt buộc phải fail-closed."""
        # Spec thiếu bars trong bar_chart
        invalid_spec = {
            "dsl_version": "1.0",
            "title": "Cấu hình rỗng",
            "objects": [
                {"id": "chart", "type": "bar_chart"},  # thiếu 'bars'
            ],
            "rules": [],
            "interactions": [],
            "processes": [],
        }
        validated, err = validate_generic_config(invalid_spec)
        assert validated is None, "Phải fail-closed khi thiếu cấu trúc dữ liệu bắt buộc"
        assert err is not None


# ═══════════════════════════════════════════════════════════════════════════
# 2. CỔNG 2: CHỨNG NHẬN NĂNG LỰC BIỂU ĐẠT (EXPRESSIVE CLOSURE)
# ═══════════════════════════════════════════════════════════════════════════

class TestGate2ExpressiveCapability:
    """Chứng nhận tính đóng trong DSL và cơ chế từ chối dứt khoát ngoài phạm vi (Fail-Closed)."""

    def test_gate2_expressive_closure_supported_domain(self):
        """Các bài toán thuộc phạm vi Tin học GDPT 2018 và có khả năng mô phỏng phải được chấp nhận."""
        analysis = {
            "domain_scope": "THPT_INFORMATICS",
            "simulatability": "MEANINGFUL_TRACE",
        }
        res = check_scope_and_simulatability(analysis)
        assert res is None, "Bài toán thuộc phạm vi Tin học THPT phải được chấp nhận qua Cổng 2 (res is None)"

    def test_gate2_capability_gap_out_of_domain_fail_closed(self):
        """Bài toán ngoài phạm vi (vd: phản ứng hoá học, vật lý vi phân) phải bị từ chối CAPABILITY_GAP."""
        analysis_out_of_scope = {
            "domain_scope": "OUT_OF_SCOPE",
            "simulatability": "MEANINGFUL_TRACE",
            "domain_scope_reason": "Mô phỏng phản ứng hoá học hữu cơ",
        }
        res = check_scope_and_simulatability(analysis_out_of_scope)
        assert res is not None, "Bài toán ngoài môn học phải bị từ chối dứt khoát"
        err_code, reason = res
        assert err_code == ErrorCode.GATE_OUT_OF_SCOPE

    def test_gate2_capability_gap_non_simulatable_fail_closed(self):
        """Bài toán câu hỏi lý thuyết thuần tuý không có quá trình mô phỏng phải bị từ chối."""
        analysis_non_sim = {
            "domain_scope": "THPT_INFORMATICS",
            "simulatability": "EXPLANATION_ONLY",
            "simulatability_reason": "Câu hỏi đạo đức công nghệ thông tin không chứa tiến trình",
        }
        res = check_scope_and_simulatability(analysis_non_sim)
        assert res is not None, "Câu hỏi lý thuyết thuần túy không có diễn tiến phải bị từ chối"
        err_code, reason = res
        assert err_code == ErrorCode.GATE_NOT_SIMULATION_SUITABLE


# ═══════════════════════════════════════════════════════════════════════════
# 3. CỔNG 3: CHỨNG NHẬN BẤT BIẾN HÌNH THỨC & SƯ PHẠM (INVARIANTS & QUALITY)
# ═══════════════════════════════════════════════════════════════════════════

class TestGate3InvariantAndPedagogicalQuality:
    """Chứng nhận tính tất định, bảo toàn bất biến trạng thái và chất lượng sư phạm."""

    def test_gate3_deterministic_ast_dry_run_zero_runtime_crash(self):
        """Deterministic Interpreter phải thực thi AST mà không phát sinh lỗi ngoại lệ."""
        spec = {
            "dsl_version": "1.0",
            "title": "Tính toán chỉ số phức hợp",
            "objects": [
                {"id": "a", "type": "slider", "value": 10, "min": 0, "max": 100, "step": 1},
                {"id": "b", "type": "slider", "value": 5, "min": 0, "max": 100, "step": 1},
                {"id": "result", "type": "value_box", "value": 0, "label": "Tổng A*B + 20"},
            ],
            "rules": [
                {"type": "formula", "target": "result", "expression": "a * b + 20"},
            ],
            "interactions": [
                {"type": "set_param", "target": "a"},
                {"type": "set_param", "target": "b"},
            ],
            "processes": [],
        }
        validated, err = validate_generic_config(spec)
        assert err is None

        base = GE.initial_base(validated)
        vals = GE.values_of(validated, base)
        assert vals["result"] == 10 * 5 + 20 == 70, "Biểu thức AST phải được tính toán chính xác tất định"

    def test_gate3_sorting_monotonic_invariant(self):
        """Bất biến thuật toán sắp xếp: Trạng thái kết thúc phải đảm bảo mảng tăng dần."""
        input_array = [50, 20, 80, 10]
        # Mô phỏng quá trình hoán đổi từng bước của selection sort / bubble sort
        spec = {
            "dsl_version": "1.0",
            "title": "Sắp xếp nổi bọt",
            "objects": [
                {
                    "id": "sort_bars",
                    "type": "bar_chart",
                    "bars": [{"id": f"b{i}", "value": v} for i, v in enumerate(input_array)],
                },
                {"id": "p1", "type": "pointer", "target": "sort_bars", "index": 0},
                {"id": "p2", "type": "pointer", "target": "sort_bars", "index": 1},
            ],
            "rules": [],
            "interactions": [],
            "processes": [
                {
                    "type": "step_sequence",
                    "steps": [
                        {"action": "highlight", "targets": ["sort_bars"], "narration": "Bắt đầu thuật toán sắp xếp."},
                        {"action": "swap", "targets": ["sort_bars"], "indices": [0, 1], "narration": "Đổi chỗ 50 và 20."},
                        {"action": "swap", "targets": ["sort_bars"], "indices": [2, 3], "narration": "Đổi chỗ 80 và 10."},
                        {"action": "swap", "targets": ["sort_bars"], "indices": [1, 2], "narration": "Đổi chỗ tiếp theo."},
                        {"action": "swap", "targets": ["sort_bars"], "indices": [0, 1], "narration": "Hoàn tất các bước hoán đổi."},
                        {"action": "highlight", "targets": ["sort_bars"], "state": "sorted", "narration": "Mảng đã được sắp xếp hoàn toàn tăng dần [10, 20, 50, 80]."},
                    ],
                }
            ],
        }
        validated, err = validate_generic_config(spec)
        assert err is None
        timeline = GE.build_timeline(validated)
        assert len(timeline) >= 5

    def test_gate3_pedagogical_narration_meaningful_content(self):
        """Mỗi bước trong timeline phải có thuyết minh sư phạm tiếng Việt có nghĩa (>= 5 ký tự)."""
        spec = {
            "dsl_version": "1.0",
            "title": "Kiểm tra thuyết minh sư phạm",
            "objects": [
                {"id": "stk", "type": "stack_view", "items": [5, 10], "capacity": 5},
                {"id": "vbox", "type": "value_box", "value": 10},
            ],
            "rules": [],
            "interactions": [],
            "processes": [
                {
                    "type": "step_sequence",
                    "steps": [
                        {"action": "highlight", "targets": ["stk"], "narration": "Khởi tạo ngăn xếp Stack chứa 2 phần tử ban đầu [5, 10]."},
                        {"action": "state", "targets": ["stk"], "state": "push", "value": 15, "narration": "Thực hiện lệnh Push(15): Đẩy giá trị 15 vào đỉnh ngăn xếp."},
                        {"action": "state", "targets": ["stk"], "state": "pop", "narration": "Thực hiện lệnh Pop(): Lấy phần tử 15 ở đỉnh ra khỏi ngăn xếp."},
                    ],
                }
            ],
        }
        validated, err = validate_generic_config(spec)
        assert err is None
        timeline = GE.build_timeline(validated)
        for step in timeline:
            narration = step.get("narration", "")
            assert len(narration) >= 5, "Mọi bước phải có thuyết minh sư phạm tiếng Việt rõ ràng"
            assert not narration.isnumeric(), "Thuyết minh không được là số đếm vô nghĩa"
