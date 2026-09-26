# -*- coding: utf-8 -*-
"""ADAPTER — `RequestContract` → `GeometryFactGraph`. TẤT ĐỊNH, 0 lượt gọi model.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20)
· `FACT_GRAPH_CONTRACT_EXTENSION` (2026-09-20) — bản `/2`.

─── ĐỌC Ở ĐÂU, VÀ VÌ SAO ───────────────────────────────────────────────────

Ba đường vào, **cả ba đều CÓ CẤU TRÚC**:

  · **độ dài** ← `contract.source_invariants` (`kind="segment_length"`):
    hai tên điểm, một phân số chính xác, một `source_fact_id`;
  · **quan hệ vuông góc** ← `contract.geometric_relations`: hai loại có kiểu,
    tham chiếu điểm kiểm được, xuất xứ và cờ giả định;
  · **nghĩa vụ** ← `contract.obligations`.

─── BẢN `/1` ĐỌC CÂU CHỮ; BẢN NÀY KHÔNG ────────────────────────────────────

`/1` không có đường có cấu trúc cho quan hệ, nên nó đọc `InputFact.values` bằng
một bộ đọc từ vựng đóng (`⊥`, *"vuông góc"*, *"vuông tại"*). Đo được ba hệ quả,
và cả ba đều là lỗi của **hợp đồng**, không phải của bộ đọc:

  · *"tam giác ABC vuông tại A"* và *"tam giác ABC có góc A là góc vuông"* cho
    **hai** FactGraph khác nhau — cùng một quan hệ, khác lời văn;
  · một câu có chữ *"vuông góc"* là đủ để bài được nhận, dù không ai khai quan
    hệ ấy như dữ kiện;
  · đề viết bằng tiếng khác ⇒ quan hệ biến mất.

Bộ đọc ấy đã **gỡ hẳn**, không chuyển sang chế độ legacy: giữ nó lại là giữ một
nguồn sự thật thứ hai cho cùng một sự kiện, và không artifact lịch sử nào cần
đọc lại hợp đồng qua nó.

⚠️ Vì vậy: **thiếu quan hệ có cấu trúc thì từ chối**, kể cả khi `problem_text`
nói rõ ràng *"SA vuông góc với mặt phẳng (ABC)"*. Đó là một phán quyết cố ý —
`UNSUPPORTED_STRUCTURED_RELATION_MISSING` — chứ không phải một lỗ hổng.

─── SUY DIỄN ĐƯỢC PHÉP, VÀ CHỈ MỘT BƯỚC ────────────────────────────────────

`SA ⟂ (ABC)` kéo theo `SA ⟂ AB` và `SA ⟂ AC`, vì `AB`, `AC` nằm trong `(ABC)`.
Những fact ấy mang `DERIVED` và **nêu cha**: quan hệ đường–mặt nguồn, cùng fact
`lies_in_plane` chứng minh đoạn nằm trong mặt. Ghi chúng thành `GIVEN` là khai
rằng đề đã nói thẳng điều đó — nó không nói.

KHÔNG BAO GIỜ: đọc `problem_text` · đọc đáp số kỳ vọng · thêm dữ kiện đề không
cho · tạo graph một phần rồi đi tiếp khi thiếu dữ kiện.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from ..semantic_program.source_entities import (
    dinh_danh_thuc_the,
    kiem_tra_grounding_prism,
)
from ..semantic_program.structured_relations import (
    QuanHeChinhTac,
    kiem_va_chuan_hoa,
)
from .fact_graph import (
    AdaptedPrismTopology,
    Fact,
    GeometryFactGraph,
    MauThuanFact,
    Nut,
    dung_graph,
)

ADAPTER_VERSION = "contract-to-fact-graph/2"

TRANG_THAI_ADAPTER: tuple[str, ...] = (
    "VALID", "INVALID_CONFLICT", "UNSUPPORTED_INCOMPLETE",
    "INVALID_STRUCTURED_RELATION",
)


@dataclass(frozen=True)
class KetQuaAdapter:
    status: str
    graph: GeometryFactGraph | None
    reason_code: str | None = None
    #: Chẩn đoán TỪ VỰNG ĐÓNG — không chở nguyên văn đề, không chở nhãn thô.
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    adapter_version: str = ADAPTER_VERSION
    #: Luật mâu thuẫn đã bắt (chỉ khi `INVALID_CONFLICT` do một luật có tên).
    rule_id: str | None = None
    #: Bằng chứng TỪ VỰNG ĐÓNG của luật: băm tam giác, số đỉnh vuông, con trỏ nguồn.
    evidence: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def _id_duong(d: tuple[str, ...]) -> str:
    return "_".join(d)


def _suy_dien(cha: str, duong: tuple[str, ...], mat: tuple[str, ...]) -> list[Fact]:
    """`line ⟂ plane` ⇒ các `line ⟂ line` với mọi cạnh của mặt phẳng ấy.

    Mỗi fact suy ra nêu HAI cha: quan hệ đường–mặt, và bằng chứng đoạn nằm
    trong mặt. Bằng chứng ấy là chuyện tham chiếu điểm, không phải chuyện toạ
    độ — hai đầu mút của đoạn đều nằm trong bộ ba xác định mặt phẳng.
    """
    ra: list[Fact] = []
    for i in range(len(mat)):
        for j in range(i + 1, len(mat)):
            canh = tuple(sorted((mat[i], mat[j])))
            if set(canh) == set(duong):
                continue  # chính nó, không phải một quan hệ mới
            nam = Fact(
                fact_id=f"lies_in__{_id_duong(canh)}__{'_'.join(mat)}",
                kind="lies_in_plane", args=(*canh, *mat), value="TRUE",
                source_fact_id=None, status="DERIVED")
            a, b = sorted((duong, canh))
            ra.append(nam)
            ra.append(Fact(
                fact_id=f"perp_lines__{_id_duong(a)}__{_id_duong(b)}",
                kind="perpendicular_lines", args=(*a, *b), value="TRUE",
                source_fact_id=None, status="DERIVED",
                derived_from=tuple(sorted((cha, nam.fact_id)))))
    return ra


def build_fact_graph(contract: Any) -> KetQuaAdapter:
    """`RequestContract` → `GeometryFactGraph`. Không bao giờ trả graph một phần."""
    bat_bien = [b for b in (getattr(contract, "source_invariants", None) or ())
                if getattr(b, "kind", None) == "segment_length"]
    if not bat_bien:
        return KetQuaAdapter("UNSUPPORTED_INCOMPLETE", None,
                             "NO_STRUCTURED_LENGTH_FACT",
                             ("không có `SourceInvariant(kind=segment_length)` nào",))

    biet: set[str] = set()
    display_labels: dict[str, str] = {}

    def _dinh_danh(raw: str) -> str:
        sid, lbl = dinh_danh_thuc_the(raw)
        biet.add(sid)
        display_labels[sid] = lbl
        return sid

    for b in bat_bien:
        for p in (b.points or ()):
            _dinh_danh(str(p))

    topo = getattr(contract, "solid_topology", None)
    adapted_topo = topo
    if topo is not None:
        if getattr(topo, "solid_kind", None) == "prism":
            base_ids = tuple(_dinh_danh(str(p)) for p in (getattr(topo, "base_cycle", ()) or ()))
            top_ids = tuple(_dinh_danh(str(p)) for p in (getattr(topo, "top_cycle", ()) or ()))
            corr_ids = tuple((_dinh_danh(str(u)), _dinh_danh(str(v)))
                             for u, v in (getattr(topo, "correspondence", ()) or ()))
            g_status, g_detail = kiem_tra_grounding_prism(
                getattr(topo, "solid_subkind", None),
                getattr(topo, "source_grounding", None),
            )
            adapted_topo = AdaptedPrismTopology(
                solid_kind="prism",
                base_cycle=base_ids,
                top_cycle=top_ids,
                correspondence=corr_ids,
                display_labels=dict(display_labels),
                base_shape=getattr(topo, "base_shape", None),
                lateral_structure=getattr(topo, "lateral_structure", "right") or "right",
                solid_subkind=getattr(topo, "solid_subkind", None),
                source_grounding=getattr(topo, "source_grounding", None),
                grounding_status=g_status,
                grounding_detail=g_detail,
            )
        else:
            for p in (getattr(topo, "base_cycle", ()) or ()):
                _dinh_danh(str(p))
            for p in (getattr(topo, "top_cycle", ()) or ()):
                _dinh_danh(str(p))
            if getattr(topo, "apex", None):
                _dinh_danh(str(topo.apex))

    nodes: dict[str, Nut] = {t: Nut(t, "point", (), "GIVEN") for t in sorted(biet)}
    facts: list[Fact] = []
    chan_doan: list[str] = []

    # ── ĐỘ DÀI ───────────────────────────────────────────────────────────
    for b in bat_bien:
        raw_pts = tuple(str(p) for p in (b.points or ()))
        if len(raw_pts) != 2:
            chan_doan.append("SEGMENT_LENGTH_ARITY_UNEXPECTED")
            continue
        try:
            Fraction(str(b.expected))
        except (ValueError, ZeroDivisionError, TypeError):
            # Độ dài KÝ HIỆU (`a`, `2a`) — hợp lệ với đề, ngoài phạm vi lát cắt.
            return KetQuaAdapter("UNSUPPORTED_INCOMPLETE", None,
                                 "SYMBOLIC_LENGTH",
                                 ("độ dài không phải hằng số hữu tỉ",))
        pts = tuple(_dinh_danh(p) for p in raw_pts)
        doan = "seg_" + "_".join(sorted(pts))
        nodes.setdefault(doan, Nut(doan, "segment", tuple(sorted(pts)), "GIVEN"))
        facts.append(Fact(
            fact_id=f"len_{'_'.join(sorted(pts))}",
            kind="length", args=tuple(sorted(pts)), value=str(b.expected),
            source_fact_id=getattr(b, "source_fact_id", None) or None,
            status="GIVEN"))

    # ── QUAN HỆ — đường CÓ CẤU TRÚC, KHÔNG đọc câu chữ ───────────────────
    kq = kiem_va_chuan_hoa(contract)
    if kq.loi:
        # Hợp đồng HỎNG, khác hẳn hợp đồng THIẾU: từ chối bằng mã của chính lỗi
        # đầu tiên, không nuốt rồi báo "thiếu dữ kiện".
        dau = kq.loi[0]
        return KetQuaAdapter(
            "INVALID_STRUCTURED_RELATION", None, dau.ma,
            tuple(sorted({e.ma for e in kq.loi})))

    da_suy: dict[str, Fact] = {}
    for q in kq.relations:
        if not q.dung_duoc_cho_tang_dung():
            # Giả định chưa xác nhận, hoặc không ghim được về mục dữ kiện nào.
            # Không âm thầm nâng thành GIVEN, và cũng không im lặng bỏ đi.
            chan_doan.append("RELATION_NOT_GROUNDED")
            continue
        q_args_sid = tuple(_dinh_danh(p) for p in q.args)
        q_duong_sid = tuple(_dinh_danh(p) for p in q.duong)
        q_mat_sid = tuple(_dinh_danh(p) for p in q.mat) if q.mat else ()

        if q.kind == "perpendicular_lines":
            fid = f"perp_lines__{_id_duong(q_args_sid[:2])}__{_id_duong(q_args_sid[2:])}"
        else:
            fid = f"perp_line_plane__{_id_duong(q_duong_sid)}__{'_'.join(q_mat_sid)}"

        facts.append(Fact(
            fact_id=fid, kind=q.kind, args=q_args_sid, value="TRUE",
            source_fact_id=q.source_fact_id, status="GIVEN"))

        if q.kind == "perpendicular_line_plane":
            for f in _suy_dien(fid, q_duong_sid, q_mat_sid):
                da_suy.setdefault(f.fact_id, f)

    # Một fact suy ra KHÔNG được đè lên fact đề cho cùng danh tính: đề cho thì
    # mạnh hơn, và ghi đè sẽ đánh mất `source_fact_id`.
    co_san = {f.fact_id for f in facts}
    facts.extend(f for _, f in sorted(da_suy.items()) if f.fact_id not in co_san)

    # ── NGHĨA VỤ ─────────────────────────────────────────────────────────
    for i, ob in enumerate(getattr(contract, "obligations", None) or ()):
        nid = f"req_{i}"
        nodes[nid] = Nut(nid, "measurement_request", (str(ob.container),), "GIVEN")
        facts.append(Fact(
            fact_id=f"req_{ob.kind}_{i}",
            kind="requested_operation", args=(str(ob.kind), str(ob.container)),
            value=str((ob.params or {}).get("witness") or ""),
            source_fact_id=None, status="GIVEN"))

    try:
        graph = dung_graph(
            tuple(nodes.values()),
            tuple(facts),
            solid_topology=adapted_topo,
        )
    except MauThuanFact as e:
        return KetQuaAdapter("INVALID_CONFLICT", None, e.ma, e.chan_doan or (e.chi_tiet,),
                             rule_id=e.rule_id, evidence=e.bang_chung)

    return KetQuaAdapter("VALID", graph, None, tuple(sorted(set(chan_doan))))
