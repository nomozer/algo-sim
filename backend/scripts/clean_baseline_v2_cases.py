# -*- coding: utf-8 -*-
"""SÁU ĐỀ cho CLEAN_BASELINE_V2 — kèm LỜI GIẢI IR CHUẨN TẮC. **0 API call.**

─── VÌ SAO KHÔNG DÙNG LẠI BỘ V1 ───────────────────────────────────────────

Bộ V1 đã dẫn tới bản sửa `IR_FIRST_BINDING_CONTRACT`: chính nó phơi ra
`assign M = midpoint(...)` chết ở runtime, và chính nó dùng để replay khi kiểm
bản sửa. Đo lại một bản sửa trên tập đã dẫn tới nó là đo trí nhớ của ta.

─── V2 KHÓ HƠN V1, CÓ CHỦ ĐÍCH ────────────────────────────────────────────

V1 nghiêng về *"một hình + một phép đo"*. V2 đòi chuỗi phụ thuộc sâu hơn: mỗi
đề ít nhất **hai** vật dẫn xuất, ít nhất một phép giao hoặc phép chiếu, và
phép đo cuối phụ thuộc cả chuỗi trước nó.

Đây là lần đầu mô hình thấy `construct_point` trong thẻ văn phạm — trước
2026-09-01 thẻ dẫn từ `_TOAN_HANG_LENH` và **giấu mất** câu lệnh ấy.

─── TRÁNH HAI GIỚI HẠN ĐÃ BIẾT, CÓ CHỦ ĐÍCH ───────────────────────────────

① Mặt cắt KHÔNG đi qua đỉnh nào của khối (`SECTION_VERTEX_INTERSECTION_GAP`
   còn OPEN). Wave này đo tổng hợp, không đo khoảng trống ấy.
② Không đề nào buộc phải ràng buộc lần đầu một vật hình học BÊN TRONG nhánh
   rồi dùng sau nhánh (`CONTROL_FLOW_DEFINITE_ASSIGNMENT` còn PARTIAL). Biến
   một giới hạn đã khai thành bài kiểm tổng hợp là đo nhầm thứ.

⚠️ `chuan_tac` là ORACLE của bộ đo. Nó KHÔNG BAO GIỜ vào prompt, và KHÔNG được
tính là một lượt thành công. Việc duy nhất của nó: khi một ca hỏng, tách
*"IR biểu diễn được mà mô hình không tìm ra"* khỏi *"IR không biểu diễn được"*.
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


def _d(t, xyz, ly_do):
    return {"kind": "declare_point", "target_var": t, "at": xyz,
            "model_assumption": ly_do}


def _cp(t, expr):
    return {"kind": "construct_point", "target_var": t, "expr": expr}


def _spec(title, decls, stmts):
    return {"spec_version": "1.0", "title": title,
            "description": "Lời giải chuẩn tắc do người viết.",
            "pedagogical_intent": "Chứng minh IR hiện có biểu diễn được đề này.",
            "memory_declarations": decls, "statements": stmts}


CASES: list[dict] = [
    # ══ 01 · TỨ DIỆN — hai trung điểm, một giao điểm, độ sâu 5 ════════════
    {
        "id": "v2_01_tu_dien_giao_trung_tuyen",
        "topology": "tứ diện vuông tại một đỉnh",
        "capability_mix": ["midpoint", "construct_line",
                           "intersect_line_line", "construct_plane",
                           "distance"],
        "derived_entity_count": 6,
        "expected_dependency_depth": 5,
        "obligation_count": 1,
        "de": (
            "Cho tứ diện ABCD có AB, AC, AD đôi một vuông góc và "
            "AB = AC = AD = 4. Gọi M là trung điểm của cạnh BC, N là trung "
            "điểm của cạnh BD, và I là giao điểm của hai đường thẳng CN và "
            "DM. Tính khoảng cách từ I đến mặt phẳng (ABC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(4,0,0) C(0,4,0) D(0,0,4). M = (2,2,0); N = (2,0,2). "
            "CN và DM là hai trung tuyến của tam giác BCD ⇒ cắt nhau tại "
            "trọng tâm I = (B+C+D)/3 = (4/3,4/3,4/3). "
            "(ABC) là z = 0 ⇒ d = 4/3."
        ),
        "dap_so": q(Fraction(4, 3)),
        "chuan_tac": _spec(
            "Khoảng cách từ trọng tâm đến mặt đáy",
            [{"name": "CN", "type": "line3"}, {"name": "DM", "type": "line3"},
             {"name": "ABC", "type": "plane3"}, {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc, ba cạnh đôi một vuông góc"),
             _d("B", [4, 0, 0], "trục x"),
             _d("C", [0, 4, 0], "trục y"),
             _d("D", [0, 0, 4], "trục z"),
             _cp("M", {"kind": "midpoint", "a": "B", "b": "C"}),
             _cp("N", {"kind": "midpoint", "a": "B", "b": "D"}),
             {"kind": "construct_line", "target_var": "CN",
              "through_a": "C", "through_b": "N"},
             {"kind": "construct_line", "target_var": "DM",
              "through_a": "D", "through_b": "M"},
             _cp("I", {"kind": "intersect_line_line",
                       "line_a": "CN", "line_b": "DM"}),
             {"kind": "construct_plane", "target_var": "ABC",
              "through": ["A", "B", "C"]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "I", "wrt": "ABC"}}]),
    },
    # ══ 02 · LĂNG TRỤ — mặt phụ, phép chiếu, đáp số không đọc từ cạnh ═════
    {
        "id": "v2_02_lang_tru_chieu_len_mat_xien",
        "topology": "lăng trụ đứng đáy tam giác vuông",
        "capability_mix": ["construct_plane", "project_onto", "distance"],
        "derived_entity_count": 3,
        "expected_dependency_depth": 4,
        "obligation_count": 1,
        "de": (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại A với AB = 3, "
            "AC = 4 và cạnh bên AA' = 4. Gọi H là hình chiếu vuông góc của "
            "đỉnh A lên mặt phẳng (A'BC). Tính khoảng cách từ H đến mặt "
            "phẳng đáy (ABC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(3,0,0) C(0,4,0) A'(0,0,4). "
            "(A'BC): A'B=(3,0,-4), A'C=(0,4,-4) ⇒ pháp tuyến (16,12,12) ∼ "
            "(4,3,3), mặt 4x+3y+3z = 12. "
            "H = t(4,3,3) với 34t = 12 ⇒ t = 6/17, H = (24/17,18/17,18/17). "
            "(ABC) là z = 0 ⇒ d = 18/17."
        ),
        "dap_so": q(Fraction(18, 17)),
        "chuan_tac": _spec(
            "Khoảng cách từ chân đường vuông góc đến đáy",
            [{"name": "P", "type": "plane3"},
             {"name": "ABC", "type": "plane3"}, {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc tại đỉnh vuông của đáy"),
             _d("B", [3, 0, 0], "trục x"),
             _d("C", [0, 4, 0], "trục y"),
             _d("A_prime", [0, 0, 4], "cạnh bên dọc trục z"),
             {"kind": "construct_plane", "target_var": "P",
              "through": ["A_prime", "B", "C"]},
             _cp("H", {"kind": "project_onto", "point": "A", "target": "P"}),
             {"kind": "construct_plane", "target_var": "ABC",
              "through": ["A", "B", "C"]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "H", "wrt": "ABC"}}]),
    },
    # ══ 03 · LẬP PHƯƠNG — đường chéo không gian, kết quả căn thức ═════════
    {
        "id": "v2_03_lap_phuong_cheo_khong_gian",
        "topology": "hình lập phương",
        "capability_mix": ["midpoint", "construct_line", "distance",
                           "radical"],
        "derived_entity_count": 3,
        "expected_dependency_depth": 4,
        "obligation_count": 1,
        "de": (
            "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Gọi M là "
            "trung điểm của cạnh CC' và I là trung điểm của đường chéo không "
            "gian AC'. Tính khoảng cách từ I đến đường thẳng BM."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,2,0) C'(2,2,2). M = (2,2,1); I = (1,1,1). "
            "BM có chỉ phương (0,2,1); BI = (-1,1,1). "
            "BI×(0,2,1) = (-1,1,-2) ⇒ |·|² = 6, |chỉ phương|² = 5. "
            "d² = 6/5 ⇒ d = √30/5."
        ),
        "dap_so": can(Fraction(1, 5), 30),
        "chuan_tac": _spec(
            "Khoảng cách từ tâm lập phương đến BM",
            [{"name": "BM", "type": "line3"}, {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc"),
             _d("B", [2, 0, 0], "trục x"),
             _d("C", [2, 2, 0], "đỉnh kề trên đáy"),
             _d("C_prime", [2, 2, 2], "đỉnh đối của A qua tâm lập phương"),
             _cp("M", {"kind": "midpoint", "a": "C", "b": "C_prime"}),
             _cp("I", {"kind": "midpoint", "a": "A", "b": "C_prime"}),
             {"kind": "construct_line", "target_var": "BM",
              "through_a": "B", "through_b": "M"},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "I", "wrt": "BM"}}]),
    },
    # ══ 04 · THIẾT DIỆN + BƯỚC TIẾP — mặt cắt KHÔNG qua đỉnh nào ══════════
    {
        "id": "v2_04_thiet_dien_goc_va_the_tich",
        "topology": "chóp tứ giác đáy vuông",
        "capability_mix": ["midpoint", "construct_solid", "construct_plane",
                           "construct_section", "volume"],
        "derived_entity_count": 6,
        "expected_dependency_depth": 5,
        "obligation_count": 2,
        # Mặt x+y+z = 2 không chứa đỉnh nào (A:0 B:4 C:8 D:4 S:4) — tránh
        # `SECTION_VERTEX_INTERSECTION_GAP` còn OPEN.
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4 và SA "
            "vuông góc với mặt phẳng đáy, SA = 4. Gọi M, N, P lần lượt là "
            "trung điểm của các cạnh AB, AD và SA. Xác định thiết diện của "
            "hình chóp cắt bởi mặt phẳng (MNP) và tính thể tích khối tứ diện "
            "AMNP."
        ),
        "kiem_tay": (
            "A(0,0,0) B(4,0,0) C(4,4,0) D(0,4,0) S(0,0,4). "
            "M(2,0,0) N(0,2,0) P(0,0,2) ⇒ (MNP) là mặt x+y+z = 2, không "
            "chứa đỉnh nào. Thiết diện là tam giác MNP. "
            "V(AMNP) = (1/6)|det[(2,0,0),(0,2,0),(0,0,2)]| = 8/6 = 4/3."
        ),
        "dap_so": q(Fraction(4, 3)),
        "chuan_tac": _spec(
            "Thiết diện (MNP) và thể tích AMNP",
            [{"name": "K", "type": "solid"}, {"name": "mp", "type": "plane3"},
             {"name": "TD", "type": "section"},
             {"name": "K2", "type": "solid"}, {"name": "V", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _d("B", [4, 0, 0], "trục x"),
             _d("C", [4, 4, 0], "đỉnh đối của A trên đáy vuông"),
             _d("D", [0, 4, 0], "trục y"),
             _d("S", [0, 0, 4], "đỉnh chóp trên trục z"),
             _cp("M", {"kind": "midpoint", "a": "A", "b": "B"}),
             _cp("N", {"kind": "midpoint", "a": "A", "b": "D"}),
             _cp("P", {"kind": "midpoint", "a": "S", "b": "A"}),
             {"kind": "construct_solid", "target_var": "K",
              "vertices": ["A", "B", "C", "D", "S"],
              "faces": [["A", "B", "C", "D"], ["S", "A", "B"],
                        ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"]]},
             {"kind": "construct_plane", "target_var": "mp",
              "through": ["M", "N", "P"]},
             {"kind": "construct_section", "target_var": "TD",
              "solid": "K", "plane": "mp"},
             {"kind": "construct_solid", "target_var": "K2",
              "vertices": ["A", "M", "N", "P"],
              "faces": [["A", "M", "N"], ["A", "N", "P"], ["A", "P", "M"],
                        ["M", "N", "P"]]},
             {"kind": "assign", "target_var": "V",
              "expr": {"kind": "measure", "quantity": "volume", "of": "K2"}}]),
    },
    # ══ 05 · TỔ HỢP — góc giữa hai đường, phải tự dựng cả hai ═════════════
    {
        "id": "v2_05_goc_hai_duong_cheo_nhau",
        "topology": "chóp tứ giác đáy chữ nhật",
        "capability_mix": ["midpoint", "construct_line", "angle_cos_sq"],
        "derived_entity_count": 3,
        "expected_dependency_depth": 4,
        "obligation_count": 1,
        # Đáy CHỮ NHẬT để phá đối xứng: đáy vuông cho cos² = 0, một đáp số
        # suy biến không phân biệt được chương trình đúng với chương trình may.
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2, "
            "AD = 4, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 2. Gọi "
            "M là trung điểm của cạnh SD. Tính bình phương côsin của góc "
            "giữa hai đường thẳng AM và SC."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(2,4,0) D(0,4,0) S(0,0,2). M = (0,2,1). "
            "AM có chỉ phương (0,2,1); SC có chỉ phương (2,4,-2) ∼ (1,2,-1). "
            "tích vô hướng = 0+4-1 = 3; |AM|² = 5, |SC|² = 6. "
            "cos² = 9/30 = 3/10."
        ),
        "dap_so": q(Fraction(3, 10)),
        "chuan_tac": _spec(
            "Góc giữa AM và SC",
            [{"name": "AM", "type": "line3"}, {"name": "SC", "type": "line3"},
             {"name": "c2", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _d("B", [2, 0, 0], "cạnh AB dọc trục x"),
             _d("C", [2, 4, 0], "đỉnh đối của A trên đáy chữ nhật"),
             _d("D", [0, 4, 0], "cạnh AD dọc trục y"),
             _d("S", [0, 0, 2], "đỉnh chóp trên trục z"),
             _cp("M", {"kind": "midpoint", "a": "S", "b": "D"}),
             {"kind": "construct_line", "target_var": "AM",
              "through_a": "A", "through_b": "M"},
             {"kind": "construct_line", "target_var": "SC",
              "through_a": "S", "through_b": "C"},
             {"kind": "assign", "target_var": "c2",
              "expr": {"kind": "measure", "quantity": "angle_cos_sq",
                       "of": "AM", "wrt": "SC"}}]),
    },
    # ══ 06 · NHIỀU NGHĨA VỤ — giao điểm rồi chiếu, chuỗi sâu ══════════════
    {
        "id": "v2_06_giao_roi_chieu_hai_nghia_vu",
        "topology": "chóp tứ giác đáy vuông",
        "capability_mix": ["construct_line", "intersect_line_line",
                           "construct_plane", "project_onto",
                           "construct_solid", "distance", "volume"],
        "derived_entity_count": 7,
        "expected_dependency_depth": 6,
        "obligation_count": 2,
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4 và SA "
            "vuông góc với mặt phẳng đáy, SA = 4. Gọi I là giao điểm của hai "
            "đường chéo AC và BD của đáy, và H là hình chiếu vuông góc của I "
            "lên mặt phẳng (SBC). Tính khoảng cách từ H đến đỉnh S và tính "
            "thể tích khối chóp S.ABCD."
        ),
        "kiem_tay": (
            "A(0,0,0) B(4,0,0) C(4,4,0) D(0,4,0) S(0,0,4). I = (2,2,0). "
            "(SBC): SB=(4,0,-4), SC=(4,4,-4) ⇒ pháp tuyến (16,0,16) ∼ "
            "(1,0,1), mặt x+z = 4. "
            "H = I + t(1,0,1) với t = (4-2)/2 = 1 ⇒ H = (3,2,1). "
            "HS² = 9+4+9 = 22 ⇒ HS = √22. "
            "V = (1/3)·16·4 = 64/3."
        ),
        "dap_so": can(1, 22),
        "dap_so_phu": q(Fraction(64, 3)),
        "chuan_tac": _spec(
            "Khoảng cách HS và thể tích chóp",
            [{"name": "AC", "type": "line3"}, {"name": "BD", "type": "line3"},
             {"name": "SBC", "type": "plane3"}, {"name": "K", "type": "solid"},
             {"name": "d", "type": "float"}, {"name": "V", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _d("B", [4, 0, 0], "trục x"),
             _d("C", [4, 4, 0], "đỉnh đối của A trên đáy vuông"),
             _d("D", [0, 4, 0], "trục y"),
             _d("S", [0, 0, 4], "đỉnh chóp trên trục z"),
             {"kind": "construct_line", "target_var": "AC",
              "through_a": "A", "through_b": "C"},
             {"kind": "construct_line", "target_var": "BD",
              "through_a": "B", "through_b": "D"},
             _cp("I", {"kind": "intersect_line_line",
                       "line_a": "AC", "line_b": "BD"}),
             {"kind": "construct_plane", "target_var": "SBC",
              "through": ["S", "B", "C"]},
             _cp("H", {"kind": "project_onto", "point": "I", "target": "SBC"}),
             {"kind": "construct_solid", "target_var": "K",
              "vertices": ["A", "B", "C", "D", "S"],
              "faces": [["A", "B", "C", "D"], ["S", "A", "B"],
                        ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"]]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "H", "wrt": "S"}},
             {"kind": "assign", "target_var": "V",
              "expr": {"kind": "measure", "quantity": "volume", "of": "K"}}]),
    },
]


# ── NHIỄM CHÉO — chữ ký cấu hình, không phải n-gram văn mẫu ────────────────
GOC = Path(__file__).resolve().parents[2]
_NGUON_CU = tuple(
    GOC / "docs" / "evaluation" / "geometry" / x
    for x in ("holdout", "fresh-probe", "generalization-matrix",
              "clean-baseline-v1", "dihedral-probe", "dihedral-probe-after",
              "dihedral-probe-after2", "dihedral-probe-after3",
              "dihedral-probe-ergonomics", "dihedral-probe-merge-verify",
              "dev-results", "dev-results-55", "dev-results-w4"))

_KHOA_DE = ("problem_text", "problem", "de", "problem_text_original")
_KHOI = ("tứ diện", "lăng trụ", "lập phương", "hộp chữ nhật", "chóp",
         "hình thoi", "hình vuông", "hình chữ nhật", "tam giác")
_HOI = re.compile(r"\b(tính|chứng minh|xác định|tìm)\b", re.IGNORECASE)


def _van(s: str) -> str:
    return re.sub(r"[^\wàáâãèéêìíòóôõùúýăđĩũơưạ-ỹ]+", " ", s.lower()).strip()


def _ngu(s: str, n: int) -> set[str]:
    t = _van(s).split()
    return {" ".join(t[i:i + n]) for i in range(max(len(t) - n + 1, 0))}


def _cau_hoi(de: str) -> str:
    m = _HOI.search(de)
    return de[m.start():] if m else de


def _de_cu() -> list[str]:
    """Mọi ĐỀ đã dùng, đọc theo CẤU TRÚC — không quét n-gram trên JSON thô.

    Bản n-gram từng báo 4/6 nhiễm với 100% cụm trùng là văn mẫu SGK dài hơn 20
    từ. Một guard báo động ở đó thì hoặc ta hạ ngưỡng — mất khả năng bắt trùng
    thật — hoặc ta viết đề bằng tiếng Việt lạ để né nó, tức làm hỏng bộ đề.
    """
    import json as _json

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

    for d in _NGUON_CU:
        if not d.is_dir():
            continue
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
    # Bộ đề V1 nằm trong mã, không trong artifact — đọc thẳng.
    try:
        from scripts.clean_baseline_cases import CASES as V1

        ra += [c["de"] for c in V1]
    except Exception:  # noqa: BLE001
        pass
    return ra


def _chu_ky(de: str) -> tuple:
    """CHỮ KÝ CẤU HÌNH: khối nào · bộ số · mệnh đề hỏi. Bỏ qua câu dẫn."""
    v = _van(de)
    return (tuple(k for k in _KHOI if k in v),
            tuple(re.findall(r"\d+(?:/\d+)?", v)),
            _van(_cau_hoi(de)))


def check_contamination(them: list[dict] | None = None) -> list[str]:
    """Trùng với BẤT KỲ bộ đề nào đã dùng? Rỗng = sạch."""
    cu = [(_chu_ky(d), d) for d in _de_cu()]
    ra = []
    for c in (CASES + (them or [])):
        ck = _chu_ky(c["de"])
        for ck_cu, van in cu:
            if ck == ck_cu:
                ra.append(f"{c['id']}: TRÙNG ĐỀ — {van[:80]}")
                break
            if ck[:2] == ck_cu[:2] and ck[2] != ck_cu[2]:
                cn = _ngu(ck[2], 8) & _ngu(ck_cu[2], 8)
                if cn:
                    ra.append(f"{c['id']}: cùng hình VÀ trùng câu hỏi — "
                              f"{sorted(cn)[0][:60]}")
                    break
    return ra
