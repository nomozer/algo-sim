# -*- coding: utf-8 -*-
"""M17-Lite W0 — ánh xạ từ chối/lỗi pipeline sang thông điệp HỌC SINH.

Lớp TRÌNH BÀY sống ở biên API (main.py), KHÔNG nằm trong run_pipeline:
- ``reason`` kỹ thuật của pipeline GIỮ NGUYÊN (nó dạy LLM retry, nuôi
  harness/diagnostics — đổi nó là đổi hợp đồng M13/M14/M15);
- học sinh chỉ thấy ``learner_reason``: tiếng Việt thân thiện, KHÔNG token
  kỹ thuật (không snake_case id, không JSON path, không schema error, không
  message exception thô) — yêu cầu M17 W0 "structured error mapping";
- bất biến #22 không bị chạm: evaluation quan sát envelope pipeline TRƯỚC
  lớp này (attach chỉ chạy ở endpoint).

Test lock: tests/test_learner_messages.py (BE) + learner-error.test.tsx (FE).
"""

from __future__ import annotations

# Thông điệp ĐÓNG — chọn theo failure_category/error_code CÓ CẤU TRÚC,
# tuyệt đối không string-match message kỹ thuật.
_MSG_CAPABILITY_GAP = (
    "Bài này cần một cơ chế mà AlgoSim chưa mô phỏng chính xác được, nên hệ "
    "thống từ chối trung thực thay vì dựng một mô phỏng gần đúng. Bạn có thể "
    "thử một bài thuộc các chủ đề đang hỗ trợ: tìm kiếm, sắp xếp, quét dãy, "
    "số nhị phân, cổng logic, định tuyến gói tin, đóng gói dữ liệu qua các "
    "tầng mạng."
)
_MSG_NOT_IN_CATALOG = (
    "Bài này chưa có mô phỏng phù hợp trong danh mục hiện tại. Danh mục sẽ "
    "được mở rộng dần — bạn có thể thử một bài khác trong các chủ đề đang "
    "hỗ trợ."
)
_MSG_INSUFFICIENT = (
    "Đề chưa cung cấp đủ dữ kiện để mô phỏng (ví dụ: cấu trúc cụ thể của cây — "
    "các nút và quan hệ con trái/con phải). Hãy mô tả rõ hơn rồi thử lại — hệ "
    "không tự bịa dữ liệu thay bạn."
)
_MSG_INCOMPLETE = (
    "Đề đang hỏi nhiều thao tác cùng lúc, nhưng mỗi lần mô phỏng chỉ trình bày "
    "được một. Em hãy tách thành từng lần hỏi (giữ nguyên dữ liệu, mỗi lần chọn "
    "một thao tác) để xem đầy đủ từng bước."
)
_MSG_PIPELINE_FAILED = (
    "AI chưa tạo được mô phỏng hợp lệ cho đề này sau nhiều lần thử. Bạn hãy "
    "diễn đạt lại đề rõ ràng hơn — nêu rõ dữ liệu vào và kết quả cần tìm — "
    "rồi thử lại."
)


def learner_reason(envelope: dict) -> str:
    """Thông điệp học sinh cho envelope ``status="unsupported"`` — chọn theo
    ``failure_category`` (structured), không đọc text reason."""
    if envelope.get("failure_category") == "capability_gap":
        return _MSG_CAPABILITY_GAP
    if envelope.get("failure_category") == "insufficient_specification":
        # M17-RC1 §C2: cổng đủ-dữ-kiện đã sinh thông điệp RIÊNG theo target
        # (`learner_prompt_template` — nêu đúng thứ đang thiếu: dãy số, số cần
        # đổi, cấu trúc cây…). Giữ nguyên vì nó hữu ích hơn câu chung; câu
        # chung chỉ dùng khi vì lý do nào đó không có.
        reason = envelope.get("reason")
        return reason if isinstance(reason, str) and reason else _MSG_INSUFFICIENT
    if envelope.get("failure_category") == "semantic_incomplete":
        # Thông điệp của gate ĐÃ thân thiện và nêu rõ cách tách đề — giữ nguyên
        # thay vì thay bằng câu chung chung kém hữu ích hơn.
        reason = envelope.get("reason")
        return reason if isinstance(reason, str) and reason else _MSG_INCOMPLETE
    return _MSG_NOT_IN_CATALOG


def attach_learner_reason(envelope: dict) -> dict:
    """Gắn ``learner_reason`` vào envelope unsupported (bản sao — không mutate
    envelope pipeline). Envelope ok đi qua NGUYÊN VẸN."""
    if not isinstance(envelope, dict) or envelope.get("status") != "unsupported":
        return envelope
    return {**envelope, "learner_reason": learner_reason(envelope)}


def learner_error_message() -> str:
    """Thông điệp học sinh cho nhánh 422 (simulate thất bại sau retry) —
    CỐ ĐỊNH, không nhúng chi tiết validator (chi tiết kỹ thuật đi field
    ``error_detail`` riêng, FE không render)."""
    return _MSG_PIPELINE_FAILED
