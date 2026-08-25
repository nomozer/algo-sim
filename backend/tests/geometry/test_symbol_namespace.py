# -*- coding: utf-8 -*-
"""WAVE 4 — TASK 1: không gian tên ký hiệu hình học. **0 API call.**

ĐO ĐƯỢC Ở PHASE 5.5 (`5f42363`), `geo_01`:

    CONTRACT   witness = 'm'      ← chữ THƯỜNG
    CHƯƠNG TRÌNH khai   = 'M'      ← chữ HOA

Không phải model lệch danh xưng. **Hai hợp đồng của ta đánh nhau**: mô tả trường
`witness` bắt snake_case (đúng ở Tin học), còn hình học gọi điểm bằng chữ hoa.
Cả hai lượt LLM đều tuân thủ đúng luật được giao.

Sửa ở HAI tầng, và thứ tự quan trọng:

  ① NGUỒN — mô tả trường theo miền. Không thể sinh khớp sai.
  ② LƯỚI — `geometry_symbol_key`, hẹp và ĐẾM ĐƯỢC, cho lần model vẫn hạ chữ
    thường. Lưới không bao giờ được thay cho nguồn.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program import domain_profile as DP
from app.simulation.semantic_program.analyze_contract import (
    MO_TA_TEN_HINH_HOC,
    MO_TA_TEN_TIN_HOC,
    MO_TA_WITNESS_HINH_HOC,
    MO_TA_WITNESS_TIN_HOC,
    analyze_schema_for,
)
from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.coverage_gate import check_structural_coverage
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract


# ══ ① NGUỒN — mô tả trường theo MIỀN ═════════════════════════════════════
def test_hai_mien_co_mo_ta_ten_KHAC_NHAU():
    hh = analyze_schema_for(DP.DOMAIN_HINH_HOC)[
        "properties"]["obligations"]["items"]["properties"]
    th = analyze_schema_for(DP.DOMAIN_TIN_HOC)[
        "properties"]["obligations"]["items"]["properties"]
    assert hh["witness"]["description"] != th["witness"]["description"]
    assert hh["container"]["description"] != th["container"]["description"]


def test_mo_ta_HINH_HOC_khong_con_bat_snake_case():
    """Đây là NGUỒN của lỗi `geo_01`. Sửa ở đây thì không thể sinh khớp sai."""
    for m in (MO_TA_TEN_HINH_HOC, MO_TA_WITNESS_HINH_HOC):
        assert "snake_case" not in m.lower() or "ĐỪNG" in m
        assert "CHỮ HOA" in m


def test_mo_ta_TIN_HOC_giu_nguyen_snake_case():
    """Không hồi quy: quy ước Tin học ĐÚNG ở miền Tin học."""
    for m in (MO_TA_TEN_TIN_HOC, MO_TA_WITNESS_TIN_HOC):
        assert "snake_case" in m


# ══ ② LƯỚI — hẹp, có kiểu, KHÔNG phải `lower()` toàn cục ═════════════════
@pytest.mark.parametrize("a,b", [
    ("m", "M"), ("M", "m"), ("A", "a"),
    ("point_a", "A"), ("diem_m", "M"), ("p_s", "S"),
    ("a1", "A1"), ("M2", "m_2"),
])
def test_cung_MOT_ky_hieu_hinh_hoc(a, b):
    assert DP.geometry_symbol_key(a) == DP.geometry_symbol_key(b) is not None


@pytest.mark.parametrize("ten", [
    "volume", "distance", "abcd", "sabcd", "the_tich", "point_on_plane",
    "giao_tuyen", "", "   ", "α", "a-b-c-d",
])
def test_KHONG_phai_ky_hieu_thi_tra_None(ten):
    """Giới hạn ≤3 ký tự là thứ giữ cho phép đồng nhất không lan ra thành
    so-không-phân-biệt-hoa-thường toàn cục. `volume` ≢ `VOLUME`."""
    assert DP.geometry_symbol_key(ten) is None


def test_A_khac_a_o_MIEN_THONG_THUONG():
    """Yêu cầu tường minh của TASK 1. Một biến Tin học tên `a` KHÔNG bao giờ đi
    qua lưới này — lưới chỉ mở cho nghĩa vụ thuộc miền hình học (kiểm ở
    `test_luoi_KHONG_mo_cho_nghia_vu_tin_hoc`), nên `A != a` vẫn đúng ở đó."""
    from app.simulation.semantic_program.request_contract import _chuan_hoa_id

    # Ở tầng ĐỊNH DANH chung, hai tên vẫn là hai chuỗi khác nhau khi so thẳng.
    assert "A" != "a"
    # `_chuan_hoa_id` (dùng cho `source_fact_id`) là phép KHÁC và cũng không
    # được nhầm với phép này.
    assert _chuan_hoa_id("A") == _chuan_hoa_id("a")  # id: có gộp
    assert DP.geometry_symbol_key("A") == DP.geometry_symbol_key("a")  # ký hiệu


def test_TRUNG_KHOA_thi_TU_CHOI_khong_doan():
    """Chương trình khai cả `a` lẫn `A` thì không ai biết hợp đồng nói cái nào.
    Mơ hồ thì từ chối — cùng luật fail-closed của mọi cổng khác."""
    assert DP.khop_ky_hieu("m", {"M"}) == "M"
    assert DP.khop_ky_hieu("m", {"M", "m_"}) is None
    assert DP.khop_ky_hieu("volume", {"VOLUME"}) is None


# ══ TÍCH HỢP: C₁a hoà giải ĐÚNG ca `geo_01` ══════════════════════════════
def _spec(ten_diem: str):
    return SemanticProgramSpec(
        spec_version="1.0",
        title="Điểm thuộc mặt phẳng",
        memory_declarations=[
            MemoryDeclaration(name=n, type="point3") for n in ("A", "B", "C")
        ] + [
            MemoryDeclaration(name=ten_diem, type="point3"),
            MemoryDeclaration(name="abcd", type="plane3"),
        ],
        statements=[
            {"kind": "construct_plane", "target_var": "abcd",
             "through": ["A", "B", "C"]},
            {"kind": "construct_point", "target_var": ten_diem,
             "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
        ],
    )


def test_C1a_hoa_giai_m_va_M_va_GHI_LAI():
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="abcd",
                   params={"witness": "m"}),
    ))
    kq = check_structural_coverage(hd, _spec("M"))
    assert kq.ok, kq.missing
    assert kq.symbol_reconciled == ["point_on_plane(abcd): witness 'm' ≡ 'M'"]


def test_khop_thang_thi_KHONG_ghi_hoa_giai():
    """Quan trắc chỉ có nghĩa nếu nó im lặng khi không cần. Danh sách rỗng suốt
    một lượt đo = bản vá NGUỒN đã đủ, và lưới nên được gỡ."""
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="abcd",
                   params={"witness": "M"}),
    ))
    kq = check_structural_coverage(hd, _spec("M"))
    assert kq.ok and kq.symbol_reconciled == []


def test_luoi_KHONG_mo_cho_nghia_vu_tin_hoc():
    """Chốt phạm vi. `extremum` là nghĩa vụ Tin học, nên dù tên chỉ khác hoa
    thường thì C₁a vẫn phải từ chối — `A != a` ở miền thông thường."""
    hd = RequestContract(obligations=(
        Obligation(kind="extremum", container="arr", params={"witness": "m"}),
    ))
    spec = SemanticProgramSpec(
        spec_version="1.0", title="Tìm max",
        memory_declarations=[
            MemoryDeclaration(name="arr", type="array", initial_value=[1, 2]),
            MemoryDeclaration(name="M", type="int"),
        ],
        statements=[{"kind": "assign", "target_var": "M",
                     "expr": {"kind": "index", "container": "arr",
                              "index": {"kind": "literal", "value": 0}}}],
    )
    kq = check_structural_coverage(hd, spec)
    assert not kq.ok and kq.symbol_reconciled == []


# ══ RANH GIỚI CỦA BẢN NỚI C₁a — tìm ra khi test CŨ đỏ ═══════════════════
#
# Wave 4 nới phép kiểm "witness phải dẫn xuất từ container" cho nghĩa vụ QUAN HỆ
# hình học, vì `M` (trung điểm AB) đúng là KHÔNG dẫn xuất từ mặt phẳng `abcd` —
# hai thứ dựng song song rồi mới hỏi quan hệ.
#
# Bản nới ĐẦU bỏ hẳn phép kiểm, và `test_3_gan_dap_an_bang_assign_thi_TRUOT` đỏ
# ngay — đúng nó phải đỏ. Lập luận "C₂ tính lại nên không có gì để đoán" sai một
# điểm: **witness chính là thứ bị đoán**.
def test_witness_BIA_bang_literal_van_bi_chan():
    """`H = assign(literal [0,0,0])` — bịa một điểm rồi hy vọng nó nằm trên mặt.
    C₂ tính lại xong vẫn PASS, vì điểm ấy ĐÚNG LÀ nằm trên mặt. Nên chặn phải
    xảy ra ở C₁a, không thể trông vào C₂."""
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="abcd",
                   params={"witness": "H"}),
    ))
    spec = SemanticProgramSpec(
        spec_version="1.0", title="Bịa điểm",
        memory_declarations=[
            MemoryDeclaration(name=n, type="point3") for n in ("A", "B", "C")
        ] + [MemoryDeclaration(name="abcd", type="plane3"),
             MemoryDeclaration(name="H", type="point3")],
        statements=[
            {"kind": "construct_plane", "target_var": "abcd",
             "through": ["A", "B", "C"]},
            {"kind": "assign", "target_var": "H",
             "expr": {"kind": "literal", "value": [0, 0, 0]}},
        ],
    )
    kq = check_structural_coverage(hd, spec)
    assert not kq.ok
    assert any("không dẫn xuất từ đối" in m for m in kq.missing), kq.missing


def test_witness_DUNG_TU_DIEM_KHAC_thi_qua_du_khong_tu_container():
    """Ca `geo_01`. `M = midpoint(A,B)`, `abcd = plane(A,B,C)` — M không dẫn
    xuất từ abcd, mà đó là hình dạng ĐÚNG."""
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="abcd",
                   params={"witness": "M"}),
    ))
    assert check_structural_coverage(hd, _spec("M")).ok


def test_nghia_vu_DAI_LUONG_KHONG_duoc_mien():
    """`distance`/`angle`/`volume` có witness là một CON SỐ, và con số ấy phải
    đo ra từ container. Miễn cho chúng là mở lại đúng cửa `max_val = 89`."""
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="chop", params={"witness": "V"}),
    ))
    spec = SemanticProgramSpec(
        spec_version="1.0", title="Gán thẳng thể tích",
        memory_declarations=[
            MemoryDeclaration(name=n, type="point3") for n in "ABCDS"
        ] + [MemoryDeclaration(name="chop", type="solid"),
             MemoryDeclaration(name="V", type="float")],
        statements=[
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": list("ABCDS"),
             "faces": [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]},
            # gán thẳng đáp số, không dùng `measure`
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "literal", "value": "2/3"}},
        ],
    )
    kq = check_structural_coverage(hd, spec)
    assert not kq.ok
    assert any("không dẫn xuất từ 'chop'" in m for m in kq.missing), kq.missing


def test_khong_co_ten_nao_khop_thi_VAN_bao_ten_GOC():
    """Thông điệp phải nói tên HỢP ĐỒNG đòi, không nói tên đã bị lưới đổi —
    người đọc cần thấy đúng thứ `analyze` khai."""
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="abcd",
                   params={"witness": "h"}),
    ))
    kq = check_structural_coverage(hd, _spec("M"))
    assert not kq.ok
    assert "'h'" in " ".join(kq.missing)
