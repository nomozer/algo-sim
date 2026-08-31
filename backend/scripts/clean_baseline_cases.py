# -*- coding: utf-8 -*-
"""SÁU ĐỀ cho CLEAN_BASELINE_V1 — kèm LỜI GIẢI IR CHUẨN TẮC. **0 API call.**

─── VÌ SAO KHÔNG DÙNG LẠI BẤT KỲ BỘ ĐỀ NÀO ────────────────────────────────

  · 4 đề nhị diện — năm vòng đo, ba vòng sửa hệ;
  · 10 đề matrix — harness truyền `domain="geometry"`, tức đo bằng prompt TIN
    HỌC (xem `FRESH_PROBE_REPORT §0`);
  · 6 đề fresh-probe — dính hai bug hợp đồng nay đã sửa (`angle_cos_sq` trả
    sin²; bề mặt quảng cáo từ vựng nghĩa vụ);
  · pool Phase 7B — đã niêm phong, không được chạm.

Không bộ nào trả lời được câu *"hợp đồng ĐÃ SỬA sinh ra gì"*.

─── LỜI GIẢI CHUẨN TẮC: ĐỂ LÀM GÌ, VÀ KHÔNG ĐỂ LÀM GÌ ─────────────────────

Mỗi đề kèm một chương trình IR **do người viết**, chạy được, ra đúng oracle.

NÓ KHÔNG BAO GIỜ ĐƯỢC GỬI CHO MÔ HÌNH. Nó cũng KHÔNG được tính là một lượt
thành công. Việc duy nhất của nó là tách hai lời buộc tội khác hẳn nhau khi
một ca hỏng:

    IR biểu diễn được, mô hình không tìm ra   →  EXISTING_IR_SYNTHESIS_FAILURE
    IR không biểu diễn được                   →  lỗi THIẾT KẾ PHÉP ĐO của ta

Matrix từng thiếu đúng phép phân biệt này, nên mọi ca hỏng đọc như "mô hình
kém". Chạy được lời giải chuẩn tắc TRƯỚC khi gọi model là cách biến
`EXISTING_IR_EXPRESSIBLE` từ một lời khẳng định thành một phép đo.

─── ORACLE ────────────────────────────────────────────────────────────────

`dap_so` tính TAY từ hệ trục ghi ở `kiem_tay`, và được đối chiếu độc lập với
kết quả chạy lời giải chuẩn tắc. Hai nguồn khớp nhau thì con số mới đáng tin;
một nguồn thì chỉ là một lần gõ phím.
"""
from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

CAN = "radical"
HUU_TI = "rational"


def q(x) -> tuple[str, Fraction]:
    return (HUU_TI, Fraction(x))


def can(he, c: int) -> tuple[str, tuple[Fraction, int]]:
    return (CAN, (Fraction(he), c))


def _diem(t, xyz, ly_do):
    return {"kind": "declare_point", "target_var": t, "at": xyz,
            "model_assumption": ly_do}


def _spec(title, decls, stmts):
    return {"spec_version": "1.0", "title": title,
            "description": "Lời giải chuẩn tắc do người viết.",
            "pedagogical_intent": "Chứng minh IR hiện có biểu diễn được đề này.",
            "memory_declarations": decls, "statements": stmts}


CASES: list[dict] = [
    # ══ 01 · TỨ DIỆN — 2 điểm phụ, một phép chiếu vuông góc ═══════════════
    {
        "id": "cb_01_tu_dien_chieu_vuong_goc",
        "topology": "tứ diện vuông tại một đỉnh",
        "capability_mix": ["midpoint", "construct_plane", "project_onto",
                           "construct_line", "distance"],
        "expected_depth": 4,
        "obligation_count": 1,
        "de": (
            "Cho tứ diện ABCD có AB, AC, AD đôi một vuông góc và "
            "AB = AC = AD = 2. Gọi M là trung điểm của BC và H là hình chiếu "
            "vuông góc của A lên mặt phẳng (BCD). Tính khoảng cách từ H đến "
            "đường thẳng AM."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(0,2,0) D(0,0,2). M = (1,1,0). "
            "(BCD): x+y+z = 2, pháp tuyến (1,1,1) ⇒ H = (2/3,2/3,2/3). "
            "AM có chỉ phương (1,1,0); AH = (2/3,2/3,2/3). "
            "AH×(1,1,0) = (-2/3, 2/3, 0) ⇒ |·|² = 8/9. "
            "d² = (8/9)/2 = 4/9 ⇒ d = 2/3."
        ),
        "dap_so": q(Fraction(2, 3)),
        "chuan_tac": _spec(
            "Khoảng cách từ H đến AM",
            [{"name": "M", "type": "point3"}, {"name": "H", "type": "point3"},
             {"name": "BCD", "type": "plane3"}, {"name": "AM", "type": "line3"},
             {"name": "d", "type": "float"}],
            [_diem("A", [0, 0, 0], "gốc, ba cạnh đôi một vuông góc"),
             _diem("B", [2, 0, 0], "trục x"),
             _diem("C", [0, 2, 0], "trục y"),
             _diem("D", [0, 0, 2], "trục z"),
             {"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "B", "b": "C"}},
             {"kind": "construct_plane", "target_var": "BCD",
              "through": ["B", "C", "D"]},
             {"kind": "construct_point", "target_var": "H",
              "expr": {"kind": "project_onto", "point": "A", "target": "BCD"}},
             {"kind": "construct_line", "target_var": "AM",
              "through_a": "A", "through_b": "M"},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "H", "wrt": "AM"}}]),
    },
    # ══ 02 · LĂNG TRỤ — mặt dẫn xuất, đo không từ cạnh gốc ════════════════
    {
        "id": "cb_02_lang_tru_mat_dan_xuat",
        "topology": "lăng trụ đứng đáy tam giác vuông cân",
        "capability_mix": ["midpoint", "construct_plane", "distance"],
        "expected_depth": 3,
        "obligation_count": 1,
        "de": (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông cân tại A với "
            "AB = AC = 2 và cạnh bên AA' = 4. Gọi M là trung điểm của cạnh "
            "B'C'. Tính khoảng cách từ M đến mặt phẳng (A'BC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(0,2,0) A'(0,0,4) B'(2,0,4) C'(0,2,4). "
            "M = (1,1,4). (A'BC): A'B=(2,0,-4), A'C=(0,2,-4) ⇒ pháp tuyến "
            "(8,8,4) ∼ (2,2,1), mặt 2x+2y+z = 4. "
            "d = |2+2+4-4|/3 = 4/3."
        ),
        "dap_so": q(Fraction(4, 3)),
        "chuan_tac": _spec(
            "Khoảng cách từ M đến (A'BC)",
            [{"name": "M", "type": "point3"},
             {"name": "P", "type": "plane3"}, {"name": "d", "type": "float"}],
            [_diem("A", [0, 0, 0], "gốc tại đỉnh vuông của đáy"),
             _diem("B", [2, 0, 0], "trục x"),
             _diem("C", [0, 2, 0], "trục y"),
             _diem("A_prime", [0, 0, 4], "cạnh bên dọc trục z"),
             _diem("B_prime", [2, 0, 4], "tịnh tiến B theo cạnh bên"),
             _diem("C_prime", [0, 2, 4], "tịnh tiến C theo cạnh bên"),
             {"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "B_prime", "b": "C_prime"}},
             {"kind": "construct_plane", "target_var": "P",
              "through": ["A_prime", "B", "C"]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "M", "wrt": "P"}}]),
    },
    # ══ 03 · HỘP CHỮ NHẬT — đường chéo, kết quả căn thức ══════════════════
    {
        "id": "cb_03_hop_duong_cheo_can",
        "topology": "hình hộp chữ nhật",
        "capability_mix": ["midpoint", "construct_line", "distance",
                           "radical"],
        "expected_depth": 4,
        "obligation_count": 1,
        "de": (
            "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 2 và "
            "AA' = 1. Gọi M là trung điểm của đường chéo AC' và N là trung "
            "điểm của cạnh AB. Tính khoảng cách từ M đến đường thẳng DN."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) C'(2,2,1). "
            "M = (1,1,1/2); N = (1,0,0). DN có chỉ phương (1,-2,0). "
            "DM = (1,-1,1/2); DM×(1,-2,0) = (1, 1/2, -1) ⇒ |·|² = 9/4. "
            "d² = (9/4)/5 = 9/20 ⇒ d = 3/(2√5) = 3√5/10."
        ),
        "dap_so": can(Fraction(3, 10), 5),
        "chuan_tac": _spec(
            "Khoảng cách từ M đến DN",
            [{"name": "M", "type": "point3"}, {"name": "N", "type": "point3"},
             {"name": "DN", "type": "line3"}, {"name": "d", "type": "float"}],
            [_diem("A", [0, 0, 0], "gốc"),
             _diem("B", [2, 0, 0], "cạnh AB dọc trục x"),
             _diem("D", [0, 2, 0], "cạnh AD dọc trục y"),
             _diem("C_prime", [2, 2, 1], "đỉnh đối của A qua tâm hộp"),
             {"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "A", "b": "C_prime"}},
             {"kind": "construct_point", "target_var": "N",
              "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
             {"kind": "construct_line", "target_var": "DN",
              "through_a": "D", "through_b": "N"},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "M", "wrt": "DN"}}]),
    },
    # ══ 04 · CHÓP — thiết diện, rồi ĐO trên chính mặt cắt ấy ══════════════
    {
        "id": "cb_04_chop_thiet_dien_noi_tiep",
        "topology": "chóp tứ giác đáy vuông",
        "capability_mix": ["midpoint", "construct_solid", "construct_plane",
                           "construct_section", "distance"],
        "expected_depth": 6,
        "obligation_count": 2,
        # ⚠️ Mặt cắt KHÔNG được đi qua đỉnh nào của khối. Bản đầu của ca này
        # cắt bằng `(MBC)` với M là trung điểm SA — mặt ấy chứa NGUYÊN cạnh
        # BC, và `section.py` ném `MALFORMED_SOLID` vì chuỗi đỉnh không nối
        # kín được. Đó là giới hạn thật của thuật toán, ghi ở báo cáo; ở đây
        # đổi hình cắt để ca đo được thứ nó định đo (§5).
        # Đáy CHỮ NHẬT với số liệu khác hẳn: guard nhiễm chéo báo bản trước
        # dùng cùng cấu hình *"chóp đáy vuông cạnh 2, SA = 2"* với `fp_4` của
        # probe cũ. Đổi số mà giữ hình là đúng thứ §3 cấm.
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 4, "
            "AD = 2, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 4. Gọi "
            "M, N, P, Q lần lượt là trung điểm của các cạnh SA, SB, SC, SD. "
            "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (MNP) và "
            "tính thể tích khối chóp S.MNPQ."
        ),
        "kiem_tay": (
            "A(0,0,0) B(4,0,0) C(4,2,0) D(0,2,0) S(0,0,4). "
            "M(0,0,2) N(2,0,2) P(2,1,2) Q(0,1,2) — cả bốn ở z = 2, nên "
            "(MNP) là mặt z = 2 và thiết diện là hình chữ nhật MNPQ có kích "
            "thước 2×1, diện tích 2. Chiều cao từ S xuống mặt ấy bằng 2. "
            "V(S.MNPQ) = (1/3)·2·2 = 4/3."
        ),
        "dap_so": q(Fraction(4, 3)),
        "chuan_tac": _spec(
            "Thiết diện (MNP) và thể tích S.MNPQ",
            [{"name": "M", "type": "point3"}, {"name": "N", "type": "point3"},
             {"name": "P", "type": "point3"}, {"name": "Q", "type": "point3"},
             {"name": "K", "type": "solid"}, {"name": "mp", "type": "plane3"},
             {"name": "TD", "type": "section"},
             {"name": "K2", "type": "solid"}, {"name": "V", "type": "float"}],
            [_diem("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _diem("B", [4, 0, 0], "cạnh AB dọc trục x"),
             _diem("C", [4, 2, 0], "đỉnh đối của A trên đáy chữ nhật"),
             _diem("D", [0, 2, 0], "cạnh AD dọc trục y"),
             _diem("S", [0, 0, 4], "đỉnh chóp trên trục z"),
             {"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "S", "b": "A"}},
             {"kind": "construct_point", "target_var": "N",
              "expr": {"kind": "midpoint", "a": "S", "b": "B"}},
             {"kind": "construct_point", "target_var": "P",
              "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
             {"kind": "construct_point", "target_var": "Q",
              "expr": {"kind": "midpoint", "a": "S", "b": "D"}},
             {"kind": "construct_solid", "target_var": "K",
              "vertices": ["A", "B", "C", "D", "S"],
              "faces": [["A", "B", "C", "D"], ["S", "A", "B"],
                        ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"]]},
             {"kind": "construct_plane", "target_var": "mp",
              "through": ["M", "N", "P"]},
             {"kind": "construct_section", "target_var": "TD",
              "solid": "K", "plane": "mp"},
             {"kind": "construct_solid", "target_var": "K2",
              "vertices": ["M", "N", "P", "Q", "S"],
              "faces": [["M", "N", "P", "Q"], ["S", "M", "N"],
                        ["S", "N", "P"], ["S", "P", "Q"], ["S", "Q", "M"]]},
             {"kind": "assign", "target_var": "V",
              "expr": {"kind": "measure", "quantity": "volume", "of": "K2"}}]),
    },
    # ══ 05 · GÓC ĐƯỜNG–MẶT — ca phân biệt cos² với sin² ══════════════════
    {
        "id": "cb_05_goc_duong_mat_phan_biet",
        "topology": "chóp tam giác vuông tại B",
        "capability_mix": ["midpoint", "construct_line", "construct_plane",
                           "angle_cos_sq"],
        "expected_depth": 4,
        "obligation_count": 1,
        # Góc KHÔNG phải 45°, nên cos² ≠ sin² — ca này phân biệt được hai đại
        # lượng. Một đề 45° sẽ xanh dưới cả hai ngữ nghĩa và không nói gì.
        "de": (
            "Cho hình chóp S.ABC có đáy ABC vuông tại B với AB = 2, BC = 2, "
            "cạnh bên SA vuông góc với mặt phẳng đáy và SA = 2. Gọi M là "
            "trung điểm của AC. Tính bình phương côsin của góc giữa đường "
            "thẳng SM và mặt phẳng (ABC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) S(0,0,2). M = (1,1,0). "
            "SM có chỉ phương (1,1,-2); (ABC) là z = 0, pháp tuyến (0,0,1). "
            "sin²θ = 4/6 = 2/3 ⇒ cos²θ = 1/3. "
            "⚠️ Runtime TRƯỚC 2026-09-01 trả 2/3 — đúng ca phân biệt."
        ),
        "dap_so": q(Fraction(1, 3)),
        "chuan_tac": _spec(
            "Góc giữa SM và mặt đáy",
            [{"name": "M", "type": "point3"}, {"name": "SM", "type": "line3"},
             {"name": "ABC", "type": "plane3"},
             {"name": "c2", "type": "float"}],
            [_diem("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _diem("B", [2, 0, 0], "trục x, tam giác vuông tại B"),
             _diem("C", [2, 2, 0], "BC vuông góc AB"),
             _diem("S", [0, 0, 2], "đỉnh trên trục z"),
             {"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "A", "b": "C"}},
             {"kind": "construct_line", "target_var": "SM",
              "through_a": "S", "through_b": "M"},
             {"kind": "construct_plane", "target_var": "ABC",
              "through": ["A", "B", "C"]},
             {"kind": "assign", "target_var": "c2",
              "expr": {"kind": "measure", "quantity": "angle_cos_sq",
                       "of": "SM", "wrt": "ABC"}}]),
    },
    # ══ 06 · NHIỀU NGHĨA VỤ — giao điểm dùng thật, độ sâu cao ═════════════
    {
        "id": "cb_06_giao_diem_va_the_tich",
        "topology": "chóp tứ giác đáy vuông",
        "capability_mix": ["construct_line", "intersect_line_line",
                           "construct_plane", "construct_solid", "distance",
                           "volume"],
        "expected_depth": 5,
        "obligation_count": 2,
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và SA "
            "vuông góc với mặt phẳng đáy, SA = 2. Gọi I là giao điểm của hai "
            "đường chéo AC và BD của đáy. Tính khoảng cách từ I đến mặt "
            "phẳng (SBC) và tính thể tích khối chóp S.ABCD."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2). I = (1,1,0). "
            "(SBC): SB=(2,0,-2), SC=(2,2,-2) ⇒ pháp tuyến (4,0,4) ∼ (1,0,1), "
            "mặt x+z = 2. d(I) = |1+0-2|/√2 = 1/√2 = √2/2. "
            "V = (1/3)·4·2 = 8/3."
        ),
        "dap_so": can(Fraction(1, 2), 2),
        "dap_so_phu": q(Fraction(8, 3)),
        "chuan_tac": _spec(
            "Khoảng cách từ I đến (SBC) và thể tích chóp",
            [{"name": "AC", "type": "line3"}, {"name": "BD", "type": "line3"},
             {"name": "I", "type": "point3"}, {"name": "SBC", "type": "plane3"},
             {"name": "K", "type": "solid"}, {"name": "d", "type": "float"},
             {"name": "V", "type": "float"}],
            [_diem("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _diem("B", [2, 0, 0], "trục x"),
             _diem("C", [2, 2, 0], "đỉnh đối của A trên đáy vuông"),
             _diem("D", [0, 2, 0], "trục y"),
             _diem("S", [0, 0, 2], "đỉnh chóp trên trục z"),
             {"kind": "construct_line", "target_var": "AC",
              "through_a": "A", "through_b": "C"},
             {"kind": "construct_line", "target_var": "BD",
              "through_a": "B", "through_b": "D"},
             {"kind": "construct_point", "target_var": "I",
              "expr": {"kind": "intersect_line_line",
                       "line_a": "AC", "line_b": "BD"}},
             {"kind": "construct_plane", "target_var": "SBC",
              "through": ["S", "B", "C"]},
             {"kind": "construct_solid", "target_var": "K",
              "vertices": ["A", "B", "C", "D", "S"],
              "faces": [["A", "B", "C", "D"], ["S", "A", "B"],
                        ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"]]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "I", "wrt": "SBC"}},
             {"kind": "assign", "target_var": "V",
              "expr": {"kind": "measure", "quantity": "volume", "of": "K"}}]),
    },
]


# ── NHIỄM CHÉO ─────────────────────────────────────────────────────────────
GOC = Path(__file__).resolve().parents[2]
_NGUON_CU = (
    GOC / "docs" / "evaluation" / "geometry" / "holdout",
    GOC / "docs" / "evaluation" / "geometry" / "fresh-probe",
    GOC / "docs" / "evaluation" / "geometry" / "generalization-matrix",
)
_HOI = re.compile(r"\b(tính|chứng minh|xác định|tìm)\b", re.IGNORECASE)


def _van(s: str) -> str:
    return re.sub(r"[^\wàáâãèéêìíòóôõùúýăđĩũơưạ-ỹ]+", " ", s.lower()).strip()


def _ngu(s: str, n: int) -> set[str]:
    t = _van(s).split()
    return {" ".join(t[i:i + n]) for i in range(max(len(t) - n + 1, 0))}


def _cau_hoi(de: str) -> str:
    m = _HOI.search(de)
    return de[m.start():] if m else de


#: Khoá mà các artifact đời trước dùng để lưu ĐỀ BÀI. Khuôn không đồng nhất
#: giữa các wave, và đọc sót một khoá là bỏ lọt cả một bộ đề.
_KHOA_DE = ("problem_text", "problem", "de", "problem_text_original")

#: Từ chỉ KHỐI. Hai bài cùng khối, cùng bộ số, cùng câu hỏi là một bài.
_KHOI = ("tứ diện", "lăng trụ", "lập phương", "hộp chữ nhật", "chóp",
         "hình thoi", "hình vuông", "tam giác")


def _de_cu() -> list[str]:
    """Mọi ĐỀ BÀI đã dùng, đọc theo CẤU TRÚC chứ không theo văn bản thô.

    Quét n-gram trên JSON thô là cách bản đầu làm, và nó báo 4/6 nhiễm với
    100% cụm trùng là văn mẫu SGK — *"Cho hình chóp S.ABCD có đáy ABCD là
    hình vuông cạnh 2 và SA vuông góc với mặt phẳng đáy"* dài hơn 20 từ và
    xuất hiện gần nguyên văn trong mọi sách. Một guard báo động ở đó thì hoặc
    ta hạ ngưỡng — mất khả năng bắt trùng thật — hoặc ta viết đề bằng tiếng
    Việt lạ để né nó, tức làm hỏng chính bộ đề.
    """
    ra: list[str] = []

    def di(x, sau=0):
        if sau > 8:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if k in _KHOA_DE and isinstance(v, str) and len(v) > 40:
                    ra.append(v)
                else:
                    di(v, sau + 1)
        elif isinstance(x, list):
            for v in x:
                di(v, sau + 1)

    import json as _json

    for d in _NGUON_CU:
        for f in d.glob("*.json"):
            try:
                di(_json.loads(f.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        for f in d.glob("*.txt"):
            try:
                for dong in f.read_text(encoding="utf-8").splitlines():
                    if len(dong) > 40 and _HOI.search(dong):
                        ra.append(dong)
            except OSError:
                continue
    return ra


def _chu_ky(de: str) -> tuple:
    """CHỮ KÝ CẤU HÌNH — thứ phân biệt hai bài, bỏ qua công thức mở đầu.

    Ba thành phần: khối nào · bộ số theo thứ tự · mệnh đề hỏi đã chuẩn hoá.
    Hai bài trùng cả ba là một bài, dù câu dẫn viết khác; hai bài chỉ trùng
    câu dẫn thì không trùng gì cả.
    """
    v = _van(de)
    khoi = tuple(k for k in _KHOI if k in v)
    so = tuple(re.findall(r"\d+(?:/\d+)?", v))
    return (khoi, so, _van(_cau_hoi(de)))


def check_contamination() -> list[str]:
    """Trùng với BẤT KỲ bộ đề nào đã dùng? Rỗng = sạch."""
    cu = [( _chu_ky(d), d) for d in _de_cu()]
    ra = []
    for c in CASES:
        ck = _chu_ky(c["de"])
        for ck_cu, van in cu:
            if ck == ck_cu:
                ra.append(f"{c['id']}: TRÙNG ĐỀ — {van[:80]}")
                break
            # Cùng khối + cùng bộ số nhưng câu hỏi khác ⇒ CẢNH BÁO, không
            # phải trùng: đổi câu hỏi trên cùng một hình là một bài khác.
            if ck[:2] == ck_cu[:2] and ck[2] != ck_cu[2]:
                cn = _ngu(ck[2], 8) & _ngu(ck_cu[2], 8)
                if cn and c["id"] not in DA_PHAN_XU:
                    ra.append(f"{c['id']}: cùng hình VÀ trùng câu hỏi — "
                              f"{sorted(cn)[0][:60]}")
                    break
    return ra


#: Ca guard báo mà người ĐỌC ĐỀ CŨ rồi phán là không trùng, kèm lý do đối
#: chiếu cụ thể. Trống nghĩa là chưa ca nào cần miễn — mỗi mục thêm vào đây
#: là một lần ta tự cấp phép, nên nó phải có lý do viết ra.
DA_PHAN_XU: dict[str, str] = {}
