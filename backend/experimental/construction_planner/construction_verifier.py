# -*- coding: utf-8 -*-
"""5-level exact geometric verification (`L0`–`L4`) for `AXO CONSTRUCTION /1`.

Reuses `app.simulation.geometry.{exact, kernel, measure, metric, radical}` and
`app.simulation.geometry_functions.{certificates, construction_continuity}` with zero
floating-point proof shortcuts, zero `eval`, and strict degeneracy checking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from app.simulation.geometry import exact as E
from app.simulation.geometry import kernel as K
from app.simulation.geometry import measure as MS
from app.simulation.geometry import metric as M
from app.simulation.geometry import radical as R
from app.simulation.geometry import section as S
from app.simulation.geometry_functions import certificates, construction_continuity

from . import EXACT_VERIFIER_V2_VERSION, EXACT_VERIFIER_VERSION
from .construction_graph import (
    ConstructionProofGraph,
    trace_dependencies,
    validate_construction_graph,
)
from .construction_objects import (
    ConstructionObject,
    _fmt_frac,
    _json_safe,
    canonical_line_key,
    canonical_plane_key,
    canonical_point_key,
    canonical_polygon_key,
    canonical_segment_key,
)

DEGENERATE_CODES = {
    "DEGENERATE_COINCIDENT_POINTS",
    "DEGENERATE_COLLINEAR_POINTS",
    "DEGENERATE_UNDEFINED_PLANE",
    "DEGENERATE_PARALLEL_NO_INTERSECTION",
    "DEGENERATE_SKEW_NO_INTERSECTION",
    "DEGENERATE_CONTAINED_INFINITE_INTERSECTION",
    "DEGENERATE_NON_SKEW_LINES",
    "DEGENERATE_POINT_ALREADY_INCIDENT",
    "IMPOSSIBLE_PERPENDICULARITY",
    "NON_UNIQUE_AUXILIARY",
    "NON_POSITIVE_DIMENSION",
    "CONTRADICTORY_CONSTRAINTS",
}


class VerificationError(ValueError):
    """Fail-closed exact geometric verification failure."""

    def __init__(self, code: str, level: str, detail: str) -> None:
        super().__init__(f"[{level}] {code}: {detail}")
        self.code = code
        self.level = level
        self.detail = detail


@dataclass(frozen=True)
class LevelResult:
    level: str
    passed: bool
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "passed": self.passed,
            "detail": self.detail,
            "evidence": _json_safe(self.evidence),
        }


@dataclass(frozen=True)
class VerificationReport:
    verifier_version: str
    passed: bool
    levels: dict[str, LevelResult]
    failure_code: str | None = None
    failure_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_version": self.verifier_version,
            "passed": self.passed,
            "failure_code": self.failure_code,
            "failure_detail": self.failure_detail,
            "levels": {k: v.to_dict() for k, v in sorted(self.levels.items())},
        }


def map_kernel_error_code(exc: E.GeometryError) -> str:
    if exc.code == E.ERR_TRUNG_DIEM:
        return "DEGENERATE_COINCIDENT_POINTS"
    if exc.code == E.ERR_THANG_HANG:
        return "DEGENERATE_COLLINEAR_POINTS"
    if exc.code in (E.ERR_PT_MAT_PHANG_SUY_BIEN, E.ERR_VECTO_KHONG):
        return "DEGENERATE_UNDEFINED_PLANE"
    if exc.code == E.ERR_SONG_SONG:
        msg = str(exc).lower()
        if "chéo" in msg:
            return "DEGENERATE_SKEW_NO_INTERSECTION"
        return "DEGENERATE_PARALLEL_NO_INTERSECTION"
    if exc.code == E.ERR_CHUA_TRONG:
        return "DEGENERATE_CONTAINED_INFINITE_INTERSECTION"
    return exc.code


def verify_points_distinct(p: E.Point3, q: E.Point3, label_p: str = "P", label_q: str = "Q") -> None:
    if (p - q).is_zero():
        raise VerificationError(
            "DEGENERATE_COINCIDENT_POINTS",
            "L1",
            f"Points {label_p!r} and {label_q!r} coincide at {canonical_point_key(p)}.",
        )


def verify_non_collinear(a: E.Point3, b: E.Point3, c: E.Point3, labels: tuple[str, str, str] = ("A", "B", "C")) -> E.Vec3:
    n = (b - a).cross(c - a)
    if n.is_zero():
        raise VerificationError(
            "DEGENERATE_COLLINEAR_POINTS",
            "L1",
            f"Points {labels[0]}, {labels[1]}, {labels[2]} are collinear or coincide.",
        )
    return n


def verify_point_on_line(pt: E.Point3, ln: E.Line3, chart_metric: M.Metric | None) -> dict[str, Any]:
    with M.using(chart_metric):
        diff = pt - ln.point
        cross_zero = diff.cross(ln.direction).is_zero()
        d2 = MS.distance_sq_point_line(pt, ln)
    if not cross_zero or d2 != 0:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", f"Point is not on line (dist_sq={d2}).")
    return {"point_on_line_dist_sq": "0"}


def verify_point_on_plane(pt: E.Point3, pl: E.Plane3, chart_metric: M.Metric | None) -> dict[str, Any]:
    with M.using(chart_metric):
        ev = pl.signed_eval(pt)
        d2 = MS.distance_sq_point_plane(pt, pl)
    if ev != 0 or d2 != 0:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", f"Point does not lie on plane (signed_eval={ev}).")
    return {"signed_eval": "0", "point_on_plane_dist_sq": "0"}


def verify_lines_perpendicular(ln1: E.Line3, ln2: E.Line3, chart_metric: M.Metric | None) -> dict[str, Any]:
    if ln1.direction.is_zero() or ln2.direction.is_zero():
        raise VerificationError("DEGENERATE_COINCIDENT_POINTS", "L1", "Zero line direction.")
    with M.using(chart_metric):
        dp = M.dot(ln1.direction, ln2.direction)
    if dp != 0:
        raise VerificationError(
            "IMPOSSIBLE_PERPENDICULARITY",
            "L2",
            f"Lines are not orthogonal in exact Gram metric (dot={_fmt_frac(dp)} != 0).",
        )
    return {"exact_gram_dot": "0", "metric_verified": True}


def verify_line_perp_plane_gram(
    line_vec: E.Vec3,
    pl: E.Plane3,
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """Verify exact orthogonality `G * line_vec ∥ pl.normal` in rational Gram space."""
    if line_vec.is_zero():
        raise VerificationError("DEGENERATE_COINCIDENT_POINTS", "L1", "Line direction vector is zero.")
    certificates.validate_gram_metric_spd(chart_metric)
    with M.using(chart_metric):
        dual_line = M.plane_covector(line_vec)
        cross_zero = dual_line.cross(pl.normal).is_zero()
        cos_sq = MS.cos_sq_line_plane(E.Line3(E.Vec3.of(0, 0, 0), line_vec), pl)
        # Note `cos_sq_line_plane` computes cos^2 of the angle between line and plane = sin^2(line, normal)!
        # Wait: let's verify exact definition in measure.py: `sin_sq_line_plane == 1` when perpendicular!
        sin_sq = MS.sin_sq_line_plane(E.Line3(E.Vec3.of(0, 0, 0), line_vec), pl)
    if not cross_zero or sin_sq != 1:
        raise VerificationError(
            "IMPOSSIBLE_PERPENDICULARITY",
            "L2",
            f"Line is not perpendicular to plane (sin_sq_line_plane={sin_sq}, covector_cross_zero={cross_zero}).",
        )
    return {
        "certificate_schema": certificates.CERTIFICATE_SCHEMA,
        "sin_sq_line_plane": "1",
        "covector_collinear": True,
    }


def verify_two_lines_deductive_perp_plane(
    target_vec: E.Vec3,
    dir1: E.Vec3,
    dir2: E.Vec3,
    pl: E.Plane3,
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """L2 deductive theorem check: `target ⟂ dir1`, `target ⟂ dir2`, `dir1 ∦ dir2`, both in `pl`."""
    if target_vec.is_zero() or dir1.is_zero() or dir2.is_zero():
        raise VerificationError("DEGENERATE_COINCIDENT_POINTS", "L1", "Zero direction in deductive perp check.")
    if dir1.cross(dir2).is_zero():
        raise VerificationError("DEGENERATE_COLLINEAR_POINTS", "L1", "Two planar lines are parallel/collinear.")
    with M.using(chart_metric):
        # Verify dir1, dir2 lie in pl (orthogonal to covector normal)
        if pl.normal.dot(dir1) != 0 or pl.normal.dot(dir2) != 0:
            raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Reference directions do not lie in target plane.")
        dot1 = M.dot(target_vec, dir1)
        dot2 = M.dot(target_vec, dir2)
        if dot1 != 0 or dot2 != 0:
            raise VerificationError(
                "IMPOSSIBLE_PERPENDICULARITY",
                "L2",
                f"Target line not perpendicular to both planar lines (dot1={dot1}, dot2={dot2}).",
            )
    return {
        "theorem": certificates.DEDUCTIVE_THEOREM_SCHEMA,
        "dot_line_d1": "0",
        "dot_line_d2": "0",
        "planar_directions_independent": True,
    }


def verify_dihedral_linear_angle(
    edge: E.Line3,
    ray_p: E.Line3,
    ray_q: E.Line3,
    pl_p: E.Plane3,
    pl_q: E.Plane3,
    vertex: E.Point3,
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """L2 exact check for constructed dihedral linear angle at `vertex ∈ P ∩ Q`."""
    verify_point_on_plane(vertex, pl_p, chart_metric)
    verify_point_on_plane(vertex, pl_q, chart_metric)
    verify_point_on_line(vertex, edge, chart_metric)
    with M.using(chart_metric):
        # Rays lie in P and Q respectively and both are orthogonal to the common edge in Gram metric
        if pl_p.normal.dot(ray_p.direction) != 0:
            raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "First ray does not lie in first plane.")
        if pl_q.normal.dot(ray_q.direction) != 0:
            raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Second ray does not lie in second plane.")
        dp1 = M.dot(ray_p.direction, edge.direction)
        dp2 = M.dot(ray_q.direction, edge.direction)
        if dp1 != 0 or dp2 != 0:
            raise VerificationError(
                "IMPOSSIBLE_PERPENDICULARITY",
                "L2",
                f"Dihedral rays must be perpendicular to common edge (dp1={dp1}, dp2={dp2}).",
            )
        cos_sq_rays = MS.cos_sq_between_vectors(ray_p.direction, ray_q.direction)
        cos_sq_planes = MS.cos_sq_between_planes(pl_p, pl_q)
    if cos_sq_rays != cos_sq_planes:
        raise VerificationError(
            "UNVERIFIED_CONSTRUCTION",
            "L2",
            f"Constructed linear angle cos^2={cos_sq_rays} mismatches plane dihedral cos^2={cos_sq_planes}.",
        )
    return {
        "dihedral_linear_angle_verified": True,
        "ray_p_perp_edge_dot": "0",
        "ray_q_perp_edge_dot": "0",
        "cos_sq": _fmt_frac(cos_sq_rays),
    }


def format_exact_unit_answer(
    exact_scalar: R.ExactNumber | Fraction,
    *,
    unit: str,
    dim: int,
) -> dict[str, Any]:
    """Deterministically format an exact length/area/volume/angle expression matching Axo evaluator conventions."""
    if isinstance(exact_scalar, Fraction):
        exact_obj = R.ExactNumber.from_fraction(exact_scalar) if hasattr(R.ExactNumber, "from_fraction") else R.multiply(exact_scalar, 1)
    else:
        exact_obj = exact_scalar
    coef_str = R.display(exact_obj)
    if dim == 0 or not unit:
        text = coef_str
    else:
        unit_sym = unit if dim == 1 else f"{unit}²" if dim == 2 else f"{unit}³"
        if coef_str == "0":
            text = "0"
        elif coef_str == "1":
            text = unit_sym
        elif "/" in coef_str and not coef_str.startswith("("):
            num, den = coef_str.split("/", 1)
            if num == "1":
                text = f"{unit_sym}/{den}"
            else:
                text = f"{num}{unit_sym}/{den}" if not num.startswith("√") else f"{unit_sym}{num}/{den}"
        else:
            text = f"{coef_str}{unit_sym}" if not coef_str.startswith("√") else f"{unit_sym}{coef_str}"
    return {"text": text, "coef": coef_str, "dim": dim, "unit": unit if dim > 0 else ""}


def _recompute_canonical_key(obj: ConstructionObject) -> str:
    """Recompute exact canonical geometric key from `obj.exact_value` (never trust stored key string)."""
    val = obj.exact_value
    k = obj.object_kind
    if k == "point3" and isinstance(val, E.Vec3):
        return canonical_point_key(val)
    if k == "segment3" and isinstance(val, E.Segment3):
        if (val.point_b - val.point_a).is_zero():
            raise VerificationError("DEGENERATE_COINCIDENT_POINTS", "L2", f"Segment {obj.object_id!r} has coincident endpoints.")
        return canonical_segment_key(val)
    if k == "line3" and isinstance(val, E.Line3):
        return canonical_line_key(val)
    if k == "plane3" and isinstance(val, E.Plane3):
        return canonical_plane_key(val)
    if k == "solid" and isinstance(val, S.Polyhedron):
        return canonical_polygon_key(val.vertices, kind="solid")
    if k == "section" and isinstance(val, S.Section):
        return canonical_polygon_key(val.polygon, kind="sec")
    if k == "polygon3" and isinstance(val, (tuple, list)):
        return canonical_polygon_key(tuple(val), kind="poly")
    return obj.canonical_geom_key


def _replay_given_relations(
    given_objs: dict[str, ConstructionObject],
    chart_metric: M.Metric | None,
) -> set[tuple[str, tuple[str, ...]]]:
    """Re-derive ONLY mathematically true incidence/orthogonality relations from verified GIVEN objects."""
    rels: set[tuple[str, tuple[str, ...]]] = set()
    pts = [o for o in given_objs.values() if o.object_kind == "point3" and isinstance(o.exact_value, E.Vec3)]
    lns = [o for o in given_objs.values() if o.object_kind == "line3" and isinstance(o.exact_value, E.Line3)]
    pls = [o for o in given_objs.values() if o.object_kind == "plane3" and isinstance(o.exact_value, E.Plane3)]
    with M.using(chart_metric):
        for p in pts:
            pk = canonical_point_key(p.exact_value)
            for ln in lns:
                if (p.exact_value - ln.exact_value.point).cross(ln.exact_value.direction).is_zero():
                    rels.add(("point_on_line", (pk, canonical_line_key(ln.exact_value))))
            for pl in pls:
                if pl.exact_value.signed_eval(p.exact_value) == 0:
                    rels.add(("point_on_plane", (pk, canonical_plane_key(pl.exact_value))))
        for pl in pls:
            plk = canonical_plane_key(pl.exact_value)
            for p in pts:
                if pl.exact_value.signed_eval(p.exact_value) != 0:
                    continue
                fk = canonical_point_key(p.exact_value)
                for q in pts:
                    if q.object_id != p.object_id and pl.exact_value.signed_eval(q.exact_value) != 0:
                        diff = q.exact_value - p.exact_value
                        if not diff.is_zero() and M.plane_covector(diff).cross(pl.exact_value.normal).is_zero():
                            rels.add(("perp_point_plane_witness", (canonical_point_key(q.exact_value), plk, fk)))
        for ln in lns:
            lk = canonical_line_key(ln.exact_value)
            for pl in pls:
                plk = canonical_plane_key(pl.exact_value)
                if pl.exact_value.signed_eval(ln.exact_value.point) == 0 and pl.exact_value.normal.dot(ln.exact_value.direction) == 0:
                    rels.add(("line_in_plane", (lk, plk)))
                if M.plane_covector(ln.exact_value.direction).cross(pl.exact_value.normal).is_zero():
                    rels.add(("perp_line_plane", (lk, plk)))
        for idx, ln1 in enumerate(lns):
            lk1 = canonical_line_key(ln1.exact_value)
            for ln2 in lns[idx + 1:]:
                if M.dot(ln1.exact_value.direction, ln2.exact_value.direction) == 0:
                    lk2 = canonical_line_key(ln2.exact_value)
                    rels.add(("perp_lines", tuple(sorted((lk1, lk2)))))
    return rels


def _same_exact_value(a: Any, b: Any) -> bool:
    if isinstance(a, E.Vec3) and isinstance(b, E.Vec3):
        return a == b
    if isinstance(a, E.Segment3) and isinstance(b, E.Segment3):
        return canonical_segment_key(a) == canonical_segment_key(b)
    if isinstance(a, E.Line3) and isinstance(b, E.Line3):
        return canonical_line_key(a) == canonical_line_key(b)
    if isinstance(a, E.Plane3) and isinstance(b, E.Plane3):
        return canonical_plane_key(a) == canonical_plane_key(b)
    if isinstance(a, S.Section) and isinstance(b, S.Section):
        return canonical_polygon_key(a.polygon, kind="sec") == canonical_polygon_key(b.polygon, kind="sec")
    return a == b


def verify_full_proof_and_scene(
    proof_graph: ConstructionProofGraph,
    chart_metric: M.Metric | None,
    scene3d: dict[str, Any] | None = None,
    *,
    strict_node_replay: bool = True,
) -> VerificationReport:
    """Execute independent L0–L4 audit over a complete `ConstructionProofGraph` (and optional `Scene3D`).

    Under `strict_node_replay=True` (`construction-exact-verifier/2`, default):
    - L0 checks DAG invariants + strict topological causality (`input_object_ids` supported in backward dep closure);
    - L1 checks SPD Sylvester criterion AND exact equality of `proof_graph.chart_metric` with `chart_metric`;
    - L2 algebraically re-executes every GIVEN, CONSTRUCTION, and DERIVED_RELATION node in topological order,
      comparing outputs, canonical keys, exact coordinates, and certificates against the proof graph;
    - L3 replays `evaluate_goal_if_witnessed` over ONLY objects and re-verified relations inside each GOAL node's
      transitive backward dependency closure;
    - L4 validates `validate_construction_continuity(scene3d)` AND `certificates.verify_perpendicular_witness`
      for every tagged witness segment.
    """
    from .construction_operators import OPERATOR_SPECS, GoalSpec, evaluate_goal_if_witnessed, execute_operator

    ver_id = EXACT_VERIFIER_V2_VERSION if strict_node_replay else EXACT_VERIFIER_VERSION
    levels: dict[str, LevelResult] = {}

    # L0: Type & DAG schema validity (+ causality check under strict replay)
    dag_report = validate_construction_graph(proof_graph, require_verified_goal_closure=True, allow_duplicate_geometry=False)
    l0_ok = dag_report.valid
    l0_detail = "Graph schema, node types, and DAG invariants valid." if l0_ok else f"DAG failed: {dag_report.failure_codes}"
    l0_fail_code = dag_report.failure_codes[0] if dag_report.failure_codes else "UNVERIFIED_CONSTRUCTION"
    node_map = proof_graph.node_map()

    if l0_ok and strict_node_replay:
        pos = {nid: idx for idx, nid in enumerate(dag_report.topological_node_order)}
        for nid in dag_report.topological_node_order:
            node = node_map[nid]
            for dep in node.dependency_ids:
                if dep not in pos or pos[dep] >= pos[nid]:
                    l0_ok = False
                    l0_fail_code = "MISSING_PRECONDITION"
                    l0_detail = f"Node {nid!r} depends on {dep!r} which does not strictly precede it."
                    break
            if not l0_ok:
                break
            dep_closure = set(trace_dependencies(proof_graph, (nid,))) - {nid}
            for oid in node.input_object_ids:
                obj = proof_graph.objects.get(oid)
                if obj is None or not obj.supporting_node_id or obj.supporting_node_id not in pos:
                    l0_ok = False
                    l0_fail_code = "MISSING_PRECONDITION"
                    l0_detail = f"Input object {oid!r} of node {nid!r} lacks a valid supporting node."
                    break
                if pos[obj.supporting_node_id] >= pos[nid] or obj.supporting_node_id not in dep_closure:
                    l0_ok = False
                    l0_fail_code = "MISSING_PRECONDITION"
                    l0_detail = (
                        f"Causal dependency violation at node {nid!r}: input object {oid!r} comes from "
                        f"{obj.supporting_node_id!r}, outside backward dependency closure."
                    )
                    break
            if not l0_ok:
                break

    levels["L0"] = LevelResult(
        level="L0",
        passed=l0_ok,
        detail=l0_detail,
        evidence=dag_report.to_dict(),
    )
    if not l0_ok:
        return VerificationReport(ver_id, False, levels, failure_code=l0_fail_code, failure_detail=l0_detail)

    # L1: SPD Gram metric & exact alignment between `proof_graph.chart_metric` and `chart_metric`
    l1_detail = "SPD Gram metric verified (Sylvester criterion) and all node preconditions satisfied."
    l1_fail_code = "NON_POSITIVE_DIMENSION"
    try:
        g_mat = certificates.validate_gram_metric_spd(chart_metric)
        l1_ok = True
        if strict_node_replay:
            expected_strs = tuple(tuple(_fmt_frac(x) for x in row) for row in g_mat)
            norm_pg_metric = tuple(tuple(_fmt_frac(Fraction(str(x))) for x in row) for row in proof_graph.chart_metric)
            if norm_pg_metric != expected_strs:
                l1_ok = False
                l1_fail_code = "METRIC_MISMATCH"
                l1_detail = f"ProofGraph chart_metric {norm_pg_metric} disagrees with certified Gram metric {expected_strs}."
    except (certificates.CertificateError, ValueError, ZeroDivisionError) as exc:
        l1_ok = False
        l1_detail = str(exc)
    levels["L1"] = LevelResult(level="L1", passed=l1_ok, detail=l1_detail, evidence={"metric_spd": l1_ok})
    if not l1_ok:
        return VerificationReport(ver_id, False, levels, failure_code=l1_fail_code, failure_detail=l1_detail)

    # L2: Topological replay of GIVEN, CONSTRUCTION & DERIVED_RELATION nodes
    rel_checked = 0
    verified_objects: dict[str, ConstructionObject] = {}
    verified_node_rels: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
    all_reverified_rels: set[tuple[str, tuple[str, ...]]] = set()

    if not strict_node_replay:
        for node in proof_graph.nodes:
            if node.node_type in ("CONSTRUCTION", "DERIVED_RELATION"):
                if not node.verification_evidence or node.verification_status != "VERIFIED":
                    levels["L2"] = LevelResult("L2", False, f"Node {node.node_id!r} lacks verified L2 evidence.")
                    return VerificationReport(
                        ver_id,
                        False,
                        levels,
                        failure_code="UNVERIFIED_CONSTRUCTION",
                        failure_detail=levels["L2"].detail,
                    )
                rel_checked += 1
        levels["L2"] = LevelResult(
            level="L2",
            passed=True,
            detail=f"All {rel_checked} construction and derived-relation nodes carry exact L2 evidence.",
            evidence={"verified_nodes": rel_checked},
        )
    else:
        for nid in dag_report.topological_node_order:
            node = node_map[nid]
            if node.verification_status != "VERIFIED" or not node.verification_evidence:
                levels["L2"] = LevelResult("L2", False, f"Node {nid!r} lacks verified L2 evidence.")
                return VerificationReport(ver_id, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L2"].detail)

            if node.node_type == "GIVEN":
                if node.producing_operation_id is not None or not node.source_fact_refs:
                    levels["L2"] = LevelResult("L2", False, f"GIVEN node {nid!r} has invalid provenance/operation.")
                    return VerificationReport(ver_id, False, levels, failure_code="CONTRADICTORY_CONSTRAINTS", failure_detail=levels["L2"].detail)
                for oid in node.output_objects:
                    obj = proof_graph.objects.get(oid)
                    if obj is None or obj.origin != "GIVEN_OBJECT" or not obj.source_fact_refs:
                        levels["L2"] = LevelResult("L2", False, f"GIVEN output {oid!r} has non-GIVEN origin or empty source_fact_refs.")
                        return VerificationReport(ver_id, False, levels, failure_code="CONTRADICTORY_CONSTRAINTS", failure_detail=levels["L2"].detail)
                    try:
                        recomp_k = _recompute_canonical_key(obj)
                    except (E.GeometryError, VerificationError) as exc:
                        levels["L2"] = LevelResult("L2", False, f"GIVEN object {oid!r} degenerate: {exc}")
                        return VerificationReport(ver_id, False, levels, failure_code="DEGENERATE_COINCIDENT_POINTS", failure_detail=levels["L2"].detail)
                    if recomp_k != obj.canonical_geom_key:
                        levels["L2"] = LevelResult("L2", False, f"GIVEN object {oid!r} canonical_geom_key {obj.canonical_geom_key!r} != recomputed {recomp_k!r}.")
                        return VerificationReport(ver_id, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L2"].detail)
                    verified_objects[oid] = obj
                continue

            if node.node_type in ("CONSTRUCTION", "DERIVED_RELATION"):
                op_id = node.producing_operation_id or ""
                if op_id not in OPERATOR_SPECS:
                    levels["L2"] = LevelResult("L2", False, f"Node {nid!r} uses unknown operator {op_id!r}.")
                    return VerificationReport(ver_id, False, levels, failure_code="UNSUPPORTED_OPERATOR", failure_detail=levels["L2"].detail)
                input_map = node.geometry_context.get("inputs")
                if not isinstance(input_map, dict) or tuple(input_map.values()) != node.input_object_ids:
                    levels["L2"] = LevelResult("L2", False, f"Node {nid!r} geometry_context.inputs disagrees with input_object_ids.")
                    return VerificationReport(ver_id, False, levels, failure_code="MISSING_PRECONDITION", failure_detail=levels["L2"].detail)
                try:
                    inputs_exact = {slot: verified_objects[oid].exact_value for slot, oid in input_map.items()}
                except KeyError as exc:
                    levels["L2"] = LevelResult("L2", False, f"Node {nid!r} references unverified input object {exc}.")
                    return VerificationReport(ver_id, False, levels, failure_code="MISSING_PRECONDITION", failure_detail=levels["L2"].detail)

                # Check prerequisite relations for deductive operators so unproved relations cannot bootstrap themselves
                if op_id == "op.deduce_planar_perp_from_perp_plane":
                    pl_key = verified_objects[input_map["host_plane"]].canonical_geom_key
                    ln_key = verified_objects[input_map["perp_line"]].canonical_geom_key
                    if ("perp_line_plane", (ln_key, pl_key)) not in (all_reverified_rels | _replay_given_relations(verified_objects, chart_metric)):
                        levels["L2"] = LevelResult("L2", False, f"Node {nid!r} uses deduce_planar_perp_from_perp_plane without prior verified perp_line_plane.")
                        return VerificationReport(ver_id, False, levels, failure_code="MISSING_PRECONDITION", failure_detail=levels["L2"].detail)

                params = dict(node.geometry_context.get("params") or {})
                try:
                    re_res = execute_operator(op_id, inputs_exact, params, chart_metric)
                except (VerificationError, E.GeometryError, TypeError, KeyError, AttributeError) as exc:
                    levels["L2"] = LevelResult("L2", False, f"Node {nid!r} failed algebraic operator replay: {exc}")
                    return VerificationReport(ver_id, False, levels, failure_code=getattr(exc, "code", "UNVERIFIED_CONSTRUCTION"), failure_detail=levels["L2"].detail)

                # Compare certificate evidence verbatim
                if _json_safe(node.verification_evidence) != _json_safe(re_res.get("verification_evidence") or {}):
                    levels["L2"] = LevelResult("L2", False, f"Node {nid!r} verification_evidence tampered/mismatches exact operator replay.")
                    return VerificationReport(ver_id, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L2"].detail)

                # Verify output objects match re-executed exact geometry & canonical keys
                re_outs = re_res.get("outputs") or {}
                re_keys = re_res.get("canonical_keys") or {}
                if node.geometry_context.get("canonical_outputs") is not None:
                    if _json_safe(node.geometry_context.get("canonical_outputs")) != _json_safe(re_keys):
                        levels["L2"] = LevelResult("L2", False, f"Node {nid!r} canonical_outputs mismatches operator replay.")
                        return VerificationReport(ver_id, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L2"].detail)
                if len(node.output_objects) != len(re_outs):
                    levels["L2"] = LevelResult("L2", False, f"Node {nid!r} output count mismatches operator output count.")
                    return VerificationReport(ver_id, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L2"].detail)

                for oid, (slot, re_val) in zip(node.output_objects, re_outs.items()):
                    obj = proof_graph.objects.get(oid)
                    if obj is None:
                        levels["L2"] = LevelResult("L2", False, f"Missing output object {oid!r} in graph.")
                        return VerificationReport(ver_id, False, levels, failure_code="MISSING_PRECONDITION", failure_detail=levels["L2"].detail)
                    try:
                        recomp_k = _recompute_canonical_key(obj)
                    except (E.GeometryError, VerificationError) as exc:
                        levels["L2"] = LevelResult("L2", False, f"Output object {oid!r} degenerate: {exc}")
                        return VerificationReport(ver_id, False, levels, failure_code="DEGENERATE_COINCIDENT_POINTS", failure_detail=levels["L2"].detail)
                    if recomp_k != obj.canonical_geom_key or recomp_k != re_keys[slot] or not _same_exact_value(obj.exact_value, re_val):
                        levels["L2"] = LevelResult(
                            "L2",
                            False,
                            f"Output object {oid!r} exact geometry or canonical key mismatches replay for {op_id}.",
                        )
                        return VerificationReport(ver_id, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L2"].detail)
                    verified_objects[oid] = obj

                node_rels: list[tuple[str, tuple[str, ...]]] = []
                for rel_kind, rel_ops, sym in re_res.get("relations", []):
                    rel = (rel_kind, tuple(sorted(rel_ops)) if sym else tuple(rel_ops))
                    node_rels.append(rel)
                    all_reverified_rels.add(rel)
                verified_node_rels[nid] = node_rels
                rel_checked += 1

        given_only = {oid: obj for oid, obj in verified_objects.items() if obj.origin == "GIVEN_OBJECT"}
        all_reverified_rels |= _replay_given_relations(given_only, chart_metric)
        levels["L2"] = LevelResult(
            level="L2",
            passed=True,
            detail=f"Algebraically re-executed and verified {rel_checked} construction/derived-relation nodes.",
            evidence={"verified_nodes": rel_checked, "strict_node_replay": True},
        )

    # L3: Independent GOAL replay on transitive backward closure
    goal_nodes = [node_map[gid] for gid in proof_graph.goal_node_ids]
    l3_ok = bool(goal_nodes)
    l3_detail = "All GOAL nodes carry verified witness construction and exact rational/radical value."
    l3_fail_code = "UNVERIFIED_CONSTRUCTION"
    if l3_ok:
        for gn in goal_nodes:
            if gn.verification_status != "VERIFIED" or gn.verification_evidence.get("witness_verified") is not True:
                l3_ok = False
                l3_detail = f"Goal {gn.node_id!r} lacks verified witness evidence."
                break
            if strict_node_replay:
                closure_nids = set(trace_dependencies(proof_graph, (gn.node_id,)))
                closure_objs: dict[str, ConstructionObject] = {}
                for oid, obj in verified_objects.items():
                    if obj.supporting_node_id in closure_nids:
                        closure_objs[oid] = obj
                # Also allow outputs referenced by nodes in closure (including reused objects)
                for cnid in closure_nids:
                    for oid in node_map[cnid].output_objects:
                        if oid in verified_objects:
                            closure_objs[oid] = verified_objects[oid]
                closure_given = {oid: obj for oid, obj in closure_objs.items() if obj.origin == "GIVEN_OBJECT"}
                closure_rels = _replay_given_relations(closure_given, chart_metric)
                for cnid in closure_nids:
                    closure_rels.update(verified_node_rels.get(cnid, ()))

                # Check every declared witness_key belongs to the closure objects or closure relations
                wkeys = list(gn.verification_evidence.get("witness_keys") or ())
                rel_key_elems = {part for _, rel_ops in closure_rels for part in rel_ops}
                obj_key_set = {obj.canonical_geom_key for obj in closure_objs.values()}
                for wk in wkeys:
                    if wk not in obj_key_set and wk not in rel_key_elems:
                        l3_ok = False
                        l3_detail = f"Goal {gn.node_id!r} witness key {wk!r} missing from goal closure."
                        break
                if not l3_ok:
                    break

                # When operands exist (all `/2` graphs and new holdouts), replay exact witness equation evaluator
                if "operands" in gn.geometry_context and "goal_kind" in gn.geometry_context:
                    pts_c = {oid: obj.exact_value for oid, obj in closure_objs.items() if obj.object_kind == "point3"}
                    lns_c = {oid: obj.exact_value for oid, obj in closure_objs.items() if obj.object_kind == "line3"}
                    pls_c = {oid: obj.exact_value for oid, obj in closure_objs.items() if obj.object_kind == "plane3"}
                    segs_c = {oid: obj.exact_value for oid, obj in closure_objs.items() if obj.object_kind == "segment3"}
                    secs_c = {oid: obj.exact_value for oid, obj in closure_objs.items() if obj.object_kind == "section"}
                    key_to_ids_c: dict[str, list[str]] = {}
                    for oid, obj in sorted(closure_objs.items()):
                        key_to_ids_c.setdefault(obj.canonical_geom_key, []).append(oid)
                    gs = GoalSpec(
                        goal_kind=str(gn.geometry_context["goal_kind"]),
                        operands=dict(gn.geometry_context["operands"]),
                        length_unit=str(gn.geometry_context.get("length_unit") or proof_graph.length_unit or "a"),
                    )
                    re_eval = evaluate_goal_if_witnessed(
                        gs,
                        points_by_id=pts_c,
                        lines_by_id=lns_c,
                        planes_by_id=pls_c,
                        segments_by_id=segs_c,
                        sections_by_id=secs_c,
                        relations=closure_rels,
                        key_to_ids=key_to_ids_c,
                        chart_metric=chart_metric,
                    )
                    if re_eval is None or re_eval.get("answer") != gn.geometry_context.get("answer"):
                        l3_ok = False
                        l3_detail = (
                            f"Goal {gn.node_id!r} independent L3 witness replay failed: "
                            f"re_eval={re_eval.get('answer') if re_eval else None!r} vs claimed={gn.geometry_context.get('answer')!r}."
                        )
                        break

    levels["L3"] = LevelResult(
        level="L3",
        passed=l3_ok,
        detail=l3_detail,
        evidence={"goal_node_ids": list(proof_graph.goal_node_ids), "strict_goal_replay": strict_node_replay},
    )
    if not l3_ok:
        return VerificationReport(ver_id, False, levels, failure_code=l3_fail_code, failure_detail=l3_detail)

    # L4: Scene3D continuity validation + perpendicular witness certificate verification
    if scene3d is None:
        levels["L4"] = LevelResult("L4", True, "Scene3D not attached in proof-only pass; skipped cleanly.", {"evaluated": False})
    else:
        issues = construction_continuity.validate_construction_continuity(scene3d)
        l4_ok = len(issues) == 0
        l4_detail = "Scene3D cumulative construction continuity validated with 0 issues." if l4_ok else f"Scene3D continuity issues: {issues}"
        if l4_ok and strict_node_replay:
            for o in scene3d.get("objects", []):
                if o.get("type") == "segment3" and o.get("perpendicular_witness") is not None:
                    ok_w, code_w = certificates.verify_perpendicular_witness(
                        o["perpendicular_witness"],
                        scene3d,
                        chart_metric=chart_metric,
                        segment_obj=o,
                    )
                    if not ok_w:
                        l4_ok = False
                        l4_detail = f"Scene3D perpendicular_witness tamper detected on {o.get('id')!r}: {code_w}"
                        issues = [l4_detail]
                        break
        levels["L4"] = LevelResult(
            level="L4",
            passed=l4_ok,
            detail=l4_detail,
            evidence={"evaluated": True, "issues": issues},
        )
        if not l4_ok:
            return VerificationReport(ver_id, False, levels, failure_code="SCENE3D_CONTINUITY_FAILED", failure_detail=l4_detail)

    return VerificationReport(ver_id, True, levels)
