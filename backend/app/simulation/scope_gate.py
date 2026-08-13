# -*- coding: utf-8 -*-
"""M20 W3 — CỔNG PHẠM VI & KHẢ-MÔ-PHỎNG, chạy TRƯỚC đường generic.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

Trước wave này, thứ DUY NHẤT ngăn một đề hoá học biến thành một cảnh hoạt hình
là việc `classify` (LLM) tự từ chối. Bốn cổng đang có đều hỏi câu khác:

  computation        — kết quả có phải TÍNH bằng cơ chế engine không sở hữu?
  mechanism          — family analyze khai có khớp target classify chọn?
  input-sufficiency  — đề đã cho đủ dữ kiện của target chưa?
  completeness       — spec dựng ra có bỏ sót yêu cầu nào không?

Không cổng nào hỏi "đề này có thuộc môn Tin học không". Một đề như "mô phỏng
phản ứng của natri với nước" không đụng gap-role nào, `result_ownership` là
"provided" (đề tả sẵn diễn biến), nên nó đi thẳng qua cổng tính toán. Nếu LLM
hôm đó thấy dễ tính, `generic.rule_scene` dựng ra một cảnh trông rất giống mô
phỏng — và đó là **vi phạm R0**: phán quyết phạm vi đang do LLM sở hữu.

Cổng này chuyển phán quyết ấy về phía tất định, theo đúng khuôn `result_
ownership` đã dùng: **LLM KHAI, server PHÁN.**

─── VÌ SAO CHỈ CHẶN ĐƯỜNG GENERIC ─────────────────────────────────────────

Giống `check_computation_ownership`. Target CHUYÊN BIỆT tồn tại được là vì đã có
người neo nó vào một đơn vị chương trình và viết engine riêng — bản thân việc
`algorithm.bubble_sort` có mặt trong catalog đã là bằng chứng phạm vi. Đường
generic mới là đường dựng-được-mọi-thứ, nên nó là chỗ phải hỏi.

─── MỘT BẤT ĐỐI XỨNG CÓ CHỦ ĐÍCH: `AMBIGUOUS` KHÔNG BỊ TỪ CHỐI ────────────

`check_computation_ownership` fail-closed cả khi `result_ownership` thiếu hoặc
lạ. Cổng này CỐ Ý không làm thế với `AMBIGUOUS`, vì hai loại rủi ro ngược nhau:

  · không chắc về NGUỒN KẾT QUẢ ⇒ rủi ro là hệ tự giải bài rồi vẽ đáp án —
    một lời nói dối. Từ chối là đúng.
  · không chắc về PHẠM VI ⇒ rủi ro là từ chối oan một bài Tin học thật, làm
    học sinh tin rằng hệ không mô phỏng được dạng bài đó.

Nói dối tệ hơn từ chối oan, nên hai cổng fail về hai hướng khác nhau.

NHƯNG **thiếu hẳn trường** thì vẫn fail-closed: đó không phải một phán quyết
"không chắc", đó là hợp đồng prompt đã vỡ. Phân biệt này là toàn bộ lý do
`AMBIGUOUS` phải là một giá trị KHAI ĐƯỢC chứ không phải chỗ trống.
"""

from __future__ import annotations

from app.simulation.error_codes import ErrorCode
from app.simulation.scope import REQUIRES_SIMULATION, DomainScope, Simulatability

#: Giá trị `domain_scope` cho phép đi tiếp. `AMBIGUOUS` nằm trong — xem docstring.
_SCOPE_OK = frozenset({
    DomainScope.THPT_INFORMATICS,
    DomainScope.ADJACENT_CONTEXT,
    DomainScope.AMBIGUOUS,
})


def _read(analysis: dict, field: str, enum_cls):
    """Đọc một trường khai. Trả `(giá_trị | None, có_mặt)`.

    Tách "thiếu trường" khỏi "giá trị lạ" vì hai ca ấy phải xử khác nhau, và
    gộp lại đúng một lần là mất luôn khả năng phân biệt.
    """
    if field not in analysis or analysis.get(field) is None:
        return None, False
    raw = analysis.get(field)
    try:
        return enum_cls(str(raw).strip().upper()), True
    except ValueError:
        return None, True


def check_scope_and_simulatability(analysis: dict) -> tuple[ErrorCode, str] | None:
    """Trả `(mã, lời từ chối tiếng Việt)` khi phải chặn; `None` khi được đi tiếp.

    Thứ tự có ý nghĩa: PHẠM VI phán trước KHẢ-MÔ-PHỎNG. Đề ngoài môn thì dù nó
    mô phỏng đẹp tới đâu cũng không dựng — giống `expected_outcome()` bên
    evaluation, nơi `OUT_OF_SCOPE` thắng mọi vế còn lại.
    """
    scope, scope_present = _read(analysis, "domain_scope", DomainScope)
    if not scope_present:
        return (
            ErrorCode.GATE_SCOPE_UNDECLARED,
            "Phân tích không khai được đề thuộc phạm vi nào — hệ dừng an toàn "
            "thay vì dựng một cảnh không rõ thuộc môn gì.",
        )
    if scope is None:
        return (
            ErrorCode.GATE_SCOPE_UNDECLARED,
            "Phân tích khai một phạm vi ngoài danh sách hệ hiểu — hệ dừng an "
            "toàn thay vì đoán.",
        )
    if scope not in _SCOPE_OK:
        return (
            ErrorCode.GATE_OUT_OF_SCOPE,
            "Bài này thuộc môn khác, không nằm trong chương trình Tin học THPT "
            "mà hệ mô phỏng — hệ từ chối trung thực thay vì dựng một cảnh trông "
            "giống mô phỏng.",
        )

    kind, kind_present = _read(analysis, "simulatability", Simulatability)
    if not kind_present or kind is None:
        return (
            ErrorCode.GATE_SCOPE_UNDECLARED,
            "Phân tích không khai được bài này nên trình bày ở dạng nào — hệ "
            "dừng an toàn thay vì mặc định dựng cảnh.",
        )
    if kind not in REQUIRES_SIMULATION:
        return (
            ErrorCode.GATE_NOT_SIMULATION_SUITABLE,
            "Bài này thuộc chương trình nhưng không có cơ chế nào để mô phỏng — "
            "dựng cảnh cho nó chỉ là trang trí, không giúp hiểu thêm.",
        )
    return None


#: `failure_category` ứng với từng mã — bề mặt học sinh đọc trường này để chọn
#: lời khuyên. `out_of_scope` và `not_simulation_suitable` PHẢI tách nhau: ca đầu
#: là "hệ không làm dạng bài này", ca sau là "dạng bài này không cần mô phỏng" —
#: nói nhầm thành "ngoài danh mục" làm học sinh tưởng chủ đề không được hỗ trợ.
SCOPE_FAILURE_CATEGORY: dict[ErrorCode, str] = {
    ErrorCode.GATE_OUT_OF_SCOPE: "out_of_scope",
    ErrorCode.GATE_NOT_SIMULATION_SUITABLE: "not_simulation_suitable",
    ErrorCode.GATE_SCOPE_UNDECLARED: "capability_gap",
}
