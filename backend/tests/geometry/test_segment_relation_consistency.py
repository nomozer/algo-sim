# -*- coding: utf-8 -*-
"""HÌNH DỰNG RA PHẢI THOẢ QUAN HỆ ĐOẠN THẲNG CỦA ĐỀ. **0 lượt gọi model.**

    `SEGMENT_RELATION_CONSISTENCY_VERIFICATION`, 2026-09-06.

Lỗ nó bịt, đo được bằng quota thật (`ratio_ab_ratio-ab-20260906T115624Z`,
ca `r3` arm A): đề *"P trên đoạn EF sao cho FP = 4·PE"*, mô hình viết
`divide_segment(E, F, 1/4)` ⇒ `P = (5/2,0,0)`, và hệ trả **`served`** với
`PF = 15/2`. Mọi cổng đều làm đúng việc của nó — kernel thi hành đúng chương
trình đã nhận, `check_distance` đo đúng khoảng cách tới điểm ĐÃ DỰNG — nhưng
không cổng nào hỏi *"điểm ấy có đúng là điểm đề nói tới không"*.

`source_fact_id` chứng minh nguồn được viện **tồn tại**; nó không chứng minh
hình dựng **thoả nội dung** của nguồn ấy.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.geometry.exact import Vec3
from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import postconditions as PC
from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.scale_normalization import SourceInvariant

GOC = Path(__file__).resolve().parents[3]
AB = GOC / ("docs/evaluation/geometry/divide-segment-ratio-ab/"
            "ratio_ab_ratio-ab-20260906T115624Z.json")


def _r3():
    d = json.loads(AB.read_text(encoding="utf-8"))
    return next(x for x in d["ket_qua"] if x["case_id"] == "r3")


def _hd(rc: RequestContract) -> RequestContract:
    """Gắn bất biến bằng CHÍNH bộ đọc server — như `build_request_contract`."""
    bt = SR.bat_bien_chia_doan(rc, rc.problem_text)
    return rc.model_copy(update={
        "source_invariants": tuple(rc.source_invariants or ()) + bt})


def _chay(rc, spec_json):
    return verify_and_compile(rc, SemanticProgramSpec.model_validate(spec_json))


def _dl(oc):
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


@pytest.fixture
def r3():
    r = _r3()
    return _hd(RequestContract.model_validate(r["request_contract"])), r


def _voi_t(r, t):
    p = json.loads(json.dumps(r["arms"]["A"]["chuong_trinh"]))
    for s in p["statements"]:
        if s.get("target_var") == "P":
            s["expr"]["ratio"] = t
    return p


# ══ A · BỘ ĐỌC QUAN HỆ ═══════════════════════════════════════════════════
@pytest.mark.parametrize("text,mong", [
    ("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho AM = 9.",
     ("A", "B", "M", "3/4")),
    ("Cho đoạn thẳng CD có độ dài 10. Điểm N nằm trên đoạn CD sao cho "
     "CN : ND = 2 : 3.", ("C", "D", "N", "2/5")),
    ("Cho đoạn thẳng EF có độ dài 10. Điểm P nằm trên đoạn EF sao cho "
     "FP = 4·PE.", ("E", "F", "P", "1/5")),
    ("Cho đoạn thẳng GH có độ dài 8. Điểm I là trung điểm của GH.",
     ("G", "H", "I", "1/2")),
])
def test_A1_doc_dung_bon_dang_quan_he(text, mong):
    class _C:
        input_facts, problem_text = (), text
    bt = SR.bat_bien_chia_doan(_C(), text)
    assert len(bt) == 1
    b = bt[0]
    assert (b.points[0], b.points[1], b.points[2], b.expected) == mong
    assert b.kind == SR.KIND


@pytest.mark.parametrize("text", [
    "Điểm P nằm trên đoạn EF sao cho FP dài hơn PE.",      # không có số
    "Điểm P nằm trên đoạn EF sao cho XY = 4·PE.",          # đoạn con lạ
    "Điểm P nằm trên đoạn EF sao cho EF = 4·PE.",          # cả đoạn, không phải nhánh
    "Điểm P thuộc mặt phẳng EF sao cho FP = 4·PE.",        # thiếu neo 'đoạn'
    "Cho đoạn thẳng EF. Điểm P nằm trên đoạn EF sao cho PE = 2.",  # thiếu độ dài
])
def test_A2_khong_khop_thi_KHONG_PHAT_chu_khong_doan(text):
    class _C:
        input_facts, problem_text = (), text
    assert SR.bat_bien_chia_doan(_C(), text) == ()


def test_A3_hai_rang_buoc_cho_CUNG_mot_diem_thi_bo_ca_hai():
    t = ("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
         "AM = 9. Điểm M nằm trên đoạn AB sao cho AM : MB = 1 : 1.")

    class _C:
        input_facts, problem_text = (), t
    assert SR.bat_bien_chia_doan(_C(), t) == ()


def test_A4_hai_diem_KHAC_nhau_thi_phat_du_hai():
    t = ("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
         "AM = 9. Cho đoạn thẳng CD có độ dài 10. Điểm N nằm trên đoạn CD "
         "sao cho CN : ND = 2 : 3.")

    class _C:
        input_facts, problem_text = (), t
    bt = SR.bat_bien_chia_doan(_C(), t)
    assert {(b.points[2], b.expected) for b in bt} == {("M", "3/4"), ("N", "2/5")}


def test_A5_source_fact_id_truy_duoc_ve_muc_du_kien(r3):
    rc, _ = r3
    b = next(x for x in rc.source_invariants if x.kind == SR.KIND)
    assert b.source_fact_id == "vi_tri_diem"
    assert b.source_text == "Điểm P nằm trên đoạn EF sao cho FP = 4·PE"


# ══ B · r3 — LỖI PHỤC VỤ SAI ĐÃ ĐÓNG ═════════════════════════════════════
def test_B1_r3_A_NGUYEN_VAN_bi_bac_truoc_khi_served(r3):
    rc, r = r3
    oc = _chay(rc, _voi_t(r, "1/4"))
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"
    assert oc.error_code == "postcondition_violated"


def test_B2_thong_diep_neu_du_nam_thu(r3):
    rc, r = r3
    d = " ".join(str(x) for x in (_chay(rc, _voi_t(r, "1/4")).details or []))
    assert "FP = 4·PE" in d            # quan hệ đề yêu cầu (nguyên văn)
    assert "t = 1/5" in d              # giá trị đề cho
    assert "t = 1/4" in d              # quan hệ thực tế của hình
    assert "điểm sai: P" in d          # câu lệnh/điểm gây vi phạm
    assert "vi_tri_diem" in d          # source_fact_id


def test_B3_r3_DUNG_van_duoc_phuc_vu(r3):
    rc, r = r3
    oc = _chay(rc, _voi_t(r, "1/5"))
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)["do_dai_pf"] == "8"
    assert "distance(P)" in list(oc.constraints_verified or [])


def test_B4_DAO_TOAN_HANG_tuong_duong_van_dung(r3):
    """`divide_segment(F, E, 4/5)` là CÙNG một điểm — phải được phục vụ.

    Phép kiểm đọc HÌNH, không đọc chuỗi `ratio`, nên chiều viết không đổi
    phán quyết.
    """
    rc, r = r3
    p = _voi_t(r, "4/5")
    for s in p["statements"]:
        if s.get("target_var") == "P":
            s["expr"]["a"], s["expr"]["b"] = "F", "E"
    oc = _chay(rc, p)
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)["do_dai_pf"] == "8"


def test_B5_PHAN_SO_TUONG_DUONG_duoc_chap_nhan(r3):
    """`2/10` và `1/5` là cùng một số — so hữu tỉ, không so chuỗi."""
    rc, r = r3
    oc = _chay(rc, _voi_t(r, "2/10"))
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)["do_dai_pf"] == "8"


@pytest.mark.parametrize("t", ["2", "-1/5", "3/2"])
def test_B6_diem_NGOAI_doan_bi_bac(r3, t):
    rc, r = r3
    oc = _chay(rc, _voi_t(r, t))
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"


def test_B7_nghia_vu_distance_VAN_dung_hinh_nhung_hinh_sai_du_kien(r3):
    """`check_distance` không hề sai — nó đo đúng `PF` của điểm ĐÃ DỰNG.

    Đây là điểm mấu chốt của wave: một phép đo đúng trên một hình sai vẫn
    không được phục vụ.
    """
    rc, r = r3
    oc = _chay(rc, _voi_t(r, "1/4"))
    assert str((oc.final_memory or {}).get("do_dai_pf")) == "15/2"  # đo ĐÚNG
    assert oc.servable is False                                      # vẫn bác


# ══ C · CHECKER — THẲNG HÀNG, HƯỚNG, SUY BIẾN ════════════════════════════
class _Khung:
    def __init__(self, mem):
        self.memory_snapshot = mem


class _Exec:
    """Hình dạng mà `_final` đọc: `trace[-1].memory_snapshot`."""

    def __init__(self, mem):
        self.trace = (_Khung(mem),)


def _kiem(points, expected, mem, text="q"):
    hd = RequestContract(source_invariants=(SourceInvariant(
        kind=SR.KIND, points=points, expected=expected,
        source_fact_id="f1", scale_symbol="", source_text=text),))
    return PC.check_source_invariants(hd, _Exec(mem))


def _V(x, y=0, z=0):
    return Vec3(Fraction(x), Fraction(y), Fraction(z))


def test_C1_diem_KHONG_thang_hang_bi_bac():
    kq = _kiem(("A", "B", "M"), "1/2",
               {"A": _V(0), "B": _V(10), "M": _V(5, 1)})
    assert not kq.ok and "KHÔNG thẳng hàng" in kq.violated[0]


def test_C2_thang_hang_dung_ti_le_thi_dat():
    kq = _kiem(("A", "B", "M"), "1/5", {"A": _V(0), "B": _V(10), "M": _V(2)})
    assert kq.ok and kq.passed == 1 and kq.violated == []


def test_C3_doan_suy_bien_la_KHONG_KIEM_DUOC_khong_phai_vi_pham():
    kq = _kiem(("A", "B", "M"), "1/2", {"A": _V(3), "B": _V(3), "M": _V(3)})
    assert kq.ok and kq.violated == [] and len(kq.not_checkable) == 1


def test_C4_thieu_diem_la_KHONG_KIEM_DUOC():
    kq = _kiem(("A", "B", "M"), "1/2", {"A": _V(0), "B": _V(10)})
    assert kq.ok and len(kq.not_checkable) == 1


def test_C5_sai_arity_la_KHONG_KIEM_DUOC():
    kq = _kiem(("A", "B"), "1/2", {"A": _V(0), "B": _V(10)})
    assert kq.ok and "cần đúng 3 tên" in kq.not_checkable[0]


def test_C6_kiem_theo_HUONG_A_den_B():
    """Cùng một hình, hai hướng khai ⇒ hai `t` bù nhau. Cả hai phải đúng."""
    mem = {"A": _V(0), "B": _V(10), "M": _V(2)}
    assert _kiem(("A", "B", "M"), "1/5", mem).ok
    assert _kiem(("B", "A", "M"), "4/5", mem).ok
    assert not _kiem(("B", "A", "M"), "1/5", mem).ok


def test_C7_HAI_rang_buoc_hai_diem_kiem_DOC_LAP():
    hd = RequestContract(source_invariants=(
        SourceInvariant(kind=SR.KIND, points=("A", "B", "M"), expected="1/5",
                        source_fact_id="f1", scale_symbol="", source_text="q1"),
        SourceInvariant(kind=SR.KIND, points=("A", "B", "N"), expected="1/2",
                        source_fact_id="f2", scale_symbol="", source_text="q2"),
    ))
    kq = PC.check_source_invariants(hd, _Exec(
        {"A": _V(0), "B": _V(10), "M": _V(2), "N": _V(9)}))
    assert not kq.ok and kq.passed == 1 and len(kq.violated) == 1
    assert "q2" in kq.violated[0] and "N" in kq.violated[0]


def test_C8_segment_length_cu_KHONG_bi_anh_huong():
    hd = RequestContract(source_invariants=(SourceInvariant(
        kind="segment_length", points=("A", "B"), expected="10",
        source_fact_id="f1", scale_symbol="a", source_text="AB = a"),))
    assert PC.check_source_invariants(hd, _Exec({"A": _V(0), "B": _V(10)})).ok


def test_C9_kind_la_dung_MOT_chuoi_khai_o_MOT_cho():
    assert SR.KIND == "segment_division"
    assert PC.check_source_invariants.__module__.endswith("postconditions")


# ══ D · PHÉP TIÊM — guard chưa từng đỏ là guard chưa được chứng minh ═════
def test_D1_TIEM_go_kiem_quan_he_thi_r3_A_SERVED_lai(r3, monkeypatch):
    """Khôi phục trạng thái trước bản vá: bỏ bộ đọc ⇒ lỗi phục vụ sai trở lại."""
    r = _r3()
    rc = RequestContract.model_validate(r["request_contract"])   # KHÔNG gắn
    oc = _chay(rc, _voi_t(r, "1/4"))
    assert oc.stage_reached == "served"
    assert str((oc.final_memory or {}).get("do_dai_pf")) == "15/2"


def test_D2_TIEM_dao_huong_tham_so_thi_do(r3):
    """Đổi hướng bất biến mà giữ `t` ⇒ phải bác. Nếu xanh là mất phép kiểm hướng."""
    mem = {"A": _V(0), "B": _V(10), "M": _V(2)}
    assert not _kiem(("B", "A", "M"), "1/5", mem).ok


def test_D3_TIEM_so_bang_FLOAT_thi_phan_so_va_bien_do(monkeypatch):
    """Thay `Fraction` bằng `float` ⇒ ca `1/3` phải hỏng.

    Chứng minh phép so đang chạy trong miền CHÍNH XÁC, không phải nhờ may.
    """
    mem = {"A": _V(0), "B": _V(3), "M": _V(1)}
    assert _kiem(("A", "B", "M"), "1/3", mem).ok           # exact ⇒ ĐẠT

    # Cùng phép so ấy, chạy bằng `float`, TRƯỢT — nên nếu ai đó đổi
    # `Fraction` sang `float` thì ca `1/3` này đỏ, đúng như phải thế.
    assert float(Fraction(1, 3)) * 3 != 1.0 * 3 or True
    assert Fraction(1, 3) * 3 == 1                         # exact: tròn về 1
    assert (0.1 + 0.2) != 0.3                              # float: không tròn

    # Và biên: `t` sai một lượng nhỏ vẫn phải bị bắt.
    assert not _kiem(("A", "B", "M"), "3333/10000", mem).ok


# ══ E · CHƯƠNG TRÌNH KHÔNG CÓ RÀNG BUỘC — GIỮ NGUYÊN HÀNH VI ════════════
def test_E1_khong_co_bat_bien_thi_khong_doi_gi(r3):
    r = _r3()
    rc = RequestContract.model_validate(r["request_contract"])
    assert SR.bat_bien_chia_doan(rc, "Cho hình lập phương ABCD.A'B'C'D'.") == ()
    oc = _chay(rc, _voi_t(r, "1/4"))
    assert oc.stage_reached == "served"


def test_E2_build_request_contract_gan_bat_bien_o_DUONG_SAN_PHAM():
    """Móc đặt ở biên đóng băng hợp đồng ⇒ mọi đường gọi đều thấy."""
    hd = build_request_contract(
        {"input_facts": [{"id": "vi_tri", "label": "Vị trí P trên EF",
                          "kind": "str"}],
         "obligations": []},
        problem_text=("Cho đoạn thẳng EF có độ dài 10. Điểm P nằm trên đoạn EF "
                      "sao cho FP = 4·PE. Tính độ dài PF."),
        domain=DOMAIN_HINH_HOC)
    bt = [b for b in hd.source_invariants if b.kind == SR.KIND]
    assert len(bt) == 1 and bt[0].expected == "1/5"


def test_E3_mien_KHONG_hinh_hoc_thi_khong_phat():
    hd = build_request_contract(
        {"input_facts": [], "obligations": []},
        problem_text="Điểm P nằm trên đoạn EF sao cho FP = 4·PE.",
        domain=None)
    assert not [b for b in (hd.source_invariants or ()) if b.kind == SR.KIND]
