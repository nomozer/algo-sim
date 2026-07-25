# -*- coding: utf-8 -*-
"""M17 W2B-PATCH §A — TẦNG PIPELINE: so cái đề HỎI với cái spec DỰNG ĐƯỢC.

Lỗ hổng đã đo được ở live L4: completeness PHA 2 so ở tầng **target**
(`satisfies_semantic_operations`), mà `database.relational_table_query` khai nó
đáp ứng CẢ CHÍN operation của family. Hệ quả: mọi spec — kể cả spec bỏ mất hai
tầng cuối — đều "đủ", và hệ trả `status=ok` cho một đề đã bị trả lời thiếu.

Cái phải so là **spec ĐÃ VALIDATE thực sự biểu diễn tầng nào**. Module này:

- đọc TẦNG ĐƯỢC YÊU CẦU từ analyze (`requested_requirements`/
  `requested_operations`) — qua danh tính SEMANTIC, không qua tên target;
- đọc TẦNG ĐƯỢC BIỂU DIỄN từ config ĐÃ VALIDATE — đọc THẲNG cấu trúc spec,
  KHÔNG đọc `notes`/narration (chữ trong notes không chứng minh được gì);
- so THAM SỐ của những tầng có thể so chắc chắn (số dòng giới hạn, hàm tổng
  hợp, chiều sắp xếp). Tên cột KHÔNG so — analyze nói nhãn ("Điểm"), spec nói
  id ("diem"), so bừa sẽ chặn oan; chỗ đó ghi `unverified_parameters`.

Đăng ký theo FAMILY, dữ liệu thuần. Family không khai ⇒ không có tầng ⇒ mọi
hàm trả rỗng và hành vi cũ không đổi một bit.
"""

from __future__ import annotations

from app.simulation.descriptor import FamilyId
from app.simulation.goal_signature import normalize_direction, normalize_identifier
from app.simulation.operations import SEMANTIC_OPERATION_MAP, operation_family
from app.simulation.program_spec import structures_present
from app.simulation.table_query_engine import PIPELINE_STAGE_ORDER, stages_of

_TABLE = FamilyId.RELATIONAL_TABLE_QUERY.value
_PROGRAM = FamilyId.BOUNDED_CONTROL_FLOW.value

# Danh tính SEMANTIC của yêu cầu → TẦNG của spec. Năm hàm tổng hợp cùng quy về
# `table.aggregate` vì spec chỉ mang MỘT hàm tổng hợp — đúng như hợp đồng.
STAGE_OF_SEMANTIC_OPERATION: dict[str, dict[str, str]] = {
    _TABLE: {
        "table.filter_rows": "filter",
        "table.project_columns": "projection",
        "table.sort_rows": "sort",
        "table.limit_rows": "limit",
        "table.aggregate": "aggregate",
    },
    # W2C — "tầng" ở đây là CẤU TRÚC ĐIỀU KHIỂN có mặt trong chương trình.
    _PROGRAM: {
        "program.assign": "assign",
        "program.branch": "branch",
        "program.loop": "loop",
        "program.output": "output",
    },
}

# Thứ tự CÔNG BỐ của từng family (một nguồn: chính hằng của engine).
PROGRAM_STRUCTURE_ORDER: tuple[str, ...] = ("assign", "branch", "loop", "output")
STAGE_ORDER: dict[str, tuple[str, ...]] = {
    _TABLE: PIPELINE_STAGE_ORDER,
    _PROGRAM: PROGRAM_STRUCTURE_ORDER,
}

# Thứ tự có phải RÀNG BUỘC NGỮ NGHĨA không?
# - bảng: CÓ — lọc → chiếu → sắp → lấy n → tổng hợp là thứ tự chạy thật.
# - chương trình: KHÔNG — thứ tự chạy do chính `main`/`statements` quyết định;
#   ở đây chỉ dùng để LIỆT KÊ cho ổn định. Nói "chạy đúng thứ tự assign → branch"
#   là SAI về ngữ nghĩa nên thông điệp phải khác.
STAGE_ORDER_AUTHORITATIVE: dict[str, bool] = {_TABLE: True, _PROGRAM: False}

# Gợi ý CỤ THỂ cho học sinh khi thiếu bước — mỗi family một ví dụ đúng lĩnh vực
# (ví dụ của bảng dán vào đề chương trình sẽ vô nghĩa).
LEARNER_HINT: dict[str, str] = {
    _TABLE: "ví dụ: lọc gì, sắp xếp theo cột nào, lấy mấy dòng, tính gì",
    _PROGRAM: "ví dụ: biến ban đầu bằng bao nhiêu, điều kiện là gì, "
              "trong nhánh/thân vòng lặp làm gì",
}

# Tầng mà spec ĐÃ VALIDATE biểu diễn — đọc thẳng cấu trúc.
STAGE_EXTRACTORS = {_TABLE: stages_of, _PROGRAM: structures_present}


def family_with_stages(families: set[str]) -> str | None:
    """Family (trong phạm vi route cuối) có khai tầng pipeline, nếu có."""
    for fam in sorted(families):
        if fam in STAGE_OF_SEMANTIC_OPERATION:
            return fam
    return None


def _stage_of(operation_id: str, fam: str) -> str | None:
    req = SEMANTIC_OPERATION_MAP.get(operation_id)
    if req is None or operation_family(operation_id) != fam:
        return None
    return STAGE_OF_SEMANTIC_OPERATION[fam].get(req.operation_id)


def _ordered(stages, fam: str) -> list[str]:
    order = STAGE_ORDER[fam]
    return [s for s in order if s in stages]


# ── THAM SỐ so được chắc chắn (KHÔNG so tên cột) ─────────────────
def _req_limit(item: dict):
    v = item.get("limit")
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None


def _req_aggregate(item: dict):
    return normalize_identifier(item.get("aggregate_func"))


def _req_sort(item: dict):
    return normalize_direction(item.get("sort_direction"))


def _rep_limit(config: dict):
    return config.get("limit")


def _rep_aggregate(config: dict):
    agg = config.get("aggregate")
    return agg.get("func") if isinstance(agg, dict) else None


def _rep_sort(config: dict):
    srt = config.get("sort")
    return srt.get("direction") if isinstance(srt, dict) else None


# stage → (đọc yêu cầu từ một item analyze, đọc cái spec dựng, nhãn tham số)
_COMPARABLE: dict[str, dict[str, tuple]] = {
    _TABLE: {
        "limit": (_req_limit, _rep_limit, "số dòng"),
        "aggregate": (_req_aggregate, _rep_aggregate, "hàm tổng hợp"),
        "sort": (_req_sort, _rep_sort, "chiều sắp xếp"),
    },
}
# Tham số CÓ trong yêu cầu nhưng KHÔNG so được chắc chắn (ghi lại, không phán).
_UNVERIFIED_FIELDS = ("filter_column", "filter_op", "filter_value",
                      "aggregate_column", "projection_columns", "sort_column")


def requested_stages(analysis: dict, fam: str) -> list[str]:
    """Tầng đề yêu cầu, theo thứ tự authoritative của family."""
    if not isinstance(analysis, dict):
        return []
    found: set[str] = set()
    raw = analysis.get("requested_requirements")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                stage = _stage_of(item.get("operation"), fam)
                if stage:
                    found.add(stage)
    ops = analysis.get("requested_operations")
    if isinstance(ops, list):
        for op in ops:
            stage = _stage_of(op, fam) if isinstance(op, str) else None
            if stage:
                found.add(stage)
    return _ordered(found, fam)


def represented_stages(config: object, fam: str) -> list[str]:
    """Tầng spec ĐÃ VALIDATE thực sự dựng được."""
    extract = STAGE_EXTRACTORS.get(fam)
    if extract is None or not isinstance(config, dict):
        return []
    present = {s for s, on in extract(config).items() if on}
    return _ordered(present, fam)


def stage_parameter_mismatches(analysis: dict, config: object, fam: str) -> list[dict]:
    """Tầng CÓ MẶT nhưng dựng SAI tham số đề nêu (đủ tầng ≠ đúng yêu cầu)."""
    if not isinstance(config, dict) or not isinstance(analysis, dict):
        return []
    raw = analysis.get("requested_requirements")
    if not isinstance(raw, list):
        return []
    comparable = _COMPARABLE.get(fam, {})
    out: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        stage = _stage_of(item.get("operation"), fam)
        if stage is None or stage in seen or stage not in comparable:
            continue
        read_req, read_rep, label = comparable[stage]
        want, got = read_req(item), read_rep(config)
        if want is None or got is None or want == got:
            continue
        seen.add(stage)
        out.append({"stage": stage, "parameter": label,
                    "requested": want, "represented": got})
    return sorted(out, key=lambda m: STAGE_ORDER[fam].index(m["stage"]))


def unverified_parameters(analysis: dict, fam: str) -> list[str]:
    """Tham số đề có nêu nhưng hệ KHÔNG tự khẳng định được là đúng/sai."""
    if not isinstance(analysis, dict):
        return []
    raw = analysis.get("requested_requirements")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if not isinstance(item, dict) or _stage_of(item.get("operation"), fam) is None:
            continue
        for field in _UNVERIFIED_FIELDS:
            if item.get(field) not in (None, [], "") and field not in out:
                out.append(field)
    return out


def stage_coverage(analysis: dict, families: set[str], config: object) -> dict | None:
    """Bản ghi máy-đọc của §A. None khi family không dùng pipeline tầng."""
    fam = family_with_stages(families)
    if fam is None:
        return None
    req = requested_stages(analysis, fam)
    rep = represented_stages(config, fam)
    dropped = [s for s in req if s not in rep]
    mismatched = stage_parameter_mismatches(analysis, config, fam)
    return {
        "family_id": fam,
        "authoritative_stage_order": list(STAGE_ORDER[fam]),
        "requested_pipeline": req,
        "represented_pipeline": rep,
        "dropped_pipeline_stages": dropped,
        "mismatched_stage_parameters": mismatched,
        "unverified_parameters": unverified_parameters(analysis, fam),
        "completeness_decision": "complete" if not dropped and not mismatched
        else "incomplete",
    }


def stage_shortfall_message(analysis: dict, target_id: str, config: object) -> str | None:
    """Lý do từ chối gửi NGƯỢC cho lượt simulate sau. None khi spec đã đủ.

    Người đọc thông điệp này là LLM chứ không phải học sinh, nên nó gọi ĐÚNG
    TÊN TRƯỜNG trong config — nói chung chung ("spec chưa đủ") thì lượt sau sai
    y hệt lượt trước."""
    from app.simulation.catalog import CATALOG

    spec = CATALOG.get(target_id)
    if spec is None:
        return None
    families = {m.family_id.value for m in spec.family_memberships}
    cov = stage_coverage(analysis, families, config)
    if cov is None or cov["completeness_decision"] == "complete":
        return None

    if STAGE_ORDER_AUTHORITATIVE.get(cov["family_id"], True):
        head = ("Đề yêu cầu một QUY TRÌNH gồm các bước: "
                + ", ".join(cov["requested_pipeline"])
                + f" (chạy đúng thứ tự {' → '.join(cov['authoritative_stage_order'])}).")
    else:
        head = ("Đề yêu cầu chương trình có ĐỦ các cấu trúc: "
                + ", ".join(cov["requested_pipeline"])
                + " (thứ tự chạy do chính chương trình quyết định).")
    parts = [head]
    if cov["dropped_pipeline_stages"]:
        parts.append(
            "Spec vừa gửi THIẾU các trường: "
            + ", ".join(cov["dropped_pipeline_stages"])
            + ". Hãy điền đủ, KHÔNG bỏ bước nào."
        )
    for m in cov["mismatched_stage_parameters"]:
        parts.append(
            f'Trường "{m["stage"]}" phải khớp đề: đề nêu {m["requested"]!r} '
            f"nhưng spec đang để {m['represented']!r}."
        )
    return " ".join(parts)


def stage_labels(stages: list[str], fam: str) -> list[str]:
    """Nhãn tiếng Việt của tầng — lấy từ CHÍNH nhãn operation (một nguồn), để
    thông điệp học sinh không bao giờ lộ id kỹ thuật."""
    from app.simulation.operations import OPERATIONS

    mapping = STAGE_OF_SEMANTIC_OPERATION[fam]
    out: list[str] = []
    for stage in stages:
        label = stage
        for op, spec in sorted(OPERATIONS().items()):
            req = SEMANTIC_OPERATION_MAP.get(op)
            if (req is not None and operation_family(op) == fam
                    and mapping.get(req.operation_id) == stage):
                label = spec.label_vi
                break
        out.append(label)
    return out


__all__ = [
    "STAGE_EXTRACTORS",
    "STAGE_OF_SEMANTIC_OPERATION",
    "STAGE_ORDER",
    "family_with_stages",
    "represented_stages",
    "requested_stages",
    "stage_coverage",
    "stage_labels",
    "stage_parameter_mismatches",
    "stage_shortfall_message",
    "unverified_parameters",
]
