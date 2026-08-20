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


class InputFact(BaseModel):
    """Một mục dữ liệu đề cho, đã được `analyze` trích và server đóng băng.

    `fact_id` là thứ mà literal trong IR phải THAM CHIẾU tới — ghim *cái nào*,
    không phải *có tồn tại đâu đó* (chuỗi provenance P2, spec §3.4).
    """

    model_config = ConfigDict(frozen=True)

    fact_id: str
    label: str
    values: tuple[Any, ...] = ()


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
