# -*- coding: utf-8 -*-
"""ORACLE HÌNH HỌC ĐỘC LẬP — Python thuần, **không import một dòng mã sản phẩm**.

ĐỘC LẬP LÀ TÍNH CHẤT KIỂM ĐƯỢC BẰNG MẮT, không phải một lời hứa: file này chỉ
`import fractions`. Không `app.simulation.geometry`, không `Vec3`, không
`Plane3`. Đầu vào là **tuple số thuần** — dạng dây, để không có đường nào cho
hai bên vô tình dùng chung một kiểu rồi dùng chung luôn một lỗi.

    Cùng khuôn `sealed_ground_truth.py` của miền Tin học, và cùng lý do.

HAI CHIẾN LƯỢC, chọn theo bản chất câu hỏi:

1. **Kiểm BẤT BIẾN** (thiết diện). Oracle **không dựng lại** thiết diện. Nó hỏi
   những câu mà một thiết diện đúng phải trả lời "có", và một thiết diện sai
   gần như chắc chắn trả lời "không":
       mọi đỉnh thuộc mặt phẳng cắt · mọi đỉnh nằm trên BIÊN khối ·
       đa giác KÍN · hai đỉnh liên tiếp cùng thuộc MỘT mặt ·
       mặt phẳng thật sự CHIA khối làm hai phía
   Kiểm bằng tính chất **độc lập hơn** kiểm bằng dựng lại: hai bản cài cùng một
   thuật toán dễ mang cùng một lỗi và triệt tiêu nhau, còn một bất biến thì
   không quan tâm anh dựng kiểu gì.

2. **Phân rã KHÁC** (thể tích). Kernel chia quạt từ **đỉnh chóp**; oracle chia
   tứ diện từ **một điểm trong** tới từng tam giác của **mọi mặt**. Hai phép
   phân rã khác nhau cho cùng một số ⇒ trùng khớp là bằng chứng, không phải
   tautology.

CHỈ NHẬN SỐ HỮU TỈ. `float` không được vào đây — oracle mà có sai số thì nó
không còn là oracle.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Iterable, Sequence

Vec = tuple[Fraction, Fraction, Fraction]
#: Mặt phẳng dạng dây: `(điểm, pháp tuyến)`.
Mp = tuple[Vec, Vec]


# ── số học tối thiểu, viết lại CÓ CHỦ ĐÍCH ────────────────────────────────
def V(x, y, z) -> Vec:
    return (Fraction(x), Fraction(y), Fraction(z))


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def dot(a: Vec, b: Vec) -> Fraction:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def is_zero(a: Vec) -> bool:
    return a == (0, 0, 0)


def eval_plane(pl: Mp, p: Vec) -> Fraction:
    return dot(pl[1], sub(p, pl[0]))


# ── 1. thiết diện — kiểm BẤT BIẾN, không dựng lại ─────────────────────────
def _diem_thuoc_mat(p: Vec, mat: Sequence[Vec]) -> bool:
    """`p` có nằm TRONG đa giác lồi phẳng `mat` không (kể cả trên biên).

    Kiểm bằng dấu tích có hướng quanh chu vi — cùng dấu (hoặc 0) với mọi cạnh
    thì nằm trong. Không dùng góc, không dùng căn.
    """
    n = cross(sub(mat[1], mat[0]), sub(mat[2], mat[0]))
    if is_zero(n):
        return False
    if dot(n, sub(p, mat[0])) != 0:
        return False           # không đồng phẳng với mặt
    duong = am = False
    for i in range(len(mat)):
        a, b = mat[i], mat[(i + 1) % len(mat)]
        s = dot(n, cross(sub(b, a), sub(p, a)))
        if s > 0:
            duong = True
        elif s < 0:
            am = True
    return not (duong and am)


def verify_section(
    vertices: Sequence[Vec],
    faces: Sequence[Sequence[int]],
    plane: Mp,
    claimed: Sequence[Vec],
) -> list[str]:
    """Thiết diện được khai có đúng không. Trả **danh sách vi phạm**; rỗng = đạt.

    Trả danh sách chứ không trả `bool`: khi sai, thứ người sửa cần là *sai ở
    bất biến nào*, không phải một chữ `False`.
    """
    loi: list[str] = []
    mat_dinh = [[vertices[i] for i in f] for f in faces]

    if len(claimed) < 3:
        loi.append(f"thiết diện chỉ có {len(claimed)} đỉnh, cần ≥3")
        return loi

    # (a) mọi đỉnh thuộc mặt phẳng cắt
    for i, p in enumerate(claimed):
        if eval_plane(plane, p) != 0:
            loi.append(f"đỉnh {i} KHÔNG thuộc mặt phẳng cắt")

    # (b) mọi đỉnh nằm trên BIÊN khối
    for i, p in enumerate(claimed):
        if not any(_diem_thuoc_mat(p, m) for m in mat_dinh):
            loi.append(f"đỉnh {i} không nằm trên mặt nào của khối")

    # (c) hai đỉnh liên tiếp cùng thuộc MỘT mặt — điều kiện để cạnh thiết diện
    #     thật sự là giao với một mặt, chứ không phải một dây cung xuyên khối
    n = len(claimed)
    for i in range(n):
        a, b = claimed[i], claimed[(i + 1) % n]
        if not any(_diem_thuoc_mat(a, m) and _diem_thuoc_mat(b, m) for m in mat_dinh):
            loi.append(f"cạnh {i}→{(i+1)%n} không nằm trên mặt nào — xuyên qua khối")

    # (d) đa giác PHẲNG và không suy biến
    n0 = cross(sub(claimed[1], claimed[0]), sub(claimed[2], claimed[0]))
    if is_zero(n0):
        loi.append("ba đỉnh đầu thẳng hàng — đa giác suy biến")

    # (e) mặt phẳng thật sự CHIA khối: có đỉnh ở cả hai phía
    dau = {eval_plane(plane, v) > 0 for v in vertices
           if eval_plane(plane, v) != 0}
    if len(dau) < 2:
        loi.append("mặt phẳng không chia khối làm hai phía — không có thiết diện")

    # (f) không trùng đỉnh
    if len(set(claimed)) != n:
        loi.append("thiết diện có đỉnh TRÙNG nhau")
    return loi


# ── 2. thể tích — phân rã KHÁC hẳn kernel ─────────────────────────────────
def volume_from_interior_point(
    vertices: Sequence[Vec], faces: Sequence[Sequence[int]]
) -> Fraction:
    """Thể tích khối lồi: chia tứ diện từ **một điểm trong** tới mọi tam giác
    của **mọi mặt**, cộng `|det|/6`.

    Điểm trong lấy là trung bình các đỉnh — với khối lồi thì luôn nằm trong.
    Dùng `abs` nên **không phụ thuộc hướng khai mặt**; kernel thì chia quạt từ
    đỉnh chóp. Hai đường đi khác nhau, cùng một số.
    """
    k = Fraction(len(vertices))
    tam: Vec = (sum(v[0] for v in vertices) / k,
                sum(v[1] for v in vertices) / k,
                sum(v[2] for v in vertices) / k)
    tong = Fraction(0)
    for f in faces:
        a = vertices[f[0]]
        for i in range(1, len(f) - 1):
            b, c = vertices[f[i]], vertices[f[i + 1]]
            d = dot(sub(a, tam), cross(sub(b, tam), sub(c, tam)))
            tong += abs(d)
    return tong / 6


# ── 3. đại lượng — công thức đóng, không gọi phép dựng nào ────────────────
def distance_sq_point_plane(p: Vec, pl: Mp) -> Fraction:
    s = eval_plane(pl, p)
    return s * s / dot(pl[1], pl[1])


def distance_sq_points(a: Vec, b: Vec) -> Fraction:
    d = sub(b, a)
    return dot(d, d)


def cos_sq(u: Vec, v: Vec) -> Fraction:
    d = dot(u, v)
    return d * d / (dot(u, u) * dot(v, v))


def perpendicular(u: Vec, v: Vec) -> bool:
    return dot(u, v) == 0


def parallel(u: Vec, v: Vec) -> bool:
    return is_zero(cross(u, v))


def coplanar(a: Vec, b: Vec, c: Vec, d: Vec) -> bool:
    return dot(sub(b, a), cross(sub(c, a), sub(d, a))) == 0


def plane_through(a: Vec, b: Vec, c: Vec) -> Mp:
    n = cross(sub(b, a), sub(c, a))
    if is_zero(n):
        raise ValueError("ba điểm thẳng hàng — không xác định mặt phẳng")
    return (a, n)
