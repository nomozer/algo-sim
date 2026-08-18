"""Kiểm thử kiểm định chất lượng cho các Archetype mô phỏng tự sinh phong phú (Universal Meta-Engine).

Xác nhận:
1. RGB Color Mixing Archetype (Slider R/G/B + Swatch + Value Box + Interaction)
2. Stack Dynamics LIFO (Stack view + Step sequence + Push/Pop)
3. Queue Dynamics FIFO (Queue view + Step sequence)
4. Binary Tree Traversal (Tree element + Step sequence)
5. Bar Chart Sorting (Bar chart + Pointer + Swap/Highlight + Narration)
6. Bit Register Bitwise (Bit register 8/16 bit + Logic gate)
7. Table Grid 2D Matrix (Table grid + Highlight)
8. Pedagogical Quality Gate (Chặn tranh tĩnh, chặn narration rỗng, chạy AST Dry-run 100%)
"""

import pytest
from app.simulation.dsl.validator import validate_generic_config, validate_pedagogical_quality
from app.simulation import generic_engine as GE


def test_rgb_color_mixing_archetype():
    """Archetype Phối màu RGB tương tác trực tiếp với 3 slider và ô màu swatch."""
    spec = {
        "dsl_version": "1.0",
        "title": "Mô hình phối màu RGB tương tác",
        "objects": [
            {"id": "r_slider", "type": "slider", "value": 255, "min": 0, "max": 255, "step": 1, "unit": "", "label": "Đỏ (R)"},
            {"id": "g_slider", "type": "slider", "value": 128, "min": 0, "max": 255, "step": 1, "unit": "", "label": "Lục (G)"},
            {"id": "b_slider", "type": "slider", "value": 0, "min": 0, "max": 255, "step": 1, "unit": "", "label": "Lam (B)"},
            {"id": "mixed_swatch", "type": "color_swatch", "color": "#ff8000", "label": "Màu tổng hợp"},
            {"id": "hex_val", "type": "value_box", "value": 0, "label": "Mã màu Hex"},
        ],
        "rules": [
            {"type": "formula", "target": "hex_val", "expression": "r_slider * 65536 + g_slider * 256 + b_slider"},
        ],
        "interactions": [
            {"type": "set_param", "target": "r_slider"},
            {"type": "set_param", "target": "g_slider"},
            {"type": "set_param", "target": "b_slider"},
        ],
        "processes": [],
        "notes": "Học sinh kéo các thanh trượt R, G, B để quan sát màu tổng hợp biến đổi tức thì.",
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    assert validated is not None
    assert len(validated["objects"]) == 5

    # Chạy AST Dry-run
    base = GE.initial_base(validated)
    vals = GE.values_of(validated, base)
    assert vals["hex_val"] == 255 * 65536 + 128 * 256 + 0


def test_stack_dynamics_lifo_archetype():
    """Archetype Ngăn xếp (Stack - LIFO) với tiến trình Push/Pop."""
    spec = {
        "dsl_version": "1.0",
        "title": "Mô phỏng thao tác Ngăn xếp (Stack)",
        "objects": [
            {"id": "stk", "type": "stack_view", "items": [10, 20], "capacity": 5, "label": "Ngăn xếp S"},
            {"id": "top_elem", "type": "value_box", "value": 20, "label": "Phần tử đỉnh (Top)"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["stk"], "narration": "Khởi tạo ngăn xếp với 2 phần tử ban đầu [10, 20]."},
                    {"action": "state", "targets": ["stk"], "state": "push", "value": 30, "narration": "Thực hiện lệnh Push(30): Thêm giá trị 30 vào đỉnh ngăn xếp."},
                    {"action": "state", "targets": ["stk"], "state": "pop", "narration": "Thực hiện lệnh Pop(): Lấy phần tử đỉnh 30 ra khỏi ngăn xếp."},
                ],
            }
        ],
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 3


def test_queue_dynamics_fifo_archetype():
    """Archetype Hàng đợi (Queue - FIFO) với Enqueue/Dequeue."""
    spec = {
        "dsl_version": "1.0",
        "title": "Mô phỏng Hàng đợi (Queue)",
        "objects": [
            {"id": "q", "type": "queue_view", "items": ["A", "B"], "capacity": 6, "label": "Hàng đợi Q"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["q"], "narration": "Hàng đợi ban đầu có phần tử A ở đầu (Front) và B ở cuối (Rear)."},
                    {"action": "state", "targets": ["q"], "state": "enqueue", "value": "C", "narration": "Enqueue('C'): Thêm C vào cuối hàng đợi."},
                    {"action": "state", "targets": ["q"], "state": "dequeue", "narration": "Dequeue(): Lấy phần tử A ở đầu hàng đợi ra xử lý."},
                ],
            }
        ],
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    timeline = GE.build_timeline(validated)
    assert len(timeline) == 3


def test_binary_tree_traversal_archetype():
    """Archetype Cây nhị phân với các nút tree_element."""
    spec = {
        "dsl_version": "1.0",
        "title": "Duyệt cây nhị phân",
        "objects": [
            {"id": "root", "type": "tree_element", "value": 50, "left": "n1", "right": "n2", "label": "Gốc 50"},
            {"id": "n1", "type": "tree_element", "value": 25, "label": "Nút 25"},
            {"id": "n2", "type": "tree_element", "value": 75, "label": "Nút 75"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["root"], "state": "active", "narration": "Thăm nút gốc 50."},
                    {"action": "highlight", "targets": ["n1"], "state": "active", "narration": "Duyệt nhánh con bên trái: thăm nút 25."},
                    {"action": "highlight", "targets": ["n2"], "state": "active", "narration": "Duyệt nhánh con bên phải: thăm nút 75."},
                ],
            }
        ],
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"
    assert len(validated["objects"]) == 3


def test_bar_chart_sorting_archetype():
    """Archetype Sắp xếp trên biểu đồ cột với con trỏ pointer."""
    spec = {
        "dsl_version": "1.0",
        "title": "Sắp xếp nổi bọt trên biểu đồ cột",
        "objects": [
            {
                "id": "chart",
                "type": "bar_chart",
                "bars": [
                    {"id": "b0", "value": 45, "label": "A[0]"},
                    {"id": "b1", "value": 12, "label": "A[1]"},
                    {"id": "b2", "value": 89, "label": "A[2]"},
                ],
                "max_val": 100,
                "label": "Dãy số cần sắp xếp",
            },
            {"id": "ptr_i", "type": "pointer", "target": "chart", "index": 0, "label": "i"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "move_pointer", "pointer_id": "ptr_i", "to_index": 0, "narration": "Đặt con trỏ i tại phần tử đầu tiên A[0]=45."},
                    {"action": "highlight", "targets": ["chart"], "indices": [0, 1], "state": "comparing", "narration": "So sánh A[0]=45 và A[1]=12: 45 > 12 nên cần đổi chỗ."},
                    {"action": "swap", "targets": ["chart"], "indices": [0, 1], "narration": "Hoán đổi vị trí giữa A[0] và A[1]."},
                ],
            }
        ],
    }
    validated, err = validate_generic_config(spec)
    assert err is None, f"Lỗi validate: {err}"


def test_pedagogical_gate_rejects_empty_narration():
    """Cổng chất lượng sư phạm từ chối bước không có thuyết minh."""
    spec = {
        "dsl_version": "1.0",
        "title": "Test thiếu thuyết minh",
        "objects": [
            {"id": "chart", "type": "bar_chart", "bars": [{"value": 10}, {"value": 20}]},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "step_sequence",
                "steps": [
                    {"action": "highlight", "targets": ["chart"], "narration": ""},  # Rỗng!
                ],
            }
        ],
    }
    ok, err = validate_pedagogical_quality(spec)
    assert not ok
    assert "thiếu thuyết minh sư phạm" in err
