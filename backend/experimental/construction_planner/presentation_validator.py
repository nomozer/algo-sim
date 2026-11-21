# -*- coding: utf-8 -*-
"""Presentation step quality validator & multi-plan Scene3D switch auditor (`presentation-step-validator/1`).

Enforces all Phase J (§18) presentation invariants and Phase I (§17) multi-plan switching invariants.
Zero runtime AI calls; strictly deterministic validation over `(ConstructionProofGraph, PresentationStepGraph, Scene3D)`.
"""
from __future__ import annotations

from typing import Any

from . import PRESENTATION_VALIDATOR_VERSION
from .construction_graph import ConstructionProofGraph, PresentationStepGraph
from .construction_state import InitialGeometryFrame
from .construction_verifier import VerificationReport, verify_full_proof_and_scene
from .scene3d_bridge import compile_proof_graph_to_scene3d

_INTERNAL_LEAK_TOKENS = ("VERIFIED", "UNVERIFIED", "node_id", "schema_version", "n_step_", "n_goal_", "op.")


def validate_presentation_step_graph(
    proof_graph: ConstructionProofGraph,
    pres_graph: PresentationStepGraph,
) -> dict[str, Any]:
    """Audit all 6 §18 student-facing pedagogical & epistemic invariants."""
    issues: list[str] = []
    if pres_graph.source_proof_graph_id != proof_graph.graph_id:
        issues.append("source_proof_graph_id mismatch")

    node_map = proof_graph.node_map()
    verified_objs = {oid for oid, obj in proof_graph.objects.items() if obj.supporting_node_id in node_map and node_map[obj.supporting_node_id].verification_status == "VERIFIED"}
    # Also include any object referenced on a verified node
    for n in proof_graph.nodes:
        if n.verification_status == "VERIFIED":
            verified_objs.update(n.output_objects)

    seen_step_ids: set[str] = set()
    for expected_idx, step in enumerate(pres_graph.steps):
        if step.step_index != expected_idx:
            issues.append(f"non-sequential step_index at {step.step_id}: {step.step_index} != {expected_idx}")
        if step.step_id in seen_step_ids:
            issues.append(f"duplicate step_id {step.step_id}")

        # 1. No unverified objects or objects missing from ProofGraph
        for oid in step.object_ids:
            if oid not in verified_objs:
                issues.append(f"{step.step_id} introduces object {oid!r} absent from verified ProofGraph")

        # 2. All construction_graph_refs must exist in ProofGraph and be VERIFIED
        if not step.construction_graph_refs:
            issues.append(f"{step.step_id} lacks construction_graph_refs evidence")
        for ref in step.construction_graph_refs:
            if ref not in node_map:
                issues.append(f"{step.step_id} references missing proof node {ref!r}")
            elif node_map[ref].verification_status != "VERIFIED":
                issues.append(f"{step.step_id} references non-VERIFIED node {ref!r}")

        # 3. No dependency reversal: every prerequisite_step must appear earlier
        for req in step.prerequisite_steps:
            if req not in seen_step_ids:
                issues.append(f"{step.step_id} depends on unseen/future step {req!r}")

        # 4. MEASURE_GOAL must link to GOAL proof node (cannot turn calculation into geometric construction)
        if step.action_type == "MEASURE_GOAL":
            if not any(node_map[r].node_type == "GOAL" for r in step.construction_graph_refs if r in node_map):
                issues.append(f"{step.step_id} is MEASURE_GOAL without backing GOAL node")

        # 5. Explanation provenance bound to ProofGraph node evidence
        if step.action_type != "INIT_GIVEN" and "node_verification" not in step.explanation_evidence:
            issues.append(f"{step.step_id} missing node_verification provenance in explanation_evidence")

        # 6. No raw internal proof tokens leaked into student-visible learner_text
        for bad_tok in _INTERNAL_LEAK_TOKENS:
            if bad_tok in step.learner_text:
                issues.append(f"{step.step_id} learner_text leaks internal token {bad_tok!r}: {step.learner_text!r}")

        seen_step_ids.add(step.step_id)

    return {
        "validator_version": PRESENTATION_VALIDATOR_VERSION,
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "step_count": len(pres_graph.steps),
    }


def validate_multiplan_switching(
    frame: InitialGeometryFrame,
    plans: tuple[Any, ...],
) -> dict[str, Any]:
    """Compile and audit all 7 §17 multi-plan Scene3D switch invariants without frontend mutation."""
    if not plans:
        return {"valid": False, "issues": ["empty plans list"], "plan_bundles": []}

    bundles: list[dict[str, Any]] = []
    issues: list[str] = []
    answers: set[str] = set()
    given_sets: list[frozenset[str]] = []

    for idx, plan in enumerate(plans):
        pres_check = validate_presentation_step_graph(plan.proof_graph, plan.presentation_graph)
        if not pres_check["valid"]:
            issues.extend(f"plan_{idx + 1}: {x}" for x in pres_check["issues"])
        scene = compile_proof_graph_to_scene3d(frame, plan.proof_graph, plan.presentation_graph)
        rep: VerificationReport = verify_full_proof_and_scene(
            plan.proof_graph, frame.chart_metric, scene3d=scene, strict_node_replay=True
        )
        if not rep.passed:
            issues.append(f"plan_{idx + 1} failed L0-L4 Scene3D verification: {rep.failure_code}")

        answers.add(str(plan.answer))
        # Core given problem geometry (vertices & base solid) must remain invariant across all alternative plans;
        # individual helper lines/planes from GIVEN solids (e.g. `ln_B_C` needed only by 2-step Plan #2) may appear in closure subsets.
        given_core_ids = frozenset(
            o["id"] for o in scene["objects"] if o.get("origin") == "given" and o.get("type") in ("point3", "solid")
        )
        missing_frame_pts = set(frame.points.keys()) - given_core_ids
        if missing_frame_pts:
            issues.append(f"plan_{idx + 1} dropped given frame points: {sorted(missing_frame_pts)}")
        given_sets.append(given_core_ids)

        # Verify self-contained object namespace & zero cross-plan dangling references inside each plan Scene3D
        scene_ids = {o["id"] for o in scene["objects"]}
        for step in scene["formation"]["steps"]:
            for vis in step.get("visible_ids", []):
                if vis not in scene_ids:
                    issues.append(f"plan_{idx + 1} step {step['step_id']} references missing object {vis!r}")
            for hi in step.get("highlighted_ids", []):
                if hi not in scene_ids:
                    issues.append(f"plan_{idx + 1} step {step['step_id']} highlights non-existent {hi!r}")
        if scene.get("chart_metric") != [list(r) for r in frame.chart_metric_strs]:
            issues.append(f"plan_{idx + 1} altered chart_metric")

        bundles.append(
            {
                "plan_rank": plan.rank,
                "answer": plan.answer,
                "source_proof_graph_id": scene["diagnostics"]["source_proof_graph_id"],
                "scene_object_ids": sorted(scene_ids),
                "step_count": len(scene["formation"]["steps"]),
                "auxiliary_object_ids": sorted(
                    o["id"] for o in scene["objects"] if "auxiliary" in (o.get("display_group") or [])
                ),
                "l0_l4_passed": rep.passed,
                "presentation_valid": pres_check["valid"],
            }
        )

    # Check mathematical invariance across alternative plans
    if len(answers) != 1:
        issues.append(f"Alternative plans produced conflicting mathematical answers: {sorted(answers)}")
    # Check given objects never vanish across plans
    if len(set(given_sets)) != 1:
        issues.append("Given object set changed when switching plans")
    # Check plans are structurally isolated (`source_proof_graph_id` unique per plan)
    pg_ids = [b["source_proof_graph_id"] for b in bundles]
    if len(pg_ids) != len(set(pg_ids)):
        issues.append("Duplicate source_proof_graph_id across alternative plan bundles")

    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "plans_count": len(bundles),
        "unique_answer": next(iter(answers)) if len(answers) == 1 else None,
        "plan_bundles": bundles,
    }


def compile_multiplan_scene3d_bundle(
    frame: InitialGeometryFrame,
    plans: tuple[Any, ...],
) -> dict[str, Any]:
    """Build multi-plan Scene3D response payload ready for `Scene3DExplorer.tsx` consumption."""
    plan_payloads = []
    for p in plans:
        sc = compile_proof_graph_to_scene3d(frame, p.proof_graph, p.presentation_graph)
        plan_payloads.append(
            {
                "rank": p.rank,
                "label": f"Cách {p.rank}",
                "answer": p.answer,
                "proof_graph_id": p.proof_graph.graph_id,
                "presentation_step_graph": p.presentation_graph.to_dict(),
                "scene3d": sc,
            }
        )
    validation = validate_multiplan_switching(frame, plans)
    return {
        "active_plan_index": 0,
        "plans_count": len(plan_payloads),
        "plans": plan_payloads,
        "multiplan_validation": validation,
    }
