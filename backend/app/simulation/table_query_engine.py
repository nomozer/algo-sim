# -*- coding: utf-8 -*-
"""M17 W2B — ENGINE TẤT ĐỊNH cho truy vấn bảng quan hệ (`database.relational_table_query`).

Bất biến R0: LLM **chỉ** cung cấp lược đồ + các dòng + yêu cầu. Nó KHÔNG BAO GIỜ
cung cấp: dòng kết quả, tập đã lọc, kết quả sắp xếp, giá trị tổng hợp, hay phán
quyết giữ/loại từng dòng. Toàn bộ những thứ đó do engine này tính.

Bản Python là **bản đối chiếu** của engine frontend (TypeScript) — hai bên phải
cho cùng một dấu vết, khoá bằng test parity như các domain khác.

Dấu vết 9 giai đoạn (đúng thứ tự học sinh cần thấy):
  1 `read_row`      — đọc từng dòng nguồn
  2 `evaluate`      — tính vị từ trên dòng đó
  3 `keep`/`drop`   — giữ hay loại (kèm LÝ DO từng vị từ con)
  4 `filtered_set`  — chốt tập đã lọc
  5 `projection`    — chỉ giữ các cột được hỏi
  6 `sort`          — sắp xếp ỔN ĐỊNH theo một khoá
  7 `limit`         — cắt bớt
  8 `accumulate`    — tích luỹ từng bước cho hàm tổng hợp
  9 `result`        — kết quả cuối

KHÔNG hỗ trợ (từ chối trung thực, không giả vờ): JOIN, truy vấn lồng, sửa dữ
liệu, SQL tự do, kết nối CSDL thật, GROUP BY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SPEC_VERSION = "table-1.0"

# ── vốn từ ĐÓNG (schema Gemini + validator đều dẫn xuất từ đây) ──
COLUMN_TYPES: tuple[str, ...] = ("text", "number", "boolean")
COMPARE_OPS: tuple[str, ...] = ("=", "!=", ">", ">=", "<", "<=", "contains")
# Toán tử chỉ dùng được với kiểu nào — chặn "lương > 'cao'" ngay ở validator.
OPS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "number": ("=", "!=", ">", ">=", "<", "<="),
    "text": ("=", "!=", "contains"),
    "boolean": ("=", "!="),
}
LOGIC_OPS: tuple[str, ...] = ("and", "or")
SORT_DIRECTIONS: tuple[str, ...] = ("asc", "desc")
AGGREGATE_FUNCS: tuple[str, ...] = ("count", "sum", "avg", "min", "max")

# ── W2B-PATCH §C — MARKER Ô THIẾU DỮ LIỆU (chính sách khai báo) ──
# Bảng thật có ô trống, và đề tiếng Việt thường VIẾT CHỮ thay vì để trống.
# Chuẩn hoá các marker này về `None` ở ĐÚNG MỘT BIÊN (validator), TRƯỚC khi ép
# kiểu — executor chỉ nhận `None` hoặc giá trị đã đúng kiểu.
#
# Hai nhóm TÁCH BẠCH, vì rủi ro khác nhau:
# - `EMPTY_CELL_MARKERS`: ô rỗng thật sự → thiếu dữ liệu ở MỌI kiểu cột;
# - `MISSING_VALUE_MARKERS`: CHỮ mô tả sự thiếu → chỉ áp cho cột nhận null
#   (number/boolean theo mặc định, hoặc cột khai `nullable: true`), vì ở cột
#   chữ thì "trống" có thể là DỮ LIỆU THẬT, không phải marker.
#
# TUYỆT ĐỐI không nhận vào đây: "0", 0, false, "không" — đó là giá trị có nghĩa.
EMPTY_CELL_MARKERS: tuple[str, ...] = ("",)
MISSING_VALUE_MARKERS: tuple[str, ...] = ("trống", "—", "–", "n/a", "null")
# Kiểu cột mặc định CHO PHÉP marker chữ (cột chữ phải khai `nullable: true`).
MARKER_NULLABLE_TYPES: tuple[str, ...] = ("number", "boolean")

# ── W2B-PATCH §A — THỨ TỰ TẦNG AUTHORITATIVE (một nguồn) ──
# Engine áp dụng đúng thứ tự này; `aggregate` tính TRÊN KẾT QUẢ SAU `limit`.
# Công bố ở đây để hợp đồng prompt, gate completeness và test khoá cùng đọc một
# chỗ — không ai được suy diễn thứ tự từ output.
PIPELINE_STAGE_ORDER: tuple[str, ...] = (
    "filter", "projection", "sort", "limit", "aggregate",
)

# ── giới hạn (bounds) ──
MAX_ROWS = 30
MAX_COLUMNS = 8
MAX_PREDICATES = 5
MAX_PREDICATE_DEPTH = 2


@dataclass
class TraceStep:
    """Một bước dấu vết. `kind` là vốn từ đóng; renderer đọc trường theo kind."""

    kind: str
    narration: str
    row_index: int | None = None
    detail: dict = field(default_factory=dict)


def _cmp(op: str, left: Any, right: Any) -> bool:
    """So sánh MỘT ô với hằng. Kiểu đã được validator ép khớp trước đó."""
    if op == "=":
        return left == right
    if op == "!=":
        return left != right
    if op == "contains":
        return str(right).lower() in str(left).lower()
    if left is None or right is None:
        return False
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    if op == "<":
        return left < right
    return left <= right


def _eval_predicate(pred: dict, row: dict) -> tuple[bool, list[dict]]:
    """Tính vị từ trên MỘT dòng. Trả (kết quả, giải thích từng vế).

    Giải thích là dữ liệu cho renderer/tường thuật — học sinh thấy VÌ SAO dòng
    bị giữ hay loại, không chỉ thấy kết quả."""
    if pred.get("op") in LOGIC_OPS:
        parts = []
        values = []
        for sub in pred.get("clauses", []):
            ok, sub_why = _eval_predicate(sub, row)
            values.append(ok)
            parts.extend(sub_why)
        result = all(values) if pred["op"] == "and" else any(values)
        parts.append({"kind": "logic", "op": pred["op"], "result": result})
        return result, parts

    col = pred["column"]
    actual = row.get(col)
    ok = _cmp(pred["op"], actual, pred["value"])
    return ok, [{
        "kind": "compare", "column": col, "op": pred["op"],
        "value": pred["value"], "actual": actual, "result": ok,
    }]


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "đúng" if v else "sai"
    if v is None:
        return "(trống)"
    return str(v)


def _sort_key(value: Any) -> tuple[int, Any]:
    """Khoá sắp xếp TOÀN PHẦN: None luôn xuống cuối, còn lại so trong cùng kiểu
    (validator đã bảo đảm một cột chỉ một kiểu)."""
    if value is None:
        return (1, "")
    if isinstance(value, bool):
        return (0, int(value))
    return (0, value)


def run_table_query(config: dict) -> dict:
    """Chạy truy vấn TẤT ĐỊNH. `config` phải ĐÃ qua validator.

    Trả `{steps, filtered_indices, projected_columns, ordered_indices,
    result_rows, aggregate}` — mọi giá trị đều do đây tính."""
    schema: list[dict] = config["schema"]
    rows: list[dict] = config["rows"]
    col_names = [c["name"] for c in schema]
    steps: list[TraceStep] = []

    # ── 1–3. đọc từng dòng · tính vị từ · giữ hoặc loại ──
    pred = config.get("filter")
    kept: list[int] = []
    for i, row in enumerate(rows):
        steps.append(TraceStep(
            "read_row", f"Đọc dòng {i + 1}: " +
            ", ".join(f"{c}={_fmt(row.get(c))}" for c in col_names[:3]) +
            ("…" if len(col_names) > 3 else ""),
            row_index=i, detail={"row": dict(row)},
        ))
        if pred is None:
            kept.append(i)
            steps.append(TraceStep(
                "keep", f"Không có điều kiện lọc → giữ dòng {i + 1}.",
                row_index=i, detail={"reasons": []},
            ))
            continue
        ok, why = _eval_predicate(pred, row)
        steps.append(TraceStep(
            "evaluate", f"Xét điều kiện trên dòng {i + 1}: " + _explain(why),
            row_index=i, detail={"reasons": why, "result": ok},
        ))
        if ok:
            kept.append(i)
        steps.append(TraceStep(
            "keep" if ok else "drop",
            f"Dòng {i + 1} " + ("THOẢ điều kiện → giữ lại." if ok else "KHÔNG thoả → loại."),
            row_index=i, detail={"reasons": why},
        ))

    # ── 4. chốt tập đã lọc ──
    steps.append(TraceStep(
        "filtered_set",
        f"Sau khi lọc còn {len(kept)}/{len(rows)} dòng.",
        detail={"kept_indices": list(kept)},
    ))

    # ── 5. phép chiếu ──
    projection: list[str] = config.get("projection") or col_names
    steps.append(TraceStep(
        "projection",
        "Chỉ giữ lại cột: " + ", ".join(projection) + "."
        if config.get("projection") else "Giữ nguyên mọi cột.",
        detail={"columns": list(projection)},
    ))

    # ── 6. sắp xếp ỔN ĐỊNH ──
    ordered = list(kept)
    sort = config.get("sort")
    if sort:
        before = list(ordered)
        # Python `sorted` ổn định ⇒ dòng bằng khoá giữ nguyên thứ tự gốc.
        ordered.sort(key=lambda idx: _sort_key(rows[idx].get(sort["column"])),
                     reverse=sort["direction"] == "desc")
        steps.append(TraceStep(
            "sort",
            f"Sắp xếp theo {sort['column']} " +
            ("giảm dần" if sort["direction"] == "desc" else "tăng dần") +
            " (ổn định: hai dòng bằng nhau giữ nguyên thứ tự cũ).",
            detail={"before": before, "after": list(ordered), "column": sort["column"],
                    "direction": sort["direction"]},
        ))

    # ── 7. giới hạn ──
    limit = config.get("limit")
    if limit is not None:
        cut = ordered[:limit]
        steps.append(TraceStep(
            "limit", f"Chỉ lấy {limit} dòng đầu (còn {len(cut)}).",
            detail={"before": list(ordered), "after": list(cut), "limit": limit},
        ))
        ordered = cut

    # ── 8. tích luỹ ──
    aggregate = config.get("aggregate")
    agg_result: dict | None = None
    if aggregate:
        agg_result = _accumulate(aggregate, rows, ordered, steps)

    # ── 9. kết quả ──
    result_rows = [{c: rows[i].get(c) for c in projection} for i in ordered]
    if agg_result is not None:
        final = f"{_agg_label(aggregate)} = {_fmt(agg_result['value'])}"
    else:
        final = f"Kết quả: {len(result_rows)} dòng."
    steps.append(TraceStep("result", final, detail={
        "rows": result_rows, "aggregateResult": agg_result,
    }))

    return {
        "steps": [s.__dict__ for s in steps],
        "filtered_indices": kept,
        "projected_columns": list(projection),
        "ordered_indices": ordered,
        "result_rows": result_rows,
        # Tên KHÁC trường `aggregate` trong config: config mang YÊU CẦU
        # ({func, column}), state mang ĐÁP ÁN engine tính ({value, counted}).
        # Trùng tên khiến oracle soi rò rỉ không phân biệt được yêu cầu với đáp
        # án — RC1-C đã báo nhầm 2 case vì đúng chỗ này.
        "aggregateResult": agg_result,
    }


def _explain(why: list[dict]) -> str:
    parts = []
    for w in why:
        if w["kind"] == "compare":
            parts.append(f"{w['column']}={_fmt(w['actual'])} {w['op']} {_fmt(w['value'])}"
                         f" → {'đúng' if w['result'] else 'sai'}")
        else:
            parts.append(("VÀ" if w["op"] == "and" else "HOẶC") +
                         f" → {'đúng' if w['result'] else 'sai'}")
    return "; ".join(parts)


def _agg_label(aggregate: dict) -> str:
    vi = {"count": "Đếm", "sum": "Tổng", "avg": "Trung bình",
          "min": "Nhỏ nhất", "max": "Lớn nhất"}
    col = aggregate.get("column")
    return vi[aggregate["func"]] + (f" của {col}" if col else " số dòng")


def _accumulate(aggregate: dict, rows: list[dict], ordered: list[int],
                steps: list[TraceStep]) -> dict:
    """Tích luỹ TỪNG BƯỚC — đây là cơ chế ẩn học sinh cần thấy, không phải
    một con số nhảy ra."""
    func = aggregate["func"]
    col = aggregate.get("column")
    acc: float | None = None
    count = 0
    for i in ordered:
        value = rows[i].get(col) if col else None
        if func != "count" and value is None:
            steps.append(TraceStep(
                "accumulate", f"Dòng {i + 1} không có giá trị {col} → bỏ qua.",
                row_index=i, detail={"skipped": True, "accumulator": acc, "count": count},
            ))
            continue
        count += 1
        if func == "count":
            acc = count
        elif func in ("sum", "avg"):
            acc = (acc or 0) + value
        elif func == "min":
            acc = value if acc is None else min(acc, value)
        else:
            acc = value if acc is None else max(acc, value)
        steps.append(TraceStep(
            "accumulate",
            f"Dòng {i + 1}: " + (
                f"đếm thêm 1 → {count}" if func == "count"
                else f"{col}={_fmt(value)} → {_agg_label(aggregate).lower()} tạm thời "
                     f"{_fmt(round(acc / count, 4) if func == 'avg' else acc)}"),
            row_index=i,
            detail={"value": value, "accumulator": acc, "count": count},
        ))
    if func == "avg":
        value: Any = round(acc / count, 4) if count else None
    elif func == "count":
        value = count
    else:
        value = acc
    return {"func": func, "column": col, "value": value, "counted": count}


def stages_of(config: dict) -> dict[str, bool]:
    """Tầng mà MỘT config ĐÃ VALIDATE thực sự biểu diễn (W2B-PATCH §A).

    Đọc THẲNG cấu trúc spec — không đọc `notes`, không đọc narration. Dùng cho
    gate completeness: `status=ok` chỉ hợp lệ khi mọi tầng đề yêu cầu có mặt."""
    if not isinstance(config, dict):
        return {s: False for s in PIPELINE_STAGE_ORDER}
    return {
        "filter": config.get("filter") is not None,
        "projection": bool(config.get("projection")),
        "sort": config.get("sort") is not None,
        "limit": config.get("limit") is not None,
        "aggregate": config.get("aggregate") is not None,
    }


__all__ = [
    "AGGREGATE_FUNCS", "COLUMN_TYPES", "COMPARE_OPS", "EMPTY_CELL_MARKERS",
    "LOGIC_OPS", "MARKER_NULLABLE_TYPES", "MAX_COLUMNS", "MAX_PREDICATES",
    "MAX_PREDICATE_DEPTH", "MAX_ROWS", "MISSING_VALUE_MARKERS", "OPS_BY_TYPE",
    "PIPELINE_STAGE_ORDER", "SORT_DIRECTIONS", "SPEC_VERSION",
    "run_table_query", "stages_of",
]
