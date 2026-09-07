# -*- coding: utf-8 -*-
"""CỔNG PHẠM VI BỎ SÓT BỐN NGHĨA VỤ ĐẠI LƯỢNG. **0 lượt gọi model.**

    Tìm ra trong `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`, 2026-09-07,
    bằng provider stub — **trước** khi tiêu một lượt quota nào.

─── PHÁT HIỆN ─────────────────────────────────────────────────────────────

`co_duong_thuc_thi` là cổng TẤT ĐỊNH đứng trước `analyze`. Hợp đồng của nó,
theo chính docstring: *"hệ có đường biểu diễn nào cho thứ đề này hỏi không"*.
Nó trả lời bằng `nghia_vu_ung_vien(text) & GEOMETRY_CHECKERS`.

Nhưng bảng manh mối `_MANH_MOI_NGHIA_VU` **thiếu bốn nghĩa vụ CÓ CHECKER**:

    area · lateral_area · radius · section_matches

Nên với một đề chỉ hỏi *"tính diện tích …"*, cổng trả **False** trong khi hệ
**có** đủ đường: `BANG_PHEP_DO["area"]`, `check_area`, và cả một kiểu
`ellipse3` vừa dựng xong. Đề bị từ chối ở tầng `scope` với
`GATE_NOT_SIMULATION_SUITABLE`, **0 lượt gọi model** — tức không phép đo nào về
hành vi mô hình chạy được cho cả một lớp bài.

─── VÌ SAO NÓ SỐNG SÓT LÂU: BA WAVE TRƯỚC LỌT NHỜ MAY ────────────────────

`CURVED_END_TO_END_FRESH_CONFIRMATION` hỏi **`radius`** của một đường tròn.
Manh mối duy nhất khớp đề ấy là **`perpendicular`** — từ cụm *"vuông góc với
SO"* trong phần MÔ TẢ, không phải phần hỏi. Bỏ hai chữ ấy đi thì lượt đo ấy
cũng đã chết ở `scope`.

Nghĩa là cổng đã cho đúng câu trả lời vì một lý do sai, và điều đó chỉ lộ ra
khi gặp một đề không tình cờ mang chữ nào trong bảng.

⚠️ Bộ test này **ghi lại lỗ**, không sửa nó — sửa là đụng mã sản phẩm và kéo
theo nhịp bump/đóng băng, việc của một wave riêng. Khi lỗ được vá,
`test_C1`/`test_C2` sẽ ĐỎ, và đó là dấu hiệu đúng để cập nhật chúng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    _MANH_MOI_NGHIA_VU,
    co_duong_thuc_thi,
    detect_domain,
    nghia_vu_ung_vien,
)
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
)

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

from gold_curved_end_to_end import PROBLEM_TEXT as DE_NON  # noqa: E402
from gold_oblique_ellipse_fresh import PROBLEM_TEXT as DE_ELIP  # noqa: E402

#: Bốn nghĩa vụ CÓ checker mà bảng manh mối không nhắc.
THIEU = frozenset({"area", "lateral_area", "radius", "section_matches"})


# ══ A · LỖ, ĐO BẰNG HAI BẢNG THẨM QUYỀN ══════════════════════════════════
def test_A1_bon_nghia_vu_CO_CHECKER_ma_KHONG_co_manh_moi():
    thieu = set(GEOMETRY_CHECKERS) - set(_MANH_MOI_NGHIA_VU)
    assert thieu == THIEU, thieu
    # Chiều ngược lại SẠCH — không manh mối nào trỏ một nghĩa vụ không checker.
    assert not (set(_MANH_MOI_NGHIA_VU) - set(GEOMETRY_CHECKERS))


def test_A2_he_THAT_SU_co_duong_cho_bon_nghia_vu_ay():
    """Nếu hệ KHÔNG có đường thì cổng từ chối là đúng — nên phải kiểm."""
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    for nv in ("area", "lateral_area", "radius"):
        assert nv in BANG_PHEP_DO, nv
        assert OBLIGATION_KINDS.get(nv), nv
        assert nv in GEOMETRY_CHECKERS, nv
    assert "section_matches" in GEOMETRY_CHECKERS


# ══ B · TÁI HIỆN TẤT ĐỊNH TRÊN ĐỀ CỦA WAVE ═══════════════════════════════
def test_B1_de_elip_bi_cong_pham_vi_chan__0_luot_goi():
    assert detect_domain(DE_ELIP) == DOMAIN_HINH_HOC     # ĐÚNG miền
    assert nghia_vu_ung_vien(DE_ELIP) == frozenset()     # KHÔNG manh mối nào
    assert co_duong_thuc_thi(DE_ELIP, DOMAIN_HINH_HOC) is False


@pytest.mark.parametrize("cach_viet", [
    "Tính diện tích elip (E).",
    "Tính diện tích của elip (E).",
    "Tính diện tích hình elip (E).",
    "Tính bán kính đường tròn (c).",
    "Tính diện tích xung quanh của hình trụ.",
])
def test_B2_moi_loi_hoi_ve_DAI_LUONG_deu_truot(cach_viet):
    """Không phải một cách viết xui — cả LỚP câu hỏi ấy trượt."""
    assert nghia_vu_ung_vien(cach_viet) == frozenset(), cach_viet


def test_B3_them_MOT_chu_khong_lien_quan_la_cong_MO():
    """Bằng chứng rằng cổng đang đọc CHỮ, không đọc thứ đề hỏi.

    Cùng câu hỏi ấy, thêm một cụm mô tả không liên quan gì tới đại lượng được
    hỏi, và cổng mở — vì nó khớp `perpendicular`.
    """
    hoi = "Tính diện tích elip (E)."
    assert co_duong_thuc_thi(hoi, DOMAIN_HINH_HOC) is False
    assert co_duong_thuc_thi(
        "Mặt phẳng vuông góc với trục. " + hoi, DOMAIN_HINH_HOC) is True


# ══ C · BA WAVE TRƯỚC LỌT NHỜ MAY ════════════════════════════════════════
def test_C1_de_bai_NON_cua_wave_truoc_qua_cong_VI_LY_DO_SAI():
    """Nó hỏi `radius`; manh mối khớp lại là `perpendicular`.

    ⚠️ Test này ĐỎ khi lỗ được vá (lúc ấy `radius` sẽ có mặt), và đó là dấu
    hiệu đúng để cập nhật nó — không phải một hồi quy.
    """
    uv = nghia_vu_ung_vien(DE_NON)
    assert co_duong_thuc_thi(DE_NON, DOMAIN_HINH_HOC) is True
    assert uv == frozenset({"perpendicular"}), uv
    assert "radius" not in uv, (
        "lỗ đã được vá — cập nhật test này và bỏ khối `HYPOTHESIS` trong "
        "docs/OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION.md")
    # …và bỏ đúng cụm ấy đi thì nó cũng chết ở cổng.
    assert co_duong_thuc_thi(
        DE_NON.replace("và vuông góc với SO ", ""), DOMAIN_HINH_HOC) is False


def test_C2_de_elip_NOI_BO_cua_wave_nen_tang_cung_truot():
    """Đề dùng trong `CURVED_MISSING_FAMILY_…` chưa bao giờ đi qua cổng thật.

    Nó chạy bằng `verify_and_compile` với hợp đồng dựng tay — đúng cho một
    phép đo về HỆ, và cũng là lý do lỗ này không lộ ra ở wave ấy.
    """
    de = ("Hình trụ tròn xoay có tâm hai đáy O và O', bán kính đáy bằng 3 và "
          "chiều cao OO' bằng 20. Ba điểm K, L, N nằm trên mặt trụ xác định "
          "mặt phẳng (P) cắt hình trụ theo elip (E). Tính diện tích của (E).")
    assert co_duong_thuc_thi(de, DOMAIN_HINH_HOC) is False


# ══ D · ĐƯỜNG SỬA, GHI SẴN ĐỂ WAVE SAU KHÔNG PHẢI TÌM LẠI ═══════════════
def test_D1_sua_la_MOT_bang_MOT_tham_quyen():
    """Chỗ sửa đúng là `_MANH_MOI_NGHIA_VU` — thêm cụm cho bốn nghĩa vụ.

    KHÔNG nới `co_duong_thuc_thi` thành 'cứ hình học thì cho qua': cổng ấy tồn
    tại để từ chối đề hỏi thứ hệ không dựng được, và bỏ nó là bỏ một lời từ
    chối đáng nói. Cũng KHÔNG dựng bảng manh mối thứ hai.
    """
    import inspect

    from app.simulation.semantic_program import domain_profile as DP

    than = inspect.getsource(DP.co_duong_thuc_thi)
    assert "_MANH_MOI_NGHIA_VU" not in than, (
        "cổng đọc bảng qua `nghia_vu_ung_vien` — một thẩm quyền, một cửa")
    assert "GEOMETRY_CHECKERS" in than
    # Bảng là dict tên-nghĩa-vụ → cụm; thêm bốn hàng là đủ, không đổi cấu trúc.
    assert all(isinstance(v, tuple) for v in _MANH_MOI_NGHIA_VU.values())
