# -*- coding: utf-8 -*-
"""P0 — `NormalizedSourceInvariantGate`. Mười hai ca A–L. 0 API call.

Lỗ đã QUAN SÁT ĐƯỢC (`wave6-canary-b/w3-thang-lan1`): hợp đồng chốt `AB = 1`,
`SA = 4/5`; chương trình dựng `A(−16,0,0) B(9,0,0) S(0,0,12)` — tức `AB = 25`,
`SA = 20`. Hình đúng về QUAN HỆ, sai về THANG, và học sinh đọc `12` cho bài có
đáp án `12a/25`. Không cổng nào bắt, vì các điểm ấy đi qua kênh tự do hệ trục
nên chẳng ghim về mục dữ kiện nào.

Ở một lượt khác cùng đề, mô hình CÓ ghim và **bị bắt**. Tức phép bắt đang phụ
thuộc trí nhớ của mô hình. Đó là thứ file này đóng lại.

Ca E và F là hai ca quan trọng nhất: chúng chứng minh cổng chạy **bất kể** IR
khai `source_fact_id` thế nào — không khai, hay khai sai, đều không đổi phán
quyết. Mất hai ca ấy thì cổng lặng lẽ tụt về đúng chỗ hỏng cũ.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.postconditions import (
    ERR_NGUON_BI_VI_PHAM,
    check_source_invariants,
)
from app.simulation.semantic_program.validator import validate_semantic_program

DE = ("Cho hình chóp S.ABC có mặt phẳng (SAB) vuông góc với mặt đáy, tam giác "
      "SAB vuông tại S, AB = a, SA = 4a/5. Tính khoảng cách từ điểm S đến mặt "
      "phẳng (ABC).")


def _hd(de: str = DE, facts=None):
    facts = facts or [
        {"id": "ab_length", "label": "Độ dài cạnh AB", "value": "a"},
        {"id": "sa_length", "label": "Độ dài cạnh SA", "value": "4a/5"},
    ]
    return build_request_contract({"input_facts": facts}, problem_text=de,
                                  domain=DOMAIN_HINH_HOC)


class _Buoc:
    def __init__(self, mem):
        self.memory_snapshot = mem


class _Exec:
    """Giả lượt chạy. Cổng đọc `trace[-1].memory_snapshot` — **cùng ảnh chụp**
    mà C₂ đọc, không phải `final_memory`. Hai nguồn khác nhau ở đây thì hai
    cổng sẽ phán quyết trên hai trạng thái khác nhau."""

    def __init__(self, mem):
        self.final_memory = mem
        self.trace = (_Buoc(mem),)


def _mem(**diem):
    from app.simulation.geometry.exact import Vec3
    return {k: Vec3(*(Fraction(x) for x in v)) for k, v in diem.items()}


def _kiem(hd, mem, ten=None):
    return check_source_invariants(hd, _Exec(mem), ten_da_hoa_giai=ten)


# ══ BẤT BIẾN CÓ CẤU TRÚC — server phát, từ CÂU VĂN của đề ═════════════════
def test_bat_bien_sinh_ra_tu_de_khong_phai_tu_fact_id():
    hd = _hd()
    bt = {b.source_fact_id: b for b in hd.source_invariants}
    assert set(bt) == {"ab_length", "sa_length"}
    assert bt["ab_length"].points == ("A", "B")
    assert bt["ab_length"].expected == "1"
    assert bt["ab_length"].source_text == "AB = a"
    assert bt["sa_length"].points == ("S", "A")
    assert bt["sa_length"].expected == "4/5"
    assert bt["sa_length"].source_text == "SA = 4a/5"
    # Toán hạng KHÔNG suy từ `fact_id`: đổi id, điểm vẫn đúng vì đọc từ đề.
    hd2 = _hd(facts=[{"id": "x1", "label": "l", "value": "a"},
                     {"id": "x2", "label": "l", "value": "4a/5"}])
    assert {b.points for b in hd2.source_invariants} == {("A", "B"), ("S", "A")}


def test_expected_la_phan_so_CHINH_XAC_khong_float():
    for b in _hd().source_invariants:
        assert isinstance(b.expected, str)
        Fraction(b.expected)          # parse được, không đi qua float


# ══ A–D · bốn ca lõi ══════════════════════════════════════════════════════
def test_A_AB_bang_a_dung_thang_thi_PASS():
    kq = _kiem(_hd(), _mem(A=(0, 0, 0), B=(1, 0, 0), S=(0, 0, "4/5")))
    assert kq.ok and kq.passed == 2 and kq.violated == []


def test_B_AB_dung_25_thi_VI_PHAM():
    kq = _kiem(_hd(), _mem(A=(-16, 0, 0), B=(9, 0, 0), S=(0, 0, 12)))
    assert not kq.ok and kq.error_code == ERR_NGUON_BI_VI_PHAM
    assert any("AB = a" in v for v in kq.violated)


def test_C_SA_bang_4a_tren_5_dung_thang_thi_PASS():
    """`S(0,0,4/5)` ⇒ SA = 4/5 đúng."""
    kq = _kiem(_hd(), _mem(A=(0, 0, 0), B=(1, 0, 0), S=(0, 0, "4/5")))
    assert kq.ok


def test_D_SA_bang_20_thi_VI_PHAM():
    """Đúng cấu hình `w3-thang` đã phục vụ nhầm: AB = 25, SA = 20."""
    kq = _kiem(_hd(), _mem(A=(-16, 0, 0), B=(9, 0, 0), S=(0, 0, 12)))
    assert not kq.ok
    assert len(kq.violated) == 2, kq.violated      # cả AB lẫn SA đều sai thang


# ══ E–F · PROVENANCE KHÔNG ĐƯỢC ẢNH HƯỞNG PHÁN QUYẾT ══════════════════════
def _spec(source_fact_id):
    """Chương trình dựng SAI THANG. `source_fact_id` là biến duy nhất."""
    d = {"name": "B", "type": "point3", "initial_value": [9, 0, 0],
         "model_assumption": "chọn hệ trục"}
    if source_fact_id is not None:
        d["source_fact_id"] = source_fact_id
    val = validate_semantic_program({
        "simulation_id": "geometry.demo", "title": "Demo thang",
        "description": "Chương trình dựng sai thang",
        "pedagogical_intent": "Cho thấy cơ chế ẩn",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [-16, 0, 0],
             "model_assumption": "gốc"}, d,
            {"name": "S", "type": "point3", "initial_value": [0, 0, 12],
             "model_assumption": "đỉnh"}],
        "statements": [], "obligations": []})
    assert val.ok, val.error
    return val.spec


@pytest.mark.parametrize("fid", [None, "ab_length", "khong_ton_tai", "sa_length"])
def test_EF_phan_quyet_KHONG_doi_theo_source_fact_id(fid):
    """Không khai · khai đúng · khai bịa · khai NHẦM mục — cùng một phán quyết.

    Đây là §5 viết thành test: `source_fact_id` chỉ để truy vết. Nếu ngày nào
    đó cổng đọc nó để quyết định có kiểm hay không, bốn ca này rẽ nhau ngay.
    """
    hd = _hd()
    mem = _mem(A=(-16, 0, 0), B=(9, 0, 0), S=(0, 0, 12))
    kq = _kiem(hd, mem)
    assert not kq.ok and kq.error_code == ERR_NGUON_BI_VI_PHAM
    _spec(fid)          # chương trình hợp lệ về schema ở cả bốn biến thể


def test_E_khong_khai_provenance_van_bi_bat():
    """Lỗ gốc: mọi điểm đi qua `model_assumption`, không ghim mục nào."""
    spec = _spec(None)
    assert all(d.source_fact_id is None for d in spec.memory_declarations)
    mem = {d.name: d for d in spec.memory_declarations}
    assert set(mem) == {"A", "B", "S"}
    kq = _kiem(_hd(), _mem(A=(-16, 0, 0), B=(9, 0, 0), S=(0, 0, 12)))
    assert not kq.ok, "không khai provenance KHÔNG được là đường thoát"


# ══ G–I · khi nào KHÔNG được sinh bất biến ════════════════════════════════
def test_G_so_cu_the_khong_sinh_bat_bien():
    hd = _hd("Cho hình lập phương ABCD.A'B'C'D' có AB = 5.",
             facts=[{"id": "ab_length", "label": "AB", "value": "5"}])
    assert hd.scale_binding is None and hd.source_invariants == ()


def test_H_ky_hieu_la_an_so_thi_khong_sinh_bat_bien():
    hd = _hd("Cho hình chóp S.ABC có AB = a. Tìm a biết thể tích bằng 6.",
             facts=[{"id": "ab_length", "label": "AB", "value": "a"}])
    assert hd.scale_binding is None and hd.source_invariants == ()


def test_I_hai_ky_hieu_tu_do_thi_khong_canonicalize():
    hd = _hd("Cho tứ diện ABCD có AB = a, CD = b.",
             facts=[{"id": "ab", "label": "AB", "value": "a"},
                    {"id": "cd", "label": "CD", "value": "b"}])
    assert hd.scale_binding is None and hd.source_invariants == ()


def test_L_bieu_thuc_hong_khong_tao_bat_bien_gia():
    hd = _hd("Cho hình chóp S.ABC có AB = a, SA = a√2.",
             facts=[{"id": "ab", "label": "AB", "value": "a"},
                    {"id": "sa", "label": "SA", "value": "a√2"}])
    assert hd.scale_binding is None and hd.source_invariants == ()


def test_L2_doan_khong_tach_duoc_thi_BO_QUA_chu_khong_doan():
    """`ABC = a` không phải một đoạn thẳng — bỏ qua, không bịa một bất biến."""
    hd = _hd("Cho hình chóp có ABC = a và AB = a.",
             facts=[{"id": "f1", "label": "l", "value": "a"}])
    assert hd.scale_binding is not None
    # Chỉ nhận `AB = a`; `ABC = a` không tách được thành hai điểm.
    assert all(len(b.points) == 2 for b in hd.source_invariants)


# ══ J · THẨM QUYỀN VỀ TÊN dùng chung ══════════════════════════════════════
def test_J_ten_phay_hoa_giai_qua_ban_do_chung():
    hd = _hd("Cho hình lăng trụ ABC.A'B'C' có A'B' = a.",
             facts=[{"id": "ab_length", "label": "A'B'", "value": "a"}])
    assert hd.source_invariants, "đoạn có phẩy phải sinh được bất biến"
    assert hd.source_invariants[0].points == ("A'", "B'")

    mem = _mem(A_prime=(0, 0, 0), B_prime=(1, 0, 0))
    # Không có bản đồ ⇒ không tìm được điểm ⇒ KHÔNG kết tội.
    kq = _kiem(hd, mem)
    assert kq.ok and kq.violated == [] and kq.not_checkable
    # Có bản đồ của C₁a ⇒ kiểm được, và kiểm ĐÚNG.
    ten = {"A'": "A_prime", "B'": "B_prime"}
    assert _kiem(hd, mem, ten).ok
    xa = _mem(A_prime=(0, 0, 0), B_prime=(7, 0, 0))
    assert not _kiem(hd, xa, ten).ok


# ══ K · SO BẰNG BÌNH PHƯƠNG, không khai căn, không float ══════════════════
def test_K_so_binh_phuong_bang_so_huu_ti():
    """`SA = 4/5` ⇒ `SA² = 16/25`. Đúng thì PASS, lệch một hạt thì VI PHẠM."""
    hd = _hd()
    assert _kiem(hd, _mem(A=(0, 0, 0), B=(1, 0, 0), S=(0, 0, "4/5"))).ok
    # `4/5 + 1/1000` — sai lệch nhỏ hơn mọi dung sai float thông thường.
    kq = _kiem(hd, _mem(A=(0, 0, 0), B=(1, 0, 0), S=(0, 0, "401/500")))
    assert not kq.ok, "phép so phải CHÍNH XÁC, không dung sai"


def test_K2_khoang_cach_VO_TI_van_kiem_duoc():
    """Không khai căn ⇒ cổng vẫn kiểm được cả cấu hình mà `measure` bó tay.

    `AB = 1` với `A(0,0,0) B(1,0,0)`: `distance_sq = 1 = 1²`. Nếu cổng đi
    đường khai căn thì mọi đoạn có độ dài vô tỉ sẽ thành `not_checkable` —
    tức đúng những bài phổ biến nhất lại mất phép kiểm.
    """
    hd = _hd("Cho tam giác ABC có AB = a.",
             facts=[{"id": "ab", "label": "AB", "value": "a"}])
    mem = _mem(A=(0, 0, 0), B=(1, 0, 0), C=(0, 1, 0))
    assert _kiem(hd, mem).ok and _kiem(hd, mem).passed == 1


# ══ §4 · VIOLATED ≠ NOT_CHECKABLE ═════════════════════════════════════════
def test_thieu_diem_thi_NOT_CHECKABLE_chu_khong_VI_PHAM():
    kq = _kiem(_hd(), _mem(A=(0, 0, 0)))       # thiếu B và S
    assert kq.ok and kq.violated == []
    assert len(kq.not_checkable) == 2 and kq.checked == 2 and kq.passed == 0


def test_bon_con_so_telemetry_cong_lai_dung():
    kq = _kiem(_hd(), _mem(A=(0, 0, 0), B=(1, 0, 0)))   # AB đúng, thiếu S
    assert kq.checked == kq.passed + len(kq.violated) + len(kq.not_checkable)
    assert kq.passed == 1 and len(kq.not_checkable) == 1
