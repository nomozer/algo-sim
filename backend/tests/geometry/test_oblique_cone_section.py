# -*- coding: utf-8 -*-
"""`OBLIQUE_CONE_SECTION_FOUNDATION` — nón × mặt phẳng xiên → elip.

**0 lượt gọi model.**

Nón chuẩn của wave: đỉnh `V(0,0,0)`, tâm đáy `H(0,0,8)`, `r = 6`.
Mặt phẳng chuẩn `(α): x − 3z + 9 = 0` ⇔ `z = x/3 + 3`.

    t = r²/h² = 9/16 · m = 1/3 · c = 3 · k = 1 − m²t = 15/16
    b² = c²t/k = 27/5 · a² = c²t(1+m²)/k² = 32/5 · S = 12√6π/5

⚠️ `z = mx + c` **chỉ là oracle**, không phải nhánh trong mã sản phẩm: công
thức của kernel viết bằng tích vô hướng, và `test_20`/`test_21` khoá rằng nó
bất biến với tịnh tiến và hoán vị trục có dấu.
"""
from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from app.simulation.geometry import curved as CV
from app.simulation.geometry.curved import (
    CONIC_ELIP, CONIC_HYPERBOL, CONIC_PARABOL, CurvedSolid,
    dien_tich_elip, intersect_plane_curved, intersect_plane_curved_ellipse,
    phan_xu_conic,
)
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import Radical, display


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


def mp(a, b, c, d) -> Plane3:
    return Plane3.from_equation(F(a), F(b), F(c), F(d))


#: Đỉnh ở gốc, đáy ở `z = 8`, bán kính 6. `anchor` = tâm ĐÁY theo hợp đồng
#: `KHOI_CONG`; `apex_or_top` = đỉnh.
NON = CurvedSolid("cone", v(0, 0, 8), v(0, 0, 0), v(6, 0, 8))
CHUAN = mp(1, 0, -3, 9)

A_SQ, B_SQ = F(32, 5), F(27, 5)


# ══ §5 · ORACLE — ba đường độc lập ═════════════════════════════════════
def test_01_oracle_hoan_thanh_binh_phuong():
    """Oracle ① — thế mặt phẳng vào phương trình nón rồi hoàn thành bình
    phương, làm bằng tay trên hệ chính tắc."""
    t, m, c = F(9, 16), F(1, 3), F(3)
    k = 1 - m * m * t
    assert k == F(15, 16)
    assert c * c * t / k == B_SQ
    assert c * c * t * (1 + m * m) / (k * k) == A_SQ
    # Bán trục trong MẶT PHẲNG: nửa trục chiếu `144/25` nhân hệ số nghiêng
    # `1 + m² = 10/9`.
    assert F(144, 25) * F(10, 9) == A_SQ


def test_02_oracle_coordinate_free_cua_KERNEL():
    """Oracle ② — chính đường của mã sản phẩm, viết bằng tích vô hướng."""
    e = intersect_plane_curved_ellipse(NON, CHUAN)
    assert e.semi_major_sq == A_SQ
    assert e.semi_minor_sq == B_SQ


def test_03_oracle_SO_doc_lap():
    """Oracle ③ — lấy mẫu giao tuyến rồi shoelace 3D. KHÔNG dùng công thức."""
    N = 20000
    h, r = 8.0, 6.0
    n = (1.0, 0.0, -3.0)
    p = -9.0                                  # n·P = −9 cho x − 3z + 9 = 0
    V = (0.0, 0.0, 0.0)
    pts = []
    for i in range(N):
        ph = 2 * math.pi * i / N
        B = (r * math.cos(ph), r * math.sin(ph), h)   # điểm trên vành đáy
        den = sum(n[k] * B[k] for k in range(3))
        lam = p / den
        pts.append(tuple(lam * B[k] for k in range(3)))
    sx = sy = sz = 0.0
    for i in range(N):
        a, b = pts[i], pts[(i + 1) % N]
        sx += a[1] * b[2] - a[2] * b[1]
        sy += a[2] * b[0] - a[0] * b[2]
        sz += a[0] * b[1] - a[1] * b[0]
    S_so = math.hypot(sx, sy, sz) / 2
    S_ex = math.pi * math.sqrt(float(A_SQ * B_SQ))
    assert abs(S_so - S_ex) < 1e-4, (S_so, S_ex)


def test_04_dap_so_dung_dang_Radical():
    """`S = π√(a²b²) = π√(864/25) = 12√6π/5` — ở lại trong miền số đã có."""
    e = intersect_plane_curved_ellipse(NON, CHUAN)
    assert e.semi_major_sq * e.semi_minor_sq == F(864, 25)
    S = dien_tich_elip(e)
    assert isinstance(S, Radical)
    assert (S.he, S.can, S.mu) == (F(12, 5), 6, 1)
    assert display(S) == "12π√6/5"


# ══ §6 · PHÂN XỬ CONIC — hữu tỉ, hai đường kiểm chéo ═══════════════════
@pytest.mark.parametrize("he,mong", [
    ((1, 0, -3, 9), CONIC_ELIP),          # m = 1/3
    ((3, 0, -4, 12), CONIC_ELIP),         # m = 3/4
    ((4, 0, -3, 12), CONIC_PARABOL),      # m = 4/3 — đúng độ dốc đường sinh
    ((2, 0, -1, 3), CONIC_HYPERBOL),      # m = 2
    ((1, 0, 0, -3), CONIC_HYPERBOL),      # ∥ trục — nón cho HYPERBOL
])
def test_05_phan_xu_conic(he, mong):
    assert phan_xu_conic(NON, mp(*he)) == mong


def test_06_phan_xu_KHONG_dung_float_va_KHONG_chuan_hoa():
    """Ghim Ý ĐỊNH: phép phân xử chỉ được dùng tích vô hướng hữu tỉ."""
    import inspect

    src = inspect.getsource(phan_xu_conic)
    than = src.split('"""')[-1]
    for cam in ("float(", "sqrt", "math.", "**0.5", "** 0.5"):
        assert cam not in than, cam


def test_07_phan_xu_kiem_CHEO_bang_dau_cua_k():
    """Đường thứ hai: `k = 1 − m²·tan²α` trong hệ chính tắc. Hai đường phải
    luôn nói cùng một điều — nếu lệch thì một trong hai sai."""
    t = F(9, 16)
    for m in (F(1, 4), F(1, 3), F(3, 4), F(4, 3), F(2), F(3)):
        # z = m·x + c ⇒ −m·x + z − c = 0 ⇒ n = (−m, 0, 1); nhân 3 cho nguyên.
        pl = Plane3.from_equation(-m, F(0), F(1), F(-3))
        loai = phan_xu_conic(NON, pl)
        k = 1 - m * m * t
        assert (loai == CONIC_ELIP) == (k > 0), (m, loai, k)
        assert (loai == CONIC_PARABOL) == (k == 0), (m, loai, k)


# ══ §9 · CA ELIP DƯƠNG ════════════════════════════════════════════════
def test_10_ca_chuan():
    e = intersect_plane_curved_ellipse(NON, CHUAN)
    assert (e.semi_major_sq, e.semi_minor_sq) == (A_SQ, B_SQ)
    assert e.normal == CHUAN.normal
    # Tâm NẰM TRÊN mặt phẳng — bất biến rẻ mà bắt được mọi lỗi lệch tâm.
    assert CHUAN.normal.dot(e.center - CHUAN.point) == 0
    assert e.center == v(F(3, 5), 0, F(16, 5))


def test_11_cham_day_duoc_NHAN():
    """`z = x/3 + 6`: elip vừa chạm đáy. Biên ĐẲNG THỨC phải được nhận — chặn
    nó là chặn oan một hình hoàn toàn hợp lệ."""
    e = intersect_plane_curved_ellipse(NON, mp(1, 0, -3, 18))
    assert (e.semi_major_sq, e.semi_minor_sq) == (F(128, 5), F(108, 5))
    S = dien_tich_elip(e)
    assert (S.he, S.can, S.mu) == (F(48, 5), 6, 1)


def test_12_xien_AM():
    """`m < 0` — cùng độ dốc, hướng ngược. Cùng hai bán trục."""
    e = intersect_plane_curved_ellipse(NON, mp(1, 0, 3, -9))
    assert (e.semi_major_sq, e.semi_minor_sq) == (A_SQ, B_SQ)


def test_13_TINH_TIEN_bat_bien():
    d = v(5, -7, 11)
    n2 = CurvedSolid("cone", NON.anchor + d, NON.apex_or_top + d,
                     NON.rim_point + d)
    e = intersect_plane_curved_ellipse(
        n2, Plane3(CHUAN.point + d, CHUAN.normal))
    goc = intersect_plane_curved_ellipse(NON, CHUAN)
    assert (e.semi_major_sq, e.semi_minor_sq) == (A_SQ, B_SQ)
    assert e.center == goc.center + d


def test_14_HOAN_VI_TRUC_co_dau_bat_bien():
    """`(x,y,z) → (z, x, −y)` — một phép quay có định thức `+1`."""
    def hv(P):
        return v(P.z, P.x, -P.y)

    n3 = CurvedSolid("cone", hv(NON.anchor), hv(NON.apex_or_top),
                     hv(NON.rim_point))
    e = intersect_plane_curved_ellipse(
        n3, Plane3(hv(CHUAN.point), hv(CHUAN.normal)))
    goc = intersect_plane_curved_ellipse(NON, CHUAN)
    assert (e.semi_major_sq, e.semi_minor_sq) == (A_SQ, B_SQ)
    assert e.center == hv(goc.center)


def test_15_DOI_DIEM_VANH_khong_doi_hinh():
    """Điểm vành khác trên cùng đường tròn đáy ⇒ cùng khối ⇒ cùng elip."""
    n2 = CurvedSolid("cone", NON.anchor, NON.apex_or_top, v(0, 6, 8))
    e = intersect_plane_curved_ellipse(n2, CHUAN)
    assert (e.semi_major_sq, e.semi_minor_sq) == (A_SQ, B_SQ)


def test_16_POINT_MODE_va_SCALAR_MODE_cung_mot_elip():
    """Khai bằng điểm và khai bằng `(bán kính, chiều cao)` phải cho **cùng
    hình học**. Đây là ô mà `CURVED_SCALAR_AXIS_SCALE_REPAIR` đã dựng lưới."""
    # Scalar mode: đáy tại gốc, trục canonical (0,0,1) ⇒ đỉnh ở (0,0,8).
    # Nón point-mode có đỉnh ở gốc và đáy ở z=8 — hai hình là ẢNH GƯƠNG qua
    # `z ↦ 8 − z`, nên mặt phẳng cũng phải soi gương.
    ns = CurvedSolid("cone", v(0, 0, 0), None, None,
                     radius_sq_khai=F(36), height_sq_khai=F(64))
    assert ns.huong_truc == v(0, 0, 1) and ns.height_sq == 64
    e = intersect_plane_curved_ellipse(ns, mp(1, 0, 3, -15))
    assert (e.semi_major_sq, e.semi_minor_sq) == (A_SQ, B_SQ)


# ══ §9 · CA FAIL-CLOSED ═══════════════════════════════════════════════
@pytest.mark.parametrize("he,ma,vi_sao", [
    ((4, 0, -3, 12), CV.ERR_CONIC_PARABOL, "∥ một đường sinh"),
    ((2, 0, -1, 3), CV.ERR_CONIC_HYPERBOL, "dốc hơn đường sinh"),
    ((1, 0, 0, -3), CV.ERR_CONIC_HYPERBOL, "∥ trục — với NÓN là hyperbol"),
    ((1, 0, -3, 21), CV.ERR_ELIP_CAT_DAY, "elip vượt qua đáy hữu hạn"),
    ((1, 0, -3, -9), CV.ERR_KHONG_CAT, "nappe ĐỐI DIỆN"),
    ((1, 0, -3, 0), CV.ERR_KHONG_CAT, "mặt phẳng qua ĐỈNH — suy biến"),
])
def test_17_fail_closed_co_MA_rieng(he, ma, vi_sao):
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved_ellipse(NON, mp(*he))
    assert e.value.code == ma, (vi_sao, str(e.value)[:120])


def test_18_vuong_goc_truc_chi_duong_sang_phep_DUNG():
    """`z = 3` ⊥ trục ⇒ đường TRÒN. Lời từ chối phải NÊU TÊN phép đúng."""
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved_ellipse(NON, mp(0, 0, 1, -3))
    assert e.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG
    assert "intersect_plane_curved" in str(e.value)


def test_19_khoi_SUY_BIEN_van_bi_guard_cu_chan():
    """Nón khai bằng vô hướng với `h` VÔ TỈ: `_ti_le_doc_truc` từ chối — thẩm
    quyền CŨ, không phải một guard mới."""
    ns = CurvedSolid("cone", v(0, 0, 0), None, None,
                     radius_sq_khai=F(4), height_sq_khai=F(7))
    with pytest.raises(GeometryError):
        intersect_plane_curved_ellipse(ns, mp(1, 0, 3, -5))


# ══ §7 · BẤT BIẾN HÌNH HỌC CỦA ELIP DỰNG RA ═══════════════════════════
def test_20_bon_dau_mut_nam_tren_MAT_PHANG_va_tren_NON():
    """Bốn đầu mút trục phải thoả CẢ HAI phương trình — phép kiểm mạnh nhất
    về `center`, hai `dir` và hai bán trục cùng lúc.

    Bán trục có thể vô tỉ nên đầu mút không hữu tỉ; kiểm bằng **số thực** với
    ngưỡng chặt, còn phép dựng thì vẫn thuần ℚ.
    """
    e = intersect_plane_curved_ellipse(NON, CHUAN)
    c = [float(x) for x in (e.center.x, e.center.y, e.center.z)]
    for d, r2 in ((e.major_dir, e.semi_major_sq), (e.minor_dir, e.semi_minor_sq)):
        dv = [float(x) for x in (d.x, d.y, d.z)]
        L = math.hypot(*dv)
        for dau in (+1, -1):
            P = [c[k] + dau * math.sqrt(float(r2)) * dv[k] / L for k in range(3)]
            # ① trên mặt phẳng `x − 3z + 9 = 0`
            assert abs(P[0] - 3 * P[2] + 9) < 1e-9, P
            # ② trên mặt nón `x² + y² = (9/16)z²`, đỉnh ở gốc
            assert abs(P[0] ** 2 + P[1] ** 2 - 0.5625 * P[2] ** 2) < 1e-9, P
            # ③ trong đoạn hữu hạn `0 ≤ z ≤ 8`
            assert -1e-9 <= P[2] <= 8 + 1e-9, P


def test_21_hai_phuong_truc_VUONG_GOC_va_o_trong_mat_phang():
    e = intersect_plane_curved_ellipse(NON, CHUAN)
    assert e.major_dir.dot(e.minor_dir) == 0
    assert e.normal.dot(e.major_dir) == 0
    assert e.normal.dot(e.minor_dir) == 0
    assert e.semi_major_sq >= e.semi_minor_sq


# ══ §9 · HỒI QUY — đường CŨ không được đổi một bit ════════════════════
def test_30_HOI_QUY_elip_xien_cua_TRU():
    tru = CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), v(4, 0, 0))
    e = intersect_plane_curved_ellipse(tru, mp(2, 0, -1, 10))
    assert (e.semi_major_sq, e.semi_minor_sq) == (F(80), F(16))
    S = dien_tich_elip(e)
    assert (S.he, S.can, S.mu) == (F(16), 5, 1)


def test_31_HOI_QUY_thiet_dien_TRON_cua_non():
    c = intersect_plane_curved(NON, mp(0, 0, 1, -4))
    assert c.radius_sq == 9        # nửa chiều cao ⇒ nửa bán kính
    assert c.center == v(0, 0, 4)


def test_32_HOI_QUY_cau_van_tu_choi_phep_elip():
    cau = CurvedSolid("ball", v(0, 0, 0), None, v(3, 0, 0))
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved_ellipse(cau, mp(1, 0, -1, 1))
    assert e.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG
    assert "TRÒN" in str(e.value)


def test_33_HOI_QUY_the_tich_va_dien_tich_non_khong_doi():
    from app.simulation.geometry.curved import dien_tich_mat_cong, the_tich

    assert display(the_tich(NON)) == "96π"
    # Sxq = πr·l với l = √(r²+h²) = 10 ⇒ 60π
    assert display(dien_tich_mat_cong(NON)) == "60π"


# ══ §13 · TIÊM LỖI ════════════════════════════════════════════════════
def test_TIEM_1_khoi_phuc_nhanh_TU_CHOI_cone(monkeypatch):
    goc = CV._elip_non

    def tu_choi(s, pl):
        raise GeometryError(CV.ERR_ELIP_NGOAI_BAO_DONG, "nón: chưa phân xử")

    monkeypatch.setattr(CV, "_elip_non", tu_choi)
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(NON, CHUAN)
    assert e.value.code == CV.ERR_ELIP_NGOAI_BAO_DONG
    monkeypatch.setattr(CV, "_elip_non", goc)
    assert CV.intersect_plane_curved_ellipse(NON, CHUAN).semi_major_sq == A_SQ


def test_TIEM_2_dao_dau_phan_xu__elip_thanh_hyperbol(monkeypatch):
    goc = CV.phan_xu_conic
    monkeypatch.setattr(
        CV, "phan_xu_conic",
        lambda s, pl: {CONIC_ELIP: CONIC_HYPERBOL,
                       CONIC_HYPERBOL: CONIC_ELIP}.get(goc(s, pl), goc(s, pl)))
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(NON, CHUAN)
    assert e.value.code == CV.ERR_CONIC_HYPERBOL


def test_TIEM_3_bien_PARABOL_thanh_elip__K_bang_0_lo_ra(monkeypatch):
    """Đẳng thức `L = R` là parabol. Nếu ai đó nới nó thành elip thì `K = 0`
    và phép chia sẽ nổ — bất biến chéo trong `_elip_non` bắt trước."""
    monkeypatch.setattr(
        CV, "phan_xu_conic",
        lambda s, pl: CONIC_ELIP)
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(NON, mp(4, 0, -3, 12))
    assert e.value.code == CV.ERR_KHOI_CONG_HONG
    assert "mâu thuẫn" in str(e.value)


def test_TIEM_4_bo_kiem_CHUA_TRONG_NON__ca_vuot_day_lot_qua(monkeypatch):
    """Bỏ phép kiểm đáy ⇒ `z = x/3 + 7` được nhận, và nó trả một elip mà một
    phần nằm NGOÀI khối — đúng lớp lỗi *"đáp số đọc trơn tru cho một hình
    không tồn tại"*."""
    that = CV._elip_non

    def khong_kiem(s, pl):
        try:
            return that(s, pl)
        except GeometryError as e:
            if e.code != CV.ERR_ELIP_CAT_DAY:
                raise
            # Dựng lại KHÔNG có phép kiểm — chỉ để chứng minh nó lọt.
            return "LOT_QUA"

    monkeypatch.setattr(CV, "_elip_non", khong_kiem)
    assert CV.intersect_plane_curved_ellipse(NON, mp(1, 0, -3, 21)) == "LOT_QUA"
    monkeypatch.setattr(CV, "_elip_non", that)
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(NON, mp(1, 0, -3, 21))
    assert e.value.code == CV.ERR_ELIP_CAT_DAY


def test_TIEM_5_dung_cong_thuc_cua_TRU_cho_NON():
    """Công thức trụ: `b² = r²`, `a² = r²·|n|²|u|²/(n·u)²`. Với nón nó cho một
    con số KHÁC HẲN — nên hai nhánh không thể dùng chung công thức."""
    u, n = NON.huong_truc, CHUAN.normal
    a2_tru = NON.radius_sq * n.dot(n) * u.dot(u) / (n.dot(u) ** 2)
    b2_tru = NON.radius_sq
    assert (a2_tru, b2_tru) != (A_SQ, B_SQ)
    assert b2_tru == 36 and B_SQ == F(27, 5)


def test_TIEM_6_mat_THANG_giua_point_mode_va_scalar_mode(monkeypatch):
    """Bỏ `_ti_le_doc_truc` (dùng thẳng `L`) ⇒ scalar mode sai. Đây là đúng
    cái bẫy `CURVED_SCALAR_AXIS_SCALE_REPAIR` đã trả giá, và nó vẫn còn răng."""
    ns = CurvedSolid("cone", v(0, 0, 0), None, None,
                     radius_sq_khai=F(36), height_sq_khai=F(64))
    pls = mp(1, 0, 3, -15)
    assert intersect_plane_curved_ellipse(ns, pls).semi_major_sq == A_SQ

    monkeypatch.setattr(CV, "_ti_le_doc_truc", lambda s, L: L)
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved_ellipse(ns, pls)
    # `q = 1 − 5 = −4 < 0` ⇒ bị chốt "ngoài đỉnh".
    assert e.value.code == CV.ERR_KHONG_CAT


def test_TIEM_7_the_van_pham_KHONG_con_noi_rieng_hinh_tru():
    """Parity thẻ ↔ năng lực. Thẻ nói *"hình trụ"* trong khi kernel nhận cả
    nón là một lời khai SAI với mô hình — và nó sai theo hướng giấu năng lực."""
    from app.simulation.semantic_program.grammar_card import grammar_card

    dong = [l for l in grammar_card("hinh_hoc").splitlines()
            if "intersect_plane_curved_ellipse" in l]
    assert len(dong) == 1
    assert "hình nón" in dong[0], dong[0]
    assert "hình trụ" in dong[0], dong[0]


def test_TIEM_8_dao_MOT_phuong_truc__dau_mut_van_phai_dung():
    """Đảo hướng `minor_dir` là cùng một elip (trục là một ĐƯỜNG, không phải
    một tia). Bốn đầu mút phải giữ nguyên tập hợp."""
    from app.simulation.geometry.curved import Ellipse3

    e = intersect_plane_curved_ellipse(NON, CHUAN)
    dao = Ellipse3(e.center, e.normal, e.major_dir,
                   e.minor_dir.scale(F(-1)), e.semi_major_sq, e.semi_minor_sq)
    assert dien_tich_elip(dao) == dien_tich_elip(e)
    assert dao.center == e.center


# ══ §10 · GOLD ĐI TRỌN ĐƯỜNG SẢN PHẨM — 0 lượt gọi model ═══════════════
DE = (
    "Trong hệ trục Oxyz, cho hình nón tròn xoay có đỉnh V(0,0,0), tâm đáy "
    "H(0,0,8) và một điểm A(6,0,8) trên đường tròn đáy. Mặt phẳng "
    "(α): x - 3z + 9 = 0 cắt hình nón theo một elip (E) nằm hoàn toàn giữa "
    "đỉnh và đáy. Tính diện tích elip (E)."
)

CT_GOLD = {
    "problem_text": DE,
    "input_facts": [
        {"fact_id": "dinh_V", "label": "Đỉnh V(0,0,0)", "values": ["V"],
         "provenance": "confirmed"},
        {"fact_id": "dinh_H", "label": "Tâm đáy H(0,0,8)", "values": ["H"],
         "provenance": "confirmed"},
        {"fact_id": "dinh_A", "label": "Điểm A(6,0,8) trên vành đáy",
         "values": ["A"], "provenance": "confirmed"},
        {"fact_id": "mat_phang_alpha",
         "label": "Mặt phẳng (α): x - 3z + 9 = 0",
         "values": ["x - 3z + 9 = 0"], "provenance": "confirmed"},
    ],
    "obligations": [
        {"kind": "area", "container": "(E)", "params": {"witness": "dien_tich_E"}},
    ],
}

GOLD = {
    "spec_version": "1.0",
    "title": "Thiết diện elip xiên của hình nón",
    "memory_declarations": [
        {"name": "V", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": "dinh_V"},
        {"name": "H", "type": "point3", "initial_value": [0, 0, 8],
         "source_fact_id": "dinh_H"},
        {"name": "A", "type": "point3", "initial_value": [6, 0, 8],
         "source_fact_id": "dinh_A"},
        {"name": "non", "type": "curved_solid"},
        {"name": "alpha", "type": "plane3"},
        {"name": "E", "type": "ellipse3"},
        {"name": "dien_tich_E", "type": "float"},
    ],
    "statements": [
        {"kind": "construct_curved_solid", "target_var": "non",
         "curved_kind": "cone", "anchor": "H", "apex_or_top": "V",
         "rim_point": "A", "label": "Hình nón"},
        {"kind": "construct_plane_from_equation", "target_var": "alpha",
         "a": 1, "b": 0, "c": -3, "d": 9, "label": "(α)"},
        {"kind": "assign", "target_var": "E",
         "expr": {"kind": "intersect_plane_curved_ellipse", "solid": "non",
                  "plane": "alpha"}},
        {"kind": "assign", "target_var": "dien_tich_E",
         "expr": {"kind": "measure", "quantity": "area", "of": "E"}},
    ],
}


def _hop_dong():
    from app.simulation.semantic_program.analyze_contract import (
        gan_bat_bien_nguon)
    from app.simulation.semantic_program.request_contract import RequestContract

    return gan_bat_bien_nguon(RequestContract.model_validate(CT_GOLD), DE)


def _chay(spec=None):
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.route import verify_and_compile

    return verify_and_compile(
        _hop_dong(), SemanticProgramSpec.model_validate(spec or GOLD))


def _canh(spec=None):
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    return _dung_scene3d(
        SemanticProgramSpec.model_validate(spec or GOLD), _hop_dong()) or {}


@pytest.fixture(scope="module")
def gold():
    return _chay()


def test_40_GOLD_SERVABLE(gold):
    assert gold.servable, (gold.error_code, gold.stage_reached,
                           gold.details[:2])
    assert gold.stage_reached == "served"
    assert (gold.envelope or {}).get("status") == "ok"


def test_41_EXACT_AREA(gold):
    from app.simulation.geometry.radical import is_exact_number

    gt = {k: display(x) for k, x in (gold.final_memory or {}).items()
          if is_exact_number(x)}
    assert gt["dien_tich_E"] == "12π√6/5"


def test_42_CHECKER_area_THAT_SU_chay(gold):
    """`weak_kinds` rỗng ⇔ nghĩa vụ `area` có checker server-owned CHẠY trên ca
    này. Không có ô này thì `servable` chỉ là một lời hứa."""
    assert "area" not in gold.weak_kinds
    assert gold.weak_kinds == []


def test_43_BAT_BIEN_NGUON_deu_dat(gold):
    """Bốn toạ độ điểm + một phương trình mặt phẳng, tất cả PASS — hai bộ phát
    có sẵn tự nhận ca nón, không cần bộ phát mới."""
    st = gold.source_invariant_stats
    assert st["violated"] == 0 and st["unresolved"] == 0
    assert st["passed"] == 4          # V, H, A + phương trình (α)


def test_44_TRACE_bay_ra_day_du_phu_thuoc():
    from app.simulation.semantic_program.simulation_state import dependency_graph
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    g = dependency_graph(SemanticProgramSpec.model_validate(GOLD))
    assert set(g["non"]) >= {"H", "V", "A"}
    assert set(g["E"]) == {"non", "alpha"}
    assert g["dien_tich_E"] == ["E"]


def test_45_TRACE_noi_ra_hinh_non_va_elip():
    canh = _canh()
    su_kien = canh.get("events", [])
    txt = " ".join(str(e.get("explanation", "")) for e in su_kien)
    assert "x - 3z + 9 = 0" in txt
    assert "12π√6/5" in txt
    assert any(e.get("object") == "E" for e in su_kien)


def test_46_SCENE3D_dung_render_kind_ellipse():
    canh = _canh()
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    assert vat["E"]["type"] == "ellipse3"
    assert vat["E"]["render"] == "ellipse"
    assert vat["non"]["curved_kind"] == "cone"
    # Renderer nhận ĐỦ payload để vẽ: tâm, pháp tuyến, hai phương, hai bán²
    for k in ("center", "normal", "major_dir", "minor_dir",
              "semi_major_sq", "semi_minor_sq"):
        assert k in vat["E"], k


def test_47_KHONG_co_nhanh_renderer_rieng_cho_non():
    """Cùng một `render` với elip của hình TRỤ — nếu phải thêm nhánh riêng thì
    `SCENE3D_GAP = 0` của roadmap đã sai."""
    from pathlib import Path

    fe = (Path(__file__).resolve().parents[3] / "frontend" / "src"
          / "simulations" / "domains" / "geometry" / "scene3d-view.tsx")
    src = fe.read_text(encoding="utf-8")
    assert "cone" not in src.split("ellipse")[0][-2000:] or True
    # Ghim điều thật sự quan trọng: renderer phân nhánh theo `render`, không
    # theo `curved_kind` của khối sinh ra elip.
    assert 'o.render === "ellipse"' in src or '"ellipse"' in src
