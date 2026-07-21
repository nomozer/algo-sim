# -*- coding: utf-8 -*-
"""M17-RC1 §C — CATALOG ARCHETYPE MATRIX: coverage THẬT của 9 family / 19 target.

Nguyên tắc:
- danh sách target/family DẪN XUẤT từ registry (không viết tay trong runner);
- bằng chứng lấy từ case CHẠY THẬT qua production ``run_pipeline`` (bất biến
  #22) — không suy đoán từ tên file/test;
- thiếu fixture thì báo ``COVERAGE_GAP``, KHÔNG bao giờ tính là PASS;
- ``NOT_APPLICABLE`` chỉ được dùng khi HỢP ĐỒNG chứng minh slot vô nghĩa với
  target đó (lý do phải DẪN XUẤT được, không phải lời khẳng định), và mẫu số
  coverage KHÔNG chứa nó.

Ranh giới claim (đọc trước khi trích số): provider là kịch bản, nên mọi số ở
đây đo **tầng quyết định phía server** (route handling / gate / validator /
completeness) khi analyze đã cho trước — KHÔNG đo năng lực phân loại của LLM
thật. Độ chính xác classify live được đo riêng ở live smoke W1/W2A.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import build_scripted_provider
from app.evaluation.authenticity_matrix import build_audit_cases
from app.evaluation.observer import AttemptObserver
from app.evaluation.rc1c_fixtures import COMPLETENESS_FIXTURES, INSUFFICIENT_FIXTURES
from app.simulation.authenticity import AUTHENTICITY_CONTRACTS
from app.simulation.catalog import CATALOG
from app.simulation.descriptor import ReachabilityLevel, ResultAuthority
from app.simulation.families import FAMILY_SELECTORS
from app.simulation.input_requirements import (
    NOT_APPLICABLE as INPUT_NOT_APPLICABLE,
    applicability_of,
)
from app.simulation.mechanisms import (
    FAMILY_MECHANISMS,
    analyze_exposed_values,
    canonical_mechanism,
    mechanism_family,
)
from app.simulation.operation_policy import FAMILY_OPERATION_POLICY, policy_for_family
from app.simulation.operations import (
    analyze_exposed_operations,
    operation_family,
    operations_for_family,
)

# ── vốn từ đóng ──────────────────────────────────────────────────
SLOTS: tuple[str, ...] = (
    "supported_canonical",
    "supported_boundary",
    "insufficient_input",
    "unsupported_variant_or_parameter",
    "cross_family_near_miss",
    "semantic_completeness",
    "executor_authenticity",
    "result_leakage",
)

COVERED_PASS = "COVERED_PASS"
COVERED_FAIL = "COVERED_FAIL"
COVERAGE_GAP = "COVERAGE_GAP"
NOT_APPLICABLE = "NOT_APPLICABLE"

GAP_KINDS: tuple[str, ...] = (
    "missing_canonical",
    "missing_boundary",
    "missing_insufficient",
    "missing_unsupported",
    "missing_cross_family",
    "missing_semantic_completeness",
    "missing_oracle",
    "missing_audit_metadata",
)

_SELECTOR_TOKENS = frozenset(s.selector_token for s in FAMILY_SELECTORS.values())


def ai_reachable_ids() -> list[str]:
    return sorted(
        sid for sid, spec in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    )


def families_of(sim_id: str) -> list[str]:
    return sorted({m.family_id.value for m in CATALOG[sim_id].family_memberships})


def owned_of(sim_id: str) -> list[str]:
    return sorted({m for mb in CATALOG[sim_id].family_memberships for m in mb.owned_mechanisms})


def required_grounded_inputs(sim_id: str) -> list[str]:
    """Nhóm dữ kiện ĐỀ phải cung cấp, theo HỢP ĐỒNG `input_requirements` (§C2).

    Trước §C2 hàm này đọc `config_schema["required"]` — sai bản chất: schema
    gộp cả trường kỹ thuật (`specVersion`, `variant`, `problem`) với dữ kiện
    thật, nên không phân biệt được "đề phải cho" và "hệ tự điền"."""
    from app.simulation.input_requirements import requirements_for

    req = requirements_for(sim_id)
    return sorted(k.value for k in req.required_grounded_inputs) if req else []


def analyze_expressible_families() -> set[str]:
    """Family mà analyze CÓ THỂ phát tín hiệu yêu cầu.

    HAI kênh: `requested_mechanisms` (chỉ 3 family — giới hạn M15) và §C1
    `requested_operations` (mọi family). Trước §C1 chỉ có kênh mechanism, nên
    6/9 family là COVERAGE_GAP `missing_audit_metadata`: gate không bao giờ
    nhận được dữ liệu ở đời thực. Nay hợp cả hai."""
    fams: set[str] = set()
    for raw in analyze_exposed_values():
        canon = canonical_mechanism(raw)
        if canon:
            fams.add(mechanism_family(canon))
    for op in analyze_exposed_operations():
        fams.add(operation_family(op))
    return fams


def mechanism_expressible_families() -> set[str]:
    """CHỈ kênh mechanism — giữ để báo cáo ranh giới M15 cho trung thực."""
    return {
        mechanism_family(canonical_mechanism(v))
        for v in analyze_exposed_values() if canonical_mechanism(v)
    }


# ── bản ghi một case chạy thật ───────────────────────────────────
@dataclass
class SlotCaseRecord:
    """Quan sát CÓ CẤU TRÚC một case (chỉ từ observer + envelope)."""

    case_id: str
    slot: str
    target_id: str | None
    family_id: str | None
    expected_status: str
    expected_route: str | None
    expected_error_code: str | None
    actual_status: str | None
    route: str | None
    variant: str | None
    executor: str | None
    simulation_created: bool
    generic_leak: bool
    false_positive_simulation: bool
    false_refusal: bool
    dropped_requirements: list[str]
    failure_category: str | None
    error_code: str | None
    leaked_result_fields: list[str]
    matched: bool
    reason: str = ""
    gates: list[dict] = field(default_factory=list)


def _result_field_names(sim_id: str) -> set[str]:
    """Tên field KẾT QUẢ (phần trước dấu chấm) theo authenticity contract —
    dùng để soi rò rỉ: config KHÔNG được chứa sẵn đáp án."""
    c = AUTHENTICITY_CONTRACTS.get(sim_id)
    if c is None:
        return set()
    return {f.split(".")[0] for f in c.required_result_fields}


def _scan_keys(value: object, out: set[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            out.add(k)
            _scan_keys(v, out)
    elif isinstance(value, list):
        for v in value:
            _scan_keys(v, out)


def leaked_result_fields(sim_id: str | None, config: object) -> list[str]:
    """Field kết quả xuất hiện TRONG config đã validate = LLM nộp sẵn đáp án.
    Chỉ tính key có GIÁ TRỊ (None = schema nullable bỏ trống, không phải rò)."""
    if sim_id is None or not isinstance(config, dict):
        return []
    names = _result_field_names(sim_id)
    if not names:
        return []
    present: set[str] = set()
    _collect_non_null(config, names, present)
    return sorted(present)


def _collect_non_null(value: object, names: set[str], out: set[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if k in names and v is not None:
                out.add(k)
            _collect_non_null(v, names, out)
    elif isinstance(value, list):
        for v in value:
            _collect_non_null(v, names, out)


async def _run(prompt: str) -> tuple[dict | None, AttemptObserver, str | None]:
    obs = AttemptObserver()
    try:
        env = await pipeline.run_pipeline(prompt, "khoa-gia", pattern_store=None, observer=obs)
        return env, obs, None
    except Exception as err:  # simulate cạn retry → RuntimeError (outcome sản phẩm)
        return None, obs, str(err)


def _record(
    *, case_id: str, slot: str, target_id: str | None, family_id: str | None,
    expected_status: str, expected_route: str | None, expected_error_code: str | None,
    env: dict | None, obs: AttemptObserver, pipeline_error: str | None,
) -> SlotCaseRecord:
    status = env.get("status") if isinstance(env, dict) else None
    route = env.get("simulation_id") if isinstance(env, dict) and status == "ok" else None
    config = env.get("config") if isinstance(env, dict) else None
    completeness = env.get("completeness") if isinstance(env, dict) else None
    dropped = list((completeness or {}).get("dropped_requirements") or [])
    fam_resolved = obs.family_resolved() or {}

    simulation_created = status == "ok" and route is not None
    generic_leak = bool(
        simulation_created and route == "generic.rule_scene" and target_id not in (None, "generic.rule_scene")
    )
    leaked = leaked_result_fields(route, config)

    matched = True
    reason = ""
    if expected_status == "ok":
        matched = (
            status == "ok" and route == expected_route
            and route in CATALOG and route not in _SELECTOR_TOKENS
        )
        if not matched:
            reason = f"kỳ vọng ok→{expected_route}, thực tế {status}→{route}"
    else:
        matched = status == "unsupported"
        if matched and expected_error_code is not None:
            matched = env.get("error_code") == expected_error_code
            if not matched:
                reason = (f"kỳ vọng error_code={expected_error_code}, "
                          f"thực tế {env.get('error_code')}")
        elif not matched:
            reason = f"kỳ vọng unsupported, thực tế {status}→{route}"
    if leaked:
        matched = False
        reason = (reason + " · " if reason else "") + f"config chứa field kết quả {leaked}"

    return SlotCaseRecord(
        case_id=case_id, slot=slot, target_id=target_id, family_id=family_id,
        expected_status=expected_status, expected_route=expected_route,
        expected_error_code=expected_error_code,
        actual_status=status, route=route,
        variant=fam_resolved.get("variant"),
        executor=CATALOG[route].executor_id if route in CATALOG else None,
        simulation_created=simulation_created,
        generic_leak=generic_leak,
        false_positive_simulation=bool(simulation_created and expected_status == "unsupported"),
        false_refusal=bool(status == "unsupported" and expected_status == "ok"),
        dropped_requirements=dropped,
        failure_category=env.get("failure_category") if isinstance(env, dict) else None,
        error_code=env.get("error_code") if isinstance(env, dict) else None,
        leaked_result_fields=leaked,
        matched=matched,
        reason=reason or (pipeline_error or ""),
        gates=[dict(g) for g in obs.gates()],
    )


_ARCHETYPE_SLOT = {
    "direct": "supported_canonical",
    "paraphrase": "supported_canonical",
    "changed_input": "supported_canonical",
    "boundary": "supported_boundary",
    "near_miss": "unsupported_variant_or_parameter",
    "leak_control": "cross_family_near_miss",
    "leak_probe": "cross_family_near_miss",
    "refusal_control": "insufficient_input",
}


def run_all_cases(set_provider) -> list[SlotCaseRecord]:
    """Chạy TOÀN BỘ case (73 audit W0/W1 tái dùng + 4 case §C) qua production
    ``run_pipeline``. ``set_provider(fake)`` cài fake ``call_gemini``."""
    records: list[SlotCaseRecord] = []

    for case in build_audit_cases():
        fake, _ = build_scripted_provider(case.script)
        set_provider(fake)
        env, obs, err = asyncio.run(_run(case.prompt_vi))
        # family của case: target → membership; near-miss (không target) → suy từ
        # cơ chế gap mà case nhắm tới (dữ liệu contract, không đoán chữ).
        # Case control khai TƯỜNG MINH nó chứng minh slot/target nào (metadata
        # cạnh fixture); case per-target suy từ archetype.
        target = case.sim_id or case.audit_target
        slot = case.audit_slot or _ARCHETYPE_SLOT[case.archetype]
        if target:
            fam = families_of(target)[0]
        elif case.mechanism:
            fam = mechanism_family(canonical_mechanism(case.mechanism) or case.mechanism)
        else:
            fam = None
        records.append(_record(
            case_id=case.case_id, slot=slot,
            target_id=target, family_id=fam,
            expected_status=case.expected_status if case.expected_status != "probe" else "unsupported",
            expected_route=case.expected_route, expected_error_code=None,
            env=env, obs=obs, pipeline_error=err,
        ))

    for fx in INSUFFICIENT_FIXTURES:
        fake, _ = build_scripted_provider(fx.script)
        set_provider(fake)
        env, obs, err = asyncio.run(_run(fx.prompt))
        records.append(_record(
            case_id=fx.case_id, slot="insufficient_input",
            target_id=fx.target_id, family_id=fx.family_id,
            expected_status="unsupported", expected_route=None,
            expected_error_code=fx.expected_error_code,
            env=env, obs=obs, pipeline_error=err,
        ))

    for fx in COMPLETENESS_FIXTURES:
        fake, _ = build_scripted_provider(fx.script)
        set_provider(fake)
        env, obs, err = asyncio.run(_run(fx.prompt))
        records.append(_record(
            case_id=fx.case_id, slot="semantic_completeness",
            target_id=None, family_id=fx.family_id,
            expected_status=fx.expected_status, expected_route=fx.expected_route,
            expected_error_code=fx.expected_error_code,
            env=env, obs=obs, pipeline_error=err,
        ))
    return records


# ── phân giải slot ───────────────────────────────────────────────
def _slot(status: str, *, cases=(), gap_kind=None, reason="", oracle=None) -> dict:
    ids = [c.case_id for c in cases]
    first = cases[0] if cases else None
    return {
        "status": status,
        "fixture_id": ids or None,
        "oracle_id": oracle,
        "expected": (first.expected_status if first else None),
        "actual": (first.actual_status if first else None),
        "route": (first.route if first else None),
        "variant": (first.variant if first else None),
        "executor": (first.executor if first else None),
        "simulation_created": (any(c.simulation_created for c in cases) if cases else None),
        "generic_leak": (any(c.generic_leak for c in cases) if cases else None),
        "false_positive_simulation": (any(c.false_positive_simulation for c in cases) if cases else None),
        "false_refusal": (any(c.false_refusal for c in cases) if cases else None),
        "dropped_requirements": sorted({d for c in cases for d in c.dropped_requirements}),
        "failure_category": (first.failure_category if first else None),
        "error_code": (first.error_code if first else None),
        "gap_kind": gap_kind,
        "reason": reason or " · ".join(c.reason for c in cases if c.reason),
    }


def _authenticity(sim_id: str, target_cases: list[SlotCaseRecord]) -> str:
    """REAL / PARTIAL / BROKEN dẫn xuất từ membership + bằng chứng chạy.
    generic.rule_scene KHÔNG BAO GIỜ được nâng lên REAL (dual authority)."""
    if any(not c.matched for c in target_cases if c.expected_status == "ok"):
        return "BROKEN"
    auth = {m.result_authority for m in CATALOG[sim_id].family_memberships}
    if ResultAuthority.COMPUTATION in auth and ResultAuthority.REPRESENTATION in auth:
        return "PARTIAL"
    if ResultAuthority.COMPUTATION in auth:
        return "REAL"
    return "REPRESENTATION_ONLY"


def build_target_records(records: list[SlotCaseRecord]) -> list[dict]:
    expressible = analyze_expressible_families()
    out: list[dict] = []

    for sid in ai_reachable_ids():
        fams = families_of(sid)
        records_for_target = [c for c in records if c.target_id == sid]
        slots: dict[str, dict] = {}

        # 1/2 — canonical + boundary
        for slot, gap in (("supported_canonical", "missing_canonical"),
                          ("supported_boundary", "missing_boundary")):
            cs = [c for c in records_for_target if c.slot == slot]
            if not cs:
                slots[slot] = _slot(
                    COVERAGE_GAP, gap_kind=gap,
                    reason=f"chưa có fixture archetype {slot} cho target này",
                )
            else:
                slots[slot] = _slot(
                    COVERED_PASS if all(c.matched for c in cs) else COVERED_FAIL,
                    cases=cs, oracle="deterministic_engine_contract",
                )

        # 3 — insufficient_input: phân loại theo HỢP ĐỒNG dữ kiện (§C2), không
        # suy từ config_schema (schema `required` gộp cả version/mô tả, không
        # phân biệt được "dữ kiện đề phải cho" với "trường kỹ thuật").
        status_app, na_reason = applicability_of(sid)
        cs = [c for c in records_for_target if c.slot == "insufficient_input"]
        if cs:
            slots["insufficient_input"] = _slot(
                COVERED_PASS if all(c.matched for c in cs) else COVERED_FAIL,
                cases=cs, oracle="input_requirements_contract",
            )
        elif status_app == INPUT_NOT_APPLICABLE:
            slots["insufficient_input"] = _slot(NOT_APPLICABLE, reason=na_reason)
        else:
            slots["insufficient_input"] = _slot(
                COVERAGE_GAP, gap_kind="missing_insufficient",
                reason=f"target APPLICABLE ({required_grounded_inputs(sid)}) nhưng "
                       "chưa có case kiểm chống bịa dữ liệu",
            )

        # 4 — unsupported variant/parameter (near-miss CÙNG family)
        cs = [c for c in records if c.slot == "unsupported_variant_or_parameter"
              and c.family_id in fams]
        near = [c for c in records if c.slot == "unsupported_variant_or_parameter"]
        cs = cs or [c for c in near if c.target_id is None
                    and _near_miss_family(c) in fams]
        if cs:
            slots["unsupported_variant_or_parameter"] = _slot(
                COVERED_PASS if all(c.matched for c in cs) else COVERED_FAIL,
                cases=cs, oracle="intentional_gap_registry",
            )
        else:
            slots["unsupported_variant_or_parameter"] = _slot(
                COVERAGE_GAP, gap_kind="missing_unsupported",
                reason="family chưa có near-miss fixture cấp cơ chế "
                       "(INTENTIONAL_GAP_MECHANISMS không phủ family này)",
            )

        # 5 — cross-family near miss
        cs = [c for c in records if c.slot == "cross_family_near_miss"
              and (c.expected_route == sid or c.target_id == sid)]
        if cs:
            slots["cross_family_near_miss"] = _slot(
                COVERED_PASS if all(c.matched for c in cs) else COVERED_FAIL,
                cases=cs, oracle="route_ownership_registry",
            )
        else:
            slots["cross_family_near_miss"] = _slot(
                COVERAGE_GAP, gap_kind="missing_cross_family",
                reason="chưa có case kiểm target này KHÔNG chiếm nhầm đề của family khác",
            )

        # 6 — semantic completeness
        slots["semantic_completeness"] = _completeness_slot(fams, records, expressible)

        # 7 — executor authenticity. BẰNG CHỨNG là case canonical đã chạy: không
        # có case nào thì đây là GAP, KHÔNG phải PASS (khai contract trong
        # registry chỉ chứng minh đã KHAI, không chứng minh engine chạy đúng).
        auth = _authenticity(sid, records_for_target)
        canon = [c for c in records_for_target if c.slot == "supported_canonical"]
        if not canon:
            slots["executor_authenticity"] = _slot(
                COVERAGE_GAP, gap_kind="missing_canonical",
                reason="chưa có case canonical chạy qua engine → không có bằng "
                       f"chứng cho engine_authenticity={auth}",
            )
        else:
            slots["executor_authenticity"] = _slot(
                COVERED_FAIL if auth == "BROKEN" else COVERED_PASS,
                cases=canon, oracle="authenticity_contract",
                reason=f"engine_authenticity={auth}",
            )

        # 8 — result leakage
        ok_cases = [c for c in records_for_target if c.actual_status == "ok"]
        leaked = [c for c in ok_cases if c.leaked_result_fields]
        if not _result_field_names(sid):
            slots["result_leakage"] = _slot(
                COVERAGE_GAP, gap_kind="missing_oracle",
                reason="authenticity contract chưa khai required_result_fields → "
                       "không có oracle để soi rò rỉ",
            )
        elif not ok_cases:
            slots["result_leakage"] = _slot(
                COVERAGE_GAP, gap_kind="missing_canonical",
                reason="không có case ok nào để soi config",
            )
        else:
            slots["result_leakage"] = _slot(
                COVERED_FAIL if leaked else COVERED_PASS,
                cases=leaked or ok_cases, oracle="authenticity_contract.required_result_fields",
            )

        pol = policy_for_family(fams[0]) if fams else policy_for_family("")
        out.append({
            "family_id": fams,
            "target_id": sid,
            "owned_mechanisms": owned_of(sid),
            "supported_variants": sorted(
                v.variant_id for sel in FAMILY_SELECTORS.values() for v in sel.variants
                if v.concrete_simulation_id == sid
            ),
            "operation_cardinality": pol.cardinality,
            "required_grounded_inputs": required_grounded_inputs(sid),
            "input_applicability": status_app,
            "validator_id": getattr(CATALOG[sid].validate, "__name__", None)
            or getattr(getattr(CATALOG[sid].validate, "func", None), "__name__", None),
            "executor_id": CATALOG[sid].executor_id,
            "renderer_id": CATALOG[sid].domain,
            "engine_authenticity": auth,
            "visual_authenticity": _visual_authenticity(sid),
            "archetype_slots": slots,
        })
    return out


def _near_miss_family(rec: SlotCaseRecord) -> str | None:
    return rec.family_id


def _visual_authenticity(sim_id: str) -> str:
    """Trạng thái review thị giác. RC1-C KHÔNG tự chấm — chỉ có tree.traversal
    đã qua review trình duyệt thật (M17-VR1); phần còn lại chờ §E."""
    if sim_id == "tree.traversal":
        return "REAL_VISUAL"
    return "NEEDS_VISUAL_REVIEW"


def _completeness_slot(fams: list[str], records, expressible: set[str]) -> dict:
    cs = [c for c in records if c.slot == "semantic_completeness" and c.family_id in fams]
    if cs:
        return _slot(
            COVERED_PASS if all(c.matched for c in cs) else COVERED_FAIL,
            cases=cs, oracle="completeness_gate",
        )
    fam = fams[0] if fams else ""
    op_count = len(operations_for_family(fam))
    pol = policy_for_family(fam)
    if op_count <= 1 and pol.cardinality == "single":
        return _slot(
            NOT_APPLICABLE,
            reason=f"family {fam} chỉ có {op_count} operation chạy được và "
                   "cardinality=single → KHÔNG tồn tại tổ hợp nhiều thao tác nào "
                   "để đề có thể yêu cầu, nên slot này vô nghĩa với target đó",
        )
    if fam not in expressible:
        return _slot(
            COVERAGE_GAP, gap_kind="missing_audit_metadata",
            reason=f"analyze KHÔNG phơi cơ chế của family {fam} "
                   "(analyze_exposed_values không chứa) → gate completeness không "
                   "bao giờ nhận được dữ liệu để đối chiếu",
        )
    return _slot(COVERAGE_GAP, gap_kind="missing_semantic_completeness",
                 reason="family biểu đạt được nhưng chưa có fixture end-to-end")


# ── metrics + gaps ───────────────────────────────────────────────
def coverage_metrics(targets: list[dict], records: list[SlotCaseRecord]) -> dict:
    counts = {COVERED_PASS: 0, COVERED_FAIL: 0, COVERAGE_GAP: 0, NOT_APPLICABLE: 0}
    full, partial, blocking = 0, 0, 0
    for t in targets:
        st = [s["status"] for s in t["archetype_slots"].values()]
        for s in st:
            counts[s] += 1
        graded = [s for s in st if s != NOT_APPLICABLE]
        if all(s == COVERED_PASS for s in graded):
            full += 1
        else:
            partial += 1
        if COVERED_FAIL in st:
            blocking += 1

    denom = counts[COVERED_PASS] + counts[COVERED_FAIL] + counts[COVERAGE_GAP]
    routed = [r for r in records if r.expected_status == "ok"]
    return {
        "target_count": len(targets),
        "family_count": len({f for t in targets for f in t["family_id"]}),
        "total_archetype_slots": sum(counts.values()),
        "covered_pass": counts[COVERED_PASS],
        "covered_fail": counts[COVERED_FAIL],
        "coverage_gap": counts[COVERAGE_GAP],
        "not_applicable": counts[NOT_APPLICABLE],
        "coverage_denominator": denom,
        "coverage_ratio": round(counts[COVERED_PASS] / denom, 4) if denom else None,
        "targets_full_coverage": full,
        "targets_partial_coverage": partial,
        "targets_with_blocking_gap": blocking,
        "total_cases_executed": len(records),
        "route_accuracy": {
            "numerator": sum(1 for r in routed if r.route == r.expected_route),
            "denominator": len(routed),
            "scope": "server-side route handling given scripted analyze — KHÔNG "
                     "phải độ chính xác classify của LLM thật",
        },
        "generic_leak_count": sum(1 for r in records if r.generic_leak),
        "false_positive_simulation_count": sum(1 for r in records if r.false_positive_simulation),
        "false_refusal_count": sum(1 for r in records if r.false_refusal),
        "semantic_loss_count": sum(
            1 for r in records
            if r.slot == "semantic_completeness" and not r.matched
            and r.actual_status == "ok"
        ),
        "result_leakage_count": sum(1 for r in records if r.leaked_result_fields),
        "engine_REAL_count": sum(1 for t in targets if t["engine_authenticity"] == "REAL"),
        "engine_PARTIAL_count": sum(1 for t in targets if t["engine_authenticity"] == "PARTIAL"),
        "engine_BROKEN_count": sum(1 for t in targets if t["engine_authenticity"] == "BROKEN"),
    }


def coverage_gaps(targets: list[dict]) -> list[dict]:
    gaps = []
    for t in targets:
        for slot, s in t["archetype_slots"].items():
            if s["status"] != COVERAGE_GAP:
                continue
            gaps.append({
                "target_id": t["target_id"],
                "family_id": t["family_id"],
                "slot": slot,
                "gap_kind": s["gap_kind"],
                "reason": s["reason"],
                "blocking": s["gap_kind"] in ("missing_canonical", "missing_oracle"),
            })
    return gaps


def records_as_dicts(records: list[SlotCaseRecord]) -> list[dict]:
    return [asdict(r) for r in records]


__all__ = [
    "COVERAGE_GAP", "COVERED_FAIL", "COVERED_PASS", "GAP_KINDS", "NOT_APPLICABLE",
    "SLOTS", "SlotCaseRecord", "ai_reachable_ids", "analyze_expressible_families",
    "build_target_records", "coverage_gaps", "coverage_metrics",
    "leaked_result_fields", "records_as_dicts", "required_grounded_inputs",
    "run_all_cases",
]
