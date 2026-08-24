# -*- coding: utf-8 -*-
"""Vị từ hình học — CHÍNH XÁC, **không một epsilon nào**.

Đây là chỗ số học chính xác trả cổ tức. Mọi vị từ dưới đây quy về *"một số hữu
tỉ có bằng 0 không"*, và câu hỏi ấy trên `Fraction` có câu trả lời **đúng**,
không phải câu trả lời *"trong dung sai"*.

    thuộc      ⇔  n · (P − A) == 0
    thẳng hàng ⇔  (B−A) × (C−A) == 0
    đồng phẳng ⇔  det(B−A, C−A, D−A) == 0
    song song  ⇔  u × v == 0
    vuông góc  ⇔  u · v == 0

MỘT CHỖ QUYẾT, không rải: nếu sau này buộc phải nhận đầu vào không hữu tỉ (toạ
độ có căn), thì dung sai được đặt **ở file này và chỉ ở đây**, có tên, có lý do.
Rải `abs(x) < 1e-9` khắp kernel là cách chắc chắn nhất để hai chỗ dùng hai
ngưỡng khác nhau rồi mâu thuẫn nhau — và mâu thuẫn ấy chỉ lộ ở một bài cụ thể,
nhiều tuần sau.

RANH GIỚI: file này **chỉ trả lời đúng/sai**, không dựng gì. Dựng thuộc
`kernel.py`; đo thuộc `measure.py`. Tách ra vì vị từ là thứ `postconditions`
gọi để kiểm chứng, và nó **không được** phụ thuộc vào chỗ dựng — nếu không thì
oracle đang kiểm chính cái nó vừa dựng.
"""
from __future__ import annotations

from .exact import Line3, Plane3, Point3, Vec3, det3


# ── quan hệ điểm ──────────────────────────────────────────────────────────
def same_point(a: Point3, b: Point3) -> bool:
    return (b - a).is_zero()


def collinear(a: Point3, b: Point3, c: Point3) -> bool:
    """Ba điểm thẳng hàng. Hai điểm trùng cũng tính là thẳng hàng — đúng theo
    định nghĩa, và đó là lý do `Plane3.through` phải kiểm bằng chính vị từ này
    chứ không kiểm 'có hai điểm trùng không'."""
    return (b - a).cross(c - a).is_zero()


def coplanar(a: Point3, b: Point3, c: Point3, d: Point3) -> bool:
    return det3(b - a, c - a, d - a) == 0


# ── thuộc ─────────────────────────────────────────────────────────────────
def point_on_line(p: Point3, ln: Line3) -> bool:
    return (p - ln.point).cross(ln.direction).is_zero()


def point_on_plane(p: Point3, pl: Plane3) -> bool:
    return pl.signed_eval(p) == 0


def line_in_plane(ln: Line3, pl: Plane3) -> bool:
    """Nằm TRONG mặt phẳng — khác hẳn 'song song với mặt phẳng'.

    Gộp hai cái này là lỗi dạy học, không chỉ lỗi mã: một đường nằm trong mặt
    phẳng thì giao là **vô số điểm**; một đường song song thì giao là **rỗng**.
    Học sinh cần thấy hai kết luận khác nhau.
    """
    return ln.direction.dot(pl.normal) == 0 and point_on_plane(ln.point, pl)


# ── song song ─────────────────────────────────────────────────────────────
def parallel_vectors(u: Vec3, v: Vec3) -> bool:
    return u.cross(v).is_zero()


def parallel_lines(a: Line3, b: Line3) -> bool:
    """Cùng phương. **Bao gồm cả trùng nhau** — xem `skew_lines` để phân biệt."""
    return parallel_vectors(a.direction, b.direction)


def parallel_line_plane(ln: Line3, pl: Plane3) -> bool:
    """Song song THẬT SỰ: cùng phương với mặt phẳng VÀ không nằm trong nó."""
    return ln.direction.dot(pl.normal) == 0 and not point_on_plane(ln.point, pl)


def parallel_planes(p: Plane3, q: Plane3) -> bool:
    return parallel_vectors(p.normal, q.normal)


def skew_lines(a: Line3, b: Line3) -> bool:
    """Hai đường CHÉO NHAU — không cắt, không song song.

    Đây là quan hệ mà **hình biểu diễn phẳng nói dối** rõ nhất: trên giấy hai
    đường chéo nhau trông y hệt hai đường cắt nhau. Nó cũng chính là lý do
    3D ở đề tài này không phải trang trí.
    """
    if parallel_lines(a, b):
        return False
    return not coplanar(a.point, a.at(1), b.point, b.at(1))


# ── vuông góc ─────────────────────────────────────────────────────────────
def perpendicular_vectors(u: Vec3, v: Vec3) -> bool:
    return u.dot(v) == 0


def perpendicular_lines(a: Line3, b: Line3) -> bool:
    """Vuông góc theo PHƯƠNG — hai đường chéo nhau vẫn có thể vuông góc.

    Đúng định nghĩa SGK ('góc giữa hai đường thẳng' tính trên phương), và cố ý
    KHÔNG đòi chúng cắt nhau.
    """
    return perpendicular_vectors(a.direction, b.direction)


def line_perpendicular_plane(ln: Line3, pl: Plane3) -> bool:
    """`d ⊥ (P)` ⇔ phương của `d` **cùng phương** với pháp tuyến của `(P)`.

    Đây là chỗ dễ viết ngược nhất trong cả file: trực giác nói "vuông góc thì
    phải `dot == 0`", nhưng với đường-và-mặt thì ngược lại — vuông góc với mặt
    nghĩa là **song song với pháp tuyến**.
    """
    return parallel_vectors(ln.direction, pl.normal)


def perpendicular_planes(p: Plane3, q: Plane3) -> bool:
    return perpendicular_vectors(p.normal, q.normal)
