# -*- coding: utf-8 -*-
"""Bộ chấm elip phải theo KỊP hệ — `OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR`.

⚠️ Lỗ đã đo được, không phải giả định. Lượt live đầu tiên mà mô hình tự chọn
`construct_plane_from_equation` bị chấm `PLANE_CONSTRUCTION_CORRECT = FAIL` —
cho một chương trình dựng mặt phẳng **ĐÚNG TỪNG HỆ SỐ**. Bộ chấm chỉ biết
`construct_plane` qua ba điểm, tức nó **tụt lại sau hệ đúng một wave**
(`PLANE_FROM_EQUATION_REPRESENTATION` thêm phép ấy, bộ chấm không được cập
nhật theo).

Đó đúng lớp lỗi *"bộ đo không nằm trên đường chạy thật"* mà kho này đã trả giá
ba lần. Test này khoá cả hai lối, và khoá luôn phép phân biệt rim/radius —
thứ §10 của wave dùng để phân loại lựa chọn của mô hình.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from score_oblique_ellipse_fresh import cham_synthesis  # noqa: E402

ART = (GOC.parent / "docs" / "evaluation" / "geometry"
       / "oblique-ellipse-after-axis-scale-repair")


def _ct(mp_stmt: dict, tru: dict | None = None) -> dict:
    tru = tru or {"kind": "construct_curved_solid", "target_var": "tru",
                  "curved_kind": "cylinder", "anchor": "O",
                  "apex_or_top": "Op", "radius": "r"}
    return {
        "memory_declarations": [
            {"name": "O", "type": "point3"}, {"name": "Op", "type": "point3"},
            {"name": "r", "type": "float"}, {"name": "alpha", "type": "plane3"},
            {"name": "E", "type": "ellipse3"}, {"name": "S", "type": "float"},
        ],
        "statements": [
            tru, mp_stmt,
            {"kind": "assign", "target_var": "E",
             "expr": {"kind": "intersect_plane_curved_ellipse",
                      "solid": "tru", "plane": "alpha"}},
            {"kind": "assign", "target_var": "S",
             "expr": {"kind": "measure", "quantity": "area", "of": "E"}},
        ],
    }


PT = {"kind": "construct_plane_from_equation", "target_var": "alpha",
      "a": 2, "b": 0, "c": -1, "d": 10}


def test_01_phep_moi_duoc_cham_PASS():
    r = cham_synthesis(_ct(PT))
    assert r["PLANE_OPERATION"] == "construct_plane_from_equation"
    assert r["PLANE_COEFFICIENTS"] == ["2", "0", "-1", "10"]
    assert r["PLANE_COEFFICIENTS_CORRECT"] == "PASS"
    assert r["PLANE_CONSTRUCTION_CORRECT"] == "PASS"


@pytest.mark.parametrize("he", [
    (-4, 0, 2, -20),        # nhân −2 — CÙNG một mặt phẳng
    (1, 0, "-1/2", 5),      # chia 2, hệ số phân số
])
def test_02_he_so_TI_LE_van_PASS(he):
    """So TỈ LỆ, không so chữ. Bộ chấm không được hẹp hơn chính hệ —
    `plane_equation.tuong_duong` đã so tỉ lệ từ khi phép dựng ra đời."""
    a, b, c, d = he
    r = cham_synthesis(_ct({**PT, "a": a, "b": b, "c": c, "d": d}))
    assert r["PLANE_COEFFICIENTS_CORRECT"] == "PASS", he


@pytest.mark.parametrize("he", [(2, 0, -1, 11), (3, 0, -1, 10)])
def test_03_he_so_SAI_bi_cham_FAIL(he):
    """⚠️ `d = 11` cho CÙNG diện tích (mặt phẳng song song) — bộ chấm vẫn
    phải bắt, vì nó hỏi *mặt phẳng nào*, không hỏi *đáp số bao nhiêu*."""
    a, b, c, d = he
    r = cham_synthesis(_ct({**PT, "a": a, "b": b, "c": c, "d": d}))
    assert r["PLANE_COEFFICIENTS_CORRECT"] == "FAIL", he
    assert r["PLANE_CONSTRUCTION_CORRECT"] == "FAIL", he


def test_04_loi_BA_DIEM_cu_van_PASS():
    """Phép mới là lối THỨ HAI; lối cũ không được mất điểm."""
    r = cham_synthesis(_ct(
        {"kind": "construct_plane", "target_var": "alpha",
         "through": ["P1", "P2", "P3"]}))
    assert r["PLANE_OPERATION"] == "construct_plane"
    assert r["PLANE_CONSTRUCTION_CORRECT"] == "PASS"
    assert r["PLANE_COEFFICIENTS_CORRECT"] == "NOT_CAPTURED"


# ══ §10 · PHÂN BIỆT RIM ↔ RADIUS ═══════════════════════════════════════
def test_05_direct_radius_doc_ra_dung():
    r = cham_synthesis(_ct(PT))
    assert r["DIRECT_RADIUS_USED"] is True
    assert r["RIM_POINT_USED"] is False
    assert r["AXIS_TWO_POINTS"] is True


def test_06_rim_point_KHONG_neo_doc_ra_dung():
    """Hình dạng ĐO ĐƯỢC ở lượt live: `anchor + apex_or_top` ĐỦ trục, nhưng
    mô hình VẪN thêm `rim_point` bịa để mã hoá bán kính.

    Bản chấm cũ trả một chuỗi duy nhất (`"rim_point"`) nên mất thông tin là
    khối đã đủ hai điểm trục — mà đó chính là thứ làm câu *"mô hình có đường
    khác không"* trả lời được.
    """
    ct = _ct(PT, {"kind": "construct_curved_solid", "target_var": "tru",
                  "curved_kind": "cylinder", "anchor": "O",
                  "apex_or_top": "Op", "rim_point": "P_rim"})
    ct["memory_declarations"].append(
        {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0],
         "model_assumption": "Chọn một điểm trên vành đáy."})
    r = cham_synthesis(ct)
    assert r["RIM_POINT_USED"] is True
    assert r["DIRECT_RADIUS_USED"] is False
    assert r["AXIS_TWO_POINTS"] is True          # trục đã đủ, rim là THỪA
    assert r["RIM_POINT_GROUNDED"] is False      # chỉ `model_assumption`


def test_07_rim_point_CO_neo_phan_biet_duoc():
    """Chọn nhầm cách khai ≠ bịa dữ liệu. Hai bệnh, hai ô."""
    ct = _ct(PT, {"kind": "construct_curved_solid", "target_var": "tru",
                  "curved_kind": "cylinder", "anchor": "O",
                  "apex_or_top": "Op", "rim_point": "P_rim"})
    ct["memory_declarations"].append(
        {"name": "P_rim", "type": "point3", "initial_value": [4, 0, 0],
         "source_fact_id": "ban_kinh_day"})
    assert cham_synthesis(ct)["RIM_POINT_GROUNDED"] is True


def test_08_height_doc_ra_duoc():
    ct = _ct(PT, {"kind": "construct_curved_solid", "target_var": "tru",
                  "curved_kind": "cylinder", "anchor": "O",
                  "radius": "r", "height": "h"})
    r = cham_synthesis(ct)
    assert r["HEIGHT_USED"] is True and r["AXIS_TWO_POINTS"] is False


# ══ CHẤM LẠI ARTIFACT BẤT BIẾN ═════════════════════════════════════════
@pytest.mark.skipif(not ART.exists(), reason="chưa có artifact lượt chạy")
def test_09_cham_lai_artifact_cho_PLANE_PASS():
    """Bằng chứng lỗ bộ chấm: cùng một ứng viên, hai kết quả khác nhau.

    Artifact lượt chạy ghi `PLANE_CONSTRUCTION_CORRECT = FAIL` (bộ chấm cũ);
    `SCORING.json` ghi `PASS` (bộ chấm nay). Ứng viên **không đổi một byte** —
    `raw_sha256` là mối nối giữa hai bản.
    """
    e2e = sorted(ART.glob("e2e_*.json"))
    diem = json.loads((ART / "SCORING.json").read_text(encoding="utf-8"))
    cu = json.loads(e2e[-1].read_text(encoding="utf-8"))

    assert cu["cham"]["synthesis"]["PLANE_CONSTRUCTION_CORRECT"] == "FAIL"
    a0 = diem["attempts"][0]
    assert a0["PLANE_CONSTRUCTION_CORRECT"] == "PASS"
    assert a0["PLANE_COEFFICIENTS"] == ["2", "0", "-1", "10"]
    # …và mọi chiều KHÁC vẫn PASS: hỏng đúng MỘT chỗ.
    assert a0["OPERATOR_CORRECT"] == "PASS"
    assert a0["RESULT_TYPE_CORRECT"] == "PASS"
    assert a0["MEASURE_DUNG_CHU_THE"] is True
    assert a0["STAGE_CUOI"] == "grounding"
    assert a0["REPAIRABLE"] is False


@pytest.mark.skipif(not ART.exists(), reason="chưa có artifact lượt chạy")
def test_10_dem_rim_affordance_khop_artifact():
    diem = json.loads((ART / "SCORING.json").read_text(encoding="utf-8"))
    d = diem["rim_point_affordance"]
    assert d["DIRECT_RADIUS_CANDIDATES"] == 0
    assert d["RIM_POINT_CANDIDATES"] == 1
    assert d["UNGROUNDED_RIM_POINT_CANDIDATES"] == 1
    assert d["REPAIRS_FROM_RIM_TO_RADIUS"] == 0
