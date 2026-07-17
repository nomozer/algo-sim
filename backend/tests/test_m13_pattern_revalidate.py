# -*- coding: utf-8 -*-
"""M13 Task 10: pattern reuse — revalidation lock.

Đường pattern reuse (M7.13B — `app/simulation/patterns.py`) tái dùng pattern
đã lưu trong DB, adapt tham số, rồi bắt buộc chạy lại ĐỦ 4 cổng `run_gates`
(structural → scene_mode → semantic → engine build; patterns.py:184-203)
trước khi cho phép dùng lại — reuse KHÔNG BAO GIỜ bypass validation.

Task này KHÔNG phải TDD RED→GREEN — đây là REGRESSION LOCK: vì `run_gates`
gọi `validate_generic_config` (đã siết ở Task 3/5, M13 §3.2), một pattern cũ
mang shape ĐÃ BỊ CẤM (weighted_sum ăn input là id CẠNH — đúng shape sự cố gốc
pseudo-Dijkstra, khóa ở test_m13_dijkstra_fixture.py) PHẢI tự động bị chặn
ngay ở cổng 1 (structural) nếu có ai đó cố "reuse" nó — không lọt qua để
poison một simulation mới, và pipeline phải fallback compose (LLM soạn lại
từ đầu) thay vì dùng mù pattern cũ.

Chiều dương (control chống over-reject): coverage cho run_gates trên cảnh
CẤU TRÚC hợp lệ (node/edge/moving_entity, KHÔNG rule) đã có sẵn ở
`test_m13_fp_budget.py::test_run_gates_node_edge_moving_entity_khong_rule_song_du_4_cong`
— không lặp lại ở đây. File này bổ sung control ở NHÁNH KHÁC: cảnh có RULE
(weighted_sum) hợp lệ — đổi-nhị-phân (switch bit + value_box + weighted_sum
weights [8,4,2,1], như test_dsl.py::test_binary_weighted_sum_khong_can_object_weight_van_dung)
— sống đủ 4 cổng, chứng minh siết chặn không lan sang MỌI cảnh có weighted_sum,
chỉ chặn đúng shape sai vai trò (input là cạnh, không phải input là switch/value_box).
"""
import json
from pathlib import Path

from app.simulation.patterns import run_gates

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "m13_dijkstra_pseudo_algorithm.json").read_text(
        encoding="utf-8"
    )
)


# ── Case âm: pattern cũ mang shape CẤM (weighted_sum ăn input CẠNH) ────────
# scene_mode/roles chọn khớp họ shape (node/edge/moving_entity/move_along_path)
# — cùng cách gọi với STRUCTURAL_ROUTE_SPEC trong test_m13_fp_budget.py để
# nhất quán quy ước test trong milestone này.

def test_pattern_reuse_shape_cam_bi_chan_ngay_cong_1_structural():
    """Giả lập đường reuse: candidate = config của pattern cũ (fixture
    pseudo-Dijkstra) được đưa thẳng vào run_gates như khi DbPatternStore adapt
    tham số xong và thử dùng lại. Validator đã siết (Task 3/5) phải chặn ngay
    ở cổng 1 (structural), KHÔNG để lọt qua cổng scene_mode/semantic/engine —
    chứng minh reuse không thể poison một simulation mới bằng shape đã biết sai."""
    candidate = json.loads(json.dumps(FIXTURE["config"]))  # deep copy, không sửa fixture gốc
    config, err = run_gates("progressive", {"relational", "temporal"}, candidate)
    assert config is None
    assert err is not None
    assert "structural:" in err
    assert "không có nguồn giá trị" in err


# ── Case dương: cảnh đổi-nhị-phân hợp lệ (nhánh khác STRUCTURAL_ROUTE_SPEC) ─
# Nhị phân là cảnh KHÁM PHÁ (đổi giá trị công tắc bit, không có process diễn
# biến theo thời gian) → scene_mode="exploratory" (check_scene_consistency:
# exploratory cấm temporal process; ở đây không có processes nào cả, nên hợp
# lệ). Nếu chọn "progressive"/"hybrid" sẽ rớt oan ở cổng 2 (scene_mode) vì
# thiếu process diễn biến — đó là lỗi test, không phải lỗi code (ghi chú theo
# brief).

BINARY_TO_DECIMAL_SPEC = {
    "dsl_version": "1.0",
    "title": "Đổi số nhị phân 1101 sang thập phân",
    "objects": [
        {"id": "b0", "type": "switch", "label": "8", "value": 1},
        {"id": "b1", "type": "switch", "label": "4", "value": 1},
        {"id": "b2", "type": "switch", "label": "2", "value": 0},
        {"id": "b3", "type": "switch", "label": "1", "value": 1},
        {"id": "out", "type": "value_box", "label": "Giá trị"},
    ],
    "rules": [
        {"type": "weighted_sum", "target": "out",
         "inputs": ["b0", "b1", "b2", "b3"], "weights": [8, 4, 2, 1]},
    ],
    "interactions": [],
    "processes": [],
}


def test_pattern_reuse_shape_hop_le_doi_nhi_phan_song_du_4_cong():
    """Control chống over-reject ở nhánh CÓ RULE weighted_sum (khác nhánh
    node/edge/moving_entity KHÔNG rule đã cover ở test_m13_fp_budget.py):
    cảnh đổi-nhị-phân — input của weighted_sum là switch có "value" (đúng hợp
    đồng provider), không phải id cạnh — phải sống đủ 4 cổng run_gates, không
    bị chặn oan bởi siết chặn nhắm vào shape pseudo-Dijkstra."""
    config, err = run_gates("exploratory", {"numeric"}, dict(BINARY_TO_DECIMAL_SPEC))
    assert err is None, err
    assert config is not None
    assert config["rules"][0]["weights"] == [8, 4, 2, 1]
