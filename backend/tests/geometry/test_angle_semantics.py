# -*- coding: utf-8 -*-
"""MỘT OPCODE = MỘT ĐẠI LƯỢNG. Khoá cho `angle_cos_sq` không nói dối nữa.

─── LỖI NÓ BỊT ────────────────────────────────────────────────────────────

`angle_cos_sq` từng trả **cos²** cho ba cặp toán hạng và **sin²** cho cặp
(đường, mặt). Cùng một tên, hai đại lượng.

`fresh-probe fp_5` giẫm lên: mô hình đo góc giữa `SC` và `(ABC)`, đặt tên biến
`cos_angle_SC_ABC_sq`, nhận `1/3`. cos² của góc ấy là `2/3`.

─── VÌ SAO BỘ CHẤM KHÔNG BẮT ĐƯỢC ────────────────────────────────────────

`geometry_obligations.check_angle` mang một **bản sao** của phép phân phối
theo cặp kiểu — cùng bug. Nó tính lại *cùng một đại lượng sai*, nên nó xác
nhận thay vì bác bỏ. Một bộ chấm chép luật của thứ nó chấm thì chỉ chấm được
lỗi gõ nhầm.

─── CA 0° LÀ CA DUY NHẤT PHÂN BIỆT ĐƯỢC ──────────────────────────────────

Ở 45° thì cos² = sin² = 1/2. Một bộ test chỉ chạy ca 45° sẽ báo XANH cho đúng
con bug này — nên MỌI ca dưới đây dùng góc 0°, 90°, hoặc một góc mà hai đại
lượng khác nhau. Đó là ràng buộc thiết kế, không phải sở thích.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.geometry.exact import GeometryError, Line3, Plane3, Vec3
from app.simulation.geometry.measure import (
    cos_between_vectors,
    cos_sq_giua,
    cos_sq_line_plane,
    sin_sq_line_plane,
)
from app.simulation.geometry.radical import Radical
from app.simulation.semantic_program.contract import MeasureExpr
from app.simulation.semantic_program.geometry_exec import eval_geometry_expr
from app.simulation.semantic_program.validator import validate_semantic_program


def v(x, y, z) -> Vec3:
    return Vec3(Fraction(x), Fraction(y), Fraction(z))


OX = Line3(v(0, 0, 0), v(1, 0, 0))
OY = Line3(v(0, 0, 0), v(0, 1, 0))
OZ = Line3(v(0, 0, 0), v(0, 0, 1))
OX_DOI = Line3(v(0, 5, 0), v(-2, 0, 0))      # song song Ox, khác điểm & chiều
D45 = Line3(v(0, 0, 0), v(1, 0, 1))
P_XY = Plane3(v(0, 0, 0), v(0, 0, 1))        # z = 0
Q45 = Plane3(v(0, 0, 0), v(1, 0, 1))


def _do(q: str, a, b, mem):
    return eval_geometry_expr("measure", MeasureExpr(quantity=q, of=a, wrt=b),
                              mem)


MEM = {"Ox": OX, "Oy": OY, "Oz": OZ, "Ox2": OX_DOI, "d45": D45,
       "P": P_XY, "Q": Q45}


# ══ ① ĐƯỜNG × ĐƯỜNG — nghĩa cũ, phải giữ nguyên ═════════════════════════
@pytest.mark.parametrize("a, b, mong", [
    ("Ox", "Oy", Fraction(0)),          # vuông góc
    ("Ox", "Ox2", Fraction(1)),         # song song (khác chiều khai)
    ("Ox", "Ox", Fraction(1)),          # trùng
    ("Ox", "d45", Fraction(1, 2)),      # 45°
])
def test_duong_duong_van_la_cos_binh(a, b, mong):
    assert _do("angle_cos_sq", a, b, MEM) == mong


def test_song_song_khong_phu_thuoc_CHIEU_khai():
    """`Ox2` khai chiều `(-2,0,0)` — ngược `Ox`. Góc giữa hai ĐƯỜNG không có
    chiều, nên cos² phải là 1 chứ không phải một giá trị âm nào đó."""
    assert cos_sq_giua(OX, OX_DOI) == 1


# ══ ② ĐƯỜNG × MẶT — ĐÂY LÀ CHỖ ĐÃ SỬA ═══════════════════════════════════
@pytest.mark.parametrize("a, b, cos2, sin2", [
    ("Ox", "P", Fraction(1), Fraction(0)),    # đường NẰM TRONG mặt, góc 0°
    ("Oz", "P", Fraction(0), Fraction(1)),    # đường ⊥ mặt, góc 90°
])
def test_duong_mat_nay_tra_COS_binh_khong_phai_SIN_binh(a, b, cos2, sin2):
    """Hai ca này phân biệt được cos² với sin²; ca 45° thì KHÔNG."""
    assert cos2 != sin2, "ca không phân biệt được — vô dụng làm guard"
    assert _do("angle_cos_sq", a, b, MEM) == cos2


def test_dao_thu_tu_toan_hang_cho_CUNG_ket_qua():
    """Góc là quan hệ đối xứng. `(P, Ox)` phải bằng `(Ox, P)`."""
    assert _do("angle_cos_sq", "P", "Ox", MEM) == _do("angle_cos_sq", "Ox",
                                                      "P", MEM)


def test_cos_sq_va_sin_sq_van_bu_nhau():
    """`cos_sq_line_plane` dẫn xuất từ `sin_sq_line_plane`; nếu quan hệ bù vỡ
    thì một trong hai đã bị sửa rời khỏi cái kia."""
    for ln in (OX, OZ, D45):
        assert cos_sq_line_plane(ln, P_XY) + sin_sq_line_plane(ln, P_XY) == 1


# ══ ③ MẶT × MẶT ════════════════════════════════════════════════════════
@pytest.mark.parametrize("a, b, mong", [
    ("P", "P", Fraction(1)),            # trùng, góc 0°
    ("P", "Q", Fraction(1, 2)),         # 45°
])
def test_mat_mat_la_cos_binh(a, b, mong):
    assert _do("angle_cos_sq", a, b, MEM) == mong


# ══ ④ CHÍNH XÁC — không float lọt vào ═══════════════════════════════════
@pytest.mark.parametrize("a, b", [("Ox", "d45"), ("Ox", "P"), ("Oz", "P"),
                                  ("P", "Q")])
def test_ket_qua_luon_la_Fraction(a, b):
    r = _do("angle_cos_sq", a, b, MEM)
    assert isinstance(r, Fraction), f"{type(r).__name__} — float đã lọt vào"


def test_gia_tri_khong_hop_ti_van_chinh_xac():
    """Đường `(1,2,3)` với mặt `z=0`: sin² = 9/14 ⇒ cos² = 5/14. Hữu tỉ, dù
    góc thì không phải một số đẹp."""
    ln = Line3(v(0, 0, 0), v(1, 2, 3))
    assert cos_sq_line_plane(ln, P_XY) == Fraction(5, 14)


# ══ ⑤ SUY BIẾN — vector không phải bị TỪ CHỐI ═══════════════════════════
def test_chi_phuong_KHONG_thi_bi_tu_choi():
    """Một `Line3` chỉ phương 0 không có góc. Trả một con số ở đây là bịa."""
    with pytest.raises(GeometryError):
        cos_sq_giua(Line3(v(0, 0, 0), v(0, 0, 0)), OX)


def test_phap_tuyen_KHONG_thi_bi_tu_choi():
    with pytest.raises(GeometryError):
        cos_sq_giua(OX, Plane3(v(0, 0, 0), v(0, 0, 0)))


def test_cap_kieu_la_bi_tu_choi():
    with pytest.raises(GeometryError):
        cos_sq_giua(v(1, 0, 0), OX)


# ══ ⑥ HỒI QUY GÓC CÓ DẤU — không đụng tới ═══════════════════════════════
def test_angle_cos_co_dau_van_nguyen():
    """`angle_cos` là phép ĐO KHÁC, có dấu, chỉ nhận vectơ. Wave này không
    chạm nó — ca dưới đây là chốt cho lời khai ấy."""
    assert cos_between_vectors(v(1, 0, 0), v(1, 0, 1)) == Radical(
        Fraction(1, 2), 2)
    assert cos_between_vectors(v(1, 0, 0), v(-1, 0, 1)) == Radical(
        Fraction(-1, 2), 2)
    assert cos_between_vectors(v(1, 0, 0), v(0, 1, 0)) == 0


def test_angle_cos_van_TU_CHOI_line3_o_validator():
    """Đường thẳng không có chiều ⇒ không cho được dấu. Luật này không đổi."""
    ct = {
        "spec_version": "1.0", "title": "Góc có dấu trên đường thẳng",
        "description": "Ca phải bị từ chối.",
        "pedagogical_intent": "Đường thẳng không có chiều.",
        "memory_declarations": [{"name": "L", "type": "line3"},
                                {"name": "M", "type": "line3"},
                                {"name": "c", "type": "float"}],
        "statements": [{"kind": "assign", "target_var": "c",
                        "expr": {"kind": "measure", "quantity": "angle_cos",
                                 "of": "L", "wrt": "M"}}],
    }
    r = validate_semantic_program(ct)
    assert not r.ok and "vector" in (r.error or "").lower()


# ══ ⑦ §12 — TÊN BIẾN KHÔNG CÓ THẨM QUYỀN ════════════════════════════════
def _ct_do_goc(ten_bien: str, opcode: str) -> dict:
    return {
        "spec_version": "1.0", "title": "Góc giữa đường và mặt",
        "description": "Tên biến không quyết định ngữ nghĩa.",
        "pedagogical_intent": "Opcode mới là thẩm quyền.",
        "memory_declarations": [{"name": ten_bien, "type": "float"}],
        "statements": [
            {"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
             "model_assumption": "gốc"},
            {"kind": "declare_point", "target_var": "B", "at": [1, 0, 0],
             "model_assumption": "trục x"},
            {"kind": "declare_point", "target_var": "C", "at": [0, 1, 0],
             "model_assumption": "trục y"},
            {"kind": "construct_line", "target_var": "L",
             "through_a": "A", "through_b": "B"},
            {"kind": "construct_plane", "target_var": "P",
             "through": ["A", "B", "C"]},
            {"kind": "assign", "target_var": ten_bien,
             "expr": {"kind": "measure", "quantity": opcode,
                      "of": "L", "wrt": "P"}}],
    }


@pytest.mark.parametrize("ten", ["cos_goc_sq", "sin_goc_sq", "ket_qua", "x"])
def test_ten_bien_KHONG_doi_duoc_ngu_nghia(ten):
    """Đường `AB` nằm TRONG mặt `(ABC)` ⇒ góc 0° ⇒ cos² = 1, bất kể biến tên
    gì. `fp_5` đặt tên `cos_angle_SC_ABC_sq` và nhận sin² — tên nói một đằng,
    runtime làm một nẻo. Nay chỉ opcode có thẩm quyền."""
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )

    r = validate_semantic_program(_ct_do_goc(ten, "angle_cos_sq"))
    assert r.ok, r.error
    kq = SemanticProgramInterpreter().execute(r.spec)
    assert kq.final_memory[ten] == 1, (
        f"biến tên {ten!r} cho ra {kq.final_memory[ten]} — tên đã đổi được "
        "ngữ nghĩa")


# ══ ⑧ §11 — BỘ CHẤM tính lại ĐÚNG đại lượng ═════════════════════════════
def test_bo_cham_dung_CUNG_ham_voi_duong_thuc_thi():
    """Bộ chấm từng mang bản sao của phép phân phối — và bản sao mang cùng
    bug, nên nó xác nhận thay vì bác bỏ."""
    import inspect
    from pathlib import Path

    from tests.source_scan import than_ma

    from app.simulation.semantic_program import geometry_obligations as GO

    # `than_ma` BÓC chú thích và docstring bằng AST. Không bóc thì guard khớp
    # chính khối chú thích giải thích bản sửa — lỗi ấy đã tái phát năm lần
    # trong kho này, và `source_scan.py` ra đời vì nó.
    src = than_ma(Path(inspect.getfile(GO)))
    dau = src.index("def check_angle")
    than = src[dau:src.index("def ", dau + 5)]
    assert "cos_sq_giua" in than, "bộ chấm không dùng thẩm quyền chung"
    assert "sin_sq_line_plane" not in than, "bản sao cũ còn sót trong bộ chấm"


def test_bo_cham_BAC_BO_gia_tri_sin_binh():
    """Chốt hành vi, không chỉ chốt mã: một chương trình khai sin² cho cặp
    (đường, mặt) phải bị bộ chấm bác."""
    from app.simulation.semantic_program.geometry_obligations import check_angle

    class _Ob:
        container, witness = "L", "gia_tri"
        params = {"wrt": "P"}

        def describe(self):
            return "angle(L, P)"

    snap = {"L": OZ, "P": P_XY, "gia_tri": Fraction(1)}   # cos²(90°) = 0
    assert check_angle(snap, _Ob()) is not None, (
        "bộ chấm nhận một giá trị sai")
    snap["gia_tri"] = Fraction(0)
    assert check_angle(snap, _Ob()) is None
