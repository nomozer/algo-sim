# -*- coding: utf-8 -*-
"""Tám checker nghĩa vụ hình học — tầng C₂ của miền không gian. **0 API call.**

VÌ SAO MIỀN NÀY CÓ ĐỦ CHECKER CHO MỌI NGHĨA VỤ, trong khi miền Tin học phải để
`predicate_verdict` ở mức yếu suốt nhiều tháng: ở đó, kiểm *"dãy này có được
sắp đúng không"* đòi **cài lại chính thuật toán đang kiểm**, nên oracle mất tính
độc lập. Ở hình học, câu trả lời là **giải tích**: `u · v == 0` là một phép
tính, không phải một cách giải bài. Kiểm không dùng lại lời giải.

RANH GIỚI VỚI KERNEL: file này **gọi vị từ**, không cài lại toán. Cài lại là đẻ
ra tầng hình học thứ hai, và hai tầng chắc chắn sẽ lệch nhau ở một ca nào đó —
lệch im lặng, vì cả hai đều "chạy".

RANH GIỚI VỚI ORACLE: đây **không** phải oracle. Đây là cổng **nội bộ** (C₂):
nó hỏi *"chương trình có tự mâu thuẫn với nghĩa vụ nó tự khai không"*. Oracle
độc lập (`docs/evaluation/geometry/custodian/geometry_oracle.py`) hỏi câu khác:
*"kết quả có khớp ground truth do người ngoài dựng không"*. Hai câu, hai tầng —
gộp lại là mất tính độc lập.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from ..geometry import Line3, Plane3, Vec3
from ..geometry import measure as M
from ..geometry import predicates as P
from ..geometry.section import Polyhedron, Section

#: Sai lệch giữa giá trị máy tính ra và giá trị đề mong đợi.
_LECH = "giá trị không khớp"


def _lay(snapshot: dict[str, Any], ten: str | None) -> Any:
    return snapshot.get(ten) if ten else None


def _so(raw: Any) -> Fraction | None:
    """Giá trị mong đợi trong nghĩa vụ → `Fraction`. Không parse được ⇒ `None`
    (mức yếu), KHÔNG phải 0 — nhầm hai cái là biến 'không biết' thành 'bằng 0'."""
    try:
        if raw is None:
            return None
        return Fraction(str(raw))
    except (ValueError, ZeroDivisionError):
        return None


# ── nhóm QUAN HỆ: trả lời đúng/sai ────────────────────────────────────────
def check_point_on_line(snapshot: dict, ob) -> str | None:
    ln, p = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if not isinstance(ln, Line3) or not isinstance(p, Vec3):
        return "cần một `line3` và một `point3`"
    return None if P.point_on_line(p, ln) else "điểm KHÔNG thuộc đường thẳng"


def check_point_on_plane(snapshot: dict, ob) -> str | None:
    pl, p = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if not isinstance(pl, Plane3) or not isinstance(p, Vec3):
        return "cần một `plane3` và một `point3`"
    return None if P.point_on_plane(p, pl) else "điểm KHÔNG thuộc mặt phẳng"


def check_parallel(snapshot: dict, ob) -> str | None:
    a, b = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if isinstance(a, Line3) and isinstance(b, Line3):
        return None if P.parallel_lines(a, b) else "hai đường KHÔNG song song"
    if isinstance(a, Plane3) and isinstance(b, Plane3):
        return None if P.parallel_planes(a, b) else "hai mặt KHÔNG song song"
    # Đường ∥ mặt là quan hệ THẬT SỰ khác: nó đòi đường KHÔNG nằm trong mặt.
    if isinstance(a, Line3) and isinstance(b, Plane3):
        return None if P.parallel_line_plane(a, b) else \
            "đường KHÔNG song song mặt phẳng (hoặc nằm TRONG nó)"
    if isinstance(a, Plane3) and isinstance(b, Line3):
        return None if P.parallel_line_plane(b, a) else \
            "đường KHÔNG song song mặt phẳng (hoặc nằm TRONG nó)"
    return "cặp đối tượng không hợp lệ cho quan hệ song song"


def check_perpendicular(snapshot: dict, ob) -> str | None:
    a, b = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if isinstance(a, Line3) and isinstance(b, Line3):
        return None if P.perpendicular_lines(a, b) else "hai đường KHÔNG vuông góc"
    if isinstance(a, Plane3) and isinstance(b, Plane3):
        return None if P.perpendicular_planes(a, b) else "hai mặt KHÔNG vuông góc"
    # ⚠️ Đường ⊥ mặt ⇔ phương đường CÙNG PHƯƠNG pháp tuyến — không phải `dot==0`.
    # Chỗ lộn dấu kinh điển; kernel đã viết đúng, ở đây chỉ gọi.
    if isinstance(a, Line3) and isinstance(b, Plane3):
        return None if P.line_perpendicular_plane(a, b) else \
            "đường KHÔNG vuông góc mặt phẳng"
    if isinstance(a, Plane3) and isinstance(b, Line3):
        return None if P.line_perpendicular_plane(b, a) else \
            "đường KHÔNG vuông góc mặt phẳng"
    return "cặp đối tượng không hợp lệ cho quan hệ vuông góc"


def check_coplanar(snapshot: dict, ob) -> str | None:
    c = _lay(snapshot, ob.container)
    diem = list(c) if isinstance(c, (list, tuple)) else \
        (list(c.polygon) if isinstance(c, Section) else None)
    if diem is None and isinstance(c, Polyhedron):
        return "một KHỐI thì hiển nhiên không đồng phẳng — nghĩa vụ gắn sai chủ thể"
    if not diem or len(diem) < 4:
        return "cần ít nhất 4 điểm để hỏi về đồng phẳng"
    a = diem[0]
    return None if all(P.coplanar(a, diem[1], diem[2], p) for p in diem[3:]) \
        else "các điểm KHÔNG đồng phẳng"


# ── nhóm ĐẠI LƯỢNG: trả lời một số ────────────────────────────────────────
#
# So sánh làm trên BÌNH PHƯƠNG với `distance`, và trên `cos²` với `angle` —
# hai đại lượng ấy vô tỉ, còn bình phương của chúng thì hữu tỉ. Lấy căn rồi so
# là đưa sai số float quay lại qua cửa sau.
def check_distance(snapshot: dict, ob) -> str | None:
    a, b = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    mong = _so(ob.params.get("value"))
    if mong is None:
        return None  # không khai giá trị ⇒ chỉ kiểm được cấu trúc, mức yếu
    try:
        if isinstance(a, Plane3) and isinstance(b, Vec3):
            d2 = M.distance_sq_point_plane(b, a)
        elif isinstance(a, Line3) and isinstance(b, Vec3):
            d2 = M.distance_sq_point_line(b, a)
        elif isinstance(a, Vec3) and isinstance(b, Vec3):
            d2 = M.distance_sq(a, b)
        else:
            return "cặp đối tượng không hợp lệ cho khoảng cách"
    except Exception as e:  # noqa: BLE001 — lỗi hình học là kết luận, không phải sự cố
        return f"không đo được khoảng cách: {e}"
    return None if d2 == mong * mong else f"{_LECH}: d² = {d2}, đề mong {mong}²"


def check_angle(snapshot: dict, ob) -> str | None:
    a, b = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    mong = _so(ob.params.get("cos_sq"))
    if mong is None:
        return None
    try:
        if isinstance(a, Line3) and isinstance(b, Line3):
            c2 = M.cos_sq_between_lines(a, b)
        elif isinstance(a, Plane3) and isinstance(b, Plane3):
            c2 = M.cos_sq_between_planes(a, b)
        elif isinstance(a, Line3) and isinstance(b, Plane3):
            c2 = M.sin_sq_line_plane(a, b)
        else:
            return "cặp đối tượng không hợp lệ cho góc"
    except Exception as e:  # noqa: BLE001
        return f"không đo được góc: {e}"
    return None if c2 == mong else f"{_LECH}: cos² = {c2}, đề mong {mong}"


def check_volume(snapshot: dict, ob) -> str | None:
    sol = _lay(snapshot, ob.container)
    if not isinstance(sol, Polyhedron):
        return "cần một `solid`"
    mong = _so(ob.params.get("value"))
    if mong is None:
        return None
    # Phân rã từ đỉnh đầu tiên qua mọi mặt — tất định, và `abs` nên không phụ
    # thuộc hướng khai mặt.
    tong = Fraction(0)
    tam = sol.vertices[0]
    for f in sol.faces:
        for i in range(1, len(f) - 1):
            tong += M.volume_tetrahedron(
                tam, sol.vertices[f[0]], sol.vertices[f[i]], sol.vertices[f[i + 1]]
            )
    return None if tong == mong else f"{_LECH}: V = {tong}, đề mong {mong}"


GEOMETRY_CHECKERS = {
    "point_on_line": check_point_on_line,
    "point_on_plane": check_point_on_plane,
    "parallel": check_parallel,
    "perpendicular": check_perpendicular,
    "coplanar": check_coplanar,
    "distance": check_distance,
    "angle": check_angle,
    "volume": check_volume,
}
