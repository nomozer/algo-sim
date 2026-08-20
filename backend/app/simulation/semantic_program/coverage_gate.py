# -*- coding: utf-8 -*-
"""SemanticCoverageGate — thay `completeness_gate` THEO-TARGET.

`completeness_gate` cũ nhận `target_id` và tra registry, nên nó vô nghĩa với bài
không có module. Nhưng bảo vệ sư phạm mà nó giữ thì THẬT: *đề hỏi hai việc mà
mô phỏng chỉ làm một thì phải từ chối, không được im lặng làm một nửa.* File này
giữ đúng bảo vệ đó mà không cần catalog.

BA CÂU HỎI KHÁC NHAU, đừng gộp (spec §5.3):
    C₁a — nghĩa vụ có witness hợp lệ VỀ CẤU TRÚC không?   (trước execution, ở đây)
    C₁b — witness đó có THẬT SỰ được hiện thực hoá không?  (sau execution, ở đây)
    C₂  — chạy xong có thoả TÍNH CHẤT không?               (postconditions.py)
"""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
from .obligations import accepts_container_type, is_supported
from .request_contract import RequestContract


class CoverageResult(BaseModel):
    ok: bool
    error_code: str | None = None
    missing: list[str] = Field(default_factory=list)
    #: Nghĩa vụ hợp lệ nhưng KHÔNG có checker server-owned → mức yếu (§5.4).
    #: Tách khỏi `missing` vì "chưa chứng minh được" ≠ "thiếu".
    weak_kinds: list[str] = Field(default_factory=list)


def _producers(statements: Iterable) -> set[str]:
    """Mọi biến có ÍT NHẤT MỘT câu lệnh tạo ra nó.

    C₁a chỉ hỏi "có ai viết vào biến này không", KHÔNG hỏi "câu lệnh đó có chạy
    không" — nên nhánh lồng vẫn tính là có. Việc nó có đạt tới hay không là câu
    hỏi của C₁b, và tách hai câu hỏi chính là điểm của thiết kế này.
    """
    found: set[str] = set()
    for st in statements or ():
        kind = getattr(st, "kind", None)
        if kind == "assign":
            found.add(st.target_var)
        elif kind in ("pop", "dequeue"):
            dest = getattr(st, "dest_var", None)
            if dest:
                found.add(dest)
        elif kind in ("write_index", "map_set", "swap", "push", "enqueue",
                      "set_insert", "set_remove"):
            found.add(st.container)
        elif kind in ("for_range", "for_each"):
            var = getattr(st, "loop_var", None) or getattr(st, "item_var", None)
            if var:
                found.add(var)
        for attr in ("body", "then_body", "else_body"):
            sub = getattr(st, attr, None)
            if sub:
                found |= _producers(sub)
    return found


def check_structural_coverage(
    contract: RequestContract, spec: SemanticProgramSpec
) -> CoverageResult:
    """C₁a — chạy TRƯỚC execution."""
    declared = {d.name: d.type for d in spec.memory_declarations}
    producers = _producers(spec.statements)

    missing: list[str] = []
    weak: list[str] = []

    for ob in contract.obligations:
        if not is_supported(ob.kind):
            # Mức YẾU: hệ chạy được nhưng chưa có cách kiểm chứng độc lập.
            # KHÔNG phải `capability_gap` — nói nhầm là báo cáo sai năng lực
            # của chính mình (§5.4).
            weak.append(ob.kind)
            continue

        ctype = declared.get(ob.container)
        if ctype is None:
            missing.append(f"{ob.describe()}: container '{ob.container}' chưa khai báo")
            continue
        if not accepts_container_type(ob.kind, ctype):
            missing.append(
                f"{ob.describe()}: kiểu '{ctype}' không hợp với nghĩa vụ này"
            )
            continue

        w = ob.witness
        if not w:
            missing.append(f"{ob.describe()}: thiếu witness")
        elif w not in declared:
            missing.append(f"{ob.describe()}: witness '{w}' chưa khai báo")
        elif w not in producers:
            missing.append(f"{ob.describe()}: witness '{w}' không có producer hợp lệ")

    if missing:
        return CoverageResult(
            ok=False,
            error_code="REQUESTED_OPERATION_UNCOVERED",
            missing=missing,
            weak_kinds=sorted(set(weak)),
        )
    if weak:
        return CoverageResult(
            ok=False,
            error_code="SEMANTIC_VERIFICATION_UNAVAILABLE",
            weak_kinds=sorted(set(weak)),
        )
    return CoverageResult(ok=True)
