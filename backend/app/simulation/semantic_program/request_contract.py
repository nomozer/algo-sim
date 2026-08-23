# -*- coding: utf-8 -*-
"""RequestContract — server ĐÓNG BĂNG nghĩa vụ do `analyze` khai.

`stage_semantic_program` KHÔNG có quyền khai lại hay sửa nghĩa vụ. Đây là R0 áp
cho chính khâu chấm điểm: tiêu chuẩn chấm được cố định TRƯỚC khi chương trình
được viết ra, nên chương trình không thể nới tiêu chuẩn cho vừa nó.

GIỚI HẠN PHẢI ĐỌC KÈM (spec §5.2): đây là **separation of responsibility**,
KHÔNG phải **independent oracle**. Nó chặn được việc chương trình tự sửa đề cho
vừa mình. Nó KHÔNG chặn được việc cùng một model hiểu sai đề một cách nhất quán
ở cả hai lượt — nghĩa vụ sai và chương trình khớp với nghĩa vụ sai đó vẫn qua
hết mọi cổng. Oracle độc lập thật nằm ở đối chứng module (§3.7) và held-out
benchmark (§7.1).

`frozen=True` không phải trang trí: nó là chỗ luật "không được khai lại" trở
thành bất khả thay vì lời dặn.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from .obligations import Obligation


def norm_value(v: Any) -> Any:
    """Chuẩn hoá một giá trị để so khớp được giữa HAI NGUỒN KHÁC KIỂU.

    `analyze` trả dữ liệu đề cho dưới dạng chuỗi (schema JSON của Gemini không
    có kiểu "số hoặc chuỗi"), còn IR khai `initial_value` đúng kiểu — `12` chứ
    không phải `"12"`. So thẳng thì P2 trượt sạch dù chương trình hoàn toàn
    đúng, và trượt CÂM: mã lỗi sẽ nói "đề không cho những giá trị này".

    Chỉ nới đúng một bậc: chuỗi trông như số thì thành số. Không đoán gì thêm —
    `"true"` vẫn là chuỗi, vì `bool` trong `int` là cái bẫy sẵn có của Python.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip()
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        return s
    return v


class InputFact(BaseModel):
    """Một mục dữ liệu đề cho, đã được `analyze` trích và server đóng băng.

    `fact_id` là thứ mà literal trong IR phải THAM CHIẾU tới — ghim *cái nào*,
    không phải *có tồn tại đâu đó* (chuỗi provenance P2, spec §3.4).
    """

    model_config = ConfigDict(frozen=True)

    fact_id: str
    label: str
    values: tuple[Any, ...] = ()

    # ── P1 — BẰNG CHỨNG NGUỒN ────────────────────────────────────────────────
    #
    # Bốn trạng thái, và sự khác nhau giữa chúng là toàn bộ giá trị của P1:
    #
    #   "unchecked" — không có `problem_text` để đối chiếu (đường gọi cũ, test
    #                 dựng contract bằng tay). KHÔNG kết luận gì; giữ nguyên
    #                 hành vi trước vNext.
    #   "extracted" — `analyze` bỏ trống ô giá trị, extractor tất định tìm thấy
    #                 literal trong đề và server lấy nó. Đây là ca đã quan sát
    #                 được: `values=null` trong khi đề ghi rõ `{[()]}`.
    #   "confirmed" — `analyze` có khai, và MỌI giá trị khai đều truy được về
    #                 một span trong đề.
    #   "claimed"   — `analyze` khai giá trị mà đề không có bằng chứng. Đây là
    #                 thứ P1 sinh ra để bắt: model tự thêm dữ liệu rồi chương
    #                 trình khớp với dữ liệu tự thêm đó, và mọi cổng phía sau
    #                 đều xanh vì chúng chỉ so chương trình với hợp đồng.
    provenance: str = "unchecked"
    source_start: int | None = None
    source_end: int | None = None
    source_text: str | None = None
    #: Đúng những giá trị KHÔNG chứng minh được. Rỗng ⇔ không có gì để trách.
    unproven_values: tuple[Any, ...] = ()


class RequestContract(BaseModel):
    """Hợp đồng yêu cầu — bất biến sau khi server đóng băng."""

    model_config = ConfigDict(frozen=True)

    obligations: tuple[Obligation, ...] = ()
    input_facts: tuple[InputFact, ...] = ()

    def fact(self, fact_id: str) -> InputFact | None:
        for f in self.input_facts:
            if f.fact_id == fact_id:
                return f
        return None
