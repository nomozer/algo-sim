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


def _vi_tu_kiem_duoc() -> list[str]:
    """Tập vị từ mà server CÓ bộ kiểm độc lập — dẫn xuất, không chép tay.

    Nhập trễ (trong hàm) để tránh vòng phụ thuộc: `postconditions` đọc
    `obligations`, còn module này đọc cả hai.

    Hai nguồn, hai loại chủ thể: `PREDICATE_CHECKERS` cho chủ thể TẬP HỢP
    (`balanced_delimiters`), `_PREDS` cho chủ thể VÔ HƯỚNG (even/odd/gt/…).
    Gộp lại vì với người khai nghĩa vụ thì đó chỉ là một câu hỏi: *tôi được
    phép gọi tên vị từ nào?*
    """
    from .postconditions import _PREDS, PREDICATE_CHECKERS

    return sorted(set(PREDICATE_CHECKERS) | set(_PREDS))


_VI_TU_KIEM_DUOC = _vi_tu_kiem_duoc()


def _schema(
    obligation_kinds: list[str],
    fact_kinds: tuple[str, ...],
    co_prescribed: bool,
) -> dict[str, Any]:
    """Dựng schema `analyze` cho MỘT miền.

    VÌ SAO THAM SỐ HOÁ thay vì viết hai schema: hai bản rời nhau sẽ lệch ở lần
    sửa tiếp theo, và lệch câm. Chỉ ba thứ khác nhau giữa hai miền — enum nghĩa
    vụ, bảng kiểu dữ kiện, và việc có `prescribed_procedure` hay không (đề hình
    học không "ép thuật toán", nên trường ấy vắng mặt chứ không để rỗng).
    """
    props: dict[str, Any] = {
        # Dữ liệu đề cho, MỖI MỤC CÓ ID BỀN. `id` là thứ mà literal trong IR
        # phải THAM CHIẾU tới — ghim *cái nào*, không phải *có tồn tại đâu đó*
        # (chuỗi provenance P2, spec §3.4).
        "input_facts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "kind": {"type": "STRING", "enum": list(fact_kinds)},
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
                    "kind": {"type": "STRING", "enum": obligation_kinds},
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
                    # VỊ TỪ — enum, không phải chuỗi tự do.
                    #
                    # ĐO ĐƯỢC (live 2026-08-24): đề chuỗi ngoặc đi trọn tới C₂,
                    # `executable=True`, rồi rơi mức yếu chỉ vì nghĩa vụ không
                    # kèm `pred`. Không phải mô hình lười — trường này là STRING
                    # tự do, nên **nó chưa bao giờ được cho biết có những vị từ
                    # nào**. Bắt ai đó gọi đúng tên một thứ chưa từng được giới
                    # thiệu thì im lặng là kết cục đương nhiên.
                    #
                    # Liệt kê ở đây = liệt kê ĐÚNG tập KIỂM ĐƯỢC, dẫn xuất từ
                    # chính hai registry chứ không chép tay: thêm một checker là
                    # từ vựng analyze tự rộng ra, không có chỗ nào lệch.
                    "pred": {
                        "type": "STRING",
                        "nullable": True,
                        "enum": _VI_TU_KIEM_DUOC,
                        "description": "Tên vị từ cho `predicate_verdict`. Chỉ "
                                       "dùng tên trong danh sách; vị từ ngoài "
                                       "danh sách sẽ không kiểm chứng được.",
                    },
                    # ── ĐẠI LƯỢNG MONG ĐỢI (miền hình học) ─────────────────
                    #
                    # `check_distance`/`check_volume` đọc `params["value"]`,
                    # `check_angle` đọc `params["cos_sq"]`. Không có hai trường
                    # này trong schema thì chúng LUÔN `None`, và ba checker đại
                    # lượng luôn trả `None` = "chỉ kiểm được cấu trúc" — tức ba
                    # nghĩa vụ nằm trong bảng mà chưa từng kiểm được lần nào.
                    #
                    # `cos_sq` chứ không phải số đo độ: góc hình học phần lớn vô
                    # tỉ, còn `cos²` của nó hữu tỉ. So trên `cos²` giữ được phép
                    # so BẰNG chính xác, không cần epsilon.
                    "value": {"type": "STRING", "nullable": True},
                    "cos_sq": {"type": "STRING", "nullable": True},
                    # ĐỐI TƯỢNG THỨ HAI của phép đo, khi `witness` là một CON
                    # SỐ. Không có nó thì cổng C₂ biết con số nhưng không biết
                    # nó đo giữa cái gì với cái gì, nên chỉ kiểm được cấu trúc.
                    "wrt": {"type": "STRING", "nullable": True},
                },
                # `value`/`cos_sq` KHÔNG bắt buộc: đề bảo *tính* thì không có
                # đáp số để khai, và ép khai là mời mô hình tự cho điểm mình.
                "required": ["kind", "container", "witness"],
            },
        },
    }
    if co_prescribed:
        props["prescribed_procedure"] = {
            "type": "STRING",
            "enum": sorted(SEMANTIC_PRESCRIBED_PROCEDURES),
            "nullable": True,
        }
    return {
        "type": "OBJECT",
        "properties": props,
        "required": ["input_facts", "obligations"],
    }


def analyze_schema_for(domain: str) -> dict[str, Any]:
    """Schema `analyze` của một miền. Enum nghĩa vụ HẸP theo miền.

    Đây là chỗ lỗ Phase 5 được bịt: bài hình học không còn nhìn thấy
    `derived_sequence` hay `structural_traversal` trong danh sách chọn.
    """
    from .domain_profile import (
        DOMAIN_HINH_HOC,
        INPUT_FACT_KINDS_HINH_HOC,
        obligation_kinds_for,
    )

    la_hh = domain == DOMAIN_HINH_HOC
    return _schema(
        obligation_kinds=sorted(obligation_kinds_for(domain)),
        fact_kinds=INPUT_FACT_KINDS_HINH_HOC if la_hh else INPUT_FACT_KINDS,
        co_prescribed=not la_hh,
    )


#: Giữ tên cũ = giữ nguyên mọi đường gọi Tin học đã có.
SEMANTIC_ANALYZE_SCHEMA: dict[str, Any] = _schema(
    obligation_kinds=sorted(OBLIGATION_KINDS),
    fact_kinds=INPUT_FACT_KINDS,
    co_prescribed=True,
)

#: `value`/`cos_sq` là ĐẠI LƯỢNG MONG ĐỢI của ba nghĩa vụ hình học. Thiếu chúng
#: ở đây thì `check_distance`/`check_angle`/`check_volume` đọc `params` ra `None`
#: và luôn rơi mức yếu — nghĩa vụ có checker mà checker không bao giờ so gì.
_PARAM_KEYS = ("witness", "cmp", "op", "transform", "pred", "item", "order",
               "src", "domain", "value", "cos_sq", "wrt")


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
    payload: dict[str, Any], problem_text: str = "", domain: str | None = None
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

    ─── `domain` (Wave 2, 2026-08-24) ───────────────────────────────────────

    `None` = **không lọc theo miền** — đúng hành vi cũ, mọi đường gọi Tin học
    giữ nguyên. Truyền một miền vào thì server loại cả nghĩa vụ *hợp lệ trong
    taxonomy nhưng SAI MIỀN*. Đây là tầng chặn thứ hai sau enum của schema:
    enum là lời đề nghị gửi cho model, còn đây là thứ cưỡng chế. Phase 5 cho
    thấy vì sao cần cả hai — model khai `derived_sequence` cho một bài hình
    học, và không có tầng nào từ chối nó.
    """
    from .domain_profile import obligation_kinds_for

    cho_phep = obligation_kinds_for(domain) if domain else None
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
        if cho_phep is not None and kind not in cho_phep:
            continue  # trong taxonomy nhưng SAI MIỀN
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
