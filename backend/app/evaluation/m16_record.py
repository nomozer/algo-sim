# -*- coding: utf-8 -*-
"""M16 Task 2 (W2) — record builder cho quan sát có cấu trúc (nguồn yêu cầu:
.superpowers/sdd/m16-task-2-brief.md).

`build_m16_record` đọc CHỈ event có cấu trúc từ `AttemptObserver` (M14 §F2,
bất biến #22) + envelope trả về từ `run_pipeline` thật — KHÔNG tái dựng stage,
KHÔNG đọc text đề, KHÔNG đoán khi thiếu dữ liệu (fault-injection: event thiếu
→ field liên quan trả None, không crash, không suy diễn từ nguồn khác).

`family_of_route` là hàm SUY family CANONICAL của một route TẤT ĐỊNH, dùng cho
cả `initial_family` lẫn `final_family` — route là selector token (bề mặt LLM
của một family span nhiều target) hoặc một `simulation_id` cụ thể trong
CATALOG (family suy từ `family_memberships`).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.evaluation.dataset import EvalItem
from app.evaluation.m16_schema import M16Expectation
from app.evaluation.observer import AttemptObserver
from app.simulation.catalog import CATALOG
from app.simulation.families import FAMILY_SELECTORS, selector_for_token

# Route "generic_dual" — generic.rule_scene mang HAI membership (result_authority
# khác nhau: boolean_composition=computation, structural_progressive_
# representation=representation). KHÔNG có cách tất định để chọn MỘT family nếu
# không có expected_family tham chiếu — trả nhãn này thay vì đoán bừa.
_DUAL_MEMBERSHIP_FAMILY = "generic_dual"

# Tập TOKEN chọn family cho LLM (KHÔNG phải family_id — SORTING_SELECTOR có
# selector_token="algorithm.comparison_sort" ≠ family_id.value="comparison_sort").
_SELECTOR_TOKENS: frozenset[str] = frozenset(sel.selector_token for sel in FAMILY_SELECTORS.values())


def family_of_route(route_id: str | None, expected_family: str | None = None) -> str | None:
    """Suy family CANONICAL của một route — TẤT ĐỊNH, không đọc text đề.

    - `route_id` None → None.
    - `route_id` là một selector token (vd "algorithm.comparison_sort") →
      `family_id` của `FamilySelector` tương ứng (`selector_for_token`).
    - `route_id` ∈ CATALOG với ĐÚNG MỘT `family_membership` → family đó.
    - `route_id` ∈ CATALOG với NHIỀU membership (hiện chỉ generic.rule_scene) →
      KHÔNG đoán: trả `"generic_dual"`, TRỪ KHI `expected_family` được truyền
      và nằm trong đúng tập family của các membership đó — khi đó so khớp TẤT
      ĐỊNH theo tập (không phải đoán, là xác nhận qua kỳ vọng có sẵn).
    - `route_id` không nằm trong CATALOG lẫn không phải selector token → None.
    """
    if route_id is None:
        return None
    sel = selector_for_token(route_id)
    if sel is not None:
        return sel.family_id.value
    spec = CATALOG.get(route_id)
    if spec is None:
        return None
    families = [m.family_id.value for m in spec.family_memberships]
    if len(families) == 1:
        return families[0]
    if len(families) > 1:
        if expected_family is not None and expected_family in families:
            return expected_family
        return _DUAL_MEMBERSHIP_FAMILY
    return None  # entry chưa khai membership nào (không nên xảy ra ở 14 entry hiện có)


@dataclass
class M16CaseRecord:
    """Quan sát có cấu trúc MỘT case đánh giá M16 — dẫn xuất TẤT ĐỊNH từ
    observer + envelope (KHÔNG phân loại theo message text; `detail` chỉ để
    tham khảo, xem `build_m16_record`)."""

    case_id: str
    group: str
    archetype: str | None
    expected_family: str | None
    expected_initial_route: str | None
    expected_final_route: str | None
    raw_prescribed: str | None
    canonical_prescribed: str | None
    result_ownership: str | None
    initial_route: str | None  # classify_done.simulation_id (status ok) else None
    initial_family: str | None  # dẫn xuất tất định (family_of_route)
    reclassify_attempted: bool
    reclassify_result_route: str | None
    final_route: str | None  # envelope ok → simulation_id
    final_family: str | None
    selector_token_used: bool  # initial_route ∈ FAMILY_SELECTORS tokens
    variant: str | None  # family_resolved.variant
    gates: list[dict]  # [{gate, fired, reason_code}]
    simulate_attempts: list[dict]  # [{n, ok, error_code}] (KHÔNG message)
    first_attempt_ok: bool | None  # None nếu không tới simulate
    semantic_ok: bool | None
    envelope_status: str | None  # "ok" | "unsupported" | None (raise)
    envelope_error_code: str | None
    envelope_failure_category: str | None
    source: str | None  # composed | family_resolved | pattern_reuse
    budget_delta: dict  # 4 counter (0 khi không budget)
    via_production_pipeline: bool  # True khi build từ evaluate_item observer path
    infra_error: str | None  # LỖI HẠ TẦNG eval (mock/script) — CALLER đặt, KHÔNG
    # tự suy từ pipeline_error (RuntimeError simulate-cạn-retry LÀ outcome sản
    # phẩm, không phải infra error — xem build_m16_record).
    detail: str = ""  # message text CHỈ tham khảo, KHÔNG dùng để phân loại


def build_m16_record(
    item: EvalItem,
    obs: AttemptObserver,
    envelope: dict | None,
    pipeline_error: str | None,
    budget_delta: dict,
    *,
    semantic_ok: bool | None = None,
    infra_error: str | None = None,
) -> M16CaseRecord:
    """Dựng `M16CaseRecord` TỪ observer + envelope (production lifecycle,
    bất biến #22 — không tái dựng stage).

    `pipeline_error`: text RuntimeError khi `run_pipeline` raise (simulate cạn
    retry, hoặc bất thường adapter) — đây là OUTCOME SẢN PHẨM (dữ liệu đáng
    phân tích: LLM không hội tụ sau 3 lần), KHÔNG map vào `infra_error`; chỉ
    lưu tham khảo ở `detail`. `envelope_status` tự nhiên là None ở nhánh này vì
    `envelope` là None (không có gì để đọc status).

    `infra_error`: CHỈ set khi CALLER truyền tường minh — dành cho lỗi hạ tầng
    eval THẬT (mock hỏng, script lỗi) không liên quan tới hành vi pipeline.

    Fault-injection an toàn: mọi field đọc qua `.get()`/accessor trả None khi
    event tương ứng vắng mặt — KHÔNG suy diễn (guess) từ field khác.
    """
    m16 = item.m16 if isinstance(item.m16, M16Expectation) else None

    analyze = obs.analyze() or {}
    classify = obs.classify() or {}
    fam_resolved = obs.family_resolved() or {}
    rc_attempted = obs.reclassify_attempted()
    rc_result = obs.reclassify_result()

    expected_family = m16.expected_family if m16 is not None else None

    initial_route = classify.get("simulation_id") if classify.get("status") == "ok" else None
    final_route = (
        envelope.get("simulation_id")
        if envelope is not None and envelope.get("status") == "ok"
        else None
    )
    reclassify_result_route = (
        rc_result.get("simulation_id") if rc_result is not None and rc_result.get("status") == "ok" else None
    )

    gates = [
        {"gate": g.get("gate"), "fired": g.get("fired"), "reason_code": g.get("reason_code")}
        for g in obs.gate_events()
    ]
    simulate_attempts = [
        {"n": a.get("n"), "ok": a.get("ok"), "error_code": a.get("error_code")}
        for a in obs.simulate_attempts()
    ]

    return M16CaseRecord(
        case_id=item.id,
        group=item.group,
        archetype=m16.archetype.value if m16 is not None else None,
        expected_family=expected_family,
        expected_initial_route=m16.expected_initial_route if m16 is not None else None,
        expected_final_route=item.expect_simulation_id,
        raw_prescribed=analyze.get("prescribed_procedure"),
        canonical_prescribed=analyze.get("canonical_prescribed"),
        result_ownership=analyze.get("result_ownership"),
        initial_route=initial_route,
        initial_family=family_of_route(initial_route, expected_family),
        reclassify_attempted=rc_attempted is not None,
        reclassify_result_route=reclassify_result_route,
        final_route=final_route,
        final_family=family_of_route(final_route, expected_family),
        selector_token_used=bool(initial_route) and initial_route in _SELECTOR_TOKENS,
        variant=fam_resolved.get("variant"),
        gates=gates,
        simulate_attempts=simulate_attempts,
        first_attempt_ok=simulate_attempts[0]["ok"] if simulate_attempts else None,
        semantic_ok=semantic_ok,
        envelope_status=envelope.get("status") if envelope is not None else None,
        envelope_error_code=envelope.get("error_code") if envelope is not None else None,
        envelope_failure_category=envelope.get("failure_category") if envelope is not None else None,
        source=envelope.get("source") if envelope is not None else None,
        budget_delta=dict(budget_delta),
        via_production_pipeline=bool(obs.envelope() is not None or pipeline_error is not None),
        infra_error=infra_error,
        detail=pipeline_error or "",
    )
