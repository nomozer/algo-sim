# -*- coding: utf-8 -*-
"""Comprehensive regression suite for AXO CONSTRUCTION /1 (`verified-construction-graph/1`,
`construction-operator/1`, `dynamic-construction-planner/1`, `scene3d_bridge`, `model2_interface`).

Covers all 17 test categories required by Phase K (§19). Runs strictly offline (`ALLOW_LIVE_AI=0`).
"""
from __future__ import annotations

import hashlib
import inspect
import os
import sys
from fractions import Fraction
from pathlib import Path

import pytest

os.environ.setdefault("ALLOW_LIVE_AI", "0")
os.environ.setdefault("GEMINI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = BACKEND_DIR / "scripts"
for p in (BACKEND_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.simulation.geometry import exact as E  # noqa: E402
from app.simulation.geometry import metric as M  # noqa: E402
from app.simulation.geometry_functions import certificates, construction_continuity, engine, planner  # noqa: E402
from evaluate_axo_construction_v1 import build_benchmark_cases  # noqa: E402
from experimental.construction_planner import VERIFIED_CONSTRUCTION_GRAPH_SCHEMA  # noqa: E402
from experimental.construction_planner.construction_graph import (  # noqa: E402
    ConstructionNode,
    ConstructionProofGraph,
    GraphValidationError,
    detect_duplicate_constructions,
    find_unused_nodes,
    project_to_presentation_graph,
    prune_to_goal_closure,
    topological_order,
    trace_dependencies,
    validate_construction_graph,
)
from experimental.construction_planner.construction_objects import (  # noqa: E402
    ConstructionObject,
    canonical_line_key,
    canonical_plane_key,
    canonical_point_key,
)
from experimental.construction_planner.construction_operators import (  # noqa: E402
    OPERATOR_SPECS,
    GoalSpec,
    evaluate_goal_if_witnessed,
    execute_operator,
)
from experimental.construction_planner.construction_search import DynamicConstructionPlanner, SearchBudget  # noqa: E402
from experimental.construction_planner.construction_serializer import (  # noqa: E402
    canonical_json_dumps,
    graph_sha256,
    presentation_sha256,
)
from experimental.construction_planner.construction_state import build_initial_frame  # noqa: E402
from experimental.construction_planner.construction_verifier import (  # noqa: E402
    VerificationError,
    verify_full_proof_and_scene,
)
from experimental.construction_planner.model2_interface import (  # noqa: E402
    build_model2_observation,
    validate_model2_action,
)
from experimental.construction_planner.scene3d_bridge import compile_proof_graph_to_scene3d  # noqa: E402


def _make_sample_equilateral_frame():
    txt = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC), SA = a."
    return build_initial_frame(
        case_id="unit_eq",
        problem_text=txt,
        solid_spec={"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"},
        chart_premises=[
            {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "quotes": ["đáy ABC là tam giác đều cạnh a"]},
            {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["đáy ABC là tam giác đều cạnh a"]},
            {"id": "p3", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "p4", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
        ],
    )


def _node(nid: str, ntype: str = "GIVEN", *, deps=(), in_objs=(), out_objs=(), status="VERIFIED", ev=None) -> ConstructionNode:
    return ConstructionNode(
        node_id=nid,
        node_type=ntype,  # type: ignore[arg-type]
        geometric_object_type="point3",
        object_refs=tuple(out_objs or in_objs),
        geometry_context={},
        source_fact_refs=("s1",) if ntype == "GIVEN" else (),
        producing_operation_id=None if ntype == "GIVEN" else "op.midpoint_segment",
        input_object_ids=tuple(in_objs),
        preconditions=("source_gate:verified",) if ntype == "GIVEN" else ("distinct_points",),
        derived_constraints=(),
        output_objects=tuple(out_objs),
        dependency_ids=tuple(deps),
        verification_status=status,  # type: ignore[arg-type]
        verification_evidence=ev if ev is not None else {"checked": True},
    )


# 1. Graph schema & object provenance tests
def test_1_graph_schema_and_provenance():
    p_a = ConstructionObject("A", "point3", "GIVEN_OBJECT", canonical_point_key(E.Vec3.of(0, 0, 0)), "A", E.Vec3.of(0, 0, 0), ("s1",), "nA")
    with pytest.raises(ValueError, match="AUXILIARY_CONSTRUCTION"):
        ConstructionObject("H", "point3", "AUXILIARY_CONSTRUCTION", canonical_point_key(E.Vec3.of(1, 0, 0)), "H", E.Vec3.of(1, 0, 0), ("s1",), "nH")
    g = ConstructionProofGraph(
        graph_id="g1",
        nodes=(_node("nA", "GIVEN", out_objs=("A",)), _node("nGoal", "GOAL", deps=("nA",), in_objs=("A",), out_objs=("A",))),
        objects={"A": p_a},
        goal_node_ids=("nGoal",),
        chart_metric=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
        length_unit="a",
    )
    assert g.schema_version == VERIFIED_CONSTRUCTION_GRAPH_SCHEMA
    d = g.to_dict()
    assert len(d["nodes"][0]) == 16
    assert validate_construction_graph(g).valid


# 2. Canonical geometric identity vs label identity + duplicate construction detection
def test_2_canonical_vs_label_identity_and_duplicates():
    l1 = E.Line3.through(E.Vec3.of(0, 0, 0), E.Vec3.of(1, 2, 3))
    l2 = E.Line3.through(E.Vec3.of(2, 4, 6), E.Vec3.of(-1, -2, -3))
    assert canonical_line_key(l1) == canonical_line_key(l2)

    pl1 = E.Plane3.through(E.Vec3.of(0, 0, 0), E.Vec3.of(1, 0, 0), E.Vec3.of(0, 1, 0))
    pl2 = E.Plane3.through(E.Vec3.of(2, 3, 0), E.Vec3.of(-1, 5, 0), E.Vec3.of(0, -4, 0))
    assert canonical_plane_key(pl1) == canonical_plane_key(pl2)

    pt = E.Vec3.of(1, 0, 0)
    k = canonical_point_key(pt)
    objs = {
        "M": ConstructionObject("M", "point3", "AUXILIARY_CONSTRUCTION", k, "M", pt, (), "c1"),
        "N": ConstructionObject("N", "point3", "AUXILIARY_CONSTRUCTION", k, "N", pt, (), "c2"),
    }
    g = ConstructionProofGraph(
        graph_id="dup",
        nodes=(
            _node("c1", "CONSTRUCTION", out_objs=("M",)),
            _node("c2", "CONSTRUCTION", out_objs=("N",)),
            _node("goal", "GOAL", deps=("c1",), in_objs=("M",), out_objs=("M",)),
        ),
        objects=objs,
        goal_node_ids=("goal",),
        chart_metric=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
        length_unit="a",
    )
    assert ("c1", "c2") in detect_duplicate_constructions(g)
    rep = validate_construction_graph(g, allow_duplicate_geometry=False)
    assert not rep.valid and "DUPLICATE_GEOMETRIC_CONSTRUCTION" in rep.failure_codes


# 3. DAG validation, unused node detection & dependency tracing
def test_3_dag_validation_unused_pruning_and_trace():
    pt_a = ConstructionObject("A", "point3", "GIVEN_OBJECT", canonical_point_key(E.Vec3.of(0, 0, 0)), "A", E.Vec3.of(0, 0, 0), ("s1",), "n1")
    pt_u = ConstructionObject("U", "point3", "AUXILIARY_CONSTRUCTION", canonical_point_key(E.Vec3.of(1, 1, 1)), "U", E.Vec3.of(1, 1, 1), (), "nUnused")
    g = ConstructionProofGraph(
        graph_id="prune_test",
        nodes=(
            _node("n1", "GIVEN", out_objs=("A",)),
            _node("nUnused", "CONSTRUCTION", deps=("n1",), in_objs=("A",), out_objs=("U",)),
            _node("nGoal", "GOAL", deps=("n1",), in_objs=("A",), out_objs=("A",)),
        ),
        objects={"A": pt_a, "U": pt_u},
        goal_node_ids=("nGoal",),
        chart_metric=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
        length_unit="a",
    )
    assert topological_order(g) == ("n1", "nUnused", "nGoal")
    assert trace_dependencies(g, ("nGoal",)) == ("n1", "nGoal")
    assert find_unused_nodes(g) == ("nUnused",)
    pruned = prune_to_goal_closure(g)
    assert set(pruned.objects.keys()) == {"A"}
    assert "nUnused" not in {n.node_id for n in pruned.nodes}


# 4. Operator L0 type validation
def test_4_operator_type_validation_L0():
    with pytest.raises(VerificationError) as exc:
        execute_operator("op.non_existent", {}, {}, None)
    assert exc.value.level == "L0" and exc.value.code == "UNSUPPORTED_OPERATOR"
    assert len(OPERATOR_SPECS) >= 20
    for oid, spec in OPERATOR_SPECS.items():
        meta = spec.to_metadata_dict()
        assert meta["operator_id"] == oid and len(meta) >= 12


# 5. Missing precondition (L1) tests
def test_5_missing_precondition_L1():
    frame = build_initial_frame(
        case_id="miss_h",
        problem_text="Cho hình chóp S.ABC có AB = a.",
        solid_spec={"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"},
        chart_premises=[{"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]}],
    )
    res = DynamicConstructionPlanner().plan(frame=frame, goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"))
    assert res.status == "MISSING_PRECONDITION" and res.plans == ()

    bad_graph = ConstructionProofGraph(
        graph_id="miss_dep",
        nodes=(_node("n2", "CONSTRUCTION", deps=("n_missing",)),),
        objects={},
        goal_node_ids=("n2",),
        chart_metric=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
        length_unit="a",
    )
    rep = validate_construction_graph(bad_graph)
    assert not rep.valid and "MISSING_PRECONDITION" in rep.failure_codes


# 6. Cyclic dependency detection
def test_6_cyclic_dependency_detection():
    pt = ConstructionObject("A", "point3", "GIVEN_OBJECT", canonical_point_key(E.Vec3.of(0, 0, 0)), "A", E.Vec3.of(0, 0, 0), ("s1",), "c1")
    g = ConstructionProofGraph(
        graph_id="cyc",
        nodes=(
            _node("c1", "CONSTRUCTION", deps=("c2",), out_objs=("A",)),
            _node("c2", "CONSTRUCTION", deps=("c1",), in_objs=("A",), out_objs=("A",)),
        ),
        objects={"A": pt},
        goal_node_ids=("c2",),
        chart_metric=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
        length_unit="a",
    )
    with pytest.raises(GraphValidationError) as exc:
        topological_order(g)
    assert exc.value.code == "CYCLIC_DEPENDENCY"
    assert "CYCLIC_DEPENDENCY" in validate_construction_graph(g).failure_codes


# 7. Contradictory constraints
def test_7_contradictory_constraints():
    frame = build_initial_frame(
        case_id="bad_tri",
        problem_text="Cho hình chóp S.ABC có AB = a, BC = a, AC = 5a, SA vuông góc với (ABC), SA = a.",
        solid_spec={"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"},
        chart_premises=[
            {"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
            {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["B", "C"], "value": "a", "quotes": ["BC = a"]},
            {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "C"], "value": "5a", "quotes": ["AC = 5a"]},
            {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "p5", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
        ],
    )
    assert frame.error_code == "CONTRADICTORY_CONSTRAINTS"
    res = DynamicConstructionPlanner().plan(frame=frame, goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"))
    assert res.status == "CONTRADICTORY_CONSTRAINTS"


# 8. Degenerate geometry checks
def test_8_degenerate_geometry_operators():
    p0 = E.Vec3.of(0, 0, 0)
    p1 = E.Vec3.of(1, 0, 0)
    p2 = E.Vec3.of(2, 0, 0)
    p_z = E.Vec3.of(0, 0, 1)
    with pytest.raises(VerificationError) as e1:
        execute_operator("op.connect_segment", {"a": p0, "b": p0}, {}, None)
    assert e1.value.code == "DEGENERATE_COINCIDENT_POINTS"

    with pytest.raises(VerificationError) as e2:
        execute_operator("op.plane_through_three_points", {"a": p0, "b": p1, "c": p2}, {}, None)
    assert e2.value.code == "DEGENERATE_COLLINEAR_POINTS"

    ln1 = E.Line3.through(p0, p1)
    ln2 = E.Line3.through(E.Vec3.of(0, 1, 0), E.Vec3.of(1, 1, 0))
    with pytest.raises(VerificationError) as e3:
        execute_operator("op.intersect_coplanar_lines", {"line1": ln1, "line2": ln2}, {}, None)
    assert e3.value.code == "DEGENERATE_PARALLEL_NO_INTERSECTION"

    with pytest.raises(VerificationError) as e4:
        execute_operator("op.common_perpendicular_skew_lines", {"line1": ln1, "line2": E.Line3.through(p0, E.Vec3.of(0, 1, 0))}, {}, None)
    assert e4.value.code == "DEGENERATE_NON_SKEW_LINES"

    pl_xy = E.Plane3.through(p0, p1, E.Vec3.of(0, 1, 0))
    with pytest.raises(VerificationError) as e5:
        execute_operator("op.deduce_line_perp_plane_two_lines", {"line": ln1, "planar_line1": ln1, "planar_line2": E.Line3.through(p0, E.Vec3.of(0, 1, 0)), "plane": pl_xy}, {}, None)
    assert e5.value.code == "IMPOSSIBLE_PERPENDICULARITY"

    with pytest.raises(VerificationError) as e6:
        execute_operator("op.intersect_line_plane", {"line": E.Line3.through(p_z, p_z + p1), "plane": pl_xy}, {}, None)
    assert e6.value.code == "DEGENERATE_PARALLEL_NO_INTERSECTION"


# 9 & 10. Search timeout and resource budget enforcement
def test_9_10_search_timeout_and_resource_budgets():
    frame = _make_sample_equilateral_frame()
    dp = DynamicConstructionPlanner()
    goal = GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a")

    res_timeout = dp.plan(frame=frame, goal_spec=goal, budget=SearchBudget(max_wall_clock_ms=0.0))
    assert res_timeout.status == "SEARCH_TIMEOUT" and res_timeout.telemetry["timeout_hit"] is True

    res_limit = dp.plan(frame=frame, goal_spec=goal, budget=SearchBudget(max_expanded_states=1))
    assert res_limit.status in ("SEARCH_RESOURCE_LIMIT", "NO_PLAN_FOUND_WITHIN_BUDGET")
    assert res_limit.telemetry["expanded_states"] <= 1


# 11. Dynamic composition (Case B) beyond Planner /26
def test_11_dynamic_composition_case_b():
    cases = {c["case_id"]: c for c in build_benchmark_cases()}
    for cid in ("B01_divide_segment_ratio_length", "B03_dihedral_linear_angle_equilateral", "B06_divide_segment_plus_point_plane_distance", "B09_deep_19step_chain_exceeds_32_ir_slots"):
        c = cases[cid]
        f = build_initial_frame(case_id=c["case_id"], problem_text=c["problem_text"], solid_spec=c["solid_spec"], chart_premises=c["chart_premises"], pending_constructions=c["pending"])
        res = DynamicConstructionPlanner().plan(frame=f, goal_spec=c["goal_spec"], budget=SearchBudget())
        assert res.status == "GOAL_VERIFIED"
        assert res.best_plan is not None and res.best_plan.verification_report.passed
        assert res.best_plan.answer == c["independent_oracle"]


# 12. Exact witness validation (refuses unwitnessed metrics; verifies oblique Gram orthogonality)
def test_12_exact_witness_required_and_oblique_gram():
    frame = _make_sample_equilateral_frame()
    from experimental.construction_planner.construction_state import make_initial_search_state

    init = make_initial_search_state(frame)
    pts = {k: v.exact_value for k, v in init.objects.items() if v.object_kind == "point3"}
    lns = {k: v.exact_value for k, v in init.objects.items() if v.object_kind == "line3"}
    pls = {k: v.exact_value for k, v in init.objects.items() if v.object_kind == "plane3"}
    segs = {k: v.exact_value for k, v in init.objects.items() if v.object_kind == "segment3"}
    goal = GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a")
    # Without constructing auxiliary foot H, evaluator refuses to bypass construction!
    assert evaluate_goal_if_witnessed(
        goal,
        points_by_id=pts,
        lines_by_id=lns,
        planes_by_id=pls,
        segments_by_id=segs,
        sections_by_id={},
        relations=set(init.relations),
        key_to_ids={k: list(v) for k, v in init.key_to_ids.items()},
        chart_metric=frame.chart_metric,
    ) is None


# 13. Oracle independence test
def test_13_oracle_independence():
    sig = inspect.signature(DynamicConstructionPlanner.plan)
    for forbidden in ("oracle", "expected", "answer", "target_value", "ground_truth"):
        assert forbidden not in sig.parameters
    frame = _make_sample_equilateral_frame()
    res = DynamicConstructionPlanner().plan(frame=frame, goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"))
    assert res.status == "GOAL_VERIFIED" and res.best_plan is not None
    assert res.best_plan.answer == "a√21/7"


# 14. Scene3D serialization & L4 continuity + tamper check
def test_14_scene3d_serialization_and_continuity():
    frame = _make_sample_equilateral_frame()
    res = DynamicConstructionPlanner().plan(frame=frame, goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"))
    bp = res.best_plan
    assert bp is not None
    scene = compile_proof_graph_to_scene3d(frame, bp.proof_graph, bp.presentation_graph)
    issues = construction_continuity.validate_construction_continuity(scene)
    assert issues == []
    full = verify_full_proof_and_scene(bp.proof_graph, frame.chart_metric, scene3d=scene)
    assert full.passed and full.levels["L4"].passed
    # Confirm perpendicular_witness passes tamper verification
    witness_segs = [o for o in scene["objects"] if o.get("type") == "segment3" and o.get("perpendicular_witness")]
    assert len(witness_segs) == 1
    pts_map = {o["id"]: [Fraction(v) for v in o["xyz"]] for o in scene["objects"] if o["type"] == "point3"}
    assert certificates.verify_perpendicular_witness(witness_segs[0]["perpendicular_witness"], pts_map, chart_metric=frame.chart_metric)


# 15. Deterministic reproducibility across independent invocations
def test_15_deterministic_reproducibility():
    frame = _make_sample_equilateral_frame()
    goal = GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a")
    r1 = DynamicConstructionPlanner().plan(frame=frame, goal_spec=goal)
    r2 = DynamicConstructionPlanner().plan(frame=frame, goal_spec=goal)
    assert len(r1.plans) == len(r2.plans) >= 2
    for p1, p2 in zip(r1.plans, r2.plans):
        assert graph_sha256(p1.proof_graph) == graph_sha256(p2.proof_graph)
        assert presentation_sha256(p1.presentation_graph) == presentation_sha256(p2.presentation_graph)
        assert p1.score_tuple == p2.score_tuple


# 16. Alternative valid plans (Group E) & substantive difference
def test_16_alternative_plans_and_ranking():
    cases = {c["case_id"]: c for c in build_benchmark_cases()}
    for cid in ("E01_multiplan_d_A_SBC_equilateral", "E03_multiplan_skew_d_SA_BC", "E05_multiplan_dihedral_linear_vs_synthetic"):
        c = cases[cid]
        f = build_initial_frame(case_id=c["case_id"], problem_text=c["problem_text"], solid_spec=c["solid_spec"], chart_premises=c["chart_premises"])
        res = DynamicConstructionPlanner().plan(frame=f, goal_spec=c["goal_spec"], budget=SearchBudget(max_plans=3))
        assert res.status == "GOAL_VERIFIED"
        assert len(res.plans) >= 2
        assert all(p.answer == c["independent_oracle"] for p in res.plans)
        # Substantively different operator lineages
        assert len({tuple(n.producing_operation_id for n in p.proof_graph.nodes if n.producing_operation_id) for p in res.plans}) >= 2
        # Deterministic monotonic score order
        scores = [p.score_tuple for p in res.plans]
        assert scores == sorted(scores)


# 17. Group A Parity with Planner /26 + Model 2 Zero-Trust Security Boundaries
def test_17_parity_and_model2_security_boundaries():
    cases = {c["case_id"]: c for c in build_benchmark_cases()}
    c = cases["A01_sb_length_right_pyramid"]
    f = build_initial_frame(case_id=c["case_id"], problem_text=c["problem_text"], solid_spec=c["solid_spec"], chart_premises=c["chart_premises"])
    dyn = DynamicConstructionPlanner().plan(frame=f, goal_spec=c["goal_spec"]).best_plan
    kh = planner.lap_ke_hoach({"schema": "typed-facts/2", "facts": c["baseline_tf2_facts"]}, c["full_problem_text"])
    kq = engine.dung_tu_loi_goi(c["full_problem_text"], {"calls": kh.calls, "goals": [g["call"] for g in kh.goals], "negated": []}, auxiliary=tuple(kh.auxiliary))
    assert dyn is not None and dyn.answer == kq.answers["q1"] == "a√2"

    # Model 2 readiness boundary checks (on synthetic E01 Plan #2 with >= 3 steps)
    f_eq = _make_sample_equilateral_frame()
    p_eq = DynamicConstructionPlanner().plan(frame=f_eq, goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a")).plans[1]
    obs = build_model2_observation(proof_graph=p_eq.proof_graph, presentation_graph=p_eq.presentation_graph, completed_step_ids=("pstep_0",), requested_goal={"goal_kind": "distance_point_plane"})
    assert validate_model2_action(obs, p_eq.presentation_graph, {"action_id": "reveal::pstep_6", "step_id": "pstep_6"}).reason_code == "MODEL2_DEPENDENCY_VIOLATION"
    assert validate_model2_action(obs, p_eq.presentation_graph, {"action_id": "reveal::pstep_1", "override_answer": "0"}).reason_code == "MODEL2_SECURITY_BOUNDARY_VIOLATION"
    assert validate_model2_action(obs, p_eq.presentation_graph, {"action_id": f"reveal::{obs.allowed_actions[0].step_id}"}).accepted is True
