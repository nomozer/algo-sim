# -*- coding: utf-8 -*-
"""TỪ VỰNG PHẠM VI & KHẢ-MÔ-PHỎNG — MỘT bộ, dùng chung production ↔ evaluation.

Hai câu hỏi khác hẳn nhau, và trộn chúng là nguồn của cả từ chối oan lẫn cảnh
bịa:

  PHẠM VI      — yêu cầu có thuộc môn Tin học THPT không?
  KHẢ-MÔ-PHỎNG — kiến thức này có đáng dựng thành mô phỏng không, và ở DẠNG nào?

Một đề có thể thuộc phạm vi mà không đáng mô phỏng ("đạo đức khi dùng mạng xã
hội" — giải thích được, mô phỏng không thêm gì), và ngược lại một đề ngoài phạm
vi vẫn hoàn toàn mô phỏng được (quỹ tích hình học). Gộp hai trục làm một sẽ mất
đúng hai ca ấy.

`ADJACENT_CONTEXT` là ca hay bị xử oan nhất: đề mang bối cảnh môn khác nhưng CƠ
CHẾ vẫn là Tin học — "đếm số cây cao hơn 2m" là `count_if`. Xếp nó OUT_OF_SCOPE
là từ chối oan một bài Tin học thật.

─── VÌ SAO FILE NÀY Ở `simulation/` CHỨ KHÔNG Ở `evaluation/` ─────────────

Vì production là nơi PHÁN, evaluation chỉ là nơi ĐO. Hướng phụ thuộc cho phép
`evaluation → simulation`, không cho chiều ngược lại (`ARCHITECTURE_MAP §4`).
`evaluation/curriculum_schema.py` import lại từ đây; nếu định nghĩa bộ enum thứ
hai ở đó thì hai bộ sẽ trôi khỏi nhau, và trôi ở đúng chỗ quyết định "từ chối
hay không" là kiểu trôi tệ nhất.
"""

from __future__ import annotations

from enum import Enum


class DomainScope(str, Enum):
    """Yêu cầu có thuộc phạm vi sản phẩm không."""

    #: nội dung Tin học THPT
    THPT_INFORMATICS = "THPT_INFORMATICS"
    #: bề mặt là môn khác, CƠ CHẾ vẫn là Tin học ⇒ KHÔNG được từ chối
    ADJACENT_CONTEXT = "ADJACENT_CONTEXT"
    #: môn khác thật sự ⇒ từ chối trung thực
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    #: không phán được ⇒ xem ghi chú ở `scope_gate.py`, KHÔNG mặc định từ chối
    AMBIGUOUS = "AMBIGUOUS"


class Simulatability(str, Enum):
    """Kiến thức này đáng được trình bày ở DẠNG nào.

    Đây là phán quyết SƯ PHẠM, độc lập với năng lực hiện có của hệ: một chủ đề
    vẫn là `INTERACTIVE_MODEL` kể cả khi AlgoSim chưa làm được nó.
    """

    #: có mô hình nhân quả thao tác được (bật/tắt, đổi tham số → hệ quả tất định)
    INTERACTIVE_MODEL = "INTERACTIVE_MODEL"
    #: hiện vật có ràng buộc (trang web, truy vấn) — thao tác trên chính sản phẩm
    INTERACTIVE_ARTIFACT = "INTERACTIVE_ARTIFACT"
    #: TRÌNH TỰ mới là bài học; xem từng bước có nghĩa, thao tác thì không
    MEANINGFUL_TRACE = "MEANINGFUL_TRACE"
    #: giải thích được, mô phỏng không thêm gì (định nghĩa, đạo đức, hướng nghiệp)
    EXPLANATION_ONLY = "EXPLANATION_ONLY"
    #: không có cơ chế để mô phỏng (kĩ năng thao tác phần mềm, ghi nhớ thuần)
    NOT_SIMULATION_SUITABLE = "NOT_SIMULATION_SUITABLE"


#: Dạng ĐÁNG dựng thành mô phỏng. Ngoài tập này thì dựng cảnh là dựng trang trí.
REQUIRES_SIMULATION = frozenset({
    Simulatability.INTERACTIVE_MODEL,
    Simulatability.INTERACTIVE_ARTIFACT,
    Simulatability.MEANINGFUL_TRACE,
})
