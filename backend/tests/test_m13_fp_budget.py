# -*- coding: utf-8 -*-
"""M13 Task 8: FP-budget offline — mọi cảnh HỢP LỆ sẵn có vẫn xanh sau khi
validator/runtime bị siết (Task 2b–6: operand coherence ba trạng thái +
role-typing + gỡ object.weight + fail-closed runtime).

Đây KHÔNG phải TDD RED/GREEN — đây là bằng chứng FALSE-POSITIVE BUDGET: siết
chặn Dijkstra-shape sai KHÔNG được lan sang chặn oan cảnh cấu trúc/nested-
boolean hợp lệ. Yêu cầu tường minh của user: "không tối ưu chỉ cho việc chặn
Dijkstra; phải đo cả chiều giữ cảnh hợp lệ".

── KIỂM KÊ COVERAGE ĐÃ CÓ (không lặp lại ở đây) ──────────────────────────
- Sample nhị phân migrate (weighted_sum, không object.weight) qua
  validate_generic_config + values_of → 13:
  test_dsl.py::test_binary_weighted_sum_khong_can_object_weight_van_dung
- Cảnh cấu trúc node/edge/reveal_sequence (KHÔNG rule) qua
  validate_generic_config → ok: test_dsl.py::test_reveal_spec_hop_le
- Cảnh cấu trúc TRIANGLE_STATIC (node/edge/reveal, KHÔNG rule) qua ĐỦ 4 cổng
  run_gates (validate + scene_mode + semantic + engine build) → ok:
  test_patterns.py::test_run_gates_khong_bypass_validation
- Cảnh node/edge/moving_entity/move_along_path (KHÔNG rule) qua
  validate_generic_config → ok: test_dsl.py::test_packet_spec_hop_le
- Nested-boolean M11 (switch → OR → lamp trung gian → AND → lamp cuối) qua
  validate_generic_config → ok: test_dsl.py::test_rule_long_qua_trung_gian_hop_le
- Nested-boolean M11 — bảng chân trị ĐẦY ĐỦ qua check_semantic (không qua
  validate_generic_config, engine gọi trực tiếp trên spec thô):
  test_semantic.py::test_nested_boolean_dung_toan_bo_bang_chan_tri (+ 5 case
  lân cận)

── PHẦN CÒN THIẾU (bổ sung ở file này) ───────────────────────────────────
1. Không có test nào CHẠY QUA validator MỚI (Task 3/5: operand coherence +
   role-typing) RỒI evaluate bảng chân trị nested-boolean trên config đã
   validate — test_dsl.py chỉ validate (không eval), test_semantic.py chỉ
   eval qua check_semantic (không đi qua validate_generic_config). Cần một
   test nối liền cả hai để khóa rằng validator mới không đổi HÀNH VI runtime
   của cảnh nested-boolean hợp lệ.
2. Không có test run_gates (ĐỦ 4 cổng, dùng trong pattern-reuse) cho cảnh
   node/edge/moving_entity — control quan trọng nhất vì đây là shape GẦN
   NHẤT với artifact pseudo-Dijkstra bị khóa ở test_m13_dijkstra_fixture.py
   (cũng node/edge/moving_entity) nhưng KHÔNG có rule sai vai trò (không
   weighted_sum ăn input cạnh) — phải sống qua đủ 4 cổng, không chỉ qua
   validate_generic_config đơn lẻ.
"""

from app.simulation.dsl.validator import validate_generic_config
from app.simulation.generic_engine import initial_base, values_of
from app.simulation.patterns import run_gates


# ── 1. Nested-boolean M11: validate (validator MỚI) + eval 2 dòng đại diện ──

NESTED_BOOLEAN_SPEC = {
    "dsl_version": "1.0",
    "title": "Đèn A và (B hoặc C)",
    "objects": [
        {"id": "a", "type": "switch", "value": 0, "label": "A"},
        {"id": "b", "type": "switch", "value": 0, "label": "B"},
        {"id": "c", "type": "switch", "value": 0, "label": "C"},
        {"id": "t", "type": "lamp", "label": "B hoặc C"},
        {"id": "y", "type": "lamp", "label": "Đèn"},
    ],
    "rules": [
        {"type": "boolean", "op": "or", "inputs": ["b", "c"], "target": "t"},
        {"type": "boolean", "op": "and", "inputs": ["a", "t"], "target": "y"},
    ],
    "interactions": [
        {"type": "toggle", "target": "a"},
        {"type": "toggle", "target": "b"},
        {"type": "toggle", "target": "c"},
    ],
    "processes": [],
}


def test_nested_boolean_m11_qua_validator_moi_va_eval_2_dong_dai_dien():
    """Validator MỚI (operand coherence ba trạng thái + role-typing) phải vẫn
    chấp nhận cảnh nested-boolean hợp lệ (target rule làm input rule khác —
    lamp trung gian "t" là derived numeric/logical source hợp lệ), VÀ config
    ĐÃ chuẩn hóa đó (không phải spec thô) phải evaluate đúng AND(a, OR(b, c))
    tại 2 tổ hợp đại diện — không chỉ validate suông."""
    config, err = validate_generic_config(NESTED_BOOLEAN_SPEC)
    assert err is None and config is not None

    base = initial_base(config)

    # Dòng 1: a=0 chặn AND ngay cả khi nhánh OR trung gian bật (t=1) → y=0.
    row1 = values_of(config, {**base, "a": 0, "b": 1, "c": 0})
    assert row1["t"] == 1
    assert row1["y"] == 0

    # Dòng 2: a=1, đúng một trong b/c bật → t=1 → y=AND(1,1)=1.
    row2 = values_of(config, {**base, "a": 1, "b": 0, "c": 1})
    assert row2["t"] == 1
    assert row2["y"] == 1


# ── 2. run_gates: cảnh node/edge/moving_entity KHÔNG rule — control gần nhất
#      với shape pseudo-Dijkstra bị khóa (test_m13_dijkstra_fixture.py) ─────

STRUCTURAL_ROUTE_SPEC = {
    "dsl_version": "1.0",
    "title": "Gói tin đi qua mạng",
    "objects": [
        {"id": "node_A", "type": "node", "label": "A"},
        {"id": "node_B", "type": "node", "label": "B"},
        {"id": "node_C", "type": "node", "label": "C"},
        {"id": "edge_AB", "type": "edge", "label": "AB", "from": "node_A", "to": "node_B"},
        {"id": "edge_BC", "type": "edge", "label": "BC", "from": "node_B", "to": "node_C"},
        {"id": "runner", "type": "moving_entity", "label": "Gói tin"},
    ],
    "rules": [],
    "interactions": [],
    "processes": [
        {"type": "move_along_path", "entity": "runner", "path": ["node_A", "node_B", "node_C"]},
    ],
}


def test_run_gates_node_edge_moving_entity_khong_rule_song_du_4_cong():
    """M13 FP-budget — control quan trọng nhất: cùng họ object (node/edge/
    moving_entity) với artifact pseudo-Dijkstra bị chặn (weighted_sum ăn input
    CẠNH), nhưng cảnh này KHÔNG hề có rule value-flow sai vai trò — chỉ node/
    edge/move_along_path thuần túy (kiểu 'gói tin đi qua mạng', không tính
    toán số trên cạnh). Phải sống qua ĐỦ 4 cổng run_gates (structural →
    scene_mode → semantic → engine build), không chỉ qua validate_generic_config
    đơn lẻ — chứng minh siết chặn KHÔNG lan sang mọi cảnh đồ thị+di chuyển."""
    config, err = run_gates("progressive", {"relational", "temporal"}, dict(STRUCTURAL_ROUTE_SPEC))
    assert err is None, err
    assert config is not None
    assert config["processes"][0]["path"] == ["node_A", "node_B", "node_C"]
