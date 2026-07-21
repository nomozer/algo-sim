# -*- coding: utf-8 -*-
"""M17-RC1 §B — CATALOG AUTO-DISCOVERY: ma trận sinh TỪ REGISTRY.

Nguyên tắc cứng: **KHÔNG viết tay danh sách target**. Mọi hàng của ma trận đọc
từ `CATALOG` + `FAMILY_SELECTORS` + `AUTHENTICITY_CONTRACTS` + fixture audit
sống. Thêm target thứ 20 → tự xuất hiện; thiếu mảnh nào → báo đúng mảnh đó.

Ba lớp kiểm (mỗi lớp trả list vi phạm, rỗng = đạt):
1. `target_conformance` — mỗi AI-reachable target có đủ: analyze/classify
   exposure, ownership, validator, executor, renderer, learner error mapping,
   audit fixture.
2. `mechanism_ownership` — cơ chế analyze-exposed phải owned XOR intentional-gap;
   không owner trùng ngoài khai báo.
3. `source_runtime_parity` — không target nào có ở source mà mất ở runtime.
"""

from __future__ import annotations

from app.simulation.authenticity import AUTHENTICITY_CONTRACTS
from app.simulation.catalog import CATALOG, llm_choices
from app.simulation.descriptor import ReachabilityLevel
from app.simulation.families import FAMILY_SELECTORS, selector_for_token
from app.simulation.mechanisms import (
    FAMILY_MECHANISMS,
    INTENTIONAL_GAP_MECHANISMS,
    analyze_exposed_values,
    canonical_mechanism,
)

# Cơ chế được PHÉP có nhiều owner — khai TƯỜNG MINH, kèm lý do. Ngoài danh sách
# này, hai target cùng sở hữu một cơ chế là vi phạm (mơ hồ quyền sở hữu).
_SCAN_CATCH_ALL = (
    "algorithm.scan là CATCH-ALL TRONG-FAMILY của single_pass_scan (M15 W2 "
    "Task 12): nó sở hữu TOÀN BỘ cơ chế quét-một-lượt để nhận biến thể ngoài 5 "
    "bài chuyên biệt. Trùng owner với bài chuyên biệt là CÓ CHỦ ĐÍCH — classify "
    "vẫn ưu tiên bài chuyên biệt khi khớp trọn."
)
DECLARED_MULTI_OWNER: dict[str, str] = {
    "single_pass_scan.track_extreme":
        "find_max + find_min (cùng cơ chế, khác chiều so sánh) + " + _SCAN_CATCH_ALL,
    "single_pass_scan.accumulate_conditional": "sum_if + " + _SCAN_CATCH_ALL,
    "single_pass_scan.count_conditional": "count_if + " + _SCAN_CATCH_ALL,
    "single_pass_scan.find_equal_early_stop": "linear_search + " + _SCAN_CATCH_ALL,
    "positional_representation.binary_positional_weights":
        "decimal_to_binary (trực quan bit) + base_conversion (đổi cơ số tổng quát)",
    "comparison_sort.adjacent_compare_swap":
        "bubble_sort concrete + selector comparison_sort (token, không phải target)",
    "comparison_sort.shift_into_sorted_prefix":
        "insertion_sort concrete + selector comparison_sort (token ảo, không phải target)",
    "comparison_sort.select_extreme_repeated":
        "selection_sort concrete + selector comparison_sort (token ảo, không phải target)",
}


def ai_reachable_ids() -> list[str]:
    return sorted(
        sid for sid, spec in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    )


def _classify_exposed(sim_id: str) -> bool:
    """Target với tới được qua classify: hoặc là choice trực tiếp, hoặc nấp sau
    một selector token (variant) — cả hai đều hợp lệ."""
    if sim_id in llm_choices():
        return True
    for token in llm_choices():
        sel = selector_for_token(token)
        if sel and any(v.concrete_simulation_id == sim_id for v in sel.variants):
            return True
    return False


def _analyze_exposed_mechanisms(sim_id: str) -> list[str]:
    """Cơ chế của target NÀY mà analyze có thể phát tín hiệu (có thể rỗng —
    hợp lệ: nhiều family route thuần bằng classify, xem claim boundary M15)."""
    owned = {m for mb in CATALOG[sim_id].family_memberships for m in mb.owned_mechanisms}
    exposed = {canonical_mechanism(v) for v in analyze_exposed_values()}
    return sorted(owned & {e for e in exposed if e})


def build_matrix(audit_fixture_ids: set[str] | None = None) -> list[dict]:
    """Ma trận catalog — MỘT hàng mỗi AI-reachable target, sinh từ registry."""
    from app.evaluation.authenticity_fixtures import TARGET_FIXTURES

    fixtures = audit_fixture_ids if audit_fixture_ids is not None else set(TARGET_FIXTURES)
    rows = []
    for sid in ai_reachable_ids():
        spec = CATALOG[sid]
        contract = AUTHENTICITY_CONTRACTS.get(sid)
        variants: list[str] = []
        for token, sel in FAMILY_SELECTORS.items():  # noqa: B007
            for v in sel.variants:
                if v.concrete_simulation_id == sid:
                    variants.append(v.variant_id)
        rows.append({
            "target_id": sid,
            "family_ids": sorted({m.family_id.value for m in spec.family_memberships}),
            "owned_mechanisms": sorted(
                {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
            ),
            "supported_variants": sorted(variants),
            "validator_id": getattr(spec.validate, "__name__", None)
                            or getattr(getattr(spec.validate, "func", None), "__name__", None),
            "executor_id": spec.executor_id,
            "renderer_id": spec.domain,
            "config_contract_version": spec.config_contract_version,
            "analyze_exposed_mechanisms": _analyze_exposed_mechanisms(sid),
            "classify_exposed": _classify_exposed(sid),
            "required_grounded_inputs": sorted(contract.required_state_fields) if contract else [],
            "required_trace_events": sorted(contract.required_trace_events) if contract else [],
            "near_miss_mechanisms": sorted(contract.near_miss_mechanisms) if contract else [],
            "authenticity_contract": contract is not None,
            "has_audit_fixture": sid in fixtures,
            "curriculum_anchor": spec.curriculum_anchor,
            "known_gaps": list(spec.known_gaps),
        })
    return rows


def target_conformance(rows: list[dict] | None = None) -> list[dict]:
    """Mỗi AI-reachable target phải đủ mảnh. Trả list vi phạm."""
    rows = rows if rows is not None else build_matrix()
    out = []
    for r in rows:
        for field, code in (
            ("classify_exposed", "MISSING_CLASSIFY_EXPOSURE"),
            ("authenticity_contract", "MISSING_AUTHENTICITY_CONTRACT"),
            ("has_audit_fixture", "MISSING_AUDIT_FIXTURE"),
        ):
            if not r[field]:
                out.append({"target_id": r["target_id"], "code": code})
        if not r["validator_id"]:
            out.append({"target_id": r["target_id"], "code": "MISSING_VALIDATOR"})
        if not r["executor_id"]:
            out.append({"target_id": r["target_id"], "code": "MISSING_EXECUTOR"})
        if not r["renderer_id"]:
            out.append({"target_id": r["target_id"], "code": "MISSING_RENDERER"})
        if not r["owned_mechanisms"]:
            out.append({"target_id": r["target_id"], "code": "MISSING_OWNERSHIP"})
        if not r["config_contract_version"]:
            out.append({"target_id": r["target_id"], "code": "MISSING_CONFIG_CONTRACT"})
    return out


def mechanism_ownership() -> list[dict]:
    """Cơ chế analyze-exposed phải owned XOR intentional-gap; owner trùng phải
    được khai tường minh."""
    out = []
    owners: dict[str, list[str]] = {}
    for sid, spec in CATALOG.items():
        for mb in spec.family_memberships:
            for m in mb.owned_mechanisms:
                owners.setdefault(m, []).append(sid)

    for raw in analyze_exposed_values():
        canon = canonical_mechanism(raw)
        if canon is None:
            continue  # "none" = không ép cơ chế
        is_owned = canon in owners
        is_gap = canon in INTENTIONAL_GAP_MECHANISMS
        if is_owned == is_gap:  # phải ĐÚNG MỘT trong hai
            out.append({
                "mechanism": canon,
                "code": "MECHANISM_OWNED_XOR_GAP_VIOLATION",
                "owned_by": owners.get(canon, []),
                "intentional_gap": is_gap,
            })

    for m, sids in owners.items():
        if len(sids) > 1 and m not in DECLARED_MULTI_OWNER:
            out.append({"mechanism": m, "code": "UNDECLARED_MULTI_OWNER", "owned_by": sorted(sids)})

    # cơ chế trong taxonomy nhưng KHÔNG owner và KHÔNG khai gap → rơi tự do
    for mechs in FAMILY_MECHANISMS.values():
        for m in mechs:
            if m not in owners and m not in INTENTIONAL_GAP_MECHANISMS:
                out.append({"mechanism": m, "code": "ORPHAN_MECHANISM"})
    return out


def source_runtime_parity(runtime: dict | None) -> list[dict]:
    """Không target/family/renderer nào có ở source mà mất ở runtime."""
    if not runtime:
        return [{"code": "RUNTIME_UNAVAILABLE"}]
    out = []
    src_targets = set(CATALOG)
    rt_targets = set(runtime.get("registered_target_ids", []))
    for missing in sorted(src_targets - rt_targets):
        out.append({"code": "MISSING_RUNTIME_TARGET", "target_id": missing})
    src_renderers = {s.domain for s in CATALOG.values()}
    for missing in sorted(src_renderers - set(runtime.get("registered_renderer_ids", []))):
        out.append({"code": "MISSING_RUNTIME_RENDERER", "renderer_id": missing})
    return out
