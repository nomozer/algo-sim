# -*- coding: utf-8 -*-
"""MỖI DÒNG THẺ TỰ KHAI LOẠI CỦA NÓ. **0 lượt gọi model.**

    `CARD_CATEGORY_AFFORDANCE`, 2026-09-04.

─── LỖ ĐO ĐƯỢC ────────────────────────────────────────────────────────────

Thẻ vốn chia hai nhóm bằng TIÊU ĐỀ, còn từng dòng thì im lặng về loại của nó.
`AUDIT_MODEL_FACING_SCHEMA_SURFACE` đo khoảng cách:

    intersect_plane_curved   cách tiêu đề nhóm  5 dòng · cách `assign` 15 dòng
    construct_section        cách tiêu đề nhóm  7 dòng   ← CÂU LỆNH

Hai phép cùng toán hạng `solid`+`plane`, hình dạng gần trùng, cách nhau 9 dòng,
**không dấu hiệu nào trên chính dòng**. `cylinder_2` (probe V2) viết phép đầu
như một câu lệnh; chín lượt sửa không cứu được ca nào.

⚠️ Các ca dưới đây khẳng định **ngữ nghĩa**, không khoá văn phong tiếng Việt:
loại đọc từ `_tap_hinh_hoc()`, cửa tiêu thụ đọc từ `_cua_tieu_thu()`. Đổi cách
viết nhãn thì test vẫn xanh; đổi PHÂN LOẠI thì test đỏ.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.grammar_card import (
    _TIEU_DE_BIEU_THUC,
    _TIEU_DE_LENH,
    _cua_tieu_thu,
    _nhan_loai,
    _tap_hinh_hoc,
    _ten_phep,
    grammar_card,
    manh_hop_dong,
)

LENH, BT = _tap_hinh_hoc()
CUA = _cua_tieu_thu(LENH)


def _dong_phep() -> dict[str, str]:
    """Dòng thẻ của từng phép, tra theo tên phép."""
    ra = {}
    for d in grammar_card("hinh_hoc").splitlines():
        t = d.strip()
        if not t.startswith("["):
            continue
        ra[_ten_phep(d)] = t
    return ra


DONG = _dong_phep()


# ══ C1 · C2 — MỌI DÒNG TỰ KHAI LOẠI ══════════════════════════════════════
def test_C1_moi_phep_trong_the_deu_co_dong_rieng():
    """Không phép nào của miền bị bỏ sót — nếu sót, model không có nhãn cho nó."""
    thieu = sorted((LENH | BT) - set(DONG))
    assert not thieu, f"phép có trong từ vựng mà không có dòng thẻ: {thieu}"


@pytest.mark.parametrize("phep", sorted(LENH))
def test_C1b_dong_CAU_LENH_tu_khai_la_cau_lenh(phep):
    assert DONG[phep].startswith(_nhan_loai(phep, True, CUA)), DONG[phep]


@pytest.mark.parametrize("phep", sorted(BT))
def test_C2_dong_BIEU_THUC_tu_khai_la_bieu_thuc(phep):
    assert DONG[phep].startswith(_nhan_loai(phep, False, CUA)), DONG[phep]


# ══ C3 — CỬA TIÊU THỤ NHÌN THẤY NGAY TRÊN DÒNG ═══════════════════════════
@pytest.mark.parametrize("phep", sorted(BT))
def test_C3_bieu_thuc_neu_CUA_TIEU_THU_ngay_tren_dong(phep):
    """`EXPRESSION_CONSUMER_AFFORDANCE` — mô hình không phải suy từ một tiêu đề
    cách đó mười lăm dòng."""
    dong = DONG[phep]
    for cua in CUA[phep]:
        assert cua in dong.partition("]")[0], (phep, dong)


def test_C3b_cua_tieu_thu_DAN_TU_MODEL_chu_khong_viet_tay():
    """`construct_point` phải tự hiện ra làm cửa của các phép sinh ĐIỂM — nếu
    ai đó viết tay `→assign` cho tất cả thì ca này đỏ."""
    assert "construct_point" in CUA["midpoint"], CUA["midpoint"]
    assert "construct_point" in CUA["project_onto"]
    # Biểu thức KHÔNG sinh điểm thì chỉ `assign` nhận.
    assert CUA["measure"] == ("assign",), CUA["measure"]
    assert CUA["intersect_plane_curved"] == ("assign",)


def test_C6_doi_THAM_QUYEN_thi_nhan_tu_doi(monkeypatch):
    """Nhãn phải DẪN từ thẩm quyền, không phải từ một bảng chép tay.

    Không thể "đẩy một phép sang nhóm kia" bằng cách sửa một tập — nhóm là
    union Pydantic, và `_loc` lọc theo chính union ấy. Nên phép tiêm đúng chỗ
    là **thẩm quyền cửa tiêu thụ**: thêm một cửa và đòi dòng thẻ đi theo.
    """
    import app.simulation.semantic_program.grammar_card as G

    that = dict(G._cua_tieu_thu(LENH))
    that["measure"] = ("assign", "construct_point")
    monkeypatch.setattr(G, "_cua_tieu_thu", lambda lenh: that)

    dong = next(d for d in G.grammar_card("hinh_hoc").splitlines()
                if _ten_phep(d) == "measure")
    assert "construct_point" in dong.partition("]")[0], dong


# ══ C4 · C5 — MỘT THẨM QUYỀN, KHÔNG MÂU THUẪN ════════════════════════════
def test_C4_C5_khong_phep_nao_o_HAI_nhom():
    """`CATEGORY_AUTHORITIES = 1`. Một phép vừa là câu lệnh vừa là biểu thức
    thì nhãn nói dối một nửa số lần."""
    assert not (LENH & BT), sorted(LENH & BT)


def test_C7_phep_khong_phan_loai_duoc_thi_NEM():
    """§7 — sinh thẻ phải KÊU TO, không im lặng bỏ nhãn. Bỏ nhãn là quay về
    đúng trạng thái wave này đi sửa, mà không gì đỏ."""
    with pytest.raises(RuntimeError, match="KHÔNG câu lệnh nào nhận"):
        _nhan_loai("phep_la_khong_ai_nhan", False, CUA)


# ══ §16 — CA CHẤP NHẬN LỊCH SỬ: CYLINDER_2 ═══════════════════════════════
def test_cylinder_2_CATEGORY_DISCOVERABILITY():
    """Từ MỘT DÒNG, trả lời được cả hai câu mà `cylinder_2` trả lời sai:
    *phép này thuộc loại gì* · *dùng nó ở đâu*."""
    dong = DONG["intersect_plane_curved"]
    nhan = dong.partition("]")[0]
    assert "BIỂU THỨC" in nhan, dong
    assert "assign" in nhan, dong
    assert "LỆNH]" not in nhan, dong


def test_cap_BAY_nay_phan_biet_duoc_TAI_CHO():
    """Cặp gần trùng nhất trong thẻ — cùng toán hạng `solid`+`plane`, khác
    nhóm. Trước wave này chỉ một tiêu đề cách xa mới phân biệt được."""
    lenh_d, bt_d = DONG["construct_section"], DONG["intersect_plane_curved"]
    assert "solid" in lenh_d and "plane" in lenh_d
    assert "solid" in bt_d and "plane" in bt_d
    assert lenh_d.partition("]")[0] != bt_d.partition("]")[0], (
        "hai phép khác nhóm mà nhãn giống nhau")


# ══ §9 — ĐẠI DIỆN MỖI NHÓM, LOẠI ĐỌC TỪ THẨM QUYỀN ═══════════════════════
@pytest.mark.parametrize("phep", [
    "construct_point", "construct_plane", "construct_curved_solid",
    "construct_section", "declare_point",
    "measure", "midpoint", "vector_from_points", "intersect_plane_curved",
    "plane_perpendicular_to_line",
])
def test_dai_dien_moi_nhom_mang_dung_nhan(phep):
    la_lenh = phep in LENH
    assert phep in (LENH | BT), f"{phep} không thuộc từ vựng hình học"
    assert DONG[phep].startswith(_nhan_loai(phep, la_lenh, CUA)), DONG[phep]


# ══ §17 — MẢNH SỬA GIỮ NGUYÊN NGỮ NGHĨA LOẠI ═════════════════════════════
def test_manh_sua_giu_duoc_nhan_loai():
    """`REPAIR_CARD_SEMANTICS_ALIGNED` — mảnh cắt ra từ thẻ nên nó mang luôn
    nhãn; không có lời riêng cho lượt sửa."""
    loi = ("statements.4\n  Input tag 'intersect_plane_curved' found using "
           "'kind' does not match any of the expected tags: 'assign'")
    m = manh_hop_dong(loi, "hinh_hoc")
    dong = next(d for d in m.splitlines()
                if _ten_phep(d) == "intersect_plane_curved")
    assert "BIỂU THỨC" in dong and "assign" in dong.partition("]")[0]
    assert _TIEU_DE_BIEU_THUC in m
    assert any(_ten_phep(d) == "assign" for d in m.splitlines())


def test_manh_sua_cho_CAU_LENH_van_dung():
    loi = ("statements.0.construct_polygon.vertices\n"
           "  Input should be a valid list")
    m = manh_hop_dong(loi, "hinh_hoc")
    dong = next(d for d in m.splitlines() if _ten_phep(d) == "construct_polygon")
    assert dong.strip().startswith(_nhan_loai("construct_polygon", True, CUA))
    assert _TIEU_DE_LENH in m


# ══ §10 · §11 · §19 · §20 — CÁC ĐỐI CHỨNG VẪN MỞ ═════════════════════════
def test_KHONG_dong_ten_toan_hang_trong_wave_nay():
    """§10 — `OPERAND_NAME_CONVERGENCE` là wave riêng. Tên toán hạng phải y
    nguyên; wave này chỉ thêm nhãn LOẠI."""
    assert "from_point" in DONG["vector_from_points"]
    assert "to_point" in DONG["vector_from_points"]
    assert "a:" in DONG["midpoint"] and "b:" in DONG["midpoint"]
    assert "anchor" in DONG["construct_curved_solid"]
    assert "through_a" in DONG["construct_line"]


def test_KHONG_them_vi_du_theo_DANG_BAI():
    """§11 — `PROBLEM_FAMILY_CARD_TEMPLATES = 0`."""
    the = grammar_card("hinh_hoc")
    for cam in ("mặt cầu ngoại tiếp", "hình chóp", "ví dụ", "Ví dụ",
                "chẳng hạn", "tứ diện"):
        assert cam not in the, cam


def test_KHONG_them_tu_vung_moi():
    """`CARD_CATEGORY_AFFORDANCE` KHÔNG mở năng lực — nó chỉ thêm nhãn LOẠI.

    ⚠️ Con số ở đây là số phép **thẻ hình học in ra**, và nó tăng khi một wave
    SAU mở năng lực thật. Lần tăng đã ghi:

      15 → 16 (2026-09-07, `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_
      ELLIPSE_FOUNDATION`): thêm ĐÚNG MỘT phép — `intersect_plane_curved_
      ellipse` — cho thiết diện xiên của hình trụ. Nó là một phép RIÊNG chứ
      không phải một kiểu trả về "tuỳ lúc chạy" của `intersect_plane_curved`,
      vì kiểu trả về động sẽ lấy đi đúng thứ `ir_static_check` sinh ra để làm.

      LỆNH 9 → 10 (2026-09-07, `PLANE_FROM_EQUATION_REPRESENTATION`): thêm ĐÚNG
      MỘT lệnh — `construct_plane_from_equation` — cho mặt phẳng đề cho bằng
      phương trình. Lệnh RIÊNG chứ không phải một ô thứ tư của `construct_plane`
      (`through` nhận **tên ba điểm**; hệ số là **số**, và một ô đổi kiểu theo
      ô khác là đúng thứ kiểu tĩnh sinh ra để chặn). Số BIỂU THỨC giữ **16** —
      wave này không thêm phép nào sinh giá trị.

      LỆNH 10 → 11 (2026-09-25, `RECTANGULAR_PYRAMID_BOUNDED_GEOMETRY_AND_VISUAL_SEMANTIC_REPAIR`):
      thêm `construct_segment` cho đoạn thẳng hữu hạn. Số BIỂU THỨC giữ 16.

    Khẳng định gốc của test vẫn nguyên: wave `CARD_CATEGORY_AFFORDANCE` không
    thêm phép nào. Đây là cổng chống thêm phép **âm thầm** — mỗi lần tăng phải
    đi kèm một dòng nói phép nào và vì sao.
    """
    assert len(LENH) == 11 and len(BT) == 16, (len(LENH), len(BT))
