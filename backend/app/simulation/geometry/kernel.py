# -*- coding: utf-8 -*-
"""Phép DỰNG hình tất định — chỗ ranh giới R0 sống hay chết.

LUẬT TRUNG TÂM CỦA CẢ ĐỀ TÀI, viết ra đây vì đây là nơi nó bị vi phạm dễ nhất:

> LLM được phép nói *"lấy giao tuyến của (SAB) và (SCD)"*.
> LLM **KHÔNG** được phép nói *"giao tuyến là đường MN"*.

Nếu toạ độ giao điểm đến từ LLM thì LLM sở hữu kết quả, và mọi thứ còn lại của
luận văn — kiểm chứng độc lập, từ chối trung thực, engine tất định — đều rỗng.
Mọi hàm ở file này **tự tính**, chỉ nhận **tên đối tượng và toạ độ ĐỀ CHO**.

FAIL-CLOSED, cùng luật đã áp cho `SemanticExecutionError`: phép dựng không xác
định thì **NÉM**, kèm mã lỗi phân biệt được hai tình huống dạy hai điều khác
nhau — *song song nên không có giao* ≠ *nằm trong nên giao là vô số điểm*.
Trả `None` ở đây là để một mặt phẳng suy biến trôi tiếp tới renderer.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable

from .exact import (
    ERR_CHUA_TRONG,
    ERR_SONG_SONG,
    ERR_VECTO_KHONG,
    GeometryError,
    Line3,
    Plane3,
    Point3,
    Vec3,
)
from . import metric as _m
from .predicates import line_in_plane, parallel_planes, point_on_line


def midpoint(a: Point3, b: Point3) -> Point3:
    return (a + b).scale(Fraction(1, 2))


def translate(p: Point3, v: Vec3) -> Point3:
    """Tịnh tiến điểm `p` theo vectơ `v`: `Q = P + v`, chính xác trong ℚ³.

    ─── VÌ SAO PHÉP NÀY TỒN TẠI (2026-09-01) ──────────────────────────────

    `SYNTHESIS_STABILITY_K3` đo được: 9/9 lượt hỏng đều dừng ở schema, và **10
    lần cùng một hình dạng** — mô hình viết `construct_point X = arith(+,
    var(P), vector_from_points(A,B))`, tức nó đang cố nói *"tịnh tiến P theo
    AB"*.

    `audit_translation_gap.py` chứng minh từ VĂN PHẠM rằng câu ấy không diễn
    đạt được: **không phép sinh điểm nào nhận vectơ**, và không câu lệnh nào
    dựng được đường/mặt từ một điểm + một phương — nên cả đường vòng *"dựng
    đường qua P phương v rồi chia đoạn"* cũng đóng, vì `construct_line` cần
    hai TÊN ĐIỂM, tức cần sẵn chính điểm ta muốn dựng.

    Trước phép này, `vector3` là một kiểu **chỉ-ghi**: dựng được bằng
    `vector_from_points` nhưng không phép dựng nào tiêu thụ nó, chỉ `angle_cos`
    đo nó.

    ─── PHÉP TỔNG QUÁT, KHÔNG PHẢI MODULE THEO DẠNG BÀI ───────────────────

    Nó là phép affine cơ bản `ĐIỂM + VECTƠ → ĐIỂM`. Hoàn thành hình bình hành
    và dựng đỉnh lăng trụ/hộp chỉ là hai HỆ QUẢ, không phải định nghĩa — nên ở
    đây không có chữ nào nhắc tới chúng, và prompt cũng vậy.

    Không định nghĩa `ĐIỂM + ĐIỂM` hay `VECTƠ + ĐIỂM`: `Vec3` gộp hai vai ở
    tầng biểu diễn, nhưng phân biệt affine ấy là THẬT và được giữ ở tầng KHAI
    (`point3` vs `vector3`), nơi validator đọc được.
    """
    return p + v


def divide_segment(a: Point3, b: Point3, t: Fraction | int | str) -> Point3:
    """Điểm chia `AB` theo tỉ lệ `t`: `t=0 → A`, `t=1 → B`.

    Dùng cho *"M thuộc AB sao cho AM = 2MB"* (⇒ `t = 2/3`) — dạng đề rất phổ
    biến, và cũng là **miền hợp lệ của thao tác kéo** ở tầng tương tác: kéo M
    nghĩa là đổi `t`, không phải đổi toạ độ tự do.
    """
    return a + (b - a).scale(t)


def intersect_line_plane(ln: Line3, pl: Plane3) -> Point3:
    """Giao điểm đường thẳng × mặt phẳng.

    Ba trường hợp, và **cả ba đều phải nói khác nhau** — gộp lại là bỏ mất một
    kết luận toán học mà học sinh cần thấy:
      - cắt tại đúng một điểm  → trả điểm
      - song song              → `PARALLEL_NO_INTERSECTION`
      - nằm trong mặt phẳng    → `CONTAINED_INFINITE_INTERSECTION`
    """
    mau = ln.direction.dot(pl.normal)
    if mau == 0:
        if line_in_plane(ln, pl):
            raise GeometryError(
                ERR_CHUA_TRONG,
                "đường thẳng NẰM TRONG mặt phẳng — giao là vô số điểm, "
                "không phải một giao điểm",
            )
        raise GeometryError(
            ERR_SONG_SONG,
            "đường thẳng SONG SONG với mặt phẳng — không có giao điểm",
        )
    t = pl.normal.dot(pl.point - ln.point) / mau
    return ln.at(t)


def intersect_plane_plane(p: Plane3, q: Plane3) -> Line3:
    """Giao tuyến hai mặt phẳng — phép dựng CỐT LÕI của bài thiết diện.

    Phương giao tuyến là `n_p × n_q`. Còn **một điểm** trên giao tuyến thì tìm
    bằng cách cắt `q` bằng một đường nằm trong `p` và không song song `q` —
    dựng thẳng thay vì giải hệ, để mọi thứ ở lại trong ℚ và không cần chọn trục.
    """
    d = p.normal.cross(q.normal)
    if d.is_zero():
        if parallel_planes(p, q) and q.signed_eval(p.point) == 0:
            raise GeometryError(
                ERR_CHUA_TRONG, "hai mặt phẳng TRÙNG NHAU — giao là cả mặt phẳng"
            )
        raise GeometryError(
            ERR_SONG_SONG, "hai mặt phẳng SONG SONG — không có giao tuyến"
        )
    # Đường qua `p.point`, nằm trong `p`, cắt `q`: lấy phương `n_p × d`.
    phuong = p.normal.cross(d)
    if phuong.is_zero():  # không xảy ra khi `d != 0`, nhưng fail-closed vẫn kiểm
        raise GeometryError(ERR_VECTO_KHONG, "không dựng được đường phụ trong (P)")
    diem = intersect_line_plane(Line3(p.point, phuong), q)
    return Line3(diem, d)


def intersect_line_line(a: Line3, b: Line3) -> Point3:
    """Giao điểm hai đường thẳng — NÉM khi chéo nhau hoặc song song.

    Hai đường chéo nhau *trông như* cắt nhau trên hình biểu diễn phẳng. Trả về
    một điểm "gần đúng" ở đây chính là dạy sai — nên nó phải nổ.
    """
    u, v = a.direction, b.direction
    w = b.point - a.point
    uv = u.cross(v)
    if uv.is_zero():
        if point_on_line(b.point, a):
            raise GeometryError(ERR_CHUA_TRONG, "hai đường thẳng TRÙNG NHAU")
        raise GeometryError(ERR_SONG_SONG, "hai đường thẳng SONG SONG")
    if w.dot(uv) != 0:
        raise GeometryError(
            ERR_SONG_SONG,
            "hai đường thẳng CHÉO NHAU — không đồng phẳng nên không cắt nhau. "
            "Trên hình biểu diễn phẳng chúng trông như cắt nhau.",
        )
    t = w.cross(v).dot(uv) / uv.norm_sq()
    return a.at(t)


def project_point_onto_plane(p: Point3, pl: Plane3) -> Point3:
    """Hình chiếu vuông góc — chân đường cao. Chính là chỗ hình vẽ tay đặt sai."""
    n = pl.normal
    t = pl.signed_eval(p) / _m.conorm_sq(n)
    return p - _m.normal_vector(n).scale(t)


def project_point_onto_line(p: Point3, ln: Line3) -> Point3:
    d = ln.direction
    t = _m.dot(p - ln.point, d) / _m.norm_sq(d)
    return ln.at(t)


def plane_through_point_perpendicular_to(p: Point3, ln: Line3) -> Plane3:
    """Mặt phẳng qua `p` và vuông góc với `ln` — pháp tuyến CHÍNH LÀ phương của
    `ln`. Viết ra thành hàm riêng vì đây là chỗ trực giác hay lộn dấu."""
    return Plane3(p, _m.plane_covector(ln.direction))


def plane_through_point_parallel_to(p: Point3, pl: Plane3) -> Plane3:
    return Plane3(p, pl.normal)


def line_through_point_parallel_to(p: Point3, ln: Line3) -> Line3:
    return Line3(p, ln.direction)


def perpendicular_foot_line(p: Point3, pl: Plane3) -> Line3:
    """Đường vuông góc hạ từ `p` xuống `(pl)` — đối tượng cần VẼ trong bài
    khoảng cách, không chỉ cần con số."""
    chan = project_point_onto_plane(p, pl)
    if (chan - p).is_zero():
        raise GeometryError(
            ERR_VECTO_KHONG,
            "điểm đã NẰM TRÊN mặt phẳng — khoảng cách bằng 0, không có đường "
            "vuông góc để dựng",
        )
    return Line3(p, chan - p)


#: Đa giác khép từ chuỗi góc vuông không lồi (hoặc suy biến) — §20.4.
ERR_KHONG_LOI = "POLYGON_CHAIN_NOT_CONVEX"


def right_angle_chain_start(k: int, is_right: "Callable[[int], object]") -> int | None:
    """Chỉ số i đầu tiên mà k − 2 đỉnh i+1 … i+k−2 (theo chu trình k đỉnh) đều có góc vuông; `None` nếu không có.

    Một đa giác k đỉnh LỒI được xác định (sai khác đẳng cự) bởi k − 1 cạnh liên tiếp cùng k − 2 góc vuông giữa
    chúng: tam giác vuông, hình thang vuông, … (ASSUMPTION_CERTIFICATE_AMENDMENT §20)."""
    return next((i for i in range(k) if all(is_right((i + t) % k) for t in range(1, k - 1))), None)


def polygon_from_right_angle_chain(lengths: "list[Fraction]") -> tuple[Point3, ...]:
    """Đa giác trong mặt z = 0 từ k − 1 cạnh của chuỗi: cạnh đầu theo +x, quay +90° tại mỗi đỉnh vuông; cạnh cuối
    khép. Chính xác trong ℚ³. NÉM `ERR_KHONG_LOI` khi đa giác khép không lồi — cách đọc lồi là cách đọc duy nhất được
    nhận, không đoán chiều quay khác."""
    huong = (Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(-1, 0, 0), Vec3.of(0, -1, 0))
    p = [Vec3.of(0, 0, 0)]
    for t, d in enumerate(lengths):
        p.append(p[-1] + huong[t % 4].scale(d))
    k = len(p)
    z = Vec3.of(0, 0, 1)
    if any((p[j] - p[j - 1]).cross(p[(j + 1) % k] - p[j]).dot(z) <= 0 for j in range(k)):
        raise GeometryError(ERR_KHONG_LOI, "chuỗi góc vuông không khép thành đa giác lồi")
    return tuple(p)
