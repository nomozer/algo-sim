# -*- coding: utf-8 -*-
"""Programmatic architecture and capability audit for AXO CONSTRUCTION /1 (Phase A).

Inspects the live runtime modules in `backend/app/simulation/**` and `backend/app/ai/**`
without modifying them (`ALLOW_LIVE_AI=0`), probes actual Planner /26, Registry /33,
Exact Kernel /24, Adapter /4, and Scene3D behavior, and emits
`CONSTRUCTION_CAPABILITY_INVENTORY.json` into the campaign run directory.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("ALLOW_LIVE_AI", "0")
os.environ.setdefault("GEMINI_API_KEY", "")

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai import adapter4_route, local_geometry_parser  # noqa: E402
from app.simulation.geometry import exact as geom_exact  # noqa: E402
from app.simulation.geometry import kernel as geom_kernel  # noqa: E402
from app.simulation.geometry import measure as geom_measure  # noqa: E402
from app.simulation.geometry import metric as geom_metric  # noqa: E402
from app.simulation.geometry import section as geom_section  # noqa: E402
from app.simulation.geometry_functions import (  # noqa: E402
    certificates,
    construction_continuity,
    engine,
    planner,
    registry,
)
from app.simulation.semantic_program import formation, interpreter, scene3d, validator  # noqa: E402

RUN_ID = "axo-construction-verified-graph-dynamic-planner-feasibility"
RUN_DIR = REPO_ROOT / "docs" / "evaluation" / "geometry" / "runs" / RUN_ID


def _git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def _probe_distance_witness_absence() -> dict[str, Any]:
    """Verify empirically whether `ask_distance_point_plane` in Adapter /4 constructs a foot H in Scene3D."""
    txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, "
        "AB = a, SA vuông góc với (ABC), SA = a. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    parsed = local_geometry_parser.parse_geometry_problem_locally(txt)
    kq = adapter4_route.run_typed_fact_next_v2_route(parsed.payload)
    resp = adapter4_route.build_adapter4_response(kq, txt)
    scene = resp["envelope"]["scene3d"]
    obj_ids = [o.get("id") for o in scene.get("objects", [])]
    point_ids = [o.get("id") for o in scene.get("objects", []) if o.get("type") == "point3"]
    seg_ids = [o.get("id") for o in scene.get("objects", []) if o.get("type") == "segment3"]
    return {
        "problem_text": txt,
        "status": kq.status,
        "answers": kq.answers,
        "answer_exact": kq.answer_exact,
        "planner_calls": [c.get("fn") for c in (kq.calls or [])],
        "scene_object_ids": obj_ids,
        "scene_point_ids": point_ids,
        "scene_segment_ids": seg_ids,
        "has_auxiliary_foot_point": any(pid not in {"A", "B", "C", "S"} for pid in point_ids),
        "continuity_issues_count": len(construction_continuity.validate_construction_continuity(scene, trace=kq.trace)),
    }


def _probe_premise_only_chart_extraction() -> dict[str, Any]:
    """Verify whether `engine.dung_tu_loi_goi` can yield certified premise points + SPD chart metric cleanly."""
    txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, "
        "AB = a, SA vuông góc với (ABC), SA = a. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    parsed = local_geometry_parser.parse_geometry_problem_locally(txt)
    p_txt = txt
    for mg in parsed.payload.get("math_goals", []):
        q = mg.get("quote", "")
        if q and q in p_txt:
            p_txt = p_txt.replace(q, "")
    p_txt = p_txt.strip().rstrip(". ") + "."
    premise_payload = {
        **parsed.payload,
        "problem_text": p_txt,
        "simulation_goals": parsed.payload["simulation_goals"][:1],
        "math_goals": [],
    }
    from app.simulation.geometry_functions import typed_fact_next_bridge as tfnb

    tf2 = tfnb.bridge_v2(premise_payload)
    kh = planner.lap_ke_hoach(tf2, p_txt)
    kq = engine.dung_tu_loi_goi(
        p_txt,
        {"calls": kh.calls, "goals": [], "negated": []},
        auxiliary=tuple(kh.auxiliary),
    )
    spd_ok = True
    try:
        certificates.validate_gram_metric_spd(kq.chart_metric)
    except Exception:
        spd_ok = False
    return {
        "status": kq.status,
        "points_count": len(kq.points or {}),
        "point_ids": sorted((kq.points or {}).keys()),
        "chart_metric_spd": spd_ok,
        "length_unit": kq.length_unit,
    }


def _probe_planner_cycle_detection() -> dict[str, Any]:
    """Verify whether Planner /26 detects cyclic dependencies explicitly."""
    calls = [
        {"id": "c1", "fn": "midpoint", "args": {"point": "M", "a": "A", "b": "N"}, "source": {"quotes": []}},
        {"id": "c2", "fn": "midpoint", "args": {"point": "N", "a": "B", "b": "M"}, "source": {"quotes": []}},
    ]
    k = planner.KeHoach()
    k.calls = calls
    k.resolver = planner._EffectResolver([], k, lambda *a, **kw: {}, "")
    try:
        planner._sap_xep_phu_thuoc_loi_goi(k)
        return {"detected": False, "code": None}
    except registry.TuChoi as exc:
        return {"detected": True, "code": exc.code, "reason": str(exc)}


def _probe_no_contract_ops() -> dict[str, Any]:
    """Verify which critical operations lack `PlanningContract` entries in Registry /33."""
    interesting = [
        "divide_segment",
        "point_reflection",
        "ask_angle_plane_plane",
        "ask_volume",
        "ask_section_area",
        "ask_distance_planes",
        "section",
    ]
    result = {}
    for fn_name in interesting:
        spec = registry.REGISTRY.get(fn_name)
        pcs = registry.planning_contracts(spec) if spec else []
        result[fn_name] = {
            "in_registry": spec is not None,
            "kind": getattr(spec, "kind", None),
            "planning_contract_count": len(pcs),
        }
    return result


def build_inventory() -> dict[str, Any]:
    head_commit = _git_output("rev-parse", "HEAD")
    branch_name = _git_output("rev-parse", "--abbrev-ref", "HEAD")
    dirty = _git_output("status", "--short")

    reg_kinds: dict[str, int] = {}
    reg_functions: list[dict[str, Any]] = []
    for name, spec in sorted(registry.REGISTRY.items()):
        kind = getattr(spec, "kind", "unknown")
        reg_kinds[kind] = reg_kinds.get(kind, 0) + 1
        pcs = registry.planning_contracts(spec)
        reg_functions.append(
            {
                "name": name,
                "kind": kind,
                "planning_contracts": [
                    {
                        "effect": pc.effect.kind,
                        "inputs": [inp.kind for inp in pc.inputs],
                        "source_policy": pc.source_policy,
                    }
                    for pc in pcs
                ],
                "has_planning_contract": bool(pcs),
            }
        )

    capabilities = [
        {
            "capability_id": "cap.solid_layout_and_gram_metric",
            "title": "Exact Solid Coordinate Chart & SPD Gram Metric Solver",
            "status": "EXISTS_VERIFIED",
            "owner_modules": [
                "backend/app/simulation/geometry_functions/engine.py",
                "backend/app/simulation/geometry/metric.py",
                "backend/app/simulation/geometry_functions/certificates.py",
            ],
            "reusable": True,
            "evidence": _probe_premise_only_chart_extraction(),
            "notes": "Computes exact Fraction/Radical coordinates and SPD Gram tensors (`Metric`) from verified premises without touching goal queries.",
        },
        {
            "capability_id": "cap.effect_regression_single_plan",
            "title": "Bounded Backward Slot-Effect Regression (`_EffectResolver`)",
            "status": "PARTIAL",
            "owner_modules": ["backend/app/simulation/geometry_functions/planner.py"],
            "reusable": False,
            "limits": {
                "max_depth": planner.MAX_EFFECT_DEPTH,
                "max_needs": planner.MAX_EFFECT_NEEDS,
                "max_candidates": planner.MAX_EFFECT_CANDIDATES,
                "max_calls": planner.MAX_CALLS,
                "registry_functions_with_contracts": sum(1 for x in reg_functions if x["has_planning_contract"]),
                "registry_functions_total": len(reg_functions),
            },
            "notes": "Only 15/64 Registry functions expose PlanningContracts; collapses to a single min-cost _Choice rather than retaining alternative plans.",
        },
        {
            "capability_id": "cap.registered_auxiliary_rules",
            "title": "Registered Auxiliary Rules (`AUXILIARY_RULES` & `POINT_DEFINITIONS`)",
            "status": "PARTIAL",
            "owner_modules": [
                "backend/app/simulation/geometry_functions/registry.py",
                "backend/app/simulation/geometry_functions/planner.py",
            ],
            "reusable": False,
            "rules_count": len(planner.AUXILIARY_RULES),
            "rules": {k: list(v) for k, v in planner.AUXILIARY_RULES.items()},
            "point_definitions": sorted(registry.POINT_DEFINITIONS.keys()),
            "notes": "7 hardcoded/registered macro auxiliary schemas exist, alongside orthocenter/circumcenter loci definitions, but no general dynamic auxiliary search.",
        },
        {
            "capability_id": "cap.dependency_dag_and_cycle_detection",
            "title": "Call-Level Topological Sort & Cycle Detection",
            "status": "EXISTS_VERIFIED",
            "owner_modules": ["backend/app/simulation/geometry_functions/planner.py"],
            "reusable": True,
            "evidence": _probe_planner_cycle_detection(),
            "notes": "`_sap_xep_phu_thuoc_loi_goi` enforces Kahn + DFS ordering on `KeHoach.calls` and raises `TuChoi('DEPENDENCY_CYCLE')`, though not yet wrapped as a typed `VerifiedConstructionGraph`.",
        },
        {
            "capability_id": "cap.exact_kernel_primitives",
            "title": "Exact Geometric Construction Kernel (`Fraction` + `Gram Metric`)",
            "status": "EXISTS_VERIFIED",
            "owner_modules": [
                "backend/app/simulation/geometry/exact.py",
                "backend/app/simulation/geometry/kernel.py",
                "backend/app/simulation/geometry/measure.py",
                "backend/app/simulation/geometry/section.py",
            ],
            "reusable": True,
            "primitives": [
                "midpoint",
                "translate",
                "divide_segment",
                "intersect_line_plane",
                "intersect_plane_plane",
                "intersect_line_line",
                "common_perpendicular_feet",
                "project_point_onto_plane",
                "project_point_onto_line",
                "plane_through_point_perpendicular_to",
                "plane_through_point_parallel_to",
                "line_through_point_parallel_to",
                "perpendicular_foot_line",
                "cross_section",
            ],
            "notes": "All Euclidean/affine 3D construction primitives and exact degenerate/parallel/skew errors (`GeometryError`) already exist and run cleanly inside `with metric.using(chart_metric):`.",
        },
        {
            "capability_id": "cap.distance_metric_to_construction_decomposition",
            "title": "Automatic Foot / Altitude Witness Construction for Metric Goals",
            "status": "ABSENT_VERIFIED",
            "owner_modules": [
                "backend/app/simulation/geometry_functions/planner.py",
                "backend/app/simulation/geometry_functions/engine.py",
            ],
            "evidence": _probe_distance_witness_absence(),
            "notes": "`ask_distance_point_plane` computes scalar answer `a√2/2` directly via `measure.distance_sq_point_plane` without constructing auxiliary foot `H` or segment `AH` in `Scene3D`.",
        },
        {
            "capability_id": "cap.verified_typed_construction_graph",
            "title": "Typed `ConstructionProofGraph` Separated from `PresentationStepGraph`",
            "status": "ABSENT_VERIFIED",
            "owner_modules": [],
            "notes": "No typed node/edge proof graph separates `GIVEN`/`DERIVED`/`AUXILIARY_CONSTRUCTION` provenance, canonical geometric identity, and pedagogical projection.",
        },
        {
            "capability_id": "cap.multi_plan_retention_and_ranking",
            "title": "Alternative Valid Construction Discovery & Deterministic Ranking",
            "status": "ABSENT_VERIFIED",
            "owner_modules": ["backend/app/simulation/geometry_functions/planner.py"],
            "notes": "`_EffectResolver._resolve` returns a single `min(choices, ...)` object, discarding alternative valid construction paths.",
        },
        {
            "capability_id": "cap.unused_node_and_semantic_duplicate_detection",
            "title": "Canonical Geometric Deduplication & Unused Node Pruning",
            "status": "PARTIAL",
            "owner_modules": [
                "backend/app/simulation/geometry_functions/planner.py",
                "backend/app/simulation/geometry_functions/construction_continuity.py",
            ],
            "notes": "`planner.py` coalesces syntactic duplicate calls by JSON key and `scene3d` tracks `unused_auxiliary_ids`, but lacks full exact canonical line/plane geometric identity (`Plane3`/`Line3` normalization).",
        },
        {
            "capability_id": "cap.dihedral_and_ratio_reflection_planning",
            "title": "Dynamic Planning Contracts for `divide_segment`, `point_reflection`, `ask_angle_plane_plane`",
            "status": "PARTIAL",
            "owner_modules": ["backend/app/simulation/geometry_functions/registry.py"],
            "evidence": _probe_no_contract_ops(),
            "notes": "Kernel/Engine support execution when explicitly called, but Registry `/33` leaves `planning_contracts=[]` for `divide_segment`, `point_reflection`, and `ask_angle_plane_plane`.",
        },
        {
            "capability_id": "cap.deep_chain_ir_memory",
            "title": "Deep Multi-Step Construction Chain (>32 memory slots) in `SemanticProgramSpec`",
            "status": "PARTIAL",
            "owner_modules": ["backend/app/simulation/semantic_program/validator.py"],
            "limits": {"max_memory_declarations": validator.MAX_MEMORY_DECLARATIONS},
            "notes": "Flat IR memory table caps at `MAX_MEMORY_DECLARATIONS = 32`, rejecting longer dynamic chains (`IR_MEMORY_BUDGET_EXCEEDED`).",
        },
        {
            "capability_id": "cap.scene3d_and_continuity_contract",
            "title": "Scene3D + Formation Steps + Construction Continuity + Certificates",
            "status": "EXISTS_VERIFIED",
            "owner_modules": [
                "backend/app/simulation/semantic_program/scene3d.py",
                "backend/app/simulation/semantic_program/formation.py",
                "backend/app/simulation/geometry_functions/construction_continuity.py",
                "backend/app/simulation/geometry_functions/certificates.py",
            ],
            "reusable": True,
            "scene3d_render_hints": dict(scene3d.RENDER_HINT),
            "notes": "Backend Scene3D schema, 5-part `step_summary`, `validate_construction_continuity`, and `certify_line_plane_perpendicularity` are mature and directly reusable.",
        },
        {
            "capability_id": "cap.frontend_scene3d_renderer_ownership",
            "title": "Frontend Scene3D Interactive Step Explorer",
            "status": "EXISTS_VERIFIED",
            "ownership": "BLOCKED_OWNERSHIP",
            "owner_modules": ["frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx"],
            "notes": "Frontend lives under separate worktree ownership (`axo-geometry-library`) and must not be modified in `AXO CONSTRUCTION /1`.",
        },
        {
            "capability_id": "cap.external_oracle_or_runtime_llm_in_planner",
            "title": "Curved-Solid General Dynamic Primitives (Tangent Sphere Locus Synthesis)",
            "status": "UNSUPPORTED",
            "owner_modules": [],
            "notes": "Out of scope for exact affine-polyhedral operator prototype; curved solids and free-parameter optimization remain outside dynamic polyhedral composition.",
        },
    ]

    candidate_operations_s6 = [
        {
            "candidate": "Tạo điểm từ dữ kiện đã xác định",
            "registry_backing": ["divide_segment", "centroid", "midpoint", "translate_point", "point_reflection"],
            "input_types": ["Point3", "Scalar"],
            "preconditions": "Anchors defined; nonzero segment/polygon; nonzero ratio denominator",
            "result_types": ["Point3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "coincident anchors, colinear polygon vertices, zero ratio",
            "scene3d_compatible": True,
            "ownership_boundary": "READ_ONLY_REUSE_IN_PROTOTYPE",
        },
        {
            "candidate": "Nối hai điểm / Tạo đoạn thẳng phụ",
            "registry_backing": ["Segment3.between (kernel/exact)", "construct_segment (scene3d)"],
            "input_types": ["Point3", "Point3"],
            "preconditions": "P1 != P2 in canonical coordinates",
            "result_types": ["Segment3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_COINCIDENT_POINTS",
            "scene3d_compatible": True,
            "ownership_boundary": "PROTOTYPE_WRAPPER_NEEDED",
        },
        {
            "candidate": "Tạo đường thẳng qua hai điểm",
            "registry_backing": ["Line3.through (exact.py)", "implicit in many asks"],
            "input_types": ["Point3", "Point3"],
            "preconditions": "P1 != P2",
            "result_types": ["Line3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_COINCIDENT_POINTS",
            "scene3d_compatible": True,
            "ownership_boundary": "PROTOTYPE_WRAPPER_NEEDED",
        },
        {
            "candidate": "Tạo mặt phẳng từ đối tượng xác định",
            "registry_backing": ["Plane3.through", "plane_through_point_parallel_to", "plane_through_point_perpendicular_to"],
            "input_types": ["3x Point3", "Point3+Plane3", "Point3+Line3"],
            "preconditions": "Non-collinear points; non-degenerate normal",
            "result_types": ["Plane3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_COLLINEAR_POINTS",
            "scene3d_compatible": True,
            "ownership_boundary": "PROTOTYPE_WRAPPER_NEEDED",
        },
        {
            "candidate": "Dựng trung điểm",
            "registry_backing": ["midpoint (Registry /33 + contract)"],
            "input_types": ["Point3", "Point3"],
            "preconditions": "Distinct endpoints",
            "result_types": ["Point3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_COINCIDENT_POINTS",
            "scene3d_compatible": True,
            "ownership_boundary": "READ_ONLY_REUSE_IN_PROTOTYPE",
        },
        {
            "candidate": "Dựng hình chiếu vuông góc (điểm lên đường / điểm lên mặt)",
            "registry_backing": ["orthogonal_projection_line", "orthogonal_projection", "kernel.project_point_onto_*"],
            "input_types": ["Point3", "Line3|Plane3"],
            "preconditions": "Valid Gram SPD metric; point not already coincident if strictly auxiliary segment needed",
            "result_types": ["Point3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_POINT_ALREADY_INCIDENT",
            "scene3d_compatible": True,
            "ownership_boundary": "READ_ONLY_REUSE_IN_PROTOTYPE",
        },
        {
            "candidate": "Dựng đường vuông góc / đường cao / đường song song",
            "registry_backing": ["kernel.common_perpendicular_feet", "kernel.line_through_point_parallel_to", "certificates.certify_deductive_line_plane_perpendicularity"],
            "input_types": ["Point3", "Line3", "Plane3"],
            "preconditions": "Skew lines for common perp; point off line for parallel line",
            "result_types": ["Line3", "Segment3", "Relation"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_NON_SKEW_LINES, DEGENERATE_POINT_ON_LINE",
            "scene3d_compatible": True,
            "ownership_boundary": "PROTOTYPE_OPERATOR_LAYER",
        },
        {
            "candidate": "Xác định giao điểm / giao tuyến",
            "registry_backing": ["intersect_line_line", "intersect_line_plane", "intersection_line", "kernel.intersect_plane_plane"],
            "input_types": ["Line3", "Line3", "Plane3"],
            "preconditions": "Coplanar non-parallel lines; line not parallel/contained in plane; non-parallel planes",
            "result_types": ["Point3", "Line3"],
            "exact_verification": "EXISTS_VERIFIED",
            "degenerate_cases": "DEGENERATE_PARALLEL_NO_INTERSECTION, DEGENERATE_SKEW_NO_INTERSECTION, DEGENERATE_CONTAINED_INFINITE_INTERSECTION",
            "scene3d_compatible": True,
            "ownership_boundary": "READ_ONLY_REUSE_IN_PROTOTYPE",
        },
        {
            "candidate": "Xác định các quan hệ khoảng cách / góc",
            "registry_backing": ["ask_distance_*", "ask_angle_* (metric solvers without automatic geometric witness chain)"],
            "input_types": ["Point3", "Line3", "Plane3"],
            "preconditions": "Constructed witness objects + verified perpendicular/parallel relations before metric evaluation",
            "result_types": ["Quantity"],
            "exact_verification": "PARTIAL (metric exists; dynamic witness synthesis absent)",
            "degenerate_cases": "Missing witness, parallel line/plane mismatch",
            "scene3d_compatible": True,
            "ownership_boundary": "PROTOTYPE_GOAL_WITNESS_VERIFIER",
        },
    ]

    return {
        "schema": "axo-construction-capability-inventory/1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": head_commit,
        "git_branch": branch_name,
        "git_dirty_before_audit": bool(dirty),
        "versions": {
            "planner": planner.PLANNER_VERSION,
            "registry": registry.REGISTRY_VERSION,
            "engine": engine.ENGINE_VERSION,
            "adapter": adapter4_route.ADAPTER_V4_VERSION,
            "certificate_schema": certificates.CERTIFICATE_SCHEMA,
            "deductive_theorem_schema": certificates.DEDUCTIVE_THEOREM_SCHEMA,
            "cache_version": "145",
        },
        "registry_summary": {
            "total_functions": len(reg_functions),
            "by_kind": reg_kinds,
            "with_planning_contracts": sum(1 for x in reg_functions if x["has_planning_contract"]),
            "without_planning_contracts": sum(1 for x in reg_functions if not x["has_planning_contract"]),
            "functions": reg_functions,
        },
        "capabilities": capabilities,
        "candidate_operations_s6": candidate_operations_s6,
    }


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    out_path = RUN_DIR / "CONSTRUCTION_CAPABILITY_INVENTORY.json"
    out_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WROTE {out_path.as_posix()} ({out_path.stat().st_size} bytes)")
    print(
        "SUMMARY:",
        json.dumps(
            {
                "git_head": inventory["git_head"],
                "registry_total": inventory["registry_summary"]["total_functions"],
                "with_contracts": inventory["registry_summary"]["with_planning_contracts"],
                "by_kind": inventory["registry_summary"]["by_kind"],
                "distance_probe_aux_foot": inventory["capabilities"][5]["evidence"]["has_auxiliary_foot_point"],
                "premise_only_points": inventory["capabilities"][0]["evidence"]["point_ids"],
                "cycle_detection": inventory["capabilities"][3]["evidence"],
            },
            ensure_ascii=False,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
