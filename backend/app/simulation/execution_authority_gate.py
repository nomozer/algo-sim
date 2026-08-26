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


#: Vai trò mà **NHÂN HÌNH HỌC** sở hữu, dù manifest DSL 2D xếp chúng là gap.
#:
#: ─── VÌ SAO DANH SÁCH NÀY TỒN TẠI (đo được ở Phase 7A, `5-goc` lượt 2) ────
#:
#: `known_gap_roles()` dẫn xuất từ `manifest.py`: *"vai trò trong taxonomy mà
#: KHÔNG PRIMITIVE THỊ GIÁC nào cover"*. Đó là một câu đúng **về DSL 2D**.
#:
#: Đường sinh hình học KHÔNG ĐI QUA DSL — nó chạy trên kernel hữu tỉ. Nên áp
#: danh sách ấy cho nó là áp giới hạn của một engine lên một engine khác. Hậu
#: quả đo được: một đề *"tính góc giữa SB và SD"* bị từ chối TRƯỚC KHI SINH vì
#: `analyze` khai `geometric_perpendicular`, trong khi kernel có
#: `P.perpendicular_lines` từ Wave 1.
#:
#: Nó KHÔNG tất định — cùng đề, hai lượt qua, một lượt trượt, tuỳ `analyze` có
#: khai vai trò ấy không. Nên nó vào báo cáo như "mô hình không làm được".
#:
#: ─── VÌ SAO CHỈ BA, KHÔNG MIỄN TRỪ CẢ MIỀN ───────────────────────────────
#:
#: Kernel **KHÔNG** sở hữu `geometric_circle` và `geometric_locus`: nó dựng trên
#: `Fraction` và đa diện, mặt cong không nằm trong mô hình
#: (`GEOMETRY_CURRICULUM_COVERAGE §4`, mục #19 và #20 đều ghi KHÔNG).
#:
#: Miễn trừ cả gói thì một đề mặt cầu đi thẳng vào sinh, tiêu ~5 lượt LLM rồi
#: hỏng muộn — hoặc tệ hơn, dựng một khối đa diện "gần giống" và học sinh tin
#: nó. Từ chối sớm ở đây mới là hành vi trung thực.
#:
#: Mỗi mục dưới đây có test khẳng định kernel THẬT SỰ có hàm tương ứng.
GEOMETRY_OWNED_GAP_ROLES = frozenset({
    "geometric_perpendicular",   # predicates.perpendicular_lines / _planes
    "geometric_intersection",    # kernel.intersect_line_plane / _plane_plane / _line_line
    "geometric_projection",      # kernel.project_point_onto_plane / _line
})


def check_execution_authority(
    analysis: dict, plan: dict, has_interpreter: bool, domain: str | None = None
) -> str | None:
    """Trả lý do (tiếng Việt) khi KHÔNG có authority; `None` khi được đi tiếp.

    `has_interpreter` = route hiện tại có `SemanticProgramInterpreter` đứng sau
    hay không. Đường module truyền `False` ⇒ hành vi y hệt `computation_gate` cũ.

    `domain` = miền đã dò TẤT ĐỊNH. `None` (mặc định) giữ nguyên hành vi cũ cho
    miền Tin học — cơ chế chặn của nó KHÔNG được nới một milimét.
    """
    # Vai trò không engine tất định nào sở hữu thì interpreter cũng không cứu
    # được — có interpreter KHÔNG có nghĩa là biểu diễn được mọi cơ chế.
    lo_hong = known_gap_roles()
    if domain == "hinh_hoc":
        # Trừ đi ĐÚNG những vai trò nhân hình học sở hữu. `geometric_circle` và
        # `geometric_locus` KHÔNG được trừ — kernel thật sự không có chúng.
        lo_hong = lo_hong - GEOMETRY_OWNED_GAP_ROLES
    gaps = sorted(set(plan.get("unsupported_capabilities", [])) & lo_hong)
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
