# -*- coding: utf-8 -*-
"""TIỀN KIỂM NỀN ĐO cho `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`.

**0 lượt gọi model.** Phải xanh **TRƯỚC** lượt live — §5 của brief nói thẳng:
gold preflight không đạt thì ghi blocker và **dừng trước khi gọi provider**.

Wave này hỏi đúng một câu, và nó là câu về MÔ HÌNH:

    SYSTEM_EXPRESSIBLE        đã chứng minh ở wave trước — bộ test này kiểm lại
    MODEL_DISCOVERABLE        lượt live trả lời; ở đây KHÔNG có dữ liệu nào về nó

Đề khác hai đề elip/nón trước ở một điểm có chủ đích: nó cho **toạ độ tường
minh** và cho mặt phẳng bằng **phương trình**. IR không có `plane_from_equation`,
nên đường duy nhất là ba điểm thoả phương trình + `construct_plane` — và gold
phải chứng minh đường ấy đi được **trước** khi hỏi mô hình có tìm ra nó không.
"""
from __future__ import annotations

import copy
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry import curved as CV
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_oblique_ellipse_fresh import (  # noqa: E402
    CONTAINER, GOLD, ORACLE, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)


def v(x, y, z) -> Vec3:
    return Vec3(F(x), F(y), F(z))


def _hd() -> RequestContract:
    return RequestContract.model_validate(REQUEST_CONTRACT_GOLD)


def _g() -> dict:
    return copy.deepcopy(GOLD)


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _dl(oc) -> dict[str, str]:
    return {k: display(x) for k, x in (oc.final_memory or {}).items()
            if is_exact_number(x)}


def _canh(p: dict) -> dict:
    return _dung_scene3d(SemanticProgramSpec.model_validate(p), _hd()) or {}


def _vat(p: dict) -> dict[str, dict]:
    return {str(o.get("id")): o for o in _canh(p).get("objects", [])}


# ══ A · HAI ORACLE ĐỘC LẬP ═══════════════════════════════════════════════
def test_A1_ORACLE_1_cong_thuc_ban_truc():
    """`b² = r²`, `a² = r²|n|²|u|²/(n·u)²`, `S = π√(a²b²)`."""
    r2, n, u = F(16), v(2, 0, -1), v(0, 0, 20)
    b2 = r2
    a2 = r2 * n.dot(n) * u.dot(u) / (n.dot(u) ** 2)
    assert b2 == F(16) and a2 == F(80)
    assert display(CV.sqrt_rational(b2)) == "4"
    assert display(CV.sqrt_rational(a2)) == "4√5"
    assert display(CV.multiply(CV.sqrt_rational(a2 * b2), CV.PI)) == "16π√5"
    assert ORACLE["area_display"] == "16π√5"


def test_A2_ORACLE_2_the_thang_phuong_trinh_tru_va_mat_phang():
    """Oracle ②: bốn đầu mút trục nằm ĐỒNG THỜI trên mặt trụ và trên `(α)`.

    Không dùng lại `a²`/`b²` của kernel — kiểm bằng toạ độ hữu tỉ độc lập, đọc
    thẳng từ đề: mặt trụ `x² + y² = 16`, mặt phẳng `2x − z + 10 = 0`.
    """
    e = CV.intersect_plane_curved_ellipse(_tru(), _mp())
    C = e.center
    t2 = e.semi_major_sq / e.major_dir.dot(e.major_dir)
    s2 = e.semi_minor_sq / e.minor_dir.dot(e.minor_dir)
    # Cả hai tham số ở ℚ ⇒ bốn đầu mút cũng ở ℚ³.
    #   minor_dir = u × n = (0, 40, 0)        ⇒ |·|² = 1600, s² = 16/1600
    #   major_dir = n × minor_dir = (40, 0, 80) ⇒ |·|² = 8000, t² = 80/8000
    assert t2 == F(1, 100) and s2 == F(1, 100), (t2, s2)
    t = s = F(1, 10)
    dm = [
        Vec3(C.x + t * e.major_dir.x, C.y + t * e.major_dir.y,
             C.z + t * e.major_dir.z),
        Vec3(C.x - t * e.major_dir.x, C.y - t * e.major_dir.y,
             C.z - t * e.major_dir.z),
        Vec3(C.x + s * e.minor_dir.x, C.y + s * e.minor_dir.y,
             C.z + s * e.minor_dir.z),
        Vec3(C.x - s * e.minor_dir.x, C.y - s * e.minor_dir.y,
             C.z - s * e.minor_dir.z),
    ]
    for P in dm:
        assert P.x * P.x + P.y * P.y == F(16), f"{P} KHÔNG trên mặt trụ"
        assert 2 * P.x - P.z + 10 == 0, f"{P} KHÔNG thoả 2x − z + 10 = 0"
    # …và biên dọc khớp `z ∈ [2, 18]` mà oracle khai.
    z = sorted(P.z for P in dm)
    assert z[0] == F(2) and z[-1] == F(18)
    assert ORACLE["z_range"] == "[2, 18]"


def _tru() -> CV.CurvedSolid:
    return CV.CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 20), None,
                          F(16), None, True)


def _mp() -> Plane3:
    """`2x − z + 10 = 0` ⇒ pháp tuyến `(2, 0, −1)`, qua `(0, 0, 10)`."""
    return Plane3(point=v(0, 0, 10), normal=v(2, 0, -1))


def test_A3_tam_va_bien_doc_khop_oracle():
    e = CV.intersect_plane_curved_ellipse(_tru(), _mp())
    assert e.center == v(0, 0, 10) and ORACLE["center"] == "(0, 0, 10)"
    assert display(CV.dien_tich_elip(e)) == "16π√5"


# ══ B · GOLD ĐI TRỌN ĐƯỜNG SẢN PHẨM ══════════════════════════════════════
def test_B1_gold_served_va_dien_tich_CHINH_XAC():
    oc = _chay(GOLD)
    assert oc.stage_reached == "served", oc.details
    assert oc.servable is True
    assert _dl(oc)[WITNESS] == "16π√5"


def test_B2_gold_qua_MOI_tang_khong_tang_nao_bi_bo():
    oc = _chay(GOLD)
    for tang in ("validator", "ir_static", "grounding", "structural_coverage",
                 "source_invariant", "runtime", "postconditions", "execution"):
        assert oc.stage_reached != tang, (tang, oc.details)


def test_B3_bon_vat_deu_dung_producer_va_dependency():
    v_ = _vat(GOLD)
    mong = {
        "tru": ("construct_curved_solid.cylinder", {"O", "Oprime", "r"}),
        "alpha": ("construct_plane", {"P1", "P2", "P3"}),
        "E": ("intersect_plane_curved_ellipse", {"tru", "alpha"}),
        WITNESS: ("measure.area", {"E"}),
    }
    for ten, (prod, dep) in mong.items():
        assert ten in v_, sorted(v_)
        assert v_[ten]["origin"] == "derived", ten
        assert v_[ten]["producer"] == prod, (ten, v_[ten]["producer"])
        assert dep <= set(v_[ten].get("depends") or []), ten


def test_B4_ket_qua_dung_KIEU_ellipse3():
    assert _vat(GOLD)["E"]["type"] == "ellipse3"


def test_B5_Scene3D_co_du_BON_vat_va_sau_truong_exact():
    v_ = _vat(GOLD)
    assert {"tru", "alpha", "E", WITNESS} <= set(v_)
    assert v_["tru"]["render"] == "curved_solid"
    assert v_["alpha"]["render"] == "surface"
    assert v_[WITNESS]["render"] == "readout"
    o = v_["E"]
    assert o["render"] == "ellipse"
    for f in ("center", "normal", "major_dir", "minor_dir",
              "semi_major_sq", "semi_minor_sq"):
        assert f in o, f
    assert o["semi_major_sq"] == "80" and o["semi_minor_sq"] == "16"


def test_B6_trace_co_du_buoc_dung_va_dung_thu_tu():
    ev = _canh(GOLD).get("events") or []
    thu_tu = [e.get("object") for e in ev if e.get("object")]
    for ten in ("tru", "alpha", "E", WITNESS):
        assert ten in thu_tu, (ten, thu_tu)
    for sau, truoc in (("E", "tru"), ("E", "alpha"), (WITNESS, "E")):
        assert thu_tu.index(truoc) < thu_tu.index(sau), (truoc, sau)


def test_B7_bao_dong_phu_thuoc_tu_dien_tich_ve_du_chuoi():
    v_ = _vat(GOLD)
    bao, hd = set(), [WITNESS]
    while hd:
        t = hd.pop()
        for d in (v_.get(t, {}).get("depends") or []):
            if d not in bao:
                bao.add(d)
                hd.append(d)
    assert {"E", "tru", "alpha", "O", "Oprime", "r",
            "P1", "P2", "P3"} <= bao, sorted(bao)


# ══ C · BẢY PHẢN VÍ DỤ ═══════════════════════════════════════════════════
def test_C1_construct_section_cho_khoi_CONG_bi_static_chan():
    """Lớp lỗi `c5b`/`c9b` — `construct_section` nhận khối ĐA DIỆN."""
    p = _g()
    for i, s in enumerate(p["statements"]):
        if s.get("target_var") == "E":
            p["statements"][i] = {"kind": "construct_section",
                                  "target_var": "E", "solid": "tru",
                                  "plane": "alpha"}
    for m in p["memory_declarations"]:
        if m["name"] == "E":
            m["type"] = "section"
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "ir_static"
    assert any("cần solid, có curved_solid" in str(x) for x in oc.details)


@pytest.mark.parametrize("kieu_sai", ["section", "circle3"])
def test_C2_khai_SAI_KIEU_khong_bi_chan__va_dap_so_VAN_DUNG(kieu_sai):
    """⚠️ Ghi HÀNH VI THẬT, không khẳng định một cổng không tồn tại.

    Kiểu **dựng ra** thắng kiểu **khai** ở mọi tầng — `bang_ky_hieu` nói thẳng
    rằng kiểu của vật dựng ra suy dẫn tất định từ `_CHU_KY`, và chương trình
    không bắt buộc khai cho đủ. Đây là hành vi **có sẵn từ trước**, đã ghi ở
    `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION §9`.

    Điều PHẢI đúng, và test này khoá: lời khai sai **không được** làm sai đáp
    số, và cảnh vẫn nhận đúng `ellipse3`.
    """
    p = _g()
    for m in p["memory_declarations"]:
        if m["name"] == "E":
            m["type"] = kieu_sai
    oc = _chay(p)
    assert oc.servable is True and _dl(oc)[WITNESS] == "16π√5"
    assert _vat(p)["E"]["type"] == "ellipse3"


def test_C3_mat_phang_SONG_SONG_truc_bi_kernel_chan():
    """`x = 1` — ba điểm `(1,0,0)`, `(1,1,0)`, `(1,0,5)`."""
    p = _g()
    toa = {"P1": [1, 0, 0], "P2": [1, 1, 0], "P3": [1, 0, 5]}
    for m in p["memory_declarations"]:
        if m["name"] in toa:
            m["initial_value"] = toa[m["name"]]
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "execution"
    assert any("CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE" in str(x)
               for x in oc.details)
    assert any("SONG SONG" in str(x) for x in oc.details)


def test_C4_elip_VUOT_day_bi_chan_bang_ma_rieng():
    """`2x − z + 2 = 0` ⇒ tâm `z = 2`, nửa trục dọc `8` ⇒ vượt đáy dưới."""
    p = _g()
    toa = {"P1": [0, 0, 2], "P2": [1, 0, 4], "P3": [0, 1, 2]}
    for m in p["memory_declarations"]:
        if m["name"] in toa:
            m["initial_value"] = toa[m["name"]]
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "execution"
    assert any("CURVED_ELLIPSE_CROSSES_CAP" in str(x) for x in oc.details)


def test_C5_do_radius_thay_cho_area_bi_static_chan():
    """`radius` không nhận `ellipse3` — elip có HAI bán trục, không một."""
    p = _g()
    for s in p["statements"]:
        if s.get("target_var") == WITNESS:
            s["expr"]["quantity"] = "radius"
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "ir_static"
    assert any("có ellipse3" in str(x) for x in oc.details)


def test_C6_thieu_PRODUCER_cho_elip_bi_chan():
    p = _g()
    p["statements"] = [s for s in p["statements"] if s.get("target_var") != "E"]
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "ir_static"
    assert any("IR_USE_BEFORE_CONSTRUCTION" in str(x) for x in oc.details)


def test_C7_SAI_HE_SO_GOC_cho_dien_tich_KHAC():
    """`1x − z + 10 = 0` thay vì `2x − …` ⇒ `a² = 32`, `S = 16π√2 ≠ 16π√5`.

    ⚠️ Ca này **không** bị một cổng nào chặn, và đó là đúng: mặt phẳng ấy hợp
    lệ về mọi mặt, chỉ **không phải mặt phẳng đề cho**. Thứ bắt nó là phép so
    ĐÁP SỐ — nên test giá trị là tuyến phòng thủ duy nhất ở đây, và nó phải
    tồn tại.
    """
    p = _g()
    for m in p["memory_declarations"]:
        if m["name"] == "P2":
            m["initial_value"] = [1, 0, 11]
    oc = _chay(p)
    assert oc.servable is True
    assert _dl(oc)[WITNESS] == "16π√2"
    assert _dl(oc)[WITNESS] != "16π√5"


# ══ D · ĐỀ MỚI THẬT ══════════════════════════════════════════════════════
def test_D1_de_CHUA_TUNG_xuat_hien_trong_corpus_nao():
    from gold_curved_end_to_end import PROBLEM_TEXT as CONE
    from gold_minimal_card_confirmation import CORPUS as F1F2
    from gold_ratio_ab import CORPUS as R

    cu = {c["problem_text"] for c in list(R) + list(F1F2)} | {CONE}
    assert PROBLEM_TEXT not in cu
    assert CONTAINER == "(E)" and WITNESS == "dien_tich_E"


def test_D2_de_cho_MAT_PHANG_bang_PHUONG_TRINH__IR_NAY_CO_phep_rieng():
    """Tính chất làm đề này khác hai đề trước — ghi thành khẳng định.

    ⚠️ **KHẲNG ĐỊNH ĐÃ ĐẢO CHIỀU, 2026-09-07.** Bản trước tên là
    `…__IR_khong_co_phep_rieng` và khoá đúng một khoảng trống:

        assert not any("equation" in k for k in (*_CHU_KY, *_KIEU_DUNG))

    `PLANE_FROM_EQUATION_REPRESENTATION` đóng khoảng trống ấy, nên dòng trên
    PHẢI đỏ — nó đã làm đúng việc của nó cho tới lúc bị bác bằng một bản sửa.
    Giữ test lại thay vì xoá, vì hai khẳng định còn lại chưa bao giờ nói về
    khoảng trống: đề vẫn cho mặt phẳng bằng phương trình, và ba điểm gold vẫn
    phải thoả nó.

    Đường DỰNG BẰNG BA ĐIỂM **không** bị gỡ và vẫn được gold dùng — phép mới là
    một lối thứ hai, không phải một lối thay thế.
    """
    from app.simulation.semantic_program.ir_static_check import (
        _CHU_KY, _KIEU_DUNG,
    )

    assert "construct_plane_from_equation" in _KIEU_DUNG
    assert _KIEU_DUNG["construct_plane_from_equation"] == "plane3"
    # Nó là CÂU LỆNH, không phải biểu thức: một mặt phẳng dựng từ hằng số
    # không đọc vật nào, nên nó không thuộc `_CHU_KY`.
    assert not any("equation" in k for k in _CHU_KY)
    assert "2x - z + 10 = 0" in PROBLEM_TEXT
    # …và ba điểm gold THẬT SỰ thoả phương trình ấy.
    for m in GOLD["memory_declarations"]:
        if m["name"] in ("P1", "P2", "P3"):
            x, _y, z = m["initial_value"]
            assert 2 * x - z + 10 == 0, m["name"]
