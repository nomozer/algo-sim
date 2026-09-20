# -*- coding: utf-8 -*-
"""ADAPTER — `RequestContract` → `GeometryFactGraph`. TẤT ĐỊNH, 0 lượt gọi model.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

─── ĐỌC Ở ĐÂU, VÀ VÌ SAO ───────────────────────────────────────────────────

**Độ dài** đọc từ `contract.source_invariants` (`kind="segment_length"`): đó là
dữ kiện CÓ CẤU TRÚC do SERVER phát, mang sẵn hai tên điểm, một phân số chính xác
và `source_fact_id`. Không regex, không đoán chính tả.

**Nghĩa vụ** đọc từ `contract.obligations` — cũng có cấu trúc.

**Quan hệ vuông góc** thì KHÔNG có đường có cấu trúc nào, và đây là khoảng trống
đã đo được của hợp đồng: `app/ai/skills/geometry_analyze.md` khai thẳng rằng
quan hệ được ghi với *"`kind` là `str`, `value` là mệnh đề ĐÚNG NHƯ ĐỀ VIẾT"*,
còn `SourceInvariant` chỉ có ba kind (`segment_length`, `plane_equation`,
`point_coordinate`).

Nên adapter đọc quan hệ từ `InputFact.values` bằng một **bộ đọc ký hiệu có TỪ
VỰNG ĐÓNG**, và siết hết mức có thể siết:

  · chỉ đọc `InputFact` — **không bao giờ** đọc `contract.problem_text`;
  · chỉ nhận ba khuôn: `X ⊥ (PQR)` · `X vuông góc (PQR)` · `… vuông tại P`;
  · nhãn điểm phải ĐÃ XUẤT HIỆN trong `source_invariants` — một ký hiệu lạ
    không tự sinh ra điểm;
  · mệnh đề quan hệ KHÔNG đọc được làm cả ca rơi về `UNSUPPORTED_INCOMPLETE`,
    **không** bị bỏ qua im lặng.

⚠️ Bộ đọc ấy vẫn tin một chuỗi do LLM viết. Đó là nợ đã khai, và cách trả là mở
`SourceInvariant` cho quan hệ — tức đổi bề mặt `analyze`, tức phải đo lại. Ngoài
phạm vi wave này; xem `FACT_GRAPH_CONTRACT_EXTENSION`.

KHÔNG BAO GIỜ: đọc đáp số kỳ vọng · dùng ground truth để dựng chương trình ·
thêm dữ kiện đề không cho · tạo graph một phần rồi đi tiếp khi thiếu dữ kiện.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from .fact_graph import (
    Fact,
    GeometryFactGraph,
    MauThuanFact,
    Nut,
    dung_graph,
)

ADAPTER_VERSION = "contract-to-fact-graph/1"

TRANG_THAI_ADAPTER: tuple[str, ...] = (
    "VALID", "INVALID_CONFLICT", "UNSUPPORTED_INCOMPLETE",
)

#: TỪ VỰNG ĐÓNG của bộ đọc quan hệ. Mở rộng bảng này là đổi hợp đồng đọc.
_KY_HIEU_VUONG_GOC = ("⊥", "vuông góc với", "vuông góc")
_KY_HIEU_VUONG_TAI = ("vuông tại",)

#: Một NHÃN ĐIỂM: chữ cái, có thể kèm dấu phẩy trên hoặc chỉ số.
_MAU_NHAN = re.compile(r"[A-Za-zÀ-Ỵà-ỵ][0-9′']?")


@dataclass(frozen=True)
class KetQuaAdapter:
    status: str
    graph: GeometryFactGraph | None
    reason_code: str | None = None
    #: Chẩn đoán TỪ VỰNG ĐÓNG — không chở nguyên văn đề, không chở nhãn thô.
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    adapter_version: str = ADAPTER_VERSION


def _nhan_trong(chuoi: str, biet: set[str]) -> list[str]:
    """Các nhãn điểm ĐÃ BIẾT xuất hiện trong chuỗi, theo thứ tự xuất hiện.

    Chỉ nhận nhãn đã có trong `source_invariants` — một ký hiệu lạ KHÔNG được
    phép sinh ra một điểm mới, vì khi ấy adapter đang thêm dữ kiện đề không cho.
    """
    ra: list[str] = []
    for m in _MAU_NHAN.finditer(chuoi):
        t = m.group(0)
        if t in biet and t not in ra:
            ra.append(t)
    return ra


def _doc_quan_he(van_ban: str, biet: set[str]) -> tuple[str, tuple[str, ...]] | None:
    """Một mệnh đề quan hệ → `(loại, đối số)`; `None` nếu không thuộc từ vựng đóng."""
    thap = van_ban.lower()

    for kh in _KY_HIEU_VUONG_TAI:
        if kh in thap:
            sau = van_ban[thap.index(kh) + len(kh):]
            dinh = _nhan_trong(sau, biet)
            truoc = _nhan_trong(van_ban[:thap.index(kh)], biet)
            if len(dinh) >= 1 and len(truoc) >= 3:
                return "right_angle", (dinh[0], *sorted(x for x in truoc if x != dinh[0]))
            return None

    for kh in _KY_HIEU_VUONG_GOC:
        if kh in van_ban or kh in thap:
            i = van_ban.find(kh) if kh in van_ban else thap.index(kh)
            trai = _nhan_trong(van_ban[:i], biet)
            phai = _nhan_trong(van_ban[i + len(kh):], biet)
            if len(trai) == 2 and len(phai) >= 3:
                # đoạn ⊥ mặt phẳng: (đoạn_a, đoạn_b, *đỉnh mặt phẳng)
                return "perpendicular", (*trai, *sorted(phai))
            return None
    return None


def build_fact_graph(contract: Any) -> KetQuaAdapter:
    """`RequestContract` → `GeometryFactGraph`. Không bao giờ trả graph một phần."""
    bat_bien = [b for b in (getattr(contract, "source_invariants", None) or ())
                if getattr(b, "kind", None) == "segment_length"]
    if not bat_bien:
        return KetQuaAdapter("UNSUPPORTED_INCOMPLETE", None,
                             "NO_STRUCTURED_LENGTH_FACT",
                             ("không có `SourceInvariant(kind=segment_length)` nào",))

    biet: set[str] = set()
    for b in bat_bien:
        biet.update(str(p) for p in (b.points or ()))

    nodes: dict[str, Nut] = {t: Nut(t, "point", (), "GIVEN") for t in sorted(biet)}
    facts: list[Fact] = []
    chan_doan: list[str] = []

    # ── ĐỘ DÀI — đường CÓ CẤU TRÚC ───────────────────────────────────────
    for b in bat_bien:
        pts = tuple(str(p) for p in (b.points or ()))
        if len(pts) != 2:
            chan_doan.append("SEGMENT_LENGTH_ARITY_UNEXPECTED")
            continue
        try:
            Fraction(str(b.expected))
        except (ValueError, ZeroDivisionError, TypeError):
            # Độ dài KÝ HIỆU (`a`, `2a`) — hợp lệ với đề, ngoài phạm vi lát cắt.
            return KetQuaAdapter("UNSUPPORTED_INCOMPLETE", None,
                                 "SYMBOLIC_LENGTH",
                                 ("độ dài không phải hằng số hữu tỉ",))
        doan = "seg_" + "_".join(sorted(pts))
        nodes.setdefault(doan, Nut(doan, "segment", tuple(sorted(pts)), "GIVEN"))
        facts.append(Fact(
            fact_id=f"len_{'_'.join(sorted(pts))}",
            kind="length", args=tuple(sorted(pts)), value=str(b.expected),
            source_fact_id=getattr(b, "source_fact_id", None) or None,
            status="GIVEN"))

    # ── QUAN HỆ — đường KHÔNG có cấu trúc (xem docstring) ────────────────
    for fct in (getattr(contract, "input_facts", None) or ()):
        for gt in (getattr(fct, "values", None) or ()):
            if not isinstance(gt, str):
                continue
            doc = _doc_quan_he(gt, biet)
            if doc is None:
                continue
            loai, args = doc
            facts.append(Fact(
                fact_id=f"{loai}_{'_'.join(args)}",
                kind=loai, args=args, value="TRUE",
                source_fact_id=getattr(fct, "fact_id", None) or None,
                status="GIVEN"))

    # ── NGHĨA VỤ — đường CÓ CẤU TRÚC ─────────────────────────────────────
    for i, ob in enumerate(getattr(contract, "obligations", None) or ()):
        nid = f"req_{i}"
        nodes[nid] = Nut(nid, "measurement_request", (str(ob.container),), "GIVEN")
        facts.append(Fact(
            fact_id=f"req_{ob.kind}_{i}",
            kind="requested_operation", args=(str(ob.kind), str(ob.container)),
            value=str((ob.params or {}).get("witness") or ""),
            source_fact_id=None, status="GIVEN"))

    try:
        graph = dung_graph(tuple(nodes.values()), tuple(facts))
    except MauThuanFact as e:
        return KetQuaAdapter("INVALID_CONFLICT", None, e.ma, (e.chi_tiet,))

    return KetQuaAdapter("VALID", graph, None, tuple(sorted(set(chan_doan))))
