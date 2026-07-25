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
from app.simulation.pipeline_stages import LEARNER_HINT, stage_coverage, stage_labels
from app.simulation.operations import (
    OPERATIONS,
    canonical_requirements,
    query_keys_of,
    requirements_from_structured,
    operation_family,
    operation_labels,
    operations_for_family,
    operations_of_target,
    satisfies_semantic_operations,
    semantic_label,
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


def _req_family(req) -> str | None:
    """Family của một SemanticRequirement — tra ngược qua registry (không đoán
    chữ từ `operation_id`)."""
    from app.simulation.operations import SEMANTIC_OPERATION_MAP

    for op, r in SEMANTIC_OPERATION_MAP.items():
        if r.operation_id == req.operation_id and r.variant_id == req.variant_id:
            return operation_family(op)
    return None


def requested_semantic(analysis: dict, families: set[str]):
    """§C1.1 — YÊU CẦU SEMANTIC chuẩn hoá trong phạm vi family của route cuối.

    Đây là bước sửa lỗi V4: gợi ý target thô (`rule_scene` vs `boolean_dag`)
    được quy về CÙNG một `boolean.evaluate_expression`, còn `find_max` và
    `find_min` vẫn là HAI yêu cầu vì khác `operation_id`."""
    return canonical_requirements(
        _ops_scope(normalized_requested_operations(analysis), families))


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

    # M17 W2B-S1 — TRUY VẤN ĐỘC LẬP. Một spec mô tả ĐÚNG MỘT yêu cầu; đề hỏi hai
    # mục tiêu khác nhau (vd "đếm tổ A" và "đếm tổ B") thì chạy cái nào cũng là
    # bỏ im lặng cái kia. Kiểm TRƯỚC luật cardinality vì đây là lý do từ chối
    # đúng bản chất hơn ("hai truy vấn", không phải "nhiều thao tác").
    for fam in sorted(families):
        pol = policy_for_family(fam)
        keys = query_keys_of(analysis, {fam})
        if len(keys) > pol.max_independent_goals:
            reqs = [r for r in requirements_from_structured(analysis)
                    if _req_family(r) == fam]
            labels = [semantic_label(r) for r in reqs] or [str(k) for k in keys]
            return (
                ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED,
                (
                    f"Đề đang hỏi {len(keys)} truy vấn độc lập, nhưng mỗi lần mô "
                    "phỏng chỉ trình bày được MỘT. Em hãy tách thành từng lần hỏi "
                    "(giữ nguyên bảng, mỗi lần một yêu cầu) để xem đầy đủ từng bước."
                ),
                {
                    "family_id": fam,
                    "operation_cardinality": pol.cardinality,
                    "max_independent_goals": pol.max_independent_goals,
                    "independent_goal_count": len(keys),
                    "independent_goal_keys": [k for k in keys if k is not None],
                    "requested_operations": [o for o in ops if operation_family(o) == fam],
                    "requested_semantic_requirements": [r.as_dict() for r in reqs],
                    "requested_operation_labels": labels,
                    "unsupported_combinations": [[str(k) for k in keys]],
                    "detected_by": "independent_goal",
                    "policy_note": pol.note,
                },
            )

    for fam in sorted(families):
        pol = policy_for_family(fam)
        fam_ops = [o for o in ops if operation_family(o) == fam]
        fam_mechs = [m for m in mechs if mechanism_family(m) == fam]
        # §C1.1: đếm YÊU CẦU SEMANTIC, không đếm gợi ý target. Ba target logic
        # cùng đáp ứng một `boolean.evaluate_expression` ⇒ MỘT yêu cầu.
        fam_reqs = canonical_requirements(fam_ops)

        # kênh OPERATION (chính)
        if len(fam_reqs) > max(pol.max_operations, 1) or (
            pol.cardinality == SINGLE and len(fam_reqs) > 1
        ):
            labels = [semantic_label(r) for r in fam_reqs]
            return (
                ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED,
                _learner_message(labels, pol.note),
                {
                    "family_id": fam,
                    "operation_cardinality": pol.cardinality,
                    "max_operations": pol.max_operations,
                    "requested_operations": fam_ops,
                    "requested_semantic_requirements": [r.as_dict() for r in fam_reqs],
                    "requested_operation_labels": labels,
                    "supported_operations": operations_for_family(fam),
                    "requested_in_family": fam_mechs,
                    "unsupported_combinations": [[r.label_key() for r in fam_reqs]],
                    "detected_by": "semantic_operation",
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

    # §C1.1 — so ở TẦNG SEMANTIC. Route chọn implementation; nó KHÔNG được xoá
    # yêu cầu của người dùng, nhưng cũng không bị phạt khi analyze gợi ý một
    # target ANH EM cùng đáp ứng đúng yêu cầu đó.
    req_ops = _ops_scope(normalized_requested_operations(analysis), families)
    req_sem = canonical_requirements(req_ops)
    rep_sem = satisfies_semantic_operations(target_id, variant) if target_id else []
    dropped_sem = [r for r in req_sem if r not in rep_sem]
    rep_ops = represented_operations(target_id, variant)

    req_mech = _mech_scope(normalized_requested(analysis), families)
    rep_mech = represented_mechanisms(analysis, families, owned, config) if config is not None else []
    dropped_mech = sorted(set(req_mech) - set(rep_mech)) if req_mech else []

    # W2B-PATCH §A — kênh TẦNG: với family kiểu pipeline, "đủ family" KHÔNG đủ.
    # So cái spec ĐÃ VALIDATE dựng được với cái đề hỏi, từng tầng một.
    stages = stage_coverage(analysis, families, config) if config is not None else None

    evidence = {
        "requested_operations": req_ops,
        "requested_semantic_requirements": [r.as_dict() for r in req_sem],
        "represented_operations": rep_ops,
        "represented_semantic_operations": [r.as_dict() for r in rep_sem],
        "represented_semantic_variants": sorted(
            {r.variant_id for r in rep_sem if r.variant_id}),
        "dropped_semantic_requirements": [r.as_dict() for r in dropped_sem],
        "dropped_operations": [r.label_key() for r in dropped_sem],
        "dropped_operation_labels": [semantic_label(r) for r in dropped_sem],
        "requested_in_family": req_mech,
        "represented": rep_mech,
        "dropped_requirements": dropped_mech,
    }
    if stages is not None:
        evidence.update(stages)

    # Kênh TẦNG chạy TRƯỚC: khi đề hỏi một quy trình nhiều bước, "thiếu bước
    # nào" là chẩn đoán đúng bản chất hơn "thiếu yêu cầu nào".
    if stages is not None and stages["completeness_decision"] == "incomplete":
        return (ErrorCode.PIPELINE_STAGE_INCOMPLETE,
                _stage_message(stages), evidence)

    if not dropped_sem and not dropped_mech:
        return None

    labels = [semantic_label(r) for r in dropped_sem] or dropped_mech
    return (
        ErrorCode.SEMANTIC_INCOMPLETE,
        (
            f"Mô phỏng dựng ra mới đáp ứng được một phần yêu cầu của đề — còn "
            f"{len(labels)} việc chưa được trình bày ({'; '.join(labels)}). "
            "Hệ không trả lời nửa vời: em hãy tách đề thành từng yêu cầu riêng "
            "để xem đủ."
        ),
        evidence,
    )


def _stage_message(stages: dict) -> str:
    """Thông điệp học sinh cho ca THIẾU BƯỚC — chỉ nhãn tiếng Việt, không id.

    KHÔNG xui "tách đề ra": quy trình nhiều bước là hợp lệ, lỗi nằm ở chỗ hệ
    chưa dựng đủ bước chứ không phải đề hỏi quá nhiều."""
    fam = stages["family_id"]
    dropped = stage_labels(stages["dropped_pipeline_stages"], fam)
    wrong = stages["mismatched_stage_parameters"]
    parts: list[str] = []
    if dropped:
        parts.append(f"chưa dựng được {len(dropped)} bước ({'; '.join(dropped)})")
    if wrong:
        listed = "; ".join(
            f"{m['parameter']} đề nêu {m['requested']} nhưng dựng thành {m['represented']}"
            for m in wrong)
        parts.append(f"dựng sai {len(wrong)} bước ({listed})")
    # Gợi ý phải ĐÚNG LĨNH VỰC: ví dụ của truy vấn bảng dán vào đề chương trình
    # thì học sinh làm theo cũng không gỡ được (đúng bài học L5 — lời khuyên sai
    # bản chất còn tệ hơn không khuyên).
    hint = LEARNER_HINT.get(fam, "ví dụ: cần làm gì ở từng bước")
    return (
        "Mô phỏng dựng ra chưa trả lời đủ đề: " + ", và ".join(parts) + ". "
        "Hệ không trả lời nửa vời. Em thử hỏi lại và nêu rõ từng bước cần làm "
        f"({hint})."
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
    req_sem = canonical_requirements(req_ops)
    rep_sem = satisfies_semantic_operations(target_id, variant) if target_id else []
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
        "requested_semantic_requirements": [r.as_dict() for r in req_sem],
        "represented_operations": rep_ops,
        "represented_semantic_operations": [r.as_dict() for r in rep_sem],
        "dropped_semantic_requirements": [
            r.as_dict() for r in req_sem if r not in rep_sem],
        "dropped_operations": [r.label_key() for r in req_sem if r not in rep_sem],
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
