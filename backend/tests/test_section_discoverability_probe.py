# -*- coding: utf-8 -*-
"""Tính toàn vẹn của probe discoverability — **0 lượt gọi model**.

    `docs/CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE.md`, 2026-09-05.

Bộ test này trả lời một câu duy nhất: **bộ đo có đo được không?** Nó chạy
scorer trên các chương trình mà ta ĐÃ BIẾT đáp án — gold (đúng) và các bản tiêm
lỗi (sai) — rồi đòi scorer phân biệt được. Một scorer chấm gold là sai, hoặc
chấm chương trình sai là đúng, sẽ cho ra một con số trông như phép đo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
for p in (str(GOC), str(GOC / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from gold_section_discoverability import (  # noqa: E402
    CORPUS,
    chay_gold,
    gold,
)
from run_section_discoverability_probe import cham  # noqa: E402

CA = {c["case_id"]: c for c in CORPUS}


def _ra_tu_gold(cid: str) -> dict:
    """Dựng bản ghi runner từ gold — như thể mô hình vừa sinh ra đúng nó."""
    r = chay_gold(CA[cid])
    _, spec_json, ob = gold(cid)
    return {
        "case_id": cid, "contract_ok": True, "schema_ok": True,
        "chuong_trinh": spec_json,
        "request_contract": {"obligations": [
            {"kind": k, "container": c, "params": {"witness": w}}
            for k, c, w in ob]},
        "stage": r.get("stage"), "executable": r.get("executable", False),
        "servable": r.get("servable", False),
        "details": r.get("details", []),
        "final_memory": {w: v for w, v in (r.get("witness") or {}).items()
                         if v is not None},
        "scene3d_ok": r.get("scene3d_ok", False), "repair_count": 0,
    }


# ══ CORPUS — hình dạng đã đăng ký ════════════════════════════════════════
def test_corpus_dung_8_ca_va_dung_ty_le_da_dang_ky():
    assert len(CORPUS) == 8
    lop = [c["expected_operator_class"] for c in CORPUS]
    assert lop.count("intersect_plane_curved") == 6
    assert lop.count("construct_section") == 1      # đối chứng đa diện
    assert lop.count("refusal") == 1                # ca âm ngoài bao đóng
    assert len({c["case_id"] for c in CORPUS}) == 8


def test_corpus_KHONG_dung_ky_hieu_cua_V3():
    """Phép đo không được đo trúng một thói quen đặt tên."""
    cam = {"r_C", "area_C", "ban_kinh_c", "hinh_tru", "hinh_non", "mp_C"}
    for c in CORPUS:
        assert not (cam & set(c["problem_text"].split())), c["case_id"]


def test_corpus_co_du_Pythagoras_va_mot_ca_Radical():
    """Ràng buộc §2, kiểm bằng ĐÁP SỐ chứ không bằng lời hứa."""
    huu_ti = [c for c in CORPUS
              if c["exact_expected_results"]
              and all(not any(ch in v for ch in "√")
                      for v in c["exact_expected_results"].values())]
    assert len(huu_ti) >= 2
    assert any("√" in v for c in CORPUS
               for v in c["exact_expected_results"].values())


def test_moi_ca_khai_du_truong_bat_buoc():
    for c in CORPUS:
        for k in ("case_id", "problem_text", "family", "feature",
                  "expected_obligations", "expected_operator_class",
                  "expected_result_type", "exact_expected_results",
                  "expected_boundary"):
            assert k in c, (c["case_id"], k)


# ══ GOLD — đường đúng phải đi được ═══════════════════════════════════════
@pytest.mark.parametrize("cid", ["d1", "d2", "d3", "d4", "d5", "d6", "d7"])
def test_gold_duong_SERVABLE_va_dap_so_KHOP(cid):
    r = chay_gold(CA[cid])
    assert r["servable"], r.get("details")
    assert r["exact_match"], r.get("thuc_te")
    assert r["scene3d_ok"]


def test_gold_ca_AM_tu_choi_dung_ma_da_cong_bo():
    r = chay_gold(CA["d8"])
    assert not r["servable"]
    assert any("CURVED_SECTION_OUTSIDE_V1_CLOSURE" in x for x in r["details"])


# ══ SCORER — chấm gold là ĐÚNG ═══════════════════════════════════════════
@pytest.mark.parametrize("cid", ["d1", "d3", "d5", "d6"])
def test_scorer_cham_gold_cong_la_DUNG(cid):
    c = cham(CA[cid], _ra_tu_gold(cid))
    assert c["SELECTED_OPERATOR"] == "intersect_plane_curved"
    assert c["OPERATOR_CLASS_CORRECT"] is True
    assert c["USED_ASSIGN_WRAPPER"] is True
    assert c["RESULT_TYPE_IS_CIRCLE3"] is True
    assert c["EXACT_ANSWER_MATCH"] is True
    assert c["EVENTUAL_SERVABLE"] is True
    assert c["FAILURE_OWNER"] is None


def test_scorer_cham_doi_chung_DA_DIEN_la_DUNG():
    """`construct_section` là lựa chọn ĐÚNG ở ca đa diện — không được trừ."""
    c = cham(CA["d7"], _ra_tu_gold("d7"))
    assert c["SELECTED_OPERATOR"] == "construct_section"
    assert c["OPERATOR_CLASS_CORRECT"] is True
    assert c["EXACT_ANSWER_MATCH"] is True


def test_scorer_cham_ca_AM_la_DUNG_va_KHONG_doi_chon_toan_tu():
    """Ca âm chấm bằng BIÊN, không bằng lựa chọn toán tử.

    Mô hình không có cách nào biết trước bao đóng v1 — bắt nó "chọn đúng" ở đây
    là chấm nó về một luật chưa từng được nói cho nó.
    """
    c = cham(CA["d8"], _ra_tu_gold("d8"))
    assert c["OPERATOR_CLASS_CORRECT"] is None
    assert c["BOUNDARY_CORRECT"] is True
    assert c["FAILURE_OWNER"] is None


# ══ TIÊM LỖI — scorer phải BẮT ĐƯỢC ══════════════════════════════════════
def _thay_producer_bang_construct_section(ra):
    """Mô hình đi nhầm đường `c5b`/`c9b`: khối cong + `construct_section`."""
    p = {**ra["chuong_trinh"]}
    p["statements"] = [
        {"kind": "construct_section", "target_var": st["target_var"],
         "solid": st["expr"]["solid"], "plane": st["expr"]["plane"]}
        if st.get("kind") == "assign"
        and (st.get("expr") or {}).get("kind") == "intersect_plane_curved"
        else st for st in p["statements"]]
    return {**ra, "chuong_trinh": p}


def test_TIEM_1_chon_construct_section_cho_khoi_cong_BI_BAT():
    c = cham(CA["d1"], _thay_producer_bang_construct_section(_ra_tu_gold("d1")))
    assert c["SELECTED_OPERATOR"] == "construct_section"
    assert c["OPERATOR_CLASS_CORRECT"] is False


def test_TIEM_2_dung_intersect_nhu_CAU_LENH_bi_dem_rieng():
    """Không gộp vào "sai toán tử" — nó là một hình dạng lỗi KHÁC."""
    ra = _ra_tu_gold("d1")
    p = {**ra["chuong_trinh"]}
    p["statements"] = [
        {"kind": "intersect_plane_curved", "target_var": st["target_var"],
         "solid": st["expr"]["solid"], "plane": st["expr"]["plane"]}
        if st.get("kind") == "assign"
        and (st.get("expr") or {}).get("kind") == "intersect_plane_curved"
        else st for st in p["statements"]]
    c = cham(CA["d1"], {**ra, "chuong_trinh": p})
    assert c["INTERSECT_AS_STATEMENT"] is True
    assert c["USED_ASSIGN_WRAPPER"] is False
    assert c["SELECTED_OPERATOR"] == "intersect_plane_curved"


def test_TIEM_3_khai_ket_qua_la_section_BI_BAT():
    ra = _ra_tu_gold("d1")
    p = {**ra["chuong_trinh"]}
    p["memory_declarations"] = [
        {**d, "type": "section"} if d["type"] == "circle3" else d
        for d in p["memory_declarations"]]
    c = cham(CA["d1"], {**ra, "chuong_trinh": p})
    assert c["RESULT_TYPE_IS_CIRCLE3"] is False
    assert "section" in c["DECLARED_RESULT_TYPE"]


def test_TIEM_4_dap_so_SAI_BI_BAT():
    ra = _ra_tu_gold("d3")
    c = cham(CA["d3"], {**ra, "final_memory": {"bk_sigma": "15"}})   # đúng: 6
    assert c["EXACT_ANSWER_MATCH"] is False


def test_TIEM_5_thieu_mot_nghia_vu_BI_BAT():
    ra = _ra_tu_gold("d1")                      # cần radius VÀ area
    ra["request_contract"]["obligations"] = [
        {"kind": "radius", "container": "w", "params": {"witness": "bk_w"}}]
    assert cham(CA["d1"], ra)["OBLIGATIONS_COMPLETE"] is False


def test_TIEM_6_hazard_ZeroDivision_quy_cho_HE_khong_quy_cho_MO_HINH():
    """Luật này đăng ký TRƯỚC lượt đo (`measurement_policy.json`).

    Chương trình chọn ĐÚNG toán tử nhưng khai khối bằng vô hướng ⇒ kernel vỡ.
    Quy cho mô hình ở đây là để một lỗi kernel viết lại kết luận về hành vi
    mô hình.
    """
    ra = _ra_tu_gold("d1")
    ra.update(servable=False, executable=False, stage="execution",
              details=["[ZeroDivisionError]", "Fraction(1, 0)"])
    c = cham(CA["d1"], ra)
    assert c["FAILURE_OWNER"] == "SYSTEM"
    assert c["SYSTEM_FAILURE_ID"] == "CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT"
    # Và chiều chính KHÔNG bị kéo xuống theo.
    assert c["OPERATOR_CLASS_CORRECT"] is True


def test_TIEM_7_khai_khoi_bang_VO_HUONG_duoc_ghi_lai():
    """Chiều này phải quan trắc được, vì nó là biến của hazard."""
    ra = _ra_tu_gold("d1")
    p = {**ra["chuong_trinh"]}
    p["statements"] = [
        {k: v for k, v in st.items() if k not in ("apex_or_top", "rim_point")}
        | {"height": "h_", "radius": "r_"}
        if st.get("kind") == "construct_curved_solid" else st
        for st in p["statements"]]
    c = cham(CA["d1"], {**ra, "chuong_trinh": p})
    assert c["CURVED_SOLID_DECLARATION"] == ["height_scalar"]


def test_TIEM_8_ngan_sach_VUOT_thi_NEM():
    from run_section_discoverability_probe import MAX_PHYSICAL, NganSach

    ns = NganSach()
    for _ in range(MAX_PHYSICAL):
        ns.ghi("semantic_program")
    with pytest.raises(RuntimeError, match="VƯỢT TRẦN VẬT LÝ"):
        ns.ghi("semantic_program")


# ══ LỖI HỆ TÌM ĐƯỢC TRONG PREFLIGHT — NAY ĐÃ ĐÓNG ════════════════════════
#
# Bản 2026-09-05 của hai test dưới đây khoá **hành vi hỏng** (`ZeroDivisionError`)
# kèm lời dặn: *"sẽ ĐỎ khi lỗi được sửa, và đỏ là ĐÚNG"*. `CURVED_SCALAR_AXIS_
# INTERSECTION_FIX` (cùng ngày) đóng lỗi, test đỏ đúng như dự đoán, và nay nó
# khẳng định hành vi ĐÚNG.
#
# Giữ mục này ở đây — thay vì xoá — vì nó là **bằng chứng lịch sử** rằng probe
# đã tìm ra lỗi TRƯỚC khi tiêu quota, và rằng hazard đăng ký trước lượt đo là
# hazard có thật. Bộ kiểm đầy đủ của bản vá nằm ở
# `tests/geometry/test_curved_scalar_axis_intersection.py`.
#
#     docs/CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE.md §3b   (phát hiện)
#     docs/CURVED_SCALAR_AXIS_INTERSECTION_FIX.md              (bản vá)
def test_LOI_HE_DA_DONG__khoi_cong_khai_bang_VO_HUONG_nay_cat_duoc():
    """Nguyên nhân vẫn còn nguyên (`truc` rỗng), nhưng nó không còn được đọc."""
    from fractions import Fraction

    from app.simulation.geometry import curved as CV
    from app.simulation.geometry.exact import Plane3, Vec3

    def P(x, y, z):
        return Vec3(Fraction(x), Fraction(y), Fraction(z))

    tru = CV.CurvedSolid("cylinder", P(0, 0, 0), None, None, Fraction(144),
                         height_sq_khai=Fraction(400))
    assert tru.truc.is_zero()                     # nguyên nhân CŨ, còn nguyên
    assert tru.huong_truc == CV.HUONG_TRUC_CANONICAL   # thứ nay được đọc

    mp = Plane3(P(0, 0, 5), P(0, 0, 1))
    c = CV.intersect_plane_curved(tru, mp)
    assert c.radius_sq == Fraction(144)
    assert c.center == P(0, 0, 5)

    # Và khai bằng ĐIỂM cho y hệt — cách khai không đổi hình.
    tru2 = CV.CurvedSolid("cylinder", P(0, 0, 0), P(0, 0, 20), P(12, 0, 0), None)
    c2 = CV.intersect_plane_curved(tru2, mp)
    assert (c2.radius_sq, c2.center) == (c.radius_sq, c.center)


def test_LOI_HE_chi_cham_intersect__the_tich_va_mat_cong_van_dung():
    """Phạm vi: `volume`/`lateral_area` KHÔNG dính, nên đây không phải lỗi khai."""
    from fractions import Fraction

    from app.simulation.geometry import curved as CV
    from app.simulation.geometry.exact import Vec3

    goc = Vec3(Fraction(0), Fraction(0), Fraction(0))
    a = CV.CurvedSolid("cylinder", goc, None, None, Fraction(144),
                       height_sq_khai=Fraction(400))
    b = CV.CurvedSolid("cylinder", goc, Vec3(Fraction(0), Fraction(0),
                                             Fraction(20)),
                       Vec3(Fraction(12), Fraction(0), Fraction(0)), None)
    assert str(CV.the_tich(a)) == str(CV.the_tich(b)) == "2880π"
    assert str(CV.dien_tich_mat_cong(a)) == str(CV.dien_tich_mat_cong(b)) == "480π"


def test_TIEM_8b_lượt_logic_doc_tu_TELEMETRY_khong_tu_bo_dem_runner():
    """Bộ đếm của runner đếm THIẾU — telemetry sản phẩm là thẩm quyền.

    `repair_count` suy từ sự kiện `semantic_program_attempt`, mà sự kiện ấy chỉ
    phát khi một lượt HỎNG; lượt cuối thành công không phát gì. Nên mọi ca đậu
    bị đếm thiếu đúng một lượt — đo được trong chính lượt chạy dev-v1: bộ đếm
    báo 21, telemetry báo 26.
    """
    src = (GOC / "scripts" / "run_section_discoverability_probe.py").read_text(
        encoding="utf-8")
    assert "logical_calls_used_telemetry" in src
    assert 'v.get("calls", 0)' in src
    # Và bộ đếm cũ vẫn được ghi lại, để lần sau còn so được hai bên.
    assert "logical_calls_used_runner_counter" in src


def test_TIEM_9_runner_KHONG_gui_expected_cho_model():
    """Nguồn của runner không được nhắc tới trường kỳ vọng nào."""
    src = (GOC / "scripts" / "run_section_discoverability_probe.py").read_text(
        encoding="utf-8")
    than = src.split("# ══ MỘT CA")[1].split("MOI_TRUONG: dict")[0]
    for cam in ("exact_expected_results", "expected_operator_class",
                "expected_result_type", "expected_boundary"):
        assert cam not in than, f"`{cam}` lọt vào đường gửi cho model"


def test_TIEM_10_chi_problem_text_di_vao_hai_stage():
    src = (GOC / "scripts" / "run_section_discoverability_probe.py").read_text(
        encoding="utf-8")
    than = src.split("async def chay_mot")[1].split("MOI_TRUONG: dict")[0]
    assert than.count("ca[\"problem_text\"]") == 2      # analyze + tổng hợp
    assert "ca[\"feature\"]" not in than
    assert "ca[\"family\"]" not in than
