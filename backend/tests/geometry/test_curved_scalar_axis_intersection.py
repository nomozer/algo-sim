# -*- coding: utf-8 -*-
"""Cắt khối cong khai bằng **vô hướng** (`radius` + `height`). 0 lượt gọi model.

    `docs/CURVED_SCALAR_AXIS_INTERSECTION_FIX.md`, 2026-09-05.

`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` mở đường khai trụ/nón bằng hai vô
hướng, cho đúng lớp đề *"hình trụ bán kính 7, chiều cao 10"* — đề không đặt tên
điểm nào nên không có `apex_or_top` nào dựng được. Wave ấy thêm `huong_truc`
kèm docstring *"hướng là thứ duy nhất mà mặt phẳng đáy và trục cần"*.

`_giao_tron_xoay` **không bao giờ chuyển sang dùng nó**. Nó vẫn đọc `truc` —
vectơ MANG độ dài — mà vectơ ấy bằng vectơ không khi khối khai bằng chiều cao.
Hệ quả: `ZeroDivisionError` trần, phân loại sai thành `capability_gap`, và tên
ngoại lệ Python rò lên `details`.

Bộ test này khoá **hành vi đúng**, và mỗi test nói rõ nó bảo vệ luật nào.

─── HAI THANG ĐO, VÀ ĐÓ LÀ CHỖ DỄ SAI NHẤT ──────────────────────────────

`huong_truc` **không chuẩn hoá**. Khai bằng điểm thì nó *là* `truc`, mang đúng
độ dài `h`; khai bằng vô hướng thì nó là vectơ đơn vị. Nên một tham số vị trí
tính theo `|u|` mang hai nghĩa khác nhau ở hai cách khai:

    khai bằng ĐIỂM     |u| = h  ⇒  L đã là TỈ LỆ dọc trục (0…1)
    khai bằng VÔ HƯỚNG |u| = 1  ⇒  L là KHOẢNG CÁCH tuyệt đối từ đáy (0…h)

Đổi `truc → huong_truc` mà quên điều này thì trụ vẫn đúng (bán kính không đổi
theo vị trí) còn **nón sai im lặng** — `test_TIEM_2`/`test_TIEM_4` là hai lưới
bắt đúng chỗ ấy.
"""
from __future__ import annotations

import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

from app.simulation.geometry import curved as CV  # noqa: E402
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3  # noqa: E402
from app.simulation.geometry.radical import display  # noqa: E402
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402


def P(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


def mp_ngang(z) -> Plane3:
    """Mặt phẳng ⊥ trục canonical, cắt tại cao độ `z`."""
    return Plane3(P(0, 0, z), P(0, 0, 1))


def vo_huong(kind, r, h):
    """Khối khai bằng HAI VÔ HƯỚNG — pose canonical, không điểm nào có tên."""
    return CV.CurvedSolid(kind, CV.GOC_CANONICAL, None, None, F(r) ** 2,
                          height_sq_khai=F(h) ** 2, pose_canonical=True)


def bang_diem(kind, r, h):
    """CÙNG khối ấy, khai bằng ba điểm — fixture đối chứng."""
    return CV.CurvedSolid(kind, P(0, 0, 0), P(0, 0, h), P(r, 0, 0), None)


# ══ §2 · TÁI HIỆN — hai cách khai phải cho CÙNG một hình ═════════════════
@pytest.mark.parametrize("kind", ["cylinder", "cone"])
def test_R1_truc_bang_VECTO_KHONG_khi_khai_bang_vo_huong(kind):
    """Nguyên nhân, nêu thẳng: `truc` rỗng còn `huong_truc` thì không."""
    s = vo_huong(kind, 9, 20)
    assert s.truc.is_zero()
    assert s.huong_truc == CV.HUONG_TRUC_CANONICAL
    assert s.height_sq == F(400)          # chiều cao vẫn biết, chỉ trục không
    assert s.radius_sq == F(81)


@pytest.mark.parametrize("kind,r,h", [("cylinder", 9, 20), ("cone", 10, 15)])
def test_R2_cat_duoc_va_KHONG_nem_ZeroDivisionError(kind, r, h):
    """Ca đã hỏng: `(p−anchor)·d / d·d` với `d = 0` là chia cho 0."""
    c = CV.intersect_plane_curved(vo_huong(kind, r, h), mp_ngang(F(h, 3)))
    assert isinstance(c.radius_sq, F) and c.radius_sq > 0


@pytest.mark.parametrize("kind,r,h,z", [
    ("cylinder", 9, 20, 4), ("cylinder", 9, 20, 10), ("cylinder", 9, 20, 16),
    ("cone", 10, 15, 3), ("cone", 10, 15, 6), ("cone", 10, 15, 12)])
def test_R3_HAI_CACH_KHAI_cho_y_HET_nhau(kind, r, h, z):
    """Bất biến trung tâm: cách KHAI không được đổi HÌNH."""
    a = CV.intersect_plane_curved(vo_huong(kind, r, h), mp_ngang(z))
    b = CV.intersect_plane_curved(bang_diem(kind, r, h), mp_ngang(z))
    assert a.center == b.center
    assert a.radius_sq == b.radius_sq
    # Pháp tuyến so theo TƯƠNG ĐƯƠNG HÌNH HỌC: cùng phương là đủ, hệ số và
    # dấu không mang nghĩa cho một mặt phẳng.
    assert a.normal.cross(b.normal).is_zero()
    assert not a.normal.is_zero() and not b.normal.is_zero()


# ══ §4 · ORACLE — đáp số tính TRỰC TIẾP từ dữ kiện ═══════════════════════
#
# Không lấy từ kernel rồi so với chính nó. Bán kính giao tuyến của nón suy từ
# tam giác đồng dạng: `r' = r·(h − L)/h`; của trụ thì hằng.
ORACLE = [
    ("cylinder", 9, 20, 4, "9", "81π"),
    ("cylinder", 9, 20, 10, "9", "81π"),
    ("cylinder", 9, 20, 16, "9", "81π"),
    ("cone", 10, 15, 3, "8", "64π"),
    ("cone", 10, 15, 6, "6", "36π"),
    ("cone", 10, 15, 12, "2", "4π"),
    ("cone", F(3, 2), F(5, 2), 1, "9/10", "81π/100"),
]


@pytest.mark.parametrize("kind,r,h,L,ban_kinh,dien_tich", ORACLE)
def test_O_dap_so_khop_ORACLE_o_ca_hai_cach_khai(kind, r, h, L, ban_kinh,
                                                 dien_tich):
    for ten, s in (("vô hướng", vo_huong(kind, r, h)),
                   ("ba điểm", bang_diem(kind, r, h))):
        c = CV.intersect_plane_curved(s, mp_ngang(L))
        assert display(CV.ban_kinh(c)) == ban_kinh, ten
        assert display(CV.dien_tich_hinh_tron(c)) == dien_tich, ten
        # Tâm nằm ĐÚNG trên trục, ở đúng cao độ mặt phẳng.
        assert c.center == P(0, 0, L), ten


def test_O_tam_va_mat_phang_cua_duong_tron_khop_hai_cach_khai():
    for z in (1, 5, 14):
        a = CV.intersect_plane_curved(vo_huong("cone", 10, 15), mp_ngang(z))
        b = CV.intersect_plane_curved(bang_diem("cone", 10, 15), mp_ngang(z))
        assert a.center == b.center == P(0, 0, z)
        assert a.normal.cross(b.normal).is_zero()


# ══ §5 · RANH GIỚI — đọc mã hiện hành, không bịa mã mới ══════════════════
@pytest.mark.parametrize("kind", ["cylinder", "cone"])
@pytest.mark.parametrize("z", [-1, 21, 100])
def test_B_mat_phang_NGOAI_chieu_cao_tu_choi_co_ma(kind, z):
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved(vo_huong(kind, 9, 20), mp_ngang(z))
    assert e.value.code == CV.ERR_KHONG_CAT


def test_B_mat_phang_qua_DINH_non_tu_choi_va_chi_sang_phep_dung_dung():
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved(vo_huong("cone", 10, 15), mp_ngang(15))
    assert e.value.code == CV.ERR_TIEP_XUC


@pytest.mark.parametrize("kind", ["cylinder", "cone"])
def test_B_mat_phang_XIEN_van_ngoai_bao_dong_v1(kind):
    """Chốt ⊥ trục phải còn răng ở cách khai vô hướng — `truc = 0` từng làm
    `cross` luôn bằng không, tức chốt này **im lặng biến mất**."""
    xien = Plane3(P(0, 0, 5), P(1, 0, 1))
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved(vo_huong(kind, 9, 20), xien)
    assert e.value.code == CV.ERR_NGOAI_BAO_DONG


def test_B_day_duoi_cua_non_cho_dung_ban_kinh_day():
    c = CV.intersect_plane_curved(vo_huong("cone", 10, 15), mp_ngang(0))
    assert c.radius_sq == F(100)


def test_B_chieu_cao_VO_TI_tru_van_cat_duoc__non_thi_TU_CHOI_co_ma():
    """Miền số quyết định, và nó quyết định KHÁC NHAU cho hai hình.

    Trụ: `r' = r` không phụ thuộc vị trí ⇒ `h = √7` vô tỉ vẫn cắt được chính
    xác. Nón: `r'² = r²(h−L)²/h²` chứa `h` ⇒ ngoài ℚ khi `h` vô tỉ. Từ chối
    **có mã**, không xấp xỉ.
    """
    tru = CV.CurvedSolid("cylinder", CV.GOC_CANONICAL, None, None, F(81),
                         height_sq_khai=F(7), pose_canonical=True)
    assert CV.intersect_plane_curved(tru, mp_ngang(2)).radius_sq == F(81)

    non = CV.CurvedSolid("cone", CV.GOC_CANONICAL, None, None, F(81),
                         height_sq_khai=F(7), pose_canonical=True)
    with pytest.raises(GeometryError) as e:
        CV.intersect_plane_curved(non, mp_ngang(1))
    assert e.value.code == CV.ERR_NGOAI_BAO_DONG


# ══ §5 · HỒI QUY — cầu và đường khai bằng điểm không được đụng ═══════════
def test_H_cau_khong_bi_dung_toi():
    for s in (CV.CurvedSolid("ball", P(0, 0, 0), None, None, F(625)),
              CV.CurvedSolid("ball", P(0, 0, 0), None, P(25, 0, 0), None)):
        assert CV.intersect_plane_curved(s, mp_ngang(7)).radius_sq == F(576)


def test_H_the_tich_va_mat_cong_giu_nguyen_o_ca_hai_cach_khai():
    for kind, r, h, v, m in (("cylinder", 12, 20, "2880π", "480π"),
                             ("cone", 10, 15, "500π", "50π√13")):
        a, b = vo_huong(kind, r, h), bang_diem(kind, r, h)
        assert display(CV.the_tich(a)) == display(CV.the_tich(b)) == v
        assert (display(CV.dien_tich_mat_cong(a))
                == display(CV.dien_tich_mat_cong(b)) == m)


# ══ §5 · ĐƯỜNG SẢN PHẨM — đi TRỌN với cách khai `height` ═════════════════
VB = {"containers": [], "pointers": [], "value_boxes": []}
FK, FD = "f_kichthuoc", "f_diem"


def _spec_vo_huong(kind, r, h, z, do):
    """Khối khai bằng VÔ HƯỚNG, `anchor` là một điểm CÓ TÊN của đề.

    Pose ấy là thứ hợp đồng hiện tại thực sự cung cấp: `anchor` có tên nên
    grounding truy được, còn trục thì do `height` xác định — đúng tổ hợp mà
    lược đồ cho phép (`ConstructCurvedSolidStmt` ② + ③).
    """
    decls = [
        {"name": "ban_kinh", "type": "float", "initial_value": r,
         "source_fact_id": FK},
        {"name": "chieu_cao", "type": "float", "initial_value": h,
         "source_fact_id": FK},
        {"name": "Tam", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": FD},
        {"name": "Moc", "type": "point3", "initial_value": [0, 0, z],
         "source_fact_id": FD},
        {"name": "Khoi", "type": "curved_solid"},
        {"name": "TrucK", "type": "line3"},
        {"name": "MpCat", "type": "plane3"},
        {"name": "Vong", "type": "circle3"}]
    stmts = [
        {"kind": "construct_curved_solid", "target_var": "Khoi",
         "curved_kind": kind, "anchor": "Tam", "radius": "ban_kinh",
         "height": "chieu_cao"},
        {"kind": "construct_line", "target_var": "TrucK",
         "through_a": "Tam", "through_b": "Moc"},
        {"kind": "assign", "target_var": "MpCat",
         "expr": {"kind": "plane_perpendicular_to_line", "point": "Moc",
                  "line": "TrucK"}},
        {"kind": "assign", "target_var": "Vong",
         "expr": {"kind": "intersect_plane_curved", "solid": "Khoi",
                  "plane": "MpCat"}}]
    for bien, luong in do:
        decls.append({"name": bien, "type": "float"})
        stmts.append({"kind": "assign", "target_var": bien,
                      "expr": {"kind": "measure", "quantity": luong,
                               "of": "Vong"}})
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thiết diện tròn, khối khai vô hướng",
        "description": "Dựng khối cong bằng bán kính và chiều cao rồi cắt.",
        "pedagogical_intent": "Thấy thiết diện ⊥ trục là một đường tròn.",
        "memory_declarations": decls, "statements": stmts,
        "visual_bindings": VB})


def _hd(de, do):
    return RequestContract(
        problem_text=de,
        input_facts=[
            {"fact_id": FK, "label": "bán kính đáy và chiều cao",
             "values": [9, 20, 10, 15, 6], "provenance": "confirmed"},
            {"fact_id": FD, "label": "Tâm là tâm đáy, Mốc thuộc trục",
             "values": ["Tam", "Moc"], "provenance": "confirmed"}],
        obligations=tuple(Obligation(kind=k, container="Vong",
                                     params={"witness": w}) for w, k in do))


@pytest.mark.parametrize("kind,r,h,z,do,mong", [
    ("cylinder", 9, 20, 10, [("bk", "radius"), ("dt", "area")],
     {"bk": "9", "dt": "81π"}),
    ("cone", 10, 15, 6, [("bk", "radius")], {"bk": "6"}),
])
def test_S_duong_san_pham_di_TRON_voi_cach_khai_height(kind, r, h, z, do, mong):
    spec = _spec_vo_huong(kind, r, h, z, do)
    out = verify_and_compile(_hd(f"Khối {kind} bị cắt.", do), spec)
    assert out.servable, getattr(out, "details", None)
    mem = {k: str(v) for k, v in (out.final_memory or {}).items()}
    assert {k: mem.get(k) for k in mong} == mong

    # Cách khai `height` vẫn CÒN NGUYÊN trong chương trình được thực thi —
    # nếu một tầng nào đó lén quy đổi sang `apex_or_top` thì test này đỏ, và
    # khi ấy phép đo ở trên không còn nói về đường đang được sửa.
    lenh = [st for st in spec.model_dump(mode="json")["statements"]
            if st["kind"] == "construct_curved_solid"][0]
    assert lenh["height"] == "chieu_cao" and lenh["apex_or_top"] is None


def test_S_scene3d_mang_circle3_dung_producer_va_phu_thuoc():
    from app.ai import pipeline

    do = [("bk", "radius"), ("dt", "area")]
    spec = _spec_vo_huong("cylinder", 9, 20, 10, do)
    hd = _hd("Hình trụ bị cắt.", do)
    assert verify_and_compile(hd, spec).servable
    canh = pipeline._dung_scene3d(spec, hd) or {}
    o = {x.get("name") or x.get("id"): x for x in canh.get("objects", [])}
    assert o["Vong"]["type"] == "circle3"
    assert o["Vong"]["producer"] == "intersect_plane_curved"
    assert set(o["Vong"]["depends"]) == {"Khoi", "MpCat"}
    assert o["bk"]["depends"] == ["Vong"] and o["dt"]["depends"] == ["Vong"]
    # Số đo trong cảnh khớp kết quả exact.
    assert o["bk"]["value"] == "9" and o["dt"]["value"] == "81π"


def test_S_diem_co_ten_van_giu_xuat_xu__grounding_khong_bi_noi():
    """Bản vá không được mua `served` bằng cách nới grounding."""
    do = [("bk", "radius")]
    spec = _spec_vo_huong("cylinder", 9, 20, 10, do)
    hong = RequestContract(
        problem_text="Hình trụ bị cắt.",
        input_facts=[{"fact_id": FK, "label": "kích thước",
                      "values": [9, 20], "provenance": "confirmed"}],
        obligations=(Obligation(kind="radius", container="Vong",
                                params={"witness": "bk"}),))
    out = verify_and_compile(hong, spec)          # `Tam`/`Moc` mất xuất xứ
    assert not out.servable
    assert out.stage_reached == "grounding"


def test_S_mat_phang_xien_qua_duong_san_pham_tu_choi_CO_CAU_TRUC():
    """Từ chối phải là lỗi hình học có mã, không phải một ngoại lệ Python."""
    do = [("bk", "radius")]
    decls_stmts = _spec_vo_huong("cylinder", 9, 20, 10, do).model_dump(
        mode="json")
    d = decls_stmts["memory_declarations"] + [
        {"name": "Lech", "type": "point3", "initial_value": [9, 0, 0],
         "source_fact_id": FD}]
    s = [st for st in decls_stmts["statements"]
         if st.get("target_var") != "MpCat"]
    i = next(k for k, x in enumerate(s) if x.get("target_var") == "Vong")
    s.insert(i, {"kind": "construct_plane", "target_var": "MpCat",
                 "through": ["Tam", "Lech", "Moc"]})
    spec = SemanticProgramSpec.model_validate({**decls_stmts,
                                               "memory_declarations": d,
                                               "statements": s})
    out = verify_and_compile(_hd("Hình trụ cắt xiên.", do), spec)
    assert not out.executable
    assert any(CV.ERR_NGOAI_BAO_DONG in x for x in (out.details or [])), \
        out.details
    assert not any("ZeroDivisionError" in x for x in (out.details or []))


# ══ §6 · TIÊM LỖI — mỗi cái gỡ đúng một mảnh của bản vá ══════════════════
def test_TIEM_1_khoi_phuc_duong_doc_TRUC_cu_thi_scalar_mode_do(monkeypatch):
    """① Đọc lại `truc` thay vì `huong_truc` ⇒ chia cho 0 quay lại."""
    monkeypatch.setattr(CV.CurvedSolid, "huong_truc",
                        property(lambda self: self.truc))
    with pytest.raises((ZeroDivisionError, GeometryError)):
        CV.intersect_plane_curved(vo_huong("cylinder", 9, 20), mp_ngang(10))


def test_TIEM_2_mat_THANG_chieu_cao_thi_nón_chieu_cao_khac_1_do(monkeypatch):
    """② Bỏ phép đổi thang `L → t` ⇒ nón sai ở mọi chiều cao ≠ 1.

    Đây là lưới cho đúng cái bẫy nêu ở đầu file: `huong_truc` KHÔNG chuẩn hoá,
    nên coi `L` là `t` sẽ đúng ở cách khai bằng điểm và sai ở cách khai vô
    hướng — một lỗi chỉ hiện ra ở một nửa miền.
    """
    monkeypatch.setattr(CV, "_ti_le_doc_truc",
                        lambda s, L: L)             # quên chia cho h
    c = CV.intersect_plane_curved(vo_huong("cone", 10, 15), mp_ngang(6))
    assert c.radius_sq != F(36)                     # đúng phải là 6² = 36


def test_TIEM_3_bo_he_so_dong_dang_non_thi_nhieu_vi_tri_do(monkeypatch):
    """③ Bỏ `(1−t)²` ⇒ nón trả bán kính ĐÁY ở mọi lát cắt."""
    goc = CV.intersect_plane_curved

    def khong_dong_dang(s, pl):
        c = goc(s, pl)
        return CV.Circle3(c.center, c.normal, s.radius_sq)

    monkeypatch.setattr(CV, "intersect_plane_curved", khong_dong_dang)
    sai = [CV.intersect_plane_curved(vo_huong("cone", 10, 15),
                                     mp_ngang(z)).radius_sq
           for z in (3, 6, 12)]
    assert sai == [F(100)] * 3                      # đúng phải là 64, 36, 4


def test_TIEM_4_dao_chieu_do_tu_DAY_va_tu_DINH_thi_do(monkeypatch):
    """④ Đảo gốc đo ⇒ lát cắt bất đối xứng lộ ngay.

    `z = 3` trên nón `h = 15` cho `r' = 8`; đo ngược từ đỉnh cho `r' = 2`.
    Chọn một vị trí KHÔNG đối xứng chính là điều làm lưới này có răng.
    """
    goc = CV._ti_le_doc_truc
    monkeypatch.setattr(CV, "_ti_le_doc_truc",
                        lambda s, L: 1 - goc(s, L))
    c = CV.intersect_plane_curved(vo_huong("cone", 10, 15), mp_ngang(3))
    assert c.radius_sq == F(4)                      # đúng phải là 64


def test_TIEM_5_tu_choi_moi_scalar_mode_thi_duong_san_pham_do(monkeypatch):
    """⑤ Trả lỗi cho mọi khối khai vô hướng ⇒ ca `served` ở §5 sập."""
    goc = CV.intersect_plane_curved

    def tu_choi(s, pl):
        if s.apex_or_top is None and s.kind != "ball":
            raise GeometryError(CV.ERR_NGOAI_BAO_DONG, "giả vờ không hỗ trợ")
        return goc(s, pl)

    monkeypatch.setattr(CV, "intersect_plane_curved", tu_choi)
    out = verify_and_compile(
        _hd("Hình trụ bị cắt.", [("bk", "radius")]),
        _spec_vo_huong("cylinder", 9, 20, 10, [("bk", "radius")]))
    assert not out.servable
