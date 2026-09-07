# -*- coding: utf-8 -*-
"""`PLANE_FROM_EQUATION_REPRESENTATION` — mặt phẳng dựng từ `ax+by+cz+d=0`.

Wave thêm ĐÚNG MỘT phép dựng và ĐÚNG MỘT `kind` bất biến nguồn. Không kiểu bộ
nhớ mới, không module theo-từng-bài.

─── HAI THỨ TEST NÀY CANH, VÀ CHÚNG KHÁC NHAU ─────────────────────────────

**(1) Phép dựng có đúng không** — pháp tuyến, điểm neo, phương trình tỉ lệ,
suy biến. Hỏi thẳng kernel.

**(2) Hệ số có ĐÚNG THEO ĐỀ không** — và đây mới là phần đắt. Bốn hệ số là
hằng viết thẳng trong câu lệnh, nên grounding (chỉ soi `memory_declarations`)
không hỏi chúng câu nào. Thứ gác chúng là `SourceInvariant kind="plane_equation"`
do SERVER đọc từ câu văn của đề.

⚠️ Vì sao (2) không thể bỏ, đo được: mặt phẳng `2x − z + 11 = 0` **song song**
với `2x − z + 10 = 0`, nên thiết diện elip của nó **bằng hệt** — cùng `16π√5`.
Mọi cổng hỏi *đáp số* đều xanh. Chỉ bất biến nguồn hỏi được câu *"mặt phẳng ấy
có phải mặt phẳng đề cho không"*.
"""
from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry.exact import (
    ERR_PT_MAT_PHANG_SUY_BIEN, GeometryError, Plane3, Vec3,
)
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.plane_equation import (
    KIND, KIND_CHUA_GIAI, bat_bien_mat_phang, doc_phuong_trinh, tuong_duong,
)
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_oblique_ellipse_fresh import (  # noqa: E402
    GOLD, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)

#: Phương trình của đề chuẩn, và đáp số đúng.
HE_SO = (F(2), F(0), F(-1), F(10))
DAP_SO = "16π√5"

#: Bốn đầu mút trục của elip — oracle độc lập, thế thẳng vào phương trình.
DAU_MUT = ((4, 0, 18), (-4, 0, 2), (0, 4, 10), (0, -4, 10))


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


def _hd(voi_bat_bien: bool = True) -> RequestContract:
    c = RequestContract.model_validate(REQUEST_CONTRACT_GOLD)
    if voi_bat_bien:
        c = c.model_copy(update={
            "source_invariants": tuple(c.source_invariants or ())
            + bat_bien_mat_phang(c, PROBLEM_TEXT)})
    return c


def _g_phep_moi(**doi) -> dict:
    """Gold, nhưng mặt phẳng dựng bằng PHÉP MỚI thay vì ba điểm."""
    g = copy.deepcopy(GOLD)
    g["memory_declarations"] = [d for d in g["memory_declarations"]
                                if d["name"] not in ("P1", "P2", "P3")]
    lenh = {"kind": "construct_plane_from_equation", "target_var": "alpha",
            "a": 2, "b": 0, "c": -1, "d": 10, "label": "(α)"}
    lenh.update(doi)
    g["statements"] = [lenh if s.get("kind") == "construct_plane" else s
                       for s in g["statements"]]
    return g


def _chay(p: dict, voi_bat_bien: bool = True):
    return verify_and_compile(_hd(voi_bat_bien),
                             SemanticProgramSpec.model_validate(p))


def _dap_so(kq) -> str | None:
    dl = {k: display(x) for k, x in (kq.final_memory or {}).items()
          if is_exact_number(x)}
    return dl.get(WITNESS)


# ══ §8 · CA CHUẨN ═══════════════════════════════════════════════════════
def test_01_phap_tuyen_va_diem_neo_canonical():
    mp = Plane3.from_equation(*HE_SO)
    assert mp.normal == v(2, 0, -1)
    # `a ≠ 0` ⇒ toàn bộ `−d` dồn vào trục x.
    assert mp.point == v(-5, 0, 0)


def test_02_diem_tren_mat_phang_kiem_CHINH_XAC():
    mp = Plane3.from_equation(*HE_SO)
    assert mp.signed_eval(v(0, 0, 10)) == 0
    for p in DAU_MUT:
        assert mp.signed_eval(v(*p)) == 0, p


def test_03_giao_hinh_tru_tra_dung_elip_va_dien_tich():
    kq = _chay(_g_phep_moi())
    assert kq.servable, (kq.error_code, kq.stage_reached)
    assert _dap_so(kq) == DAP_SO


def test_04_diem_neo_KHONG_phai_diem_cua_de():
    """Điểm neo là chi tiết thực thi — nó KHÔNG được thành một vật có tên."""
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(
        SemanticProgramSpec.model_validate(_g_phep_moi()), _hd()) or {}
    ten = {str(o.get("id")) for o in canh.get("objects", [])}
    assert "alpha" in ten
    # Không vật nào mang toạ độ `(-5,0,0)` như một ĐIỂM riêng.
    diem = [o for o in canh.get("objects", []) if o.get("type") == "point3"]
    assert all(o.get("point") != ["-5", "0", "0"] for o in diem)


# ══ §8 · TƯƠNG ĐƯƠNG ════════════════════════════════════════════════════
@pytest.mark.parametrize("he", [
    (2, 0, -1, 10),
    (-4, 0, 2, -20),          # nhân −2
    (1, 0, "-1/2", 5),        # chia 2, hệ số phân số
    (2, 0, -1, 10),           # `2x - z = -10` sau khi chuyển vế
])
def test_05_phuong_trinh_ti_le_CUNG_mot_mat_phang(he):
    a, b, c, d = he
    kq = _chay(_g_phep_moi(a=a, b=b, c=c, d=d))
    assert kq.servable, (he, kq.error_code, kq.stage_reached)
    assert _dap_so(kq) == DAP_SO, he


def test_06_ti_le_o_muc_KERNEL_cung_dung():
    """Hai `Plane3` khác dữ liệu nhưng bằng nhau về HÌNH."""
    p = Plane3.from_equation(*HE_SO)
    q = Plane3.from_equation(F(-4), F(0), F(2), F(-20))
    assert p.normal != q.normal          # dữ liệu KHÁC
    assert p.point == q.point
    for pt in DAU_MUT:                   # hình GIỐNG
        assert q.signed_eval(v(*pt)) == 0


# ══ §8 · BA TRỤC CANONICAL ══════════════════════════════════════════════
@pytest.mark.parametrize("he,neo,phap", [
    ((1, 0, 0, -3), (3, 0, 0), (1, 0, 0)),      # x = 3
    ((0, 1, 0, 2), (0, -2, 0), (0, 1, 0)),      # y = −2
    ((0, 0, 1, -10), (0, 0, 10), (0, 0, 1)),    # z = 10
])
def test_07_truc_canonical(he, neo, phap):
    mp = Plane3.from_equation(*[F(x) for x in he])
    assert mp.point == v(*neo)
    assert mp.normal == v(*phap)


# ══ §8 · PHẢN VÍ DỤ ═════════════════════════════════════════════════════
def test_08_he_so_suy_bien_chan_o_LUOC_DO():
    """Bắt ở lược đồ, vì lỗi lược đồ ĐI NGƯỢC về mô hình qua vòng sửa."""
    with pytest.raises(Exception) as e:
        SemanticProgramSpec.model_validate(_g_phep_moi(a=0, b=0, c=0, d=5))
    assert "(0, 0, 0)" in str(e.value)


def test_09_he_so_suy_bien_KERNEL_cung_giu_tien_dieu_kien():
    """Hàng phòng thủ thứ hai — `Plane3.from_equation` là hàm CÔNG KHAI."""
    with pytest.raises(GeometryError) as e:
        Plane3.from_equation(F(0), F(0), F(0), F(5))
    assert e.value.code == ERR_PT_MAT_PHANG_SUY_BIEN


def test_10_sai_MOT_he_so_so_voi_de__bat_bien_nguon_TU_CHOI():
    kq = _chay(_g_phep_moi(a=3))
    assert not kq.servable


def test_11_dung_ba_he_so_SAI_d__van_bi_tu_choi():
    """⚠️ Ca đắt nhất của cả wave, và là lý do bất biến nguồn phải tồn tại.

    `2x − z + 11 = 0` SONG SONG với mặt phẳng đề cho, nên thiết diện elip
    **bằng hệt** — `16π√5`, đúng đáp số. Mọi cổng hỏi *đáp số* đều xanh; hình
    thì sai chỗ. Chỉ câu hỏi *"mặt phẳng có đúng mặt phẳng đề cho không"* bắt
    được, và câu ấy chỉ trả lời được bằng dữ liệu server tự đọc từ đề.
    """
    kq = _chay(_g_phep_moi(d=11))
    assert not kq.servable
    assert kq.error_code == "postcondition_violated"
    assert kq.source_invariant_stats["violated"] == 1
    # …và đáp số VẪN đúng — bằng chứng cho câu trên.
    assert _dap_so(kq) == DAP_SO


def test_12_he_so_khong_doc_duoc_thanh_phan_so():
    with pytest.raises(Exception) as e:
        SemanticProgramSpec.model_validate(_g_phep_moi(a="hai"))
    assert "hữu tỉ" in str(e.value)


def test_13_he_so_khong_nhan_BIEU_THUC():
    """Ô này nhận SỐ. Một biểu thức lồng vào là mở lại kênh R0 vừa đóng."""
    with pytest.raises(Exception):
        SemanticProgramSpec.model_validate(
            _g_phep_moi(a={"kind": "literal", "value": 2}))


def test_14_toan_hang_chua_dung__van_bi_ir_static_chan():
    """Phép mới KHÔNG nới lỏng luật dựng-trước-dùng cho các vật khác."""
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    g = _g_phep_moi()
    g["statements"] = [s for s in g["statements"]
                       if s.get("kind") != "construct_curved_solid"]
    r = kiem_tinh(SemanticProgramSpec.model_validate(g))
    assert not r.ok
    assert any(i.error_code == "IR_USE_BEFORE_CONSTRUCTION" for i in r.issues)


# ══ §7 · BỘ ĐỌC PHƯƠNG TRÌNH ════════════════════════════════════════════
@pytest.mark.parametrize("s,mong", [
    ("2x - z + 10 = 0", (2, 0, -1, 10)),
    ("-2x + z - 10 = 0", (-2, 0, 1, -10)),      # đổi dấu toàn bộ
    ("4x - 2z + 20 = 0", (4, 0, -2, 20)),       # nhân 2
    ("-z + 2x + 10 = 0", (2, 0, -1, 10)),       # đổi thứ tự hạng tử
    ("x - z + 5 = 0", (1, 0, -1, 5)),           # hệ số 1 viết ẩn
    ("-x + z = 0", (-1, 0, 1, 0)),              # hệ số −1 viết ẩn
    ("2x - z = -10", (2, 0, -1, 10)),           # chuyển vế
    ("x - z/2 + 5 = 0", (1, 0, "-1/2", 5)),     # hệ số phân số
    ("x + y + z = 1", (1, 1, 1, -1)),           # đủ ba biến
])
def test_15_doc_phuong_trinh(s, mong):
    assert doc_phuong_trinh(s) == tuple(F(x) for x in mong), s


@pytest.mark.parametrize("s", [
    "2x + my - z + 10 = 0",   # tham số — NGOÀI ngưỡng V1
    "x^2 + y^2 = 9",          # không tuyến tính
    "0 = 0",                  # không phải mặt phẳng nào
    "3 = 5",                  # cũng không
    "2x 3 = 0",               # chuỗi hỏng: thiếu dấu giữa hai hạng tử
    "2x - z + 10",            # thiếu dấu `=`
    "2x = z = 0",             # hai dấu `=`
])
def test_16_khong_doc_bua_mot_nua(s):
    assert doc_phuong_trinh(s) is None, s


@pytest.mark.parametrize("u,v_,mong", [
    (("2", "0", "-1", "10"), ("2", "0", "-1", "10"), True),
    (("2", "0", "-1", "10"), ("-4", "0", "2", "-20"), True),
    (("2", "0", "-1", "10"), ("1", "0", "-1/2", "5"), True),
    (("2", "0", "-1", "10"), ("2", "0", "-1", "11"), False),   # lệch d
    (("2", "0", "-1", "10"), ("2", "0", "-1", "-10"), False),  # đổi dấu RIÊNG d
    (("2", "0", "-1", "10"), ("3", "0", "-1", "10"), False),
    (("2", "0", "-1", "10"), ("0", "0", "0", "0"), False),     # λ phải khác 0
])
def test_17_tuong_duong_TI_LE_chinh_xac(u, v_, mong):
    assert tuong_duong(u, v_) is mong, (u, v_)


# ══ §7 · BỘ PHÁT BẤT BIẾN ═══════════════════════════════════════════════
def test_18_phat_dung_MOT_bat_bien_cho_de_chuan():
    bb = bat_bien_mat_phang(RequestContract.model_validate(REQUEST_CONTRACT_GOLD),
                            PROBLEM_TEXT)
    assert len(bb) == 1
    assert bb[0].kind == KIND
    assert tuple(bb[0].coefficients) == ("2", "0", "-1", "10")
    assert bb[0].source_fact_id == "mat_phang_alpha"


def test_19_KHONG_phat_khi_khong_co_cum_mat_phang():
    """`2x + 3 = 7` trong một bài bất kỳ KHÔNG được thành một mặt phẳng."""
    c = RequestContract.model_validate(
        {"problem_text": "Giải phương trình 2x + 3 = 7.", "input_facts": [],
         "obligations": []})
    assert bat_bien_mat_phang(c, "Giải phương trình 2x + 3 = 7.") == ()


def test_20_cum_mat_phang_nhung_KHONG_co_bien__im_lang():
    """*"diện tích mặt phẳng … = 12"* là câu về ĐỘ LỚN, không phải mặt phẳng.

    Biến nó thành `plane_equation_unresolved` sẽ CHẶN OAN cả một lớp đề.
    """
    t = "Cho hình chóp. Diện tích mặt phẳng đáy = 12."
    c = RequestContract.model_validate(
        {"problem_text": t, "input_facts": [], "obligations": []})
    assert bat_bien_mat_phang(c, t) == ()


def test_21_thay_ma_khong_giai_duoc__CHAN_chu_khong_doan():
    t = "Mặt phẳng (α): 2x + my - z + 10 = 0 cắt hình trụ."
    c = RequestContract.model_validate(
        {"problem_text": t, "input_facts": [], "obligations": []})
    bb = bat_bien_mat_phang(c, t)
    assert len(bb) == 1 and bb[0].kind == KIND_CHUA_GIAI


def test_22_bat_bien_chua_giai_LAM_CHAN_chuong_trinh():
    """`unresolved` phải CHẶN, cùng khuôn `segment_division_unresolved`."""
    c = _hd(voi_bat_bien=False)
    from app.simulation.semantic_program.scale_normalization import (
        SourceInvariant,
    )

    c = c.model_copy(update={"source_invariants": (
        SourceInvariant(kind=KIND_CHUA_GIAI, points=(), expected="",
                        coefficients=(), source_fact_id="mat_phang_alpha",
                        scale_symbol="", source_text="2x + my - z + 10 = 0"),)})
    kq = verify_and_compile(
        c, SemanticProgramSpec.model_validate(_g_phep_moi()))
    assert not kq.servable
    assert kq.source_invariant_stats["unresolved"] == 1


def test_23_phat_MOT_ban_du_phuong_trinh_xuat_hien_hai_cho():
    """Đề VÀ mục dữ kiện cùng chứa phương trình ⇒ vẫn chỉ một bất biến."""
    bb = bat_bien_mat_phang(
        RequestContract.model_validate(REQUEST_CONTRACT_GOLD), PROBLEM_TEXT)
    assert len(bb) == 1


# ══ §9 · BẢO TOÀN GROUNDING ═════════════════════════════════════════════
def test_24_duong_BA_DIEM_van_chiu_nguyen_luat_grounding():
    """Phép mới là một lối THỨ HAI, không phải một lối nới lỏng.

    Ba điểm khai bằng `model_assumption` (không `source_fact_id`) vẫn phải
    chết ở grounding y như trước wave này.
    """
    from app.simulation.semantic_program.grounding_gate import check_grounding

    g = copy.deepcopy(GOLD)
    for d in g["memory_declarations"]:
        if d["name"] in ("P1", "P2", "P3"):
            d.pop("source_fact_id", None)
    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(g))
    assert not r.ok
    assert r.error_code == "UNANCHORED_DERIVED_ASSUMPTION"


def test_25_duong_BA_DIEM_dung_van_di_duoc__va_bat_bien_moi_KIEM_luon_no():
    """Bất biến hỏi trên HÌNH, nên nó phủ cả lối cũ."""
    kq = _chay(GOLD)
    assert kq.servable
    assert kq.source_invariant_stats["passed"] >= 1
    assert _dap_so(kq) == DAP_SO


def test_26_ba_diem_SAI_mat_phang__bat_bien_moi_bat_duoc():
    """Lối cũ dựng sai mặt phẳng thì cũng trượt — không có cửa sau."""
    g = copy.deepcopy(GOLD)
    for d in g["memory_declarations"]:
        if d["name"] == "P1":
            d["initial_value"] = [0, 0, 11]
        if d["name"] == "P2":
            d["initial_value"] = [1, 0, 13]
        if d["name"] == "P3":
            d["initial_value"] = [0, 1, 11]
    kq = _chay(g)
    assert not kq.servable
    assert kq.source_invariant_stats["violated"] == 1


def test_27_khai_bao_muc_tieu_KHONG_can_xuat_xu_vi_no_duoc_DUNG():
    """`alpha` do câu lệnh sinh ⇒ grounding bỏ qua khai báo của nó.

    Đây là chỗ wave đổi được lời khai xuất xứ từ *không trung thực* sang
    *không cần khai*: mặt phẳng là HỆ QUẢ của bốn hệ số, và bốn hệ số ấy được
    server đối chiếu thẳng với đề.
    """
    from app.simulation.semantic_program.grounding_gate import check_grounding

    r = check_grounding(_hd(), SemanticProgramSpec.model_validate(_g_phep_moi()))
    assert r.ok
    assert not any(x.startswith("alpha|") for x in r.unjustified_literals)


# ══ §10 · TRACE VÀ SCENE3D ══════════════════════════════════════════════
def test_28_dung_MOT_buoc_dung_va_loi_ke_noi_PHUONG_TRINH():
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(
        SemanticProgramSpec.model_validate(_g_phep_moi()), _hd()) or {}
    buoc = [e for e in canh.get("events", []) if e.get("object") == "alpha"]
    assert len(buoc) == 1
    assert buoc[0]["action"] == "CREATE"
    assert buoc[0]["depends"] == []
    assert "2x - z + 10 = 0" in buoc[0]["explanation"]


def test_29_loi_ke_KHONG_nhac_diem_neo_canonical():
    """Điểm neo là chi tiết thực thi. Gọi tên nó là dạy một điểm đề không có."""
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(
        SemanticProgramSpec.model_validate(_g_phep_moi()), _hd()) or {}
    ke = next(e["explanation"] for e in canh.get("events", [])
              if e.get("object") == "alpha")
    assert "-5" not in ke and "−5" not in ke


def test_30_mat_phang_vao_canh_voi_du_diem_va_phap_tuyen():
    from app.ai.pipeline import _dung_scene3d

    canh = _dung_scene3d(
        SemanticProgramSpec.model_validate(_g_phep_moi()), _hd()) or {}
    o = next(x for x in canh["objects"] if x["id"] == "alpha")
    assert o["type"] == "plane3" and o["render"] == "surface"
    assert o["point"] == ["-5", "0", "0"] and o["normal"] == ["2", "0", "-1"]
    assert o["producer"] == "construct_plane_from_equation"
    # Mọi số là CHUỖI phân số — không `float` nào lọt xuống renderer.
    assert all(isinstance(x, str) for x in o["point"] + o["normal"])


def test_31_viet_phuong_trinh_theo_loi_SGK():
    """Hạng tử 0 lược, hệ số ±1 ẩn — `1x + 0y` đọc như lỗi chính tả."""
    from app.simulation.semantic_program.geometry_exec import _viet_pt

    assert _viet_pt(F(2), F(0), F(-1), F(10)) == "2x - z + 10 = 0"
    assert _viet_pt(F(1), F(0), F(0), F(-3)) == "x - 3 = 0"
    assert _viet_pt(F(-1), F(1), F(0), F(0)) == "-x + y = 0"


# ══ §6 · THẨM QUYỀN — DẪN XUẤT, KHÔNG CHÉP TAY ══════════════════════════
def test_32_dang_ky_o_DUNG_MOT_bang_va_moi_consumer_dan_tu_no():
    from app.simulation.semantic_program.coverage_gate import _producers
    from app.simulation.semantic_program.ir_static_check import (
        _CHU_KY, _KIEU_DUNG, _TOAN_HANG_LENH,
    )
    from app.simulation.semantic_program.simulation_state import (
        _NGUON_CUA_PHEP_DUNG,
    )

    assert _KIEU_DUNG["construct_plane_from_equation"] == "plane3"
    # KHÔNG có toán hạng TÊN — sự VẮNG MẶT ở đây là một khẳng định.
    assert "construct_plane_from_equation" not in _TOAN_HANG_LENH
    assert "construct_plane_from_equation" not in _CHU_KY
    # …và đăng ký TƯỜNG MINH là rỗng ở bảng xuất xứ, để câu ấy đọc được.
    assert _NGUON_CUA_PHEP_DUNG["construct_plane_from_equation"] == ()
    # `_producers` DẪN từ `_KIEU_DUNG`, nên nó tự biết.
    spec = SemanticProgramSpec.model_validate(_g_phep_moi())
    assert "alpha" in _producers(spec.statements)


def test_33_the_van_pham_SINH_tu_lang_ke_khong_viet_tay():
    from app.simulation.semantic_program.grammar_card import grammar_card

    the = grammar_card("hinh_hoc")
    dong = [d for d in the.splitlines()
            if "construct_plane_from_equation" in d]
    assert len(dong) == 1
    for o in ("a:", "b:", "c:", "d:"):
        assert o in dong[0]
    assert "ax+by+cz+d=0" in dong[0]
    assert "plane3" in the


def test_34_nhan_kieu_o_so_tran_dan_TU_KIEU_khong_tu_ten_truong():
    """Luật một dòng cho MỌI ô `int | str`, không phải bảng ngoại lệ."""
    import typing

    from app.simulation.semantic_program.grammar_card import _kieu

    assert _kieu(typing.Union[int, str]) == "số hữu tỉ THÔ"


def test_35_validator_khong_coi_lenh_moi_la_KHONG_HO_TRO():
    from app.simulation.semantic_program.validator import (
        validate_semantic_program,
    )

    kq = validate_semantic_program(_g_phep_moi())
    assert kq.ok, kq.error


# ══ §12 · TIÊM LỖI ══════════════════════════════════════════════════════
def test_TIEM_1_bo_qua_d_khi_so_ti_le__ca_sai_d_LOT_QUA(monkeypatch):
    """Tiêm: `tuong_duong` chỉ so `(a,b,c)`. Ca `d = 11` phải LỌT."""
    from app.simulation.semantic_program import postconditions as P

    monkeypatch.setattr(
        P, "tuong_duong",
        lambda u, v_: tuong_duong(tuple(u)[:3] + ("0",),
                                  tuple(v_)[:3] + ("0",)),
        raising=False)
    # Bản tiêm được nhập BÊN TRONG hàm, nên phải vá ở module SỞ HỮU nó.
    import app.simulation.semantic_program.plane_equation as PE

    monkeypatch.setattr(
        PE, "tuong_duong",
        lambda u, v_: tuple(F(x) for x in u)[:3] == tuple(F(x) for x in v_)[:3])
    kq = _chay(_g_phep_moi(d=11))
    assert kq.servable, "tiêm không có hiệu lực — test_11 chưa chứng minh gì"


def test_TIEM_2_bo_kiem_suy_bien_o_LUOC_DO__KERNEL_van_giu(monkeypatch):
    """Tiêm: gỡ kiểm `(a,b,c)≠0` ở lược đồ ⇒ ca suy biến qua được tầng ấy.

    Và đó chính là lúc đo được **hàng phòng thủ thứ hai**: kernel vẫn ném
    `PLANE_EQUATION_DEGENERATE`, nên chương trình chết ở `execution` thay vì
    được phục vụ. Hai tầng, hai câu trả lời khác nhau — không phải nhân đôi.
    """
    import app.simulation.semantic_program.contract as C

    monkeypatch.setattr(
        C.ConstructPlaneFromEquationStmt, "_he_so_huu_ti_va_khong_suy_bien",
        classmethod(lambda cls, v: v), raising=False)
    # Lược đồ đã vá vẫn không dựng nổi hình: kernel giữ tiền điều kiện.
    with pytest.raises(GeometryError) as e:
        Plane3.from_equation(F(0), F(0), F(0), F(5))
    assert e.value.code == ERR_PT_MAT_PHANG_SUY_BIEN


def test_TIEM_3_bo_bat_bien_nguon__hinh_SAI_duoc_phuc_vu():
    """Tiêm: không phát bất biến ⇒ `2x − z + 11 = 0` `served` với đáp số ĐÚNG.

    Đây là số đo nói rõ nhất vì sao tầng bất biến phải có: mất nó thì hệ phục
    vụ một hình SAI CHỖ kèm một đáp số ĐÚNG, và không cổng nào kêu.
    """
    kq = _chay(_g_phep_moi(d=11), voi_bat_bien=False)
    assert kq.servable
    assert _dap_so(kq) == DAP_SO


def test_TIEM_4_diem_neo_SAI__phuong_trinh_khong_con_thoa(monkeypatch):
    """Tiêm: điểm neo dồn `−d` vào SAI trục ⇒ mặt phẳng lệch."""
    from app.simulation.geometry import exact as E

    goc = E.Plane3.from_equation

    def hong(a, b, c, d):
        n = Vec3(F(a), F(b), F(c))
        return E.Plane3(Vec3(F(0), F(0), -F(d)), n)   # luôn dồn vào z

    monkeypatch.setattr(E.Plane3, "from_equation", staticmethod(hong))
    mp = E.Plane3.from_equation(F(2), F(0), F(-1), F(10))
    assert mp.signed_eval(v(0, 0, 10)) != 0, "tiêm không có hiệu lực"
    monkeypatch.setattr(E.Plane3, "from_equation", staticmethod(goc))
    assert E.Plane3.from_equation(*HE_SO).signed_eval(v(0, 0, 10)) == 0


def test_TIEM_5_go_dang_ky_producer__witness_mat_nguoi_dung(monkeypatch):
    """Tiêm: gỡ lệnh khỏi `_KIEU_DUNG` ⇒ `_producers` mất nó, cổng phủ kêu."""
    from app.simulation.semantic_program import ir_static_check as IR
    from app.simulation.semantic_program.coverage_gate import _producers

    bang = dict(IR._KIEU_DUNG)
    bang.pop("construct_plane_from_equation")
    monkeypatch.setattr(IR, "_KIEU_DUNG", bang)
    import app.simulation.semantic_program.coverage_gate as CG

    monkeypatch.setattr(CG, "_KIEU_DUNG", bang)
    spec = SemanticProgramSpec.model_validate(_g_phep_moi())
    assert "alpha" not in _producers(spec.statements)


# ══ §11 · REPLAY NGUYÊN BYTE ════════════════════════════════════════════
def test_36_replay_attempt_1_QUA_DUOC_ir_static():
    """Khẳng định TRUNG TÂM của wave, đo trên chính ứng viên mô hình đã viết.

    Trước wave: attempt 1 chết ở **schema** (`Input tag
    'construct_plane_from_equation' … does not match any of the expected
    tags`). Nay nó qua schema VÀ qua `ir_static` — tức đúng hai tầng đã chặn
    lối biểu đạt này đều đã thông.
    """
    from replay_plane_from_equation import nap
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    tho, _ = nap()
    spec = SemanticProgramSpec.model_validate(json.loads(tho[1]))
    assert kiem_tinh(spec).ok


def test_37_replay_minimal_delta_toi_SERVED_voi_dap_so_dung():
    """Delta HAI TRƯỜNG, và không trường nào thuộc câu lệnh mặt phẳng.

    Phần còn tắc của attempt 1 là một lỗ **có sẵn, không liên quan wave**: mô
    hình bịa điểm vành `P_rim` cho hình trụ trong khi chính nó đã khai `R` với
    `source_fact_id`. Đó là ca `ball_2` mà `ConstructCurvedSolidStmt` đã ghi.
    """
    from replay_plane_from_equation import hop_dong, minimal_delta, nap

    tho, phan_tich = nap()
    delta, ly_do = minimal_delta(tho[1])
    assert len(ly_do) == 2
    goc, moi = json.loads(tho[1]), json.loads(delta)
    mp = [s for s in goc["statements"]
          if s["kind"] == "construct_plane_from_equation"]
    assert mp == [s for s in moi["statements"]
                  if s["kind"] == "construct_plane_from_equation"]

    kq = verify_and_compile(hop_dong(phan_tich),
                            SemanticProgramSpec.model_validate(moi))
    assert kq.servable, (kq.error_code, kq.stage_reached)
    assert _dap_so(kq) == DAP_SO
    # ⚠️ 1 → 3 (2026-09-08, `POINT_COORDINATE_SOURCE_INVARIANT`). Đề này cho
    # toạ độ HAI tâm đáy — `O(0,0,0)` và `O'(0,0,20)` — nên nay có thêm hai
    # bất biến toạ độ, và **cả hai ĐẠT**. Chương trình không đổi một byte;
    # thứ đổi là số câu hỏi hệ biết hỏi về nó.
    #
    # Ghim cả `violated == 0`: nếu con số `3` một ngày nào đó đạt được bằng
    # cách khác — thêm bất biến rồi để chúng trượt — thì ô này phải đỏ.
    assert kq.source_invariant_stats["passed"] == 3
    assert kq.source_invariant_stats["violated"] == 0
    assert kq.source_invariant_stats["not_checkable"] == 0
