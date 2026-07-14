# -*- coding: utf-8 -*-
"""Bộ đề đánh giá MỞ RỘNG (M8-PRE S1) — KHÔNG đụng benchmark lịch sử.

`dataset.DATASET` (30 case) là BASELINE HỒI QUY LỊCH SỬ: đóng băng để số liệu
M7.13 / M7.14 / M7.14T còn so sánh được. Mọi case mới nằm ở các pool dưới đây và
được CHỌN qua `--dataset`, không bao giờ chèn vào DATASET.

Bốn pool:
- curriculum   — phủ chương trình SGK (chỉ chủ đề CÓ giá trị sư phạm thật)
- capability   — phủ HÌNH THỨC mô phỏng (gồm sorting: engine có, benchmark trước đây trống)
- cross_domain — CÙNG capability, KHÁC miền bề mặt (bằng chứng tái sử dụng)
- thesis       — bộ flagship đại diện cho luận văn

LUẬT KẾT NẠP (admission rule) — case mới chỉ hợp lệ khi trả lời rõ:
  1. learning_objective      — học sinh hiểu/làm được gì?
  2. pedagogical_rationale   — CƠ CHẾ ẨN nào được mô phỏng, vì sao hơn text/ảnh/video/quiz?
  3. capability_family       — đang kiểm năng lực nào?
  4. complexity              — L1/L2/L3/L4?
  5. result_mode             — executable_simulation / interactive_visualization /
                               practice_activity / unsupported?
  6. curriculum_area         — neo vào đâu trong SGK?
`check_admission` thực thi luật này; `test_datasets.py` khoá lại. Rationale mơ hồ
→ loại case. Một chủ đề CÓ trong chương trình KHÔNG phải là lý do để thêm đề.
"""

from __future__ import annotations

from app.evaluation.dataset import DATASET, EvalItem
from app.evaluation.datasets.capability import CAPABILITY_ITEMS
from app.evaluation.datasets.cross_domain import CROSS_DOMAIN_ITEMS
from app.evaluation.datasets.curriculum import CURRICULUM_ITEMS
from app.evaluation.datasets.thesis import FLAGSHIP_ITEMS

RESULT_MODES = (
    "executable_simulation",
    "interactive_visualization",
    "practice_activity",
    "unsupported",
)
COMPLEXITY_LEVELS = ("L1", "L2", "L3", "L4")

# Pool mới (đã qua admission rule). "regression" là baseline lịch sử — MIỄN TRỪ
# admission rule (viết trước khi có metadata) và TUYỆT ĐỐI không được sửa.
NEW_POOLS: dict[str, list[EvalItem]] = {
    "curriculum": CURRICULUM_ITEMS,
    "capability": CAPABILITY_ITEMS,
    "cross_domain": CROSS_DOMAIN_ITEMS,
}

POOLS: dict[str, list[EvalItem]] = {
    "regression": DATASET,  # FROZEN — 30 case lịch sử
    **NEW_POOLS,
    "thesis": FLAGSHIP_ITEMS,  # trộn case lịch sử + case mới → không tự kiểm admission
}


def get_pool(name: str) -> list[EvalItem]:
    if name not in POOLS:
        raise KeyError(f"Pool không tồn tại: {name}. Có: {', '.join(sorted(POOLS))}")
    return POOLS[name]


def check_admission(item: EvalItem) -> list[str]:
    """Trả danh sách vi phạm luật kết nạp (rỗng = hợp lệ)."""
    errs: list[str] = []
    if len(item.learning_objective.strip()) < 10:
        errs.append(f"{item.id}: thiếu learning_objective")
    if len(item.pedagogical_rationale.strip()) < 30:
        errs.append(f"{item.id}: pedagogical_rationale mơ hồ/thiếu (phải nêu CƠ CHẾ ẨN)")
    if not item.capability_family:
        errs.append(f"{item.id}: thiếu capability_family")
    if not item.curriculum_area:
        errs.append(f"{item.id}: thiếu curriculum_area")
    if item.complexity not in COMPLEXITY_LEVELS:
        errs.append(f"{item.id}: complexity lạ {item.complexity!r}")
    if item.result_mode not in RESULT_MODES:
        errs.append(f"{item.id}: result_mode lạ {item.result_mode!r}")
    return errs
