"""Representation Plan (M7.11) — bước trung gian TẤT ĐỊNH giữa analysis và
SimulationSpec.

analysis (semantic requirements) → representation plan → SimulationSpec.

Plan suy TỪ manifest role taxonomy (không LLM, không hard-code môn học): gom
vai trò ngữ nghĩa đề cần, ánh xạ sang năng lực DSL, xác định scene_mode và
các vai trò KHÔNG biểu diễn được (capability gap).
"""

from __future__ import annotations

from app.simulation.dsl.manifest import (
    SEMANTIC_ROLES,
    all_coverable_roles,
    primitives_for_role,
)

_ROLE_FIELDS = [
    "entity_roles",
    "relation_roles",
    "process_roles",
    "interaction_needs",
    "visual_needs",
    "temporal_needs",
]


def required_roles(analysis: dict) -> set[str]:
    """Hợp mọi vai trò ngữ nghĩa từ các trường requirement của analysis."""
    roles: set[str] = set()
    for field in _ROLE_FIELDS:
        for r in analysis.get(field) or []:
            if r in SEMANTIC_ROLES:
                roles.add(r)
    return roles


def _scene_mode(analysis: dict, roles: set[str]) -> str:
    has_temporal = "temporal" in roles or analysis.get("scene_construction") == "step_by_step"
    has_interactive = "interactive" in roles
    if has_temporal and has_interactive:
        return "hybrid"
    if has_temporal:
        return "progressive"
    return "exploratory"


def build_representation_plan(analysis: dict) -> dict:
    """Trả representation plan tất định (dùng trước khi sinh SimulationSpec)."""
    roles = required_roles(analysis)
    coverable = all_coverable_roles()
    unsupported = sorted(roles - coverable)
    caps = sorted({p for r in roles for p in primitives_for_role(r)})
    return {
        "semantic_roles": sorted(roles),
        "required_dsl_capabilities": caps,
        "scene_mode": _scene_mode(analysis, roles),
        "mapping_intent": {r: primitives_for_role(r) for r in sorted(roles)},
        "unsupported_capabilities": unsupported,
    }
