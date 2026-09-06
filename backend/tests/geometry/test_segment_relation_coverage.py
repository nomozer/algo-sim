# -*- coding: utf-8 -*-
"""PHỦ QUAN HỆ CHIA ĐOẠN CHO LỚP CÂU TỔNG QUÁT. **0 lượt gọi model.**

    `SEGMENT_RELATION_COVERAGE_HARDENING`, 2026-09-06.

Wave trước đóng `r3/A`, nhưng bộ đọc khi ấy gộp neo và quan hệ vào MỘT mẫu
(*"M nằm trên đoạn AB **sao cho** …"*), nên nó **không đọc được `e4`** — một
ca có thật, đã chạy bằng quota thật:

    "… mặt phẳng vuông góc với PQ **cắt PQ tại điểm T** sao cho **PT bằng 20**
     …, chiều cao **PQ bằng 28**"

Ba thứ lệch cùng lúc: neo dạng **cắt**, từ nối **"bằng"**, và độ dài cả đoạn
nằm ở **câu khác**. Hệ quả đo được: `divide_segment(P,Q,1/2)` — sai dữ kiện
nhưng vẫn dựng được thiết diện — được **`served`** với bán kính `21/2`.

Ba trạng thái, và test ở đây giữ chúng **không bị gộp**:

    COVERED        phát được bất biến ⇒ checker phán trên hình
    NOT_CHECKABLE  thấy quan hệ nhưng không giải được ⇒ CHẶN `served`
    NOT_EXTRACTED  không đủ tín hiệu ⇒ im lặng, giữ hành vi cũ
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.geometry.radical import display, is_exact_number
from app.simulation.semantic_program import postconditions as PC
from app.simulation.semantic_program import segment_relation as SR
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[3]
E4 = GOC / "docs/evaluation/geometry/obligation-container-binding/cases/e4.json"


def _nap_e4():
    return json.loads(E4.read_text(encoding="utf-8"))


def _hd(rc: RequestContract) -> RequestContract:
    bt = SR.bat_bien_chia_doan(rc, rc.problem_text)
    return rc.model_copy(update={
        "source_invariants": tuple(rc.source_invariants or ()) + bt})


def _doc(text: str, facts=()):
    class _C:
        input_facts, problem_text = facts, text
    return SR.bat_bien_chia_doan(_C(), text)


def _mot(text: str, facts=()):
    bt = _doc(text, facts)
    assert len(bt) == 1, [(b.kind, b.points, b.expected) for b in bt]
    return bt[0]


@pytest.fixture
def e4():
    d = _nap_e4()
    return _hd(RequestContract.model_validate(d["request_contract"])), d


def _voi(d, rc, a, b, t):
    p = json.loads(json.dumps(d["parsed_input"]))
    for s in p["statements"]:
        if s.get("target_var") == "T":
            s["expr"]["a"], s["expr"]["b"], s["expr"]["ratio"] = a, b, t
    return verify_and_compile(rc, SemanticProgramSpec.model_validate(p))


def _dl(oc):
    return {k: display(v) for k, v in (oc.final_memory or {}).items()
            if is_exact_number(v)}


# ══ A · e4 — KHOẢNG PHỦ ĐÃ THIẾU ═════════════════════════════════════════
def test_A1_e4_PHAT_duoc_bo_ba_va_ti_le(e4):
    rc, _ = e4
    bt = [b for b in rc.source_invariants if b.kind == SR.KIND]
    assert len(bt) == 1
    assert bt[0].points == ("P", "Q", "T")
    assert bt[0].expected == "5/7"            # 20/28


def test_A2_e4_nguon_truy_duoc_va_thong_diep_giu_ca_HAI_ve(e4):
    rc, _ = e4
    b = next(x for x in rc.source_invariants if x.kind == SR.KIND)
    assert b.source_fact_id                    # truy về một mục dữ kiện
    assert "cắt PQ tại điểm T" in b.source_text     # NEO: chia đoạn nào
    assert "PT = 20" in b.source_text               # MẢNH: theo tỉ lệ nào


def test_A3_e4_dung_t_5_7_van_duoc_phuc_vu(e4):
    rc, d = e4
    oc = _voi(d, rc, "P", "Q", "5/7")
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)["ban_kinh_t"] == "15"


def test_A4_e4_SAI_TI_LE_nhung_van_dung_duoc_hinh_thi_BI_BAC(e4):
    """Phản ví dụ chính của wave.

    `t = 1/2` cho một điểm NẰM TRONG khối, nên kernel dựng được thiết diện và
    checker đo đúng bán kính `21/2`. Trước wave này ca ấy **`served`** — một
    đáp số sai, im lặng. Nay nó phải bị chặn vì hình KHÔNG thoả dữ kiện.
    """
    rc, d = e4
    oc = _voi(d, rc, "P", "Q", "1/2")
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"
    t = " ".join(str(x) for x in (oc.details or []))
    assert "NORMALIZED_SOURCE_VIOLATED" in t
    assert "t = 5/7" in t and "t = 1/2" in t and "điểm sai: T" in t


def test_A5_e4_DAO_HUONG_dung_cung_mot_diem_thi_duoc_chap_nhan(e4):
    """`divide_segment(Q, P, 2/7)` dựng ĐÚNG `T` — phải được phục vụ.

    Kiểm đọc HÌNH, không đọc chuỗi `ratio`, nên chiều viết không đổi phán quyết.
    """
    rc, d = e4
    oc = _voi(d, rc, "Q", "P", "2/7")
    assert oc.stage_reached == "served", oc.details
    assert _dl(oc)["ban_kinh_t"] == "15"


# ══ B · KHÔNG PHỤ THUỘC TÊN BÀI ══════════════════════════════════════════
def test_B1_doi_ten_nhat_quan_sang_A_B_M_giu_ket_qua():
    goc = ("Hình nón có đỉnh P và tâm đáy Q, chiều cao PQ bằng 28. Một mặt "
           "phẳng vuông góc với PQ cắt PQ tại điểm T sao cho PT bằng 20.")
    moi = goc.replace("P", "A").replace("Q", "B").replace("T", "M")
    a, b = _mot(goc), _mot(moi)
    assert (a.points, a.expected) == (("P", "Q", "T"), "5/7")
    assert (b.points, b.expected) == (("A", "B", "M"), "5/7")


def test_B2_doi_SO_thi_ti_le_doi_theo():
    b = _mot("Đoạn PQ bằng 35. Một mặt phẳng cắt PQ tại điểm M sao cho "
             "PM bằng 15.")
    assert b.points == ("P", "Q", "M") and b.expected == "3/7"


def test_B3_du_kien_MB_doi_dung_theo_huong_A_den_B():
    """`MB = 3` trên `AB = 12` ⇒ `t` đo từ A là `9/12 = 3/4`."""
    b = _mot("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
             "MB = 3.")
    assert b.expected == "3/4"


def test_B4_ti_so_dung_m_tren_m_cong_n():
    b = _mot("Điểm N nằm trên đoạn CD sao cho CN : ND = 2 : 3.")
    assert b.expected == "2/5"


def test_B5_boi_so_theo_ca_hai_chieu():
    assert _mot("Điểm P nằm trên đoạn EF sao cho FP = 4·PE.").expected == "1/5"
    assert _mot("Điểm P nằm trên đoạn EF sao cho PE = 4·FP.").expected == "4/5"


@pytest.mark.parametrize("nhan", ["·", "×", "*", ""])
def test_B6_moi_dau_nhan_deu_doc_duoc(nhan):
    assert _mot(f"Điểm P nằm trên đoạn EF sao cho FP = 4{nhan}PE.").expected == "1/5"


def test_B7_phan_so_tuong_duong_so_CHINH_XAC():
    """`AM = 9` trên `AB = 12` ⇒ `3/4`, không phải chuỗi `9/12`."""
    b = _mot("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
             "AM = 9.")
    assert b.expected == "3/4"


def test_B8_quan_he_nam_o_HAI_InputFact_van_ghep_dung():
    """Luật ghép là *cùng xác định một bộ ba*, không phải *cùng một câu*."""
    class _F:
        def __init__(self, i, l, v):
            self.fact_id, self.label, self.values = i, l, v
    facts = (_F("f_dai", "Độ dài đoạn AB", (12,)),
             _F("f_vi_tri", "Điểm M nằm trên đoạn AB", ()),
             _F("f_am", "Độ dài đoạn AM", (9,)))
    b = _mot("Một mặt phẳng cắt AB tại điểm M.", facts)
    assert (b.points, b.expected) == (("A", "B", "M"), "3/4")
    assert b.source_fact_id


def test_B9_hai_doan_cung_xuat_hien_van_phan_biet():
    bt = _doc("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
              "AM = 9. Cho đoạn thẳng CD có độ dài 10. Điểm N nằm trên đoạn CD "
              "sao cho CN : ND = 2 : 3.")
    assert {(b.points, b.expected) for b in bt} == {
        (("A", "B", "M"), "3/4"), (("C", "D", "N"), "2/5")}


# ══ C · BA TRẠNG THÁI KHÔNG ĐƯỢC GỘP ═════════════════════════════════════
def test_C1_NOT_EXTRACTED_cau_khong_mo_ta_chia_doan():
    assert _doc("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 6.") == ()
    assert _doc("Tính thể tích khối chóp S.ABCD.") == ()


def test_C2_NOT_CHECKABLE_thay_quan_he_nhung_thieu_do_dai():
    b = _mot("Một mặt phẳng cắt PQ tại điểm T sao cho PT bằng 20.")
    assert b.kind == SR.KIND_CHUA_GIAI and b.expected == ""


def test_C3_NOT_CHECKABLE_MO_HO_hai_ti_le_khac_nhau():
    b = _mot("Cho đoạn thẳng AB có độ dài 12. Điểm M nằm trên đoạn AB sao cho "
             "AM = 9. Điểm M nằm trên đoạn AB sao cho AM : MB = 1 : 1.")
    assert b.kind == SR.KIND_CHUA_GIAI


def test_C4_NOT_CHECKABLE_CHAN_served(e4):
    """Trạng thái *chưa kiểm được* phải chặn — không im lặng cho qua."""
    rc, d = e4
    chua = next(b for b in SR.bat_bien_chia_doan(
        type("C", (), {"input_facts": (), "problem_text":
                       "Một mặt phẳng cắt PQ tại điểm T sao cho PT bằng 20."})(),
        None))
    rc2 = rc.model_copy(update={"source_invariants": (chua,)})
    oc = _voi(d, rc2, "P", "Q", "5/7")          # chương trình ĐÚNG
    assert oc.servable is False
    assert oc.stage_reached == "source_invariant"
    t = " ".join(str(x) for x in (oc.details or []))
    assert PC.ERR_NGUON_CHUA_KIEM_DUOC in t
    assert "KHÔNG tính được tỉ lệ chia" in t


def test_C5_NOT_CHECKABLE_khac_han_not_checkable_cu(e4):
    """`unresolved` chặn; `not_checkable` (thiếu vật trong trạng thái) KHÔNG."""
    from app.simulation.semantic_program.scale_normalization import SourceInvariant

    class _Khung:
        def __init__(self, mem):
            self.memory_snapshot = mem

    class _Exec:
        def __init__(self, mem):
            self.trace = (_Khung(mem),)

    thieu = RequestContract(source_invariants=(SourceInvariant(
        kind=SR.KIND, points=("A", "B", "M"), expected="1/2",
        source_fact_id="f", scale_symbol="", source_text="q"),))
    kq = PC.check_source_invariants(thieu, _Exec({}))
    assert kq.ok is True and kq.not_checkable and not kq.unresolved

    chua = RequestContract(source_invariants=(SourceInvariant(
        kind=SR.KIND_CHUA_GIAI, points=("A", "B", "M"), expected="",
        source_fact_id="f", scale_symbol="", source_text="q"),))
    kq2 = PC.check_source_invariants(chua, _Exec({}))
    assert kq2.ok is False and kq2.unresolved
    assert kq2.error_code == PC.ERR_NGUON_CHUA_KIEM_DUOC


def test_C6_VI_PHAM_thang_khi_co_ca_hai():
    """*"Hình sai"* là kết luận mạnh hơn *"chưa đọc hiểu"* — báo cái mạnh trước."""
    from fractions import Fraction

    from app.simulation.geometry.exact import Vec3
    from app.simulation.semantic_program.scale_normalization import SourceInvariant

    class _Khung:
        def __init__(self, mem):
            self.memory_snapshot = mem

    class _Exec:
        def __init__(self, mem):
            self.trace = (_Khung(mem),)

    V = lambda x: Vec3(Fraction(x), Fraction(0), Fraction(0))  # noqa: E731
    hd = RequestContract(source_invariants=(
        SourceInvariant(kind=SR.KIND, points=("A", "B", "M"), expected="1/2",
                        source_fact_id="f", scale_symbol="", source_text="q1"),
        SourceInvariant(kind=SR.KIND_CHUA_GIAI, points=("A", "B", "N"),
                        expected="", source_fact_id="g", scale_symbol="",
                        source_text="q2"),
    ))
    kq = PC.check_source_invariants(hd, _Exec({"A": V(0), "B": V(10), "M": V(2)}))
    assert kq.ok is False
    assert kq.error_code == PC.ERR_NGUON_BI_VI_PHAM      # vi phạm thắng
    assert kq.violated and kq.unresolved


# ══ D · PHÉP TIÊM ════════════════════════════════════════════════════════
def test_D1_TIEM_go_mau_CAT_thi_e4_do(monkeypatch):
    """Gỡ neo dạng *"cắt AB tại M"* ⇒ `e4` mất bất biến, quay lại `served` sai."""
    import re as _re
    monkeypatch.setattr(SR, "_NEO_CAT", _re.compile(r"(?!x)x"))
    d = _nap_e4()
    rc = _hd(RequestContract.model_validate(d["request_contract"]))
    assert not [b for b in rc.source_invariants if b.kind.startswith("segment_")]
    assert _voi(d, rc, "P", "Q", "1/2").stage_reached == "served"


def test_D2_TIEM_dao_huong_A_B_thi_do(e4):
    """Đổi hướng bất biến mà giữ `t` ⇒ chương trình ĐÚNG bị bác. Phải đỏ."""
    from app.simulation.semantic_program.scale_normalization import SourceInvariant

    rc, d = e4
    b = next(x for x in rc.source_invariants if x.kind == SR.KIND)
    dao = SourceInvariant(kind=b.kind, points=("Q", "P", "T"),
                          expected=b.expected, source_fact_id=b.source_fact_id,
                          scale_symbol="", source_text=b.source_text)
    rc2 = rc.model_copy(update={"source_invariants": (dao,)})
    assert _voi(d, rc2, "P", "Q", "5/7").servable is False


def test_D3_TIEM_bo_ghep_hai_InputFact_thi_do(monkeypatch):
    """Chỉ đọc `problem_text` ⇒ ca dữ kiện tách dòng mất bất biến."""
    monkeypatch.setattr(SR, "_van_ban",
                        lambda c, t: [SR._chuan(t or "")])

    class _F:
        def __init__(self, i, l, v):
            self.fact_id, self.label, self.values = i, l, v
    facts = (_F("f_dai", "Độ dài đoạn AB", (12,)),
             _F("f_am", "Độ dài đoạn AM", (9,)))
    bt = _doc("Một mặt phẳng cắt AB tại điểm M.", facts)
    # Không đọc dữ kiện thì KHÔNG CÒN mảnh quan hệ nào — tức `NOT_EXTRACTED`,
    # và chương trình đi tiếp không bị kiểm. Đó chính là thứ phép ghép cứu.
    assert bt == ()


def test_D4_TIEM_so_bang_FLOAT_thi_bien_phan_so_do():
    """`t` sai một lượng nhỏ vẫn phải bị bắt — phép so nằm trong miền chính xác."""
    from fractions import Fraction

    from app.simulation.geometry.exact import Vec3
    from app.simulation.semantic_program.scale_normalization import SourceInvariant

    class _Khung:
        def __init__(self, mem):
            self.memory_snapshot = mem

    class _Exec:
        def __init__(self, mem):
            self.trace = (_Khung(mem),)

    V = lambda x: Vec3(Fraction(x), Fraction(0), Fraction(0))  # noqa: E731
    mem = {"A": V(0), "B": V(7), "M": V(5)}
    def _kq(t):
        hd = RequestContract(source_invariants=(SourceInvariant(
            kind=SR.KIND, points=("A", "B", "M"), expected=t,
            source_fact_id="f", scale_symbol="", source_text="q"),))
        return PC.check_source_invariants(hd, _Exec(mem))
    assert _kq("5/7").ok                       # exact ⇒ ĐẠT
    assert not _kq("7142857/10000000").ok      # xấp xỉ float ⇒ BỊ BẮT
