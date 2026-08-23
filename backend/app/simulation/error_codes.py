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
    # M17 W2B-PATCH §A — đề hỏi MỘT quy trình nhiều bước (hợp lệ!) nhưng spec
    # dựng ra bỏ bước hoặc dựng sai tham số bước. PHẢI tách khỏi
    # MULTIPLE_OPERATIONS_NOT_SUPPORTED: hai ca cùng `failure_category`
    # "semantic_incomplete" nhưng lời khuyên cho học sinh NGƯỢC NHAU — ca kia là
    # "tách đề ra", ca này tách cũng vô ích (đề đã là một truy vấn). Review thị
    # giác W2B-PATCH bắt được đúng lỗi này: notice gắn nhầm tiêu đề "TÁCH THÀNH
    # TỪNG YÊU CẦU" cho ca thiếu bước.
    PIPELINE_STAGE_INCOMPLETE = "pipeline_stage_incomplete"
    # M17-RC1 §C2 — đề CHƯA CHO dữ kiện bắt buộc của target đã chọn (dãy số, số
    # cần đổi, mạch logic, đối tượng cảnh…). Tổng quát hoá STRUCTURE_INSUFFICIENT
    # (vốn chỉ dành cho cấu trúc nút–cạnh) ra mọi nhóm dữ kiện. Cùng ý nghĩa:
    # KHÔNG để LLM bịa dữ liệu thay người học.
    INPUT_INSUFFICIENT = "input_insufficient"
    # M20 W3 — cổng PHẠM VI & KHẢ-MÔ-PHỎNG (`scope_gate.py`). Ba mã, ba lời
    # khuyên khác nhau; gộp lại là nói sai với học sinh:
    #   OUT_OF_SCOPE           — môn khác ⇒ "hệ không làm dạng bài này"
    #   NOT_SIMULATION_SUITABLE — thuộc chương trình nhưng không có cơ chế để mô
    #                             phỏng ⇒ "dạng bài này không CẦN mô phỏng".
    #                             Gọi nó là "ngoài danh mục" làm học sinh tưởng
    #                             chủ đề không được hỗ trợ — sai và làm nản.
    #   SCOPE_UNDECLARED        — analyze không khai được trường phạm vi: hợp
    #                             đồng prompt vỡ, KHÔNG phải phán quyết về đề.
    GATE_OUT_OF_SCOPE = "gate_out_of_scope"
    GATE_NOT_SIMULATION_SUITABLE = "gate_not_simulation_suitable"
    GATE_SCOPE_UNDECLARED = "gate_scope_undeclared"

    # 2026-08-20 — route sinh ngữ nghĩa `generic.semantic_program`.
    SEMANTIC_PROGRAM_INVALID = "semantic_program_invalid"
    INTERPRETER_BUDGET_EXHAUSTED = "interpreter_budget_exhausted"
    INPUT_NOT_GROUNDED = "input_not_grounded"
    REQUESTED_OPERATION_UNCOVERED = "requested_operation_uncovered"
    OBLIGATION_WITNESS_UNREALIZED = "obligation_witness_unrealized"
    #: Mức yếu — hệ CHẠY ĐƯỢC nhưng chưa có checker độc lập. KHÔNG phải
    #: `capability_gap`: nói "không làm được" khi thật ra "chưa chứng minh
    #: được" là báo cáo sai năng lực của chính mình.
    SEMANTIC_VERIFICATION_UNAVAILABLE = "semantic_verification_unavailable"
    #: Hậu điều kiện SERVER-OWNED/executable bị vi phạm. KHÔNG diễn giải là
    #: "chứng minh AI hiểu sai đề" — hậu điều kiện do LLM đề xuất mà vi phạm
    #: thì chỉ chứng minh chương trình TỰ MÂU THUẪN.
    POSTCONDITION_VIOLATED = "postcondition_violated"
    #: Chạy được, biên dịch được, nhưng MÀN HÌNH không mang đủ thứ để hiểu bài:
    #: một container biến động không có binding, hoặc chỗ chứa đáp án không hiện
    #: ra. Xem `semantic_program/learner_surface.py`.
    LEARNER_SURFACE_INCOMPLETE = "learner_surface_incomplete"
    #: Telemetry-only, KHÔNG BAO GIỜ lên UI. Exact-trace mismatch là subtype.
    ORACLE_SEMANTIC_MISMATCH = "oracle_semantic_mismatch"


#: `failure_category` của từng mã lỗi route semantic.
#:
#: `verification_gap` tách hẳn `capability_gap` vì chúng trả lời HAI câu hỏi
#: khác nhau (spec §3.6):
#:   capability_gap    — "Máy có thực thi được không?"            → KHÔNG
#:   verification_gap  — "Máy chạy được, nhưng có đủ bằng chứng   → CHƯA
#:                        để phát canonical cho học sinh không?"
#: Gộp hai cái làm một là lẫn "hệ không làm được" với "hệ làm được nhưng chưa
#: chứng minh được" — và chính sự phân biệt đó là đóng góp của đề tài.
SEMANTIC_FAILURE_CATEGORY: dict[str, str] = {
    ErrorCode.SEMANTIC_PROGRAM_INVALID.value: "capability_gap",
    ErrorCode.INTERPRETER_BUDGET_EXHAUSTED.value: "capability_gap",
    ErrorCode.INPUT_NOT_GROUNDED.value: "insufficient_specification",
    ErrorCode.REQUESTED_OPERATION_UNCOVERED.value: "semantic_incomplete",
    ErrorCode.OBLIGATION_WITNESS_UNREALIZED.value: "semantic_incomplete",
    ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE.value: "verification_gap",
    ErrorCode.POSTCONDITION_VIOLATED.value: "verification_gap",
    #: `verification_gap`, KHÔNG phải `capability_gap`: hệ thực thi được bài này,
    #: nó chỉ chưa đủ điều kiện để PHÁT cho học sinh. Đúng ranh giới mà hai tỉ lệ
    #: của luận văn tách nhau — xếp nhầm sang `capability_gap` là tự khai năng
    #: lực thấp hơn thực tế.
    ErrorCode.LEARNER_SURFACE_INCOMPLETE.value: "verification_gap",
}
