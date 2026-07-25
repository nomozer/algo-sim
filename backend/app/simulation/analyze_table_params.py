# -*- coding: utf-8 -*-
"""M17 W2B-PATCH3 §B/§C/§D — VALIDATOR HOÀN CHỈNH THAM SỐ TẦNG cho analyze.

Chạy SAU analyze normalization và TRƯỚC manifest/simulate. Bất biến §A: một
`requested stage` chỉ grounded khi TOÀN BỘ tham số bắt buộc của tầng đã được
trích từ evidence — operation name MỘT MÌNH KHÔNG đủ.

Chỉ áp cho tầng của `relational_table_query`; family khác → NOT_APPLICABLE (không
lây). KHÔNG đọc raw prompt, KHÔNG đoán, KHÔNG ép kiểu (chỉ kiểm presence + kiểu
số của limit). Column-to-schema resolution vẫn do MERGE làm (schema có ở simulate).
"""

from __future__ import annotations

from app.simulation.operations import SEMANTIC_OPERATION_MAP, operation_family
from app.simulation.pipeline_stages import STAGE_OF_SEMANTIC_OPERATION, _TABLE
from app.simulation.table_query_engine import AGGREGATE_FUNCS, PIPELINE_STAGE_ORDER

NOT_APPLICABLE = "not_applicable"
COMPLETE = "complete"
INCOMPLETE = "incomplete"

# Toán tử KHÔNG cần value (§B ngoại lệ). Chuẩn hoá khoảng trắng + hạ chữ.
_NULL_OPERATORS = frozenset({
    "is null", "is not null", "isnull", "isnotnull", "not_null", "null", "notnull",
})


def _s(v) -> str | None:
    """Chuỗi non-empty đã trim, hoặc None."""
    if isinstance(v, str) and v.strip():
        return " ".join(v.split()).strip()
    return None


def _stage_of_op(operation_id) -> str | None:
    if not isinstance(operation_id, str):
        return None
    req = SEMANTIC_OPERATION_MAP.get(operation_id)
    if req is None or operation_family(operation_id) != _TABLE:
        return None
    return STAGE_OF_SEMANTIC_OPERATION[_TABLE].get(req.operation_id)


def _agg_func_of(item: dict) -> str | None:
    """Hàm tổng hợp: field `aggregate_func` hoặc suy từ operation (`:avg`)."""
    func = _s(item.get("aggregate_func"))
    if func:
        return func.lower()
    req = SEMANTIC_OPERATION_MAP.get(item.get("operation"))
    return req.variant_id if (req is not None and req.variant_id) else None


def _check_stage(kind: str, item: dict) -> tuple[list[str], list[str]]:
    """Trả (missing_fields, invalid_fields) cho MỘT tầng."""
    missing: list[str] = []
    invalid: list[str] = []

    if kind == "filter":
        if _s(item.get("filter_column")) is None:
            missing.append("filter_column")
        op = _s(item.get("filter_op"))
        if op is None:
            missing.append("filter_op")
        needs_value = op is None or op.casefold() not in _NULL_OPERATORS
        if needs_value:
            v = item.get("filter_value")
            # None = thiếu; 0/"0"/False đều là GIÁ TRỊ hợp lệ (không phải thiếu).
            if v is None:
                missing.append("filter_value")

    elif kind == "projection":
        cols = item.get("projection_columns")
        good = isinstance(cols, list) and [c for c in cols if _s(c)]
        if not good:
            missing.append("projection_columns")

    elif kind == "sort":
        if _s(item.get("sort_column")) is None:
            missing.append("sort_column")
        # direction mặc định asc nếu thiếu — không bắt buộc (contract engine).

    elif kind == "limit":
        n = item.get("limit")
        if n is None:
            missing.append("limit")
        elif isinstance(n, bool) or not isinstance(n, int) or n < 1:
            invalid.append("limit")

    elif kind == "aggregate":
        func = _agg_func_of(item)
        if func is None or func not in AGGREGATE_FUNCS:
            missing.append("aggregate_func")
            func = None
        col = _s(item.get("aggregate_column"))
        mode = _s(item.get("count_mode"))
        if func == "count":
            # count(*) không cần cột; count(cột) cần cột. count_mode='star' KÈM
            # cột là mâu thuẫn → invalid (không tự đoán biến * thành cột).
            if mode and mode.casefold() in ("star", "*", "all"):
                if col is not None:
                    invalid.append("aggregate")
            elif col is None and not mode:
                # không khai mode và không cột → coi là count(*) hợp lệ
                pass
        elif func is not None:
            # sum/avg/min/max BẮT BUỘC cột
            if col is None:
                missing.append("aggregate_column")

    return missing, invalid


def _known_columns(analysis: dict) -> list[str]:
    """Cột suy được từ evidence analyze (best-effort, để BÁO unknown refs; KHÔNG
    dùng để phán quyết — schema thật ở simulate). Nguồn: objects 'cột X' +
    data.labels."""
    cols: list[str] = []
    objs = analysis.get("objects") if isinstance(analysis, dict) else None
    if isinstance(objs, list):
        for o in objs:
            s = _s(o)
            if s and s.lower().startswith("cột "):
                cols.append(s[4:].strip())
    return cols


def validate_table_parameters(analysis: object) -> dict:
    """§C — báo cáo máy-đọc completeness tham số tầng. `analyze_parameter_
    decision` ∈ {not_applicable, complete, incomplete}."""
    reqs = analysis.get("requested_requirements") if isinstance(analysis, dict) else None
    if not isinstance(reqs, list):
        return _empty_report(NOT_APPLICABLE)

    # gom item theo tầng (giữ item GROUNDED nhất nếu một tầng lặp).
    per_stage: dict[str, dict] = {}
    for item in reqs:
        if not isinstance(item, dict):
            continue
        kind = _stage_of_op(item.get("operation"))
        if kind is None:
            continue
        per_stage.setdefault(kind, item)

    if not per_stage:
        return _empty_report(NOT_APPLICABLE)

    requested = [k for k in PIPELINE_STAGE_ORDER if k in per_stage]
    missing_by: dict[str, list[str]] = {}
    invalid_by: dict[str, list[str]] = {}
    grounded: list[str] = []
    incomplete: list[str] = []
    for kind in requested:
        miss, inval = _check_stage(kind, per_stage[kind])
        if miss:
            missing_by[kind] = miss
        if inval:
            invalid_by[kind] = inval
        if miss or inval:
            incomplete.append(kind)
        else:
            grounded.append(kind)

    known = _known_columns(analysis)
    unknown_refs: list[dict] = []
    if known:
        known_norm = {c.casefold() for c in known}
        for kind in requested:
            for col in _referenced_columns(kind, per_stage[kind]):
                if col.casefold() not in known_norm:
                    unknown_refs.append({"stage": kind, "column": col})

    decision = COMPLETE if not incomplete else INCOMPLETE
    return {
        "requested_stages": requested,
        "grounded_stages": grounded,
        "incomplete_stages": incomplete,
        "missing_parameters_by_stage": missing_by,
        "invalid_parameters_by_stage": invalid_by,
        "unknown_column_references": unknown_refs,
        "analyze_parameter_decision": decision,
    }


def _referenced_columns(kind: str, item: dict) -> list[str]:
    if kind == "filter":
        c = _s(item.get("filter_column"))
        return [c] if c else []
    if kind == "projection":
        cols = item.get("projection_columns")
        return [c for c in (cols if isinstance(cols, list) else []) if _s(c)]
    if kind == "sort":
        c = _s(item.get("sort_column"))
        return [c] if c else []
    if kind == "aggregate":
        c = _s(item.get("aggregate_column"))
        return [c] if c else []
    return []


def _empty_report(decision: str) -> dict:
    return {
        "requested_stages": [], "grounded_stages": [], "incomplete_stages": [],
        "missing_parameters_by_stage": {}, "invalid_parameters_by_stage": {},
        "unknown_column_references": [], "analyze_parameter_decision": decision,
    }


# Field tham số của một requirement item được phép PATCH (đóng — repair không
# được thêm khoá lạ, không được chèn kết quả).
_PATCHABLE_FIELDS = (
    "filter_column", "filter_op", "filter_value",
    "projection_columns", "sort_column", "sort_direction", "limit",
    "aggregate_func", "aggregate_column", "count_mode",
)


def _is_empty(v) -> bool:
    """Field coi là 'thiếu' (cho phép điền): None, chuỗi rỗng, list rỗng.
    0/False/"0" KHÔNG rỗng (là giá trị thật)."""
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == ""
    if isinstance(v, list):
        return len(v) == 0
    return False


def patch_requirements(original: list, repaired: object) -> list:
    """§E — PATCH TẤT ĐỊNH: chỉ ĐIỀN field còn thiếu của MỖI tầng từ bản repair,
    KHÔNG ghi đè field đã hợp lệ, KHÔNG thêm stage mới ngoài original.

    Ghép theo (stage). Field ngoài `_PATCHABLE_FIELDS` của repair bị bỏ qua (repair
    không được chèn kết quả/khoá lạ). Trả list MỚI (không mutate original)."""
    if not isinstance(original, list):
        return original if isinstance(original, list) else []
    rep_by_stage: dict[str, dict] = {}
    if isinstance(repaired, list):
        for item in repaired:
            if not isinstance(item, dict):
                continue
            kind = _stage_of_op(item.get("operation"))
            if kind is not None:
                rep_by_stage.setdefault(kind, item)

    out: list = []
    for item in original:
        if not isinstance(item, dict):
            out.append(item)
            continue
        kind = _stage_of_op(item.get("operation"))
        patched = dict(item)
        rep = rep_by_stage.get(kind) if kind else None
        if rep is not None:
            for field in _PATCHABLE_FIELDS:
                if _is_empty(patched.get(field)) and not _is_empty(rep.get(field)):
                    patched[field] = rep[field]
        out.append(patched)
    return out


def has_table_requirements(analysis: object) -> bool:
    """Analyze có yêu cầu tầng bảng nào không (để pipeline biết có cần check)."""
    return validate_table_parameters(analysis)["requested_stages"] != []


__all__ = [
    "COMPLETE", "INCOMPLETE", "NOT_APPLICABLE",
    "has_table_requirements", "patch_requirements", "validate_table_parameters",
]
