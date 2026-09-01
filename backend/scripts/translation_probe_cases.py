# -*- coding: utf-8 -*-
"""BỐN ĐỀ cho FRESH_TRANSLATION_COMPOSITION_PROBE. **0 API call.**

─── CÂU HỎI ───────────────────────────────────────────────────────────────

Gặp bài mới cần dời một điểm theo một vectơ, mô hình có **tự tìm ra**
`translate(point, vector)` và ghép nó với các phép dựng khác không?

Không đo toàn bộ hình học. Không k=3. Không thêm năng lực giữa probe.

─── §4 — TÍNH BẮT BUỘC, VÀ MỘT ĐÍNH CHÍNH PHẢI NÓI TRƯỚC ──────────────────

Chỉ thị đòi ≥3/4 ca có `TRANSLATION_REQUIRED_BY_CURRENT_IR = YES`. **Không ca
nào đạt**, và đó là sự thật chứ không phải thiếu sót của bộ đề:

    M = midpoint(P, S)
    Q = divide_segment(R, M, 2)      →  R + 2(M − R) = P + S − R

đúng bằng `translate(P, vector_from_points(R, S))`. Với vectơ định nghĩa bằng
HAI ĐIỂM — tức mọi ca ở đây — phép tịnh tiến LUÔN biểu diễn được, kể cả trước
khi `translate` tồn tại. Xem `audit_translation_gap.audit_to_hop` và dòng đính
chính ở `STATUS_LEDGER`.

Nên mỗi ca ghi `TRANSLATION_USEFUL_BUT_NOT_REQUIRED = YES`, kèm chính đường
vòng ấy viết ra. Điều probe đo được vẫn nguyên vẹn và vẫn đáng đo: **mô hình
chọn gì khi cả hai đường đều mở** — phép đúng nghĩa, hay một `divide_segment`
tỉ lệ 2 đi ra ngoài đoạn, hay khai thẳng toạ độ.

─── ORACLE ────────────────────────────────────────────────────────────────

`dap_so` tính TAY từ hệ trục ở `kiem_tay`, đối chiếu độc lập với kết quả chạy
lời giải chuẩn tắc. `chuan_tac` KHÔNG BAO GIỜ vào prompt.
"""
from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

CAN, HUU_TI = "radical", "rational"


def q(x) -> tuple[str, Fraction]:
    return (HUU_TI, Fraction(x))


def can(he, c: int) -> tuple[str, tuple[Fraction, int]]:
    return (CAN, (Fraction(he), c))


def _d(t, xyz, ly_do):
    return {"kind": "declare_point", "target_var": t, "at": xyz,
            "model_assumption": ly_do}


def _vec(t, a, b):
    return {"kind": "assign", "target_var": t,
            "expr": {"kind": "vector_from_points", "from_point": a,
                     "to_point": b}}


def _tt(t, p, v):
    return {"kind": "construct_point", "target_var": t,
            "expr": {"kind": "translate", "point": p, "vector": v}}


def _spec(title, decls, stmts):
    return {"spec_version": "1.0", "title": title,
            "description": "Lời giải chuẩn tắc do người viết.",
            "pedagogical_intent": "Một đỉnh dựng ra bằng phép tịnh tiến.",
            "memory_declarations": decls, "statements": stmts}


CASES: list[dict] = [
    # ══ T1 · HÌNH BÌNH HÀNH — đỉnh thứ tư dùng tiếp ═══════════════════════
    {
        "id": "t1_binh_hanh_dinh_thu_tu",
        "topology": "hình bình hành đáy + đỉnh trên trục",
        "capability_mix": ["vector_from_points", "translate",
                           "construct_plane", "distance"],
        "translation_required": False,
        "translation_useful": True,
        "duong_vong": "C = divide_segment(A, midpoint(B, D), 2)",
        "translated_point_count": 1,
        "dependency_depth": 4,
        "obligation_count": 1,
        "de": (
            "Cho hình bình hành ABCD có AB = 6, AD = 4 và AB vuông góc với "
            "AD. Trên đường thẳng vuông góc với mặt phẳng (ABCD) tại A lấy "
            "điểm S sao cho SA = 3. Tính khoảng cách từ đỉnh C đến mặt phẳng "
            "(SBD)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(6,0,0) D(0,4,0) ⇒ C = B + AD = (6,4,0); S(0,0,3). "
            "(SBD): x/6 + y/4 + z/3 = 1 ⇒ 2x + 3y + 4z = 12. "
            "d(C) = |12+12+0-12|/√29 = 12/√29 = 12√29/29."
        ),
        "dap_so": can(Fraction(12, 29), 29),
        "chuan_tac": _spec(
            "Khoảng cách từ C đến (SBD)",
            [{"name": "SBD", "type": "plane3"}, {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc tại đỉnh có hai cạnh vuông góc"),
             _d("B", [6, 0, 0], "trục x"),
             _d("D", [0, 4, 0], "trục y"),
             _d("S", [0, 0, 3], "trục z, SA vuông góc đáy"),
             _vec("AD", "A", "D"),
             _tt("C", "B", "AD"),
             {"kind": "construct_plane", "target_var": "SBD",
              "through": ["S", "B", "D"]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "C", "wrt": "SBD"}}]),
    },
    # ══ T2 · LĂNG TRỤ — đỉnh tầng trên ════════════════════════════════════
    {
        "id": "t2_lang_tru_dinh_tang_tren",
        "topology": "lăng trụ đứng đáy tam giác vuông",
        "capability_mix": ["vector_from_points", "translate",
                           "construct_plane", "distance"],
        "translation_required": False,
        "translation_useful": True,
        "duong_vong": "B_prime = divide_segment(A, midpoint(B, A_prime), 2)",
        "translated_point_count": 1,
        "dependency_depth": 4,
        "obligation_count": 1,
        "de": (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại A với AB = 2, "
            "AC = 6 và cạnh bên AA' = 3. Tính khoảng cách từ đỉnh B' đến mặt "
            "phẳng (A'BC)."
        ),
        "kiem_tay": (
            "A(0,0,0) B(2,0,0) C(0,6,0) A'(0,0,3) ⇒ B' = B + AA' = (2,0,3). "
            "(A'BC): x/2 + y/6 + z/3 = 1 ⇒ 3x + y + 2z = 6. "
            "d(B') = |6+0+6-6|/√14 = 6/√14 = 3√14/7."
        ),
        "dap_so": can(Fraction(3, 7), 14),
        "chuan_tac": _spec(
            "Khoảng cách từ B' đến (A'BC)",
            [{"name": "P", "type": "plane3"}, {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc tại đỉnh vuông của đáy"),
             _d("B", [2, 0, 0], "trục x"),
             _d("C", [0, 6, 0], "trục y"),
             _d("A_prime", [0, 0, 3], "cạnh bên dọc trục z"),
             _vec("AA_prime", "A", "A_prime"),
             _tt("B_prime", "B", "AA_prime"),
             {"kind": "construct_plane", "target_var": "P",
              "through": ["A_prime", "B", "C"]},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "B_prime", "wrt": "P"}}]),
    },
    # ══ T3 · HỘP — tịnh tiến DÂY CHUYỀN, ba điểm dựng ═════════════════════
    {
        "id": "t3_hop_tinh_tien_day_chuyen",
        "topology": "hình hộp chữ nhật",
        "capability_mix": ["vector_from_points", "translate", "midpoint",
                           "construct_line", "distance", "radical"],
        "translation_required": False,
        "translation_useful": True,
        "duong_vong": "mỗi đỉnh qua divide_segment(·, midpoint(·,·), 2)",
        "translated_point_count": 3,
        "dependency_depth": 5,
        "obligation_count": 1,
        "de": (
            "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4 và "
            "AA' = 6. Gọi M là trung điểm của cạnh CC'. Tính khoảng cách từ "
            "đỉnh A đến đường thẳng B'M."
        ),
        "kiem_tay": (
            "A(0,0,0) B(3,0,0) D(0,4,0) A'(0,0,6). "
            "C = B + AD = (3,4,0); B' = B + AA' = (3,0,6); "
            "C' = C + AA' = (3,4,6) ⇒ M = (3,4,3). "
            "B'M có chỉ phương (0,4,-3); AB' = (3,0,6). "
            "AB'×(0,4,-3) = (-24, 9, 12) ⇒ |·|² = 801, |chỉ phương|² = 25. "
            "d² = 801/25 ⇒ d = 3√89/5."
        ),
        "dap_so": can(Fraction(3, 5), 89),
        "chuan_tac": _spec(
            "Khoảng cách từ A đến B'M",
            [{"name": "BM", "type": "line3"}, {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc"),
             _d("B", [3, 0, 0], "cạnh AB dọc trục x"),
             _d("D", [0, 4, 0], "cạnh AD dọc trục y"),
             _d("A_prime", [0, 0, 6], "cạnh bên dọc trục z"),
             _vec("AD", "A", "D"),
             _vec("AA_prime", "A", "A_prime"),
             _tt("C", "B", "AD"),
             _tt("B_prime", "B", "AA_prime"),
             _tt("C_prime", "C", "AA_prime"),
             {"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "C", "b": "C_prime"}},
             {"kind": "construct_line", "target_var": "BM",
              "through_a": "B_prime", "through_b": "M"},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "A", "wrt": "BM"}}]),
    },
    # ══ T4 · TỊNH TIẾN LÀ MỘT MẮT XÍCH — chuỗi sâu ═══════════════════════
    {
        "id": "t4_mat_xich_trong_chuoi_sau",
        "topology": "chóp đáy hình bình hành",
        "capability_mix": ["vector_from_points", "translate",
                           "construct_line", "intersect_line_line",
                           "construct_plane", "project_onto", "distance"],
        "translation_required": False,
        "translation_useful": True,
        "duong_vong": "C = divide_segment(A, midpoint(B, D), 2)",
        "translated_point_count": 1,
        "dependency_depth": 6,
        "obligation_count": 1,
        "de": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành với AB = 4, "
            "AD = 2 và AB vuông góc với AD. Cạnh SA vuông góc với mặt phẳng "
            "đáy và SA = 4. Gọi I là giao điểm của AC và BD, H là hình chiếu "
            "vuông góc của I lên mặt phẳng (SAB). Tính khoảng cách từ H đến "
            "đỉnh C."
        ),
        "kiem_tay": (
            "A(0,0,0) B(4,0,0) D(0,2,0) S(0,0,4) ⇒ C = B + AD = (4,2,0). "
            "I = AC ∩ BD = (2,1,0). (SAB) là mặt y = 0 ⇒ H = (2,0,0). "
            "HC = (2,2,0) ⇒ |HC| = √8 = 2√2."
        ),
        "dap_so": can(2, 2),
        "chuan_tac": _spec(
            "Khoảng cách từ H đến C",
            [{"name": "AC", "type": "line3"}, {"name": "BD", "type": "line3"},
             {"name": "SAB", "type": "plane3"},
             {"name": "d", "type": "float"}],
            [_d("A", [0, 0, 0], "gốc, SA vuông góc đáy"),
             _d("B", [4, 0, 0], "trục x"),
             _d("D", [0, 2, 0], "trục y"),
             _d("S", [0, 0, 4], "trục z"),
             _vec("AD", "A", "D"),
             _tt("C", "B", "AD"),
             {"kind": "construct_line", "target_var": "AC",
              "through_a": "A", "through_b": "C"},
             {"kind": "construct_line", "target_var": "BD",
              "through_a": "B", "through_b": "D"},
             {"kind": "construct_point", "target_var": "I",
              "expr": {"kind": "intersect_line_line",
                       "line_a": "AC", "line_b": "BD"}},
             {"kind": "construct_plane", "target_var": "SAB",
              "through": ["S", "A", "B"]},
             {"kind": "construct_point", "target_var": "H",
              "expr": {"kind": "project_onto", "point": "I",
                       "target": "SAB"}},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "H", "wrt": "C"}}]),
    },
]


# ── NHIỄM CHÉO — chữ ký cấu hình ──────────────────────────────────────────
GOC = Path(__file__).resolve().parents[2]
_THU_MUC = ("holdout", "fresh-probe", "generalization-matrix",
            "clean-baseline-v1", "clean-baseline-v2", "stability-seed",
            "stability-k3", "dihedral-probe", "dihedral-probe-after",
            "dihedral-probe-after2", "dihedral-probe-after3",
            "dihedral-probe-ergonomics", "dihedral-probe-merge-verify",
            "dev-results", "dev-results-55", "dev-results-w4")
_KHOA_DE = ("problem_text", "problem", "de", "problem_text_original")
_KHOI = ("tứ diện", "lăng trụ", "lập phương", "hộp chữ nhật", "chóp",
         "hình thoi", "hình vuông", "hình chữ nhật", "hình bình hành",
         "tam giác")
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
    import json as _json

    ra: list[str] = []

    def di(x, sau=0):
        if sau > 8:
            return
        if isinstance(x, dict):
            for k, val in x.items():
                if k in _KHOA_DE and isinstance(val, str) and len(val) > 40:
                    ra.append(val)
                else:
                    di(val, sau + 1)
        elif isinstance(x, list):
            for val in x:
                di(val, sau + 1)

    for ten in _THU_MUC:
        d = GOC / "docs" / "evaluation" / "geometry" / ten
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
    # Bộ đề V1/V2 nằm trong MÃ, không trong artifact — đọc thẳng.
    for mod in ("clean_baseline_cases", "clean_baseline_v2_cases"):
        try:
            m = __import__(f"scripts.{mod}", fromlist=["CASES"])
            ra += [c["de"] for c in m.CASES]
        except Exception:  # noqa: BLE001
            pass
    return ra


def _chu_ky(de: str) -> tuple:
    v = _van(de)
    return (tuple(k for k in _KHOI if k in v),
            tuple(re.findall(r"\d+(?:/\d+)?", v)),
            _van(_cau_hoi(de)))


def check_contamination(them: list[dict] | None = None) -> list[str]:
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
