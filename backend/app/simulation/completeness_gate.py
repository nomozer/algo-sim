# -*- coding: utf-8 -*-
"""M17-RC1 §D + §C1 — SEMANTIC COMPLETENESS GATE (dùng chung mọi family).

Bất biến: **`status=ok` ⟹ `dropped_operations` rỗng VÀ `dropped_requirements`
rỗng.** Không request nào được trả ok khi spec chỉ biểu diễn MỘT PHẦN yêu cầu.

§C1 sửa sai lầm định danh của §D: yêu cầu được định danh bằng **operation**
(mục tiêu: "tìm max", "tìm min") chứ KHÔNG phải mechanism (cơ chế:
`track_extreme`). Hai operation dùng chung một mechanism nên định danh bằng
mechanism làm chúng gộp thành một → đề "tìm cả max lẫn min" từng trả `ok` và
bỏ im lặng một nửa. **Operation KHÔNG BAO GIỜ dedupe theo mechanism.**

Hai kênh chạy SONG SONG, không kênh nào thay thế kênh kia:
- kênh OPERATION (chính, phủ 9/9 family — `requested_operations`);
- kênh MECHANISM (giữ từ §D, chỉ 3 family phơi mechanism qua analyze) — vẫn
  bắt được khi analyze khai mechanism mà không khai operation.

Deterministic given analyze + route đã chốt. KHÔNG đọc text đề, KHÔNG keyword,
KHÔNG nhánh riêng cho family nào.

HAI PHA:
- `check_requested_combination` (TRƯỚC simulate): tập yêu cầu tự nó vượt chính
  sách family → chặn ngay, khỏi tốn lượt simulate;
- `check_represented_coverage` (SAU khi biết target+variant): so cái spec THỰC
  SỰ biểu diễn với cái được yêu cầu; còn sót là chặn.
"""

from __future__ import annotations

from app.simulation.error_codes import ErrorCode
from app.simulation.mechanisms import canonical_mechanism, mechanism_family
from app.simulation.operation_policy import (
    SINGLE,
    mechanism_for_variant,
    policy_for_family,
)
from app.simulation.operations import (
    OPERATIONS,
    operation_family,
    operation_labels,
    operations_for_family,
    operations_of_target,
)


# ── chuẩn hoá yêu cầu ────────────────────────────────────────────
def normalized_requested_operations(analysis: dict) -> list[str]:
    """`requested_operations` → id operation hợp lệ, thứ tự ổn định.

    CHỈ bỏ trùng theo CHÍNH id operation — tuyệt đối không gộp theo mechanism
    (đó là lỗi §D). Giá trị lạ (không có trong registry) bị loại: operation
    phải có target/executor thật."""
    if not isinstance(analysis, dict):
        return []
    raw = analysis.get("requested_operations")
    if not isinstance(raw, list):
        return []
    reg = OPERATIONS()
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item in reg and item not in out:
            out.append(item)
    return sorted(out)


def normalized_requested(analysis: dict) -> list[str]:
    """Kênh MECHANISM (§D): `requested_mechanisms` + `prescribed_procedure`
    chuẩn hoá về id canonical, bỏ trùng."""
    if not isinstance(analysis, dict):
        return []
    raw: list = []
    req = analysis.get("requested_mechanisms")
    if isinstance(req, list):
        raw.extend(req)
    single = analysis.get("prescribed_procedure")
    if single is not None:
        raw.append(single)
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        canon = canonical_mechanism(item)
        if canon and canon not in out:
            out.append(canon)
    return sorted(out)


def _ops_scope(operations: list[str], families: set[str]) -> list[str]:
    return [o for o in operations if operation_family(o) in families]


def _mech_scope(requested: list[str], families: set[str]) -> list[str]:
    """Chỉ xét cơ chế THUỘC family của route cuối — cơ chế khác họ đã do
    route-consistency gate (M15 khoá 3) xử lý, không lấn sân."""
    return [m for m in requested if mechanism_family(m) in families]


def _learner_message(labels: list[str], note: str) -> str:
    """Thông điệp CHỈ ĐƯỜNG, dùng nhãn tiếng Việt — không id kỹ thuật."""
    listed = "; ".join(labels)
    return (
        f"Đề đang yêu cầu {len(labels)} việc cùng lúc ({listed}), nhưng mỗi lần "
        "mô phỏng chỉ trình bày được MỘT. "
        + (note + " " if note else "")
        + "Em hãy tách thành từng lần hỏi — giữ nguyên dữ liệu, mỗi lần chọn một "
        "yêu cầu — để xem đầy đủ từng bước."
    ).strip()


# ── PHA 1: tập yêu cầu tự nó có vượt chính sách family không? ────
def check_requested_combination(
    analysis: dict, families: set[str]
) -> tuple[ErrorCode, str, dict] | None:
    """Trả (code, message học-sinh, evidence) khi vi phạm; None khi hợp lệ."""
    ops = _ops_scope(normalized_requested_operations(analysis), families)
    mechs = _mech_scope(normalized_requested(analysis), families)

    for fam in sorted(families):
        pol = policy_for_family(fam)
        fam_ops = [o for o in ops if operation_family(o) == fam]
        fam_mechs = [m for m in mechs if mechanism_family(m) == fam]

        # kênh OPERATION (chính)
        if len(fam_ops) > max(pol.max_operations, 1) or (
            pol.cardinality == SINGLE and len(fam_ops) > 1
        ):
            labels = operation_labels(fam_ops)
            return (
                ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED,
                _learner_message(labels, pol.note),
                {
                    "family_id": fam,
                    "operation_cardinality": pol.cardinality,
                    "max_operations": pol.max_operations,
                    "requested_operations": fam_ops,
                    "requested_operation_labels": labels,
                    "supported_operations": operations_for_family(fam),
                    "requested_in_family": fam_mechs,
                    "unsupported_combinations": [fam_ops],
                    "detected_by": "operation",
                    "policy_note": pol.note,
                },
            )

        # kênh MECHANISM (§D, giữ nguyên hành vi cũ)
        if len(fam_mechs) <= 1:
            continue
        conflicts = pol.exclusive_conflict(set(fam_mechs))
        if not conflicts and len(fam_mechs) <= pol.max_operations:
            continue
        return (
            ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED,
            _learner_message(operation_labels(fam_ops) or fam_mechs, pol.note),
            {
                "family_id": fam,
                "operation_cardinality": pol.cardinality,
                "max_operations": pol.max_operations,
                "requested_operations": fam_ops,
                "requested_in_family": fam_mechs,
                "unsupported_combinations": conflicts or [fam_mechs],
                "detected_by": "mechanism",
                "policy_note": pol.note,
            },
        )
    return None


# ── PHA 2: spec dựng ra có bỏ sót yêu cầu nào không? ─────────────
def represented_operations(target_id: str | None, variant: str | None) -> list[str]:
    """Operation mà target ĐÃ CHỐT (kèm variant đã resolve) thực sự biểu diễn."""
    if not target_id:
        return []
    return operations_of_target(target_id, variant)


def represented_mechanisms(
    analysis: dict, families: set[str], owned: set[str], config: object
) -> list[str]:
    """Cơ chế mà SPEC ĐÃ VALIDATE thực sự biểu diễn (kênh mechanism, §D)."""
    variant = config.get("variant") if isinstance(config, dict) else None
    for fam in sorted(families):
        mech = mechanism_for_variant(fam, variant if isinstance(variant, str) else None)
        if mech:
            return [mech]
    requested = set(normalized_requested(analysis))
    scoped_owned = {m for m in owned if mechanism_family(m) in families}
    overlap = sorted(scoped_owned & requested)
    return overlap if overlap else sorted(scoped_owned)


def check_represented_coverage(
    analysis: dict, families: set[str], owned: set[str], config: object,
    *, target_id: str | None = None, variant: str | None = None,
) -> tuple[ErrorCode, str, dict] | None:
    """`status=ok` chỉ được phép khi hàm này trả None."""
    if variant is None and isinstance(config, dict):
        v = config.get("variant")
        variant = v if isinstance(v, str) else None

    req_ops = _ops_scope(normalized_requested_operations(analysis), families)
    rep_ops = represented_operations(target_id, variant)
    dropped_ops = sorted(set(req_ops) - set(rep_ops))

    req_mech = _mech_scope(normalized_requested(analysis), families)
    rep_mech = represented_mechanisms(analysis, families, owned, config) if config is not None else []
    dropped_mech = sorted(set(req_mech) - set(rep_mech)) if req_mech else []

    if not dropped_ops and not dropped_mech:
        return None

    labels = operation_labels(dropped_ops) or dropped_mech
    return (
        ErrorCode.SEMANTIC_INCOMPLETE,
        (
            f"Mô phỏng dựng ra mới đáp ứng được một phần yêu cầu của đề — còn "
            f"{len(labels)} việc chưa được trình bày ({'; '.join(labels)}). "
            "Hệ không trả lời nửa vời: em hãy tách đề thành từng yêu cầu riêng "
            "để xem đủ."
        ),
        {
            "requested_operations": req_ops,
            "represented_operations": rep_ops,
            "dropped_operations": dropped_ops,
            "dropped_operation_labels": operation_labels(dropped_ops),
            "requested_in_family": req_mech,
            "represented": rep_mech,
            "dropped_requirements": dropped_mech,
        },
    )


def completeness_report(
    analysis: dict, families: set[str], owned: set[str], config: object,
    decision: str, *, target_id: str | None = None, variant: str | None = None,
) -> dict:
    """Bản ghi máy-đọc cho artifact audit (§D/§C1 yêu cầu đủ trường)."""
    if variant is None and isinstance(config, dict):
        v = config.get("variant")
        variant = v if isinstance(v, str) else None

    req_ops = _ops_scope(normalized_requested_operations(analysis), families)
    rep_ops = represented_operations(target_id, variant)
    requested = normalized_requested(analysis)
    in_scope = _mech_scope(requested, families)
    represented = (
        represented_mechanisms(analysis, families, owned, config)
        if config is not None else []
    )
    pol = policy_for_family(sorted(families)[0]) if families else policy_for_family("")
    return {
        "requested_requirements": analysis.get("requested_mechanisms")
        if isinstance(analysis, dict) else None,
        "requested_operations": req_ops,
        "normalized_requested_operations": req_ops,
        "represented_operations": rep_ops,
        "dropped_operations": sorted(set(req_ops) - set(rep_ops)),
        "normalized_requested_requirements": requested,
        "requested_in_family": in_scope,
        "represented_requirements": represented,
        "represented_mechanisms": represented,
        "dropped_requirements": sorted(set(in_scope) - set(represented)) if in_scope else [],
        "unsupported_combinations": [
            sorted(g) for g in pol.exclusive_conflict(set(in_scope))
        ],
        "operation_cardinality": pol.cardinality,
        "max_operations": pol.max_operations,
        "completeness_decision": decision,
    }


__all__ = [
    "SINGLE",
    "check_represented_coverage",
    "check_requested_combination",
    "completeness_report",
    "normalized_requested",
    "normalized_requested_operations",
    "represented_mechanisms",
    "represented_operations",
]
