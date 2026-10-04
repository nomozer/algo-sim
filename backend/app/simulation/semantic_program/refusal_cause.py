# -*- coding: utf-8 -*-
"""W17 §15.3 — NGUYÊN NHÂN của một lời từ chối: chính dữ kiện của đề (`SOURCE`), khâu dựng của hệ
trên một đề hợp lệ (`CONSTRUCTION`), hay chưa rõ (`UNKNOWN`).

Quyết định CHỈ từ mã có cấu trúc và bộ đọc đề của server — không bao giờ từ văn xuôi `reason`.
Bảng (kèm đính chính Task 1): `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §15.3.
Lời cho người học (`learner_messages`) chọn theo nguyên nhân: đề hợp lệ thì không bảo sửa đề.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from .plane_equation import doc_mat_phang_de, tuong_duong
from .segment_relation import _D, do_dai_trong_de
from .shape_constraint import che_muc_tieu, doc_rang_buoc
from .source_entities import dinh_danh_thuc_the

SOURCE, CONSTRUCTION, UNKNOWN = "SOURCE", "CONSTRUCTION", "UNKNOWN"
MA_DO_DAI_KHONG_DUONG = "NON_POSITIVE_LENGTH"
MA_KHONG_CAT = "PLANE_DOES_NOT_CUT"

#: Mã mà nguyên nhân không phụ thuộc đề ghi gì. Mã ngoài bảng (và ngoài hai mã phân xử theo đề
#: bên dưới) là `UNKNOWN` — kể cả `ASSUMPTION_INVARIANCE_UNPROVEN`.
NGUYEN_NHAN_THEO_MA: dict[str, str] = {
    "GIVEN_VALUE_NOT_IN_SOURCE": SOURCE,
    "ASSUMPTION_DETERMINES_ANSWER": SOURCE,
    "GIVEN_ONLY_IN_GOAL_CLAUSE": SOURCE,
    "SOURCE_TEXT_MISSING": SOURCE,
    "CONSTRUCTION_NOT_TEXT_BOUND": CONSTRUCTION,
    "CONSTRUCTION_REPLACED_BY_COORDINATES": CONSTRUCTION,
    "SOURCE_EVIDENCE_CONFLICT": CONSTRUCTION,
    "SOURCE_SPAN_MISMATCH": CONSTRUCTION,
}


def theo_ma(ma: str | None) -> str:
    return NGUYEN_NHAN_THEO_MA.get(ma or "", UNKNOWN)


def _id(t: str) -> str:
    return dinh_danh_thuc_the(t)[0]


def do_dai_khong_duong(contract: Any) -> dict[str, Any]:
    """`NON_POSITIVE_LENGTH` của compiler: đoạn mà hợp đồng mang độ dài ≤ 0 (ký hiệu học sinh), và
    `SOURCE` khi bộ đọc đề của server đọc đúng độ dài ≤ 0 ấy cho đúng đoạn ấy (hoặc cạnh hình lập
    phương ≤ 0) — không thì `CONSTRUCTION` (đề hợp lệ, hợp đồng của hệ sai)."""
    de = che_muc_tieu(getattr(contract, "problem_text", "") or "")
    # Độ dài của hợp đồng đến từ hai kênh: mục dữ kiện nhãn `XY`, và bất biến `segment_length`.
    ung = [(re.fullmatch(rf"\s*({_D})({_D})\s*", str(f.label).replace("’", "'")), f.values)
           for f in getattr(contract, "input_facts", ()) or ()]
    ung = [((m[1], m[2]), v) for m, v in ung if m is not None]
    ung += [(tuple(i.points), (i.expected,)) for i in getattr(contract, "source_invariants", ()) or ()
            if i.kind == "segment_length" and len(i.points) == 2]
    doan: list[tuple[str, str]] = []
    for d, gia_tri in ung:
        try:
            am = any(Fraction(str(v).replace(" ", "")) <= 0 for v in gia_tri)
        except (ValueError, ZeroDivisionError):
            am = False
        if am and frozenset(map(_id, d)) not in {frozenset(map(_id, x)) for x in doan}:
            doan.append(d)
    doc = {frozenset(_id(t) for t in k): v for k, v in do_dai_trong_de(de).items()}
    lap_phuong = any(r.kind == "cube_edge" and r.value is not None and r.value <= 0 for r in doc_rang_buoc(de))
    de_ghi = bool(doan) and all(
        lap_phuong or doc.get(frozenset(_id(t) for t in d), 1) <= 0 for d in doan)
    return {"reason_code": MA_DO_DAI_KHONG_DUONG,
            "reason_subjects": ["".join(dinh_danh_thuc_the(t)[1] for t in d) for d in doan],
            "refusal_cause": SOURCE if de_ghi else CONSTRUCTION}


def mat_phang_khong_cat(contract: Any, spec: Any, bien: str | None) -> dict[str, Any]:
    """`PLANE_DOES_NOT_CUT` của kernel: `SOURCE` khi mặt phẳng của câu lệnh hỏng (`bien`) có phương
    trình tỉ lệ với một phương trình mặt phẳng đề cho — chủ thể là cách đề gọi nó; không thì
    `CONSTRUCTION` (mặt phẳng do hệ đặt, đề không ghi)."""
    de = che_muc_tieu(getattr(contract, "problem_text", "") or "")
    st = next((s for s in getattr(spec, "statements", ()) if getattr(s, "target_var", None) == bien
               and s.kind == "construct_plane_from_equation"), None) if bien else None
    khop = [m for m in doc_mat_phang_de(de) if tuong_duong((st.a, st.b, st.c, st.d), m.he_so)] if st else []
    if not khop:
        return {"reason_code": MA_KHONG_CAT, "reason_subjects": [], "refusal_cause": CONSTRUCTION}
    m = khop[0]
    return {"reason_code": MA_KHONG_CAT, "refusal_cause": SOURCE,
            "reason_subjects": [f"({m.ten})" if m.ten else de[m.span[0]:m.span[1]].strip()]}
