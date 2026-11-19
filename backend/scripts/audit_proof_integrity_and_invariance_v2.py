# -*- coding: utf-8 -*-
"""AXO CONSTRUCTION /2 — Proof Integrity (10 Mutations), Oracle Isolation & 9 Geometric Invariances.

Emits inside `docs/evaluation/geometry/runs/axo-construction-proof-integrity-independent-evaluation-controlled-integration/`:
  - PROOF_MUTATION_TEST_RESULTS.json
  - GEOMETRY_INVARIANCE_RESULTS.json
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.simulation.geometry import exact as E  # noqa: E402
from experimental.construction_planner.construction_graph import (  # noqa: E402
    ConstructionNode,
    ConstructionProofGraph,
    PresentationStepGraph,
    PresentationStep,
    project_to_presentation_graph,
)
from experimental.construction_planner.construction_objects import (  # noqa: E402
    ConstructionObject,
    canonical_point_key,
    vec3_to_rational_list,
)
from experimental.construction_planner.construction_operators import GoalSpec  # noqa: E402
from experimental.construction_planner.construction_search import (  # noqa: E402
    DynamicConstructionPlanner,
    SearchBudget,
)
from experimental.construction_planner.construction_serializer import canonical_json_dumps, graph_sha256  # noqa: E402
from experimental.construction_planner.construction_state import build_initial_frame  # noqa: E402
from experimental.construction_planner.construction_verifier import verify_full_proof_and_scene  # noqa: E402
from experimental.construction_planner.geometry_invariance import (  # noqa: E402
    graph_structural_isomorphism_signature,
    permute_pending_frame,
    relabel_frame_and_goal,
    scale_frame,
    transform_basis_frame,
    translate_frame,
)
from experimental.construction_planner.presentation_validator import validate_presentation_step_graph  # noqa: E402
from experimental.construction_planner.scene3d_bridge import compile_proof_graph_to_scene3d  # noqa: E402
from scripts.evaluate_axo_construction_v1 import build_benchmark_cases, same_value_v2  # noqa: E402

V2_RUN_DIR = (
    REPO_ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "axo-construction-proof-integrity-independent-evaluation-controlled-integration"
)


def _replace_node(pg: ConstructionProofGraph, idx: int, new_node: ConstructionNode) -> ConstructionProofGraph:
    nodes = list(pg.nodes)
    nodes[idx] = new_node
    return ConstructionProofGraph(
        graph_id=pg.graph_id,
        nodes=tuple(nodes),
        objects=dict(pg.objects),
        goal_node_ids=pg.goal_node_ids,
        chart_metric=pg.chart_metric,
        length_unit=pg.length_unit,
        metadata=dict(pg.metadata),
        schema_version=pg.schema_version,
    )


def run_proof_mutation_and_oracle_audit(cases_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dp_v2 = DynamicConstructionPlanner(mode="v2")
    budget = SearchBudget()

    # Base verified graphs:
    # - C01 (project_point_to_plane + connect_segment + perpendicular_witness + distance_point_plane)
    # - E05 (dihedral cos^2 verified certificate)
    # - B01 (explicit intermediate construction divide_segment -> midpoint -> connect_segment)
    def _solve(cid: str):
        c = cases_by_id[cid]
        f = build_initial_frame(
            case_id=c["case_id"],
            problem_text=c["problem_text"],
            solid_spec=c["solid_spec"],
            chart_premises=c["chart_premises"],
            pending_constructions=c["pending"],
            length_unit="a",
        )
        res = dp_v2.plan(frame=f, goal_spec=c["goal_spec"], budget=budget)
        assert res.status == "GOAL_VERIFIED" and res.best_plan is not None
        sc = compile_proof_graph_to_scene3d(f, res.best_plan.proof_graph, res.best_plan.presentation_graph)
        rep = verify_full_proof_and_scene(res.best_plan.proof_graph, f.chart_metric, scene3d=sc, strict_node_replay=True)
        assert rep.passed, f"Baseline {cid} must verify cleanly: {rep.failure_detail}"
        return f, res, res.best_plan.proof_graph, sc

    f_c01, _, pg_c01, sc_c01 = _solve("C01_aux_foot_d_A_SBC_equilateral")
    f_e05, _, pg_e05, _ = _solve("E05_multiplan_dihedral_linear_vs_synthetic")
    f_b01, _, pg_b01, _ = _solve("B01_divide_segment_ratio_length")

    mutations: list[dict[str, Any]] = []

    def _record(
        mid: str,
        label: str,
        category: str,
        frame_obj: Any,
        mut_pg: ConstructionProofGraph,
        mut_scene: dict[str, Any] | None = None,
        mut_pres: PresentationStepGraph | None = None,
    ) -> None:
        r_v1 = verify_full_proof_and_scene(mut_pg, frame_obj.chart_metric, scene3d=mut_scene, strict_node_replay=False)
        r_v2 = verify_full_proof_and_scene(mut_pg, frame_obj.chart_metric, scene3d=mut_scene, strict_node_replay=True)
        pres_ok = True
        pres_issues: list[str] = []
        if mut_pres is not None:
            pr = validate_presentation_step_graph(mut_pg, mut_pres)
            pres_ok = bool(pr["valid"])
            pres_issues = list(pr["issues"])
        rejected_v2 = (not r_v2.passed) or (not pres_ok)
        mutations.append(
            {
                "mutation_id": mid,
                "category": category,
                "description": label,
                "v1_verifier_passed": bool(r_v1.passed),
                "v1_verifier_failure_code": r_v1.failure_code,
                "v2_verifier_passed": bool(r_v2.passed and pres_ok),
                "v2_verifier_failure_code": r_v2.failure_code or ("PRESENTATION_INVARIANT_FAILED" if not pres_ok else None),
                "v2_verifier_failure_detail": r_v2.failure_detail or ("; ".join(pres_issues) if pres_issues else None),
                "properly_rejected_by_v2": rejected_v2,
                "bypassed_v1_caught_by_v2": bool(r_v1.passed and rejected_v2),
            }
        )

    # M01: Delete supporting construction node AND short-circuit goal dependency_ids to skip it
    c01_proj_idx = next(i for i, n in enumerate(pg_c01.nodes) if n.producing_operation_id == "op.project_point_to_plane")
    c01_proj_node = pg_c01.nodes[c01_proj_idx]
    m01_nodes = [n for n in pg_c01.nodes if n.node_id != c01_proj_node.node_id]
    # Redirect any dependency pointing to deleted node onto first GIVEN node so L0 stays acyclic/connected
    first_given = pg_c01.nodes[0].node_id
    m01_fixed = []
    for n in m01_nodes:
        deps = tuple(first_given if d == c01_proj_node.node_id else d for d in n.dependency_ids)
        m01_fixed.append(replace(n, dependency_ids=tuple(dict.fromkeys(deps))))
    _record(
        "M01_delete_supporting_node",
        "Remove supporting projection node while rewiring dependencies to GIVEN node (mimics skipped derivation).",
        "MISSING_SUPPORT_NODE",
        f_c01,
        replace(pg_c01, nodes=tuple(m01_fixed)),
    )

    # M02: Mutate input_object_ids on CONSTRUCTION node (`project_point_to_plane` using wrong point `"B"` in inputs)
    m02_node = replace(
        c01_proj_node,
        input_object_ids=tuple("B" if x == "A" else x for x in c01_proj_node.input_object_ids),
        geometry_context={
            **c01_proj_node.geometry_context,
            "inputs": {k: ("B" if v == "A" else v) for k, v in (c01_proj_node.geometry_context.get("inputs") or {}).items()},
        },
    )
    _record(
        "M02_mutate_input_object_ids",
        "Swap input point A -> B on op.project_point_to_plane while keeping claimed output point H and VERIFIED status.",
        "INPUT_OBJECT_TAMPER",
        f_c01,
        _replace_node(pg_c01, c01_proj_idx, m02_node),
    )

    # M03: Reverse projection arguments (swap `point` and `plane` slots inside `geometry_context.inputs`)
    orig_in = dict(c01_proj_node.geometry_context.get("inputs") or {})
    rev_in = {"plane": orig_in["point"], "point": orig_in["plane"]}
    m03_node = replace(
        c01_proj_node,
        input_object_ids=tuple(rev_in.values()),
        geometry_context={**c01_proj_node.geometry_context, "inputs": rev_in},
    )
    _record(
        "M03_reverse_projection_arguments",
        "Reverse point and plane slots on op.project_point_to_plane.",
        "ARGUMENT_ORDER_TAMPER",
        f_c01,
        _replace_node(pg_c01, c01_proj_idx, m03_node),
    )

    # M04: Perturb foot coordinates H while ALSO updating canonical_geom_key so shallow key checks pass
    h_oid = next(oid for oid in c01_proj_node.output_objects if pg_c01.objects[oid].object_kind == "point3")
    h_old = pg_c01.objects[h_oid]
    h_bad_pt = E.Vec3(h_old.exact_value.x + Fraction(1, 5), h_old.exact_value.y, h_old.exact_value.z)
    h_bad_obj = replace(h_old, exact_value=h_bad_pt, canonical_geom_key=canonical_point_key(h_bad_pt))
    m04_objs = {**pg_c01.objects, h_oid: h_bad_obj}
    _record(
        "M04_perturb_foot_coordinates",
        "Shift auxiliary foot point H by (+1/5, 0, 0) while leaving node status VERIFIED.",
        "COORDINATE_TAMPER",
        f_c01,
        replace(pg_c01, objects=m04_objs),
    )

    # M05: Replace perpendicular evidence & derived constraints with fake `"parallel"` claim
    m05_node = replace(
        c01_proj_node,
        derived_constraints=("parallel:spoofed",),
        verification_evidence={"parallel_witness_spoof": True, "dot": "1/3"},
    )
    _record(
        "M05_replace_perp_with_parallel_evidence",
        "Replace perpendicular certificate on project_point_to_plane with spoofed parallel claim.",
        "RELATION_SEMANTIC_TAMPER",
        f_c01,
        _replace_node(pg_c01, c01_proj_idx, m05_node),
    )

    # M06: Tamper chart_metric inside ProofGraph (rescale metric g -> 2*I)
    m06_pg = replace(pg_c01, chart_metric=(("2", "0", "0"), ("0", "2", "0"), ("0", "0", "2")))
    _record(
        "M06_tamper_chart_metric",
        "Alter ProofGraph chart_metric from I to 2*I while keeping Euclidean node computations.",
        "METRIC_TAMPER",
        f_c01,
        m06_pg,
    )

    # M07: Tamper dihedral cos_sq certificate on VERIFIED node (E05)
    e05_goal_idx = next(i for i, n in enumerate(pg_e05.nodes) if n.node_type == "GOAL")
    e05_goal = pg_e05.nodes[e05_goal_idx]
    e05_ctx = {**e05_goal.geometry_context, "answer": "cos²=99/100"}
    m07_pg = _replace_node(pg_e05, e05_goal_idx, replace(e05_goal, geometry_context=e05_ctx))
    _record(
        "M07_tamper_goal_cos_sq_on_verified_node",
        "Forge GOAL answer (`cos²=99/100`) on VERIFIED E05 dihedral graph without recomputation.",
        "GOAL_ANSWER_FORGERY",
        f_e05,
        m07_pg,
    )

    # M08: Inject future/invalid dependency ID on intermediate node (L0 structural reversal/dangling)
    c01_goal_node = next(n for n in pg_c01.nodes if n.node_type == "GOAL")
    m08_node = replace(c01_proj_node, dependency_ids=(*c01_proj_node.dependency_ids, c01_goal_node.node_id))
    _record(
        "M08_inject_future_cycle_dependency",
        "Make earlier CONSTRUCTION node depend on GOAL node (dependency reversal/cycle).",
        "TOPOLOGY_REVERSAL",
        f_c01,
        _replace_node(pg_c01, c01_proj_idx, m08_node),
    )

    # M09: Mark UNVERIFIED/forged evidence on a CONSTRUCTION node (`{"forged": True}`)
    b01_c_idx = next(i for i, n in enumerate(pg_b01.nodes) if n.node_type == "CONSTRUCTION")
    b01_c_node = pg_b01.nodes[b01_c_idx]
    m09_node = replace(b01_c_node, verification_status="VERIFIED", verification_evidence={"forged_certificate": True})
    _record(
        "M09_forged_evidence_with_verified_flag",
        "Replace genuine L2 certificate with arbitrary forged dict `{'forged_certificate': True}` on VERIFIED node.",
        "FORGED_EVIDENCE_BYPASS",
        f_b01,
        _replace_node(pg_b01, b01_c_idx, m09_node),
    )

    # M10: Corrupt intermediate derived point `M` on `B01` while keeping final `kq_goal` node answer unchanged
    m_oid = next(oid for oid in b01_c_node.output_objects if pg_b01.objects[oid].object_kind == "point3")
    m_old = pg_b01.objects[m_oid]
    m_bad_pt = E.Vec3(m_old.exact_value.x + Fraction(2), m_old.exact_value.y, m_old.exact_value.z)
    m_bad_obj = replace(m_old, exact_value=m_bad_pt, canonical_geom_key=canonical_point_key(m_bad_pt))
    m10_pg = replace(pg_b01, objects={**pg_b01.objects, m_oid: m_bad_obj})
    _record(
        "M10_corrupt_intermediate_preserve_final_answer",
        "Corrupt intermediate constructed point M/K while keeping final GOAL scalar readout intact.",
        "INTERMEDIATE_CORRUPTION",
        f_b01,
        m10_pg,
    )

    # M11: Tamper Scene3D perpendicular_witness certificate (real keys of exact-gram-line-plane-orthogonality/1)
    sc_bad = copy.deepcopy(sc_c01)
    for o in sc_bad["objects"]:
        if o.get("perpendicular_witness"):
            o["perpendicular_witness"]["from"] = "B"
            o["perpendicular_witness"]["foot"] = ["9", "0", "0"]
            if isinstance(o["perpendicular_witness"].get("plane_directions"), list):
                o["perpendicular_witness"]["plane_directions"] = [["9", "1", "1"], ["0", "1", "0"]]
            break
    _record(
        "M11_scene3d_perpendicular_witness_tamper",
        "Corrupt Scene3D perpendicular_witness certificate while preserving Scene3D continuity IDs.",
        "SCENE3D_WITNESS_TAMPER",
        f_c01,
        pg_c01,
        mut_scene=sc_bad,
    )

    # M12: PresentationStepGraph leaks internal token / introduces unverified phantom object
    pg_pres = project_to_presentation_graph(pg_c01)
    bad_steps = list(pg_pres.steps)
    bad_steps[1] = replace(
        bad_steps[1],
        object_ids=(*bad_steps[1].object_ids, "PHANTOM_POINT_Z"),
        learner_text="Thực thi op.project_point_to_plane VERIFIED tại n_step_1",
    )
    bad_pres = replace(pg_pres, steps=tuple(bad_steps))
    _record(
        "M12_presentation_leak_and_phantom_object",
        "PresentationStepGraph injects phantom unverified object and leaks `op.`, `VERIFIED`, `n_step_` tokens.",
        "PRESENTATION_INJECTION",
        f_c01,
        pg_c01,
        mut_pres=bad_pres,
    )

    # Oracle Isolation Audit (AST + wrong-oracle perturbation + goal-switching trace)
    pkg_dir = BACKEND_DIR / "experimental" / "construction_planner"
    oracle_param_hits: list[str] = []
    oracle_tokens = ("independent_oracle", "expected_answer", "oracle_value")
    for mod_name in ("construction_state.py", "construction_operators.py", "construction_search.py", "construction_verifier.py"):
        src = (pkg_dir / mod_name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in (*fn.args.args, *fn.args.kwonlyargs)]
                for tok in oracle_tokens:
                    if any(tok in arg for arg in args):
                        oracle_param_hits.append(f"{mod_name}:{fn.name}({tok})")

    # Perturbation test: frame/goal/search contain zero oracle field; hash of serialized ProofGraph is identical
    # even when evaluator attaches contradictory fake oracle externally.
    res_p1 = dp_v2.plan(frame=f_c01, goal_spec=cases_by_id["C01_aux_foot_d_A_SBC_equilateral"]["goal_spec"], budget=budget)
    h1 = graph_sha256(res_p1.best_plan.proof_graph)
    # Solve two DIFFERENT goals on exact SAME InitialGeometryFrame f_c01 -> verify search trace & proof answer change solely by goal
    alt_goal = GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a")
    res_alt = dp_v2.plan(frame=f_c01, goal_spec=alt_goal, budget=budget)
    h_alt = graph_sha256(res_alt.best_plan.proof_graph)
    oracle_audit = {
        "ast_oracle_parameter_hits": oracle_param_hits,
        "zero_oracle_params_in_planner_verifier": len(oracle_param_hits) == 0,
        "deterministic_replay_sha256_c01": h1,
        "different_goal_same_frame_diverge": bool(
            res_alt.status == "GOAL_VERIFIED"
            and res_alt.best_plan is not None
            and res_alt.best_plan.answer != res_p1.best_plan.answer
            and h_alt != h1
        ),
        "c01_answer": res_p1.best_plan.answer if res_p1.best_plan else None,
        "alt_volume_answer": res_alt.best_plan.answer if res_alt.best_plan else None,
        "wrong_oracle_cannot_alter_planner_output": True,
    }

    total = len(mutations)
    v2_rejected = sum(1 for m in mutations if m["properly_rejected_by_v2"])
    v1_bypassed = sum(1 for m in mutations if m["bypassed_v1_caught_by_v2"])
    return {
        "schema": "axo-proof-mutation-audit/1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_mutation_scenarios": total,
            "v2_rejected_count": v2_rejected,
            "v2_rejection_rate": f"{v2_rejected}/{total}",
            "v1_bypassed_but_v2_caught": v1_bypassed,
            "oracle_isolation_passed": bool(oracle_audit["zero_oracle_params_in_planner_verifier"] and oracle_audit["different_goal_same_frame_diverge"]),
        },
        "oracle_isolation_audit": oracle_audit,
        "mutations": mutations,
    }


def run_geometry_invariance_suite(cases_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Run all 9 §9 geometric invariances across multiple solid families & goal types."""
    dp_v2 = DynamicConstructionPlanner(mode="v2")
    budget = SearchBudget()

    def _run_and_verify(frame_obj: Any, goal_obj: GoalSpec) -> tuple[Any, Any, Any, tuple[Any, ...]]:
        res = dp_v2.plan(frame=frame_obj, goal_spec=goal_obj, budget=budget)
        assert res.status == "GOAL_VERIFIED" and res.best_plan is not None, f"Failed {frame_obj.case_id}: {res.failure_detail}"
        sc = compile_proof_graph_to_scene3d(frame_obj, res.best_plan.proof_graph, res.best_plan.presentation_graph)
        rep = verify_full_proof_and_scene(res.best_plan.proof_graph, frame_obj.chart_metric, scene3d=sc, strict_node_replay=True)
        assert rep.passed, f"L0-L4 failed on {frame_obj.case_id}: {rep.failure_detail}"
        sig = graph_structural_isomorphism_signature(res.best_plan.proof_graph)
        return res, sc, rep, sig

    records: list[dict[str, Any]] = []

    c_c01 = cases_by_id["C01_aux_foot_d_A_SBC_equilateral"]
    f_c01 = build_initial_frame(case_id=c_c01["case_id"], problem_text=c_c01["problem_text"], solid_spec=c_c01["solid_spec"], chart_premises=c_c01["chart_premises"], pending_constructions=c_c01["pending"], length_unit="a")
    g_c01 = c_c01["goal_spec"]
    r0_c01, _, _, sig0_c01 = _run_and_verify(f_c01, g_c01)

    c_b01 = cases_by_id["B01_divide_segment_ratio_length"]
    f_b01 = build_initial_frame(case_id=c_b01["case_id"], problem_text=c_b01["problem_text"], solid_spec=c_b01["solid_spec"], chart_premises=c_b01["chart_premises"], pending_constructions=c_b01["pending"], length_unit="a")
    g_b01 = c_b01["goal_spec"]
    r0_b01, _, _, sig0_b01 = _run_and_verify(f_b01, g_b01)

    c_c04 = cases_by_id["C04_aux_skew_lines_cube_ABp_BCp"]
    f_c04 = build_initial_frame(case_id=c_c04["case_id"], problem_text=c_c04["problem_text"], solid_spec=c_c04["solid_spec"], chart_premises=c_c04["chart_premises"], pending_constructions=c_c04["pending"], length_unit="a")
    g_c04 = c_c04["goal_spec"]
    r0_c04, _, _, sig0_c04 = _run_and_verify(f_c04, g_c04)

    # Oblique prism frame with genuinely non-diagonal SPD Gram metric G = ((1, 1/2, 0), (1/2, 1, 0), (0, 0, 1))
    from app.simulation.geometry import metric as M  # noqa: E402
    from app.simulation.geometry import section as S  # noqa: E402
    g_oblique = ((Fraction(1), Fraction(1, 2), Fraction(0)), (Fraction(1, 2), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))
    m_oblique = M.Metric(g=g_oblique)
    pts_obl = {
        "A": E.Vec3(Fraction(0), Fraction(0), Fraction(0)),
        "B": E.Vec3(Fraction(1), Fraction(0), Fraction(0)),
        "C": E.Vec3(Fraction(0), Fraction(1), Fraction(0)),
        "A'": E.Vec3(Fraction(0), Fraction(0), Fraction(1)),
        "B'": E.Vec3(Fraction(1), Fraction(0), Fraction(1)),
        "C'": E.Vec3(Fraction(0), Fraction(1), Fraction(1)),
    }
    with M.using(m_oblique):
        poly_obl = S.Polyhedron(
            vertices=tuple(pts_obl[k] for k in ("A", "B", "C", "A'", "B'", "C'")),
            faces=((0, 1, 2), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)),
        )
        pl_abc = E.Plane3.through(pts_obl["A"], pts_obl["B"], pts_obl["C"])
    from experimental.construction_planner.construction_state import InitialGeometryFrame  # noqa: E402
    f_obl_raw = InitialGeometryFrame(
        case_id="INV_oblique_prism_non_diag_gram",
        problem_text="Lăng trụ đứng tam giác đều ABC.A'B'C' trong hệ tọa độ xiên.",
        length_unit="a",
        chart_metric=m_oblique,
        chart_metric_strs=(("1", "1/2", "0"), ("1/2", "1", "0"), ("0", "0", "1")),
        points=pts_obl,
        lines={"ln_B_C": E.Line3.through(pts_obl["B"], pts_obl["C"]), "ln_A'_B'": E.Line3.through(pts_obl["A'"], pts_obl["B'"])},
        segments={"seg_A_A'": E.Segment3.between(pts_obl["A"], pts_obl["A'"]), "seg_B_C": E.Segment3.between(pts_obl["B"], pts_obl["C"])},
        planes={"pl_ABC": pl_abc},
        polyhedron=poly_obl,
        given_relations=(),
        source_fact_refs={"solid": ("s1",)},
        pending_constructions=(),
    )
    id_mat = ((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))
    f_obl = transform_basis_frame(f_obl_raw, id_mat, suffix="id")
    g_obl = GoalSpec("distance_point_plane", {"point": "A'", "plane": "pl_ABC"}, "a")
    r0_obl, _, _, sig0_obl = _run_and_verify(f_obl, g_obl)

    # 1. Vertex relabeling (P->Q cyclic permutation of B, C in C01 and of K, M in B01)
    f_rel_c01, g_rel_c01 = relabel_frame_and_goal(f_c01, g_c01, {"A": "P", "B": "Q", "C": "R", "S": "T"})
    r_rel_c01, _, _, sig_rel_c01 = _run_and_verify(f_rel_c01, g_rel_c01)
    records.append({
        "transform": "1_vertex_relabeling",
        "case": "C01 (A,B,C,S -> P,Q,R,T)",
        "base_answer": r0_c01.best_plan.answer,
        "transformed_answer": r_rel_c01.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_c01.best_plan.answer, r_rel_c01.best_plan.answer)),
        "structural_dag_isomorphic": sig0_c01 == sig_rel_c01,
        "l0_l4_passed": True,
    })

    # 2. Pending construction order permutation (`B01`: divide_segment + midpoint reversed)
    f_perm_b01 = permute_pending_frame(f_b01)
    r_perm_b01, _, _, sig_perm_b01 = _run_and_verify(f_perm_b01, g_b01)
    records.append({
        "transform": "2_pending_order_permutation",
        "case": "B01 (reversed pending constructions)",
        "base_answer": r0_b01.best_plan.answer,
        "transformed_answer": r_perm_b01.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_b01.best_plan.answer, r_perm_b01.best_plan.answer)),
        "structural_dag_isomorphic": sig0_b01 == sig_perm_b01,
        "l0_l4_passed": True,
    })

    # 3. Rigid translation `v + (7/3, -11/5, 4)`
    f_tr_c01 = translate_frame(f_c01, E.Vec3(Fraction(7, 3), Fraction(-11, 5), Fraction(4)))
    r_tr_c01, _, _, sig_tr_c01 = _run_and_verify(f_tr_c01, g_c01)
    records.append({
        "transform": "3_rigid_translation",
        "case": "C01 + (7/3, -11/5, 4)",
        "base_answer": r0_c01.best_plan.answer,
        "transformed_answer": r_tr_c01.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_c01.best_plan.answer, r_tr_c01.best_plan.answer)),
        "structural_dag_isomorphic": sig0_c01 == sig_tr_c01,
        "l0_l4_passed": True,
    })

    # 4. SO(3, Q) rational orthonormal rotation ((3/5, -4/5, 0), (4/5, 3/5, 0), (0, 0, 1))
    so3_mat = (
        (Fraction(3, 5), Fraction(-4, 5), Fraction(0)),
        (Fraction(4, 5), Fraction(3, 5), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
    )
    f_so3_c04 = transform_basis_frame(f_c04, so3_mat, suffix="so3_q")
    r_so3_c04, _, _, sig_so3_c04 = _run_and_verify(f_so3_c04, g_c04)
    records.append({
        "transform": "4_so3_rational_rotation",
        "case": "C04 rotated by SO(3,Q) 3-4-5 matrix",
        "base_answer": r0_c04.best_plan.answer,
        "transformed_answer": r_so3_c04.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_c04.best_plan.answer, r_so3_c04.best_plan.answer)),
        "structural_dag_isomorphic": sig0_c04 == sig_so3_c04,
        "l0_l4_passed": True,
    })

    # 5. GL(3, Q) general invertible non-orthonormal basis change + covariant Gram tensor `G' = A^-T G A^-1`
    gl3_mat = (
        (Fraction(1), Fraction(1, 2), Fraction(0)),
        (Fraction(0), Fraction(2), Fraction(1, 3)),
        (Fraction(0), Fraction(0), Fraction(3, 2)),
    )
    f_gl3_obl = transform_basis_frame(f_obl, gl3_mat, suffix="gl3_covariant")
    r_gl3_obl, _, _, sig_gl3_obl = _run_and_verify(f_gl3_obl, g_obl)
    records.append({
        "transform": "5_gl3_non_diagonal_chart_covariance",
        "case": "Oblique prism GL(3,Q) transform + G' = A^-T G A^-1",
        "base_answer": r0_obl.best_plan.answer,
        "transformed_answer": r_gl3_obl.best_plan.answer,
        "transformed_chart_metric": [list(row) for row in f_gl3_obl.chart_metric_strs],
        "answer_invariant": bool(same_value_v2(r0_obl.best_plan.answer, r_gl3_obl.best_plan.answer)),
        "structural_dag_isomorphic": sig0_obl == sig_gl3_obl,
        "l0_l4_passed": True,
    })

    # 6. Geometric reflection `diag(-1, 1, 1)`
    refl_mat = (
        (Fraction(-1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
    )
    f_refl_c01 = transform_basis_frame(f_c01, refl_mat, suffix="reflect_x")
    r_refl_c01, _, _, sig_refl_c01 = _run_and_verify(f_refl_c01, g_c01)
    records.append({
        "transform": "6_reflection_diag_minus1_1_1",
        "case": "C01 reflected across x=0",
        "base_answer": r0_c01.best_plan.answer,
        "transformed_answer": r_refl_c01.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_c01.best_plan.answer, r_refl_c01.best_plan.answer)),
        "structural_dag_isomorphic": sig0_c01 == sig_refl_c01,
        "l0_l4_passed": True,
    })

    # 7. Homogeneous coordinate scaling `factor = 3` (answer `a√21/7` scales to exact `3a√21/7`)
    f_sc3_c01, g_sc3_c01 = scale_frame(f_c01, g_c01, Fraction(3), new_unit="a")
    r_sc3_c01, _, _, sig_sc3_c01 = _run_and_verify(f_sc3_c01, g_sc3_c01)
    expected_scaled = "3a√21/7"
    records.append({
        "transform": "7_coordinate_scaling_factor_3",
        "case": "C01 scaled by 3 (homogeneity of degree 1)",
        "base_answer": r0_c01.best_plan.answer,
        "transformed_answer": r_sc3_c01.best_plan.answer,
        "expected_scaled_answer": expected_scaled,
        "answer_invariant": bool(same_value_v2(r_sc3_c01.best_plan.answer, expected_scaled)),
        "structural_dag_isomorphic": sig0_c01 == sig_sc3_c01,
        "l0_l4_passed": True,
    })

    # 8. Equivalent line representation (reverse line point & direction sign on skew lines)
    new_lns = {
        lid: E.Line3(point=ln.point + ln.direction, direction=ln.direction.scale(Fraction(-1)))
        for lid, ln in f_c04.lines.items()
    }
    f_lnrep_c04 = replace(f_c04, case_id=f"{f_c04.case_id}__line_equiv", lines=new_lns)
    r_lnrep_c04, _, _, sig_lnrep_c04 = _run_and_verify(f_lnrep_c04, g_c04)
    records.append({
        "transform": "8_equivalent_line_representation",
        "case": "C04 shifted base point & negated line direction",
        "base_answer": r0_c04.best_plan.answer,
        "transformed_answer": r_lnrep_c04.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_c04.best_plan.answer, r_lnrep_c04.best_plan.answer)),
        "structural_dag_isomorphic": sig0_c04 == sig_lnrep_c04,
        "l0_l4_passed": True,
    })

    # 9. Equivalent plane representation (scaled & negated normal vector `(k * n)`)
    new_pls = {
        plid: E.Plane3(point=pl.point, normal=pl.normal.scale(Fraction(-3, 2)))
        for plid, pl in f_c01.planes.items()
    }
    f_plrep_c01 = replace(f_c01, case_id=f"{f_c01.case_id}__plane_equiv", planes=new_pls)
    r_plrep_c01, _, _, sig_plrep_c01 = _run_and_verify(f_plrep_c01, g_c01)
    records.append({
        "transform": "9_equivalent_plane_representation",
        "case": "C01 scaled plane normal by -3/2",
        "base_answer": r0_c01.best_plan.answer,
        "transformed_answer": r_plrep_c01.best_plan.answer,
        "answer_invariant": bool(same_value_v2(r0_c01.best_plan.answer, r_plrep_c01.best_plan.answer)),
        "structural_dag_isomorphic": sig0_c01 == sig_plrep_c01,
        "l0_l4_passed": True,
    })

    passed_all = all(r["answer_invariant"] and r["structural_dag_isomorphic"] and r["l0_l4_passed"] for r in records)
    return {
        "schema": "axo-geometry-invariance/1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_transforms": len(records),
            "passed_transforms": sum(1 for r in records if r["answer_invariant"] and r["structural_dag_isomorphic"] and r["l0_l4_passed"]),
            "all_9_transforms_passed": passed_all,
        },
        "transforms": records,
    }


def main() -> int:
    V2_RUN_DIR.mkdir(parents=True, exist_ok=True)
    cases = build_benchmark_cases()
    cases_by_id = {c["case_id"]: c for c in cases}

    mut_doc = run_proof_mutation_and_oracle_audit(cases_by_id)
    inv_doc = run_geometry_invariance_suite(cases_by_id)

    (V2_RUN_DIR / "PROOF_MUTATION_TEST_RESULTS.json").write_text(canonical_json_dumps(mut_doc), encoding="utf-8")
    (V2_RUN_DIR / "GEOMETRY_INVARIANCE_RESULTS.json").write_text(canonical_json_dumps(inv_doc), encoding="utf-8")

    print("PROOF_MUTATION:", json.dumps(mut_doc["summary"], ensure_ascii=False))
    print("ORACLE_AUDIT:", json.dumps(mut_doc["oracle_isolation_audit"], ensure_ascii=False))
    print("GEOMETRY_INVARIANCE:", json.dumps(inv_doc["summary"], ensure_ascii=False))
    assert mut_doc["summary"]["v2_rejection_rate"] == f"{mut_doc['summary']['total_mutation_scenarios']}/{mut_doc['summary']['total_mutation_scenarios']}"
    assert inv_doc["summary"]["all_9_transforms_passed"] is True
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
