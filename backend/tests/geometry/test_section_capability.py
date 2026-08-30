# -*- coding: utf-8 -*-
"""THIẾT DIỆN như một KẾT QUẢ HÌNH HỌC hạng nhất — kernel · so chu trình · C₂.

VÌ SAO CÓ FILE NÀY, nói bằng thứ đo được chứ không bằng cảm giác: trước
2026-08-30, checker duy nhất nhận một `Section` là `coplanar`, và `coplanar`
trên một thiết diện **gần như luôn xanh** — mọi đỉnh của nó sinh ra từ giao với
đúng MỘT mặt phẳng, nên chúng đồng phẳng theo định nghĩa. Một chương trình bỏ
sót đỉnh thứ tư của một thiết diện tứ giác vẫn qua cổng.

Ca `O` dưới đây là ca chứng minh: cùng một dữ liệu, `coplanar` nói ĐƯỢC còn
`section_matches` nói KHÔNG. Không có ca ấy thì "checker mới mạnh hơn" chỉ là
một lời khai.

Đáp án **kiểm tay**, không chép từ đầu ra kernel — chép thì test thành phép
lặp lại chính cài đặt đang kiểm.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry.exact import GeometryError, Vec3
from app.simulation.geometry.kernel import Plane3
from app.simulation.geometry.section import (
    Polyhedron,
    canonical_cycle,
    cross_section,
    same_section_cycle,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.postconditions import CHECKERS


def V(*t) -> Vec3:
    return Vec3(*(F(x) for x in t))


# ── HÌNH DỰNG SẴN, toạ độ chọn cho đáp án kiểm tay được ──────────────────
#: Tứ diện vuông tại A: A(0,0,0) B(3,0,0) C(0,3,0) S(0,0,3).
TU_DIEN = Polyhedron(
    vertices=(V(0, 0, 0), V(3, 0, 0), V(0, 3, 0), V(0, 0, 3)),
    faces=((0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 2, 3)),
)
#: Chóp tứ giác đều đáy vuông cạnh 2, đỉnh S(1,1,2).
CHOP = Polyhedron(
    vertices=(V(0, 0, 0), V(2, 0, 0), V(2, 2, 0), V(0, 2, 0), V(1, 1, 2)),
    faces=((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)),
)
#: Hình hộp 2×2×2, một góc ở gốc.
HOP = Polyhedron(
    vertices=(V(0, 0, 0), V(2, 0, 0), V(2, 2, 0), V(0, 2, 0),
              V(0, 0, 2), V(2, 0, 2), V(2, 2, 2), V(0, 2, 2)),
    faces=((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
           (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)),
)

#: Mặt phẳng ngang `z = h`.
def NGANG(h) -> Plane3:
    return Plane3(V(0, 0, h), V(0, 0, 1))


# ══ A–H · KERNEL ═════════════════════════════════════════════════════════
def test_A_tu_dien_cho_thiet_dien_TAM_GIAC():
    """`x+y+z = 3/2` cắt ba cạnh xuất phát từ A ⇒ tam giác trung điểm.

    Kiểm tay: AB đi từ (0,0,0) tới (3,0,0), tổng toạ độ chạy `0 → 3`, bằng
    `3/2` tại trung điểm ⇒ (3/2,0,0). AC và AS đối xứng. Mặt BCS có cả ba đỉnh
    ở tổng `3 > 3/2` nên không bị cắt — đúng 3 cạnh, đúng 3 đỉnh.

    ⚠️ KHÔNG dùng `x+y+z = 3`: mặt phẳng ấy CHỨA TRỌN mặt BCS, tức ca D chứ
    không phải ca A. Bản nháp đầu của test này đã sai đúng chỗ đó.
    """
    s = cross_section(TU_DIEN, Plane3(V(F(3, 2), 0, 0), V(1, 1, 1)))
    assert len(s.polygon) == 3
    assert same_section_cycle(
        s.polygon, [V(F(3, 2), 0, 0), V(0, F(3, 2), 0), V(0, 0, F(3, 2))])


def test_B_chop_cho_thiet_dien_TU_GIAC():
    """`z = 1` cắt bốn cạnh bên của chóp ⇒ tứ giác, mỗi đỉnh là trung điểm.

    Kiểm tay: cạnh AS đi từ (0,0,0) tới (1,1,2); tại `z = 1` là `t = 1/2` ⇒
    (1/2, 1/2, 1). Ba cạnh còn lại đối xứng.
    """
    s = cross_section(CHOP, NGANG(1))
    assert len(s.polygon) == 4
    assert same_section_cycle(
        s.polygon,
        [V(F(1, 2), F(1, 2), 1), V(F(3, 2), F(1, 2), 1),
         V(F(3, 2), F(3, 2), 1), V(F(1, 2), F(3, 2), 1)],
    )


def test_C_hop_cho_thiet_dien_TU_GIAC():
    """`z = 1` cắt hộp ngang ⇒ hình vuông cạnh 2 ở độ cao 1."""
    s = cross_section(HOP, NGANG(1))
    assert len(s.polygon) == 4
    assert same_section_cycle(
        s.polygon,
        [V(0, 0, 1), V(2, 0, 1), V(2, 2, 1), V(0, 2, 1)],
    )


def test_D_mat_phang_TRUNG_mot_mat_cua_khoi_thi_KHONG_HO_TRO():
    """Giới hạn ĐÃ KHAI, không phải bug: `z = 0` trùng đáy hộp.

    Thiết diện khi ấy **là chính mặt đáy** — một kết quả hợp lệ về toán, nhưng
    hệ chưa dựng: `_canh_tren_mat` gặp một mặt có >2 điểm chung và ném. Ghi
    thành test để giới hạn này không tự mục đi thành "chắc là chạy được".
    """
    with pytest.raises(GeometryError) as e:
        cross_section(HOP, NGANG(0))
    assert e.value.code == "CONTAINED_INFINITE_INTERSECTION"


def test_E_mat_phang_KHONG_CHAM_khoi():
    with pytest.raises(GeometryError) as e:
        cross_section(HOP, NGANG(9))
    assert e.value.code == "PLANE_DOES_NOT_CUT"
    assert "không có điểm chung" in str(e.value)


def test_F_chi_cham_MOT_DINH_co_ma_rieng():
    """`z = 2` chạm đúng đỉnh S của chóp. KHÁC ca E: có điểm chung."""
    with pytest.raises(GeometryError) as e:
        cross_section(CHOP, NGANG(2))
    assert e.value.code == "PLANE_TOUCHES_VERTEX"


def test_G_chi_cham_MOT_CANH_co_ma_rieng():
    """`y + z = 0` chứa cạnh AB của tứ diện; C và S cùng phía dương.

    Kiểm tay: A(0,0,0) → 0, B(3,0,0) → 0, C(0,3,0) → 3, S(0,0,3) → 3. Đúng hai
    đỉnh nằm trên mặt phẳng, và AB là cạnh thật của khối.
    """
    with pytest.raises(GeometryError) as e:
        cross_section(TU_DIEN, Plane3(V(0, 0, 0), V(0, 1, 1)))
    assert e.value.code == "PLANE_TOUCHES_EDGE"


def test_H_ba_ma_suy_bien_KHONG_duoc_gop_lam_mot():
    """Ba ca E · F · G phải cho BA mã khác nhau.

    Gộp lại là vứt đi thông tin kernel đã có: *"mặt phẳng của em đi qua đỉnh
    S"* là một lời chẩn đoán dạy được, *"không cắt"* thì không.
    """
    ma = set()
    for khoi, pl in ((HOP, NGANG(9)), (CHOP, NGANG(2)),
                     (TU_DIEN, Plane3(V(0, 0, 0), V(0, 1, 1)))):
        with pytest.raises(GeometryError) as e:
            cross_section(khoi, pl)
        ma.add(e.value.code)
    assert len(ma) == 3, f"ba ca suy biến khác nhau mà chỉ có {ma}"


def test_H2_thiet_dien_KHONG_BAO_GIO_co_dinh_trung():
    """Hậu điều kiện của chính `cross_section`, trên cả ba khối."""
    for khoi in (TU_DIEN, CHOP, HOP):
        for h in (F(1, 2), 1, F(3, 2)):
            try:
                s = cross_section(khoi, NGANG(h))
            except GeometryError:
                continue
            assert len(set(s.polygon)) == len(s.polygon)
            assert len(s.polygon) >= 3


def test_H3_moi_dinh_thiet_dien_NAM_TREN_mat_phang_cat():
    pl = Plane3.through(V(2, 0, 0), V(0, 2, 0), V(0, 0, 2))
    s = cross_section(HOP, pl)
    assert all(pl.signed_eval(v) == 0 for v in s.polygon)


def test_H4_canh_noi_thanh_VONG_KIN():
    s = cross_section(CHOP, NGANG(1))
    for i in range(len(s.steps)):
        assert s.steps[i].b == s.steps[(i + 1) % len(s.steps)].a


# ══ SO CHU TRÌNH (§6) ════════════════════════════════════════════════════
P, Q, R, T = V(0, 0, 0), V(1, 0, 0), V(1, 1, 0), V(0, 1, 0)


def test_chu_trinh_XOAY_la_cung_mot_thiet_dien():
    assert same_section_cycle([P, Q, R, T], [Q, R, T, P])
    assert same_section_cycle([P, Q, R, T], [T, P, Q, R])


def test_chu_trinh_DAO_HUONG_la_cung_mot_thiet_dien():
    assert same_section_cycle([P, Q, R, T], [T, R, Q, P])


def test_chu_trinh_NOI_CHEO_la_thiet_dien_KHAC():
    """`[P,R,Q,T]` dùng đúng bốn đỉnh ấy nhưng nối chéo — tứ giác KHÁC."""
    assert not same_section_cycle([P, Q, R, T], [P, R, Q, T])


def test_chu_trinh_THIEU_DINH_la_thiet_dien_KHAC():
    assert not same_section_cycle([P, Q, R, T], [P, Q, R])


def test_dang_chuan_KHONG_dung_float():
    """Khoá sắp xếp phải là `Fraction`. Một `float` lọt vào là mở lại cửa sai số."""
    import inspect

    from app.simulation.geometry import section as S

    src = inspect.getsource(S._khoa) + inspect.getsource(S.canonical_cycle)
    for cam in ("float(", "math.", "round(", "** 0.5"):
        assert cam not in src, f"`{cam}` không được có trong đường so chu trình"


def test_dang_chuan_ON_DINH_voi_moi_cach_viet():
    """2n cách viết cùng một tứ giác ⇒ đúng MỘT dạng chuẩn."""
    goc = [P, Q, R, T]
    viet = [goc[i:] + goc[:i] for i in range(4)]
    viet += [list(reversed(v)) for v in viet]
    assert len({canonical_cycle(v) for v in viet}) == 1


# ══ I–O · CHECKER `section_matches` ══════════════════════════════════════
def _ob(container="td", solid="khoi", plane="mp", **them):
    return Obligation(kind="section_matches", container=container,
                      params={"solid": solid, "plane": plane, **them})


#: Thiết diện ĐÚNG của `CHOP` với `z = 1` — kiểm tay ở ca B.
DUNG = [V(F(1, 2), F(1, 2), 1), V(F(3, 2), F(1, 2), 1),
        V(F(3, 2), F(3, 2), 1), V(F(1, 2), F(3, 2), 1)]


def _cham(poly, khoi=CHOP, pl=None, ob=None):
    snap = {"td": tuple(poly), "khoi": khoi, "mp": pl or NGANG(1)}
    return CHECKERS["section_matches"](snap, ob or _ob())


def test_I_thiet_dien_DUNG_thi_PASS():
    assert _cham(DUNG) is None


def test_J_XOAY_chu_trinh_van_PASS():
    assert _cham(DUNG[2:] + DUNG[:2]) is None


def test_K_DAO_HUONG_van_PASS():
    assert _cham(list(reversed(DUNG))) is None


def test_L_THIEU_mot_dinh_thi_FAIL():
    loi = _cham(DUNG[:3])
    assert loi is not None and "3 đỉnh" in loi


def test_M_THUA_mot_dinh_thi_FAIL():
    """Thêm tâm của thiết diện — vẫn đồng phẳng, vẫn nằm trên `z = 1`."""
    assert _cham(DUNG + [V(1, 1, 1)]) is not None


def test_N_SAI_MAT_PHANG_CAT_thi_FAIL():
    """Đa giác là thiết diện thật của `z = 1`, nhưng nghĩa vụ hỏi `z = 1/2`."""
    loi = _cham(DUNG, pl=NGANG(F(1, 2)))
    assert loi is not None


def test_N2_SAI_KHOI_thi_FAIL():
    loi = _cham(DUNG, khoi=HOP)
    assert loi is not None


def test_O_DONG_PHANG_DUNG_nhung_DA_GIAC_SAI_thi_FAIL():
    """CA CHỨNG MINH — `coplanar` xanh, `section_matches` đỏ, cùng dữ liệu.

    Bốn điểm dưới đây nằm trọn trên `z = 1` (nên đồng phẳng, và nằm đúng mặt
    phẳng cắt), nhưng chúng là một hình vuông NHỎ HƠN nằm bên trong thiết diện
    thật. Đây đúng hình dạng lỗi mà `coplanar` không thấy được.
    """
    gia = [V(F(3, 4), F(3, 4), 1), V(F(5, 4), F(3, 4), 1),
           V(F(5, 4), F(5, 4), 1), V(F(3, 4), F(5, 4), 1)]
    snap = {"td": tuple(gia), "khoi": CHOP, "mp": NGANG(1)}

    coplanar_noi = CHECKERS["coplanar"](
        snap, Obligation(kind="coplanar", container="td", params={}))
    section_noi = CHECKERS["section_matches"](snap, _ob())

    assert coplanar_noi is None, "tiền đề của ca này: `coplanar` PHẢI xanh"
    assert section_noi is not None, "checker mới phải bắt được"
    assert "cùng số đỉnh" in section_noi


def test_O2_cung_da_giac_ay_KHONG_bi_coplanar_bat_o_bat_ky_hinh_nao():
    """Khái quát ca O: `coplanar` mù với MỌI đa giác con nằm trên mặt cắt."""
    for k in (F(1, 4), F(1, 2), F(3, 4)):
        gia = [V(1 + k * (v.x - 1), 1 + k * (v.y - 1), 1) for v in DUNG]
        snap = {"td": tuple(gia), "khoi": CHOP, "mp": NGANG(1)}
        assert CHECKERS["coplanar"](
            snap, Obligation(kind="coplanar", container="td", params={})) is None
        assert CHECKERS["section_matches"](snap, _ob()) is not None


def test_thieu_toan_hang_thi_MUC_YEU_chu_khong_KET_TOI():
    """Nghĩa vụ không khai `solid`/`plane` ⇒ `None`, không phải FAIL.

    Khai thiếu là chuyện của C₁a. Kết tội ở đây là đổ lỗi sai tầng.
    """
    snap = {"td": tuple(DUNG)}
    ob = Obligation(kind="section_matches", container="td", params={})
    assert CHECKERS["section_matches"](snap, ob) is None


def test_nghia_vu_tro_sai_KIEU_thi_noi_dung_cho_sai():
    snap = {"td": tuple(DUNG), "khoi": NGANG(1), "mp": NGANG(1)}
    assert "không phải một KHỐI" in CHECKERS["section_matches"](snap, _ob())


def test_mat_phang_nghia_vu_KHONG_CAT_thi_bao_MA_SUY_BIEN():
    """Đề bảo cắt, kernel bảo không cắt ⇒ trả đúng mã, không nuốt thành
    'không khớp' — mã suy biến là lời chẩn đoán hữu ích nhất ở đây."""
    loi = _cham(DUNG, pl=NGANG(9))
    assert loi is not None and "PLANE_DOES_NOT_CUT" in loi


def test_checker_KHONG_doc_gia_tri_chuong_trinh_khai():
    """C₂ tự dựng lại. Một `Section` mang polygon bịa vẫn phải bị bắt."""
    from app.simulation.geometry.section import Section

    that = cross_section(CHOP, NGANG(1))
    bia = Section(polygon=tuple(DUNG[:3]), steps=that.steps)
    snap = {"td": bia, "khoi": CHOP, "mp": NGANG(1)}
    assert CHECKERS["section_matches"](snap, _ob()) is not None


def test_section_matches_CO_TRONG_taxonomy_va_CO_checker():
    from app.simulation.semantic_program.obligations import (
        OBLIGATION_KINDS,
        accepts_container_type,
        has_server_owned_checker,
    )

    assert "section_matches" in OBLIGATION_KINDS
    assert has_server_owned_checker("section_matches")
    assert accepts_container_type("section_matches", "section")
    assert accepts_container_type("section_matches", "polygon3")
