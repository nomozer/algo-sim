"""Bộ đề kiểm thử live AI composition (M7 §3) — 24 đề, 3 nhóm.

Mỗi item khai báo KỲ VỌNG: nhóm, và (với generic) kỳ vọng ngữ nghĩa để
semantic check. Dùng cho cả harness offline (mock) lẫn live (Gemini thật).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalItem:
    id: str
    text: str
    group: str  # "specialized" | "generic" | "unsupported"
    # Với specialized: id mô phỏng kỳ vọng. Với generic: "generic.rule_scene".
    expect_simulation_id: str | None = None
    # Kỳ vọng ngữ nghĩa cho generic (semantic.check_semantic)
    semantic: dict = field(default_factory=lambda: {"kind": "none"})


DATASET: list[EvalItem] = [
    # ── Nhóm A: specialized-supported (8) ────────────────────
    EvalItem("a-findmax", "Cho dãy 7, 9, 6, 10, 8. Tìm phần tử lớn nhất.", "specialized", "algorithm.find_max"),
    EvalItem("a-findmin", "Cho dãy 4, 2, 9, 1, 7. Tìm phần tử nhỏ nhất.", "specialized", "algorithm.find_min"),
    EvalItem("a-countif", "Có 8 bạn điểm 7,5;9;6;8;5;9,5;7;8,5. Đếm số bạn đạt từ 8 trở lên.", "specialized", "algorithm.count_if"),
    EvalItem("a-linear", "Danh sách số báo danh 105,213,178,154,231. Tìm xem 178 có trong danh sách không.", "specialized", "algorithm.linear_search"),
    EvalItem("a-binary", "Dãy đã sắp tăng dần 4,5,6,7,8,9,10. Tìm nhanh số 8 bằng cách chia đôi.", "specialized", "algorithm.binary_search"),
    EvalItem("a-and", "Khi nào cổng logic AND có đầu ra bằng 1?", "specialized", "logic.and_gate"),
    EvalItem("a-binconv", "Số 13 được biểu diễn dưới dạng nhị phân như thế nào?", "specialized", "binary.decimal_to_binary"),
    EvalItem("a-packet", "Minh họa đường đi của một gói tin từ máy tính đến máy chủ.", "specialized", "network.packet_routing"),

    # ── Nhóm B: generic-composable trong DSL v1 (10) ─────────
    EvalItem("b-xor", "Mô phỏng cổng logic XOR gồm hai đầu vào và một đầu ra.", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
    EvalItem("b-or", "Mô phỏng cổng logic OR: đèn sáng khi ít nhất một trong hai công tắc bật.", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "or"}),
    EvalItem("b-not", "Mô phỏng cổng NOT: đầu ra ngược với đầu vào.", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "not"}),
    EvalItem("b-and3", "Đèn chỉ sáng khi cả ba công tắc A, B, C đều bật.", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "and"}),
    EvalItem("b-wsum", "Bốn công tắc có trọng số 8, 4, 2, 1; ban đầu bật các trọng số 8, 4 và 1. Tính tổng trọng số đang bật.", "generic", "generic.rule_scene", {"kind": "weighted_sum", "value": 13}),
    EvalItem("b-wsum2", "Ba công tắc trọng số 5, 3, 2; ban đầu bật trọng số 5 và 2. Hiển thị tổng.", "generic", "generic.rule_scene", {"kind": "weighted_sum", "value": 7}),
    EvalItem("b-path4", "Một vật di chuyển lần lượt qua bốn điểm A → B → C → D.", "generic", "generic.rule_scene", {"kind": "moving_path", "min_len": 4}),
    # Gói tin định tuyến ĐÚNG là bài của mô phỏng chuyên biệt network.packet_routing
    # (hệ đã có sẵn) → kỳ vọng specialized, không tính là lỗi classifier (M7.6 §4).
    EvalItem("b-graphpkt", "Gói tin đi từ máy khách qua switch, router, ISP rồi tới máy chủ.", "specialized", "network.packet_routing"),
    EvalItem("b-xor2", "Cổng XOR: đầu ra bằng 1 khi hai đầu vào KHÁC nhau.", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
    EvalItem("b-orlamp", "Một đèn sáng nếu công tắc X HOẶC công tắc Y đang bật.", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "or"}),
    # Progressive (M7.7): cảnh dựng hình phải hình thành TỪNG BƯỚC (reveal_sequence)
    EvalItem("b-triangle", "Cho hai điểm A và B. Dựng tam giác ABC từng bước: vẽ AB, rồi thêm điểm C, rồi vẽ AC và BC.", "generic", "generic.rule_scene", {"kind": "progressive_reveal", "min_steps": 4}),

    # ── Nhóm C: unsupported / vượt DSL v1 (6) ────────────────
    EvalItem("c-threshold", "Đèn sáng khi ít nhất 2 trong 3 công tắc được bật.", "unsupported"),
    EvalItem("c-parabola", "Vẽ đồ thị hàm số bậc hai y = x^2 - 2x.", "unsupported"),
    EvalItem("c-chem", "Mô phỏng phản ứng hóa học giữa natri và nước.", "unsupported"),
    EvalItem("c-orbit", "Mô phỏng chuyển động tròn của các hành tinh quanh mặt trời.", "unsupported"),
    EvalItem("c-deriv", "Tính đạo hàm của hàm số f(x) = 3x^2 + 2x.", "unsupported"),
    EvalItem("c-freealgo", "Hãy mô phỏng một thuật toán sắp xếp do em tự nghĩ ra.", "unsupported"),
]
