# -*- coding: utf-8 -*-
"""Controlled feature-flagged integration adapter (`dynamic-construction-integration-adapter/1`).

Implements `AXO_DYNAMIC_CONSTRUCTION_MODE` with 3 isolated modes:
- `"off"` (default): runs ONLY verified product pipeline `function_route.run_fact_route` + `adapter4_route.build_adapter4_response`
- `"shadow"`: serves verified product pipeline, runs Dynamic Construction Planner offline on Source-Gate-verified input,
  and emits `ShadowComparisonReceipt` without affecting user output or performing any external AI call
- `"experimental"`: uses Dynamic Construction Planner ONLY when Source Gate accepts, L0–L4 passes, Scene3D passes
  `validate_construction_continuity`, and execution completes within timeout; otherwise fails closed or safely falls
  back ONLY to verified product output when the legacy path itself passes Source Gate + Kernel verification.
"""
from __future__ import annotations

import os
import time
from typing import Any, Literal

from app.ai import adapter4_route, function_route

from . import INTEGRATION_ADAPTER_VERSION
from .construction_search import DynamicConstructionPlanner, SearchBudget
from .construction_verifier import verify_full_proof_and_scene
from .presentation_validator import compile_multiplan_scene3d_bundle
from .scene3d_bridge import compile_proof_graph_to_scene3d
from .verified_input_bridge import bridge_verified_facts_to_construction_input

DynamicMode = Literal["off", "shadow", "experimental"]
VALID_DYNAMIC_MODES = frozenset({"off", "shadow", "experimental"})

os.environ.setdefault("ALLOW_LIVE_AI", "0")
os.environ.setdefault("GEMINI_API_KEY", "")


def resolve_dynamic_construction_mode(explicit_mode: str | None = None) -> DynamicMode:
    raw = (explicit_mode if explicit_mode is not None else os.environ.get("AXO_DYNAMIC_CONSTRUCTION_MODE", "off")).strip().lower()
    if raw not in VALID_DYNAMIC_MODES:
        return "off"
    return raw  # type: ignore[return-value]


def run_with_dynamic_construction_mode(
    *,
    case_id: str,
    problem_text: str,
    raw_facts_payload: dict[str, Any],
    mode: str | None = None,
    budget: SearchBudget | None = None,
    force_experimental_failure: bool = False,
) -> dict[str, Any]:
    """Execute controlled integration mode without modifying `backend/app/**` or `HYBRID_ROUTE_MODE`."""
    active_mode = resolve_dynamic_construction_mode(mode)
    t0 = time.perf_counter()

    # Always run verified product pipeline (`function_route.run_fact_route` -> `build_adapter4_response`)
    from copy import deepcopy
    from hashlib import sha256

    t_legacy0 = time.perf_counter()
    kq_legacy = function_route.run_fact_route(problem_text, raw_facts_payload)
    if problem_text and not kq_legacy.ai.get("source_sha256"):
        kq_legacy.ai["source_sha256"] = sha256(problem_text.encode("utf-8")).hexdigest()
        kq_legacy.route_d = deepcopy(adapter4_route._phong_bi(kq_legacy))
    resp_legacy = adapter4_route.build_adapter4_response(kq_legacy, problem_text)
    legacy_ms = round((time.perf_counter() - t_legacy0) * 1000.0, 3)

    legacy_status = kq_legacy.status
    legacy_ans = str((kq_legacy.answers or {}).get("q1") or "") or None
    legacy_served_verified = (
        legacy_status == "SERVED"
        and resp_legacy.get("route_d", {}).get("status") == "SERVED"
        and kq_legacy.kernel_check is True
    )

    if active_mode == "off":
        return {
            "adapter_version": INTEGRATION_ADAPTER_VERSION,
            "mode": "off",
            "served_by": "LEGACY_PRODUCT_PIPELINE",
            "status": legacy_status,
            "code": kq_legacy.code,
            "answer": legacy_ans,
            "scene3d": (resp_legacy.get("envelope") or {}).get("scene3d"),
            "fallback_used": False,
            "shadow_receipt": None,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    # For shadow or experimental: bridge verified input through Source Gate first (zero Source Gate bypass)
    t_dyn0 = time.perf_counter()
    bridge_res = bridge_verified_facts_to_construction_input(
        case_id=case_id,
        problem_text=problem_text,
        raw_facts_payload=raw_facts_payload,
    )
    dyn_status = "REFUSED"
    dyn_code = bridge_res.source_gate_code
    dyn_ans: str | None = None
    dyn_l0_l4 = False
    dyn_bundle: dict[str, Any] | None = None
    dyn_scene: dict[str, Any] | None = None
    dyn_plans_count = 0

    if not force_experimental_failure and bridge_res.accepted and bridge_res.frame is not None and bridge_res.goal_spec is not None:
        dp = DynamicConstructionPlanner(mode="v2")
        res = dp.plan(frame=bridge_res.frame, goal_spec=bridge_res.goal_spec, budget=budget or SearchBudget())
        dyn_status = res.status
        dyn_code = res.failure_code
        dyn_plans_count = len(res.plans)
        if res.status == "GOAL_VERIFIED" and res.best_plan is not None:
            bp = res.best_plan
            dyn_scene = compile_proof_graph_to_scene3d(bridge_res.frame, bp.proof_graph, bp.presentation_graph)
            full_rep = verify_full_proof_and_scene(bp.proof_graph, bridge_res.frame.chart_metric, scene3d=dyn_scene, strict_node_replay=True)
            dyn_l0_l4 = full_rep.passed
            if dyn_l0_l4:
                dyn_ans = bp.answer
                dyn_bundle = compile_multiplan_scene3d_bundle(bridge_res.frame, res.plans)
            else:
                dyn_status = "VERIFICATION_FAILED"
                dyn_code = full_rep.failure_code
    elif force_experimental_failure:
        dyn_status = "SEARCH_TIMEOUT"
        dyn_code = "FORCED_TIMEOUT_FAULT_INJECTION"

    dyn_ms = round((time.perf_counter() - t_dyn0) * 1000.0, 3)
    shadow_receipt = {
        "source_gate_status": bridge_res.source_gate_status,
        "legacy_status": legacy_status,
        "legacy_code": kq_legacy.code,
        "legacy_answer": legacy_ans,
        "legacy_ms": legacy_ms,
        "dynamic_status": dyn_status,
        "dynamic_code": dyn_code,
        "dynamic_answer": dyn_ans,
        "dynamic_l0_l4_verified": dyn_l0_l4,
        "dynamic_plans_count": dyn_plans_count,
        "dynamic_ms": dyn_ms,
        "answers_match": (legacy_ans == dyn_ans) if (legacy_ans and dyn_ans) else None,
        "user_impact": "NONE",
    }

    if active_mode == "shadow":
        return {
            "adapter_version": INTEGRATION_ADAPTER_VERSION,
            "mode": "shadow",
            "served_by": "LEGACY_PRODUCT_PIPELINE",
            "status": legacy_status,
            "code": kq_legacy.code,
            "answer": legacy_ans,
            "scene3d": (resp_legacy.get("envelope") or {}).get("scene3d"),
            "fallback_used": False,
            "shadow_receipt": shadow_receipt,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    # active_mode == "experimental"
    if dyn_status == "GOAL_VERIFIED" and dyn_l0_l4 and dyn_scene is not None and dyn_bundle is not None:
        if dyn_bundle["multiplan_validation"]["valid"]:
            return {
                "adapter_version": INTEGRATION_ADAPTER_VERSION,
                "mode": "experimental",
                "served_by": "DYNAMIC_CONSTRUCTION_PLANNER_V2",
                "status": "SERVED",
                "code": None,
                "answer": dyn_ans,
                "scene3d": dyn_scene,
                "multiplan_bundle": dyn_bundle,
                "fallback_used": False,
                "shadow_receipt": shadow_receipt,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
            }

    # Fail-closed or verified fallback to legacy ONLY if legacy itself passed Source Gate + Kernel checks
    if legacy_served_verified and bridge_res.source_gate_status == "VERIFIED":
        return {
            "adapter_version": INTEGRATION_ADAPTER_VERSION,
            "mode": "experimental",
            "served_by": "SAFE_VERIFIED_LEGACY_FALLBACK",
            "status": legacy_status,
            "code": kq_legacy.code,
            "answer": legacy_ans,
            "scene3d": (resp_legacy.get("envelope") or {}).get("scene3d"),
            "fallback_used": True,
            "fallback_reason": dyn_code or dyn_status,
            "shadow_receipt": shadow_receipt,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    # Neither dynamic nor legacy verified -> fail-closed REFUSED
    return {
        "adapter_version": INTEGRATION_ADAPTER_VERSION,
        "mode": "experimental",
        "served_by": "FAIL_CLOSED_REFUSED",
        "status": "REFUSED",
        "code": dyn_code or kq_legacy.code or "REFUSED",
        "answer": None,
        "scene3d": None,
        "fallback_used": False,
        "shadow_receipt": shadow_receipt,
        "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
    }
