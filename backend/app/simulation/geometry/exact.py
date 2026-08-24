# -*- coding: utf-8 -*-
"""Kiểu hình học 3D trên số học CHÍNH XÁC (`Fraction`). Nền của geometry kernel.

VÌ SAO KHÔNG DÙNG `float`: so sánh dấu phẩy động là nguồn sai **lặng lẽ** kinh
điển ở hình học. Hai mặt phẳng song song hoá ra "cắt nhau" ở một điểm cách xa
10^15, hoặc ba điểm thẳng hàng hoá ra dựng được một mặt phẳng có pháp tuyến
gần-không. Không có gì nổ; chỉ có một hình vẽ sai mà học sinh tin.

VÌ SAO `Fraction` ĐỦ, không cần đại số ký hiệu: đề hình học không gian THPT cho
toạ độ **hữu tỉ** (`A(0,0,0)`, `B(1,0,0)`, `S(0,0,2)`). Và mọi phép DỰNG ở đây
là đại số tuyến tính trên ℚ — giao tuyến, giao điểm, trung điểm, hình chiếu,
thể tích — nên kết quả **ở lại trong ℚ**. Vô tỉ chỉ xuất hiện khi lấy căn, tức
ở *độ dài* và *góc*, và `measure.py` xử lý bằng cách giữ **bình phương**.

HỆ QUẢ QUAN TRỌNG NHẤT — tầng vị từ KHÔNG cần một epsilon nào:

    vuông góc  ⇔  u · v == 0          (chính xác)
    song song  ⇔  u × v == 0          (chính xác)
    đồng phẳng ⇔  det == 0            (chính xác)

Đây là lý do claim của luận văn nâng được từ *"kernel tất định"* lên **"kernel
chính xác"**: tất định nghĩa là chạy lại ra cùng kết quả — kể cả cùng một kết
quả SAI. Chính xác nghĩa là không có sai số nào để mà tích luỹ.

FAIL-CLOSED, cùng luật `SemanticExecutionError` của interpreter: phép dựng không
xác định thì **NÉM LỖI**, không trả `None`, không trả một giá trị "gần đúng".
Trả `None` ở đây là để một mặt phẳng suy biến đi tiếp vào renderer.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable

#: Số hữu tỉ chấp nhận được ở đầu vào. `float` được nhận rồi chuyển sang
#: `Fraction` CHÍNH XÁC theo biểu diễn nhị phân của nó — không làm tròn, không
#: đoán. Đề cho `0.5` thì thành `1/2`; đề cho `0.1` thì thành đúng cái mà máy
#: hiểu là `0.1`, và điều đó phải hiện ra chứ không bị giấu.
Huu_ti = Fraction | int | str


class GeometryError(Exception):
    """Phép dựng không xác định. KHÔNG BAO GIỜ thành `None` hay giá trị gần đúng."""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


#: Hai điểm trùng nhau nhưng đòi dựng đường thẳng qua chúng.
ERR_TRUNG_DIEM = "DEGENERATE_POINTS"
#: Ba điểm thẳng hàng nhưng đòi dựng mặt phẳng.
ERR_THANG_HANG = "COLLINEAR_POINTS"
#: Hai đối tượng song song nhưng đòi giao.
ERR_SONG_SONG = "PARALLEL_NO_INTERSECTION"
#: Đối tượng nằm TRONG đối tượng kia — giao là vô số điểm, không phải một điểm.
#: Tách khỏi `ERR_SONG_SONG` vì hai tình huống này dạy hai điều khác nhau.
ERR_CHUA_TRONG = "CONTAINED_INFINITE_INTERSECTION"
#: Vector không, không định hướng được.
ERR_VECTO_KHONG = "ZERO_VECTOR"


def hf(x: Any) -> Fraction:
    """Về `Fraction` chính xác. `float` chuyển theo đúng giá trị nhị phân của nó."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, bool):  # `bool` là subclass của `int` — chặn tường minh
        raise GeometryError(ERR_VECTO_KHONG, "toạ độ không nhận giá trị bool")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        return Fraction(x).limit_denominator(10**9)
    if isinstance(x, str):
        return Fraction(x)
    raise GeometryError(ERR_VECTO_KHONG, f"toạ độ không hợp lệ: {x!r}")


@dataclass(frozen=True)
class Vec3:
    """Vector (hoặc điểm) trong ℚ³. Bất biến — mọi phép trả về đối tượng mới."""

    x: Fraction
    y: Fraction
    z: Fraction

    @staticmethod
    def of(x: Any, y: Any, z: Any) -> "Vec3":
        return Vec3(hf(x), hf(y), hf(z))

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def scale(self, k: Any) -> "Vec3":
        f = hf(k)
        return Vec3(self.x * f, self.y * f, self.z * f)

    def dot(self, o: "Vec3") -> Fraction:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o: "Vec3") -> "Vec3":
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )

    def norm_sq(self) -> Fraction:
        """|v|² — CHÍNH XÁC. Độ dài `|v|` thì vô tỉ, nên không có ở đây.

        Mọi phép so sánh độ dài phải làm trên bình phương. `measure.py` mới là
        chỗ được phép trả `float`, và chỉ để hiển thị.
        """
        return self.dot(self)

    def is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0

    def as_float(self) -> tuple[float, float, float]:
        """BIÊN HIỂN THỊ — chỉ dùng khi đóng gói cho renderer, không để tính."""
        return (float(self.x), float(self.y), float(self.z))


#: Điểm và vector cùng một biểu diễn, khác vai. Đặt bí danh để chữ ký hàm đọc
#: đúng ý định — `Point3` ở vị trí điểm, `Vec3` ở vị trí phương.
Point3 = Vec3


@dataclass(frozen=True)
class Line3:
    """Đường thẳng: một điểm + một phương. Phương KHÁC vector không (đã kiểm)."""

    point: Point3
    direction: Vec3

    @staticmethod
    def through(a: Point3, b: Point3) -> "Line3":
        d = b - a
        if d.is_zero():
            raise GeometryError(
                ERR_TRUNG_DIEM,
                "không dựng được đường thẳng qua hai điểm TRÙNG nhau",
            )
        return Line3(a, d)

    def at(self, t: Any) -> Point3:
        return self.point + self.direction.scale(t)


@dataclass(frozen=True)
class Plane3:
    """Mặt phẳng dạng `n · (X − P) = 0`. Pháp tuyến KHÁC vector không.

    Giữ `point` + `normal` thay vì `(a,b,c,d)` vì mọi phép dựng ở đây bắt đầu
    từ **điểm của đề bài**, và giữ nguyên điểm ấy làm cho thông báo lỗi nói
    được tên đối tượng học sinh nhìn thấy.
    """

    point: Point3
    normal: Vec3

    @staticmethod
    def through(a: Point3, b: Point3, c: Point3) -> "Plane3":
        n = (b - a).cross(c - a)
        if n.is_zero():
            raise GeometryError(
                ERR_THANG_HANG,
                "ba điểm THẲNG HÀNG (hoặc có hai điểm trùng) — không xác định "
                "được mặt phẳng",
            )
        return Plane3(a, n)

    def signed_eval(self, p: Point3) -> Fraction:
        """`n · (p − P)`. Bằng 0 ⇔ `p` thuộc mặt phẳng — kiểm CHÍNH XÁC."""
        return self.normal.dot(p - self.point)


def det3(u: Vec3, v: Vec3, w: Vec3) -> Fraction:
    """Định thức 3×3 — CHÍNH XÁC. Bằng 0 ⇔ ba vector đồng phẳng."""
    return u.dot(v.cross(w))


def points_of(raw: Iterable[Iterable[Any]]) -> tuple[Point3, ...]:
    """Tiện ích đọc danh sách toạ độ từ IR. Sai hình dạng thì NÉM, không bỏ qua."""
    ra: list[Point3] = []
    for i, t in enumerate(raw):
        c = list(t)
        if len(c) != 3:
            raise GeometryError(
                ERR_VECTO_KHONG, f"điểm thứ {i} có {len(c)} toạ độ, cần đúng 3"
            )
        ra.append(Vec3.of(*c))
    return tuple(ra)
