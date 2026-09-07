# -*- coding: utf-8 -*-
"""BỐN NGHĨA VỤ ĐẠI LƯỢNG ĐỊNH TUYẾN ĐƯỢC. **0 lượt gọi model.**

    `SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION`
    Pha A, 2026-09-07.

Lỗ đã tái hiện ở `test_scope_gate_quantity_obligation_gap.py`: bốn nghĩa vụ
**vừa analyze phát được vừa có checker** — `area` · `lateral_area` · `radius` ·
`section_matches` — không có manh mối nào trong `_MANH_MOI_NGHIA_VU`, nên
`co_duong_thuc_thi` từ chối cả một lớp bài mà hệ giải được.

Bộ test này khoá bản sửa theo BỐN chiều:

    ① chính diện — mỗi nghĩa vụ có mặt trong tập ứng viên
    ② bảo toàn  — manh mối cũ định tuyến y như trước, ngoài miền vẫn bị chặn
    ③ parity    — tập cần phủ DẪN từ registry chính thức, không liệt kê tay
    ④ tiêm lỗi  — bỏ từng entry một, đúng test tương ứng phải đỏ

⚠️ **Chấm trên `nghia_vu_ung_vien`, không chỉ trên `co_duong_thuc_thi`.** Cổng
là một phép giao tập rồi lấy `bool`, nên bỏ `lateral_area` đi thì
*"diện tích xung quanh…"* **vẫn** mở cổng nhờ `area`. Khẳng định ở mức boolean
sẽ không thấy gì — và một phép tiêm không đỏ được là một phép tiêm không chứng
minh gì.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.analyze_contract import analyze_schema_for
from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
    _MANH_MOI_NGHIA_VU,
    co_duong_thuc_thi,
    detect_domain,
    nghia_vu_ung_vien,
)
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
)

BON = ("area", "lateral_area", "radius", "section_matches")


def _emit() -> set[str]:
    """Nghĩa vụ mà `analyze` PHÁT được — đọc thẳng enum của lược đồ."""
    s = analyze_schema_for(DOMAIN_HINH_HOC)
    return set(s["properties"]["obligations"]["items"]["properties"]["kind"]["enum"])


# ══ ① CHÍNH DIỆN ═════════════════════════════════════════════════════════
@pytest.mark.parametrize("cau", [
    "Tính diện tích elip (E).",
    "Tính diện tích xung quanh hình trụ.",
    "Tính bán kính mặt cầu.",
])
def test_01_ba_cau_BAT_BUOC_cua_brief_deu_mo_cong(cau):
    assert co_duong_thuc_thi(cau, DOMAIN_HINH_HOC) is True, cau


@pytest.mark.parametrize("nv,cau", [
    # ── area: bốn lối hỏi tự nhiên ──────────────────────────────────────
    ("area", "Tính diện tích thiết diện."),
    ("area", "Tính diện tích elip (E)."),
    ("area", "Tính diện tích hình tròn giao tuyến."),
    ("area", "Diện tích của (E) bằng bao nhiêu?"),
    # ── lateral_area: khái niệm CÓ ĐỊNH NGỮ ─────────────────────────────
    ("lateral_area", "Tính diện tích xung quanh hình trụ."),
    ("lateral_area", "Tính diện tích mặt bên của hình nón."),
    ("lateral_area", "Tính diện tích mặt cong của khối cầu."),
    # ── radius ──────────────────────────────────────────────────────────
    ("radius", "Tính bán kính mặt cầu."),
    ("radius", "Xác định bán kính đường tròn giao tuyến."),
    ("radius", "Bán kính của (c) bằng bao nhiêu?"),
    # ── section_matches ─────────────────────────────────────────────────
    ("section_matches", "Xác định thiết diện của hình chóp khi cắt bởi (MNP)."),
    ("section_matches", "Dựng thiết diện tạo bởi mặt phẳng (P) và khối hộp."),
])
def test_02_moi_nghia_vu_CO_MAT_trong_tap_ung_vien(nv, cau):
    """Chấm ở mức TẬP — xem docstring đầu file về vì sao không chấm bool."""
    assert nv in nghia_vu_ung_vien(cau), (nv, sorted(nghia_vu_ung_vien(cau)))


@pytest.mark.parametrize("nv,cau", [
    ("area", "TÍNH DIỆN TÍCH ELIP (E)."),
    ("radius", "TÍNH BÁN KÍNH MẶT CẦU."),
    ("lateral_area", "Tính DIỆN TÍCH XUNG QUANH hình trụ."),
    ("section_matches", "XÁC ĐỊNH THIẾT DIỆN của khối chóp."),
])
def test_03_bien_the_VIET_HOA_van_dinh_tuyen(nv, cau):
    """Cổng chuẩn hoá bằng `text.lower()` — biến thể hoa phải đi qua."""
    assert nv in nghia_vu_ung_vien(cau), cau


@pytest.mark.parametrize("cau", [
    "Cho hình trụ bán kính đáy 4, chiều cao 20. Mặt phẳng (α) cắt hình trụ "
    "theo một elip (E). Tính diện tích elip (E).",
    "Cho hình nón đỉnh S. Mặt phẳng qua T cắt hình nón theo đường tròn (c). "
    "Tính bán kính của đường tròn (c).",
    "Cho khối cầu tâm O bán kính R. Tính diện tích mặt cong của khối cầu.",
])
def test_04_bai_HINH_CONG_day_du_deu_di_vao_duoc(cau):
    assert detect_domain(cau) == DOMAIN_HINH_HOC
    assert co_duong_thuc_thi(cau, DOMAIN_HINH_HOC) is True


def test_05_de_cua_wave_ELIP_nay_dinh_tuyen_duoc():
    """Chính đề mà lượt trước bị chặn — nay phải vào được pipeline."""
    import sys
    from pathlib import Path

    GOC = Path(__file__).resolve().parents[2]
    if str(GOC / "scripts") not in sys.path:
        sys.path.insert(0, str(GOC / "scripts"))
    from gold_oblique_ellipse_fresh import PROBLEM_TEXT

    assert co_duong_thuc_thi(PROBLEM_TEXT, DOMAIN_HINH_HOC) is True
    assert "area" in nghia_vu_ung_vien(PROBLEM_TEXT)


def test_06_de_bai_NON_nay_TU_MO_TUYEN_bang_chinh_nghia_vu_no_hoi():
    """Đính chính lối lọt tình cờ: nó hỏi `radius`, nay `radius` tự mở tuyến.

    Trước bản sửa nó qua cổng nhờ `perpendicular` từ cụm *"vuông góc với SO"*
    ở phần MÔ TẢ. Bỏ hai chữ ấy thì nó chết ở `scope`. Nay không còn phụ thuộc.
    """
    import sys
    from pathlib import Path

    GOC = Path(__file__).resolve().parents[2]
    if str(GOC / "scripts") not in sys.path:
        sys.path.insert(0, str(GOC / "scripts"))
    from gold_curved_end_to_end import PROBLEM_TEXT as NON

    assert "radius" in nghia_vu_ung_vien(NON)
    khong_vuong_goc = NON.replace("và vuông góc với SO ", "")
    assert "perpendicular" not in nghia_vu_ung_vien(khong_vuong_goc)
    assert co_duong_thuc_thi(khong_vuong_goc, DOMAIN_HINH_HOC) is True


# ══ ② BẢO TOÀN ═══════════════════════════════════════════════════════════
@pytest.mark.parametrize("nv,cau", [
    ("distance", "Tính khoảng cách từ A đến mặt phẳng (SBD)."),
    ("volume", "Tính thể tích khối chóp S.ABCD."),
    ("angle", "Tính góc giữa SA và mặt phẳng (ABCD)."),
    ("parallel", "Chứng minh MNPQ là hình bình hành."),
    ("perpendicular", "Chứng minh SA vuông góc với (ABCD)."),
    ("coplanar", "Chứng minh bốn điểm đồng phẳng."),
    ("point_on_line", "Tìm giao tuyến của (SAB) và (SCD)."),
    ("point_on_plane", "Tìm giao điểm của SA và mặt phẳng (MNP)."),
])
def test_07_manh_moi_CU_dinh_tuyen_y_nhu_truoc(nv, cau):
    assert nv in nghia_vu_ung_vien(cau), (nv, sorted(nghia_vu_ung_vien(cau)))
    assert co_duong_thuc_thi(cau, DOMAIN_HINH_HOC) is True


def test_08_NGOAI_MIEN_van_bi_chan_nhu_cu():
    """Cổng này đứng SAU `detect_domain`; thêm manh mối không mở cửa cho ai."""
    tin_hoc = ("Viết chương trình tính diện tích hình chữ nhật rồi in ra "
               "màn hình bằng Python.")
    assert co_duong_thuc_thi(tin_hoc, DOMAIN_TIN_HOC) is False
    # …và ngay cả khi ép miền hình học, một chuỗi rỗng vẫn fail-closed.
    assert co_duong_thuc_thi("", DOMAIN_HINH_HOC) is False
    assert co_duong_thuc_thi("Cho hình chóp S.ABCD.", DOMAIN_HINH_HOC) is False


def test_09_qua_cong_KHONG_phai_la_duoc_HO_TRO():
    """Cổng chỉ cho ĐI VÀO pipeline. Capability là một câu hỏi khác."""
    from app.simulation.product_capability import NANG_LUC_SAN_PHAM, da_ho_tro

    cau = "Cho hình trụ. Mặt phẳng (α) cắt theo elip (E). Tính diện tích (E)."
    assert co_duong_thuc_thi(cau, DOMAIN_HINH_HOC) is True
    assert NANG_LUC_SAN_PHAM["curved_oblique_section"].trang_thai == \
        "foundation_only"
    assert not da_ho_tro("curved_oblique_section")
    for h in ("ball", "cylinder", "cone"):
        assert not da_ho_tro(h)


# ══ ③ PARITY — tập cần phủ DẪN từ registry, không liệt kê tay ════════════
def test_10_PARITY_moi_nghia_vu_emit_VA_checker_deu_co_manh_moi():
    """Bất biến của wave, và nó là thứ chống tái phát thật sự.

    Thêm một nghĩa vụ vào enum analyze + viết checker cho nó mà quên bảng manh
    mối ⇒ test này ĐỎ, thay vì cả một lớp bài bị fail-closed trong im lặng.
    """
    can_phu = _emit() & set(GEOMETRY_CHECKERS)
    thieu = can_phu - set(_MANH_MOI_NGHIA_VU)
    assert thieu == set(), (
        f"nghĩa vụ {sorted(thieu)} vừa analyze phát được vừa có checker "
        "nhưng KHÔNG có manh mối scope — đề hỏi chúng sẽ bị `co_duong_thuc_thi` "
        "từ chối trước khi tới model")
    # Chiều ngược lại cũng phải sạch: không manh mối nào trỏ một nghĩa vụ chết.
    assert set(_MANH_MOI_NGHIA_VU) - set(GEOMETRY_CHECKERS) == set()


def test_11_PARITY_khong_manh_moi_nao_RONG():
    for nv, cum in _MANH_MOI_NGHIA_VU.items():
        assert isinstance(cum, tuple) and cum, nv
        for c in cum:
            assert c and c == c.lower(), (nv, c)


def test_12_bon_nghia_vu_moi_CO_MAT_trong_bang():
    for nv in BON:
        assert nv in _MANH_MOI_NGHIA_VU, nv
        assert _MANH_MOI_NGHIA_VU[nv], nv


# ══ ④ TIÊM LỖI — bỏ từng entry một ═══════════════════════════════════════
@pytest.mark.parametrize("nv,cau", [
    ("area", "Tính diện tích elip (E)."),
    ("lateral_area", "Tính diện tích xung quanh hình trụ."),
    ("radius", "Tính bán kính mặt cầu."),
    ("section_matches", "Xác định thiết diện của hình chóp."),
])
def test_13_TIEM_bo_MOT_entry_thi_dung_nghia_vu_ay_MAT_TUYEN(
        nv, cau, monkeypatch):
    """Bốn phép tiêm riêng biệt — mỗi cái làm đỏ đúng chiều của nó.

    ⚠️ Chấm ở mức TẬP: bỏ `lateral_area` thì cổng **vẫn mở** nhờ `area`, nên
    một khẳng định ở mức `bool` sẽ xanh và không chứng minh gì.
    """
    from app.simulation.semantic_program import domain_profile as DP

    assert nv in nghia_vu_ung_vien(cau)            # trước khi tiêm
    con_lai = {k: v for k, v in _MANH_MOI_NGHIA_VU.items() if k != nv}
    monkeypatch.setattr(DP, "_MANH_MOI_NGHIA_VU", con_lai)
    assert nv not in DP.nghia_vu_ung_vien(cau), (
        f"bỏ entry `{nv}` mà nó vẫn định tuyến — phép tiêm không gác gì")
    # …và cổng parity cũng phải đỏ theo.
    assert (_emit() & set(GEOMETRY_CHECKERS)) - set(con_lai) == {nv}


def test_14_TIEM_bo_area_thi_de_cua_wave_MAT_TUYEN_hoan_toan(monkeypatch):
    """`area` là entry DUY NHẤT giữ đề elip này ở trong phạm vi."""
    import sys
    from pathlib import Path

    from app.simulation.semantic_program import domain_profile as DP

    GOC = Path(__file__).resolve().parents[2]
    if str(GOC / "scripts") not in sys.path:
        sys.path.insert(0, str(GOC / "scripts"))
    from gold_oblique_ellipse_fresh import PROBLEM_TEXT

    con_lai = {k: v for k, v in _MANH_MOI_NGHIA_VU.items()
               if k not in ("area", "radius")}
    monkeypatch.setattr(DP, "_MANH_MOI_NGHIA_VU", con_lai)
    assert DP.nghia_vu_ung_vien(PROBLEM_TEXT) == frozenset()
    assert DP.co_duong_thuc_thi(PROBLEM_TEXT, DOMAIN_HINH_HOC) is False


def test_15_XANH_LAI_sau_khi_go_moi_phep_tiem():
    """Khôi phục xong toàn bộ xanh — khẳng định tường minh, không ngầm định."""
    assert (_emit() & set(GEOMETRY_CHECKERS)) - set(_MANH_MOI_NGHIA_VU) == set()
    for nv, cau in (("area", "Tính diện tích elip (E)."),
                    ("lateral_area", "Tính diện tích xung quanh hình trụ."),
                    ("radius", "Tính bán kính mặt cầu."),
                    ("section_matches", "Xác định thiết diện của hình chóp.")):
        assert nv in nghia_vu_ung_vien(cau), nv
