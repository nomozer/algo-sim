# -*- coding: utf-8 -*-
"""`OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN` — khoá bằng chứng của lượt cuối.

Lượt live đạt `served` **ngay attempt 0**, và mô hình dùng `radius` thay vì tự
tạo một `rim_point` — lần đầu trong chuỗi. Test này khoá bằng chứng ấy vào
artifact bất biến, và khoá cả **nhiễu đã khai**: hợp đồng analyze của lượt này
tốt hơn lượt trước, nên kết quả **không quy được cho riêng dòng Card**.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

RA = (GOC.parent / "docs" / "evaluation" / "geometry"
      / "oblique-ellipse-final-card-rerun")
CU = (GOC.parent / "docs" / "evaluation" / "geometry"
      / "oblique-ellipse-after-axis-scale-repair")

pytestmark = pytest.mark.skipif(
    not (RA / "SCORING.json").exists(), reason="chưa có artifact lượt cuối")


def _diem() -> dict:
    return json.loads((RA / "SCORING.json").read_text(encoding="utf-8"))


def _e2e() -> dict:
    return json.loads(
        sorted(RA.glob("e2e_*.json"))[-1].read_text(encoding="utf-8"))


# ══ §13 · KẾT QUẢ ══════════════════════════════════════════════════════
def test_01_served_ngay_attempt_0():
    k = _diem()["ket_qua"]
    assert k["FIRST_ATTEMPT_SERVABLE"] is True
    assert k["EVENTUAL_SERVABLE"] is True
    assert k["CANDIDATE_PROGRAM_ATTEMPTS"] == 1
    assert k["REPAIR_CALLS"] == 0
    assert k["STAGE"] == "served" and k["ENVELOPE_STATUS"] == "ok"


def test_02_dap_so_dung_tu_HAI_nguon_doc_lap():
    """⚠️ Một nguồn là chưa đủ, và bản đầu của bộ chấm đã chứng minh điều đó:
    nó chỉ tra chuỗi `16π√5` trong `FINAL_MEMORY` — nơi chỉ có `repr` của
    `Radical` — rồi trả `KHONG DOC DUOC` cho một đáp số ĐÚNG."""
    k = _diem()["ket_qua"]
    assert k["EXACT_ANSWER"] == "16π√5"
    n = k["EXACT_ANSWER_NGUON"]
    assert n["radical_trong_final_memory"] is True
    assert n["chuoi_hien_thi_trong_trace"] is True


def test_03_postconditions_trace_scene3d():
    k = _diem()["ket_qua"]
    assert k["POSTCONDITIONS"] == "PASS"
    assert k["TRACE"] == "PASS" and k["SCENE3D"] == "PASS"
    assert k["scene3d_objects"] == 7 and k["scene3d_events"] == 5


# ══ §10 · CHẤM ỨNG VIÊN ════════════════════════════════════════════════
def test_04_ung_vien_dung_MOI_chieu():
    a = _diem()["attempts"][0]
    assert a["PLANE_OPERATION"] == "construct_plane_from_equation"
    assert a["PLANE_COEFFICIENTS"] == ["2", "0", "-1", "10"]
    assert a["PLANE_COEFFICIENTS_CORRECT"] == "PASS"
    assert a["PLANE_CONSTRUCTION_CORRECT"] == "PASS"
    assert a["OPERATOR_CORRECT"] == "PASS"
    assert a["RESULT_TYPE_CORRECT"] == "PASS"
    assert a["CYLINDER_CONSTRUCTION_CORRECT"] == "PASS"
    assert a["MEASURE_DUNG_CHU_THE"] is True
    assert a["STAGE_CUOI"] == "served"


def test_05_analyze_contract_PASS_toan_bo():
    an = _diem()["analyze"]
    assert an["ANALYZE_CONTRACT_CORRECT"] == "PASS"
    for o in ("CO_HAI_TAM", "CO_BAN_KINH_4", "CO_CHIEU_CAO_HOAC_TRUC",
              "CO_PHUONG_TRINH_MP", "CO_VAT_DUOC_HOI_LA_ELIP"):
        assert an[o] is True, o


# ══ §11 · HIỆU QUẢ DÒNG CARD — và NHIỄU ════════════════════════════════
def test_06_mo_hinh_dung_radius_khong_dung_rim_point():
    """Lần ĐẦU trong chuỗi. Lịch sử: 0/2 direct-radius, 2/2 rim_point."""
    h = _diem()["hieu_qua_dong_card"]
    assert h["HISTORICAL_DIRECT_RADIUS"] == "0/2"
    assert h["HISTORICAL_RIM_POINT"] == "2/2"
    assert h["CURRENT_DIRECT_RADIUS_CANDIDATES"] == 1
    assert h["CURRENT_RIM_POINT_CANDIDATES"] == 0
    assert h["CURRENT_UNGROUNDED_RIM_FAILURES"] == 0
    assert h["CARD_LINE_ASSOCIATED_WITH_DESIRED_SELECTION"] == "YES"


def test_07_NHIEU_da_khai__khong_quy_duoc_cho_rieng_dong_Card():
    """⚠️ Ô quan trọng nhất của wave, và nó là một ô THÚ NHẬN.

    Hợp đồng analyze của lượt này **tốt hơn** lượt trước — `PASS` toàn bộ so
    với `FAIL` (bốn ô `NOT_CAPTURED`, mất cả toạ độ lẫn phương trình). Đó là
    một **biến số thứ hai** đổi cùng lúc với dòng Card, nên không quy được kết
    quả cho riêng dòng Card.

    Test này khoá lời thú nhận ấy: xoá nó khỏi artifact là đỏ.
    """
    h = _diem()["hieu_qua_dong_card"]
    assert h["CAUSAL_ATTRIBUTION"] == "LIMITED"
    assert "BIEN SO THU HAI" in h["nhieu_da_khai"]
    # …và nhiễu ấy KIỂM ĐƯỢC: lượt trước thật sự FAIL ở analyze.
    cu = json.loads(sorted(CU.glob("e2e_*.json"))[-1].read_text(
        encoding="utf-8"))
    assert cu["cham"]["analyze"]["ANALYZE_CONTRACT_CORRECT"] == "FAIL"


def test_08_hai_raw_lich_su_khoa_bang_bam():
    """Phép so trước/sau neo vào BĂM, không neo vào trí nhớ."""
    dk = json.loads((RA / "registration.json").read_text(encoding="utf-8"))
    ls = dk["lich_su_de_so_sanh"]
    assert ls["HISTORICAL_DIRECT_RADIUS"] == "0/2"
    assert set(ls["raw_sha256"]) == set(
        _diem()["hieu_qua_dong_card"]["raw_lich_su_sha256"])


# ══ §12 · KẾ TOÁN ══════════════════════════════════════════════════════
def test_09_ngan_sach_va_token():
    t = _e2e()["tokens"]["theo_stage"]
    assert t["semantic_analyze"]["calls"] == 1
    assert t["semantic_program"]["calls"] == 1
    assert "semantic_program_repair" not in t
    assert _e2e()["tokens"]["tong"] == 7927
    assert _e2e()["tokens"]["tong"] < 40000


# ══ §14 · DANH TÍNH TRONG LƯỢT ĐO ══════════════════════════════════════
def test_10_danh_tinh_luot_do_khop_he_hien_tai():
    from app.main import CACHE_VERSION
    from app.runtime_identity import semantic_environment_fingerprint

    dk = json.loads((RA / "registration.json").read_text(encoding="utf-8"))
    dt = dk["danh_tinh_he_duoc_do"]
    # ⚠️ ĐÍNH CHÍNH 2026-09-07 (`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`):
    # `CACHE_VERSION` đã bump **91 → 92**, nên hai vế KHÔNG còn bằng nhau — và
    # đó là điều ĐÚNG, không phải một chỗ hỏng cần vá.
    #
    # Artifact giữ nguyên `91`: nó là số đo đông cứng của lượt đo, không được
    # sửa. Hệ ở `92` vì thể tích khối LÕM từng sai và envelope cũ mang số sai —
    # một lý do **không dính gì tới bề mặt mô hình**.
    #
    # Điều test này thật sự bảo vệ vẫn nguyên vẹn và được ghim chặt hơn ở vòng
    # `for` ngay dưới: **năm băm model-facing KHÔNG đổi một byte**, nên lượt đo
    # vẫn nói đúng về đúng cái nó đo — thứ mô hình đọc và viết. Ghim
    # `cache_version` của hai bên bằng nhau sẽ biến mọi bump ở tầng kernel
    # thành một lượt đo mất giá trị, mà nó không hề mất.
    assert dt["cache_version"] == "91"
    assert CACHE_VERSION == "92"
    fp = semantic_environment_fingerprint()
    for k, v in dt["model_facing"].items():
        assert fp[k] == v, k
    # Thẻ gửi đi trong lượt chạy đúng là thẻ sản phẩm hiện hành.
    m = _e2e()["manifest"]
    assert m["card_C_sha256"] == dt["card_C_sha256"]
    assert m["card_C_bytes"] == 6672
