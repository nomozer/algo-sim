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
from .literal_extractor import (
    LiteralCandidate,
    extract_literals,
    gia_tri_kem_ky_tu,
)
from .request_contract import InputFact, RequestContract, norm_value

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
                    # MẢNG, không phải một chuỗi. Bản đầu khai STRING đơn và nó
                    # làm P2 trượt sạch một cách câm: dãy "12, 45, 67" về dưới
                    # dạng MỘT giá trị, còn `initial_value` trong IR là ba số
                    # nguyên, nên không giá trị nào "có trong mục dữ liệu" cả.
                    "value": {"type": "ARRAY", "items": {"type": "STRING"}},
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
                    # ĐỊNH DANH, không phải câu chữ. Lượt pilot 3 thu được
                    # `container` = "các năm từ nam_bat_dau đến nam_ket_thuc" —
                    # một cụm từ tiếng Việt, không thể là tên biến, nên chương
                    # trình không có cách nào khai báo trùng và C₁a luôn trượt.
                    "container": {
                        "type": "STRING",
                        "description": "Tên biến kiểu snake_case, chỉ chữ "
                                       "thường không dấu, số và gạch dưới. "
                                       "KHÔNG viết cụm từ hay câu.",
                    },
                    "witness": {
                        "type": "STRING",
                        "description": "Tên biến kiểu snake_case sẽ chứa câu "
                                       "trả lời. KHÔNG viết cụm từ hay câu.",
                    },
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
    """Phẳng hoá + chuẩn hoá kiểu. Xem `norm_value` để biết vì sao cần bậc này."""
    if raw is None:
        return ()
    if isinstance(raw, (list, tuple)):
        return tuple(norm_value(v) for v in raw)
    return (norm_value(raw),)


#: Ứng viên kind nào được nhận cho một fact kind nào.
#:
#: `str` ↔ `array` mở hai chiều là CÓ CHỦ ĐÍCH, không phải nới ẩu: đề viết đầu
#: vào là một chuỗi (`{[()]}`) còn chương trình quét nó như mảng ký tự. Đóng
#: chiều đó lại thì mọi bài xử lý chuỗi — Stack, palindrome, đếm nguyên âm —
#: trượt vì HÌNH DẠNG chứ không vì dữ liệu.
_UNG_VIEN_HOP_LE: dict[str, tuple[str, ...]] = {
    "array": ("array", "str"),
    "str": ("str", "array"),
    "int": ("int",),
    "float": ("float", "int"),
    "bool": ("bool",),
    # `matrix`/`map`/`set`/`graph`/`tree_node` cố ý KHÔNG có ứng viên: chúng
    # thường được mô tả bằng văn xuôi, và đoán span cho chúng là đúng thứ
    # `RULES §3b` gọi là provenance toàn diện.
}


def _chon_ung_vien(
    cands: tuple[LiteralCandidate, ...],
    fact_kind: str,
    label: str,
    fid: str,
    da_dung: set[int],
) -> LiteralCandidate | None:
    """Literal nào trong đề nên lấp vào một fact mà `analyze` bỏ trống?

    Hai bậc ưu tiên, và không có bậc thứ ba đoán mò: khớp NHÃN trước (`n = 10`
    lấp đúng fact tên `n`), rồi mới tới thứ tự xuất hiện trong đề.
    """
    nhan = _UNG_VIEN_HOP_LE.get(fact_kind, ())
    if not nhan:
        return None
    ung = [
        c for i, c in enumerate(cands)
        if i not in da_dung and c.kind in nhan
    ]
    if not ung:
        return None
    khoa = {fid.lower(), label.lower()}
    for c in ung:
        if c.label_hint and c.label_hint.lower() in khoa:
            return c
    return ung[0]


def _gia_tri_khong_chung_minh_duoc(
    values: tuple[Any, ...],
    cands: tuple[LiteralCandidate, ...],
    problem_text: str,
) -> tuple[Any, ...]:
    """Trong những giá trị `analyze` khai, cái nào đề KHÔNG hề có?

    Hai luật, cố ý khác chặt-lỏng theo mức mà extractor thật sự phủ được:

    - **số và boolean** — extractor phủ TRỌN hai lớp này, nên vắng mặt trong mọi
      span đồng nghĩa với bịa. Xét chặt.
    - **chuỗi** — chỉ đòi nó xuất hiện đâu đó trong đề dưới dạng chuỗi con. Đủ
      để bắt giá trị dựng đứng ("mảng [5, 3, 9]" trong khi đề không có số nào),
      mà không từ chối oan nhãn rút từ văn xuôi (tên đỉnh đồ thị, tên thành
      phố), vốn là dữ liệu thật của đề nhưng không phải literal có cú pháp.
    """
    trong_span: set[Any] = set()
    for c in cands:
        for v in gia_tri_kem_ky_tu(c):
            trong_span.add(v)

    thieu: list[Any] = []
    for v in values:
        if isinstance(v, bool) or isinstance(v, (int, float)):
            if v not in trong_span:
                thieu.append(v)
        elif isinstance(v, str):
            if v not in trong_span and v not in problem_text:
                thieu.append(v)
    return tuple(thieu)


def build_request_contract(
    payload: dict[str, Any], problem_text: str = ""
) -> RequestContract:
    """Đóng băng đầu ra của `analyze` thành hợp đồng BẤT BIẾN.

    Lọc tại đây, không tin nguyên lời LLM:
    - nghĩa vụ có `kind` ngoài taxonomy đã đóng băng → **loại**;
    - mục dữ liệu thiếu `id` → **loại** (không có id thì P2 không ghim được).

    ─── MERGE P1 (vNext) ─────────────────────────────────────────────────────

    `problem_text` là TUỲ CHỌN và mặc định rỗng — mọi đường gọi cũ giữ nguyên
    hành vi, fact ra với `provenance="unchecked"`. Có `problem_text` thì thêm
    một nguồn thứ hai, tất định, và nó **thắng ở đúng một chỗ**:

        `analyze` bỏ trống giá trị + đề có literal chứng minh được
        ⇒ server lấy literal của đề.

    Ngoài chỗ đó, `analyze` vẫn sở hữu mọi thứ nó vốn sở hữu — nhãn, kind, vai
    trò, nghĩa vụ. Extractor không có ý kiến gì về ngữ nghĩa; nó chỉ trả lời
    "đoạn văn bản này có thật trong đề, ở đây".

    Chiều ngược lại cũng được ghi nhận chứ không im lặng: `analyze` khai một giá
    trị mà đề không có bằng chứng ⇒ fact mang `provenance="claimed"` kèm
    `unproven_values`, để cổng phía sau có cái mà từ chối. Đây chính là lỗ hổng
    mà `request_contract.py` tự khai trong docstring của nó — hợp đồng chặn được
    "chương trình sửa đề cho vừa mình", nhưng không chặn được "đề bị khai sai
    ngay từ đầu".
    """
    cands = extract_literals(problem_text) if problem_text else ()
    da_dung: set[int] = set()

    facts: list[InputFact] = []
    for raw in payload.get("input_facts") or ():
        if not isinstance(raw, dict):
            continue
        fid = raw.get("id")
        if not isinstance(fid, str) or not fid:
            continue
        label = str(raw.get("label") or fid)
        kind = raw.get("kind") if raw.get("kind") in INPUT_FACT_KINDS else "str"
        values = _as_values(raw.get("value"))

        provenance = "unchecked"
        s_start = s_end = None
        s_text = None
        chua_chung_minh: tuple[Any, ...] = ()

        if problem_text:
            if not values:
                c = _chon_ung_vien(cands, kind, label, fid, da_dung)
                if c is not None:
                    da_dung.add(cands.index(c))
                    values = gia_tri_kem_ky_tu(c)
                    provenance = "extracted"
                    s_start, s_end, s_text = c.source_start, c.source_end, c.source_text
                else:
                    provenance = "confirmed"  # không khai gì, không bịa gì
            else:
                chua_chung_minh = _gia_tri_khong_chung_minh_duoc(
                    values, cands, problem_text
                )
                provenance = "claimed" if chua_chung_minh else "confirmed"
                khop = [
                    c for c in cands
                    if any(v in gia_tri_kem_ky_tu(c) for v in values)
                ]
                if khop:
                    c = khop[0]
                    s_start, s_end, s_text = c.source_start, c.source_end, c.source_text

        facts.append(
            InputFact(
                fact_id=fid,
                label=label,
                values=values,
                provenance=provenance,
                source_start=s_start,
                source_end=s_end,
                source_text=s_text,
                unproven_values=chua_chung_minh,
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
