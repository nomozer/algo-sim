# -*- coding: utf-8 -*-
"""M17-RC1 §D — SEMANTIC COMPLETENESS GATE (dùng chung mọi family).

Bất biến mới: **`status=ok` ⟹ `dropped_requirements` rỗng.** Không request nào
được trả ok khi spec chỉ biểu diễn MỘT PHẦN yêu cầu.

Deterministic given analyze + config đã validate. KHÔNG đọc text đề, KHÔNG
keyword, KHÔNG nhánh riêng cho family nào — mọi khác biệt nằm ở dữ liệu
(`FAMILY_OPERATION_POLICY`, `VARIANT_MECHANISM`).

HAI PHA, cả hai chạy TRƯỚC khi envelope tới executor FE:
- `check_requested_combination` (TRƯỚC simulate): tập yêu cầu tự nó đã vượt
  chính sách family (vd 4 kiểu duyệt cây trong khi family là `single`) → chặn
  ngay, khỏi tốn lượt simulate.
- `check_represented_coverage` (SAU validate config): so cái spec THỰC SỰ biểu
  diễn với cái được yêu cầu → còn sót là chặn.

Family `pipeline`/`multiple` (đóng gói PDU, mạch logic, cảnh generic) KHÔNG bị
coi là xung đột khi có nhiều cơ chế — đúng chính sách đã khai.
"""

from __future__ import annotations

from app.simulation.error_codes import ErrorCode
from app.simulation.mechanisms import canonical_mechanism, mechanism_family
from app.simulation.operation_policy import (
    SINGLE,
    mechanism_for_variant,
    policy_for_family,
)


def normalized_requested(analysis: dict) -> list[str]:
    """`requested_mechanisms` (+ `prescribed_procedure` cho tương thích ngược)
    chuẩn hoá về id canonical, bỏ trùng, thứ tự ổn định."""
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


def _family_scope(requested: list[str], families: set[str]) -> list[str]:
    """Chỉ xét cơ chế THUỘC family của route cuối — cơ chế khác họ đã do
    route-consistency gate (M15 khoá 3) xử lý, không lấn sân."""
    return [m for m in requested if mechanism_family(m) in families]


def check_requested_combination(
    analysis: dict, families: set[str]
) -> tuple[ErrorCode, str, dict] | None:
    """PHA 1 — tập YÊU CẦU tự nó có vượt chính sách family không?
    Trả (code, message học-sinh, evidence) khi vi phạm; None khi hợp lệ."""
    requested = normalized_requested(analysis)
    in_scope = _family_scope(requested, families)
    if len(in_scope) <= 1:
        return None  # 0 hoặc 1 thao tác — không bao giờ là xung đột

    for fam in sorted(families):
        pol = policy_for_family(fam)
        scoped = [m for m in in_scope if mechanism_family(m) == fam]
        if len(scoped) <= 1:
            continue
        conflicts = pol.exclusive_conflict(set(scoped))
        over_max = len(scoped) > pol.max_operations
        if not conflicts and not over_max:
            continue  # family multiple/pipeline cho phép — KHÔNG chặn
        evidence = {
            "family_id": fam,
            "operation_cardinality": pol.cardinality,
            "max_operations": pol.max_operations,
            "requested_in_family": scoped,
            "unsupported_combinations": conflicts or [scoped],
            "policy_note": pol.note,
        }
        return (
            ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED,
            (
                "Đề yêu cầu nhiều thao tác cùng lúc, nhưng mỗi lần mô phỏng chỉ "
                "trình bày được MỘT. " + (pol.note or "")
                + " Em hãy tách thành từng lần hỏi (giữ nguyên dữ liệu, mỗi lần "
                "chọn một thao tác) để xem đầy đủ từng bước."
            ).strip(),
            evidence,
        )
    return None


def represented_mechanisms(
    analysis: dict, families: set[str], owned: set[str], config: object
) -> list[str]:
    """Cơ chế mà SPEC ĐÃ VALIDATE thực sự biểu diễn.

    Có trường `variant` → tra bảng dữ liệu variant→mechanism (chính xác nhất).
    Không có → dùng cơ chế target sở hữu, giao với yêu cầu để không thổi phồng
    (target catch-all sở hữu nhiều cơ chế nhưng một lần chạy chỉ làm một việc)."""
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
    analysis: dict, families: set[str], owned: set[str], config: object
) -> tuple[ErrorCode, str, dict] | None:
    """PHA 2 — spec đã validate có bỏ sót yêu cầu nào không?
    `status=ok` chỉ được phép khi hàm này trả None."""
    requested = normalized_requested(analysis)
    in_scope = _family_scope(requested, families)
    if not in_scope:
        return None  # analyze không nêu yêu cầu cơ chế → không có gì để đối chiếu
    represented = represented_mechanisms(analysis, families, owned, config)
    dropped = sorted(set(in_scope) - set(represented))
    if not dropped:
        return None
    evidence = {
        "requested_in_family": in_scope,
        "represented": represented,
        "dropped_requirements": dropped,
    }
    return (
        ErrorCode.SEMANTIC_INCOMPLETE,
        (
            "Mô phỏng dựng ra mới đáp ứng được một phần yêu cầu của đề — còn "
            f"{len(dropped)} thao tác chưa được trình bày. Hệ không trả lời "
            "nửa vời: em hãy tách đề thành từng yêu cầu riêng để xem đủ."
        ),
        evidence,
    )


def completeness_report(
    analysis: dict, families: set[str], owned: set[str], config: object,
    decision: str,
) -> dict:
    """Bản ghi máy-đọc cho artifact audit (§D yêu cầu đủ trường)."""
    requested = normalized_requested(analysis)
    in_scope = _family_scope(requested, families)
    represented = (
        represented_mechanisms(analysis, families, owned, config)
        if config is not None else []
    )
    pol = policy_for_family(sorted(families)[0]) if families else policy_for_family("")
    return {
        "requested_requirements": analysis.get("requested_mechanisms")
        if isinstance(analysis, dict) else None,
        "normalized_requested_requirements": requested,
        "requested_in_family": in_scope,
        "represented_requirements": represented,
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
    "represented_mechanisms",
]
