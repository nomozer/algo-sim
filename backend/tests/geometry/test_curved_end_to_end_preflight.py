# -*- coding: utf-8 -*-
"""TIỀN KIỂM NỀN ĐO cho `CURVED_END_TO_END_FRESH_CONFIRMATION`.

**0 lượt gọi model.** Phải xanh **TRƯỚC** lượt live: nền đo không tự đứng được
thì con số lượt live không nói lên điều gì
(`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`).

Wave này khác mọi wave A/B trước ở chỗ nó đo **cả đường sản phẩm** — có
`analyze`, có vòng sửa. Nên tiền kiểm phải trả lời hai câu **tách bạch**:

    SYSTEM_EXPRESSIBLE      hệ CÓ diễn đạt được bài này không  (bộ test này)
    MODEL_DISCOVERABILITY   mô hình có TỰ tìm ra đường ấy không  (lượt live)

Trộn hai câu là cách chắc chắn để một lượt live hỏng bị đọc thành "hệ thiếu
năng lực", hoặc ngược lại.
"""
from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_curved_end_to_end import (  # noqa: E402
    CONTAINER, GOLD, LY_DO_GOC, ORACLE, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD,
    WITNESS,
)


def _hd() -> RequestContract:
    """Hợp đồng + source invariants, y như `build_request_contract` gắn."""
    rc = RequestContract.model_validate(REQUEST_CONTRACT_GOLD)
    return rc.model_copy(update={"source_invariants": (
        SR.bat_bien_do_dai(rc, rc.problem_text)
        + SR.bat_bien_chia_doan(rc, rc.problem_text))})


def _g() -> dict:
    return copy.deepcopy(GOLD)


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _dl(oc) -> dict[str, str]:
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


def _canh(p: dict) -> dict:
    return _dung_scene3d(SemanticProgramSpec.model_validate(p), _hd()) or {}


def _vat(p: dict) -> dict[str, dict]:
    return {str(o.get("id")): o for o in _canh(p).get("objects", [])}


# ══ A · ORACLE TỰ NHẤT QUÁN — kiểm bằng số học, không bằng niềm tin ══════
def test_A1_oracle_tu_kiem_bang_hai_loi_tinh():
    """`r(c)` tính hai cách phải ra một số.

    Cách 1 — tỉ lệ trên trục: `r = R · ST/SO`.
    Cách 2 — chiều cao còn lại tính từ đáy: `r = R · (1 − OT/SO)`.
    Nếu oracle sai, hai lối này lệch nhau.
    """
    R, t = Fraction(ORACLE["ban_kinh_day"]), Fraction(ORACLE["t_S_den_O"])
    assert R * t == Fraction(ORACLE["radius_c"])
    # `T` cách đáy `SO·(1−t)` ⇒ bán kính tại đó cũng bằng `R·t`.
    SO = Fraction(ORACLE["chieu_cao"])
    cao_tren_day = SO * (1 - t)
    assert R * (1 - cao_tren_day / SO) == Fraction(ORACLE["radius_c"]) == 4


def test_A2_bat_bien_nguon_DAN_XUAT_khop_oracle():
    """Bộ đọc đề của SẢN PHẨM phải tự ra `1/3` và `18` — không do ta gán."""
    bt = {b.kind: b for b in _hd().source_invariants}
    assert set(bt) == {"segment_length", "segment_division"}
    assert bt["segment_division"].expected == ORACLE["t_S_den_O"] == "1/3"
    assert bt["segment_length"].expected == ORACLE["chieu_cao"] == "18"
    assert set(bt["segment_division"].points) == {"S", "O", "T"}


def test_A3_KERNEL_doc_lap_cho_dung_ban_kinh_4():
    """Kiểm chéo ở tầng KERNEL, không đi qua IR — hai đường tới cùng một số."""
    from app.simulation.geometry import curved as CV
    from app.simulation.geometry.exact import Vec3
    from app.simulation.geometry.kernel import Plane3

    non = CV.CurvedSolid(
        kind="cone", anchor=Vec3(Fraction(0), Fraction(0), Fraction(0)),
        apex_or_top=Vec3(Fraction(0), Fraction(0), Fraction(18)),
        rim_point=None, radius_sq_khai=Fraction(144), height_sq_khai=None,
        pose_canonical=True)
    T = Vec3(Fraction(0), Fraction(0), Fraction(12))
    c = CV.intersect_plane_curved(
        non, Plane3(point=T, normal=Vec3(Fraction(0), Fraction(0), Fraction(1))))
    assert display(CV.ban_kinh(c)) == "4"


# ══ B · GOLD ĐI TRỌN MỌI TẦNG ════════════════════════════════════════════
def test_B1_gold_served_va_dap_so_CHINH_XAC():
    oc = _chay(GOLD)
    assert oc.stage_reached == "served", oc.details
    assert oc.servable is True
    assert _dl(oc)[WITNESS] == ORACLE["radius_c"] == "4"


def test_B2_gold_qua_moi_tang_khong_tang_nao_bi_bo():
    oc = _chay(GOLD)
    for tang in ("ir_static", "grounding", "structural_coverage",
                 "source_invariant", "runtime", "postconditions"):
        assert oc.stage_reached != tang, (tang, oc.details)


def test_B3_NAM_phep_dung_deu_co_producer_va_dependency_dung():
    v = _vat(GOLD)
    mong = {
        "non": ("construct_curved_solid.cone", {"O", "S", "r_day"}),
        "truc_SO": ("construct_line", {"O", "S"}),
        "T": ("construct_point.divide_segment", {"O", "S"}),
        "mp_cat": ("plane_perpendicular_to_line", {"T", "truc_SO"}),
        "c": ("intersect_plane_curved", {"mp_cat", "non"}),
        WITNESS: ("measure.radius", {"c"}),
    }
    for ten, (prod, dep) in mong.items():
        assert ten in v, sorted(v)
        assert v[ten]["origin"] == "derived", ten
        assert v[ten]["producer"] == prod, (ten, v[ten]["producer"])
        assert dep <= set(v[ten].get("depends") or []), ten


def test_B4_duong_tron_c_dung_KIEU_circle3():
    """`radius` không nhận `section`; nếu (c) ra `section` thì cả bài sai đường."""
    assert _vat(GOLD)["c"]["type"] == "circle3"


def test_B5_hai_diem_dau_vao_TU_DO_con_lai_deu_DAN_XUAT():
    v = _vat(GOLD)
    assert {t for t, o in v.items() if o["origin"] == "free"} == {"O", "S", "r_day"}


def test_B6_trace_co_du_buoc_va_DUNG_THU_TU_dung():
    ev = _canh(GOLD).get("events") or []
    thu_tu = [e.get("object") for e in ev if e.get("object")]
    for ten in ("non", "truc_SO", "T", "mp_cat", "c", WITNESS):
        assert ten in thu_tu, (ten, thu_tu)
    # Vật chỉ xuất hiện SAU thứ nó phụ thuộc.
    for sau, truoc in (("mp_cat", "T"), ("c", "mp_cat"), (WITNESS, "c"),
                       ("mp_cat", "truc_SO"), ("c", "non")):
        assert thu_tu.index(truoc) < thu_tu.index(sau), (truoc, sau)


def test_B7_T_nam_dung_cho_tren_truc():
    """`T = (0,0,12)` — cách đáy 12, tức 1/3 trục tính từ đỉnh."""
    ev = _canh(GOLD).get("events") or []
    noi_ve_T = [e for e in ev if e.get("object") == "T"]
    assert noi_ve_T and "(0, 0, 12)" in noi_ve_T[0]["explanation"], noi_ve_T


# ══ C · SÁU PHẢN VÍ DỤ — mỗi cái CHẶN Ở ĐÚNG TẦNG CỦA NÓ ════════════════
def test_C1_ratio_SAI_trong_doan_bi_source_invariant_chan():
    p = _g()
    for s in p["statements"]:
        if s.get("target_var") == "T":
            s["expr"]["ratio"] = "1/2"
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "source_invariant"
    assert any("NORMALIZED_SOURCE_VIOLATED" in str(x) for x in oc.details)


def test_C2_T_khai_thang_toa_do_bi_derived_point_guard_chan():
    p = _g()
    for m in p["memory_declarations"]:
        if m["name"] == "T":
            m["initial_value"] = [0, 0, 12]
            m["model_assumption"] = LY_DO_GOC
    p["statements"] = [s for s in p["statements"]
                       if s.get("target_var") != "T"]
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "grounding"
    assert any("DERIVED_ENTITY_WITHOUT_PRODUCER" in str(x) for x in oc.details)


def test_C3_toa_do_TRAI_chieu_cao_de_cho_bi_segment_length_chan():
    p = _g()
    for m in p["memory_declarations"]:
        if m["name"] == "S":
            m["initial_value"] = [0, 0, 99]
            m.pop("source_fact_id", None)
            m["model_assumption"] = LY_DO_GOC
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "source_invariant"
    assert any("OS = 18" in str(x) for x in oc.details), oc.details


def test_C4_giao_voi_SAI_KIEU_bi_static_checker_chan():
    p = _g()
    for s in p["statements"]:
        if s.get("target_var") == "c":
            s["expr"]["solid"] = "truc_SO"
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "ir_static"
    assert any("IR_OPERAND_TYPE" in str(x) for x in oc.details)


def test_C5_KERNEL_bac_mat_phang_KHONG_vuong_goc_truc():
    """Bác bằng **mã ổn định**, không phải bằng một số sai im lặng.

    ⚠️ Ở tầng IR, một mặt cắt xiên KHÔNG dựng nổi mà không bịa thêm một điểm
    ngoài trục — và `grounding` bắt điểm bịa ấy trước
    (`UNANCHORED_DERIVED_ASSUMPTION`, xem `test_C6`). Nên câu hỏi *"kernel xử
    mặt xiên thế nào"* phải hỏi thẳng kernel, nếu không nó sẽ được trả lời
    bằng một cổng KHÁC — đúng kiểu "đỏ nhờ tầng khác" mà kho này cấm.
    """
    from app.simulation.geometry import curved as CV
    from app.simulation.geometry.exact import Vec3
    from app.simulation.geometry.kernel import GeometryError, Plane3

    non = CV.CurvedSolid(
        kind="cone", anchor=Vec3(Fraction(0), Fraction(0), Fraction(0)),
        apex_or_top=Vec3(Fraction(0), Fraction(0), Fraction(18)),
        rim_point=None, radius_sq_khai=Fraction(144), height_sq_khai=None,
        pose_canonical=True)
    T = Vec3(Fraction(0), Fraction(0), Fraction(12))
    for nx, nz in ((Fraction(1), Fraction(1)), (Fraction(1), Fraction(0))):
        with pytest.raises(GeometryError) as e:
            CV.intersect_plane_curved(
                non, Plane3(point=T, normal=Vec3(nx, Fraction(0), nz)))
        assert e.value.code == "CURVED_SECTION_OUTSIDE_V1_CLOSURE"
        assert "không vuông góc với trục" in str(e.value)


def test_C6_diem_NGOAI_TRUC_bia_ra_bi_grounding_chan():
    """Hệ quả của C5 ở tầng IR: muốn cắt xiên thì phải bịa điểm, và bịa bị bắt."""
    p = _g()
    p["memory_declarations"].append(
        {"name": "P9", "type": "point3", "initial_value": [12, 0, 0],
         "model_assumption": LY_DO_GOC})
    for i, s in enumerate(p["statements"]):
        if s.get("target_var") == "mp_cat":
            p["statements"][i] = {"kind": "construct_plane",
                                  "target_var": "mp_cat",
                                  "through": ["T", "P9", "S"]}
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "grounding"
    assert any("UNANCHORED_DERIVED_ASSUMPTION" in str(x) for x in oc.details)


def test_C7_do_ban_kinh_SAI_CHU_THE_bi_cong_phu_chan():
    """Đo `radius` của KHỐI NÓN (= 12) thay vì của `(c)` (= 4).

    Đây là phản ví dụ nguy hiểm nhất của bài: nó chạy được, ra một số **hợp
    lệ**, và chỉ sai ở chỗ **đo nhầm chủ thể**. Cổng phủ phải bắt nó.
    """
    p = _g()
    for s in p["statements"]:
        if s.get("target_var") == WITNESS:
            s["expr"]["of"] = "non"
    oc = _chay(p)
    assert oc.servable is False and oc.stage_reached == "structural_coverage"
    assert any("không dẫn xuất từ" in str(x) for x in oc.details), oc.details


# ══ D · ĐỀ MỚI THẬT ══════════════════════════════════════════════════════
def test_D1_de_CHUA_TUNG_xuat_hien_trong_corpus_nao():
    from gold_minimal_card_confirmation import CORPUS as F
    from gold_ratio_ab import CORPUS as R

    cu = {c["problem_text"] for c in list(R) + list(F)}
    assert PROBLEM_TEXT not in cu
    assert CONTAINER == "(c)" and WITNESS == "ban_kinh_c"


def test_D2_de_dung_DU_NAM_manh_nang_luc_moi():
    """Nếu đề rơi mất một mảnh thì nó không còn xác nhận được thứ định xác nhận."""
    kinds = {s.get("kind") for s in GOLD["statements"]}
    exprs = {(s.get("expr") or {}).get("kind") for s in GOLD["statements"]}
    assert "construct_curved_solid" in kinds
    assert {"divide_segment", "plane_perpendicular_to_line",
            "intersect_plane_curved", "measure"} <= exprs
    # `radius` cho bằng SỐ (không có điểm vành đặt tên) — lớp mà
    # CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION mở.
    non = next(s for s in GOLD["statements"]
               if s.get("kind") == "construct_curved_solid")
    assert non.get("radius") and not non.get("rim_point")
