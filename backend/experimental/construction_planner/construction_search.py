# -*- coding: utf-8 -*-
"""Bounded dynamic best-first construction planner (`dynamic-construction-planner/1`).

Discovers, verifies (L0-L3), deduplicates, collects multiple distinct valid plans,
and ranks them without access to external LLMs, hardcoded per-problem recipes, or
answer oracles.
"""
from __future__ import annotations

import heapq
import itertools
import time
import tracemalloc
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from app.simulation.geometry import exact as E
from app.simulation.geometry import measure as MS
from app.simulation.geometry import metric as M

from . import DYNAMIC_PLANNER_VERSION
from .construction_graph import (
    ConstructionNode,
    ConstructionProofGraph,
    PresentationStepGraph,
    project_to_presentation_graph,
)
from .construction_objects import (
    ConstructionObject,
    _json_safe,
    canonical_line_key,
    canonical_plane_key,
    canonical_point_key,
    canonical_polygon_key,
    canonical_segment_key,
)
from .construction_operators import (
    OPERATOR_SPECS,
    GoalSpec,
    evaluate_goal_if_witnessed,
    execute_operator,
)
from .construction_state import (
    InitialGeometryFrame,
    PendingConstruction,
    PlannerSearchState,
    make_initial_search_state,
    materialize_proof_graph_from_state,
)
from .construction_verifier import (
    VerificationError,
    VerificationReport,
    verify_full_proof_and_scene,
)


@dataclass(frozen=True)
class SearchBudget:
    """Hard resource bounds enforced at every expansion step."""

    max_depth: int = 8
    max_expanded_states: int = 250
    max_graph_nodes: int = 96
    max_candidate_operators: int = 600
    max_wall_clock_ms: float = 2000.0
    max_memory_mb: float = 128.0
    max_plans: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_depth": self.max_depth,
            "max_expanded_states": self.max_expanded_states,
            "max_graph_nodes": self.max_graph_nodes,
            "max_candidate_operators": self.max_candidate_operators,
            "max_wall_clock_ms": self.max_wall_clock_ms,
            "max_memory_mb": self.max_memory_mb,
            "max_plans": self.max_plans,
        }


@dataclass(frozen=True)
class RankedPlan:
    rank: int
    score_tuple: tuple[Any, ...]
    proof_graph: ConstructionProofGraph
    presentation_graph: PresentationStepGraph
    verification_report: VerificationReport
    answer: str
    answer_exact: dict[str, Any]
    operator_lineage: tuple[str, ...]

    def to_summary_dict(self) -> dict[str, Any]:
        aux_ids = [oid for oid, o in self.proof_graph.objects.items() if o.origin == "AUXILIARY_CONSTRUCTION"]
        return {
            "rank": self.rank,
            "answer": self.answer,
            "answer_exact": _json_safe(self.answer_exact),
            "operator_lineage": list(self.operator_lineage),
            "node_count": len(self.proof_graph.nodes),
            "presentation_step_count": len(self.presentation_graph.steps),
            "auxiliary_object_ids": sorted(aux_ids),
            "auxiliary_count": len(aux_ids),
            "score_tuple": list(self.score_tuple),
            "l0_l4_passed": self.verification_report.passed,
        }


@dataclass(frozen=True)
class DynamicPlannerResult:
    planner_version: str
    status: str  # GOAL_VERIFIED | NO_PLAN_FOUND_WITHIN_BUDGET | UNSUPPORTED_OPERATOR | MISSING_PRECONDITION | CONTRADICTORY_CONSTRAINTS | SEARCH_TIMEOUT | SEARCH_RESOURCE_LIMIT | VERIFICATION_FAILED
    case_id: str
    plans: tuple[RankedPlan, ...]
    failure_code: str | None
    failure_detail: str | None
    telemetry: dict[str, Any]

    @property
    def best_plan(self) -> RankedPlan | None:
        return self.plans[0] if self.plans else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "planner_version": self.planner_version,
            "status": self.status,
            "case_id": self.case_id,
            "failure_code": self.failure_code,
            "failure_detail": self.failure_detail,
            "plans": [p.to_summary_dict() for p in self.plans],
            "telemetry": _json_safe(self.telemetry),
        }


def _collect_typed_views(
    state: PlannerSearchState,
) -> tuple[dict[str, E.Point3], dict[str, E.Line3], dict[str, E.Plane3], dict[str, E.Segment3], dict[str, Any]]:
    pts = {oid: o.exact_value for oid, o in state.objects.items() if o.object_kind == "point3"}
    lns = {oid: o.exact_value for oid, o in state.objects.items() if o.object_kind == "line3"}
    pls = {oid: o.exact_value for oid, o in state.objects.items() if o.object_kind == "plane3"}
    segs = {oid: o.exact_value for oid, o in state.objects.items() if o.object_kind == "segment3"}
    secs = {oid: o.exact_value for oid, o in state.objects.items() if o.object_kind == "section"}
    return pts, lns, pls, segs, secs


def _resolve_object_by_ref(state: PlannerSearchState, ref: Any, kind: str) -> str | None:
    if isinstance(ref, str) and ref in state.objects and state.objects[ref].object_kind == kind:
        return ref
    pts = {oid: o.exact_value for oid, o in state.objects.items() if o.object_kind == "point3"}
    if kind == "line3" and isinstance(ref, (list, tuple)) and len(ref) == 2:
        if ref[0] in pts and ref[1] in pts and pts[ref[0]] != pts[ref[1]]:
            lk = canonical_line_key(E.Line3.through(pts[ref[0]], pts[ref[1]]))
            ids = state.key_to_ids.get(lk, ())
            return next((oid for oid in ids if oid in state.objects and state.objects[oid].object_kind == "line3"), None)
    if kind == "plane3" and isinstance(ref, (list, tuple)) and len(ref) >= 3:
        if all(x in pts for x in ref[:3]):
            try:
                plk = canonical_plane_key(E.Plane3.through(pts[ref[0]], pts[ref[1]], pts[ref[2]]))
                ids = state.key_to_ids.get(plk, ())
                return next((oid for oid in ids if oid in state.objects and state.objects[oid].object_kind == "plane3"), None)
            except E.GeometryError:
                return None
    if kind == "segment3" and isinstance(ref, (list, tuple)) and len(ref) == 2:
        if ref[0] in pts and ref[1] in pts and pts[ref[0]] != pts[ref[1]]:
            sk = canonical_segment_key(E.Segment3.between(pts[ref[0]], pts[ref[1]]))
            ids = state.key_to_ids.get(sk, ())
            return next((oid for oid in ids if oid in state.objects and state.objects[oid].object_kind == "segment3"), None)
    return None


def _apply_candidate_step(
    state: PlannerSearchState,
    frame: InitialGeometryFrame,
    *,
    operator_id: str,
    input_id_map: dict[str, str],
    output_label_overrides: dict[str, str] | None,
    params: dict[str, Any] | None,
    pending_resolved_id: str | None,
    origin: str,
    learner_hint: str,
    step_seq: int,
    extra_dep_nids: tuple[str, ...] = (),
) -> PlannerSearchState:
    """Execute one atomic operator, verify L0-L2, update state & proof graph DAG."""
    spec = OPERATOR_SPECS[operator_id]
    inputs_exact = {k: state.objects[oid].exact_value for k, oid in input_id_map.items()}
    res = execute_operator(operator_id, inputs_exact, params, frame.chart_metric)

    new_objects = dict(state.objects)
    new_key_to_ids: dict[str, list[str]] = {k: list(v) for k, v in state.key_to_ids.items()}
    new_last_node = dict(state.last_node_by_object)
    new_rels = set(state.relations)
    new_rel_nodes = dict(state.relation_node_ids)

    nid = f"n_step_{state.depth + 1}_{step_seq}_{operator_id.replace('op.', '')}"
    dep_nids = list(
        dict.fromkeys(
            [
                *(
                    state.last_node_by_object[oid]
                    for oid in input_id_map.values()
                    if oid in state.last_node_by_object
                ),
                *extra_dep_nids,
            ]
        )
    )

    out_ids: list[str] = []
    out_canonical_keys = res.get("canonical_keys", {})
    out_exact = res.get("outputs", {})

    new_aux_count = state.aux_count
    overrides = output_label_overrides or {}

    kind_map = {"point": "point3", "foot": "point3", "foot1": "point3", "foot2": "point3", "segment": "segment3", "line": "line3", "ray1": "line3", "ray2": "line3", "plane": "plane3", "perp_plane": "plane3", "section": "section"}

    for slot, val in out_exact.items():
        ckey = out_canonical_keys[slot]
        # Deduplicate geometrically identical objects: reuse existing ID instead of creating duplicate geometry!
        existing_ids = new_key_to_ids.get(ckey, [])
        okind = kind_map.get(slot, "point3")
        reusable = next((eid for eid in existing_ids if eid in new_objects and new_objects[eid].object_kind == okind), None)
        if reusable is not None:
            out_ids.append(reusable)
            continue

        base_lbl = overrides.get(slot)
        if not base_lbl:
            prefix = {"point3": "AuxP", "segment3": "aux_seg", "line3": "aux_ln", "plane3": "aux_pl", "section": "sec"}.get(okind, "aux")
            idx_num = 1
            while f"{prefix}_{idx_num}" in new_objects:
                idx_num += 1
            base_lbl = f"{prefix}_{idx_num}"
        oid = base_lbl
        obj_origin = "DERIVED_OBJECT" if origin == "DERIVED_OBJECT" else "AUXILIARY_CONSTRUCTION"
        if obj_origin == "AUXILIARY_CONSTRUCTION":
            new_aux_count += 1

        new_objects[oid] = ConstructionObject(
            object_id=oid,
            object_kind=okind,  # type: ignore[arg-type]
            origin=obj_origin,  # type: ignore[arg-type]
            canonical_geom_key=ckey,
            label=oid,
            exact_value=val,
            source_fact_refs=(),
            supporting_node_id=nid,
            metadata={"operator_id": operator_id},
        )
        new_key_to_ids.setdefault(ckey, []).append(oid)
        new_last_node[oid] = nid
        out_ids.append(oid)

    for rel_kind, rel_ops, sym in res.get("relations", []):
        r = (rel_kind, tuple(sorted(rel_ops)) if sym else tuple(rel_ops))
        new_rels.add(r)
        if r not in new_rel_nodes:
            new_rel_nodes[r] = nid

    node_type = "DERIVED_RELATION" if spec.category == "relation" else "CONSTRUCTION"
    primary_out_type = (
        new_objects[out_ids[0]].object_kind if out_ids and out_ids[0] in new_objects else "relation"
    )
    node = ConstructionNode(
        node_id=nid,
        node_type=node_type,  # type: ignore[arg-type]
        geometric_object_type=primary_out_type,
        object_refs=tuple(dict.fromkeys([*out_ids, *input_id_map.values()])),
        geometry_context={
            "inputs": dict(input_id_map),
            "params": _json_safe(params or {}),
            "canonical_outputs": _json_safe(out_canonical_keys),
        },
        source_fact_refs=(),
        producing_operation_id=operator_id,
        input_object_ids=tuple(input_id_map.values()),
        preconditions=spec.preconditions,
        derived_constraints=tuple(res.get("derived_constraints") or ()),
        output_objects=tuple(out_ids),
        dependency_ids=tuple(dep_nids),
        verification_status="VERIFIED",
        verification_evidence=dict(res.get("verification_evidence") or {}),
        exact_computation_ref=res.get("exact_computation_ref"),
        scene3d_render_hints={**spec.visualization_semantics, "learner_text": learner_hint},
    )

    new_pending = tuple(p for p in state.pending if p.req_id != pending_resolved_id) if pending_resolved_id else state.pending
    return PlannerSearchState(
        objects=new_objects,
        nodes=(*state.nodes, node),
        relations=frozenset(new_rels),
        key_to_ids={k: tuple(v) for k, v in new_key_to_ids.items()},
        pending=new_pending,
        cost=state.cost + spec.estimated_cost,
        depth=state.depth + 1,
        aux_count=new_aux_count,
        lineage=(*state.lineage, f"{operator_id}({','.join(f'{k}={v}' for k, v in sorted(input_id_map.items()))})"),
        last_node_by_object=new_last_node,
        relation_node_ids=new_rel_nodes,
    )


def _generate_candidates(
    state: PlannerSearchState,
    frame: InitialGeometryFrame,
    goal_spec: GoalSpec,
) -> list[dict[str, Any]]:
    """Structurally enumerate valid next atomic operators from `state` and `goal_spec` (NO oracle input)."""
    pts, lns, pls, segs, secs = _collect_typed_views(state)
    candidates: list[dict[str, Any]] = []

    # 1. Expand explicitly declared pending derived constructions whose inputs are now available
    for pend in state.pending:
        resolved_map: dict[str, str] = {}
        ok = True
        for slot, ref in pend.input_refs.items():
            if slot == "solid":
                if "solid_main" in state.objects:
                    resolved_map[slot] = "solid_main"
                else:
                    ok = False
                    break
            else:
                expected_kind = "point3"
                if "plane" in slot:
                    expected_kind = "plane3"
                elif "line" in slot:
                    expected_kind = "line3"
                oid = _resolve_object_by_ref(state, ref, expected_kind)
                if oid is None:
                    ok = False
                    break
                resolved_map[slot] = oid
        if ok:
            cat = OPERATOR_SPECS[pend.operator_id].category
            out_slot = {"section": "section", "plane": "plane", "line": "line", "segment": "segment"}.get(cat, "point")
            candidates.append(
                {
                    "operator_id": pend.operator_id,
                    "inputs": resolved_map,
                    "params": pend.params,
                    "overrides": {out_slot: pend.output_label} if pend.output_label else None,
                    "pending_id": pend.req_id,
                    "origin": "DERIVED_OBJECT",
                    "hint": pend.description or f"Dựng {pend.output_label} từ giả thiết",
                }
            )
            # Commit earliest unlocked declared premise construction deterministically to avoid O(k!) permutation blowup
            return candidates

    # 2. Ensure target structural entities in GoalSpec exist in `state.objects` before geometric search
    ops = goal_spec.operands
    gk = goal_spec.goal_kind

    def _ensure_point_list_plane(ref: Any, hint_lbl: str = "mp_goal") -> str | None:
        if isinstance(ref, str) and ref in pls:
            return ref
        if isinstance(ref, (list, tuple)) and len(ref) >= 3:
            oid = _resolve_object_by_ref(state, ref, "plane3")
            if oid:
                return oid
            if all(isinstance(x, str) and x in pts for x in ref[:3]):
                candidates.append(
                    {
                        "operator_id": "op.plane_through_three_points",
                        "inputs": {"a": ref[0], "b": ref[1], "c": ref[2]},
                        "params": {},
                        "overrides": {"plane": hint_lbl if hint_lbl not in state.objects else None},
                        "pending_id": None,
                        "origin": "DERIVED_OBJECT",
                        "hint": f"Xác định mặt phẳng ({''.join(ref[:3])})",
                    }
                )
        return None

    def _ensure_point_pair_line(ref: Any, hint_lbl: str = "dt_goal") -> str | None:
        if isinstance(ref, str) and ref in lns:
            return ref
        if isinstance(ref, (list, tuple)) and len(ref) == 2:
            oid = _resolve_object_by_ref(state, ref, "line3")
            if oid:
                return oid
            if all(isinstance(x, str) and x in pts for x in ref):
                candidates.append(
                    {
                        "operator_id": "op.line_through_points",
                        "inputs": {"a": ref[0], "b": ref[1]},
                        "params": {},
                        "overrides": {"line": hint_lbl if hint_lbl not in state.objects else None},
                        "pending_id": None,
                        "origin": "DERIVED_OBJECT",
                        "hint": f"Dựng đường thẳng {ref[0]}{ref[1]}",
                    }
                )
        return None

    if state.pending and len(candidates) > 0:
        # Still allow target lines/planes to be built concurrently, then return before aux branching if pending remains
        pass

    target_pl_id = _ensure_point_list_plane(ops.get("plane"), "mp_target") if "plane" in ops else None
    target_pl1_id = _ensure_point_list_plane(ops.get("plane1"), "mp_target_1") if "plane1" in ops else None
    target_pl2_id = _ensure_point_list_plane(ops.get("plane2"), "mp_target_2") if "plane2" in ops else None
    target_ln_id = _ensure_point_pair_line(ops.get("line"), "dt_target") if "line" in ops else None
    target_ln1_id = _ensure_point_pair_line(ops.get("line1"), "dt_target_1") if "line1" in ops else None
    target_ln2_id = _ensure_point_pair_line(ops.get("line2"), "dt_target_2") if "line2" in ops else None

    if gk == "solid_volume" and "base" in ops:
        target_pl_id = _ensure_point_list_plane(ops["base"], "mp_base")

    if gk == "segment_length":
        a, b = ops.get("a"), ops.get("b")
        if a in pts and b in pts:
            if _resolve_object_by_ref(state, [a, b], "segment3") is None:
                candidates.append(
                    {
                        "operator_id": "op.connect_segment",
                        "inputs": {"a": a, "b": b},
                        "params": {},
                        "overrides": {"segment": f"seg_{a}_{b}" if f"seg_{a}_{b}" not in state.objects else None},
                        "pending_id": None,
                        "origin": "AUXILIARY_CONSTRUCTION",
                        "hint": f"Nối đoạn thẳng {a}{b}",
                    }
                )

    if gk == "polygon_area":
        verts = ops.get("points") or []
        if len(verts) >= 3 and all(v in pts for v in verts):
            for i in range(len(verts)):
                u, v = verts[i], verts[(i + 1) % len(verts)]
                if _resolve_object_by_ref(state, [u, v], "segment3") is None:
                    candidates.append(
                        {
                            "operator_id": "op.connect_segment",
                            "inputs": {"a": u, "b": v},
                            "params": {},
                            "overrides": {"segment": f"seg_{u}_{v}" if f"seg_{u}_{v}" not in state.objects else None},
                            "pending_id": None,
                            "origin": "AUXILIARY_CONSTRUCTION",
                            "hint": f"Nối cạnh đa giác {u}{v}",
                        }
                    )

    if gk == "section_area" and target_pl_id and "solid_main" in state.objects and not state.pending:
        pl_k = state.objects[target_pl_id].canonical_geom_key
        if not any(r[0] == "section_of_solid_plane" and r[1][0] == pl_k for r in state.relations):
            candidates.append(
                {
                    "operator_id": "op.polyhedron_plane_section",
                    "inputs": {"solid": "solid_main", "plane": target_pl_id},
                    "params": {},
                    "overrides": {"section": "sec_goal"},
                    "pending_id": None,
                    "origin": "DERIVED_OBJECT",
                    "hint": f"Xác định thiết diện của khối bởi {target_pl_id}",
                }
            )

    # 3. Auxiliary & deductive synthesis for distance/angle goals once derived premises are resolved
    # 3a. Point-to-plane foot & classical synthetic two-step path
    pt_target_id: str | None = None
    pl_target_id: str | None = None
    if gk in ("distance_point_plane", "solid_volume"):
        pt_target_id = ops.get("point") if gk == "distance_point_plane" else ops.get("apex")
        pl_target_id = target_pl_id
    elif gk == "distance_line_plane" and target_ln_id and target_pl_id:
        lnk = state.objects[target_ln_id].canonical_geom_key
        plk = state.objects[target_pl_id].canonical_geom_key
        transfers = [r[1][2] for r in state.relations if r[0] == "distance_transfer_line_to_point" and r[1][0] == lnk and r[1][1] == plk]
        if not transfers:
            for pid, pval in sorted(pts.items()):
                if ("point_on_line", (canonical_point_key(pval), lnk)) in state.relations:
                    candidates.append(
                        {
                            "operator_id": "op.deduce_parallel_line_plane_transfer",
                            "inputs": {"line": target_ln_id, "plane": target_pl_id, "sample_point": pid},
                            "params": {},
                            "overrides": None,
                            "pending_id": None,
                            "origin": "DERIVED_OBJECT",
                            "hint": f"Chứng minh {target_ln_id} // {target_pl_id} và quy về khoảng cách từ {pid}",
                        }
                    )
        else:
            pt_target_id = (state.key_to_ids.get(transfers[0]) or [None])[0]
            pl_target_id = target_pl_id
    elif gk == "angle_line_plane" and target_ln_id and target_pl_id:
        lnk = state.objects[target_ln_id].canonical_geom_key
        plk = state.objects[target_pl_id].canonical_geom_key
        with M.using(frame.chart_metric):
            sin_sq = MS.sin_sq_line_plane(lns[target_ln_id], pls[target_pl_id])
        if sin_sq in (0, 1):
            # Boundary special case: prove parallelism or orthogonality via two lines / transfer
            if sin_sq == 0:
                p_on_ln = next((pid for pid, pval in sorted(pts.items()) if ("point_on_line", (canonical_point_key(pval), lnk)) in state.relations), None)
                if p_on_ln:
                    candidates.append(
                        {
                            "operator_id": "op.deduce_parallel_line_plane_transfer",
                            "inputs": {"line": target_ln_id, "plane": target_pl_id, "sample_point": p_on_ln},
                            "params": {},
                            "overrides": None,
                            "pending_id": None,
                            "origin": "DERIVED_OBJECT",
                            "hint": f"Chứng minh {target_ln_id} // {target_pl_id}",
                        }
                    )
            else:
                planar_lns = [lid for lid in sorted(lns) if ("line_in_plane", (state.objects[lid].canonical_geom_key, plk)) in state.relations]
                if len(planar_lns) >= 2:
                    candidates.append(
                        {
                            "operator_id": "op.deduce_line_perp_plane_two_lines",
                            "inputs": {"line": target_ln_id, "planar_line1": planar_lns[0], "planar_line2": planar_lns[1], "plane": target_pl_id},
                            "params": {},
                            "overrides": None,
                            "pending_id": None,
                            "origin": "DERIVED_OBJECT",
                            "hint": f"Chứng minh {target_ln_id} ⟂ {target_pl_id}",
                        }
                    )
        else:
            meets = [r[1][2] for r in state.relations if r[0] == "line_plane_intersection_witness" and r[1][0] == lnk and r[1][1] == plk]
            if not meets:
                candidates.append(
                    {
                        "operator_id": "op.intersect_line_plane",
                        "inputs": {"line": target_ln_id, "plane": target_pl_id},
                        "params": {},
                        "overrides": {"point": "I_meet" if "I_meet" not in pts else None},
                        "pending_id": None,
                        "origin": "AUXILIARY_CONSTRUCTION",
                        "hint": f"Tìm giao điểm {target_ln_id} ∩ {target_pl_id}",
                    }
                )
            else:
                meet_k = meets[0]
                meet_id = (state.key_to_ids.get(meet_k) or [None])[0]
                # Choose an off-plane point on line
                for pid, pval in sorted(pts.items()):
                    pk = canonical_point_key(pval)
                    if pk != meet_k and ("point_on_line", (pk, lnk)) in state.relations:
                        feet = [r[1][2] for r in state.relations if r[0] == "perp_point_plane_witness" and r[1][0] == pk and r[1][1] == plk]
                        if not feet:
                            pt_target_id = pid
                            pl_target_id = target_pl_id
                            break
                        else:
                            foot_id = (state.key_to_ids.get(feet[0]) or [None])[0]
                            if meet_id and foot_id and _resolve_object_by_ref(state, [meet_id, foot_id], "segment3") is None:
                                candidates.append(
                                    {
                                        "operator_id": "op.connect_segment",
                                        "inputs": {"a": meet_id, "b": foot_id},
                                        "params": {},
                                        "overrides": {"segment": f"seg_{meet_id}_{foot_id}" if f"seg_{meet_id}_{foot_id}" not in state.objects else None},
                                        "pending_id": None,
                                        "origin": "AUXILIARY_CONSTRUCTION",
                                        "hint": f"Dựng hình chiếu {meet_id}{foot_id} xác định góc giữa đường và mặt",
                                    }
                                )

    if gk == "distance_skew_lines" and target_ln1_id and target_ln2_id:
        # Path 1: direct common perpendicular
        candidates.append(
            {
                "operator_id": "op.common_perpendicular_skew_lines",
                "inputs": {"line1": target_ln1_id, "line2": target_ln2_id},
                "params": {},
                "overrides": {"foot1": "P1_perp", "foot2": "P2_perp", "segment": "seg_common_perp", "line": "ln_common_perp"},
                "pending_id": None,
                "origin": "AUXILIARY_CONSTRUCTION",
                "hint": f"Dựng đoạn vuông góc chung của hai đường chéo nhau {target_ln1_id} và {target_ln2_id}",
            }
        )
        # Path 2: auxiliary parallel plane R containing line2 and parallel to line1 (and vice versa), then project anchor of other line!
        k1 = state.objects[target_ln1_id].canonical_geom_key
        k2 = state.objects[target_ln2_id].canonical_geom_key
        for host_lid, host_k, par_lid, par_k, pname in (
            (target_ln2_id, k2, target_ln1_id, k1, "pl_par_skew_1"),
            (target_ln1_id, k1, target_ln2_id, k2, "pl_par_skew_2"),
        ):
            existing_r = [
                sid
                for sid, sobj in sorted(state.objects.items())
                if sobj.object_kind == "plane3"
                and ("parallel_line_plane", (par_k, sobj.canonical_geom_key)) in state.relations
                and ("line_in_plane", (host_k, sobj.canonical_geom_key)) in state.relations
            ]
            if not existing_r:
                candidates.append(
                    {
                        "operator_id": "op.plane_through_line_parallel_line",
                        "inputs": {"host_line": host_lid, "parallel_to_line": par_lid},
                        "params": {},
                        "overrides": {"plane": pname if pname not in state.objects else None},
                        "pending_id": None,
                        "origin": "AUXILIARY_CONSTRUCTION",
                        "hint": f"Dựng mặt phẳng phụ chứa {host_lid} và song song {par_lid}",
                    }
                )
            else:
                r_id = existing_r[0]
                for pid, pval in sorted(pts.items()):
                    if ("point_on_line", (canonical_point_key(pval), par_k)) in state.relations:
                        candidates.append(
                            {
                                "operator_id": "op.project_point_to_plane",
                                "inputs": {"point": pid, "plane": r_id},
                                "params": {},
                                "overrides": {"foot": f"H_{pid}", "segment": f"seg_{pid}_H", "line": f"ln_{pid}_H"},
                                "pending_id": None,
                                "origin": "AUXILIARY_CONSTRUCTION",
                                "hint": f"Hạ đường vuông góc từ {pid} xuống mặt phẳng phụ {r_id}",
                            }
                        )
                        break

    # Point-to-plane projection + Classical synthetic 2-step theorem expansion
    if pt_target_id in pts and pl_target_id in pls:
        pk = canonical_point_key(pts[pt_target_id])
        plk = canonical_plane_key(pls[pl_target_id])
        already_witnessed = any(r[0] == "perp_point_plane_witness" and r[1][0] == pk and r[1][1] == plk for r in state.relations)
        if not already_witnessed:
            # Candidate A: Direct project point onto plane
            candidates.append(
                {
                    "operator_id": "op.project_point_to_plane",
                    "inputs": {"point": pt_target_id, "plane": pl_target_id},
                    "params": {},
                    "overrides": {"foot": f"H_{pt_target_id}", "segment": f"seg_{pt_target_id}_H", "line": f"ln_{pt_target_id}_H"},
                    "pending_id": None,
                    "origin": "AUXILIARY_CONSTRUCTION",
                    "hint": f"Hạ {pt_target_id}H vuông góc với mặt phẳng {pl_target_id}",
                }
            )
            # Candidate B (Multi-step Euclidean theorem synthesis):
            # Look for a base line `edge` inside `pl_target_id` AND a given vertical/altitude line at `pt_target_id` (e.g. `SA ⟂ base` so `SA ⟂ edge`)
            # Step B1: Find a line `vert_ln` passing through `pt_target_id` that is perpendicular to some `edge` lying in `pl_target_id`
            edges_in_pl = [
                lid
                for lid, lval in sorted(lns.items())
                if ("line_in_plane", (state.objects[lid].canonical_geom_key, plk)) in state.relations
                and MS.distance_sq_point_line(pts[pt_target_id], lval) > 0
            ]
            for edge_id in edges_in_pl[:6]:
                edge_k = state.objects[edge_id].canonical_geom_key
                edge_ln = lns[edge_id]
                # Check if another point `apex_id` in target plane forms a line `(apex_id, pt_target_id)` orthogonal to `edge_ln`
                third_pts = [
                    pid
                    for pid, pval in sorted(pts.items())
                    if pid != pt_target_id
                    and pls[pl_target_id].signed_eval(pval) == 0
                    and ("point_on_line", (canonical_point_key(pval), edge_k)) not in state.relations
                ]
                for third_id in third_pts[:2]:
                    with M.using(frame.chart_metric):
                        alt_vec = pts[third_id] - pts[pt_target_id]
                        if alt_vec.is_zero() or M.dot(alt_vec, edge_ln.direction) != 0:
                            continue
                    # B1: Check if foot M = proj(pt_target_id, edge_id) already exists
                    feet_on_edge = [
                        r[1][2]
                        for r in state.relations
                        if r[0] == "perp_point_line_witness" and r[1][0] == pk and r[1][1] == edge_k
                    ]
                    if not feet_on_edge:
                        candidates.append(
                            {
                                "operator_id": "op.project_point_to_line",
                                "inputs": {"point": pt_target_id, "line": edge_id},
                                "params": {},
                                "overrides": {"foot": f"M_{pt_target_id}", "segment": f"seg_{pt_target_id}_M", "line": f"ln_{pt_target_id}_M"},
                                "pending_id": None,
                                "origin": "AUXILIARY_CONSTRUCTION",
                                "hint": f"Kẻ hình chiếu vuông góc từ {pt_target_id} xuống {edge_id}",
                            }
                        )
                    else:
                        m_id = (state.key_to_ids.get(feet_on_edge[0]) or [None])[0]
                        if not m_id:
                            continue
                        # Ensure auxiliary plane `(third_id, pt_target_id, m_id)` and slant line `(third_id, m_id)` exist
                        aux_pl_id = _resolve_object_by_ref(state, [third_id, pt_target_id, m_id], "plane3")
                        slant_id = _resolve_object_by_ref(state, [third_id, m_id], "line3")
                        vert_id = _resolve_object_by_ref(state, [third_id, pt_target_id], "line3")
                        am_id = _resolve_object_by_ref(state, [pt_target_id, m_id], "line3")
                        if aux_pl_id is None:
                            candidates.append(
                                {
                                    "operator_id": "op.plane_through_three_points",
                                    "inputs": {"a": third_id, "b": pt_target_id, "c": m_id},
                                    "params": {},
                                    "overrides": {"plane": f"pl_{third_id}{pt_target_id}{m_id}"},
                                    "pending_id": None,
                                    "origin": "AUXILIARY_CONSTRUCTION",
                                    "hint": f"Xét mặt phẳng phụ ({third_id}{pt_target_id}{m_id})",
                                }
                            )
                        if slant_id is None:
                            candidates.append(
                                {
                                    "operator_id": "op.line_through_points",
                                    "inputs": {"a": third_id, "b": m_id},
                                    "params": {},
                                    "overrides": {"line": f"ln_{third_id}_{m_id}"},
                                    "pending_id": None,
                                    "origin": "AUXILIARY_CONSTRUCTION",
                                    "hint": f"Nối {third_id}{m_id} trong mặt phẳng ({third_id}{pt_target_id}{m_id})",
                                }
                            )
                        if vert_id is None:
                            candidates.append(
                                {
                                    "operator_id": "op.line_through_points",
                                    "inputs": {"a": third_id, "b": pt_target_id},
                                    "params": {},
                                    "overrides": {"line": f"ln_{third_id}_{pt_target_id}"},
                                    "pending_id": None,
                                    "origin": "DERIVED_OBJECT",
                                    "hint": f"Xét đường thẳng {third_id}{pt_target_id}",
                                }
                            )
                        if aux_pl_id and slant_id and vert_id and am_id:
                            aux_plk = state.objects[aux_pl_id].canonical_geom_key
                            if ("perp_line_plane", (edge_k, aux_plk)) not in state.relations:
                                candidates.append(
                                    {
                                        "operator_id": "op.deduce_line_perp_plane_two_lines",
                                        "inputs": {"line": edge_id, "planar_line1": am_id, "planar_line2": vert_id, "plane": aux_pl_id},
                                        "params": {},
                                        "overrides": None,
                                        "pending_id": None,
                                        "origin": "DERIVED_OBJECT",
                                        "hint": f"Chứng minh {edge_id} ⟂ ({third_id}{pt_target_id}{m_id}) vì vuông góc với hai đường cắt nhau",
                                    }
                                )
                            else:
                                # Step B4: Project pt_target_id onto slant line `(third_id, m_id)` -> foot K_synth
                                slant_k = state.objects[slant_id].canonical_geom_key
                                feet_on_slant = [
                                    r[1][2]
                                    for r in state.relations
                                    if r[0] == "perp_point_line_witness" and r[1][0] == pk and r[1][1] == slant_k
                                ]
                                if not feet_on_slant:
                                    candidates.append(
                                        {
                                            "operator_id": "op.project_point_to_line",
                                            "inputs": {"point": pt_target_id, "line": slant_id},
                                            "params": {},
                                            "overrides": {"foot": f"K_alt_{pt_target_id}", "segment": f"seg_{pt_target_id}_K", "line": f"ln_{pt_target_id}_K"},
                                            "pending_id": None,
                                            "origin": "AUXILIARY_CONSTRUCTION",
                                            "hint": f"Kẻ đường vuông góc từ {pt_target_id} xuống {slant_id}",
                                        }
                                    )
                                else:
                                    k_id = (state.key_to_ids.get(feet_on_slant[0]) or [None])[0]
                                    ak_ln_id = _resolve_object_by_ref(state, [pt_target_id, k_id], "line3") if k_id else None
                                    if k_id and ak_ln_id:
                                        # Step B5: Prove `line(pt, K) ⟂ target_plane` using `edge_id` and `slant_id` via two-line theorem!
                                        perp_rel_key = ("perp_line_plane", (edge_k, aux_plk))
                                        req_rel_nid = state.relation_node_ids.get(perp_rel_key)
                                        candidates.append(
                                            {
                                                "operator_id": "op.deduce_line_perp_plane_two_lines",
                                                "inputs": {
                                                    "line": ak_ln_id,
                                                    "planar_line1": edge_id,
                                                    "planar_line2": slant_id,
                                                    "plane": pl_target_id,
                                                    "anchor_on_plane": k_id,
                                                },
                                                "params": {},
                                                "overrides": None,
                                                "pending_id": None,
                                                "origin": "DERIVED_OBJECT",
                                                "hint": f"Chứng minh {pt_target_id}{k_id} ⟂ {pl_target_id} do vuông góc với {slant_id} và {edge_id}",
                                                "extra_dep_nids": (req_rel_nid,) if req_rel_nid else (),
                                            }
                                        )

    # 3b. Point-to-line projection
    if gk == "distance_point_line" and ops.get("point") in pts and target_ln_id in lns:
        candidates.append(
            {
                "operator_id": "op.project_point_to_line",
                "inputs": {"point": ops["point"], "line": target_ln_id},
                "params": {},
                "overrides": {"foot": f"H_{ops['point']}", "segment": f"seg_{ops['point']}_H", "line": f"ln_{ops['point']}_H"},
                "pending_id": None,
                "origin": "AUXILIARY_CONSTRUCTION",
                "hint": f"Hạ chân đường vuông góc từ {ops['point']} xuống {target_ln_id}",
            }
        )

    # 3c. Skew/intersecting angle between lines
    if gk == "angle_lines" and target_ln1_id and target_ln2_id:
        la, lb = lns[target_ln1_id], lns[target_ln2_id]
        if not la.direction.cross(lb.direction).is_zero():
            if (lb.point - la.point).dot(la.direction.cross(lb.direction)) == 0:
                candidates.append(
                    {
                        "operator_id": "op.intersect_coplanar_lines",
                        "inputs": {"line1": target_ln1_id, "line2": target_ln2_id},
                        "params": {},
                        "overrides": {"point": "I_lines" if "I_lines" not in pts else None},
                        "pending_id": None,
                        "origin": "AUXILIARY_CONSTRUCTION",
                        "hint": f"Xác định giao điểm của {target_ln1_id} và {target_ln2_id}",
                    }
                )
            else:
                k1, k2 = state.objects[target_ln1_id].canonical_geom_key, state.objects[target_ln2_id].canonical_geom_key
                for pid, pval in sorted(pts.items()):
                    if ("point_on_line", (canonical_point_key(pval), k1)) in state.relations:
                        candidates.append(
                            {
                                "operator_id": "op.line_parallel_through_point",
                                "inputs": {"point": pid, "line": target_ln2_id},
                                "params": {},
                                "overrides": {"line": f"par_{target_ln2_id}_{pid}"},
                                "pending_id": None,
                                "origin": "AUXILIARY_CONSTRUCTION",
                                "hint": f"Qua {pid} ∈ {target_ln1_id} dựng đường thẳng song song với {target_ln2_id}",
                            }
                        )
                        break
                for pid, pval in sorted(pts.items()):
                    if ("point_on_line", (canonical_point_key(pval), k2)) in state.relations:
                        candidates.append(
                            {
                                "operator_id": "op.line_parallel_through_point",
                                "inputs": {"point": pid, "line": target_ln1_id},
                                "params": {},
                                "overrides": {"line": f"par_{target_ln1_id}_{pid}"},
                                "pending_id": None,
                                "origin": "AUXILIARY_CONSTRUCTION",
                                "hint": f"Qua {pid} ∈ {target_ln2_id} dựng đường thẳng song song với {target_ln1_id}",
                            }
                        )
                        break

    # 3d. Dihedral / plane-plane angle (`op.intersect_planes` -> `op.construct_dihedral_linear_angle` + altitude-plane alternative)
    if gk == "angle_plane_plane" and target_pl1_id and target_pl2_id:
        pk1 = state.objects[target_pl1_id].canonical_geom_key
        pk2 = state.objects[target_pl2_id].canonical_geom_key
        pair_k = tuple(sorted((pk1, pk2)))
        edges = [r[1][2] for r in state.relations if r[0] == "planes_intersection_line" and tuple(sorted((r[1][0], r[1][1]))) == pair_k]
        if not edges:
            candidates.append(
                {
                    "operator_id": "op.intersect_planes",
                    "inputs": {"plane1": target_pl1_id, "plane2": target_pl2_id},
                    "params": {},
                    "overrides": {"line": "delta_inter" if "delta_inter" not in lns else None},
                    "pending_id": None,
                    "origin": "DERIVED_OBJECT",
                    "hint": f"Tìm giao tuyến Δ của hai mặt phẳng {target_pl1_id} và {target_pl2_id}",
                }
            )
        else:
            edge_k = edges[0]
            edge_id = (state.key_to_ids.get(edge_k) or [None])[0]
            if edge_id:
                candidates.append(
                    {
                        "operator_id": "op.construct_dihedral_linear_angle",
                        "inputs": {"plane1": target_pl1_id, "plane2": target_pl2_id, "edge": edge_id},
                        "params": {},
                        "overrides": {"ray1": "ray_p1", "ray2": "ray_p2", "perp_plane": "pl_dihedral"},
                        "pending_id": None,
                        "origin": "AUXILIARY_CONSTRUCTION",
                        "hint": f"Dựng góc phẳng nhị diện của hai mặt phẳng qua hai tia vuông góc giao tuyến {edge_id}",
                    }
                )
                # Alternative vertex-specific synthetic path: project a point in plane1 off edge onto edge -> then establish perp_line_plane(edge, (M, off_pt, ...))
                with M.using(frame.chart_metric):
                    for pid, pval in sorted(pts.items()):
                        if pls[target_pl1_id].signed_eval(pval) == 0 and MS.distance_sq_point_line(pval, lns[edge_id]) > 0:
                            feet = [r[1][2] for r in state.relations if r[0] == "perp_point_line_witness" and r[1][0] == canonical_point_key(pval) and r[1][1] == edge_k]
                            if not feet:
                                candidates.append(
                                    {
                                        "operator_id": "op.project_point_to_line",
                                        "inputs": {"point": pid, "line": edge_id},
                                        "params": {},
                                        "overrides": {"foot": f"M_{pid}_edge", "segment": f"seg_{pid}_M_edge", "line": f"ln_{pid}_M_edge"},
                                        "pending_id": None,
                                        "origin": "AUXILIARY_CONSTRUCTION",
                                        "hint": f"Kẻ {pid}M ⟂ {edge_id} để tìm mặt phẳng vuông góc giao tuyến",
                                    }
                                )
                            else:
                                m_id = (state.key_to_ids.get(feet[0]) or [None])[0]
                                if m_id:
                                    # Also look for any point off plane 1 whose line to a base point is perp to edge -> deduce edge ⟂ auxiliary plane!
                                    for other_id, oval in sorted(pts.items()):
                                        if other_id != pid and pls[target_pl2_id].signed_eval(oval) == 0 and M.dot(oval - pval, lns[edge_id].direction) == 0:
                                            if len({other_id, pid, m_id}) == 3:
                                                aux_pl_id = _resolve_object_by_ref(state, [other_id, pid, m_id], "plane3")
                                                l_a = _resolve_object_by_ref(state, [pid, m_id], "line3")
                                                l_b = _resolve_object_by_ref(state, [other_id, pid], "line3")
                                                if aux_pl_id is None:
                                                    candidates.append(
                                                        {
                                                            "operator_id": "op.plane_through_three_points",
                                                            "inputs": {"a": other_id, "b": pid, "c": m_id},
                                                            "params": {},
                                                            "overrides": {"plane": f"pl_orth_{other_id}{pid}{m_id}"},
                                                            "pending_id": None,
                                                            "origin": "AUXILIARY_CONSTRUCTION",
                                                            "hint": f"Tạo mặt phẳng vuông góc với giao tuyến ({other_id}{pid}{m_id})",
                                                        }
                                                    )
                                                if l_b is None:
                                                    candidates.append(
                                                        {
                                                            "operator_id": "op.line_through_points",
                                                            "inputs": {"a": other_id, "b": pid},
                                                            "params": {},
                                                            "overrides": {"line": f"ln_{other_id}_{pid}"},
                                                            "pending_id": None,
                                                            "origin": "DERIVED_OBJECT",
                                                            "hint": f"Dựng đường vuông góc phụ {other_id}{pid}",
                                                        }
                                                    )
                                                if aux_pl_id and l_a and l_b:
                                                    candidates.append(
                                                        {
                                                            "operator_id": "op.deduce_line_perp_plane_two_lines",
                                                            "inputs": {"line": edge_id, "planar_line1": l_a, "planar_line2": l_b, "plane": aux_pl_id},
                                                            "params": {},
                                                            "overrides": None,
                                                            "pending_id": None,
                                                            "origin": "DERIVED_OBJECT",
                                                            "hint": f"Chứng minh {edge_id} ⟂ mặt phẳng ({other_id}{pid}{m_id})",
                                                        }
                                                    )
                            break

    return candidates


def _compute_heuristic(state: PlannerSearchState, goal_spec: GoalSpec) -> float:
    """Structural admissable-style goal distance estimate (ZERO numerical oracles)."""
    h = float(len(state.pending))
    gk = goal_spec.goal_kind
    if gk in ("distance_point_plane", "distance_line_plane", "solid_volume"):
        if not any(r[0] == "perp_point_plane_witness" for r in state.relations):
            h += 1.5 if not any(r[0] == "perp_point_line_witness" for r in state.relations) else 0.9
    elif gk == "distance_skew_lines":
        if not any(r[0] == "common_perpendicular_witness" for r in state.relations):
            h += 0.8 if any(r[0] == "parallel_line_plane" for r in state.relations) else 1.5
    elif gk == "angle_plane_plane":
        if not any(r[0] == "dihedral_linear_angle_witness" for r in state.relations):
            h += 0.7 if any(r[0] == "planes_intersection_line" for r in state.relations) else 1.5
    elif gk == "section_area":
        if not any(r[0] == "section_of_solid_plane" for r in state.relations):
            h += 1.0
    return h


class DynamicConstructionPlanner:
    """Bounded dependency-aware best-first construction planner (`dynamic-construction-planner/1`)."""

    def plan(
        self,
        *,
        frame: InitialGeometryFrame,
        goal_spec: GoalSpec,
        budget: SearchBudget | None = None,
    ) -> DynamicPlannerResult:
        """Search and verify one or more construction plans. Note: takes NO oracle argument."""
        cfg = budget or SearchBudget()
        t_start = time.perf_counter()
        tracemalloc.start()
        expanded_states = 0
        generated_states = 0
        pruned_states = 0
        candidate_ops_evaluated = 0
        rejection_reasons: list[str] = []
        visited_sigs: dict[str, int] = {}

        def _stop_mem() -> float:
            try:
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return round(peak / 1024.0, 2)
            except Exception:
                return 0.0

        def _base_telemetry(timeout_hit: bool = False) -> dict[str, Any]:
            elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 3)
            peak_kib = _stop_mem()
            return {
                "algorithm": "bounded_best_first_dependency_aware_search",
                "budget": cfg.to_dict(),
                "search_ms": elapsed_ms,
                "expanded_states": expanded_states,
                "generated_candidates": generated_states,
                "pruned_states": pruned_states,
                "candidate_operators_evaluated": candidate_ops_evaluated,
                "peak_memory_kib": peak_kib,
                "timeout_hit": timeout_hit,
                "rejection_reasons": rejection_reasons[:20],
            }

        if frame.error_code is not None:
            status = (
                "CONTRADICTORY_CONSTRAINTS"
                if frame.error_code in ("CONTRADICTORY_CONSTRAINTS", "NON_POSITIVE_DIMENSION", "DEGENERATE_COINCIDENT_POINTS", "DEGENERATE_COLLINEAR_POINTS")
                else "UNSUPPORTED_OPERATOR"
                if "UNSUPPORTED" in frame.error_code
                else "MISSING_PRECONDITION"
            )
            return DynamicPlannerResult(
                planner_version=DYNAMIC_PLANNER_VERSION,
                status=status,
                case_id=frame.case_id,
                plans=(),
                failure_code=frame.error_code,
                failure_detail=frame.error_detail,
                telemetry=_base_telemetry(),
            )

        if goal_spec.goal_kind == "unsupported_goal":
            return DynamicPlannerResult(
                planner_version=DYNAMIC_PLANNER_VERSION,
                status="UNSUPPORTED_OPERATOR",
                case_id=frame.case_id,
                plans=(),
                failure_code="UNSUPPORTED_OPERATOR",
                failure_detail=str(goal_spec.operands.get("reason") or "Goal requires primitive outside operator inventory."),
                telemetry=_base_telemetry(),
            )

        init_state = make_initial_search_state(frame)
        visited_sigs[init_state.canonical_state_signature()] = 0
        seq_counter = itertools.count(1)
        frontier: list[tuple[float, int, int, str, PlannerSearchState]] = []
        heapq.heappush(frontier, (_compute_heuristic(init_state, goal_spec), 0, next(seq_counter), init_state.canonical_state_signature(), init_state))

        collected_solutions: list[tuple[tuple[Any, ...], ConstructionProofGraph, PresentationStepGraph, VerificationReport, dict[str, Any], tuple[str, ...]]] = []
        seen_solution_sigs: set[str] = set()
        last_reject_code: str | None = None
        last_reject_detail: str | None = None

        while frontier:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            if elapsed_ms >= cfg.max_wall_clock_ms:
                if collected_solutions:
                    break
                return DynamicPlannerResult(
                    planner_version=DYNAMIC_PLANNER_VERSION,
                    status="SEARCH_TIMEOUT",
                    case_id=frame.case_id,
                    plans=(),
                    failure_code="SEARCH_TIMEOUT",
                    failure_detail=f"Exceeded wall-clock limit {cfg.max_wall_clock_ms} ms after {expanded_states} expanded states.",
                    telemetry=_base_telemetry(timeout_hit=True),
                )
            _, cur_peak = tracemalloc.get_traced_memory()
            if cur_peak / (1024.0 * 1024.0) > cfg.max_memory_mb:
                if collected_solutions:
                    break
                return DynamicPlannerResult(
                    planner_version=DYNAMIC_PLANNER_VERSION,
                    status="SEARCH_RESOURCE_LIMIT",
                    case_id=frame.case_id,
                    plans=(),
                    failure_code="SEARCH_RESOURCE_LIMIT",
                    failure_detail=f"Exceeded memory limit {cfg.max_memory_mb} MiB.",
                    telemetry=_base_telemetry(),
                )
            if expanded_states >= cfg.max_expanded_states or candidate_ops_evaluated >= cfg.max_candidate_operators:
                if collected_solutions:
                    break
                return DynamicPlannerResult(
                    planner_version=DYNAMIC_PLANNER_VERSION,
                    status="SEARCH_RESOURCE_LIMIT",
                    case_id=frame.case_id,
                    plans=(),
                    failure_code="SEARCH_RESOURCE_LIMIT",
                    failure_detail=f"Exceeded expansion/operator budget (expanded={expanded_states}, ops={candidate_ops_evaluated}).",
                    telemetry=_base_telemetry(),
                )

            _, _, _, sig, cur = heapq.heappop(frontier)
            expanded_states += 1

            # Check whether all pending constructions resolved AND goal witness exists in current state
            if not cur.pending:
                pts, lns, pls, segs, secs = _collect_typed_views(cur)
                g_eval = evaluate_goal_if_witnessed(
                    goal_spec,
                    points_by_id=pts,
                    lines_by_id=lns,
                    planes_by_id=pls,
                    segments_by_id=segs,
                    sections_by_id=secs,
                    relations=set(cur.relations),
                    key_to_ids={k: list(v) for k, v in cur.key_to_ids.items()},
                    chart_metric=frame.chart_metric,
                )
                if g_eval is not None:
                    p_idx = len(collected_solutions) + 1
                    pg = materialize_proof_graph_from_state(frame, cur, goal_spec=goal_spec, goal_eval=g_eval, plan_index=p_idx)
                    report = verify_full_proof_and_scene(pg, frame.chart_metric)
                    if report.passed:
                        pres = project_to_presentation_graph(pg)
                        # Deduplicate substantively identical plans (not permutations of independent steps!)
                        ops_used = tuple(
                            sorted(
                                n.producing_operation_id or ""
                                for n in pg.nodes
                                if n.node_type in ("CONSTRUCTION", "DERIVED_RELATION")
                            )
                        )
                        geom_footprint = tuple(
                            sorted(
                                o.canonical_geom_key
                                for o in pg.objects.values()
                                if o.origin in ("AUXILIARY_CONSTRUCTION", "DERIVED_OBJECT") and o.object_kind != "quantity"
                            )
                        )
                        substantive_sig = f"{ops_used}::{geom_footprint}"
                        if substantive_sig not in seen_solution_sigs:
                            seen_solution_sigs.add(substantive_sig)
                            score_tuple = (
                                round(cur.cost, 4),
                                len([o for o in pg.objects.values() if o.origin == "AUXILIARY_CONSTRUCTION"]),
                                cur.depth,
                                len(pres.steps),
                                substantive_sig,
                            )
                            collected_solutions.append((score_tuple, pg, pres, report, g_eval, cur.lineage))
                            if len(collected_solutions) >= cfg.max_plans:
                                break
                        # Note: if `cur` solved the goal via fast direct route, we still allow sibling/pending branches to complete!
                        continue
                    else:
                        last_reject_code = report.failure_code
                        last_reject_detail = report.failure_detail

            effective_max_depth = cfg.max_depth + len(frame.pending_constructions)
            if cur.depth >= effective_max_depth or len(cur.nodes) >= cfg.max_graph_nodes:
                pruned_states += 1
                continue

            cands = _generate_candidates(cur, frame, goal_spec)
            for cand_idx, cand in enumerate(cands):
                if candidate_ops_evaluated >= cfg.max_candidate_operators:
                    break
                candidate_ops_evaluated += 1
                try:
                    nxt = _apply_candidate_step(
                        cur,
                        frame,
                        operator_id=cand["operator_id"],
                        input_id_map=cand["inputs"],
                        output_label_overrides=cand.get("overrides"),
                        params=cand.get("params"),
                        pending_resolved_id=cand.get("pending_id"),
                        origin=cand.get("origin", "AUXILIARY_CONSTRUCTION"),
                        learner_hint=cand.get("hint", cand["operator_id"]),
                        step_seq=cand_idx,
                        extra_dep_nids=tuple(cand.get("extra_dep_nids") or ()),
                    )
                except VerificationError as exc:
                    pruned_states += 1
                    last_reject_code = exc.code
                    last_reject_detail = exc.detail
                    if exc.code not in rejection_reasons:
                        rejection_reasons.append(f"{exc.code}: {exc.detail[:120]}")
                    continue

                generated_states += 1
                nxt_sig = nxt.canonical_state_signature()
                if nxt_sig in visited_sigs and visited_sigs[nxt_sig] <= nxt.depth:
                    pruned_states += 1
                    continue
                visited_sigs[nxt_sig] = nxt.depth
                prio = nxt.cost + _compute_heuristic(nxt, goal_spec)
                heapq.heappush(frontier, (prio, nxt.depth, next(seq_counter), nxt_sig, nxt))

        if collected_solutions:
            collected_solutions.sort(key=lambda item: item[0])
            ranked = tuple(
                RankedPlan(
                    rank=idx + 1,
                    score_tuple=item[0],
                    proof_graph=item[1],
                    presentation_graph=item[2],
                    verification_report=item[3],
                    answer=str(item[4]["answer"]),
                    answer_exact=dict(item[4]["answer_exact"]),
                    operator_lineage=item[5],
                )
                for idx, item in enumerate(collected_solutions)
            )
            return DynamicPlannerResult(
                planner_version=DYNAMIC_PLANNER_VERSION,
                status="GOAL_VERIFIED",
                case_id=frame.case_id,
                plans=ranked,
                failure_code=None,
                failure_detail=None,
                telemetry=_base_telemetry(),
            )

        # Map exact failure status
        if last_reject_code and last_reject_code.startswith("DEGENERATE_"):
            term_status = "CONTRADICTORY_CONSTRAINTS"
        elif last_reject_code == "IMPOSSIBLE_PERPENDICULARITY":
            term_status = "VERIFICATION_FAILED"
        elif last_reject_code == "UNSUPPORTED_OPERATOR":
            term_status = "UNSUPPORTED_OPERATOR"
        else:
            term_status = "NO_PLAN_FOUND_WITHIN_BUDGET"

        return DynamicPlannerResult(
            planner_version=DYNAMIC_PLANNER_VERSION,
            status=term_status,
            case_id=frame.case_id,
            plans=(),
            failure_code=last_reject_code or "NO_PLAN_FOUND_WITHIN_BUDGET",
            failure_detail=last_reject_detail or "Exhausted search frontier without finding a verified witness plan.",
            telemetry=_base_telemetry(),
        )
