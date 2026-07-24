# -*- coding: utf-8 -*-
"""M17 W2B-S1 — CHỮ KÝ MỤC TIÊU tất định (canonical goal signature).

Vấn đề đã đo được (fixture #10): "đếm tổ A **và** đếm tổ B" là HAI yêu cầu độc
lập, nhưng cả hai quy về cùng `table.aggregate/count` nên bị gộp thành một —
hệ trả `ok` và bỏ im lặng một phép đếm. Đó là mất mát ngữ nghĩa thật.

`SemanticRequirement.goal_id` đã có sẵn chỗ phân biệt, nhưng chưa có gì điền
vào. Module này sinh giá trị đó **bằng code tất định** từ các trường CÓ CẤU
TRÚC mà analyze khai — KHÔNG nhận id tự do do LLM tự đặt (id tự do thì hai cách
diễn đạt cùng một mục tiêu sẽ ra hai id khác nhau, gây từ chối oan; và LLM có
thể vô tình đặt trùng id cho hai mục tiêu khác nhau, gây mất mát ngữ nghĩa).

Yêu cầu với chữ ký (đúng §3):
- ổn định, KHÔNG phụ thuộc thứ tự khoá JSON;
- GIỮ kiểu của literal ("5" chuỗi ≠ 5 số);
- chuẩn hoá tên cột/toán tử theo hợp đồng;
- phân biệt hai vị từ khác nhau, hai cột tổng hợp khác nhau, hai truy vấn độc
  lập;
- KHÔNG chứa kết quả cuối (chữ ký mô tả YÊU CẦU, không mô tả đáp án).
"""

from __future__ import annotations

from typing import Any

# Trường mô tả MỤC TIÊU (đóng). Trường lạ bị bỏ qua — không để LLM mở rộng
# không gian chữ ký bằng khoá tự chế.
GOAL_FIELDS: tuple[str, ...] = (
    "filter_column", "filter_op", "filter_value",
    "aggregate_func", "aggregate_column",
    "projection_columns", "sort_column", "sort_direction", "limit",
)

# Toán tử viết bằng chữ → ký hiệu, để "lớn hơn" và ">" ra CÙNG chữ ký.
_OP_ALIASES: dict[str, str] = {
    "eq": "=", "equals": "=", "bang": "=", "=": "=",
    "ne": "!=", "neq": "!=", "khac": "!=", "!=": "!=", "<>": "!=",
    "gt": ">", "greater": ">", "lon_hon": ">", ">": ">",
    "gte": ">=", "ge": ">=", ">=": ">=", "=>": ">=",
    "lt": "<", "less": "<", "nho_hon": "<", "<": "<",
    "lte": "<=", "le": "<=", "<=": "<=", "=<": "<=",
    "contains": "contains", "chua": "contains",
}
_DIRECTION_ALIASES: dict[str, str] = {
    "asc": "asc", "ascending": "asc", "tang": "asc", "tang_dan": "asc",
    "desc": "desc", "descending": "desc", "giam": "desc", "giam_dan": "desc",
}


def _norm_ident(value: Any) -> str | None:
    """Tên cột: bỏ khoảng trắng thừa, hạ chữ. Hai cách viết cùng một cột ⇒ một
    chữ ký; hai cột khác nhau vẫn khác nhau."""
    if not isinstance(value, str):
        return None
    v = " ".join(value.split()).strip().lower()
    return v or None


def _norm_literal(value: Any) -> str | None:
    """Literal GIỮ KIỂU: 5 (số) ≠ "5" (chuỗi) ≠ True (bool).

    Chuỗi trông như số KHÔNG bị ép — analyze khai kiểu gì thì chữ ký ghi kiểu
    đó, còn việc ép kiểu theo lược đồ là việc của validator."""
    if value is None:
        return None
    if isinstance(value, bool):
        return f"b:{'1' if value else '0'}"
    if isinstance(value, (int, float)):
        # 6 và 6.0 là CÙNG một giá trị ⇒ cùng chữ ký
        f = float(value)
        return f"n:{int(f) if f.is_integer() else f}"
    if isinstance(value, str):
        v = " ".join(value.split()).strip()
        return f"s:{v.lower()}" if v else None
    return None


def _norm_op(value: Any) -> str | None:
    v = _norm_ident(value)
    return _OP_ALIASES.get(v) if v else None


def _norm_direction(value: Any) -> str | None:
    v = _norm_ident(value)
    return _DIRECTION_ALIASES.get(v) if v else None


def _norm_columns(value: Any) -> str | None:
    """Danh sách cột chiếu: THỨ TỰ KHÔNG quan trọng ⇒ sắp xếp trước khi ký."""
    if not isinstance(value, list):
        return None
    cols = sorted({c for c in (_norm_ident(x) for x in value) if c})
    return ",".join(cols) if cols else None


def canonical_goal_signature(goal: object) -> str | None:
    """Chữ ký ổn định của MỘT mục tiêu; None khi đề không nêu gì cụ thể.

    None nghĩa là "không phân biệt được" — KHÔNG phải "mục tiêu rỗng". Hai yêu
    cầu cùng chữ ký None sẽ gộp, đúng như hành vi trước S1 (tương thích ngược
    cho mọi family chưa khai mục tiêu có cấu trúc)."""
    if not isinstance(goal, dict):
        return None
    parts: list[str] = []

    fc, fo = _norm_ident(goal.get("filter_column")), _norm_op(goal.get("filter_op"))
    fv = _norm_literal(goal.get("filter_value"))
    if fc or fo or fv:
        parts.append(f"filter={fc or '?'}|{fo or '?'}|{fv or '?'}")

    af = _norm_ident(goal.get("aggregate_func"))
    if af:
        ac = _norm_ident(goal.get("aggregate_column"))
        # COUNT(*) phân biệt tường minh với COUNT(cột)
        parts.append(f"agg={af}|{ac or '*'}")

    proj = _norm_columns(goal.get("projection_columns"))
    if proj:
        parts.append(f"proj={proj}")

    sc, sd = _norm_ident(goal.get("sort_column")), _norm_direction(goal.get("sort_direction"))
    if sc:
        parts.append(f"sort={sc}|{sd or 'asc'}")

    limit = goal.get("limit")
    if isinstance(limit, int) and not isinstance(limit, bool) and limit > 0:
        parts.append(f"limit={limit}")

    # Sắp xếp ⇒ chữ ký KHÔNG phụ thuộc thứ tự khoá JSON analyze trả về.
    return ";".join(sorted(parts)) if parts else None


# Bề mặt CÔNG KHAI của hai phép chuẩn hoá trên — gate tầng pipeline (§A) phải
# đọc tên cột/chiều sắp xếp bằng ĐÚNG luật này, không viết lại lần thứ hai.
normalize_identifier = _norm_ident
normalize_direction = _norm_direction


def query_key(requirement_goal: object, declared_group: object = None) -> str | None:
    """Định danh TRUY VẤN mà một yêu cầu thuộc về.

    Ưu tiên `query_group` analyze khai tường minh (các tầng của cùng một truy
    vấn cùng nhóm); không có thì lùi về chữ ký mục tiêu. Cả hai đều None ⇒
    None (một truy vấn duy nhất, hành vi cũ)."""
    if isinstance(declared_group, int) and not isinstance(declared_group, bool):
        return f"g:{declared_group}"
    if isinstance(declared_group, str) and declared_group.strip():
        return f"g:{declared_group.strip().lower()}"
    return canonical_goal_signature(requirement_goal)


__all__ = ["GOAL_FIELDS", "canonical_goal_signature", "normalize_direction",
           "normalize_identifier", "query_key"]
