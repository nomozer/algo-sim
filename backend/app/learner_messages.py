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
_MSG_OUT_OF_SCOPE = (
    "Bài này thuộc môn học khác, không nằm trong chương trình Tin học THPT mà "
    "AlgoSim mô phỏng. Hệ thống nói thẳng thay vì dựng một hình vẽ trông giống "
    "mô phỏng nhưng không dựa trên cơ chế nào. Bạn thử một bài Tin học nhé — "
    "thuật toán trên dãy số, số nhị phân, cổng logic, mạng máy tính, cơ sở dữ "
    "liệu, hoặc trang web."
)
# TÁCH KHỎI `_MSG_NOT_IN_CATALOG` có chủ đích: chủ đề này CÓ trong chương trình,
# chỉ là nó không có cơ chế để mô phỏng. Nói "chưa có trong danh mục" ở đây làm
# học sinh tưởng hệ chưa hỗ trợ chủ đề và chờ nó được thêm vào — một lời hứa
# không bao giờ tới, vì chẳng có gì để thêm.
_MSG_NOT_SIMULATION_SUITABLE = (
    "Nội dung này thuộc chương trình Tin học, nhưng nó không có cơ chế nào để "
    "mô phỏng — đọc và hiểu là đủ, dựng cảnh chỉ thành hình trang trí. Nếu bạn "
    "muốn thấy một quá trình diễn ra từng bước, hãy thử một bài có dữ liệu và "
    "có thao tác trên dữ liệu đó."
)
_MSG_PIPELINE_FAILED = (
    "AI chưa tạo được mô phỏng hợp lệ cho đề này sau nhiều lần thử. Bạn hãy "
    "diễn đạt lại đề rõ ràng hơn — nêu rõ dữ liệu vào và kết quả cần tìm — "
    "rồi thử lại."
)


_MSG_GEOMETRY_GENERATION_FAILED = (
    "AlgoSim đã nhận ra đây là bài hình học không gian và đã thử dựng chương "
    "trình mô phỏng, nhưng chương trình sinh ra chưa qua được khâu kiểm chứng. "
    "Hệ thống không hiển thị hình chưa được kiểm — thà không có mô phỏng còn hơn "
    "một hình sai mà em tin theo. Em thử diễn đạt lại đề gọn hơn (nêu rõ hình "
    "gì, dữ kiện nào, cần dựng hoặc tính gì) rồi gửi lại nhé."
)


def learner_reason(envelope: dict) -> str:
    """Thông điệp học sinh cho envelope ``status="unsupported"`` — chọn theo
    ``failure_category`` (structured), không đọc text reason."""
    if envelope.get("failure_category") == "capability_gap":
        return _MSG_CAPABILITY_GAP
    if envelope.get("failure_category") == "geometry_generation_failed":
        # KHÔNG dùng `_MSG_OUT_OF_SCOPE` ở đây, và đó là toàn bộ lý do nhánh này
        # tồn tại: nói "bài thuộc môn khác" cho một đề hình học mà hệ VỪA bỏ hai
        # phút để dựng là đổ lỗi cho đề bài cái sai của hệ.
        return _MSG_GEOMETRY_GENERATION_FAILED
    if envelope.get("failure_category") == "out_of_scope":
        return _MSG_OUT_OF_SCOPE
    if envelope.get("failure_category") == "not_simulation_suitable":
        return _MSG_NOT_SIMULATION_SUITABLE
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
