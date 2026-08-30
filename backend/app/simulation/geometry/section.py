# -*- coding: utf-8 -*-
"""Dựng THIẾT DIỆN — phép dựng cốt lõi, và bài có cơ chế ẩn lớn nhất.

VÌ SAO ĐÂY LÀ BÀI QUAN TRỌNG NHẤT: học sinh **không hình dung nổi** giao tuyến
trong đầu. Hình vẽ trong vở là một hình chiếu phẳng, và trên hình chiếu ấy hai
đường chéo nhau trông y hệt hai đường cắt nhau. Đây là chỗ mô phỏng 3D không
trang trí — nó cho thấy đúng thứ giấy không cho thấy được.

THUẬT TOÁN — đi theo MẶT, không đi theo ĐIỂM. Cách ngây thơ là gom mọi giao
điểm rồi sắp xếp quanh trọng tâm theo góc; cách ấy cần `atan2`, tức kéo vô tỉ
vào đúng chỗ đang cố giữ chính xác, **và** nó vứt mất thứ ta cần nhất: **thứ tự
dựng**. Đi theo mặt thì mỗi mặt cho **một cạnh** của thiết diện, và dãy cạnh ấy
chính là dãy bước mà học sinh phải làm trên giấy — timeline có sẵn, không phải
bịa ra sau.

Chỉ nhận **đa diện LỒI**. Đa diện lõm cho thiết diện có thể gồm nhiều mảnh rời,
và `RUN2`/roadmap đã khoanh phạm vi ở khối lồi.

FAIL-CLOSED: mặt phẳng không cắt khối → **NÉM**, không trả đa giác rỗng. Một
đa giác rỗng đi tiếp tới renderer sẽ thành một cảnh trống mà không ai nói là
đang trống — đúng lỗi đã sinh ra bất biến #31.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .exact import (
    ERR_CHUA_TRONG,
    ERR_SONG_SONG,
    ERR_THANG_HANG,
    GeometryError,
    Plane3,
    Point3,
)

#: Mặt phẳng nằm hẳn ngoài khối — không một điểm chung nào.
ERR_KHONG_CAT = "PLANE_DOES_NOT_CUT"
#: Chạm khối ở ĐÚNG MỘT ĐỈNH. Có điểm chung, nhưng thiết diện suy biến thành
#: một điểm.
ERR_CHAM_DINH = "PLANE_TOUCHES_VERTEX"
#: Chạm khối ở ĐÚNG MỘT CẠNH. Thiết diện suy biến thành một đoạn thẳng.
ERR_CHAM_CANH = "PLANE_TOUCHES_EDGE"
#: Khối khai sai (mặt < 3 đỉnh, chỉ số ngoài biên…).
ERR_KHOI_HONG = "MALFORMED_SOLID"

#: BỐN mã suy biến, cố ý KHÔNG gộp thành một.
#:
#: Bản đầu gộp *"không cắt"* và *"chạm một đỉnh"* vào cùng `PLANE_DOES_NOT_CUT`
#: **với cùng một câu** — *"toàn bộ khối nằm về một phía"* — và câu ấy SAI cho
#: ca chạm đỉnh: khối có đúng một điểm nằm TRÊN mặt phẳng, không nằm về phía
#: nào cả. Kernel phân biệt được bốn ca này (đếm đỉnh có `signed_eval == 0` và
#: xem chúng có tạo thành một cạnh của khối không), nên gộp chúng lại là **vứt
#: đi thông tin đã có sẵn** — và đó đúng là thông tin học sinh cần: "mặt phẳng
#: của em đi qua đỉnh S" là một lời chẩn đoán, "không cắt" thì không.
SECTION_DEGENERATE_CODES = (
    ERR_KHONG_CAT, ERR_CHAM_DINH, ERR_CHAM_CANH, ERR_CHUA_TRONG,
)


@dataclass(frozen=True)
class Polyhedron:
    """Đa diện lồi: đỉnh + mặt (mỗi mặt là dãy chỉ số đỉnh, theo thứ tự vòng).

    Đặt ở đây chứ không ở `exact.py` vì hiện chỉ `section` dùng. Chuyển lên khi
    có người dùng thứ hai — chuyển sớm là suy đoán.
    """

    vertices: tuple[Point3, ...]
    faces: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        n = len(self.vertices)
        if n < 4:
            raise GeometryError(ERR_KHOI_HONG, f"đa diện cần ≥4 đỉnh, có {n}")
        for i, f in enumerate(self.faces):
            if len(f) < 3:
                raise GeometryError(
                    ERR_KHOI_HONG, f"mặt {i} có {len(f)} đỉnh, cần ≥3"
                )
            for j in f:
                if not 0 <= j < n:
                    raise GeometryError(
                        ERR_KHOI_HONG, f"mặt {i} trỏ đỉnh {j} ngoài [0,{n})"
                    )

    def edges_of_face(self, fi: int) -> list[tuple[int, int]]:
        f = self.faces[fi]
        return [(f[i], f[(i + 1) % len(f)]) for i in range(len(f))]


@dataclass(frozen=True)
class SectionStep:
    """Một bước dựng — đúng một cạnh của thiết diện, kèm mặt sinh ra nó.

    `face_index` không phải trang trí: lời kể *"trên mặt (SBC), nối M với N"*
    chỉ nói được khi biết cạnh này đến từ mặt nào.
    """

    face_index: int
    a: Point3
    b: Point3


@dataclass(frozen=True)
class Section:
    polygon: tuple[Point3, ...]
    steps: tuple[SectionStep, ...]

    @property
    def is_closed(self) -> bool:
        return len(self.polygon) >= 3


def _giao_canh(p: Point3, q: Point3, pl: Plane3) -> Point3| None:
    """Giao của ĐOẠN `pq` với mặt phẳng, hoặc `None` nếu đoạn không cắt.

    Đầu mút nằm trên mặt phẳng được trả về chính nó — không nội suy. Nội suy
    một điểm đã nằm sẵn trên mặt phẳng là cách sinh ra hai điểm "gần trùng"
    rồi thất bại khi nối vòng.
    """
    sp, sq = pl.signed_eval(p), pl.signed_eval(q)
    if sp == 0:
        return p
    if sq == 0:
        return q
    if (sp > 0) == (sq > 0):
        return None
    t = sp / (sp - sq)
    return p + (q - p).scale(t)


def _canh_tren_mat(sol: Polyhedron, fi: int, pl: Plane3) -> tuple[Point3, Point3] | None:
    """Mặt phẳng cắt mặt `fi` theo đoạn nào. `None` nếu không cắt / chỉ chạm."""
    diem: list[Point3] = []
    for i, j in sol.edges_of_face(fi):
        g = _giao_canh(sol.vertices[i], sol.vertices[j], pl)
        if g is not None and all(g != d for d in diem):
            diem.append(g)
    if len(diem) < 2:
        return None          # không cắt, hoặc chỉ chạm một đỉnh
    if len(diem) > 2:
        # Mặt nằm TRONG mặt phẳng cắt: thiết diện suy biến thành chính mặt ấy.
        raise GeometryError(
            ERR_CHUA_TRONG,
            f"mặt {fi} NẰM TRONG mặt phẳng cắt — thiết diện suy biến thành "
            f"chính mặt đó, không phải một đa giác cắt ngang",
        )
    return diem[0], diem[1]


def _loi_suy_bien(sol: Polyhedron, pl: Plane3) -> GeometryError:
    """Chẩn đoán ca suy biến từ TIẾP XÚC THẬT, không từ số cạnh gom được.

    Câu hỏi phân loại là *"những đỉnh nào NẰM TRÊN mặt phẳng"* — `signed_eval`
    trả `Fraction`, nên `== 0` ở đây là một mệnh đề đúng-hoặc-sai, không phải
    một phép so gần đúng.

    Hai đỉnh nằm trên mặt phẳng **chưa chắc** là ca "chạm một cạnh": chúng phải
    là hai đầu của một cạnh THẬT của khối. Hai đỉnh đối nhau trên một mặt vuông
    thì mặt phẳng đi xuyên qua khối chứ không chạm — nên phải tra bảng mặt, và
    tra bảng mặt là thứ hàm này có mà tầng gọi không nên tự làm.
    """
    tren = [i for i, v in enumerate(sol.vertices) if pl.signed_eval(v) == 0]
    if not tren:
        return GeometryError(
            ERR_KHONG_CAT,
            "mặt phẳng KHÔNG cắt khối — toàn bộ khối nằm về một phía, "
            "không có điểm chung nào",
        )
    if len(tren) == 1:
        return GeometryError(
            ERR_CHAM_DINH,
            f"mặt phẳng chỉ CHẠM khối ở đúng một đỉnh (đỉnh thứ {tren[0] + 1}) "
            "— thiết diện suy biến thành một điểm, không phải đa giác",
        )
    if len(tren) == 2:
        canh = {
            tuple(sorted(c))
            for fi in range(len(sol.faces))
            for c in sol.edges_of_face(fi)
        }
        if tuple(sorted(tren)) in canh:
            return GeometryError(
                ERR_CHAM_CANH,
                f"mặt phẳng chỉ CHẠM khối ở đúng một cạnh (đỉnh thứ "
                f"{tren[0] + 1} và {tren[1] + 1}) — thiết diện suy biến thành "
                "một đoạn thẳng, không phải đa giác",
            )
    return GeometryError(
        ERR_KHONG_CAT,
        f"mặt phẳng chạm khối ở {len(tren)} đỉnh nhưng không cắt được thành "
        "đa giác — kiểm lại bảng mặt của khối",
    )


def cross_section(sol: Polyhedron, pl: Plane3) -> Section:
    """Thiết diện của `pl` với đa diện lồi `sol`.

    Trả về **đa giác đã sắp thứ tự** cùng **dãy bước dựng** — mỗi bước là một
    cạnh, gắn với mặt sinh ra nó.
    """
    doan: list[tuple[int, Point3, Point3]] = []
    for fi in range(len(sol.faces)):
        c = _canh_tren_mat(sol, fi, pl)
        if c is not None:
            doan.append((fi, c[0], c[1]))

    if len(doan) < 3:
        raise _loi_suy_bien(sol, pl)

    # Nối vòng: mỗi cạnh phải khớp đầu mút với đúng một cạnh kế.
    thu_tu: list[SectionStep] = [SectionStep(doan[0][0], doan[0][1], doan[0][2])]
    con_lai = doan[1:]
    dinh = [doan[0][1], doan[0][2]]
    while con_lai:
        cuoi = dinh[-1]
        for k, (fi, a, b) in enumerate(con_lai):
            if a == cuoi or b == cuoi:
                tiep = b if a == cuoi else a
                thu_tu.append(SectionStep(fi, cuoi, tiep))
                dinh.append(tiep)
                con_lai.pop(k)
                break
        else:
            raise GeometryError(
                ERR_KHOI_HONG,
                "không nối được thiết diện thành đa giác kín — khối có thể "
                "KHÔNG LỒI, hoặc bảng mặt khai thiếu",
            )

    if dinh[-1] != dinh[0]:
        raise GeometryError(
            ERR_KHOI_HONG, "thiết diện không khép kín — bảng mặt khai thiếu"
        )
    da_giac = tuple(dinh[:-1])
    _kiem_hau_dieu_kien(da_giac, pl)
    return Section(da_giac, tuple(thu_tu))


def _kiem_hau_dieu_kien(poly: tuple[Point3, ...], pl: Plane3) -> None:
    """Hậu điều kiện của chính `cross_section`, KHÔNG phải checker thứ hai.

    Đặt ở đây thay vì ở tầng nghĩa vụ là có chủ đích: ba mệnh đề dưới đây là
    lời hứa của **hàm này**, nên hàm này phải là chỗ nó vỡ. Một checker song
    song ở tầng trên sẽ kiểm lại cùng một điều bằng một cài đặt thứ hai — và
    hai cài đặt cùng một luật là hai chỗ để trôi khỏi nhau.
    """
    if len(poly) < 3:
        raise GeometryError(
            ERR_KHOI_HONG,
            f"thiết diện chỉ có {len(poly)} đỉnh — cần ít nhất 3 để là đa giác",
        )
    if len(set(poly)) != len(poly):
        raise GeometryError(
            ERR_KHOI_HONG, "thiết diện có đỉnh TRÙNG NHAU — vòng nối hỏng"
        )
    for i, v in enumerate(poly):
        if pl.signed_eval(v) != 0:
            raise GeometryError(
                ERR_KHOI_HONG,
                f"đỉnh thứ {i + 1} của thiết diện KHÔNG nằm trên mặt phẳng cắt",
            )


# ── SO SÁNH HAI THIẾT DIỆN ────────────────────────────────────────────────
def _khoa(p: Point3) -> tuple[Fraction, Fraction, Fraction]:
    """Khoá sắp xếp CHÍNH XÁC. `Fraction` so trực tiếp — không có float ở đây."""
    return (p.x, p.y, p.z)


def canonical_cycle(poly: Sequence[Point3]) -> tuple[Point3, ...]:
    """Dạng chuẩn của một CHU TRÌNH đa giác — bất biến với xoay và với đảo hướng.

    `[A,B,C,D]`, `[B,C,D,A]`, `[D,C,B,A]` cho **cùng một** dạng chuẩn: chúng là
    cùng một đa giác, chỉ khác chỗ bắt đầu đọc và chiều đọc. `[A,C,B,D]` thì
    KHÁC — đó là một tứ giác khác, nối chéo.

    Cách làm: sinh cả **2n** ảnh của nhóm nhị diện (n phép xoay × 2 chiều) rồi
    lấy dãy nhỏ nhất theo khoá toạ độ. Chọn "xoay về đỉnh nhỏ nhất" thì rẻ hơn
    nhưng SAI khi có hai đỉnh cùng nhỏ nhất; ở đây `n ≤ vài chục` nên vét cạn
    là đúng và không đáng tiếc.

    ⚠️ Đây là so sánh HÌNH HỌC theo toạ độ chính xác, **không** phải so nhãn.
    Hai thiết diện cùng hình mà một bên đặt tên `MNPQ`, bên kia `PQMN` vẫn phải
    là một — nhãn là chuyện trình bày.
    """
    n = len(poly)
    if n == 0:
        return ()
    t = tuple(poly)
    ung = [c[i:] + c[:i] for c in (t, t[::-1]) for i in range(n)]
    return min(ung, key=lambda c: tuple(_khoa(p) for p in c))


def same_section_cycle(a: Sequence[Point3], b: Sequence[Point3]) -> bool:
    """Hai chu trình có phải cùng một đa giác không. Xoay/đảo hướng ⇒ CÙNG."""
    return len(a) == len(b) and canonical_cycle(a) == canonical_cycle(b)


# ── khối dựng sẵn, dùng cho demo và test ──────────────────────────────────
def box(w: Fraction | int = 1, d: Fraction | int = 1, h: Fraction | int = 1) -> Polyhedron:
    """Hình hộp chữ nhật, một góc ở gốc toạ độ. Mặt theo thứ tự vòng."""
    from .exact import Vec3

    v = tuple(
        Vec3.of(x, y, z)
        for x in (0, w) for y in (0, d) for z in (0, h)
    )  # chỉ số: (x,y,z) → 4x + 2y + z với 0/1
    return Polyhedron(
        vertices=v,
        faces=(
            (0, 2, 3, 1),  # x = 0
            (4, 5, 7, 6),  # x = w
            (0, 1, 5, 4),  # y = 0
            (2, 6, 7, 3),  # y = d
            (0, 4, 6, 2),  # z = 0
            (1, 3, 7, 5),  # z = h
        ),
    )


def pyramid_square(side: Fraction | int = 1, height: Fraction | int = 2) -> Polyhedron:
    """Chóp `S.ABCD` đáy vuông — cấu hình kinh điển của Toán 11.

    Đỉnh 0..3 = `A B C D` (đáy, `z=0`), đỉnh 4 = `S` trên `A`.
    """
    from .exact import Vec3

    return Polyhedron(
        vertices=(
            Vec3.of(0, 0, 0), Vec3.of(side, 0, 0),
            Vec3.of(side, side, 0), Vec3.of(0, side, 0),
            Vec3.of(0, 0, height),
        ),
        faces=((0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)),
    )
