"""M14 — FAMILY_SELECTORS registry + cross-lock (§C1.3, §C4).

FAMILY_SELECTORS = bề mặt lựa chọn family cho LLM. Cross-lock với
family_memberships trên CATALOG (song ánh variant↔target) → không nguồn thứ hai.
"""

from __future__ import annotations

from app.simulation.families.base import FamilySelector, VariantSpec
from app.simulation.families.sorting import SORTING_SELECTOR

FAMILY_SELECTORS: dict[str, FamilySelector] = {
    SORTING_SELECTOR.family_id.value: SORTING_SELECTOR,
}

# family_id (giá trị enum) của các family CÓ selector — dùng để ẩn runtime target
# tương ứng khỏi menu classify (llm_choices).
SELECTOR_FAMILY_IDS: frozenset[str] = frozenset(
    sel.family_id.value for sel in FAMILY_SELECTORS.values()
)


def selector_for_token(token: str) -> FamilySelector | None:
    for sel in FAMILY_SELECTORS.values():
        if sel.selector_token == token:
            return sel
    return None


def _selector_internal_violations(sel: FamilySelector) -> list[str]:
    """Lỗi NỘI BỘ một selector (không cần CATALOG)."""
    v: list[str] = []
    seen: set[str] = set()
    for var in sel.variants:
        if var.variant_id in seen:
            v.append(f"{sel.family_id.value}: variant trùng '{var.variant_id}'")
        seen.add(var.variant_id)
        if var.mechanism_id not in sel.owned_mechanisms:
            v.append(
                f"{sel.family_id.value}/{var.variant_id}: mechanism_id "
                f"'{var.mechanism_id}' ∉ owned_mechanisms"
            )
    return v


def cross_lock_violations(catalog: dict) -> list[str]:
    """§C4 — song ánh selector.variants ↔ family_memberships của runtime target.

    Trả list lỗi (rỗng = nhất quán). Nhận `catalog` (inject) để tránh vòng import.
    """
    violations: list[str] = []
    for sel in FAMILY_SELECTORS.values():
        violations.extend(_selector_internal_violations(sel))
        # selector_token KHÔNG được trùng bất kỳ simulation_id nào (nó là token ảo)
        if sel.selector_token in catalog:
            violations.append(f"selector_token '{sel.selector_token}' trùng một simulation_id")
        # chiều xuôi: mỗi variant → target CÓ THẬT + membership khớp
        for var in sel.variants:
            spec = catalog.get(var.concrete_simulation_id)
            if spec is None:
                violations.append(
                    f"{sel.family_id.value}/{var.variant_id}: target "
                    f"'{var.concrete_simulation_id}' không có trong CATALOG"
                )
                continue
            match = [
                m for m in spec.family_memberships
                if m.family_id.value == sel.family_id.value
                and m.variant_id == var.variant_id
            ]
            if not match:
                violations.append(
                    f"{var.concrete_simulation_id}: thiếu membership khớp "
                    f"{sel.family_id.value}/{var.variant_id}"
                )
                continue
            if match[0].family_spec_version != sel.family_spec_version:
                violations.append(
                    f"{var.concrete_simulation_id}: family_spec_version lệch selector "
                    f"({match[0].family_spec_version} ≠ {sel.family_spec_version})"
                )
            if match[0].mechanism_id != var.mechanism_id:
                violations.append(
                    f"{var.concrete_simulation_id}: mechanism_id membership lệch variant"
                )
    # chiều ngược: target mang membership thuộc family-có-selector phải là đúng một variant
    for sim_id, spec in catalog.items():
        for m in spec.family_memberships:
            if m.family_id.value not in SELECTOR_FAMILY_IDS:
                continue
            sel = FAMILY_SELECTORS[m.family_id.value]
            hits = [var for var in sel.variants if var.concrete_simulation_id == sim_id]
            if len(hits) != 1:
                violations.append(
                    f"{sim_id}: membership {m.family_id.value} nhưng khớp {len(hits)} variant (≠1)"
                )
    return violations


__all__ = [
    "FamilySelector",
    "VariantSpec",
    "FAMILY_SELECTORS",
    "SELECTOR_FAMILY_IDS",
    "selector_for_token",
    "cross_lock_violations",
]
