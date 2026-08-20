# -*- coding: utf-8 -*-
"""Kết quả phải có một AUTHORITY TẤT ĐỊNH sở hữu.

Thay khái niệm của `computation_gate.py` (giữ nguyên file cũ cho đường module).

VÌ SAO ĐỔI KHÁI NIỆM, KHÔNG PHẢI NỚI LUẬT: luật cũ viết là "algorithmic thì từ
chối", kèm lý do *"thay vì để AI tự giải rồi dựng cảnh minh hoạ đáp án"*. Lý do
đó vẫn đúng nguyên vẹn — cái sai là ĐỒNG NHẤT nó với "algorithmic". Câu đúng
luôn là: kết quả phải có authority tất định sở hữu. Khi hệ chưa có interpreter,
mọi bài algorithmic đều không có authority nên hai câu trùng nhau; nay đã có
thì phải tách, nếu không hệ sẽ từ chối đúng lớp bài nó vừa làm được.

R0 KHÔNG bị nới một milimet: LLM vẫn không bao giờ là authority.
"""
from __future__ import annotations

from app.simulation.dsl.manifest import known_gap_roles

_CO_AUTHORITY_SAN = ("provided", "rule_derivable")


def check_execution_authority(
    analysis: dict, plan: dict, has_interpreter: bool
) -> str | None:
    """Trả lý do (tiếng Việt) khi KHÔNG có authority; `None` khi được đi tiếp.

    `has_interpreter` = route hiện tại có `SemanticProgramInterpreter` đứng sau
    hay không. Đường module truyền `False` ⇒ hành vi y hệt `computation_gate` cũ.
    """
    # Vai trò không engine tất định nào sở hữu thì interpreter cũng không cứu
    # được — có interpreter KHÔNG có nghĩa là biểu diễn được mọi cơ chế.
    gaps = sorted(set(plan.get("unsupported_capabilities", [])) & known_gap_roles())
    if gaps:
        return (
            f"Bài cần cơ chế chưa có engine tất định sở hữu ({', '.join(gaps)}) — "
            "hệ từ chối trung thực thay vì dựng cảnh xấp xỉ."
        )

    ownership = analysis.get("result_ownership")

    if ownership in _CO_AUTHORITY_SAN:
        return None

    if ownership == "algorithmic":
        if has_interpreter:
            # Authority là INTERPRETER TẤT ĐỊNH, không phải LLM. LLM chỉ viết
            # chương trình; chạy nó ra kết quả là việc của engine.
            return None
        return (
            "Kết quả của bài phải được TÍNH qua cơ chế thuật toán mà không "
            "authority tất định nào của hệ sở hữu — hệ từ chối trung thực thay "
            "vì để AI tự giải rồi dựng cảnh minh hoạ đáp án."
        )

    # Thiếu hoặc ngoài enum → fail-closed, không default sang giá trị nào.
    return (
        "Phân tích không xác định được nguồn kết quả của bài (result_ownership "
        f"= {ownership!r}) — hệ từ chối an toàn thay vì đoán."
    )
