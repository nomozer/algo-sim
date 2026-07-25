# -*- coding: utf-8 -*-
"""M17 W2B-PATCH2 §B/§C/§D — MANIFEST TẦNG TẤT ĐỊNH + MERGE cho truy vấn bảng.

Quyết định sản phẩm (§A): target `database.relational_table_query` đã KHAI hỗ
trợ pipeline filter→projection→sort→limit→aggregate, nên một request hợp lệ
trong hợp đồng PHẢI có đường sinh candidate spec đủ tầng, KIỂM CHỨNG ĐƯỢC. Cổng
completeness fail-closed vẫn là tầng bảo vệ cuối, nhưng KHÔNG được dùng nó thay
cho khả năng tạo spec hợp lệ.

Sự cố gốc (live P2): LLM gửi lại spec BA tầng ba lần dù được báo đích danh
"THIẾU: limit, aggregate". Giải pháp: từ analyze CÓ CẤU TRÚC
(`requested_requirements`) dựng TẤT ĐỊNH các tầng cần + tham số canonical, rồi
MERGE tầng grounded vào candidate — LLM KHÔNG còn là nguồn DUY NHẤT quyết định
tầng nào tồn tại.

Bất biến giữ chặt:
- manifest KHÔNG chứa kết quả (dòng cuối / giá trị tổng hợp / phán quyết giữ-loại
  / trạng thái tích luỹ) — chỉ chứa YÊU CẦU;
- tầng KHÔNG grounded (analyze thiếu tham số) → KHÔNG bịa: để LLM/cổng xử lý;
- cột manifest nêu mà schema (do LLM dựng) không có → KHÔNG resolve được →
  KHÔNG chèn (không tạo tầng tham chiếu cột không tồn tại).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.simulation.goal_signature import normalize_direction, normalize_identifier
from app.simulation.pipeline_stages import (
    STAGE_OF_SEMANTIC_OPERATION,
    _TABLE,
)
from app.simulation.operations import SEMANTIC_OPERATION_MAP, operation_family
from app.simulation.table_query_engine import PIPELINE_STAGE_ORDER

# Phiên bản thứ tự pipeline — đổi ngữ nghĩa thứ tự thì bump (đi kèm CACHE_VERSION).
PIPELINE_ORDER_VERSION = "table-pipeline-order-1"

_OP_ALIASES = {
    "eq": "=", "equals": "=", "bang": "=", "=": "=",
    "ne": "!=", "neq": "!=", "khac": "!=", "!=": "!=", "<>": "!=",
    "gt": ">", "greater": ">", "lon_hon": ">", ">": ">",
    "gte": ">=", "ge": ">=", ">=": ">=", "=>": ">=",
    "lt": "<", "less": "<", "nho_hon": "<", "<": "<",
    "lte": "<=", "le": "<=", "<=": "<=", "=<": "<=",
    "contains": "contains", "chua": "contains",
}


@dataclass(frozen=True)
class RequiredStage:
    """MỘT tầng đề yêu cầu. `params` ở KHÔNG GIAN NHÃN của analyze (vd cột 'Tổ')
    — merge resolve sang id schema. `grounded` = đủ tham số bắt buộc để dựng."""

    kind: str
    params: dict
    grounded: bool
    required_fields: tuple[str, ...] = ()
    unresolved_fields: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"kind": self.kind, "params": dict(self.params),
                "grounded": self.grounded,
                "required_fields": list(self.required_fields),
                "unresolved_fields": list(self.unresolved_fields)}


@dataclass(frozen=True)
class RequiredTablePipeline:
    """Manifest TẤT ĐỊNH: các tầng cần theo THỨ TỰ authoritative, cho MỘT truy
    vấn. Nhiều truy vấn độc lập KHÔNG gộp ở đây (đó là việc của completeness)."""

    ordered_stages: tuple[RequiredStage, ...]
    query_group: object = None
    order_version: str = PIPELINE_ORDER_VERSION
    _extra: dict = field(default_factory=dict)

    def grounded_stages(self) -> list[RequiredStage]:
        return [s for s in self.ordered_stages if s.grounded]

    def stage(self, kind: str) -> RequiredStage | None:
        return next((s for s in self.ordered_stages if s.kind == kind), None)

    def as_dict(self) -> dict:
        return {"ordered_stages": [s.as_dict() for s in self.ordered_stages],
                "query_group": self.query_group,
                "order_version": self.order_version}


# ── §B — build từ analyze CÓ CẤU TRÚC ────────────────────────────
def _norm_op(value) -> str | None:
    v = normalize_identifier(value)
    return _OP_ALIASES.get(v) if v else None


def _stage_of_op(operation_id) -> str | None:
    if not isinstance(operation_id, str):
        return None
    req = SEMANTIC_OPERATION_MAP.get(operation_id)
    if req is None or operation_family(operation_id) != _TABLE:
        return None
    return STAGE_OF_SEMANTIC_OPERATION[_TABLE].get(req.operation_id)


def _extract_stage(kind: str, item: dict) -> RequiredStage:
    """Rút tham số canonical (không gian nhãn) + xác định grounded/unresolved."""
    if kind == "filter":
        col = item.get("filter_column")
        op = _norm_op(item.get("filter_op"))
        val = item.get("filter_value")
        req = ("filter_column", "filter_op", "filter_value")
        missing = tuple(f for f, v in (("filter_column", col), ("filter_op", op),
                                       ("filter_value", val)) if v in (None, ""))
        params = {"column": col, "op": op, "value": val}
    elif kind == "projection":
        cols = item.get("projection_columns")
        cols = [c for c in cols if isinstance(c, str) and c.strip()] if isinstance(cols, list) else []
        req = ("projection_columns",)
        missing = () if cols else ("projection_columns",)
        params = {"columns": cols}
    elif kind == "sort":
        col = item.get("sort_column")
        direction = normalize_direction(item.get("sort_direction")) or "asc"
        req = ("sort_column",)
        missing = () if isinstance(col, str) and col.strip() else ("sort_column",)
        params = {"column": col, "direction": direction}
    elif kind == "limit":
        n = item.get("limit")
        ok = isinstance(n, int) and not isinstance(n, bool) and n >= 1
        req = ("limit",)
        missing = () if ok else ("limit",)
        params = {"count": n if ok else None}
    elif kind == "aggregate":
        func = normalize_identifier(item.get("aggregate_func"))
        if not func:
            # analyze có thể mã hoá hàm trong CHÍNH operation (`:avg`, `:count`…)
            # thay vì field riêng — không phụ thuộc một field duy nhất.
            req = SEMANTIC_OPERATION_MAP.get(item.get("operation"))
            if req is not None and req.variant_id:
                func = req.variant_id
        col = item.get("aggregate_column")
        req = ("aggregate_func",)
        # count có thể không cột; các hàm khác cần cột
        missing_fields = []
        if not func:
            missing_fields.append("aggregate_func")
        elif func != "count" and not (isinstance(col, str) and col.strip()):
            missing_fields.append("aggregate_column")
        missing = tuple(missing_fields)
        params = {"func": func, "column": col if isinstance(col, str) and col.strip() else None}
    else:
        req, missing, params = (), ("unknown_stage",), {}
    return RequiredStage(kind=kind, params=params, grounded=not missing,
                         required_fields=req, unresolved_fields=missing)


def build_required_pipeline(analysis: object) -> RequiredTablePipeline | None:
    """Manifest cho truy vấn bảng, hoặc None nếu analyze không có yêu cầu bảng.

    Chỉ đọc `requested_requirements` (có cấu trúc) — KHÔNG đọc narration/goal
    text. Nhiều query_group → CHỈ dựng cho nhóm đầu tiên (một truy vấn); nhiều
    truy vấn độc lập do completeness gate xử lý riêng, KHÔNG merge chéo."""
    if not isinstance(analysis, dict):
        return None
    raw = analysis.get("requested_requirements")
    if not isinstance(raw, list) or not raw:
        return None

    # gom theo query_group; giữ nhóm XUẤT HIỆN đầu tiên (ổn định).
    groups: dict[object, list[tuple[str, dict]]] = {}
    order: list[object] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = _stage_of_op(item.get("operation"))
        if kind is None:
            continue
        g = item.get("query_group")
        if g not in groups:
            groups[g] = []
            order.append(g)
        groups[g].append((kind, item))
    if not order:
        return None

    group = order[0]
    per_kind: dict[str, RequiredStage] = {}
    for kind, item in groups[group]:
        stage = _extract_stage(kind, item)
        # nếu một kind xuất hiện nhiều lần, ưu tiên bản GROUNDED
        if kind not in per_kind or (stage.grounded and not per_kind[kind].grounded):
            per_kind[kind] = stage

    ordered = tuple(per_kind[k] for k in PIPELINE_STAGE_ORDER if k in per_kind)
    if not ordered:
        return None
    return RequiredTablePipeline(ordered_stages=ordered, query_group=group)


# ── §C/§D — MERGE tầng grounded vào candidate ────────────────────
def _schema_label_index(config: dict) -> dict[str, str]:
    """Nhãn/tên cột (chuẩn hoá) → id cột trong schema candidate."""
    idx: dict[str, str] = {}
    for col in config.get("schema", []) or []:
        if not isinstance(col, dict):
            continue
        name = col.get("name")
        if not isinstance(name, str):
            continue
        for key in (col.get("label"), name):
            k = normalize_identifier(key)
            if k and k not in idx:
                idx[k] = name
    return idx


def _resolve(label, idx: dict[str, str]) -> str | None:
    return idx.get(normalize_identifier(label))


def _stage_config(kind: str, params: dict, idx: dict[str, str]):
    """Dựng cấu hình tầng ở KHÔNG GIAN ID schema, hoặc None nếu cột không có
    trong schema (không resolve được ⇒ không grounded được ở candidate này)."""
    if kind == "filter":
        col = _resolve(params.get("column"), idx)
        if col is None:
            return None
        return {"op": params.get("op"), "column": col, "value": params.get("value")}
    if kind == "projection":
        ids = [_resolve(c, idx) for c in params.get("columns", [])]
        if not ids or any(x is None for x in ids):
            return None
        return ids
    if kind == "sort":
        col = _resolve(params.get("column"), idx)
        if col is None:
            return None
        return {"column": col, "direction": params.get("direction", "asc")}
    if kind == "limit":
        return params.get("count")
    if kind == "aggregate":
        col = params.get("column")
        rid = _resolve(col, idx) if col else None
        if col and rid is None:
            return None
        return {"func": params.get("func"), "column": rid}
    return None


_STAGE_FIELD = {"filter": "filter", "projection": "projection", "sort": "sort",
                "limit": "limit", "aggregate": "aggregate"}


def _present(config: dict, kind: str) -> bool:
    v = config.get(_STAGE_FIELD[kind])
    if kind == "projection":
        return bool(v)
    return v is not None


def merge_required_stages(
    config: dict, pipeline: RequiredTablePipeline | None
) -> tuple[dict, dict]:
    """Trả (candidate ĐÃ MERGE, log máy-đọc).

    - tầng grounded THIẾU trong candidate → CHÈN từ manifest;
    - tầng grounded CÓ nhưng tham số LỆCH manifest → SỬA về manifest (ghi log);
    - tầng grounded CÓ và khớp → XÁC NHẬN;
    - tầng KHÔNG grounded hoặc cột không resolve được → để nguyên, ghi unresolved.

    KHÔNG bao giờ thêm final result. KHÔNG xoá tầng LLM tự thêm (vd non-null
    filter của P1) — chỉ bảo đảm các tầng manifest yêu cầu có mặt & đúng."""
    merged = dict(config)
    candidate_stages = [k for k in PIPELINE_STAGE_ORDER if _present(config, k)]
    log = {
        "candidate_stage_set": candidate_stages,
        "inserted_stages": [], "corrected_stages": [], "confirmed_stages": [],
        "unresolved_fields": [], "merge_applied": False,
        "order_version": pipeline.order_version if pipeline else None,
    }
    if pipeline is None:
        return merged, log

    idx = _schema_label_index(config)
    for stage in pipeline.ordered_stages:
        field_name = _STAGE_FIELD[stage.kind]
        if not stage.grounded:
            log["unresolved_fields"].append(
                f"{stage.kind}:{','.join(stage.unresolved_fields)}")
            continue
        want = _stage_config(stage.kind, stage.params, idx)
        if want is None:
            log["unresolved_fields"].append(f"{stage.kind}:column_not_in_schema")
            continue
        if not _present(config, stage.kind):
            merged[field_name] = want
            log["inserted_stages"].append(stage.kind)
        elif config.get(field_name) != want:
            log["corrected_stages"].append(
                {"stage": stage.kind, "from": config.get(field_name), "to": want})
            merged[field_name] = want
        else:
            log["confirmed_stages"].append(stage.kind)

    log["merge_applied"] = bool(
        log["inserted_stages"] or log["corrected_stages"])
    return merged, log


def manifest_prompt_hint(pipeline: RequiredTablePipeline | None) -> str:
    """§C — manifest MÁY-ĐỌC nhồi vào prompt simulate để LLM tự điền đúng ngay
    lượt đầu (post-merge vẫn là chốt chặn tất định)."""
    if pipeline is None or not pipeline.grounded_stages():
        return ""
    lines = ["YÊU CẦU TẦNG (bắt buộc có đủ, đúng thứ tự — hệ sẽ kiểm và bù tất định):"]
    for i, s in enumerate(pipeline.ordered_stages, 1):
        p = s.params
        if s.kind == "filter":
            desc = f'lọc {p.get("column")} {p.get("op")} {p.get("value")!r}'
        elif s.kind == "projection":
            desc = f'chỉ hiển thị cột {", ".join(map(str, p.get("columns", [])))}'
        elif s.kind == "sort":
            desc = f'sắp xếp {p.get("column")} {"giảm dần" if p.get("direction") == "desc" else "tăng dần"}'
        elif s.kind == "limit":
            desc = f'lấy {p.get("count")} dòng đầu'
        else:
            desc = f'tính {p.get("func")}({p.get("column") or "*"})'
        flag = "" if s.grounded else "  (đề chưa nêu đủ — điền nếu bảng có căn cứ)"
        lines.append(f"  {i}. {s.kind}: {desc}{flag}")
    return "\n".join(lines)


__all__ = [
    "PIPELINE_ORDER_VERSION",
    "RequiredStage",
    "RequiredTablePipeline",
    "build_required_pipeline",
    "manifest_prompt_hint",
    "merge_required_stages",
]
