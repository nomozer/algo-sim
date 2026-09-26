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
from .scale_normalization import chuan_hoa_thang
from .structured_relations import RELATION_KINDS, GeometricRelation

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


#: Quy ước ĐẶT TÊN của miền Tin học — chữ thường, snake_case.
MO_TA_TEN_TIN_HOC = (
    "Tên biến kiểu snake_case, chỉ chữ thường không dấu, số và gạch dưới. "
    "KHÔNG viết cụm từ hay câu."
)
MO_TA_WITNESS_TIN_HOC = (
    "Tên biến kiểu snake_case sẽ chứa câu trả lời. KHÔNG viết cụm từ hay câu."
)

#: Quy ước ĐẶT TÊN của miền hình học — **KHÔNG** snake_case.
#:
#: ─── ĐO ĐƯỢC Ở PHASE 5.5 (`5f42363`), `geo_01` ──────────────────────────────
#:
#: Hợp đồng khai `witness = 'm'`; chương trình khai `M`. C₁a từ chối, và cả hai
#: lượt LLM đều **làm đúng luật được giao**: mô tả trường này bắt snake_case
#: (đúng ở miền Tin học), còn hình học gọi tên điểm bằng CHỮ HOA — `A`, `B`,
#: `M`, `S` — nên lượt viết chương trình cũng theo đúng quy ước miền nó.
#:
#: Hai luật mâu thuẫn, không tầng nào hoà giải. Đây là NGUỒN, và sửa ở nguồn
#: thì không thể sinh khớp sai; mọi bộ khớp thêm vào chỉ là lưới an toàn.
MO_TA_TEN_HINH_HOC = (
    "Ký hiệu của đối tượng, viết ĐÚNG NHƯ ĐỀ BÀI. Hình học dùng CHỮ HOA cho "
    "điểm (`A`, `M`, `S`), và tên mặt phẳng/khối cũng giữ nguyên ký hiệu "
    "(`abcd`, `sabcd`). ĐỪNG hạ về chữ thường, đừng đổi sang snake_case."
)
MO_TA_WITNESS_HINH_HOC = (
    "Ký hiệu của thứ mang câu trả lời, viết ĐÚNG NHƯ ĐỀ BÀI — điểm thì CHỮ HOA "
    "(`M`, `H`). Với nghĩa vụ đại lượng (distance/angle/volume) thì đây là tên "
    "biến chứa con số. ĐỪNG hạ về chữ thường. "
    "Nghĩa vụ không có witness (ví dụ `section_matches`, vốn nhận hai toán hạng "
    "qua `solid` và `plane`) thì đặt witness = null — ĐỪNG viết chuỗi \"null\"."
)


def _schema(
    obligation_kinds: list[str],
    fact_kinds: tuple[str, ...],
    co_prescribed: bool,
    mo_ta_container: str = MO_TA_TEN_TIN_HOC,
    mo_ta_witness: str = MO_TA_WITNESS_TIN_HOC,
    co_quan_he: bool = False,
) -> dict[str, Any]:
    """Dựng schema `analyze` cho MỘT miền.

    VÌ SAO THAM SỐ HOÁ thay vì viết hai schema: hai bản rời nhau sẽ lệch ở lần
    sửa tiếp theo, và lệch câm. Chỉ bốn thứ khác nhau giữa hai miền — enum nghĩa
    vụ, bảng kiểu dữ kiện, việc có `prescribed_procedure` hay không (đề hình
    học không "ép thuật toán", nên trường ấy vắng mặt chứ không để rỗng), và
    việc có `geometric_relations` hay không (quan hệ vuông góc là khái niệm của
    riêng miền hình học — cho Tin học nhìn thấy nó là mời khai một thứ vô nghĩa,
    và làm lược đồ Tin học đổi byte mà không ai được lợi).
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
                        "description": mo_ta_container,
                    },
                    # NULLABLE, và vẫn nằm trong `required` — hai điều kiện,
                    # mỗi điều kiện chặn một kiểu hỏng khác nhau.
                    #
                    # `nullable` vì có nghĩa vụ KHÔNG CÓ witness
                    # (`WITNESS_FREE_KINDS`). Trước 2026-08-30 trường này là
                    # `STRING` không nullable và nằm trong `required`, nên
                    # structured output **không cho mô hình cách hợp lệ nào để
                    # nói "không có"** — lượt live `geo_03` cho ra chuỗi
                    # `"null"`, rồi C₁a bác vì `null` không phải tên biến nào.
                    # Câu trả lời đúng mà không biểu diễn được thì đó là lỗi
                    # của hợp đồng, không phải của mô hình.
                    #
                    # Vẫn GIỮ trong `required` vì bỏ ra thì mô hình được phép
                    # im lặng bỏ qua witness ở những kind THẬT SỰ cần — và
                    # "quên" với "không có" lại trở thành cùng một hình dạng,
                    # đúng chỗ mù vừa dọn.
                    "witness": {
                        "type": "STRING",
                        "nullable": True,
                        "description": mo_ta_witness,
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
                    # ── HAI TOÁN HẠNG CỦA `section_matches` ────────────────
                    #
                    # Thiếu chúng ở đây thì `check_section_matches` đọc
                    # `params["solid"]`/`params["plane"]` ra `None` và LUÔN trả
                    # `None` = mức yếu. Tức nghĩa vụ có checker mạnh nhất của
                    # miền hình học mà **chưa từng chấm được lần nào qua đường
                    # sản phẩm** — cùng đúng lớp lỗi "kernel có, cầu nối
                    # không" đã bắt ở `distance` và ở chính `section_matches`.
                    #
                    # Lấy từ ĐỀ, không từ chương trình: checker dựng lại thiết
                    # diện chuẩn từ hai toán hạng này rồi so với cái chương
                    # trình tạo ra. Lấy từ chương trình là một tautology.
                    "solid": {"type": "STRING", "nullable": True},
                    "plane": {"type": "STRING", "nullable": True},
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
    if co_quan_he:
        props["geometric_relations"] = _luoc_do_quan_he()
        props["solid_topology"] = _luoc_do_solid_topology()
    return {
        "type": "OBJECT",
        "properties": props,
        "required": ["input_facts", "obligations"],
    }


def _luoc_do_quan_he() -> dict[str, Any]:
    """Ô `geometric_relations` — quan hệ vuông góc dưới dạng CÓ KIỂU.

    ⚠️ **Một nguồn định nghĩa trường duy nhất.** `enum` dẫn từ
    `structured_relations.RELATION_KINDS`, arity dẫn từ `SO_DIEM_*`. Chép tay
    một bảng thứ hai ở đây là cách hai bề mặt lệch nhau một cách câm — đúng thứ
    `_schema` được tham số hoá để tránh.

    Không có `source_text`, không có ô tự do nào: trường này tồn tại để **thay**
    câu tiếng Việt, nên cho nó một ô chở câu tiếng Việt là làm hỏng chính nó.
    """
    from .structured_relations import (
        RELATION_KINDS, SO_DIEM_DUONG, SO_DIEM_MAT,
    )

    def _diem(n: int, mo_ta: str) -> dict[str, Any]:
        return {"type": "ARRAY", "items": {"type": "STRING"},
                "minItems": n, "maxItems": n, "description": mo_ta}

    return {
        "type": "ARRAY",
        "description": (
            "Quan hệ VUÔNG GÓC đề cho, dưới dạng có cấu trúc. Khai ở đây thì "
            "khỏi khai lại thành câu trong `input_facts`."),
        "items": {
            "type": "OBJECT",
            "properties": {
                "kind": {"type": "STRING", "enum": list(RELATION_KINDS)},
                "line": _diem(SO_DIEM_DUONG,
                              "Hai đỉnh của đường thẳng thứ nhất. Thứ tự "
                              "không quan trọng."),
                "other_line": _diem(SO_DIEM_DUONG,
                                    "Hai đỉnh của đường thẳng thứ hai. CHỈ "
                                    "dùng với `perpendicular_lines`."),
                "plane": _diem(SO_DIEM_MAT,
                               "Ba đỉnh xác định mặt phẳng. CHỈ dùng với "
                               "`perpendicular_line_plane`."),
                # Bắt buộc ghim về một mục `input_facts`: không có nó thì quan
                # hệ không truy được về đề, và tầng dựng phải từ chối nó.
                "source_fact_id": {"type": "STRING", "nullable": True},
                # Mô hình TỰ SUY, đề không nói. Không có ô này thì một giả định
                # và một dữ kiện có cùng hình dạng — đúng chỗ mù cần bịt.
                "model_assumption": {"type": "BOOLEAN", "nullable": True},
            },
            "required": ["kind", "line", "source_fact_id"],
        },
    }


def _luoc_do_solid_topology() -> dict[str, Any]:
    """Ô `solid_topology` model-facing — hỗ trợ lăng trụ đứng và hình chóp."""
    return {
        "type": "OBJECT",
        "description": "Cấu trúc tô-pô của khối đa diện (lăng trụ đứng hoặc hình chóp có đáy phẳng).",
        "properties": {
            "solid_kind": {
                "type": "STRING",
                "enum": ["prism", "pyramid"],
                "description": "Loại khối đa diện ('prism' cho lăng trụ, 'pyramid' cho chóp).",
            },
            "apex": {
                "type": "STRING",
                "description": "Đỉnh chóp (bắt buộc đối với pyramid, vd 'S').",
            },
            "base_cycle": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Chu trình đỉnh đáy theo thứ tự vòng quanh, vd ['A', 'B', 'C', 'D'].",
            },
            "base_shape": {
                "type": "STRING",
                "enum": ["rectangle", "square"],
                "description": "Dạng hình học của đáy nếu xác định được ('rectangle' hoặc 'square').",
            },
            "lateral_structure": {
                "type": "STRING",
                "enum": ["right", "oblique"],
                "description": "Cấu trúc cạnh bên ('right' cho lăng trụ đứng, 'oblique' cho lăng trụ xiên).",
            },
            "solid_subkind": {
                "type": "STRING",
                "enum": ["cuboid", "cube", "right_square_prism"],
                "description": "Phân loại chuyên biệt của khối lăng trụ: 'cuboid' (hình hộp chữ nhật), 'cube' (hình lập phương), 'right_square_prism' (lăng trụ đứng đáy vuông).",
            },
            "source_grounding": {
                "type": "STRING",
                "description": "Căn cứ từ ngữ trong đề bài xác nhận phân loại (vd 'hình lập phương', 'hình hộp chữ nhật', 'lăng trụ đứng').",
            },
            "top_cycle": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Chu trình đỉnh đáy trên (chỉ dành cho prism), vd ['D', 'E', 'F'] hoặc ['A\'', 'B\'', 'C\'', 'D\''].",
            },
            "correspondence": {
                "type": "ARRAY",
                "items": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "description": "Cặp đỉnh tương ứng của cạnh bên giữa đáy dưới và đáy trên (chỉ dành cho prism), vd [['A', 'A\''], ['B', 'B\''], ['C', 'C\''], ['D', 'D\'']].",
            },
        },
        "required": ["solid_kind", "base_cycle"],
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
        mo_ta_container=MO_TA_TEN_HINH_HOC if la_hh else MO_TA_TEN_TIN_HOC,
        mo_ta_witness=(MO_TA_WITNESS_HINH_HOC if la_hh
                       else MO_TA_WITNESS_TIN_HOC),
        co_quan_he=la_hh,
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
               "src", "domain", "value", "cos_sq", "wrt", "solid", "plane")

#: Tham số TRỎ TỚI MỘT VẬT trong chương trình — C₁a tra chúng trong bảng ký
#: hiệu, C₂ tra chúng trong bộ nhớ cuối. Khác hẳn `value`/`cos_sq` (con số) và
#: `cmp`/`op`/`pred` (từ khoá).
_THAM_SO_LA_TEN = ("witness", "wrt", "solid", "plane")

#: Những chuỗi KHÔNG BAO GIỜ là tên một vật.
#:
#: Đây KHÔNG phải bản vá cho một ca cụ thể. Luật là: tham số ở
#: `_THAM_SO_LA_TEN` phải là một ĐỊNH DANH mà chương trình khai được. Không
#: chương trình nào khai một biến tên `null` — nên nhận chuỗi ấy làm tên là
#: nhận một tên chắc chắn tra không ra, rồi bác ở tầng sau với thông điệp
#: *"witness 'null' chưa khai báo"*, che mất nguyên nhân thật.
#:
#: Sau khi `witness` thành `nullable`, mô hình có đường hợp lệ để nói "không
#: có". Bảng này là **lưới an toàn cho envelope cũ và cho lượt mô hình bướng**,
#: không phải cách chữa chính — cách chữa chính là schema.
_TEN_RONG = frozenset({"null", "none", "nil", "undefined", "n/a", "na", "-", ""})


def _canonical_ten(raw: Any) -> str | None:
    """Chuỗi → tên vật, hoặc `None` nếu nó không thể là một cái tên."""
    if not isinstance(raw, str):
        return None
    ten = raw.strip()
    return None if ten.casefold() in _TEN_RONG else (ten or None)


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


def _doc_quan_he(payload: dict[str, Any]) -> tuple[GeometricRelation, ...]:
    """`analyze.geometric_relations` → model đã đóng băng. LỌC, không tin nguyên lời.

    Cùng kỷ luật với vòng `obligations` ngay dưới: `kind` ngoài bảng đóng bị
    loại **tại đây**, chỗ duy nhất còn biết nó đến từ `analyze`.

    ⚠️ Chỉ lọc thứ **không biểu diễn được**. Suy biến và tham chiếu lạ KHÔNG bị
    nuốt ở đây — chúng đi tiếp để `structured_relations.kiem_va_chuan_hoa` từ
    chối bằng **mã ổn định**. Nuốt ở biên thì tầng dựng thấy một hợp đồng
    *thiếu* thay vì một hợp đồng *hỏng*, và hai thứ ấy cần hai lời đáp khác nhau.
    """
    ra: list[GeometricRelation] = []
    for raw in payload.get("geometric_relations") or ():
        if not isinstance(raw, dict):
            continue
        if raw.get("kind") not in RELATION_KINDS:
            continue

        def _diem(khoa: str) -> tuple[str, ...]:
            v = raw.get(khoa)
            return tuple(str(x) for x in v) if isinstance(v, (list, tuple)) else ()

        sfid = raw.get("source_fact_id")
        ra.append(GeometricRelation(
            kind=str(raw["kind"]),
            line=_diem("line"),
            other_line=_diem("other_line"),
            plane=_diem("plane"),
            source_fact_id=str(sfid) if isinstance(sfid, str) and sfid else None,
            model_assumption=bool(raw.get("model_assumption")),
        ))
    return tuple(ra)


def _doc_solid_topology(payload: dict[str, Any]):
    raw_topo = payload.get("solid_topology")
    if raw_topo is None:
        return None
    if not isinstance(raw_topo, dict):
        raise ValueError("solid_topology phải là một đối tượng dict")
    skind = raw_topo.get("solid_kind")
    if skind == "pyramid":
        apex = raw_topo.get("apex")
        base = raw_topo.get("base_cycle")
        bshape = raw_topo.get("base_shape")
        if not apex or not base:
            raise ValueError("solid_topology của pyramid thiếu apex hoặc base_cycle")
        if not isinstance(apex, str) or not apex.strip():
            raise ValueError("apex của pyramid phải là chuỗi không rỗng")
        if not isinstance(base, (list, tuple)) or len(base) < 3:
            raise ValueError("base_cycle của pyramid phải là danh sách ít nhất 3 đỉnh")
        base_tuple = tuple(str(x) for x in base)
        if len(set(base_tuple)) != len(base_tuple):
            raise ValueError("Chu trình đáy không được chứa đỉnh lặp")
        if apex in base_tuple:
            raise ValueError("Đỉnh chóp không được nằm trong chu trình đáy")
        if bshape is not None and bshape not in ("rectangle", "square"):
            raise ValueError("base_shape phải là 'rectangle' hoặc 'square'")
        from .request_contract import PyramidTopologySpec
        return PyramidTopologySpec(
            solid_kind="pyramid",
            apex=str(apex),
            base_cycle=base_tuple,
            base_shape=bshape,
        )

    if skind != "prism":
        raise ValueError(f"solid_kind '{skind}' không được hỗ trợ trong wave này (chỉ 'prism' hoặc 'pyramid')")
    base = raw_topo.get("base_cycle")
    top = raw_topo.get("top_cycle")
    corr = raw_topo.get("correspondence")
    if not base or not top or not corr:
        raise ValueError("solid_topology thiếu base_cycle, top_cycle hoặc correspondence")
    if len(base) < 3 or len(top) < 3:
        raise ValueError("base_cycle và top_cycle phải có ít nhất 3 đỉnh")
    if len(base) != len(top):
        raise ValueError("base_cycle và top_cycle phải có cùng số lượng đỉnh")
    if len(set(base)) != len(base) or len(set(top)) != len(top):
        raise ValueError("Chu trình đáy không được chứa đỉnh lặp")
    if set(base) & set(top):
        raise ValueError("Trùng đỉnh giữa chu trình đáy dưới và đáy trên")

    parsed_corr: list[tuple[str, str]] = []
    for pair in corr:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("Mỗi cặp trong correspondence phải có đúng 2 đỉnh")
        parsed_corr.append((str(pair[0]), str(pair[1])))

    corr_dict = dict(parsed_corr)
    if len(corr_dict) != len(base) or set(corr_dict.keys()) != set(base):
        raise ValueError("Correspondence không phải song ánh từ đáy dưới sang đáy trên")
    if set(corr_dict.values()) != set(top):
        raise ValueError("Ảnh của correspondence không khớp với các đỉnh đáy trên")

    base_shape = raw_topo.get("base_shape")
    lateral_structure = raw_topo.get("lateral_structure") or "right"
    solid_subkind = raw_topo.get("solid_subkind") or raw_topo.get("prism_variant")
    source_grounding = raw_topo.get("source_grounding")

    if base_shape is not None and base_shape not in ("rectangle", "square"):
        raise ValueError(f"base_shape '{base_shape}' không hợp lệ (chỉ 'rectangle' hoặc 'square')")
    if lateral_structure not in ("right", "oblique"):
        raise ValueError(f"lateral_structure '{lateral_structure}' không hợp lệ (chỉ 'right' hoặc 'oblique')")
    if solid_subkind is not None and solid_subkind not in ("cuboid", "cube", "right_square_prism"):
        raise ValueError(f"solid_subkind '{solid_subkind}' không hợp lệ")

    if solid_subkind == "cube":
        if len(base) != 4:
            raise ValueError("Hình lập phương phải có đáy 4 đỉnh")
        if base_shape is not None and base_shape != "square":
            raise ValueError("Hình lập phương phải có đáy hình vuông")
        if lateral_structure == "oblique":
            raise ValueError("Hình lập phương phải có cạnh bên vuông góc đáy")
        base_shape = "square"
    elif solid_subkind == "cuboid":
        if len(base) != 4:
            raise ValueError("Hình hộp chữ nhật phải có đáy 4 đỉnh")
        if base_shape is not None and base_shape not in ("rectangle", "square"):
            raise ValueError("Hình hộp chữ nhật phải có đáy hình chữ nhật hoặc hình vuông")
        if lateral_structure == "oblique":
            raise ValueError("Hình hộp chữ nhật phải có cạnh bên vuông góc đáy")
        if base_shape is None:
            base_shape = "rectangle"
    elif solid_subkind == "right_square_prism":
        if len(base) != 4:
            raise ValueError("Lăng trụ đứng đáy vuông phải có đáy 4 đỉnh")
        if base_shape is not None and base_shape != "square":
            raise ValueError("Lăng trụ đứng đáy vuông phải có đáy hình vuông")
        if lateral_structure == "oblique":
            raise ValueError("Lăng trụ đứng phải có cạnh bên vuông góc đáy")
        base_shape = "square"

    from .request_contract import PrismTopologySpec
    return PrismTopologySpec(
        base_cycle=tuple(str(x) for x in base),
        top_cycle=tuple(str(x) for x in top),
        correspondence=tuple(parsed_corr),
        base_shape=base_shape,
        lateral_structure=lateral_structure,
        solid_subkind=solid_subkind,
        source_grounding=str(source_grounding) if source_grounding else None,
    )


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
        # Tham số TRỎ TỚI MỘT VẬT phải là một cái tên. Chuỗi `"null"` không
        # phải tên nào cả — bỏ nó ở BIÊN, chỗ duy nhất còn biết nó đến từ
        # analyze. Để nó đi tiếp thì C₁a bác bằng thông điệp *"witness 'null'
        # chưa khai báo"*, và người đọc đi tìm một biến không hề tồn tại.
        for k in _THAM_SO_LA_TEN:
            if k in params and _canonical_ten(params[k]) is None:
                del params[k]
        obligations.append(
            Obligation(kind=kind, container=container, params=params)
        )

    hd = RequestContract(
        obligations=tuple(obligations), input_facts=tuple(facts),
        geometric_relations=_doc_quan_he(payload),
        solid_topology=_doc_solid_topology(payload),
        # Giữ đề bài lại: nó là thẩm quyền của câu "thứ này có trong đề không".
        problem_text=problem_text or "",
    )
    # ── CHUẨN HOÁ THANG — SERVER quyết, và quyết TRƯỚC khi mô hình nhìn thấy ─
    #
    # Đặt ở cuối `build_request_contract` chứ không ở pipeline là có chủ đích:
    # đây là biên đóng băng hợp đồng, nên MỌI đường gọi — pipeline live, bộ
    # chấm DEV, test — đều thấy cùng một hợp đồng. Đặt ở pipeline thì hai đường
    # nhìn hai bản khác nhau, đúng lớp lỗi "một cổng mới đọc dữ liệu thô" đã
    # vấp sáu lần.
    #
    # Chỉ hình học: ở Tin học một chuỗi `"a"` là DỮ LIỆU ĐỀ CHO, không phải
    # tham số tỉ lệ, và viết lại nó thành `1` là phá đúng bài toán.
    from .domain_profile import DOMAIN_HINH_HOC

    if domain == DOMAIN_HINH_HOC:
        hd = chuan_hoa_thang(hd, problem_text)
        hd = gan_bat_bien_nguon(hd, problem_text)
    return hd


def gan_bat_bien_nguon(hd: RequestContract, problem_text: str | None
                       ) -> RequestContract:
    """Chạy MỌI bộ phát bất biến nguồn rồi ghép vào hợp đồng. Một thẩm quyền.

    ─── VÌ SAO LÀ MỘT HÀM CÓ TÊN, KHÔNG PHẢI MỘT KHỐI INLINE ──────────────

    Tách ra 2026-09-08 (`POINT_COORDINATE_SOURCE_INVARIANT`), và lý do đo được
    ngay trong wave ấy: replay của bộ đo dựng `RequestContract` **thẳng**, nên
    nó không đi qua biên đóng băng và **không thấy bất biến nào**. Bản vá đúng
    mà replay báo *"không đổi gì"* — đúng lớp lỗi kho gọi tên là *"một sửa
    chữa không nằm trên đường chạy thật"*.

    Cách chữa KHÔNG phải chép danh sách bộ phát sang bộ đo: chép là dựng bản
    thứ hai, và bản thứ hai sẽ quên bộ phát tiếp theo. Cách chữa là để cả sản
    phẩm lẫn bộ đo gọi CÙNG hàm này.

    ─── THỨ TỰ CÓ NGHĨA, VÀ LÀ THỨ TỰ CỘNG DỒN ────────────────────────────

    CỘNG THÊM, không ghi đè: một đề có thể vừa buộc thang, vừa chia đoạn, vừa
    cho toạ độ — mất một trong số đó là mở lại đúng lỗ vừa đóng.

    · ĐỘ DÀI trước, CHIA ĐOẠN sau — *"đoạn ấy dài đúng chưa"* và *"điểm chia
      đúng chỗ chưa"* là hai câu khác nhau về cùng một hình. Thiếu câu đầu thì
      một hình đúng tỉ lệ mà SAI THANG vẫn được phục vụ
      (`FRAME_ORIGIN_PROVENANCE_AFFORDANCE` phản ví dụ ⓑ: `F = [99,0,0]` cho
      đề `EF = 10` ⇒ `served` với `396/5` thay vì `8`).
    · PHƯƠNG TRÌNH MẶT PHẲNG (2026-09-07) — bộ phát DUY NHẤT gác được
      `construct_plane_from_equation`: bốn hệ số của câu lệnh ấy là hằng, nên
      grounding — thứ chỉ soi `memory_declarations` — không hỏi chúng câu nào.
    · TOẠ ĐỘ ĐIỂM (2026-09-08) — bịt lỗ đo được ở
      `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY`: đề cho `B(6,0,0)`, chương
      trình khai `B(99,7,0)`, `source_fact_id` trỏ một fact CÓ THẬT ⇒ hệ phục
      vụ `V = 540` thay vì `45`. `source_fact_id` được kiểm SỰ TỒN TẠI, không
      kiểm SỰ KHỚP — và trước wave ấy không cổng nào hỏi câu còn lại.
    """
    from .plane_equation import bat_bien_mat_phang
    from .point_coordinate import bat_bien_toa_do
    from .segment_relation import bat_bien_chia_doan, bat_bien_do_dai

    them = (bat_bien_do_dai(hd, problem_text)
            + bat_bien_chia_doan(hd, problem_text)
            + bat_bien_mat_phang(hd, problem_text)
            + bat_bien_toa_do(hd, problem_text))
    if not them:
        return hd
    return hd.model_copy(update={
        "source_invariants": tuple(hd.source_invariants or ()) + them})
