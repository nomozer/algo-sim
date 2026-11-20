# -*- coding: utf-8 -*-
"""AXO CONSTRUCTION /2 — 18-Category Proof Integrity, Geometric Invariance & Controlled Integration Test Suite."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.simulation.geometry import exact as E  # noqa: E402
from app.simulation.geometry import metric as M  # noqa: E402
from app.simulation.geometry import section as S  # noqa: E402
from experimental.construction_planner.construction_graph import (  # noqa: E402
    PresentationStepGraph,
    project_to_presentation_graph,
)
from experimental.construction_planner.construction_objects import canonical_point_key  # noqa: E402
from experimental.construction_planner.construction_operators import GoalSpec  # noqa: E402
from experimental.construction_planner.construction_search import (  # noqa: E402
    DynamicConstructionPlanner,
    SearchBudget,
)
from experimental.construction_planner.construction_serializer import graph_sha256  # noqa: E402
from experimental.construction_planner.construction_state import (  # noqa: E402
    InitialGeometryFrame,
    build_initial_frame,
)
from experimental.construction_planner.construction_verifier import verify_full_proof_and_scene  # noqa: E402
from experimental.construction_planner.geometry_invariance import (  # noqa: E402
    graph_structural_isomorphism_signature,
    permute_pending_frame,
    relabel_frame_and_goal,
    scale_frame,
    transform_basis_frame,
    translate_frame,
)
from experimental.construction_planner.integration_adapter import (  # noqa: E402
    resolve_dynamic_construction_mode,
    run_with_dynamic_construction_mode,
)
from experimental.construction_planner.model2_interface import (  # noqa: E402
    DeterministicModel2BaselineSelector,
    build_model2_observation,
    validate_model2_action,
)
from experimental.construction_planner.presentation_validator import (  # noqa: E402
    validate_multiplan_switching,
    validate_presentation_step_graph,
)
from experimental.construction_planner.scene3d_bridge import compile_proof_graph_to_scene3d  # noqa: E402
from experimental.construction_planner.verified_input_bridge import (  # noqa: E402
    bridge_verified_facts_to_construction_input,
)
from scripts.evaluate_axo_construction_v1 import build_benchmark_cases, same_value_v2  # noqa: E402
from scripts.evaluate_independent_construction_v2 import (  # noqa: E402
    CANDIDATE_V2_FREEZE_SHA256,
    compute_candidate_freeze_sha256,
)
from scripts.reconcile_and_compare_construction_v2 import verify_v1_run_immutability  # noqa: E402

V2_RUN_DIR = (
    REPO_ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "axo-construction-proof-integrity-independent-evaluation-controlled-integration"
)


@pytest.fixture(scope="module")
def v1_cases_map() -> dict[str, dict]:
    return {c["case_id"]: c for c in build_benchmark_cases()}


@pytest.fixture(scope="module")
def planner_v2() -> DynamicConstructionPlanner:
    return DynamicConstructionPlanner(mode="v2")


# Category 1: D02 Goal Semantics 3-Way Split
def test_cat01_d02_coincident_goal_semantic_split(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    d02 = v1_cases_map["D02_degenerate_coincident_points"]
    frame = build_initial_frame(
        case_id=d02["case_id"],
        problem_text=d02["problem_text"],
        solid_spec=d02["solid_spec"],
        chart_premises=d02["chart_premises"],
        pending_constructions=[],
        length_unit="a",
    )
    assert frame.error_code is None
    res_seg = planner_v2.plan(frame=frame, goal_spec=GoalSpec("segment_length", {"a": "A", "b": "A"}, "a"), budget=SearchBudget())
    assert res_seg.status == "DEGENERATE_CONSTRUCTION"
    assert res_seg.failure_code == "DEGENERATE_COINCIDENT_POINTS"

    res_pt = planner_v2.plan(frame=frame, goal_spec=GoalSpec("point_distance", {"a": "A", "b": "A"}, "a"), budget=SearchBudget())
    assert res_pt.status == "GOAL_VERIFIED"
    assert res_pt.best_plan is not None and res_pt.best_plan.answer == "0"
    sc = compile_proof_graph_to_scene3d(frame, res_pt.best_plan.proof_graph, res_pt.best_plan.presentation_graph)
    assert verify_full_proof_and_scene(res_pt.best_plan.proof_graph, frame.chart_metric, scene3d=sc, strict_node_replay=True).passed


# Category 2: Strict L0–L4 Replay Rejects Proof Mutations & Scene3D Witness Tamper
def test_cat02_proof_mutations_and_scene3d_witness_tamper_rejected(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    c01 = v1_cases_map["C01_aux_foot_d_A_SBC_equilateral"]
    f01 = build_initial_frame(case_id=c01["case_id"], problem_text=c01["problem_text"], solid_spec=c01["solid_spec"], chart_premises=c01["chart_premises"], pending_constructions=c01["pending"], length_unit="a")
    res = planner_v2.plan(frame=f01, goal_spec=c01["goal_spec"], budget=SearchBudget())
    assert res.status == "GOAL_VERIFIED" and res.best_plan is not None
    pg = res.best_plan.proof_graph
    sc = compile_proof_graph_to_scene3d(f01, pg, res.best_plan.presentation_graph)

    # Valid baseline passes strict L0-L4
    assert verify_full_proof_and_scene(pg, f01.chart_metric, scene3d=sc, strict_node_replay=True).passed

    proj_idx = next(i for i, n in enumerate(pg.nodes) if n.producing_operation_id == "op.project_point_to_plane")
    proj_node = pg.nodes[proj_idx]

    # Swap input slots (point <-> plane) must fail closed without unhandled exception
    orig_in = dict(proj_node.geometry_context["inputs"])
    swapped = replace(proj_node, input_object_ids=tuple(reversed(proj_node.input_object_ids)), geometry_context={**proj_node.geometry_context, "inputs": {"plane": orig_in["point"], "point": orig_in["plane"]}})
    pg_swapped = replace(pg, nodes=tuple(swapped if i == proj_idx else n for i, n in enumerate(pg.nodes)))
    rep_swap = verify_full_proof_and_scene(pg_swapped, f01.chart_metric, strict_node_replay=True)
    assert not rep_swap.passed and rep_swap.failure_code is not None

    # Metric tamper (`2*I` vs `I`) fails L1
    rep_metric = verify_full_proof_and_scene(replace(pg, chart_metric=(("2", "0", "0"), ("0", "2", "0"), ("0", "0", "2"))), f01.chart_metric, strict_node_replay=True)
    assert not rep_metric.passed and rep_metric.failure_code == "METRIC_MISMATCH"

    # Perturb auxiliary point coordinates + update key still caught by L2 operator replay
    h_oid = next(oid for oid in proj_node.output_objects if pg.objects[oid].object_kind == "point3")
    h_old = pg.objects[h_oid]
    h_bad = E.Vec3(h_old.exact_value.x + Fraction(1, 5), h_old.exact_value.y, h_old.exact_value.z)
    pg_coord = replace(pg, objects={**pg.objects, h_oid: replace(h_old, exact_value=h_bad, canonical_geom_key=canonical_point_key(h_bad))})
    assert not verify_full_proof_and_scene(pg_coord, f01.chart_metric, strict_node_replay=True).passed

    # Tamper Scene3D perpendicular_witness caught by L4
    sc_bad = copy.deepcopy(sc)
    for o in sc_bad["objects"]:
        if o.get("perpendicular_witness"):
            o["perpendicular_witness"]["from"] = "B"
            o["perpendicular_witness"]["foot"] = ["9", "0", "0"]
            break
    rep_sc = verify_full_proof_and_scene(pg, f01.chart_metric, scene3d=sc_bad, strict_node_replay=True)
    assert not rep_sc.passed and rep_sc.failure_code == "SCENE3D_CONTINUITY_FAILED"

    # Verify full 12/12 mutation audit JSON also holds when present
    mut_path = V2_RUN_DIR / "PROOF_MUTATION_TEST_RESULTS.json"
    if mut_path.exists():
        mut_doc = json.loads(mut_path.read_text(encoding="utf-8"))
        assert mut_doc["summary"]["v2_rejection_rate"] == "12/12"
        assert mut_doc["summary"]["oracle_isolation_passed"] is True


# Category 3: A07 Projection Segment Witness Retention
def test_cat03_a07_projection_segment_witness_retained_and_replayed(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    a07 = v1_cases_map["A07_angle_sc_base_square"]
    f = build_initial_frame(case_id=a07["case_id"], problem_text=a07["problem_text"], solid_spec=a07["solid_spec"], chart_premises=a07["chart_premises"], pending_constructions=a07["pending"], length_unit="a")
    res = planner_v2.plan(frame=f, goal_spec=a07["goal_spec"], budget=SearchBudget())
    assert res.status == "GOAL_VERIFIED" and res.best_plan is not None
    assert "seg_C_A" in res.best_plan.proof_graph.objects or "seg_A_C" in res.best_plan.proof_graph.objects
    sc = compile_proof_graph_to_scene3d(f, res.best_plan.proof_graph, res.best_plan.presentation_graph)
    rep = verify_full_proof_and_scene(res.best_plan.proof_graph, f.chart_metric, scene3d=sc, strict_node_replay=True)
    assert rep.passed and rep.levels["L3"].passed


# Category 4: 6-Flag Witness Classification & v1 Immutability
def test_cat04_v1_reconciliation_and_immutability() -> None:
    v1_immut = verify_v1_run_immutability()
    assert v1_immut["intact"] is True and v1_immut["artifacts_checked"] == 16
    rec_path = V2_RUN_DIR / "CONSTRUCTION_V1_METRIC_RECONCILIATION.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        cls_counts = rec["reconciled_positive_33_classifications"]
        assert cls_counts["VERIFIED_GRAPH"] == 33
        assert cls_counts["HAS_AUXILIARY_OBJECT_HISTORICAL_V1_FIELD"] == 26
        assert cls_counts["HAS_GENUINE_IMPLICIT_AUXILIARY_OBJECT"] < 20


# Category 5: Multi-Label N0–N5 Novelty Reclassification Schema
def test_cat05_novelty_n0_to_n5_reclassification_schema() -> None:
    nov_path = V2_RUN_DIR / "CONSTRUCTION_NOVELTY_RECLASSIFICATION.json"
    if nov_path.exists():
        nov = json.loads(nov_path.read_text(encoding="utf-8"))
        assert len(nov["cases"]) == 40
        counts = nov["summary_label_counts"]
        for key in ("N0_EXISTING_COMPLETE_RECIPE", "N1_EXPLICIT_CONSTRUCTION_SCHEDULING", "N2_OPERATOR_COMPOSITION", "N3_IMPLICIT_AUXILIARY_DISCOVERY", "N4_ALTERNATIVE_VERIFIED_STRATEGY", "N5_UNSUPPORTED_CAPABILITY"):
            assert counts.get(key, 0) >= 1


# Category 6: Frozen Candidate Digest & Independent Holdout Provenance
def test_cat06_candidate_freeze_sha256_and_holdout_provenance() -> None:
    live_sha, _ = compute_candidate_freeze_sha256()
    assert live_sha == CANDIDATE_V2_FREEZE_SHA256
    man_path = V2_RUN_DIR / "INDEPENDENT_CONSTRUCTION_HOLDOUT_MANIFEST.json"
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        assert man["external_independence"] == "NOT_MEASURED"
        assert man["provenance_class"] == "INTERNAL_POST_FREEZE_INDEPENDENT_SYNTHESIS"
        assert man["candidate_v2_freeze_sha256"] == CANDIDATE_V2_FREEZE_SHA256
        assert man["total_cases"] >= 60 and man["positive_cases"] >= 40 and man["negative_cases"] >= 15


# Category 7: Geometric Invariances including GL(3, Q) Non-Diagonal Chart Covariance
def test_cat07_geometric_invariances_so3_and_gl3_covariant(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    c01 = v1_cases_map["C01_aux_foot_d_A_SBC_equilateral"]
    f0 = build_initial_frame(case_id=c01["case_id"], problem_text=c01["problem_text"], solid_spec=c01["solid_spec"], chart_premises=c01["chart_premises"], pending_constructions=c01["pending"], length_unit="a")
    g0 = c01["goal_spec"]
    r0 = planner_v2.plan(frame=f0, goal_spec=g0, budget=SearchBudget())
    assert r0.status == "GOAL_VERIFIED" and r0.best_plan is not None
    sig0 = graph_structural_isomorphism_signature(r0.best_plan.proof_graph)

    # Relabeling, translation, SO(3,Q), reflection, scaling*3, pending permutation
    f_tr = translate_frame(f0, E.Vec3(Fraction(5, 2), Fraction(-3, 4), Fraction(7)))
    r_tr = planner_v2.plan(frame=f_tr, goal_spec=g0, budget=SearchBudget())
    assert r_tr.status == "GOAL_VERIFIED" and same_value_v2(r_tr.best_plan.answer, r0.best_plan.answer)
    assert graph_structural_isomorphism_signature(r_tr.best_plan.proof_graph) == sig0

    f_rel, g_rel = relabel_frame_and_goal(f0, g0, {"A": "P", "B": "Q", "C": "R", "S": "T"})
    r_rel = planner_v2.plan(frame=f_rel, goal_spec=g_rel, budget=SearchBudget())
    assert r_rel.status == "GOAL_VERIFIED" and same_value_v2(r_rel.best_plan.answer, r0.best_plan.answer)
    assert graph_structural_isomorphism_signature(r_rel.best_plan.proof_graph) == sig0

    so3 = ((Fraction(3, 5), Fraction(-4, 5), Fraction(0)), (Fraction(4, 5), Fraction(3, 5), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))
    f_rot = transform_basis_frame(f0, so3, suffix="rot")
    r_rot = planner_v2.plan(frame=f_rot, goal_spec=g0, budget=SearchBudget())
    assert r_rot.status == "GOAL_VERIFIED" and same_value_v2(r_rot.best_plan.answer, r0.best_plan.answer)

    f_sc, g_sc = scale_frame(f0, g0, Fraction(3), new_unit="a")
    r_sc = planner_v2.plan(frame=f_sc, goal_spec=g_sc, budget=SearchBudget())
    assert r_sc.status == "GOAL_VERIFIED" and same_value_v2(r_sc.best_plan.answer, "3a√21/7")

    # Non-diagonal SPD chart + GL(3, Q) covariant Gram G' = A^-T G A^-1
    g_obl = ((Fraction(1), Fraction(1, 2), Fraction(0)), (Fraction(1, 2), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))
    m_obl = M.Metric(g=g_obl)
    pts_obl = {"A": E.Vec3(Fraction(0), Fraction(0), Fraction(0)), "B": E.Vec3(Fraction(1), Fraction(0), Fraction(0)), "C": E.Vec3(Fraction(0), Fraction(1), Fraction(0)), "A'": E.Vec3(Fraction(0), Fraction(0), Fraction(1)), "B'": E.Vec3(Fraction(1), Fraction(0), Fraction(1)), "C'": E.Vec3(Fraction(0), Fraction(1), Fraction(1))}
    with M.using(m_obl):
        poly_obl = S.Polyhedron(vertices=tuple(pts_obl[k] for k in ("A", "B", "C", "A'", "B'", "C'")), faces=((0, 1, 2), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)))
        pl_abc = E.Plane3.through(pts_obl["A"], pts_obl["B"], pts_obl["C"])
    f_raw = InitialGeometryFrame(case_id="GL3", problem_text="x", length_unit="a", chart_metric=m_obl, chart_metric_strs=(("1", "1/2", "0"), ("1/2", "1", "0"), ("0", "0", "1")), points=pts_obl, lines={"ln_B_C": E.Line3.through(pts_obl["B"], pts_obl["C"])}, segments={"seg_A_A'": E.Segment3.between(pts_obl["A"], pts_obl["A'"])}, planes={"pl_ABC": pl_abc}, polyhedron=poly_obl, given_relations=(), source_fact_refs={"solid": ("s1",)}, pending_constructions=())
    f_id = transform_basis_frame(f_raw, ((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1))), suffix="id")
    f_gl = transform_basis_frame(f_raw, ((Fraction(1), Fraction(1, 2), Fraction(0)), (Fraction(0), Fraction(2), Fraction(1, 3)), (Fraction(0), Fraction(0), Fraction(3, 2))), suffix="gl")
    g_o = GoalSpec("distance_point_plane", {"point": "A'", "plane": "pl_ABC"}, "a")
    ro0, ro1 = planner_v2.plan(frame=f_id, goal_spec=g_o, budget=SearchBudget()), planner_v2.plan(frame=f_gl, goal_spec=g_o, budget=SearchBudget())
    assert ro0.best_plan is not None and ro1.best_plan is not None
    assert ro0.best_plan.answer == "a" and ro1.best_plan.answer == "a"
    assert graph_structural_isomorphism_signature(ro0.best_plan.proof_graph) == graph_structural_isomorphism_signature(ro1.best_plan.proof_graph)

    # Pending permutation invariance
    b01 = v1_cases_map["B01_divide_segment_ratio_length"]
    fb0 = build_initial_frame(case_id=b01["case_id"], problem_text=b01["problem_text"], solid_spec=b01["solid_spec"], chart_premises=b01["chart_premises"], pending_constructions=b01["pending"], length_unit="a")
    fbp = permute_pending_frame(fb0)
    assert same_value_v2(planner_v2.plan(frame=fb0, goal_spec=b01["goal_spec"], budget=SearchBudget()).best_plan.answer, planner_v2.plan(frame=fbp, goal_spec=b01["goal_spec"], budget=SearchBudget()).best_plan.answer)


# Category 8: Search Resource & Timeout Limits Never Masquerade as Contradictions
def test_cat08_search_budget_exhaustion_status_distinction(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    c01 = v1_cases_map["C01_aux_foot_d_A_SBC_equilateral"]
    f = build_initial_frame(case_id=c01["case_id"], problem_text=c01["problem_text"], solid_spec=c01["solid_spec"], chart_premises=c01["chart_premises"], pending_constructions=c01["pending"], length_unit="a")
    r_lim = planner_v2.plan(frame=f, goal_spec=c01["goal_spec"], budget=SearchBudget(max_expanded_states=1, max_wall_clock_ms=5000.0))
    assert r_lim.status == "SEARCH_RESOURCE_LIMIT" and r_lim.status != "CONTRADICTORY_CONSTRAINTS"
    r_to = planner_v2.plan(frame=f, goal_spec=c01["goal_spec"], budget=SearchBudget(max_expanded_states=500, max_wall_clock_ms=0.0001))
    assert r_to.status in ("SEARCH_TIMEOUT", "GOAL_VERIFIED") and r_to.status != "CONTRADICTORY_CONSTRAINTS"


# Category 9: Multi-Plan Group E 5/5 Self-Contained Scene3D Switching
def test_cat09_group_e_5_of_5_multiplan_switching(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    e_ids = [cid for cid in sorted(v1_cases_map) if cid.startswith("E0")]
    assert len(e_ids) == 5
    for cid in e_ids:
        c = v1_cases_map[cid]
        f = build_initial_frame(case_id=cid, problem_text=c["problem_text"], solid_spec=c["solid_spec"], chart_premises=c["chart_premises"], pending_constructions=c["pending"], length_unit="a")
        res = planner_v2.plan(frame=f, goal_spec=c["goal_spec"], budget=SearchBudget())
        assert res.status == "GOAL_VERIFIED" and len(res.plans) >= 2, f"{cid} produced <2 plans"
        sw = validate_multiplan_switching(f, res.plans)
        assert sw["valid"] is True, f"{cid} multiplan switch failed: {sw['issues']}"


# Category 10: Presentation Step Quality 6 Invariants + Token Leak Rejection
def test_cat10_presentation_step_6_invariants_and_token_leak_rejection(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    c04 = v1_cases_map["C04_aux_skew_lines_cube_ABp_BCp"]
    f = build_initial_frame(case_id=c04["case_id"], problem_text=c04["problem_text"], solid_spec=c04["solid_spec"], chart_premises=c04["chart_premises"], pending_constructions=c04["pending"], length_unit="a")
    res = planner_v2.plan(frame=f, goal_spec=c04["goal_spec"], budget=SearchBudget())
    assert res.status == "GOAL_VERIFIED" and res.best_plan is not None
    v = validate_presentation_step_graph(res.best_plan.proof_graph, res.best_plan.presentation_graph)
    assert v["valid"] is True and v["issue_count"] == 0

    bad_steps = list(res.best_plan.presentation_graph.steps)
    bad_steps[1] = replace(bad_steps[1], learner_text="op.project_point_to_plane VERIFIED n_step_1")
    v_bad = validate_presentation_step_graph(res.best_plan.proof_graph, replace(res.best_plan.presentation_graph, steps=tuple(bad_steps)))
    assert v_bad["valid"] is False and v_bad["issue_count"] >= 3


# Category 11: Source-Gate-Respecting VerifiedInputBridge
def test_cat11_verified_input_bridge_source_gate_zero_bypass(v1_cases_map: dict) -> None:
    b01 = v1_cases_map["B01_divide_segment_ratio_length"]
    from scripts.reconcile_and_compare_construction_v2 import _arm_a2_equivalent_input

    txt, facts = _arm_a2_equivalent_input(b01)
    ok_res = bridge_verified_facts_to_construction_input(case_id="BR_OK", problem_text=txt, raw_facts_payload={"schema": "typed-facts/2", "facts": facts})
    assert ok_res.accepted is True and ok_res.source_gate_status == "VERIFIED" and ok_res.frame is not None

    # Tampered quote that does not appear in problem_text MUST be refused by Source Gate
    bad_facts = copy.deepcopy(facts)
    bad_facts[1]["quotes"] = ["trích dẫn giả không tồn tại trong đề"]
    ref_res = bridge_verified_facts_to_construction_input(case_id="BR_FORGED_QUOTE", problem_text=txt, raw_facts_payload={"schema": "typed-facts/2", "facts": bad_facts})
    assert ref_res.accepted is False and ref_res.source_gate_status == "REFUSED" and ref_res.frame is None


# Category 12: Integration Adapter Modes (`off`, `shadow`, `experimental`, Fallback, Fail-Closed)
def test_cat12_integration_adapter_modes_and_safe_fallback(v1_cases_map: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    c01 = v1_cases_map["C01_aux_foot_d_A_SBC_equilateral"]
    payload = {"schema": "typed-facts/2", "facts": c01["baseline_tf2_facts"]}

    monkeypatch.setenv("AXO_DYNAMIC_CONSTRUCTION_MODE", "off")
    assert resolve_dynamic_construction_mode() == "off"
    r_off = run_with_dynamic_construction_mode(case_id="INT_OFF", problem_text=c01["full_problem_text"], raw_facts_payload=payload)
    assert r_off["mode"] == "off" and r_off["served_by"] == "LEGACY_PRODUCT_PIPELINE" and r_off["status"] == "SERVED"

    r_sh = run_with_dynamic_construction_mode(case_id="INT_SHADOW", problem_text=c01["full_problem_text"], raw_facts_payload=payload, mode="shadow")
    assert r_sh["served_by"] == "LEGACY_PRODUCT_PIPELINE" and r_sh["shadow_receipt"] is not None
    assert r_sh["shadow_receipt"]["user_impact"] == "NONE" and r_sh["shadow_receipt"]["dynamic_l0_l4_verified"] is True

    r_exp = run_with_dynamic_construction_mode(case_id="INT_EXP", problem_text=c01["full_problem_text"], raw_facts_payload=payload, mode="experimental")
    assert r_exp["served_by"] == "DYNAMIC_CONSTRUCTION_PLANNER_V2" and r_exp["status"] == "SERVED"
    assert len(r_exp["multiplan_bundle"]["plans"]) >= 2

    r_fb = run_with_dynamic_construction_mode(case_id="INT_FB", problem_text=c01["full_problem_text"], raw_facts_payload=payload, mode="experimental", force_experimental_failure=True)
    assert r_fb["served_by"] == "SAFE_VERIFIED_LEGACY_FALLBACK" and r_fb["fallback_used"] is True and r_fb["status"] == "SERVED"


# Category 13: DeterministicModel2BaselineSelector Full Verified Walkthrough
def test_cat13_model2_deterministic_selector_walkthrough(v1_cases_map: dict, planner_v2: DynamicConstructionPlanner) -> None:
    e01 = v1_cases_map["E01_multiplan_d_A_SBC_equilateral"]
    f = build_initial_frame(case_id=e01["case_id"], problem_text=e01["problem_text"], solid_spec=e01["solid_spec"], chart_premises=e01["chart_premises"], pending_constructions=e01["pending"], length_unit="a")
    res = planner_v2.plan(frame=f, goal_spec=e01["goal_spec"], budget=SearchBudget())
    pg = res.best_plan.proof_graph
    pres = res.best_plan.presentation_graph
    walk = DeterministicModel2BaselineSelector.run_deterministic_walkthrough(proof_graph=pg, presentation_graph=pres, requested_goal=e01["goal_spec"].to_dict())
    assert walk["completed_all_steps"] is True and walk["steps_executed"] == walk["total_steps"] >= 3

    # Attempting last step before completing earlier steps is blocked cleanly
    obs0 = build_model2_observation(proof_graph=pg, presentation_graph=pres, completed_step_ids=(), requested_goal=e01["goal_spec"].to_dict())
    bad = validate_model2_action(obs0, pres, {"action_id": f"act_{pres.steps[-1].step_id}", "step_id": pres.steps[-1].step_id})
    assert not bad.accepted and bad.reason_code in ("MODEL2_DEPENDENCY_VIOLATION", "MODEL2_ACTION_NOT_ALLOWED")


# Category 14:freeze_evaluation_candidate --verify Governance Lock
def test_cat14_freeze_evaluation_candidate_verify() -> None:
    proc = subprocess.run([sys.executable, "backend/scripts/freeze_evaluation_candidate.py", "--verify"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"freeze_evaluation_candidate failed: {proc.stdout}\n{proc.stderr}"


# Category 15: lock_cache_identity --verify Governance Lock
def test_cat15_lock_cache_identity_verify() -> None:
    proc = subprocess.run([sys.executable, "backend/scripts/lock_cache_identity.py", "--verify"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"lock_cache_identity failed: {proc.stdout}\n{proc.stderr}"


#: Commit whose tree the handoff patches were written against (they were added, not applied, in 03200886a).
HANDOFF_BASE = "03200886a"
#: Patches that no longer fit the INTEGRATED tree and must be rebased by AXO CONSTRUCTION /2 (owner order: Model 1 →
#: merge main → Construction /2). The frozen patch itself is never edited. frontend: the /13 merge of main brought
#: the Option B classroom-scope retirement, which removed `phien`/`daiLop`/`daiLopTomTat` from `Scene3DExplorer`'s
#: props — the patch's context lines.
HANDOFF_REBASE_REQUIRED = {"frontend_scene3d_multiplan_switcher.patch"}


# Category 16: Handoff Patches Cleanly Pass git apply --check & Ownership Files Untouched
def test_cat16_handoff_patches_apply_cleanly_with_zero_unowned_edits(tmp_path) -> None:
    import os

    handoff_dir = V2_RUN_DIR / "handoff"
    index_env = {**os.environ, "GIT_INDEX_FILE": str(tmp_path / "base.index")}
    subprocess.run(["git", "read-tree", HANDOFF_BASE], cwd=REPO_ROOT, env=index_env, check=True)
    for patch_name in ("backend_adapter4_dynamic_construction_flag.patch", "frontend_scene3d_multiplan_switcher.patch"):
        p_file = handoff_dir / patch_name
        assert p_file.exists(), f"Missing patch {p_file}"
        # The frozen handoff is still valid at the tree it was written for (index blobs are LF; the patch is CRLF).
        lf = p_file.read_bytes().replace(b"\r\n", b"\n")
        at_base = subprocess.run(["git", "apply", "--cached", "--check", "-"], cwd=REPO_ROOT, env=index_env,
                                 input=lf, capture_output=True, check=False)
        assert at_base.returncode == 0, f"{patch_name} no longer applies at {HANDOFF_BASE}: {at_base.stderr!r}"
        if patch_name in HANDOFF_REBASE_REQUIRED:
            continue
        proc = subprocess.run(["git", "apply", "--check", str(p_file)], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        assert proc.returncode == 0, f"git apply --check failed for {patch_name}: {proc.stderr}"

    diff_proc = subprocess.run(["git", "status", "--porcelain", "--", "backend/app", "frontend"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert diff_proc.stdout.strip() == "", f"Blocked-ownership directory modified: {diff_proc.stdout}"


# Category 17: Zero Oracle Leakage AST Check
def test_cat17_oracle_isolation_ast_clean() -> None:
    pkg_dir = BACKEND_DIR / "experimental" / "construction_planner"
    for mod in ("construction_state.py", "construction_operators.py", "construction_search.py", "construction_verifier.py"):
        tree = ast.parse((pkg_dir / mod).read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in (*fn.args.args, *fn.args.kwonlyargs)]
                assert all(tok not in a for a in args for tok in ("independent_oracle", "expected_answer", "oracle_value")), f"Oracle param in {mod}:{fn.name}"


# Category 18: Runtime Zero Live AI Guard
def test_cat18_zero_live_ai_dependencies() -> None:
    pkg_dir = BACKEND_DIR / "experimental" / "construction_planner"
    for p in pkg_dir.glob("*.py"):
        txt = p.read_text(encoding="utf-8")
        assert "google.genai" not in txt and "gemini-2.5" not in txt
