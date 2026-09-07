# -*- coding: utf-8 -*-
"""`CURVED_SCALAR_AXIS_SCALE_REPAIR` — hai cách khai, MỘT hình học.

Wave khôi phục tính tương đương giữa

    POINT_MODE  = anchor + apex_or_top / rim_point
    SCALAR_MODE = radius + height + pose

và hội tụ hợp đồng của toán hạng `height`. `APPLICATION_LLM_CALLS = 0`.

─── PHÂN TÍCH ĐƠN VỊ, VÀ VÌ SAO NÓ LÀ TOÀN BỘ VẤN ĐỀ ──────────────────────

`huong_truc` cố ý trả hai thứ khác THANG: `truc` (`|u| = h`) khi khối khai
bằng ĐIỂM, vectơ đơn vị (`|u| = 1`) khi khai bằng VÔ HƯỚNG. Nên `L =
(tâm−anchor)·u/(u·u)` là **tỉ lệ** ở nhánh đầu và **khoảng cách tuyệt đối** ở
nhánh sau.

Đo trên ca chuẩn (`r=4, h=20, 2x−z+10=0`), ba đại lượng của cap check:

    h_half_sq   64   ↔   64      BẤT BIẾN THANG (tử/mẫu cùng bậc hai theo u)
    duoi_sq    100   ↔  100      ĐỘ DÀI² ở cả hai (L²·|u|² triệt tiêu thang)
    tren_sq    100   ↔   81      ✗ `(1−L)²·|u|²` — chỉ đúng khi |u| = h

Hai vế đầu **đã** ở ĐỘ DÀI², nên đơn vị chuẩn của cả phép kiểm là ĐỘ DÀI² —
cùng đơn vị đường ĐƯỜNG TRÒN đã chọn (`_giao_tron_xoay` so `d2` với
`height_sq`). Bản vá kéo nốt vế thứ ba về đó, thay vì kéo hai vế kia sang
thang tỉ lệ.
"""
from __future__ import annotations

import copy
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry import curved as CV
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.plane_equation import bat_bien_mat_phang
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_oblique_ellipse_fresh import (  # noqa: E402
    GOLD, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)

DAP_SO = "16π√5"


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


def tru_diem(r2, h) -> CV.CurvedSolid:
    """POINT_MODE — trục Oz, đáy tại gốc, đỉnh tại `(0,0,h)`."""
    return CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, h), None, F(r2))


def tru_vo_huong(r2, h2) -> CV.CurvedSolid:
    """SCALAR_MODE — cùng hình trụ, khai bằng `(bán kính², chiều cao²)`."""
    return CV.CurvedSolid("cylinder", v(0, 0, 0), None, None, F(r2),
                          height_sq_khai=F(h2))


def phan_quyet(s: CV.CurvedSolid, pl: Plane3):
    """`(mã lỗi | None, elip | None)` — không ném, để so được hai nhánh."""
    try:
        return None, CV.intersect_plane_curved_ellipse(s, pl)
    except GeometryError as e:
        return e.code, None


def mp(a, b, c, d) -> Plane3:
    return Plane3.from_equation(F(a), F(b), F(c), F(d))


# ══ §6 · TƯƠNG ĐƯƠNG HAI REPRESENTATION ═════════════════════════════════
#
# `(r², h, mặt phẳng, mô tả)` — bốn ca §6 đòi, mỗi ca một dáng lát cắt.
CA_PARITY = [
    (16, 20, (2, 0, -1, 10), "ca chuẩn, lát cắt giữa thân"),
    (9, 10, (1, 0, -1, 5), "r=3 h=10, lát cắt xiên nằm trọn"),
    (25, 40, (1, 0, -2, 10), "r=5 h=40, lệch về đáy dưới"),
    (25, 50, (1, 0, -2, 90), "r=5 h=50, lệch về đáy trên"),
]


@pytest.mark.parametrize("r2,h,pt,ten", CA_PARITY)
def test_01_parity_bon_ca(r2, h, pt, ten):
    """Cùng verdict · cùng tâm · cùng hai bán trục · cùng diện tích."""
    pl = mp(*pt)
    ma_a, ea = phan_quyet(tru_diem(r2, h), pl)
    ma_b, eb = phan_quyet(tru_vo_huong(r2, h * h), pl)

    assert ma_a is None, (ten, "POINT_MODE từ chối", ma_a)
    assert ma_b is None, (ten, "SCALAR_MODE từ chối", ma_b)
    assert ea.center == eb.center, ten
    assert ea.semi_major_sq == eb.semi_major_sq, ten
    assert ea.semi_minor_sq == eb.semi_minor_sq, ten
    assert (display(CV.dien_tich_elip(ea))
            == display(CV.dien_tich_elip(eb))), ten


def test_02_ca_chuan_cho_dung_dap_so():
    """Parity mà cả hai cùng SAI thì vô nghĩa — neo vào oracle độc lập."""
    pl = mp(2, 0, -1, 10)
    for s in (tru_diem(16, 20), tru_vo_huong(16, 400)):
        e = CV.intersect_plane_curved_ellipse(s, pl)
        assert display(CV.dien_tich_elip(e)) == DAP_SO
        assert e.center == v(0, 0, 10)
        assert e.semi_minor_sq == F(16)      # b² = r²
        assert e.semi_major_sq == F(80)      # a² = r²·|n|²|u|²/(n·u)²


# ══ §6 · BIÊN ══════════════════════════════════════════════════════════
#
# `n = (2,0,−1)`, `r = 4` ⇒ nửa trục dọc `h_half = r·|a/c| = 8`. Trụ cao 20,
# nên tâm elip phải nằm trong `[8, 12]` mới đủ chỗ hai đầu.
CA_BIEN = [
    ((2, 0, -1, 8), None, "elip vừa CHẠM đáy dưới (duoi = h_half = 8)"),
    ((2, 0, -1, 12), None, "elip vừa CHẠM đáy trên (tren = h_half = 8)"),
    ((2, 0, -1, 7), CV.ERR_ELIP_CAT_DAY, "vượt đáy dưới"),
    ((2, 0, -1, 13), CV.ERR_ELIP_CAT_DAY, "vượt đáy trên"),
    ((1, 0, 0, -3), CV.ERR_ELIP_NGOAI_BAO_DONG, "mặt phẳng SONG SONG trục"),
    ((0, 0, 1, -10), CV.ERR_ELIP_NGOAI_BAO_DONG, "mặt phẳng VUÔNG GÓC trục"),
    ((2, 0, -1, 25), CV.ERR_KHONG_CAT, "tâm NGOÀI khối"),
]


@pytest.mark.parametrize("pt,ma,ten", CA_BIEN)
def test_03_bien_parity(pt, ma, ten):
    """Mọi ca biên phải cho CÙNG phán quyết ở hai cách khai."""
    pl = mp(*pt)
    ma_a, _ = phan_quyet(tru_diem(16, 20), pl)
    ma_b, _ = phan_quyet(tru_vo_huong(16, 400), pl)
    assert ma_a == ma_b == ma, (ten, ma_a, ma_b)


def test_04_elip_vuot_CA_HAI_day():
    """Trụ quá thấp so với độ dốc ⇒ từ chối ở cả hai cách khai."""
    pl = mp(2, 0, -1, 2)
    assert phan_quyet(tru_diem(16, 4), pl)[0] == CV.ERR_ELIP_CAT_DAY
    assert phan_quyet(tru_vo_huong(16, 16), pl)[0] == CV.ERR_ELIP_CAT_DAY


def test_05_duong_TRON_parity_giu_nguyen():
    """`intersect_plane_curved` vốn đã đúng — bản vá KHÔNG được đụng nó."""
    ngang = mp(0, 0, 1, -10)
    a = CV.intersect_plane_curved(tru_diem(16, 20), ngang)
    b = CV.intersect_plane_curved(tru_vo_huong(16, 400), ngang)
    assert a.radius_sq == b.radius_sq == F(16)
    assert a.center == b.center == v(0, 0, 10)


def test_06_chieu_cao_VO_TI_van_cat_duoc():
    """⚠️ Bất biến DỄ MẤT NHẤT của bản vá, và là lý do KHÔNG dùng `_ti_le_truc`.

    Hình trụ không cần biết `h` là số nào — bán kính nó là hằng dọc trục. Nên
    `h² = 300` (`h = 10√3`, vô tỉ) vẫn phải cắt được CHÍNH XÁC.

    Một bản vá đổi cap check sang thang TỈ LỆ sẽ phải chia cho `h` và ca này
    chết với `CURVED_SECTION_OUTSIDE_V1_CLOSURE` — tức thu hẹp một năng lực
    đang chạy để chữa một lỗi thang.
    """
    h2 = F(300)
    assert not isinstance(CV.sqrt_rational(h2), F)   # h thật sự vô tỉ
    s = tru_vo_huong(16, h2)
    e = CV.intersect_plane_curved_ellipse(s, mp(1, 0, -4, 32))
    assert e.center == v(0, 0, 8)
    assert e.semi_minor_sq == F(16)


def test_07_bat_bien_TI_LE():
    """Nhân mọi độ dài bởi `s` hữu tỉ: phân loại giữ nguyên, diện tích × s²."""
    goc = CV.intersect_plane_curved_ellipse(tru_vo_huong(16, 400),
                                            mp(2, 0, -1, 10))
    for he in (F(3), F(1, 2), F(5, 3)):
        # `r → s·r` ⇒ `r² → s²r²`; `h → s·h` ⇒ `h² → s²h²`; `d → s·d`.
        to = CV.intersect_plane_curved_ellipse(
            tru_vo_huong(16 * he * he, 400 * he * he),
            Plane3.from_equation(F(2), F(0), F(-1), F(10) * he))
        assert to.semi_major_sq == goc.semi_major_sq * he * he, he
        assert to.semi_minor_sq == goc.semi_minor_sq * he * he, he
        assert to.center == goc.center.scale(he), he


def test_08_bat_bien_ti_le_giu_ca_phan_loai_TU_CHOI():
    """Ca bị từ chối cũng phải giữ nguyên phân loại khi nhân thang."""
    for he in (F(3), F(1, 2)):
        ma, _ = phan_quyet(
            tru_vo_huong(16 * he * he, 400 * he * he),
            Plane3.from_equation(F(2), F(0), F(-1), F(7) * he))
        assert ma == CV.ERR_ELIP_CAT_DAY, he


def test_09_cau_va_non_khong_bi_anh_huong():
    """Bản vá chỉ chạm phép ELIP của trụ. Cầu và nón giữ verdict hiện hành."""
    cau = CV.CurvedSolid("ball", v(0, 0, 0), None, None, F(25))
    assert CV.intersect_plane_curved(cau, mp(0, 0, 1, -3)).radius_sq == F(16)
    non = CV.CurvedSolid("cone", v(0, 0, 0), v(0, 0, 12), None, F(36))
    assert CV.intersect_plane_curved(non, mp(0, 0, 1, -6)).radius_sq == F(9)
    # Nón khai bằng vô hướng: `_ti_le_doc_truc` vẫn là thẩm quyền của nó.
    non_vh = CV.CurvedSolid("cone", v(0, 0, 0), None, None, F(36),
                            height_sq_khai=F(144))
    assert CV.intersect_plane_curved(non_vh, mp(0, 0, 1, -6)).radius_sq == F(9)


# ══ §5 · TOÁN HẠNG `height` ════════════════════════════════════════════
def test_10_height_la_toan_hang_scalar_o_MOT_tham_quyen():
    """Một dòng ở `_TOAN_HANG_LENH`; `O_TEN` và thẻ DẪN XUẤT theo."""
    from app.simulation.semantic_program.hoisting import O_TEN
    from app.simulation.semantic_program.ir_static_check import _TOAN_HANG_LENH

    o = _TOAN_HANG_LENH["construct_curved_solid"]
    assert ("height", ("scalar", "float", "int"), False) in o
    assert O_TEN["construct_curved_solid"]["height"] == (
        ("scalar", "float", "int"), False)


def _chuong_trinh_height(kieu_h="float", gia_tri=20, do_bang_measure=False):
    """Gold, nhưng trụ khai bằng `anchor + radius + height`."""
    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                               if d["name"] not in ("P1", "P2", "P3")]
    g["statements"] = [
        {"kind": "construct_plane_from_equation", "target_var": "alpha",
         "a": 2, "b": 0, "c": -1, "d": 10, "label": "(α)"}
        if s.get("kind") == "construct_plane" else s
        for s in g["statements"]]
    if do_bang_measure:
        g["memory_declarations"].append({"name": "h", "type": "float"})
        do = {"kind": "assign", "target_var": "h",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "O", "wrt": "Oprime"}}
    else:
        g["memory_declarations"].append(
            {"name": "h", "type": kieu_h, "initial_value": gia_tri,
             "source_fact_id": "tam_day_tren"})
        do = None
    moi = []
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            if do:
                moi.append(do)
            s = dict(s)
            s.pop("apex_or_top", None)
            s["height"] = "h"
        moi.append(s)
    g["statements"] = moi
    return g


def test_11_static_height_scalar_hop_le_QUA_duoc():
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    r = kiem_tinh(SemanticProgramSpec.model_validate(
        _chuong_trinh_height(do_bang_measure=True)))
    assert r.ok, [i.error_code for i in r.issues]


def test_12_static_height_bien_CHUA_DUNG_bi_tu_choi():
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    g = _chuong_trinh_height(do_bang_measure=True)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                               if d["name"] != "h"]
    g["statements"] = [s for s in g["statements"]
                       if s.get("target_var") != "h"]
    r = kiem_tinh(SemanticProgramSpec.model_validate(g))
    assert not r.ok
    assert any(i.object_id == "h" for i in r.issues)


@pytest.mark.parametrize("kieu", ["point3", "vector3", "plane3"])
def test_13_static_height_SAI_KIEU_bi_tu_choi(kieu):
    """Trước bản vá, ba kiểu này đi LỌT thẩm định tĩnh rồi mới vỡ ở runtime —
    và lỗi runtime KHÔNG được gửi ngược cho vòng sửa."""
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    g = _chuong_trinh_height(do_bang_measure=True)
    for d in g["memory_declarations"]:
        if d["name"] == "h":
            d["type"] = kieu
    g["statements"] = [s for s in g["statements"]
                       if s.get("target_var") != "h"]
    r = kiem_tinh(SemanticProgramSpec.model_validate(g))
    assert not r.ok, kieu
    assert any(i.object_id == "h" for i in r.issues), kieu


def test_14_dependency_chieu_cao_ve_duoc_hai_TAM():
    """`ellipse → cylinder → h → {O, O′}` — trên CẢ HAI bảng phụ thuộc.

    Hai bảng, hai vai, và cả hai từng thiếu `height`:

      · `coverage_gate._phu_thuoc` — DẪN XUẤT từ `_TOAN_HANG_LENH`, nên nó tự
        đúng theo một dòng thêm. Đây là bảng C₁b dùng để hỏi *"witness có
        được TÍNH ra không"*.
      · `simulation_state._NGUON_CUA_PHEP_DUNG` — viết tay có chủ đích (nó là
        chỗ duy nhất nói *trường nào chở provenance*), nên phải sửa riêng.
        Đây là bảng CẢNH dùng để dựng cây thành phần cho học sinh.
    """
    from app.simulation.semantic_program.coverage_gate import _phu_thuoc

    spec = SemanticProgramSpec.model_validate(
        _chuong_trinh_height(do_bang_measure=True))

    pt = _phu_thuoc(spec.statements, frozenset())
    assert "h" in pt["tru"], pt.get("tru")
    assert {"O", "Oprime"} <= pt["h"], pt.get("h")

    def bao_dong(bang, ten, tham=None):
        tham = set() if tham is None else tham
        if ten in tham:
            return set()
        tham.add(ten)
        ra = set(bang.get(ten, ()) or ())
        for x in list(ra):
            ra |= bao_dong(bang, x, tham)
        return ra

    assert {"O", "Oprime", "h", "tru"} <= bao_dong(pt, "E")


def test_15_the_van_pham_in_DU_kieu_va_vai_tro_cho_height():
    from app.simulation.semantic_program.grammar_card import grammar_card

    dong = next(d for d in grammar_card("hinh_hoc").splitlines()
                if "construct_curved_solid:" in d)
    assert "height?:tên<scalar|float|int>[ĐẠI LƯỢNG chiều cao" in dong


# ══ §7 · REPLAY ĐƯỜNG SẢN PHẨM ═════════════════════════════════════════
def _hd() -> RequestContract:
    c = RequestContract.model_validate(REQUEST_CONTRACT_GOLD)
    return c.model_copy(update={
        "source_invariants": tuple(c.source_invariants or ())
        + bat_bien_mat_phang(c, PROBLEM_TEXT)})


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _dap_so(kq):
    return {k: display(x) for k, x in (kq.final_memory or {}).items()
            if is_exact_number(x)}.get(WITNESS)


def test_16_replay_POINT_MODE_tron_duong():
    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                               if d["name"] not in ("P1", "P2", "P3")]
    g["statements"] = [
        {"kind": "construct_plane_from_equation", "target_var": "alpha",
         "a": 2, "b": 0, "c": -1, "d": 10, "label": "(α)"}
        if s.get("kind") == "construct_plane" else s
        for s in g["statements"]]
    kq = _chay(g)
    assert kq.servable and kq.stage_reached == "served"
    assert _dap_so(kq) == DAP_SO
    assert kq.source_invariant_stats["passed"] == 1


def test_17_replay_SCALAR_MODE_trung_thuc_tron_duong():
    """⚠️ Đường này TRƯỚC bản vá chết ở `execution` với `CROSSES_CAP`.

    Chiều cao do chương trình ĐO (`measure(distance, O, O′)`), nên grounding
    bỏ qua đúng luật — nó là giá trị TÍNH RA, không phải dữ kiện khai.
    """
    kq = _chay(_chuong_trinh_height(do_bang_measure=True))
    assert kq.servable, (kq.error_code, kq.stage_reached)
    assert _dap_so(kq) == DAP_SO
    assert kq.source_invariant_stats["passed"] == 1


def test_18_replay_SCALAR_MODE_co_trace_va_scene3d():
    from app.ai.pipeline import _dung_scene3d

    spec = SemanticProgramSpec.model_validate(
        _chuong_trinh_height(do_bang_measure=True))
    canh = _dung_scene3d(spec, _hd()) or {}
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    assert any(o.get("type") == "ellipse3" for o in vat.values())
    # Chiều cao là NGUỒN của khối — cây thành phần phải nói được điều đó.
    assert "h" in (vat["tru"].get("depends") or [])


def test_19_khai_chieu_cao_bang_HANG_thieu_nguon__grounding_VAN_chat():
    """Fixture này chứng minh grounding còn chặt, KHÔNG chứng minh kernel lỗi.

    Đề cho tâm đáy trên là một ĐIỂM; `20` không phải một độ dài đề cho.
    """
    from app.simulation.semantic_program.grounding_gate import check_grounding

    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(
        _chuong_trinh_height(gia_tri=20)))
    assert not r.ok
    assert any(x.startswith("h|") for x in r.unjustified_literals)


# ══ §8 · BẢO TOÀN NGUỒN VÀ HÌNH HỌC ════════════════════════════════════
def test_20_bat_bien_phuong_trinh_van_bac_2x_z_11():
    g = _chuong_trinh_height(do_bang_measure=True)
    for s in g["statements"]:
        if s.get("kind") == "construct_plane_from_equation":
            s["d"] = 11
    kq = _chay(g)
    assert not kq.servable
    assert kq.source_invariant_stats["violated"] == 1
    assert _dap_so(kq) == DAP_SO          # đáp số ĐÚNG, hình SAI CHỖ


def test_21_diem_vanh_tu_tao_van_chiu_grounding():
    from app.simulation.semantic_program.grounding_gate import check_grounding

    g = _chuong_trinh_height(do_bang_measure=True)
    g["memory_declarations"].append(
        {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0],
         "model_assumption": "Chọn một điểm trên vành đáy dưới."})
    for s in g["statements"]:
        if s.get("kind") == "construct_curved_solid":
            # `radius` và `rim_point` loại trừ nhau ở lược đồ — bỏ `radius`
            # thay vì khai cả hai, nếu không ca này chết ở SCHEMA và không
            # kiểm được điều nó muốn kiểm (grounding).
            s.pop("radius", None)
            s["rim_point"] = "P_rim"
    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(g))
    assert not r.ok
    assert r.error_code == "UNANCHORED_DERIVED_ASSUMPTION"


# ══ §9 · TIÊM LỖI ══════════════════════════════════════════════════════
def test_TIEM_1_khoi_phuc_tren_bang_1_tru_L__parity_VO(monkeypatch):
    """Tiêm đường lỗi CŨ: `tren = 1 − L`, `tren_sq = tren²·|u|²`."""
    goc = CV.intersect_plane_curved_ellipse

    def hong(s, pl):
        u = s.huong_truc
        uu = u.dot(u)
        tam = CV.intersect_line_plane(s.axis, pl)
        L = (tam - s.anchor).dot(u) / uu
        if (1 - L) < 0 or (1 - L) ** 2 * uu < F(64):
            raise GeometryError(CV.ERR_ELIP_CAT_DAY, "tiêm: đường lỗi cũ")
        return goc(s, pl)

    monkeypatch.setattr(CV, "intersect_plane_curved_ellipse", hong)
    pl = mp(2, 0, -1, 10)
    assert phan_quyet(tru_diem(16, 20), pl)[0] is None
    assert phan_quyet(tru_vo_huong(16, 400), pl)[0] == CV.ERR_ELIP_CAT_DAY


def test_TIEM_2_bo_quy_doi_nua_do_lech_ve_cung_thang(monkeypatch):
    """Tiêm: coi `height_sq` như đã ở thang TỈ LỆ (`= 1`) ⇒ nhánh vô hướng vỡ."""
    goc = CV._con_cho_toi_day_tren
    monkeypatch.setattr(CV, "_con_cho_toi_day_tren",
                        lambda hs, ds, hh: goc(F(1), ds, hh))
    assert phan_quyet(tru_vo_huong(16, 400),
                      mp(2, 0, -1, 10))[0] == CV.ERR_ELIP_CAT_DAY


def test_TIEM_3_dao_day_tren_va_day_duoi(monkeypatch):
    """Tiêm: hỏi khoảng hở đáy TRÊN bằng công thức của đáy DƯỚI.

    Ca bất đối xứng: tâm ở `z = 12`, `h_half = 8` ⇒ dưới hở 12, trên hở 8.
    Đảo hai vế thì ca `z = 8` (dưới hở 8, trên hở 12) vẫn qua, nhưng ca sát
    đáy trên phải đổi phán quyết.
    """
    # Tiêm: phép kiểm đáy TRÊN nay hỏi đúng câu của đáy DƯỚI (`duoi ≥ h_half`).
    monkeypatch.setattr(CV, "_con_cho_toi_day_tren",
                        lambda hs, ds, hh: ds >= hh)
    # `d = 13` ⇒ tâm z = 13, dưới hở 13 (≥ 8 ✅) nhưng trên chỉ hở 7 (< 8 ❌).
    # Bản tiêm chỉ nhìn vế dưới nên nó LỌT — ở cả hai cách khai.
    assert phan_quyet(tru_diem(16, 20), mp(2, 0, -1, 13))[0] is None
    assert phan_quyet(tru_vo_huong(16, 400), mp(2, 0, -1, 13))[0] is None


def test_TIEM_4_bo_height_khoi_static_operands(monkeypatch):
    """Tiêm: gỡ `height` khỏi `_TOAN_HANG_LENH` ⇒ sai kiểu đi LỌT."""
    from app.simulation.semantic_program import ir_static_check as IR

    bang = dict(IR._TOAN_HANG_LENH)
    bang["construct_curved_solid"] = tuple(
        t for t in bang["construct_curved_solid"] if t[0] != "height")
    monkeypatch.setattr(IR, "_TOAN_HANG_LENH", bang)

    g = _chuong_trinh_height(do_bang_measure=True)
    for d in g["memory_declarations"]:
        if d["name"] == "h":
            d["type"] = "point3"
    g["statements"] = [s for s in g["statements"]
                       if s.get("target_var") != "h"]
    assert IR.kiem_tinh(SemanticProgramSpec.model_validate(g)).ok


def test_TIEM_5_bo_height_khoi_dependency(monkeypatch):
    """Tiêm: gỡ `height` khỏi `_NGUON_CUA_PHEP_DUNG` ⇒ cây mất mắt xích."""
    from app.simulation.semantic_program import simulation_state as SS

    bang = dict(SS._NGUON_CUA_PHEP_DUNG)
    bang["construct_curved_solid"] = tuple(
        t for t in bang["construct_curved_solid"] if t != "height")
    monkeypatch.setattr(SS, "_NGUON_CUA_PHEP_DUNG", bang)

    spec = SemanticProgramSpec.model_validate(
        _chuong_trinh_height(do_bang_measure=True))
    prov = SS._provenance(spec)
    assert "h" not in (prov["tru"]["sources"] or [])
