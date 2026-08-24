# -*- coding: utf-8 -*-
"""Đại lượng — nơi DUY NHẤT vô tỉ được phép xuất hiện, và bị nhốt kỹ.

Khoảng cách và góc là hai chỗ ℚ không đóng: `√2` và `arccos` đi ra khỏi hữu tỉ.
Nên luật ở file này:

    tính và SO SÁNH  →  trên BÌNH PHƯƠNG, chính xác trong ℚ
    hiển thị         →  `float`, ở đúng biên, có tên hàm nói rõ

`d² ` và `cos²θ` đều **hữu tỉ**, nên mọi câu hỏi mà bài toán thật sự hỏi vẫn trả
lời được chính xác:

    "khoảng cách này có bằng khoảng cách kia không"  →  so `d²`
    "góc này có bằng 60° không"                      →  so `cos²θ` với `1/4`
    "có vuông góc không"                             →  `u · v == 0`

Chỉ khi in ra cho học sinh mới lấy căn. **Không được** lấy căn rồi so sánh —
đó là đường đưa sai số float quay lại qua cửa sau.

THỂ TÍCH thì hữu tỉ hoàn toàn: khối đa diện có đỉnh hữu tỉ luôn có thể tích
hữu tỉ. Nên `volume_*` trả `Fraction`, không trả `float`.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Sequence

from .exact import GeometryError, Line3, Plane3, Point3, Vec3, det3
from .kernel import project_point_onto_line, project_point_onto_plane
from .predicates import parallel_lines, skew_lines

#: Mã lỗi riêng của tầng đo.
ERR_KHONG_DO_DUOC = "MEASURE_UNDEFINED"


# ── khoảng cách: luôn trả BÌNH PHƯƠNG ─────────────────────────────────────
def distance_sq(a: Point3, b: Point3) -> Fraction:
    return (b - a).norm_sq()


def distance_sq_point_plane(p: Point3, pl: Plane3) -> Fraction:
    """`d² = (n·(p−P))² / |n|²` — hữu tỉ, chính xác."""
    s = pl.signed_eval(p)
    return s * s / pl.normal.norm_sq()


def distance_sq_point_line(p: Point3, ln: Line3) -> Fraction:
    h = project_point_onto_line(p, ln)
    return distance_sq(p, h)


def distance_sq_parallel_lines(a: Line3, b: Line3) -> Fraction:
    if not parallel_lines(a, b):
        raise GeometryError(
            ERR_KHONG_DO_DUOC,
            "hai đường KHÔNG song song — 'khoảng cách giữa hai đường thẳng' "
            "chỉ định nghĩa khi song song hoặc chéo nhau",
        )
    return distance_sq_point_line(b.point, a)


def distance_sq_skew_lines(a: Line3, b: Line3) -> Fraction:
    """Khoảng cách hai đường CHÉO NHAU — `|(w · (u×v))|² / |u×v|²`.

    Đây là công thức học sinh khó hình dung nhất, và cũng là chỗ mô phỏng 3D có
    giá trị nhất: đoạn vuông góc chung không nằm trên mặt giấy.
    """
    if not skew_lines(a, b):
        raise GeometryError(
            ERR_KHONG_DO_DUOC, "hai đường KHÔNG chéo nhau — dùng hàm tương ứng"
        )
    n = a.direction.cross(b.direction)
    s = (b.point - a.point).dot(n)
    return s * s / n.norm_sq()


def length(d_sq: Fraction) -> float:
    """BIÊN HIỂN THỊ. Chỉ gọi khi ĐÓNG GÓI cho renderer — không dùng để so sánh.

    Tách thành hàm có tên thay vì rải `math.sqrt` khắp nơi, để `grep length(`
    chỉ ra đúng mọi chỗ vô tỉ đi vào hệ.
    """
    return math.sqrt(float(d_sq))


# ── góc: so trên cos², chính xác ──────────────────────────────────────────
def cos_sq_between_vectors(u: Vec3, v: Vec3) -> Fraction:
    """`cos²θ = (u·v)² / (|u|²|v|²)` — hữu tỉ, chính xác.

    Dùng bình phương vì góc giữa hai ĐƯỜNG THẲNG không phân biệt chiều: `θ` và
    `180°−θ` là cùng một góc theo định nghĩa SGK.
    """
    if u.is_zero() or v.is_zero():
        raise GeometryError(ERR_KHONG_DO_DUOC, "không có góc với vector không")
    d = u.dot(v)
    return d * d / (u.norm_sq() * v.norm_sq())


def cos_sq_between_lines(a: Line3, b: Line3) -> Fraction:
    return cos_sq_between_vectors(a.direction, b.direction)


def sin_sq_line_plane(ln: Line3, pl: Plane3) -> Fraction:
    """Góc giữa đường và mặt: `sin θ` với pháp tuyến, không phải `cos`.

    Chỗ lộn dấu kinh điển — góc với mặt phẳng là **phần bù** của góc với pháp
    tuyến, nên trả `sin²` để tên hàm nói đúng thứ nó trả.
    """
    return cos_sq_between_vectors(ln.direction, pl.normal)


def cos_sq_between_planes(p: Plane3, q: Plane3) -> Fraction:
    return cos_sq_between_vectors(p.normal, q.normal)


def degrees(cos_sq: Fraction) -> float:
    """BIÊN HIỂN THỊ. Trả góc trong `[0°, 90°]` — đúng quy ước góc giữa hai
    đường thẳng / hai mặt phẳng của SGK."""
    c = math.sqrt(min(1.0, max(0.0, float(cos_sq))))
    return math.degrees(math.acos(c))


# ── thể tích: hữu tỉ hoàn toàn ────────────────────────────────────────────
def volume_tetrahedron(a: Point3, b: Point3, c: Point3, d: Point3) -> Fraction:
    """`V = |det(b−a, c−a, d−a)| / 6` — CHÍNH XÁC, không sai số.

    Trả `Fraction`: thể tích của khối có đỉnh hữu tỉ luôn hữu tỉ. Trả `float`
    ở đây là vứt tính chính xác đi mà không được gì.
    """
    v = det3(b - a, c - a, d - a)
    return abs(v) / 6


def volume_pyramid_fan(apex: Point3, base: Sequence[Point3]) -> Fraction:
    """Thể tích chóp có đáy là đa giác PHẲNG LỒI, chia quạt từ đỉnh đáy đầu.

    Đòi đáy phẳng và **kiểm**, không giả định: đáy không phẳng thì phép chia
    quạt cho một con số trông hợp lý nhưng vô nghĩa — đúng loại sai lặng lẽ mà
    cả kernel này sinh ra để chặn.
    """
    if len(base) < 3:
        raise GeometryError(ERR_KHONG_DO_DUOC, "đáy cần ít nhất 3 đỉnh")
    a0, a1, a2 = base[0], base[1], base[2]
    n = (a1 - a0).cross(a2 - a0)
    if n.is_zero():
        raise GeometryError(ERR_KHONG_DO_DUOC, "ba đỉnh đầu của đáy THẲNG HÀNG")
    for i, p in enumerate(base[3:], start=3):
        if n.dot(p - a0) != 0:
            raise GeometryError(
                ERR_KHONG_DO_DUOC,
                f"đỉnh đáy thứ {i} KHÔNG đồng phẳng với ba đỉnh đầu — "
                "đây không phải một đa giác phẳng",
            )
    tong = Fraction(0)
    for i in range(1, len(base) - 1):
        tong += volume_tetrahedron(apex, base[0], base[i], base[i + 1])
    return tong
