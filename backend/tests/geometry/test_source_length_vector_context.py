# -*- coding: utf-8 -*-
"""ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO — "XY = số" chỉ là ĐỘ DÀI đoạn XY khi XY đứng một mình.

Bộ đọc độ dài nguồn (`segment_relation.do_dai_trong_de`) là MỘT thẩm quyền cho grounding, bất biến nguồn, formation,
nguyên nhân từ chối (`refusal_cause`) và preview. Trước bản sửa nó đọc `GC = 0` trong "GA + GB + GC = 0", `BC = 0` trong
"SA.BC = 0", `CD = 5` trong "AB + CD = 5": một độ dài KHÔNG AI VIẾT, rồi từ chối đề hợp lệ với `refusal_cause = SOURCE`.

Kỳ vọng dưới đây viết tay theo nghĩa toán của câu (không suy từ bộ đọc): vectơ/tổng/hiệu/tích/tỉ số/điều kiện ⇒ không
có độ dài; câu độ dài đứng một mình (kể cả 0 suy biến thật của đề) ⇒ vẫn đọc.
"""
from __future__ import annotations

from fractions import Fraction
from types import SimpleNamespace

import pytest

from app.simulation.geometry.radical import parse_exact
from app.simulation.semantic_program.grounding_gate import _bang_chung_do_dai
from app.simulation.semantic_program.refusal_cause import do_dai_de_ghi_khong_duong
from app.simulation.semantic_program.segment_relation import NHAN_BIEU_THUC, cac_doan_truoc, do_dai_trong_de
from app.simulation.semantic_program.shape_constraint import phan_chua_doc


def _doc(text: str) -> dict[str, Fraction | object]:
    return {"".join(sorted(k)): v for k, v in do_dai_trong_de(text).items()}


# ── KHÔNG phải độ dài đoạn: vectơ, tổng/hiệu, tích (vô hướng/có hướng), tỉ số, điều kiện ─────────────────────────────
KHONG_PHAI_DO_DAI = [
    "Cho tam giác ABC có trọng tâm G thoả GA + GB + GC = 0.",
    "GA+GB+GC=0",
    "GA  +  GB +  GC =0",
    "Gọi M thoả vectơ MA + vectơ MB = 0.",
    "Gọi M thoả véctơ MA + véc tơ MB = 0.",
    "Gọi M thoả MA + MB = 0 (vectơ).",
    "Biết AB + CD = 0 (tổng hai vectơ).",
    "Cho SA.BC = 0.",
    "Cho SA . BC = 0.",
    "Cho SA·BC = 0.",
    "Cho SA × BC = 0.",
    "Cho SA*BC = 0.",
    "Biết AB + CD = 5.",
    "Biết AB − CD = 1.",
    "Biết AB – CD = 1.",
    "Biết AB - CD = 1.",
    "Biết AB/CD = 2.",
    # review của run (I2): các lối viết tích/tỉ số khác.
    "Cho AB ⋅ CD = 0.",
    "Cho AB \\cdot CD = 0.",
    "Cho AB x CD = 0.",
    "Biết tích vô hướng của hai vectơ AB và CD bằng 0.",
    "Biết AB : CD = 2.",
    "Gọi M sao cho vectơ AM = 0.",
    "Cho →GA + →GB + →GC = →0.",
    "Cho GA→ + GB→ + GC→ = 0→.",
    "Cho vectơ MA = 0→.",
    # review lượt 2: hệ số trước toán hạng ("2GA + GB = 0") và hệ số căn nhân nhãn — cùng lớp lỗi của issue.
    "Biết 2GA + GB = 0.",
    "Biết 2MA + 3MB = 0.",
    "Biết √2.AB = 2.",
    "Biết 1 + AB = 5.",
    "Cho S(ABC) × SA = 10.",
    "Cho 2√3GA + GB = 0.",
    "Cho (2;3) + GB = 0.",
    "Cho vectơ AB = (0; 0; 0).",
]


@pytest.mark.parametrize("text", KHONG_PHAI_DO_DAI)
def test_bieu_thuc_vecto_tong_tich_dieu_kien_khong_la_do_dai(text):
    assert _doc(text) == {}


@pytest.mark.parametrize("text", KHONG_PHAI_DO_DAI)
def test_nguyen_nhan_tu_choi_khong_goi_de_sai_vi_bieu_thuc_vecto(text):
    assert do_dai_de_ghi_khong_duong(SimpleNamespace(problem_text=text)) is None


# ── VẪN là độ dài: câu đứng một mình, chuỗi bằng nhau, đầu câu sau dấu chấm, sau dấu hai chấm, căn, suy biến thật ──
LA_DO_DAI = [
    ("Cho tam giác ABC có AB = 3, AC = 4.", {"AB": Fraction(3), "AC": Fraction(4)}),
    ("Cho hình chóp S.ABCD có SA = SB = SC = SD = 2.",
     {"AS": Fraction(2), "BS": Fraction(2), "CS": Fraction(2), "DS": Fraction(2)}),
    ("Cho hình chóp S.ABCD. SA = 3.", {"AS": Fraction(3)}),
    ("Cho hình chóp S.ABCD. Biết: AB = 5.", {"AB": Fraction(5)}),
    ("Cho tam giác ABC có AB bằng 0,5.", {"AB": Fraction(1, 2)}),
    ("Cho tam giác ABC có AB dài 7.", {"AB": Fraction(7)}),
    ("Cho tam giác ABC có AB = 0.", {"AB": Fraction(0)}),
    ("Cho hình chóp S.ABC có SA = 3 và GA + GB + GC = 0.", {"AS": Fraction(3)}),
    ("Cho hình chóp S.ABC có SA = 3, MA + MB = 0 (vectơ).", {"AS": Fraction(3)}),
    # review của run (I1): gạch đầu dòng, đánh số, dấu chấm dính, tên hình ba chữ, "khi đó" — vẫn là độ dài.
    ("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2:\n- SA vuông góc với (ABCD)\n- SA = 3", {"AS": Fraction(3)}),
    ("Cho tứ diện ABCD có:\n- AB = 3\n- AC = 4", {"AB": Fraction(3), "AC": Fraction(4)}),
    ("Cho tam giác ABC vuông tại A - AB = 3, AC = 4", {"AB": Fraction(3), "AC": Fraction(4)}),
    ("Cho hình chóp S.ABCD.SA = 3", {"AS": Fraction(3)}),
    ("Bài 1/ AB = 3", {"AB": Fraction(3)}),
    # "3 ·": `_SAU_DO_DAI` (có từ trước, không đổi ở đây) không cắt số ngay trước `*` ⇒ AB không đọc, như trên `main`;
    # điều được sửa là AC — chấm giữa sau một CON SỐ không phải phép nhân giữa hai đoạn.
    ("AB = 3 · AC = 4", {"AC": Fraction(4)}),
    ("Cho hình chóp S.ABC có SA = 3 khi đó tính thể tích.", {"AS": Fraction(3)}),
    # review lượt 2 (N1): "tích vô hướng" chỉ chiếm ô toán hạng ngay sau nó, không nuốt cả câu.
    ("Tính tích vô hướng của AB và AC, biết AB = 3, AC = 4.", {"AB": Fraction(3), "AC": Fraction(4)}),
    ("Cho hai vectơ có tích vô hướng bằng 0 và SA = 3.", {"AS": Fraction(3)}),
    # (N2): dấu hai chấm giới thiệu, không phải tỉ số.
    ("Cho hình chóp S.ABCD, đường cao SH: SH = 3.", {"HS": Fraction(3)}),
    ("Trung tuyến AM: AM = 4.", {"AM": Fraction(4)}),
    # (N3): ngoặc đóng rồi gạch — gạch nối, không phải phép trừ.
    ("Cho SA ⊥ (ABC) - SA = 3.", {"AS": Fraction(3)}),
    # số đứng sau "=" là giá trị của lời trước, không phải hệ số; "x" của kích thước hộp không làm hỏng lời sau.
    ("Cho x = AB = 3.", {"AB": Fraction(3)}),
    ("Cho hình hộp kích thước 2 x 3 x 4, AB = 2.", {"AB": Fraction(2)}),
]


# ── Giả định "khi/nếu XY = …": vẫn là giá trị đề nêu cho mọi phép ĐỐI CHIẾU (không nới cổng), nhưng không là TIỀN ĐỀ ──
GIA_DINH = [
    ("Nếu độ dài vectơ AB = 0 thì A trùng B.", {"AB": Fraction(0)}),
    ("Ta có MA = 0 khi M trùng A.", {"AM": Fraction(0)}),
    ("MA = 0 nếu M trùng A.", {"AM": Fraction(0)}),
    ("Khi MA = 0 thì M trùng A.", {"AM": Fraction(0)}),
    ("Nếu SA bằng 4 thì thể tích khối chóp là bao nhiêu?", {"AS": Fraction(4)}),
]


@pytest.mark.parametrize(("text", "expected"), GIA_DINH)
def test_gia_dinh_doi_chieu_duoc_nhung_khong_la_tien_de(text, expected):
    assert _doc(text) == expected
    assert do_dai_trong_de(text, ca_gia_dinh=False) == {}
    assert do_dai_de_ghi_khong_duong(SimpleNamespace(problem_text=text)) is None


def test_gia_dinh_khong_noi_cong_grounding():
    """review của run (I3): đề chỉ nêu SA trong giả định "nếu SA = 5"; chương trình khai GIVEN SA = 3 (lấy số 3 của
    "cạnh 3") phải bị bác như trên `main`, không được lọt vì giả định bị bỏ qua."""
    de = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 3. Nếu SA = 5 thì thể tích là bao nhiêu?"
    ma, _bc, _ly_do = _bang_chung_do_dai(de, "SA_length", Fraction(3), None)
    assert ma == "SOURCE_EVIDENCE_CONFLICT"
    assert _bang_chung_do_dai(de, "SA_length", Fraction(5), None)[0] is None


@pytest.mark.parametrize(("text", "expected"), LA_DO_DAI)
def test_do_dai_dung_mot_minh_van_doc(text, expected):
    assert _doc(text) == expected


def test_do_dai_can_van_doc():
    assert _doc("Cho tam giác ABC đều có AB = 2√3.") == {"AB": parse_exact("2√3")}


def test_suy_bien_that_cua_de_van_la_SOURCE():
    r = do_dai_de_ghi_khong_duong(SimpleNamespace(problem_text="Cho tam giác ABC có AB = 0. Tính diện tích."))
    assert r is not None and r["refusal_cause"] == "SOURCE" and r["reason_subjects"] == ["AB"]


def test_tron_vecto_va_suy_bien_that_chi_bao_doan_that():
    r = do_dai_de_ghi_khong_duong(SimpleNamespace(
        problem_text="Cho tam giác ABC có AB = 0 và GA + GB + GC = 0. Tính diện tích."))
    assert r is not None and r["reason_subjects"] == ["AB"]


# ── Nhãn-trước-số (grounding_gate, quantity_annotations) dùng cùng luật ─────────────────────────────────────────────
@pytest.mark.parametrize(("tien_to", "sau_so", "expected"), [
    ("Cho tam giác ABC có AB = ", ".", (("A", "B"),)),
    ("SA = SB = ", "", (("S", "A"), ("S", "B"))),
    ("Cho hình chóp S.ABCD. SA = ", ".", (("S", "A"),)),
    ("Cho GA + GB + GC = ", ".", NHAN_BIEU_THUC),
    ("Cho SA.BC = ", ".", NHAN_BIEU_THUC),
    ("Cho MA + MB = ", " (vectơ).", NHAN_BIEU_THUC),
    ("Cho MA = ", " (vectơ).", NHAN_BIEU_THUC),
    ("Cho MA = ", "→.", NHAN_BIEU_THUC),
    ("Cho vectơ MA = ", ".", NHAN_BIEU_THUC),
    # Giả định: con số vẫn là của đúng đoạn ấy (không thành số trơn).
    ("Ta có MA = ", " khi M trùng A.", (("M", "A"),)),
    ("Cho AB ⋅ CD = ", ".", NHAN_BIEU_THUC),
    ("Cho tứ diện ABCD có:\n- AB = 3\n- AC = ", "", (("A", "C"),)),
])
def test_nhan_truoc_so_cung_luat(tien_to, sau_so, expected):
    """`sau_so` là phần đề NGAY SAU con số (con số không nằm trong hai đối số).

    Con số của một biểu thức KHÔNG được thành "số trơn" (`()`): số trơn làm bằng chứng được cho mọi đoạn."""
    assert cac_doan_truoc(tien_to, sau_so) == expected


# ── Ca thật do phép so parity trên 1889 đề của kho phát hiện (main ↔ bản sửa) ───────────────────────────────────
def test_cham_giua_la_gach_dau_dong_khong_phai_phep_nhan():
    text = ("Cho hình chóp F.GKL —   · đáy GKL là tam giác vuông đỉnh G;   · GK = 7, GL = 3;   · FG ⊥ (GKL), FG = 2. "
            "Tính thể tích khối chóp F.GKL.")
    assert _doc(text) == {"GK": Fraction(7), "GL": Fraction(3), "FG": Fraction(2)}


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 3. "
    "Nếu SA bằng 4 thì thể tích khối chóp là bao nhiêu?",
    "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
    "Tính khoảng cách từ trung điểm của SC đến (SAB). Tính lại khi SA = 5.",
])
def test_gia_dinh_lam_doan_mo_ho_khong_chon_mot_gia_tri(text):
    """Đề cho SA = 3 rồi hỏi "nếu/khi SA = …": không có MỘT độ dài nguồn của SA để đối chiếu."""
    assert "AS" not in _doc(text)


def test_gia_dinh_trung_tien_de_khong_gay_mo_ho():
    text = ("Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
            "Nếu SA = 3 thì tính khoảng cách từ trung điểm của SC đến (SAB).")
    assert _doc(text)["AS"] == Fraction(3)


def test_gia_dinh_mot_minh_khong_la_tien_de():
    """Không là TIỀN ĐỀ (nguyên nhân từ chối), nhưng vẫn là giá trị đề nêu khi đối chiếu (`test_gia_dinh_khong_noi_cong`)."""
    assert do_dai_trong_de("Nếu SA bằng 4 thì thể tích khối chóp là bao nhiêu?", ca_gia_dinh=False) == {}


def test_do_dai_cua_vecto_la_do_dai_doan():
    assert _doc("Cho tam giác ABC có độ dài vectơ AB = 3.") == {"AB": Fraction(3)}


@pytest.mark.parametrize("text", ["V = 1/3 × S(ABC) × SA = 10", "V = S(ABCD) × AA′ = 60",
                                  "Thể tích S.ABCDV = 1/3 × S(ABCD) × SO = 16Dựa trên: S(ABCD), d(S, (ABC))"])
def test_cong_thuc_the_tich_khong_cho_do_dai_doan(text):
    """Số cuối là THỂ TÍCH, không phải độ dài của thừa số đứng trước dấu `=`."""
    assert _doc(text) == {}


# ── Phần dữ kiện: biểu thức vectơ KHÔNG bị coi là "đã đọc" như một câu độ dài ─────────────────────────────────────
def test_phan_chua_doc_khong_nuot_bieu_thuc_vecto():
    """Đối chứng: cùng đề, thêm mệnh đề vectơ ⇒ phần chưa đọc có thêm đúng các ký hiệu của mệnh đề ấy."""
    goc = set(phan_chua_doc("Cho tam giác ABC có AB = 3. Tính diện tích."))
    them = set(phan_chua_doc("Cho tam giác ABC có AB = 3 và GA + GB + GC = 0. Tính diện tích.")) - goc
    assert {"GC", "0"} <= them, them
    assert "AB" not in set(phan_chua_doc("Cho tam giác ABC có AB = 3 và GA + GB + GC = 0. Tính diện tích."))
