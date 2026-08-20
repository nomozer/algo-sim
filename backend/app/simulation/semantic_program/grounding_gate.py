# -*- coding: utf-8 -*-
"""`semantic_input_grounding_gate` — thay `check_input_sufficiency` (target-bound).

Cổng cũ gọi `requirements_for(target_id)`, nên nó vô nghĩa khi không có target.
Bảo vệ mà nó giữ thì thật: đề thiếu dữ liệu thì phải HỎI LẠI, không được để LLM
tự bịa.

CHUỖI PROVENANCE HAI ĐOẠN (spec §3.4) — hai đoạn có mức đảm bảo KHÁC HẲN nhau:

    Original input --P1--> RequestContract fact --P2--> SemanticProgram reference

P2 (ở file này) kiểm được TẤT ĐỊNH và mạnh: `source_fact_id` phải tồn tại, và
giá trị phải khớp mục ĐƯỢC CHỈ ĐÍCH DANH. Cố ý KHÔNG làm kiểu "tìm xem giá trị
này có xuất hiện đâu đó trong hợp đồng không" — khớp theo giá trị đơn thuần dễ
trùng ngẫu nhiên, và cho qua cả trường hợp khai sai nguồn.

P1 chỉ mạnh nếu fact có bằng chứng nguồn (`source_span`, vị trí có cấu trúc,
hoặc extractor tất định). Chưa có thì P1 là KHẲNG ĐỊNH của `analyze`, không phải
sự kiện kiểm được — xem `docs/evaluation/semantic-benchmark/P1_LIMITATION.md`.
Gate này là điều kiện CẦN, CHƯA ĐỦ.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
from .request_contract import RequestContract

#: HẠT KHỞI TẠO — giá trị quy ước để bắt đầu, KHÔNG mang thông tin của đề.
#:
#: Phân biệt này là bắt buộc, không phải tinh chỉnh: một biến đếm khai
#: `initial_value = 0` là biến LÀM VIỆC, không phải dữ liệu đề cho. Bắt nó khai
#: `source_fact_id` thì mọi biến tích luỹ đều phải bịa ra một nguồn — và cổng
#: lập tức mất nghĩa vì ai cũng phải nói dối để đi qua.
#:
#: Ngưỡng đặt ở "giá trị quy ước": không thể tuồn dữ liệu đề qua `0`/`""`/rỗng.
#: Giá trị khác — kể cả `1` hay `-1` — vẫn phải ghim nguồn.
_SEED_SCALARS = (0, 0.0, False, "")


def _is_seed(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict, set)) and not value:
        return True
    # `is` cho bool để `False` không nuốt `0` và ngược lại; `==` cho số/chuỗi.
    if isinstance(value, bool):
        return value is False
    return any(
        value == s and not isinstance(s, bool) for s in _SEED_SCALARS
    )


class GroundingResult(BaseModel):
    ok: bool
    error_code: str | None = None
    unresolved: list[str] = Field(default_factory=list)


def _canon(value: Any) -> tuple[Any, ...]:
    """Chuẩn hoá về tuple để so khớp không phụ thuộc list/tuple/vô hướng."""
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return (value,)


def check_grounding(
    contract: RequestContract, spec: SemanticProgramSpec
) -> GroundingResult:
    """P2 — mọi giá trị khởi tạo phải truy được về ĐÚNG mục dữ liệu đã chỉ."""
    unresolved: list[str] = []

    for decl in spec.memory_declarations:
        if _is_seed(decl.initial_value):
            continue  # hạt khởi tạo, không mang thông tin của đề

        fid = decl.source_fact_id
        if not fid:
            unresolved.append(
                f"{decl.name}: có initial_value nhưng thiếu source_fact_id — "
                "không truy được về đề bài"
            )
            continue

        fact = contract.fact(fid)
        if fact is None:
            unresolved.append(
                f"{decl.name}: source_fact_id '{fid}' không có trong RequestContract"
            )
            continue

        khai = _canon(decl.initial_value)
        cho = fact.values
        thua = [v for v in khai if v not in cho]
        if thua:
            unresolved.append(
                f"{decl.name}: giá trị {thua!r} không có trong mục '{fid}' "
                f"({fact.label}) — đề không cho những giá trị này"
            )

    if unresolved:
        return GroundingResult(
            ok=False, error_code="INPUT_NOT_GROUNDED", unresolved=unresolved
        )
    return GroundingResult(ok=True)
