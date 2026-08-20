# -*- coding: utf-8 -*-
"""Bề mặt `analyze` của route semantic — TÁCH HẲN khỏi từ vựng catalog.

VÌ SAO PHẢI TÁCH (spec E5): khoá phạm vi cũ không nằm ở các cổng, nó nằm ngay
trong response schema của `analyze` — `requested_operations` và
`requested_mechanisms` dùng `enum: list(analyze_exposed_operations())`, dẫn
xuất từ 24 target. Bài ngoài catalog thì LLM **không có từ vựng để khai**, nên
tháo `mechanism_gate`/`completeness_gate` vẫn chưa mở được phạm vi.

Cách tách: HAI schema riêng, KHÔNG trộn semantic obligation với catalog
operation vào cùng một enum. Catalog vocabulary vẫn sống cho đường module; nó
chỉ không được quyết định admissibility ở đây.

Server ĐÓNG BĂNG nghĩa là server LỌC, không phải chép nguyên lời LLM: nghĩa vụ
ngoài taxonomy bị loại ngay tại đây, không để C₁a phát hiện muộn một tầng.
"""
from __future__ import annotations

from typing import Any

from .obligations import (
    OBLIGATION_KINDS,
    SEMANTIC_PRESCRIBED_PROCEDURES,
    Obligation,
)
from .request_contract import InputFact, RequestContract

#: Kiểu của một mục dữ liệu đề cho — đóng, và bám hệ kiểu của IR.
INPUT_FACT_KINDS = ("array", "matrix", "map", "set", "graph", "tree_node",
                    "int", "str", "bool", "float")

SEMANTIC_ANALYZE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        # Dữ liệu đề cho, MỖI MỤC CÓ ID BỀN. `id` là thứ mà literal trong IR
        # phải THAM CHIẾU tới — ghim *cái nào*, không phải *có tồn tại đâu đó*
        # (chuỗi provenance P2, spec §3.4).
        "input_facts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "kind": {"type": "STRING", "enum": list(INPUT_FACT_KINDS)},
                    "label": {"type": "STRING"},
                    "value": {"type": "STRING"},
                },
                "required": ["id", "kind", "label"],
            },
        },
        # Nghĩa vụ ngữ nghĩa — enum DẪN XUẤT TỪ TAXONOMY ĐÃ ĐÓNG BĂNG, không
        # phải từ catalog.
        "obligations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "kind": {"type": "STRING", "enum": sorted(OBLIGATION_KINDS)},
                    "container": {"type": "STRING"},
                    "witness": {"type": "STRING"},
                    "cmp": {"type": "STRING", "nullable": True},
                    "op": {"type": "STRING", "nullable": True},
                    "transform": {"type": "STRING", "nullable": True},
                    "pred": {"type": "STRING", "nullable": True},
                },
                "required": ["kind", "container", "witness"],
            },
        },
        "prescribed_procedure": {
            "type": "STRING",
            "enum": sorted(SEMANTIC_PRESCRIBED_PROCEDURES),
            "nullable": True,
        },
    },
    "required": ["input_facts", "obligations"],
}

_PARAM_KEYS = ("witness", "cmp", "op", "transform", "pred", "item", "order",
               "src", "domain")


def _as_values(raw: Any) -> tuple[Any, ...]:
    if raw is None:
        return ()
    if isinstance(raw, (list, tuple)):
        return tuple(raw)
    return (raw,)


def build_request_contract(payload: dict[str, Any]) -> RequestContract:
    """Đóng băng đầu ra của `analyze` thành hợp đồng BẤT BIẾN.

    Lọc tại đây, không tin nguyên lời LLM:
    - nghĩa vụ có `kind` ngoài taxonomy đã đóng băng → **loại**;
    - mục dữ liệu thiếu `id` → **loại** (không có id thì P2 không ghim được).
    """
    facts: list[InputFact] = []
    for raw in payload.get("input_facts") or ():
        if not isinstance(raw, dict):
            continue
        fid = raw.get("id")
        if not isinstance(fid, str) or not fid:
            continue
        facts.append(
            InputFact(
                fact_id=fid,
                label=str(raw.get("label") or fid),
                values=_as_values(raw.get("value")),
            )
        )

    obligations: list[Obligation] = []
    for raw in payload.get("obligations") or ():
        if not isinstance(raw, dict):
            continue
        kind = raw.get("kind")
        if kind not in OBLIGATION_KINDS:
            # Ngoài taxonomy ⇒ loại NGAY. Giữ lại thì C₁a mới phát hiện, muộn
            # hơn một tầng và lẫn với lỗi "thiếu witness".
            continue
        container = raw.get("container")
        if not isinstance(container, str) or not container:
            continue
        params = {k: raw[k] for k in _PARAM_KEYS if raw.get(k) is not None}
        obligations.append(
            Obligation(kind=kind, container=container, params=params)
        )

    return RequestContract(
        obligations=tuple(obligations), input_facts=tuple(facts)
    )
