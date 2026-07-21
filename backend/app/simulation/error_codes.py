"""M14 §H — mã lỗi CÓ CẤU TRÚC cho các cổng pipeline.

Structured error code là NGUỒN PHÂN LOẠI CHÍNH (quyết định 13). String-match
message tiếng Việt chỉ còn là fallback tương thích (harness, Task 10). Message
tiếng Việt cho LLM retry GIỮ NGUYÊN vai trò dạy — code chạy song song, máy đọc.
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    # Cổng validate/scene (đã có hành vi từ trước — nay gắn mã)
    STRUCTURAL_INVALID = "structural_invalid"
    SCENE_MODE_MISMATCH = "scene_mode_mismatch"
    SYSTEM_FLOW_INVALID = "system_flow_invalid"
    SEMANTIC_INCOMPAT = "semantic_incompat"
    # M14 family pilot
    FAMILY_SPEC_INVALID = "family_spec_invalid"
    ADAPTER_TARGET_INVALID = "adapter_target_invalid"
    # Cổng ownership (M13 + M14)
    GATE_KNOWN_GAP = "gate_known_gap"
    GATE_RESULT_OWNERSHIP = "gate_result_ownership"
    GATE_MECHANISM_OWNERSHIP = "gate_mechanism_ownership"  # E4 tầng 1 → capability_gap
    MECHANISM_VARIANT_MISMATCH = "mechanism_variant_mismatch"  # E4 tầng 2 → retry
    # M15 E2 nhánh 3 — analyze mechanism family ↔ classify target family mâu thuẫn
    ROUTE_MECHANISM_FAMILY_MISMATCH = "route_mechanism_family_mismatch"
    # M17 W2A — đề đòi duyệt cây nhưng analyze KHÔNG thấy cấu trúc cây nào →
    # thiếu dữ kiện; refuse thay vì để LLM bịa cây (chống false-positive sim).
    STRUCTURE_INSUFFICIENT = "structure_insufficient"
    # M17-RC1 §D — mất mát ngữ nghĩa: đề hỏi nhiều thao tác mà family chỉ biểu
    # diễn được một (PHA 1), hoặc spec đã dựng bỏ sót yêu cầu (PHA 2).
    # Mã ĐÓNG và TRUNG LẬP-FAMILY có chủ đích: chi tiết family/cơ chế nằm ở
    # evidence + message, không sinh mã động (giữ enum đóng — M14 §H).
    MULTIPLE_OPERATIONS_NOT_SUPPORTED = "multiple_operations_not_supported"
    SEMANTIC_INCOMPLETE = "semantic_incomplete"
    # M17-RC1 §C2 — đề CHƯA CHO dữ kiện bắt buộc của target đã chọn (dãy số, số
    # cần đổi, mạch logic, đối tượng cảnh…). Tổng quát hoá STRUCTURE_INSUFFICIENT
    # (vốn chỉ dành cho cấu trúc nút–cạnh) ra mọi nhóm dữ kiện. Cùng ý nghĩa:
    # KHÔNG để LLM bịa dữ liệu thay người học.
    INPUT_INSUFFICIENT = "input_insufficient"
