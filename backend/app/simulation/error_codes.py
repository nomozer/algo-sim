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
