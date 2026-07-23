# -*- coding: utf-8 -*-
"""M17 W2B — validator cho `database.relational_table_query` (FAIL-CLOSED).

Mọi hằng số giới hạn/vốn từ **dẫn xuất từ `table_query_engine`** (một nguồn) —
không viết tay lần thứ hai, để schema Gemini · validator · engine không thể trôi
khỏi nhau (đúng anti-pattern #1 đã từng gây bug: enum hand-written lệch manifest).

Nguyên tắc: nghi ngờ thì TỪ CHỐI. Config sai kiểu, sai toán tử, vượt biên, cột
lạ, hay yêu cầu ngoài phạm vi (JOIN/subquery/mutation) đều bị chặn ở đây — chứ
không để engine chạy trên dữ liệu vô nghĩa rồi trả một kết quả trông có vẻ đúng.
"""

from __future__ import annotations

from typing import Any

from app.simulation.table_query_engine import (
    AGGREGATE_FUNCS,
    COLUMN_TYPES,
    COMPARE_OPS,
    LOGIC_OPS,
    MAX_COLUMNS,
    MAX_PREDICATE_DEPTH,
    MAX_PREDICATES,
    MAX_ROWS,
    OPS_BY_TYPE,
    SORT_DIRECTIONS,
    SPEC_VERSION,
)

_IDENT_MAX = 40


def _err(msg: str) -> tuple[None, str]:
    return None, msg


def _coerce(value: Any, kind: str) -> tuple[Any, str | None]:
    """Ép MỘT ô về kiểu cột đã khai. Không ép được → lỗi (không đoán bừa)."""
    if value is None:
        return None, None
    if kind == "number":
        if isinstance(value, bool):
            return None, "giá trị boolean không dùng cho cột kiểu số"
        if isinstance(value, (int, float)):
            return value, None
        if isinstance(value, str):
            try:
                return float(value) if "." in value else int(value), None
            except ValueError:
                return None, f'"{value}" không phải số'
        return None, f"{value!r} không phải số"
    if kind == "boolean":
        if isinstance(value, bool):
            return value, None
        if isinstance(value, str) and value.lower() in ("true", "false", "đúng", "sai"):
            return value.lower() in ("true", "đúng"), None
        if value in (0, 1):
            return bool(value), None
        return None, f"{value!r} không phải giá trị đúng/sai"
    return (value if isinstance(value, str) else str(value)), None


def _validate_predicate(pred: Any, types: dict[str, str], depth: int,
                        counter: list[int]) -> tuple[dict | None, str | None]:
    if not isinstance(pred, dict):
        return None, "điều kiện lọc phải là đối tượng"
    op = pred.get("op")
    if op in LOGIC_OPS:
        if depth >= MAX_PREDICATE_DEPTH:
            return None, f"điều kiện lồng quá {MAX_PREDICATE_DEPTH} tầng"
        clauses = pred.get("clauses")
        if not isinstance(clauses, list) or len(clauses) < 2:
            return None, f'phép "{op}" cần ít nhất 2 vế'
        out = []
        for sub in clauses:
            v, err = _validate_predicate(sub, types, depth + 1, counter)
            if err:
                return None, err
            out.append(v)
        return {"op": op, "clauses": out}, None

    if op not in COMPARE_OPS:
        return None, f"toán tử so sánh không hỗ trợ: {op!r}"
    counter[0] += 1
    if counter[0] > MAX_PREDICATES:
        return None, f"quá {MAX_PREDICATES} điều kiện so sánh"
    col = pred.get("column")
    if col not in types:
        return None, f"điều kiện lọc dùng cột không có trong bảng: {col!r}"
    kind = types[col]
    if op not in OPS_BY_TYPE[kind]:
        return None, (f'toán tử "{op}" không dùng được với cột {col!r} kiểu {kind}')
    value, err = _coerce(pred.get("value"), kind)
    if err:
        return None, f"giá trị so sánh của cột {col!r}: {err}"
    if value is None:
        return None, f"điều kiện trên cột {col!r} thiếu giá trị so sánh"
    return {"op": op, "column": col, "value": value}, None


def validate_table_query_config(raw: object) -> tuple[dict | None, str | None]:
    """Trả (config đã chuẩn hoá, None) hoặc (None, lý do từ chối)."""
    if not isinstance(raw, dict):
        return _err("Cấu hình truy vấn bảng phải là một đối tượng.")

    version = raw.get("specVersion")
    if version not in (None, SPEC_VERSION):
        return _err(f'specVersion không hỗ trợ: {version!r} (cần "{SPEC_VERSION}").')

    # ── lược đồ ──
    schema = raw.get("schema")
    if not isinstance(schema, list) or not schema:
        return _err("Thiếu lược đồ bảng (schema): cần ít nhất một cột.")
    if len(schema) > MAX_COLUMNS:
        return _err(f"Bảng quá {MAX_COLUMNS} cột — ngoài phạm vi hỗ trợ.")
    types: dict[str, str] = {}
    norm_schema = []
    for col in schema:
        if not isinstance(col, dict):
            return _err("Mỗi cột trong lược đồ phải là một đối tượng.")
        name, kind = col.get("name"), col.get("type")
        if not isinstance(name, str) or not name.strip():
            return _err("Có cột thiếu tên.")
        if len(name) > _IDENT_MAX:
            return _err(f"Tên cột quá dài: {name[:20]}…")
        if name in types:
            return _err(f"Tên cột bị lặp: {name!r}.")
        if kind not in COLUMN_TYPES:
            return _err(f"Cột {name!r} khai kiểu không hỗ trợ: {kind!r} "
                        f"(chỉ có {', '.join(COLUMN_TYPES)}).")
        types[name] = kind
        norm_schema.append({"name": name, "type": kind,
                            "label": col.get("label") if isinstance(col.get("label"), str) else None})

    # ── các dòng ──
    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        return _err("Bảng chưa có dòng dữ liệu nào — hệ không tự tạo bảng mẫu.")
    if len(rows) > MAX_ROWS:
        return _err(f"Bảng quá {MAX_ROWS} dòng — ngoài phạm vi hỗ trợ.")
    col_order = [c["name"] for c in norm_schema]
    norm_rows = []
    for i, row in enumerate(rows):
        # Schema Gemini gửi MỖI DÒNG là mảng ô theo thứ tự cột (structured
        # output không có khoá động). Quy về dict ngay tại đây — một chỗ đổi
        # dạng duy nhất; phần còn lại của validator/engine chỉ biết dict.
        if isinstance(row, list):
            if len(row) > len(col_order):
                return _err(f"Dòng {i + 1} có {len(row)} ô nhưng lược đồ chỉ "
                            f"{len(col_order)} cột.")
            row = {col_order[j]: (v if v != "" else None) for j, v in enumerate(row)}
        if not isinstance(row, dict):
            return _err(f"Dòng {i + 1} phải là một đối tượng hoặc mảng ô.")
        unknown = set(row) - set(types)
        if unknown:
            return _err(f"Dòng {i + 1} có cột không khai trong lược đồ: "
                        f"{', '.join(sorted(unknown))}.")
        norm: dict[str, Any] = {}
        for name, kind in types.items():
            value, err = _coerce(row.get(name), kind)
            if err:
                return _err(f"Dòng {i + 1}, cột {name!r}: {err}.")
            norm[name] = value
        norm_rows.append(norm)

    # ── lọc ──
    filt = raw.get("filter")
    norm_filter = None
    if filt is not None:
        norm_filter, err = _validate_predicate(filt, types, 0, [0])
        if err:
            return _err(f"Điều kiện lọc không hợp lệ: {err}.")

    # ── chiếu ──
    projection = raw.get("projection")
    norm_projection = None
    if projection is not None:
        if not isinstance(projection, list) or not projection:
            return _err("Danh sách cột cần hiển thị (projection) rỗng.")
        for col in projection:
            if col not in types:
                return _err(f"Cột cần hiển thị không có trong bảng: {col!r}.")
        if len(set(projection)) != len(projection):
            return _err("Danh sách cột cần hiển thị bị lặp.")
        norm_projection = list(projection)

    # ── sắp xếp (MỘT khoá) ──
    sort = raw.get("sort")
    norm_sort = None
    if sort is not None:
        if not isinstance(sort, dict):
            return _err("Khai báo sắp xếp phải là một đối tượng.")
        col = sort.get("column")
        direction = sort.get("direction", "asc")
        if col not in types:
            return _err(f"Sắp xếp theo cột không có trong bảng: {col!r}.")
        if direction not in SORT_DIRECTIONS:
            return _err(f"Chiều sắp xếp không hợp lệ: {direction!r}.")
        norm_sort = {"column": col, "direction": direction}

    # ── giới hạn ──
    limit = raw.get("limit")
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            return _err("Giới hạn số dòng phải là số nguyên ≥ 1.")
        if limit > len(norm_rows):
            return _err(f"Giới hạn {limit} lớn hơn số dòng của bảng ({len(norm_rows)}).")

    # ── tổng hợp (MỘT hàm) ──
    aggregate = raw.get("aggregate")
    norm_agg = None
    if aggregate is not None:
        if not isinstance(aggregate, dict):
            return _err("Khai báo hàm tổng hợp phải là một đối tượng.")
        func = aggregate.get("func")
        if func not in AGGREGATE_FUNCS:
            return _err(f"Hàm tổng hợp không hỗ trợ: {func!r} "
                        f"(chỉ có {', '.join(AGGREGATE_FUNCS)}).")
        col = aggregate.get("column")
        if func == "count":
            if col is not None and col not in types:
                return _err(f"Đếm theo cột không có trong bảng: {col!r}.")
        else:
            if col not in types:
                return _err(f"Hàm {func.upper()} cần một cột có trong bảng, nhận {col!r}.")
            if func in ("sum", "avg") and types[col] != "number":
                return _err(f"Hàm {func.upper()} chỉ dùng được với cột kiểu số, "
                            f"cột {col!r} là {types[col]}.")
        norm_agg = {"func": func, "column": col}

    return {
        "specVersion": SPEC_VERSION,
        "schema": norm_schema,
        "rows": norm_rows,
        "filter": norm_filter,
        "projection": norm_projection,
        "sort": norm_sort,
        "limit": limit,
        "aggregate": norm_agg,
        "notes": raw.get("notes") if isinstance(raw.get("notes"), str) else None,
    }, None


__all__ = ["validate_table_query_config"]
