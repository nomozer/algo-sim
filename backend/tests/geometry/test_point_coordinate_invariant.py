# -*- coding: utf-8 -*-
"""`POINT_COORDINATE_SOURCE_INVARIANT` — §7 ranh giới + §9 tiêm lỗi.

**0 lượt gọi model.**

Lỗ được bịt, đo ở `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY`: đề cho
`B(6,0,0)`, chương trình khai `B(99,7,0)`, `source_fact_id` trỏ một fact CÓ
THẬT ⇒ hệ phục vụ `V = 540` thay vì `45`, `unjustified_literals = []`.

Nguyên nhân KHÔNG phải *"analyze quên trích toạ độ"* — chạy lại với hợp đồng
có đủ toạ độ cho kết quả y hệt. Nguyên nhân: `source_fact_id` được kiểm **SỰ
TỒN TẠI**, không kiểm **SỰ KHỚP**.
"""
from __future__ import annotations

import copy
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
_SC = GOC / "backend" / "scripts"
if str(_SC) not in sys.path:
    sys.path.insert(0, str(_SC))

from app.simulation.geometry.exact import Vec3  # noqa: E402
from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.semantic_program import point_coordinate as PC  # noqa: E402
from app.simulation.semantic_program import postconditions as PO  # noqa: E402
from app.simulation.semantic_program.analyze_contract import (  # noqa: E402
    gan_bat_bien_nguon,
)
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

from gold_nonconvex_polyhedron import (  # noqa: E402
    GOLD, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD, WITNESS,
)


#: Giả lượt chạy — DÙNG LẠI test double của `test_source_invariant_gate`.
#: Cổng đọc `trace[-1].memory_snapshot`, KHÔNG đọc `final_memory`; dựng một
#: bản thứ hai ở đây là cách hai bộ test phán trên hai trạng thái khác nhau.
from test_source_invariant_gate import _Exec  # noqa: E402


def _hd(de: str, facts=None, obligations=None) -> RequestContract:
    hd = RequestContract.model_validate({
        "problem_text": de,
        "input_facts": facts or [],
        "obligations": obligations or [],
    })
    return gan_bat_bien_nguon(hd, de)


def _bt_toa_do(hd) -> list:
    return [b for b in (hd.source_invariants or ()) if b.kind == PC.KIND]


def _chay(spec: dict, ct: dict | None = None):
    hd = gan_bat_bien_nguon(
        RequestContract.model_validate(ct or REQUEST_CONTRACT_GOLD),
        PROBLEM_TEXT)
    return verify_and_compile(hd, SemanticProgramSpec.model_validate(spec))


def _v(kq) -> str | None:
    return {k: display(x) for k, x in (kq.final_memory or {}).items()
            if is_exact_number(x)}.get(WITNESS)


def _doi(ten: str, xyz: list, **truong) -> dict:
    g = copy.deepcopy(GOLD)
    for m in g["memory_declarations"]:
        if m["name"] == ten:
            m["initial_value"] = xyz
            m.update(truong)
    return g


# ══ §5 · BỘ PHÁT — ngưỡng đọc, đo bằng chính grammar ═══════════════════
@pytest.mark.parametrize("de,mong", [
    ("Cho A(1,2,3).", {"A": (1, 2, 3)}),
    ("Cho A = (1, 2, 3).", {"A": (1, 2, 3)}),
    ("Cho A(1; 2; 3).", {"A": (1, 2, 3)}),
    ("Cho A(-1, 2, -3).", {"A": (-1, 2, -3)}),
    ("Cho A(1/2, -3/4, 5).", {"A": (F(1, 2), F(-3, 4), 5)}),
    ("Cho A(1.5, 0, 2.25).", {"A": (F(3, 2), 0, F(9, 4))}),
    ("Cho A(0,0,0), B(1,0,0) và C(0,1,0).",
     {"A": (0, 0, 0), "B": (1, 0, 0), "C": (0, 1, 0)}),
    ("Cho A1(1,0,0) và A_2(2,0,0).", {"A1": (1, 0, 0), "A2": (2, 0, 0)}),
    ("Cho A₁(1,0,0).", {"A1": (1, 0, 0)}),
    ("Cho A'(7,0,0).", {"A'": (7, 0, 0)}),
])
def test_01_grammar_toa_do_da_chung_minh(de, mong):
    doc = PC.doc_toa_do([de])
    that = {k: tuple(next(iter(v))) for k, v in doc.items()}
    assert that == {k: tuple(F(x) for x in v) for k, v in mong.items()}


@pytest.mark.parametrize("de", [
    # Phương trình mặt phẳng — KHÔNG phải một điểm.
    "Mặt phẳng (α): 2x - z + 10 = 0 cắt hình trụ.",
    # Vectơ không gắn với TÊN ĐIỂM.
    "Vectơ pháp tuyến (1, 2, 3) của mặt phẳng.",
    "Cho vectơ n(1, 2, 3).",
    # Hai chữ cái ⇒ một đoạn/vectơ, không phải một điểm.
    "Cho AB(1, 2, 3).",
    # Độ dài và tỉ lệ.
    "Cho hình chóp S.ABCD có AB = 6 và SA = 8.",
    "Điểm M chia đoạn AB theo tỉ lệ 1:2.",
    # Nhãn hình, container, tên mặt phẳng.
    "Cho khối chóp S.ABCDE và mặt phẳng (P).",
    "Thiết diện (E) có diện tích 16π√5.",
    # Thập phân dấu PHẨY — cố ý ngoài ngưỡng, xem docstring `_SO`.
    "Cho A(1,5, 2, 3).",
])
def test_02_KHONG_bat_nham(de):
    assert PC.doc_toa_do([de]) == {}, PC.doc_toa_do([de])


def test_03_de_KHONG_cho_toa_do_thi_KHONG_phat_gi():
    """Quyền chọn hệ trục còn nguyên khi đề không nói gì về toạ độ."""
    hd = _hd("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a.")
    assert _bt_toa_do(hd) == []


def test_04_lap_lai_CUNG_gia_tri_chi_phat_MOT():
    hd = _hd("Cho A(1,2,3).",
             facts=[{"fact_id": "a", "label": "Điểm A(1,2,3)",
                     "values": ["A(1,2,3)"], "provenance": "confirmed"}])
    assert len(_bt_toa_do(hd)) == 1


def test_05_MAU_THUAN_thanh_unresolved_va_CHAN():
    """Đề nêu toạ độ cùng một điểm ở hai chỗ khác nhau ⇒ hệ không biết đề muốn
    điểm nào. Phục vụ một hình đoán bừa còn tệ hơn từ chối."""
    hd = _hd("Cho A(1,2,3). Sau đó lấy A(9,9,9).")
    ub = [b for b in hd.source_invariants if b.kind == PC.KIND_CHUA_GIAI]
    assert len(ub) == 1 and ub[0].points == ("A",)
    assert _bt_toa_do(hd) == []


# ══ §7 · ĐIỂM ĐỀ CHO TOẠ ĐỘ ═══════════════════════════════════════════
def test_06_toa_do_DUNG_van_served():
    kq = _chay(GOLD)
    assert kq.servable, (kq.error_code, kq.details[:2])
    assert _v(kq) == "45"
    st = kq.source_invariant_stats
    assert st["passed"] == 6 and st["violated"] == 0
    # ⚠️ `not_checkable == 1` là một bất biến CÓ SẴN, không phải của wave này:
    # câu *"đáy ABCDE nằm trong mặt phẳng z = 0"* sinh một `plane_equation`, và
    # chương trình không dựng mặt phẳng nào để đối chiếu. Ghim con số ấy để nếu
    # nó đổi thì có người nhìn — chứ không phải vì nó là mục tiêu.
    assert st["not_checkable"] == 1
    assert st["checked"] == 7 and st["unresolved"] == 0


@pytest.mark.parametrize("ten,xyz,ly_do", [
    ("B", [99, 7, 0], "sai cả ba thành phần"),
    ("B", [7, 0, 0], "sai ĐÚNG MỘT thành phần, vẫn trong mặt phẳng đáy"),
    ("D", [3, 3, 0], "mất phần lõm"),
    ("S", [2, 2, 90], "đổi chiều cao ⇒ thể tích khác mà vẫn hợp lệ"),
])
def test_07_toa_do_SAI_bi_BAT_BIEN_NGUON_tu_choi(ten, xyz, ly_do):
    kq = _chay(_doi(ten, xyz))
    assert not kq.servable, ly_do
    assert kq.stage_reached == "source_invariant"
    assert kq.source_invariant_stats["violated"] == 1


def test_07b_nhac_khoi_MAT_PHANG_day__KERNEL_chan_TRUOC():
    """⚠️ Ghi lại một điều đo được, không phải một điều mong muốn.

    `B(6,0,1)` cũng là *"sai đúng một thành phần"*, nhưng nó nhấc `B` ra khỏi
    mặt phẳng đáy, nên **kernel** bác trước bằng `POLYHEDRON_FACE_NOT_PLANAR`
    (`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`) và bất biến nguồn không bao giờ
    chạy tới.

    Hai cổng độc lập cùng chặn một ca là chuyện tốt; ghim ca này vào
    `source_invariant` sẽ là ghim SAI tầng, và ô ấy sẽ đỏ vì một lý do chẳng
    liên quan tới thứ nó bảo vệ.
    """
    kq = _chay(_doi("B", [6, 0, 1]))
    assert not kq.servable
    assert kq.stage_reached == "execution"
    assert any("POLYHEDRON_FACE_NOT_PLANAR" in d for d in kq.details)


def test_08_source_fact_id_TON_TAI_khong_cuu_duoc():
    """Đây là chính lỗ được bịt: trích dẫn nêu tên một fact CÓ THẬT, và trước
    bản vá điều đó là đủ để đi qua."""
    kq = _chay(_doi("B", [99, 7, 0], source_fact_id="dinh_B"))
    assert not kq.servable
    kq2 = _chay(_doi("B", [99, 7, 0], source_fact_id="dinh_A"))
    assert not kq2.servable


def test_09_model_assumption_khong_che_duoc_toa_do_de_cho():
    """Kênh tự do hệ trục KHÔNG được thắng một dữ kiện đề nêu tường minh."""
    g = _doi("B", [99, 7, 0])
    for m in g["memory_declarations"]:
        if m.get("type") == "point3":
            m.pop("source_fact_id", None)
            m["model_assumption"] = "Chọn hệ trục Oxyz như trên."
    kq = _chay(g)
    assert not kq.servable
    assert kq.source_invariant_stats["violated"] >= 1


def test_10_thong_bao_NOI_RO_diem_nao_va_lech_truc_nao():
    kq = _chay(_doi("B", [7, 0, 0]))
    t = " ".join(kq.details)
    assert "B" in t and "lệch" in t and "x" in t
    assert "(6, 0, 0)" in t and "(7, 0, 0)" in t


def test_11_doi_TOAN_BO_hinh_ma_the_tich_van_hop_le_bi_tu_choi():
    """Nhân đôi mọi toạ độ đáy: thể tích thành `180`, một con số "hợp lệ" —
    và hình thì không còn là hình của đề."""
    g = copy.deepcopy(GOLD)
    for m in g["memory_declarations"]:
        if m.get("type") == "point3" and m["name"] != "S":
            m["initial_value"] = [x * 2 for x in m["initial_value"]]
    kq = _chay(g)
    assert not kq.servable
    assert kq.source_invariant_stats["violated"] >= 1


def test_12_diem_VANG_khong_bi_ket_toi():
    """Đề nhắc một điểm mà chương trình không dựng ⇒ `not_checkable`, không
    phải `violated`. *"Đáng lẽ phải dựng"* là câu của cổng phủ."""
    hd = _hd("Cho A(1,2,3) và B(4,5,6).")
    kq = PO.check_source_invariants(hd, _Exec({"A": Vec3(F(1), F(2), F(3))}))
    assert kq.violated == []
    assert kq.passed == 1 and len(kq.not_checkable) == 1


# ══ §7 · HỆ QUY CHIẾU — quyền chọn hệ trục PHẢI còn ═══════════════════
def test_13_de_KHONG_cho_toa_do__goc_canonical_van_hop_le():
    de = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ đáy, SA = 3."
    hd = _hd(de, obligations=[{"kind": "volume", "container": "S.ABCD",
                               "params": {"witness": "V"}}])
    assert _bt_toa_do(hd) == []
    spec = {
        "spec_version": "1.0", "title": "Chóp vuông",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "Chọn hệ trục Oxyz với A tại gốc."}
            for n, v in (("A", [0, 0, 0]), ("B", [2, 0, 0]), ("C", [2, 2, 0]),
                         ("D", [0, 2, 0]), ("S", [0, 0, 3]))
        ] + [{"name": "kh", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "kh",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [["D", "C", "B", "A"], ["A", "B", "S"], ["B", "C", "S"],
                       ["C", "D", "S"], ["D", "A", "S"]], "label": "S.ABCD"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "kh"}},
        ],
    }
    kq = verify_and_compile(hd, SemanticProgramSpec.model_validate(spec))
    assert kq.servable, (kq.error_code, kq.details[:2])
    assert kq.source_invariant_stats.get("violated", 0) == 0


def test_14_de_KHONG_cho_toa_do__TINH_TIEN_he_truc_van_hop_le():
    """Cùng hình, gốc đặt chỗ khác. Không có bất biến toạ độ nào để phá."""
    de = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ đáy, SA = 3."
    hd = _hd(de, obligations=[{"kind": "volume", "container": "S.ABCD",
                               "params": {"witness": "V"}}])
    d = 5
    spec = {
        "spec_version": "1.0", "title": "Chóp vuông, gốc dời",
        "memory_declarations": [
            {"name": n, "type": "point3",
             "initial_value": [v[0] + d, v[1] - d, v[2]],
             "model_assumption": "Chọn hệ trục Oxyz tuỳ ý."}
            for n, v in (("A", [0, 0, 0]), ("B", [2, 0, 0]), ("C", [2, 2, 0]),
                         ("D", [0, 2, 0]), ("S", [0, 0, 3]))
        ] + [{"name": "kh", "type": "solid"}, {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "kh",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [["D", "C", "B", "A"], ["A", "B", "S"], ["B", "C", "S"],
                       ["C", "D", "S"], ["D", "A", "S"]], "label": "S.ABCD"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "kh"}},
        ],
    }
    kq = verify_and_compile(hd, SemanticProgramSpec.model_validate(spec))
    assert kq.servable, (kq.error_code, kq.details[:2])
    assert _v(kq) == "4"


# ══ §7 · ĐIỂM DẪN XUẤT — bất biến toạ độ KHÔNG thay producer ══════════
def test_15_diem_dan_xuat_van_phai_co_PRODUCER():
    """Bất biến toạ độ hỏi *"điểm ở đúng chỗ chưa"*; producer hỏi *"nó có được
    DỰNG ra không"*. Hai câu khác nhau, và câu thứ hai không được mất."""
    de = "Cho A(0,0,0), B(4,0,0). Gọi M là trung điểm AB."
    hd = _hd(de, facts=[
        {"fact_id": "a", "label": "Điểm A(0,0,0)", "values": ["A(0,0,0)"],
         "provenance": "confirmed"},
        {"fact_id": "b", "label": "Điểm B(4,0,0)", "values": ["B(4,0,0)"],
         "provenance": "confirmed"},
    ])
    spec = {
        "spec_version": "1.0", "title": "Trung điểm",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "a"},
            {"name": "B", "type": "point3", "initial_value": [4, 0, 0],
             "source_fact_id": "b"},
            # M khai THẲNG toạ độ đúng — vẫn phải bị chốt vì thiếu bước dựng.
            {"name": "M", "type": "point3", "initial_value": [2, 0, 0],
             "source_fact_id": "a"},
        ],
        "statements": [],
    }
    kq = verify_and_compile(hd, SemanticProgramSpec.model_validate(spec))
    assert not kq.servable
    assert "DERIVED_ENTITY_WITHOUT_PRODUCER" in " ".join(
        kq.details) or kq.error_code, kq.details[:2]


def test_16_diem_dan_xuat_DUNG_producer_van_PASS():
    de = "Cho A(0,0,0), B(4,0,0). Gọi M là trung điểm AB."
    hd = _hd(de, facts=[
        {"fact_id": "a", "label": "Điểm A(0,0,0)", "values": ["A(0,0,0)"],
         "provenance": "confirmed"},
        {"fact_id": "b", "label": "Điểm B(4,0,0)", "values": ["B(4,0,0)"],
         "provenance": "confirmed"},
    ])
    spec = {
        "spec_version": "1.0", "title": "Trung điểm",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "a"},
            {"name": "B", "type": "point3", "initial_value": [4, 0, 0],
             "source_fact_id": "b"},
            {"name": "M", "type": "point3"},
        ],
        "statements": [
            {"kind": "construct_point", "target_var": "M",
             "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
        ],
    }
    kq = verify_and_compile(hd, SemanticProgramSpec.model_validate(spec))
    assert kq.servable, (kq.error_code, kq.details[:2])
    assert kq.source_invariant_stats.get("violated", 0) == 0
    # Ba bất biến ĐẠT: toạ độ `A` · toạ độ `B` · và `segment_division` cho `M`
    # (bộ phát CÓ SẴN đọc *"M là trung điểm AB"*). Ba tầng cùng nói về một
    # hình, không tầng nào thay tầng nào.
    assert kq.source_invariant_stats.get("passed", 0) == 3


# ══ §9 · TIÊM LỖI ═════════════════════════════════════════════════════
def test_TIEM_1_bo_BO_PHAT__ca_B_99_duoc_phuc_vu_lai(monkeypatch):
    monkeypatch.setattr(PC, "bat_bien_toa_do", lambda c, t: ())
    kq = _chay(_doi("B", [99, 7, 0]))
    assert kq.servable and _v(kq) == "540"


def test_TIEM_2_bo_DISPATCH_checker__ca_sai_duoc_phuc_vu_lai(monkeypatch):
    """Đổi `kind` mà **chỉ ở phía CHECKER** — bộ phát vẫn phát như cũ, nên
    nhánh dispatch không còn khớp và bất biến rơi xuống *"chưa có checker"*.

    ⚠️ Vá `PC.KIND` là VÔ HIỆU: bộ phát và checker cùng đọc hằng ấy, nên nó
    đổi cả hai vế và phép tiêm tự triệt tiêu. Đo được ở lượt đầu — guard xanh
    mà chẳng chứng minh gì. Phải vá đúng MỘT vế.
    """
    import app.simulation.semantic_program.route as RT

    goc = PO.check_source_invariants

    def bo_dispatch(contract, exec_result, ten_da_hoa_giai=None):
        loc = contract.model_copy(update={"source_invariants": tuple(
            b.model_copy(update={"kind": "point_coordinate_DA_TAT"})
            if b.kind == PC.KIND else b
            for b in (contract.source_invariants or ()))})
        return goc(loc, exec_result, ten_da_hoa_giai)

    monkeypatch.setattr(RT, "check_source_invariants", bo_dispatch)
    kq = _chay(_doi("B", [99, 7, 0]))
    assert kq.servable and _v(kq) == "540"
    # …và cổng tự khai là nó KHÔNG kiểm được, thay vì im lặng.
    assert kq.source_invariant_stats["not_checkable"] >= 6


def test_TIEM_3_chi_kiem_TON_TAI_cua_fact__tai_hien_loi_goc(monkeypatch):
    """Mô phỏng đúng luật cũ: có `source_fact_id` trỏ fact có thật là đủ."""
    import app.simulation.semantic_program.route as RT

    goc = PO.check_source_invariants

    def chi_ton_tai(contract, exec_result, ten_da_hoa_giai=None):
        loc = contract.model_copy(update={"source_invariants": tuple(
            b for b in (contract.source_invariants or ())
            if b.kind != PC.KIND)})
        return goc(loc, exec_result, ten_da_hoa_giai)

    monkeypatch.setattr(RT, "check_source_invariants", chi_ton_tai)
    kq = _chay(_doi("B", [99, 7, 0], source_fact_id="dinh_B"))
    assert kq.servable and _v(kq) == "540"


def test_TIEM_4_so_bang_DUNG_SAI_float__phan_vi_du_exact_lot_qua():
    """`1/3` và `333333333333/1000000000000` lệch < 1e-12: mọi dung sai float
    thông thường coi chúng bằng nhau. Phép so CHÍNH XÁC thì không."""
    a, b = F(1, 3), F(333333333333, 1000000000000)
    assert a != b
    assert abs(float(a) - float(b)) < 1e-12       # float KHÔNG phân biệt nổi

    de = "Cho A(1/3, 0, 0)."
    hd = _hd(de)
    kq = PO.check_source_invariants(hd, _Exec({"A": Vec3(b, F(0), F(0))}))
    assert not kq.ok and len(kq.violated) == 1


def test_TIEM_5_bo_THAM_QUYEN_TEN__ca_chi_so_va_phay_do(monkeypatch):
    """Nấc ③ dùng `chuan_hoa_ten`. Bỏ nó thì `O'` không nối được `Oprime`."""
    de = "Cho O(0,0,0) và O'(0,0,20)."
    hd = _hd(de)
    mem = {"O": Vec3(F(0), F(0), F(0)), "Oprime": Vec3(F(0), F(0), F(20))}
    exec_gia = _Exec(mem)
    assert PO.check_source_invariants(hd, exec_gia).passed == 2

    monkeypatch.setattr(
        "app.simulation.semantic_program.source_entities.chuan_hoa_ten",
        lambda t: frozenset({t}))
    kq = PO.check_source_invariants(hd, exec_gia)
    assert kq.passed == 1 and len(kq.not_checkable) == 1


def test_TIEM_6_model_assumption_THANG_du_kien__ca_sai_lot_qua(monkeypatch):
    """Nếu bộ phát chịu im khi điểm khai bằng `model_assumption` thì kênh tự
    do hệ trục thành cửa sau cho mọi toạ độ sai."""
    goc = PC.bat_bien_toa_do

    def nhuong_gia_dinh(contract, problem_text):
        return ()                       # "điểm có model_assumption ⇒ bỏ qua"

    monkeypatch.setattr(PC, "bat_bien_toa_do", nhuong_gia_dinh)
    g = _doi("B", [99, 7, 0])
    for m in g["memory_declarations"]:
        if m.get("type") == "point3":
            m.pop("source_fact_id", None)
            m["model_assumption"] = "Chọn hệ trục Oxyz như trên."
    assert _chay(g).servable
    monkeypatch.setattr(PC, "bat_bien_toa_do", goc)
    assert not _chay(g).servable


def test_TIEM_7_bo_chan_UNRESOLVED__ca_mau_thuan_duoc_phuc_vu():
    """Mâu thuẫn phải CHẶN. Nếu nó chỉ là `not_checkable` thì một đề tự mâu
    thuẫn vẫn ra một con số, và con số ấy không của hình nào."""
    de = "Cho A(1,2,3). Sau đó lấy A(9,9,9)."
    hd = _hd(de)
    exec_gia = type("R", (), {"final_memory": {"A": Vec3(F(1), F(2), F(3))}})()
    kq = PO.check_source_invariants(hd, exec_gia)
    assert not kq.ok and kq.unresolved and kq.violated == []

    # Tiêm: hạ `unresolved` xuống `not_checkable` ⇒ hết chặn.
    hd_gia = hd.model_copy(update={"source_invariants": ()})
    assert PO.check_source_invariants(hd_gia, exec_gia).ok


# ══ §13 · GIỚI HẠN — khai bằng TEST, không bằng lời hứa bao phủ ════════
@pytest.mark.parametrize("de,vi_sao", [
    ("Cho A(1,5, 2, 3).",
     "thập phân dấu PHẨY — đọc được hai cách, cố ý không đoán"),
    ("Điểm có toạ độ (1, 2, 3) là A.",
     "tên đứng SAU bộ ba"),
    ("Cho điểm A với x_A = 1, y_A = 2, z_A = 3.",
     "toạ độ tách thành ba phương trình"),
    ("Cho A(1, 2).",
     "toạ độ 2D — ngoài miền của hệ 3D"),
    ("Cho A(√2, 0, 0).",
     "toạ độ VÔ TỈ — ngoài `Fraction`"),
    ("Cho A(1, 2, 3) hoặc A(4, 5, 6) tuỳ trường hợp.",
     "⚠️ ĐỌC ĐƯỢC nhưng thành MÂU THUẪN ⇒ CHẶN, xem test_05"),
])
def test_90_GIOI_HAN_cu_phap_chua_doc_duoc(de, vi_sao):
    """Liệt kê thứ bộ phát KHÔNG đọc, thay vì tuyên bố bao phủ mọi cách viết.

    Ô này XANH nghĩa là giới hạn CÒN. Wave sau nới grammar thì nó ĐỎ, và đó là
    tín hiệu đúng — người nới phải cập nhật danh sách này, không được lặng lẽ
    mở rộng phạm vi kết luận.
    """
    doc = PC.doc_toa_do([de])
    # Không đọc ra một RÀNG BUỘC ĐƠN TRỊ nào cho `A`: hoặc không thấy gì, hoặc
    # thấy nhiều giá trị (mâu thuẫn) — cả hai đều KHÔNG phát `KIND`.
    assert "A" not in doc or len(doc["A"]) > 1, (de, vi_sao, doc)


def test_91_GIOI_HAN_khong_bao_gio_thanh_KET_TOI_oan():
    """Giới hạn phải fail-OPEN ở chiều *"không đọc được"* và fail-CLOSED ở
    chiều *"đọc được mà mâu thuẫn"*. Nhầm chiều là chặn oan cả một lớp đề."""
    hd = _hd("Cho A(√2, 0, 0). Tính thể tích.")
    assert _bt_toa_do(hd) == []
    kq = PO.check_source_invariants(hd, _Exec({"A": Vec3(F(9), F(9), F(9))}))
    assert kq.ok and kq.violated == []
