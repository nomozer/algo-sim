# -*- coding: utf-8 -*-
"""`verified-construction-graph/1` and `presentation-step-graph/1` schemas and validators."""
from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Literal

from . import PRESENTATION_STEP_GRAPH_SCHEMA, VERIFIED_CONSTRUCTION_GRAPH_SCHEMA
from .construction_objects import ConstructionObject, _json_safe

NodeType = Literal["GIVEN", "CONSTRUCTION", "DERIVED_RELATION", "VERIFICATION", "GOAL"]
VerificationStatus = Literal["VERIFIED", "UNVERIFIED", "REFUSED", "UNSUPPORTED", "CONTRADICTORY"]
PresentationActionType = Literal[
    "INIT_GIVEN",
    "CONSTRUCT_AUXILIARY",
    "CONSTRUCT_DERIVED",
    "ESTABLISH_RELATION",
    "MEASURE_GOAL",
]

VALID_NODE_TYPES = frozenset({"GIVEN", "CONSTRUCTION", "DERIVED_RELATION", "VERIFICATION", "GOAL"})
VALID_VERIFICATION_STATUSES = frozenset({"VERIFIED", "UNVERIFIED", "REFUSED", "UNSUPPORTED", "CONTRADICTORY"})

ERR_CYCLIC = "CYCLIC_DEPENDENCY"
ERR_MISSING_PRECOND = "MISSING_PRECONDITION"
ERR_UNVERIFIED = "UNVERIFIED_CONSTRUCTION"
ERR_CONTRADICTORY = "CONTRADICTORY_CONSTRAINTS"
ERR_DUPLICATE_GEOM = "DUPLICATE_GEOMETRIC_CONSTRUCTION"


class GraphValidationError(ValueError):
    """Fail-closed validation error for `ConstructionProofGraph`."""

    def __init__(self, code: str, detail: str, node_ids: tuple[str, ...] = ()) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.node_ids = node_ids


@dataclass(frozen=True)
class ConstructionNode:
    """Typed node inside `ConstructionProofGraph` (`verified-construction-graph/1`)."""

    node_id: str
    node_type: NodeType
    geometric_object_type: str
    object_refs: tuple[str, ...]
    geometry_context: dict[str, Any]
    source_fact_refs: tuple[str, ...]
    producing_operation_id: str | None
    input_object_ids: tuple[str, ...]
    preconditions: tuple[str, ...]
    derived_constraints: tuple[str, ...]
    output_objects: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    verification_status: VerificationStatus
    verification_evidence: dict[str, Any]
    exact_computation_ref: str | None = None
    scene3d_render_hints: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.node_type not in VALID_NODE_TYPES:
            raise ValueError(f"Unsupported node_type={self.node_type!r}")
        if self.verification_status not in VALID_VERIFICATION_STATUSES:
            raise ValueError(f"Unsupported verification_status={self.verification_status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "geometric_object_type": self.geometric_object_type,
            "object_refs": list(self.object_refs),
            "geometry_context": _json_safe(self.geometry_context),
            "source_fact_refs": list(self.source_fact_refs),
            "producing_operation_id": self.producing_operation_id,
            "input_object_ids": list(self.input_object_ids),
            "preconditions": list(self.preconditions),
            "derived_constraints": list(self.derived_constraints),
            "output_objects": list(self.output_objects),
            "dependency_ids": list(self.dependency_ids),
            "verification_status": self.verification_status,
            "verification_evidence": _json_safe(self.verification_evidence),
            "exact_computation_ref": self.exact_computation_ref,
            "scene3d_render_hints": _json_safe(self.scene3d_render_hints),
        }


@dataclass(frozen=True)
class GraphValidationReport:
    valid: bool
    failure_codes: tuple[str, ...]
    issues: tuple[dict[str, Any], ...]
    topological_node_order: tuple[str, ...]
    unused_node_ids: tuple[str, ...]
    duplicate_construction_groups: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "failure_codes": list(self.failure_codes),
            "issues": [dict(x) for x in self.issues],
            "topological_node_order": list(self.topological_node_order),
            "unused_node_ids": list(self.unused_node_ids),
            "duplicate_construction_groups": [list(g) for g in self.duplicate_construction_groups],
        }


@dataclass(frozen=True)
class ConstructionProofGraph:
    """Full mathematically verified construction and proof DAG (`verified-construction-graph/1`)."""

    graph_id: str
    nodes: tuple[ConstructionNode, ...]
    objects: dict[str, ConstructionObject]
    goal_node_ids: tuple[str, ...]
    chart_metric: tuple[tuple[str, ...], ...]
    length_unit: str
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = VERIFIED_CONSTRUCTION_GRAPH_SCHEMA

    def node_map(self) -> dict[str, ConstructionNode]:
        return {n.node_id: n for n in self.nodes}

    def to_dict(self) -> dict[str, Any]:
        order = topological_order_safe(self)
        by_id = self.node_map()
        ordered_nodes = [by_id[nid].to_dict() for nid in order] if order else [n.to_dict() for n in self.nodes]
        return {
            "schema_version": self.schema_version,
            "graph_id": self.graph_id,
            "length_unit": self.length_unit,
            "chart_metric": [list(r) for r in self.chart_metric],
            "goal_node_ids": list(self.goal_node_ids),
            "objects": {oid: self.objects[oid].to_dict() for oid in sorted(self.objects)},
            "nodes": ordered_nodes,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class PresentationStep:
    """Student-facing pedagogical step projected exclusively from verified proof nodes (§14)."""

    step_id: str
    step_index: int
    construction_graph_refs: tuple[str, ...]
    object_ids: tuple[str, ...]
    action_type: PresentationActionType
    prerequisite_steps: tuple[str, ...]
    visual_emphasis: tuple[str, ...]
    camera_target: dict[str, Any] | None
    explanation_evidence: dict[str, Any]
    completion_condition: dict[str, Any]
    learner_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_index": self.step_index,
            "construction_graph_refs": list(self.construction_graph_refs),
            "object_ids": list(self.object_ids),
            "action_type": self.action_type,
            "prerequisite_steps": list(self.prerequisite_steps),
            "visual_emphasis": list(self.visual_emphasis),
            "camera_target": _json_safe(self.camera_target) if self.camera_target is not None else None,
            "explanation_evidence": _json_safe(self.explanation_evidence),
            "completion_condition": _json_safe(self.completion_condition),
            "learner_text": self.learner_text,
        }


@dataclass(frozen=True)
class PresentationStepGraph:
    """Pedagogical presentation DAG projected from a verified `ConstructionProofGraph`."""

    graph_id: str
    source_proof_graph_id: str
    steps: tuple[PresentationStep, ...]
    schema_version: str = PRESENTATION_STEP_GRAPH_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph_id": self.graph_id,
            "source_proof_graph_id": self.source_proof_graph_id,
            "steps": [s.to_dict() for s in self.steps],
        }


def topological_order(graph: ConstructionProofGraph) -> tuple[str, ...]:
    """Deterministic topological ordering over `graph.nodes`; raises `CYCLIC_DEPENDENCY` or `MISSING_PRECONDITION`."""
    by_id = graph.node_map()
    if len(by_id) != len(graph.nodes):
        seen: set[str] = set()
        dups = tuple(sorted({n.node_id for n in graph.nodes if n.node_id in seen or seen.add(n.node_id)}))
        raise GraphValidationError(ERR_MISSING_PRECOND, f"Duplicate node IDs in graph: {dups}", dups)

    in_deg: dict[str, int] = {nid: 0 for nid in by_id}
    adj: dict[str, list[str]] = {nid: [] for nid in by_id}
    priority_rank = {"GIVEN": 0, "CONSTRUCTION": 1, "DERIVED_RELATION": 2, "VERIFICATION": 3, "GOAL": 4}
    index_of = {n.node_id: idx for idx, n in enumerate(graph.nodes)}

    for node in graph.nodes:
        for dep in node.dependency_ids:
            if dep == node.node_id:
                raise GraphValidationError(ERR_CYCLIC, f"Node {node.node_id!r} depends on itself", (node.node_id,))
            if dep not in by_id:
                raise GraphValidationError(
                    ERR_MISSING_PRECOND,
                    f"Node {node.node_id!r} depends on missing node {dep!r}",
                    (node.node_id, dep),
                )
            adj[dep].append(node.node_id)
            in_deg[node.node_id] += 1

    heap: list[tuple[int, int, str]] = [
        (priority_rank.get(by_id[nid].node_type, 9), index_of[nid], nid)
        for nid, deg in in_deg.items()
        if deg == 0
    ]
    heapq.heapify(heap)
    order: list[str] = []
    while heap:
        _, _, cur = heapq.heappop(heap)
        order.append(cur)
        for nxt in adj[cur]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                heapq.heappush(heap, (priority_rank.get(by_id[nxt].node_type, 9), index_of[nxt], nxt))

    if len(order) != len(by_id):
        rem = tuple(sorted(nid for nid, deg in in_deg.items() if deg > 0))
        raise GraphValidationError(ERR_CYCLIC, f"Cyclic dependency detected among nodes {rem}", rem)
    return tuple(order)


def topological_order_safe(graph: ConstructionProofGraph) -> tuple[str, ...]:
    try:
        return topological_order(graph)
    except GraphValidationError:
        return ()


def trace_dependencies(graph: ConstructionProofGraph, target_node_ids: tuple[str, ...]) -> tuple[str, ...]:
    """Return full transitive backward dependency closure for `target_node_ids` in deterministic topological order."""
    by_id = graph.node_map()
    closure: set[str] = set()
    queue: deque[str] = deque()
    for tid in target_node_ids:
        if tid not in by_id:
            raise GraphValidationError(ERR_MISSING_PRECOND, f"Target node {tid!r} missing from graph", (tid,))
        if tid not in closure:
            closure.add(tid)
            queue.append(tid)
    while queue:
        cur = queue.popleft()
        for dep in by_id[cur].dependency_ids:
            if dep not in by_id:
                raise GraphValidationError(ERR_MISSING_PRECOND, f"Dangling dependency {dep!r}", (cur, dep))
            if dep not in closure:
                closure.add(dep)
                queue.append(dep)
    topo = topological_order(graph)
    return tuple(nid for nid in topo if nid in closure)


def find_unused_nodes(graph: ConstructionProofGraph) -> tuple[str, ...]:
    """Identify nodes not required by the backward dependency closure of `graph.goal_node_ids`."""
    if not graph.goal_node_ids:
        return ()
    by_id = graph.node_map()
    valid_goals = tuple(gid for gid in graph.goal_node_ids if gid in by_id)
    if not valid_goals:
        return tuple(n.node_id for n in graph.nodes)
    used = set(trace_dependencies(graph, valid_goals))
    return tuple(n.node_id for n in graph.nodes if n.node_id not in used)


def detect_duplicate_constructions(graph: ConstructionProofGraph) -> tuple[tuple[str, ...], ...]:
    """Detect distinct CONSTRUCTION nodes producing geometrically identical objects via `canonical_geom_key`."""
    by_geom_key: dict[str, list[str]] = {}
    for node in graph.nodes:
        if node.node_type != "CONSTRUCTION":
            continue
        for oid in node.output_objects:
            obj = graph.objects.get(oid)
            if obj is None or obj.object_kind in ("relation", "quantity"):
                continue
            by_geom_key.setdefault(obj.canonical_geom_key, []).append(node.node_id)
    groups = [tuple(sorted(set(nids))) for nids in by_geom_key.values() if len(set(nids)) > 1]
    return tuple(sorted(groups))


def prune_to_goal_closure(graph: ConstructionProofGraph) -> ConstructionProofGraph:
    """Return a clean copy containing only nodes & objects referenced inside `goal_node_ids` closure."""
    used_nids = set(trace_dependencies(graph, graph.goal_node_ids)) if graph.goal_node_ids else {n.node_id for n in graph.nodes}
    kept_nodes = tuple(n for n in graph.nodes if n.node_id in used_nids)
    kept_obj_ids = {
        oid
        for n in kept_nodes
        for oid in (*n.object_refs, *n.input_object_ids, *n.output_objects)
        if oid in graph.objects
    }
    kept_objects = {oid: graph.objects[oid] for oid in sorted(kept_obj_ids)}
    return ConstructionProofGraph(
        graph_id=graph.graph_id,
        nodes=kept_nodes,
        objects=kept_objects,
        goal_node_ids=graph.goal_node_ids,
        chart_metric=graph.chart_metric,
        length_unit=graph.length_unit,
        metadata={**graph.metadata, "pruned_unused_count": len(graph.nodes) - len(kept_nodes)},
        schema_version=graph.schema_version,
    )


def validate_construction_graph(
    graph: ConstructionProofGraph,
    *,
    require_verified_goal_closure: bool = True,
    allow_unused_nodes: bool = True,
    allow_duplicate_geometry: bool = False,
) -> GraphValidationReport:
    """Validate structural DAG invariants, preconditions, exact verification provenance, and consistency."""
    issues: list[dict[str, Any]] = []
    codes: list[str] = []

    def add_issue(code: str, detail: str, node_id: str | None = None) -> None:
        if code not in codes:
            codes.append(code)
        issues.append({"code": code, "detail": detail, "node_id": node_id})

    by_id = graph.node_map()
    if len(by_id) != len(graph.nodes):
        add_issue(ERR_MISSING_PRECOND, "Duplicate node_id detected in ConstructionProofGraph.")

    for node in graph.nodes:
        if node.verification_status == "CONTRADICTORY":
            add_issue(ERR_CONTRADICTORY, f"Node {node.node_id!r} marked CONTRADICTORY.", node.node_id)
        for oid in node.input_object_ids:
            if oid not in graph.objects:
                add_issue(ERR_MISSING_PRECOND, f"Node {node.node_id!r} references missing input object {oid!r}.", node.node_id)
        for oid in node.output_objects:
            if oid not in graph.objects:
                add_issue(ERR_MISSING_PRECOND, f"Node {node.node_id!r} references missing output object {oid!r}.", node.node_id)
            else:
                obj = graph.objects[oid]
                if obj.origin == "AUXILIARY_CONSTRUCTION" and node.node_type == "GIVEN":
                    add_issue(
                        ERR_CONTRADICTORY,
                        f"AUXILIARY_CONSTRUCTION {oid!r} cannot be produced by a GIVEN node.",
                        node.node_id,
                    )
        if node.node_type in ("CONSTRUCTION", "DERIVED_RELATION", "GOAL"):
            if not node.preconditions and node.node_type != "DERIVED_RELATION":
                add_issue(ERR_MISSING_PRECOND, f"Node {node.node_id!r} has empty preconditions.", node.node_id)
        if require_verified_goal_closure and node.verification_status != "VERIFIED":
            add_issue(
                ERR_UNVERIFIED,
                f"Node {node.node_id!r} has verification_status={node.verification_status!r} != 'VERIFIED'.",
                node.node_id,
            )
        if node.verification_status == "VERIFIED" and not node.verification_evidence:
            add_issue(
                ERR_UNVERIFIED,
                f"Node {node.node_id!r} marked VERIFIED without verification_evidence.",
                node.node_id,
            )

    topo: tuple[str, ...] = ()
    try:
        topo = topological_order(graph)
    except GraphValidationError as exc:
        add_issue(exc.code, exc.detail, exc.node_ids[0] if exc.node_ids else None)

    for gid in graph.goal_node_ids:
        if gid not in by_id:
            add_issue(ERR_MISSING_PRECOND, f"Goal node {gid!r} missing from graph.", gid)
        elif by_id[gid].node_type != "GOAL":
            add_issue(ERR_MISSING_PRECOND, f"Goal node {gid!r} has node_type={by_id[gid].node_type!r} != 'GOAL'.", gid)

    unused: tuple[str, ...] = ()
    dup_groups: tuple[tuple[str, ...], ...] = ()
    if topo and all(gid in by_id for gid in graph.goal_node_ids):
        unused = find_unused_nodes(graph)
        if unused and not allow_unused_nodes:
            add_issue(ERR_UNVERIFIED, f"Graph contains unused nodes outside goal closure: {unused}")
    dup_groups = detect_duplicate_constructions(graph)
    if dup_groups and not allow_duplicate_geometry:
        add_issue(ERR_DUPLICATE_GEOM, f"Duplicate geometric constructions detected: {dup_groups}")

    return GraphValidationReport(
        valid=len(issues) == 0,
        failure_codes=tuple(codes),
        issues=tuple(issues),
        topological_node_order=topo,
        unused_node_ids=unused,
        duplicate_construction_groups=dup_groups,
    )


def project_to_presentation_graph(proof_graph: ConstructionProofGraph) -> PresentationStepGraph:
    """Deterministically project a validated `ConstructionProofGraph` into `PresentationStepGraph` (§14).

    Filters out internal `VERIFICATION` nodes from student-visible steps while attaching their
    exact verification evidence directly onto the owning construction/goal step.
    """
    report = validate_construction_graph(proof_graph, require_verified_goal_closure=True, allow_duplicate_geometry=False)
    if not report.valid:
        raise GraphValidationError(
            report.failure_codes[0],
            f"Cannot project unverified ConstructionProofGraph: {report.issues[0]['detail']}",
        )

    by_id = proof_graph.node_map()
    ordered_nodes = [by_id[nid] for nid in report.topological_node_order]
    verif_evidence_by_target: dict[str, list[dict[str, Any]]] = {}
    for node in ordered_nodes:
        if node.node_type == "VERIFICATION":
            for dep in node.dependency_ids:
                verif_evidence_by_target.setdefault(dep, []).append(
                    {
                        "verification_node_id": node.node_id,
                        "exact_computation_ref": node.exact_computation_ref,
                        "evidence": dict(node.verification_evidence),
                    }
                )

    steps: list[PresentationStep] = []
    node_to_step: dict[str, str] = {}

    given_nodes = [n for n in ordered_nodes if n.node_type == "GIVEN"]
    if given_nodes:
        step_id = "pstep_0"
        given_refs = tuple(n.node_id for n in given_nodes)
        given_objs = tuple(dict.fromkeys(oid for n in given_nodes for oid in n.object_refs))
        for nid in given_refs:
            node_to_step[nid] = step_id
        steps.append(
            PresentationStep(
                step_id=step_id,
                step_index=0,
                construction_graph_refs=given_refs,
                object_ids=given_objs,
                action_type="INIT_GIVEN",
                prerequisite_steps=(),
                visual_emphasis=given_objs[:6],
                camera_target={"focus_object_ids": list(given_objs[:4])},
                explanation_evidence={
                    "source_fact_refs": sorted({r for n in given_nodes for r in n.source_fact_refs}),
                    "verified_by": [n.verification_evidence for n in given_nodes],
                },
                completion_condition={"required_objects_visible": list(given_objs)},
                learner_text="Khởi tạo các đối tượng hình học ban đầu từ giả thiết đã kiểm chứng của đề bài.",
            )
        )

    for node in ordered_nodes:
        if node.node_type in ("GIVEN", "VERIFICATION"):
            continue
        # Only present meaningful geometric steps; internal trivial equality checks stay in evidence
        if node.geometry_context.get("presentation_internal_only"):
            for dep in node.dependency_ids:
                if dep in node_to_step:
                    node_to_step[node.node_id] = node_to_step[dep]
                    break
            continue

        step_idx = len(steps)
        step_id = f"pstep_{step_idx}"
        node_to_step[node.node_id] = step_id
        prereq_steps = tuple(
            dict.fromkeys(node_to_step[d] for d in node.dependency_ids if d in node_to_step and node_to_step[d] != step_id)
        )
        out_objs = node.output_objects or node.object_refs
        any_aux = any(
            (oid in proof_graph.objects and proof_graph.objects[oid].origin == "AUXILIARY_CONSTRUCTION")
            for oid in out_objs
        )
        if node.node_type == "GOAL":
            action_type: PresentationActionType = "MEASURE_GOAL"
        elif node.node_type == "DERIVED_RELATION":
            action_type = "ESTABLISH_RELATION"
        elif any_aux:
            action_type = "CONSTRUCT_AUXILIARY"
        else:
            action_type = "CONSTRUCT_DERIVED"

        learner_text = str(
            node.scene3d_render_hints.get("learner_text")
            or f"Thực hiện bước {node.producing_operation_id or node.node_type.lower()} tạo {', '.join(out_objs)}."
        )
        steps.append(
            PresentationStep(
                step_id=step_id,
                step_index=step_idx,
                construction_graph_refs=(node.node_id,),
                object_ids=out_objs,
                action_type=action_type,
                prerequisite_steps=prereq_steps,
                visual_emphasis=out_objs,
                camera_target={"focus_object_ids": list(out_objs)},
                explanation_evidence={
                    "producing_operation_id": node.producing_operation_id,
                    "preconditions": list(node.preconditions),
                    "derived_constraints": list(node.derived_constraints),
                    "node_verification": dict(node.verification_evidence),
                    "attached_verifications": verif_evidence_by_target.get(node.node_id, []),
                },
                completion_condition={"required_objects_visible": list(out_objs)},
                learner_text=learner_text,
            )
        )

    return PresentationStepGraph(
        graph_id=f"pres_{proof_graph.graph_id}",
        source_proof_graph_id=proof_graph.graph_id,
        steps=tuple(steps),
    )
