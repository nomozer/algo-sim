# -*- coding: utf-8 -*-
"""ORACLE ĐỘC LẬP cho bộ đánh giá cuối của khoá luận. **0 lượt gọi model.**

    `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`, 2026-09-08.

Bộ đo, ở `scripts/` — ngoài `MEASURED_SYSTEM_PATHS`.

─── LUẬT CỨNG CỦA FILE NÀY ────────────────────────────────────────────────

**KHÔNG import bất cứ thứ gì dưới `app.simulation.geometry`.** Đó không phải
một quy ước cho đẹp: `geometry/` chính là thứ đang bị kiểm, và một oracle gọi
lại nó thì chỉ chứng minh nó nhất quán với chính mình. Cổng chống tái phát:
`tests/geometry/test_thesis_acceptance_matrix.py` quét AST file này và ĐỎ nếu
thấy một `import` nào chạm `app.`.

Hệ quả: mọi đại lượng ở đây dẫn lại **từ đầu**, bằng đường khác đường kernel đi.

    thể tích khối chóp     shoelace 2D + h/3        (kernel: tổng có dấu trên mặt)
    diện tích đa giác 3D   ½|Σ Pᵢ × Pᵢ₊₁|           (kernel: chiếu + Newell)
    khoảng cách điểm–đường |w × u| / |u|            (kernel: đại số chính xác)
    cầu · trụ · nón        công thức SGK
    thiết diện elip        **LẤY MẪU giao tuyến + shoelace 3D**, KHÔNG công thức

Ô cuối là chỗ độc lập đáng giá nhất. `curved.py` phân xử conic rồi dẫn hai bán
trục bằng một phép rút gọn hữu tỉ; ở đây không có bán trục nào cả — chỉ có vài
vạn điểm nằm trên giao tuyến và một phép tính diện tích đa giác. Hai đường ấy
sai theo hai kiểu khác nhau, nên chúng trùng số là một bằng chứng thật.

─── VÌ SAO CÓ MỘT BỘ PHÂN TÍCH CHUỖI HIỂN THỊ Ở ĐÂY ───────────────────────

Sản phẩm trả đáp số dưới dạng CHUỖI người đọc (`25π√5`), do `radical.display()`
sinh. So chuỗi với chuỗi là phép kiểm đúng — đó là thứ học sinh nhìn thấy —
nhưng nó **chỉ** kiểm chính tả: một quy ước hiển thị đổi chỗ `π` và `√` sẽ làm
mọi ca đỏ dù số không sai một li, và ngược lại hai chuỗi giống nhau chưa nói
được chúng chỉ về cùng một số.

Nên có hai cột, và cố ý không gộp:

    EXACT_ANSWER_MATCH        chuỗi khớp chuỗi          ← thứ sản phẩm hiện ra
    ORACLE_NUMERIC_AGREEMENT  |giá trị − oracle| nhỏ    ← thứ nói chuỗi ấy ĐÚNG SỐ

Bộ phân tích dưới đây đọc chuỗi hiển thị bằng mã **của riêng nó**, không gọi
`radical.py`. Nó cố tình hẹp: chỉ nhận đúng ngữ pháp mà `display()` phát ra.
Gặp dạng lạ thì NÉM, không đoán — một oracle đoán là một oracle nói dối.
"""
from __future__ import annotations

import math
import re
from fractions import Fraction
from typing import Callable, Iterable, Sequence

__all__ = [
    "ORACLE_KHONG_DUOC_IMPORT",
    "OracleError",
    "doc_chuoi_hien_thi",
    "dien_tich_da_giac_3d",
    "dien_tich_shoelace_2d",
    "elip_lay_mau_non",
    "elip_lay_mau_tru",
    "khoang_cach_diem_duong",
    "khoi_cau",
    "khoi_non",
    "khoi_tru",
    "sai_so_tuong_doi",
    "the_tich_chop",
    "thiet_dien_tron_cau",
]

#: Tiền tố module mà file này KHÔNG được import. Guard đọc hằng số này thay vì
#: gõ lại chuỗi — một danh sách chép hai nơi sẽ lệch ở nơi không ai nhìn.
ORACLE_KHONG_DUOC_IMPORT = ("app",)

Vec = tuple[float, float, float]


class OracleError(RuntimeError):
    """Oracle từ chối trả lời. **Không** trả một con số đoán."""


# ══ ĐA DIỆN — đường khác hẳn kernel ═══════════════════════════════════════
def dien_tich_shoelace_2d(diem: Sequence[Sequence[float]]) -> float:
    """Diện tích đa giác phẳng theo thứ tự quanh biên. Giữ DẤU rồi mới `abs`.

    Chỗ lõm sống hay chết nằm đúng ở đây: `abs` từng số hạng sẽ lấp chỗ lõm và
    cho một số lớn hơn — bệnh mà `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` đã
    đo được ở chính mã sản phẩm (`28` thay vì `20`).
    """
    n = len(diem)
    if n < 3:
        raise OracleError(f"cần ≥ 3 đỉnh, nhận {n}")
    s = sum(diem[i][0] * diem[(i + 1) % n][1]
            - diem[(i + 1) % n][0] * diem[i][1] for i in range(n))
    return abs(s) / 2.0


def the_tich_chop(day: Sequence[Sequence[float]], cao: float) -> float:
    """`V = S_đáy · h / 3` — đáy phẳng nằm trong một mặt phẳng toạ độ."""
    return dien_tich_shoelace_2d(day) * cao / 3.0


def _tru(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _nhan_co(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _do_dai(a: Vec) -> float:
    return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


def dien_tich_da_giac_3d(diem: Sequence[Vec]) -> float:
    """`½|Σ Pᵢ × Pᵢ₊₁|` — đúng cho MỌI đa giác phẳng, kể cả không lồi.

    Không chiếu xuống mặt toạ độ nào, nên nó không cần biết đa giác nằm trong
    mặt phẳng nào — khác hẳn đường `section.py` đi.
    """
    n = len(diem)
    if n < 3:
        raise OracleError(f"cần ≥ 3 đỉnh, nhận {n}")
    tong = (0.0, 0.0, 0.0)
    for i in range(n):
        c = _nhan_co(diem[i], diem[(i + 1) % n])
        tong = (tong[0] + c[0], tong[1] + c[1], tong[2] + c[2])
    return _do_dai(tong) / 2.0


def khoang_cach_diem_duong(p: Vec, a: Vec, b: Vec) -> float:
    """`|(p−a) × (b−a)| / |b−a|`."""
    u = _tru(b, a)
    if _do_dai(u) == 0:
        raise OracleError("hai điểm định nghĩa đường trùng nhau")
    return _do_dai(_nhan_co(_tru(p, a), u)) / _do_dai(u)


# ══ KHỐI TRÒN CƠ BẢN — công thức SGK ══════════════════════════════════════
def khoi_cau(r: float) -> dict[str, float]:
    return {"volume": 4.0 / 3.0 * math.pi * r ** 3,
            "area": 4.0 * math.pi * r ** 2, "radius": float(r)}


def khoi_tru(r: float, h: float) -> dict[str, float]:
    return {"volume": math.pi * r ** 2 * h,
            "lateral_area": 2.0 * math.pi * r * h, "radius": float(r)}


def khoi_non(r: float, h: float) -> dict[str, float]:
    l = math.sqrt(r ** 2 + h ** 2)
    return {"volume": math.pi * r ** 2 * h / 3.0,
            "lateral_area": math.pi * r * l, "duong_sinh": l,
            "radius": float(r)}


def thiet_dien_tron_cau(r: float, d: float) -> dict[str, float]:
    """Mặt phẳng cách tâm `d` cắt mặt cầu bán kính `r` theo đường tròn."""
    if d >= r:
        raise OracleError(f"mặt phẳng cách tâm {d} ≥ bán kính {r} — không cắt")
    rc = math.sqrt(r ** 2 - d ** 2)
    return {"radius": rc, "area": math.pi * rc ** 2}


# ══ THIẾT DIỆN ELIP — LẤY MẪU, không dùng công thức bán trục ══════════════
#
# Đây là chỗ oracle phải đi xa nhất khỏi kernel. `curved.py` phân xử conic bằng
# một phép so hữu tỉ rồi rút ra `a²`, `b²`; nếu oracle cũng làm vậy thì hai bên
# chỉ đang kiểm lại cùng một phép rút gọn. Ở đây không có bán trục: lấy vài vạn
# điểm NẰM TRÊN giao tuyến rồi tính diện tích đa giác 3D nội tiếp.
#
# Sai số của phép này là sai số ĐA GIÁC NỘI TIẾP, giảm như `O(1/n²)`, nên với
# `n = 200 000` nó ở cỡ `1e-10` tương đối — đủ để phân biệt một đáp số đúng với
# một đáp số sai ở chữ số thứ ba, tức mọi lỗi thật.
_MAU_MAC_DINH = 200_000


def _lay_mau_giao_tuyen(diem_tren_giao: Callable[[float], Vec],
                        n: int) -> list[Vec]:
    return [diem_tren_giao(2.0 * math.pi * i / n) for i in range(n)]


def elip_lay_mau_tru(*, tam_day: Vec, tam_day_kia: Vec, ban_kinh: float,
                     mat_phang: tuple[float, float, float, float],
                     n: int = _MAU_MAC_DINH) -> dict[str, float]:
    """Diện tích thiết diện của HÌNH TRỤ cắt bởi `ax+by+cz+d = 0`.

    Trục trụ giả thiết song song `Oz` — đúng cho bộ ca, và guard kiểm điều đó
    thay vì tin: một oracle im lặng chấp nhận trục xiên sẽ trả một con số sai
    trông rất giống đúng.
    """
    a, b, c, d = mat_phang
    if tam_day[0] != tam_day_kia[0] or tam_day[1] != tam_day_kia[1]:
        raise OracleError("oracle này chỉ nhận trục trụ song song Oz")
    if c == 0:
        raise OracleError("mặt phẳng song song trục — không cho elip")
    x0, y0 = tam_day[0], tam_day[1]

    def diem(t: float) -> Vec:
        x = x0 + ban_kinh * math.cos(t)
        y = y0 + ban_kinh * math.sin(t)
        return (x, y, -(a * x + b * y + d) / c)

    mau = _lay_mau_giao_tuyen(diem, n)
    _kiem_tren_mat_phang(mau, mat_phang)
    return {"area": dien_tich_da_giac_3d(mau), "so_mau": n}


def elip_lay_mau_non(*, dinh: Vec, tam_day: Vec, ban_kinh: float,
                     mat_phang: tuple[float, float, float, float],
                     n: int = _MAU_MAC_DINH) -> dict[str, float]:
    """Diện tích thiết diện của HÌNH NÓN HỮU HẠN cắt bởi `ax+by+cz+d = 0`.

    Đi theo TIA từ đỉnh, không theo phương trình mặt nón: mỗi đường sinh cắt
    mặt phẳng ở đúng một điểm (khi mặt phẳng không song song đường sinh ấy), và
    tập những điểm đó CHÍNH LÀ giao tuyến. Cách này không cần biết conic thuộc
    loại nào — nên nó cũng không thể "biết trước" đáp án như một công thức elip.
    """
    a, b, c, d = mat_phang
    if dinh[0] != tam_day[0] or dinh[1] != tam_day[1]:
        raise OracleError("oracle này chỉ nhận trục nón song song Oz")
    x0, y0 = tam_day[0], tam_day[1]
    cao = tam_day[2] - dinh[2]

    def diem(t: float) -> Vec:
        vanh = (x0 + ban_kinh * math.cos(t), y0 + ban_kinh * math.sin(t),
                tam_day[2])
        u = _tru(vanh, dinh)
        mau_so = a * u[0] + b * u[1] + c * u[2]
        if abs(mau_so) < 1e-15:
            raise OracleError("mặt phẳng song song một đường sinh — không elip")
        s = -(a * dinh[0] + b * dinh[1] + c * dinh[2] + d) / mau_so
        if not (0.0 < s <= 1.0 + 1e-12):
            raise OracleError(
                f"giao điểm nằm NGOÀI nón hữu hạn (s = {s:.6f}) — thiết diện "
                f"không nằm trọn giữa đỉnh và đáy")
        return (dinh[0] + s * u[0], dinh[1] + s * u[1], dinh[2] + s * u[2])

    _ = cao
    mau = _lay_mau_giao_tuyen(diem, n)
    _kiem_tren_mat_phang(mau, mat_phang)
    return {"area": dien_tich_da_giac_3d(mau), "so_mau": n}


def _kiem_tren_mat_phang(mau: Iterable[Vec],
                         mp: tuple[float, float, float, float]) -> None:
    """Mọi điểm lấy mẫu PHẢI nằm trên mặt phẳng. Guard chống lỗi đại số của
    chính oracle — không có nó thì một dấu trừ sai sẽ đi thẳng vào kết luận."""
    a, b, c, d = mp
    chuan = max(math.sqrt(a * a + b * b + c * c), 1e-30)
    lech = max(abs(a * p[0] + b * p[1] + c * p[2] + d) / chuan for p in mau)
    if lech > 1e-9:
        raise OracleError(f"điểm lấy mẫu lệch mặt phẳng {lech:.3e}")


# ══ ĐỌC CHUỖI HIỂN THỊ — ngữ pháp hẹp, gặp lạ thì NÉM ═════════════════════
#
# Ngữ pháp `radical.display()` phát ra, đọc từ artifact thật của kho:
#
#     72 · 96 · 320/3            hữu tỉ
#     4500π · 144π               hữu tỉ × π
#     3√6                        hữu tỉ × căn
#     25π√5 · 2π√6               hữu tỉ × π × căn
#
# Cố ý KHÔNG nhận tổng (`1+√2`) và KHÔNG nhận căn lồng: bộ ca hiện tại không
# sinh ra chúng, và một bộ phân tích nhận nhiều hơn thứ nó đã được kiểm là một
# bộ phân tích sẽ đọc sai lặng lẽ vào lần đầu gặp dạng mới.
_MAU = re.compile(
    r"^(?P<dau>-)?"
    r"(?P<tu>\d+)?"
    r"(?:/(?P<mau>\d+))?"
    r"(?P<pi>π)?"
    r"(?:√(?P<can>\d+))?$"
)


def doc_chuoi_hien_thi(s: str) -> float:
    """Chuỗi hiển thị của sản phẩm → `float`. Dạng lạ ⇒ NÉM."""
    if not isinstance(s, str) or not s.strip():
        raise OracleError(f"không phải chuỗi hiển thị: {s!r}")
    m = _MAU.match(s.strip())
    if m is None:
        raise OracleError(
            f"chuỗi {s!r} nằm NGOÀI ngữ pháp oracle biết đọc — bộ đo từ chối "
            f"đoán. Mở rộng ngữ pháp Ở ĐÂY, có test, rồi mới dùng.")
    g = m.groupdict()
    if g["tu"] is None and g["pi"] is None and g["can"] is None:
        raise OracleError(f"chuỗi {s!r} rỗng nghĩa")
    gt = Fraction(int(g["tu"] or 1), int(g["mau"] or 1))
    ra = float(gt)
    if g["pi"]:
        ra *= math.pi
    if g["can"]:
        ra *= math.sqrt(int(g["can"]))
    return -ra if g["dau"] else ra


def sai_so_tuong_doi(hien_thi: str, oracle: float) -> float:
    """`|đọc(hiển thị) − oracle| / max(|oracle|, 1)`."""
    return abs(doc_chuoi_hien_thi(hien_thi) - oracle) / max(abs(oracle), 1.0)
