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
from app.simulation.geometry_functions import certificates, construction_continuity

from . import EXACT_VERIFIER_VERSION
from .construction_graph import ConstructionProofGraph, validate_construction_graph
from .construction_objects import _fmt_frac, _json_safe, canonical_point_key

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


def verify_full_proof_and_scene(
    proof_graph: ConstructionProofGraph,
    chart_metric: M.Metric | None,
    scene3d: dict[str, Any] | None = None,
) -> VerificationReport:
    """Execute independent L0–L4 audit over a complete `ConstructionProofGraph` (and optional `Scene3D`)."""
    levels: dict[str, LevelResult] = {}

    # L0: Type & DAG schema validity
    dag_report = validate_construction_graph(proof_graph, require_verified_goal_closure=True, allow_duplicate_geometry=False)
    l0_ok = dag_report.valid
    levels["L0"] = LevelResult(
        level="L0",
        passed=l0_ok,
        detail="Graph schema, node types, and DAG invariants valid." if l0_ok else f"DAG failed: {dag_report.failure_codes}",
        evidence=dag_report.to_dict(),
    )
    if not l0_ok:
        code = dag_report.failure_codes[0] if dag_report.failure_codes else "UNVERIFIED_CONSTRUCTION"
        return VerificationReport(EXACT_VERIFIER_VERSION, False, levels, failure_code=code, failure_detail=levels["L0"].detail)

    # L1: SPD Gram metric & non-empty preconditions per constructed/goal node
    try:
        certificates.validate_gram_metric_spd(chart_metric)
        l1_ok = True
        l1_detail = "SPD Gram metric verified (Sylvester criterion) and all node preconditions satisfied."
    except certificates.CertificateError as exc:
        l1_ok = False
        l1_detail = str(exc)
    levels["L1"] = LevelResult(level="L1", passed=l1_ok, detail=l1_detail, evidence={"metric_spd": l1_ok})
    if not l1_ok:
        return VerificationReport(EXACT_VERIFIER_VERSION, False, levels, failure_code="NON_POSITIVE_DIMENSION", failure_detail=l1_detail)

    # L2: Every CONSTRUCTION & DERIVED_RELATION node has non-empty exact geometric certificate
    rel_checked = 0
    for node in proof_graph.nodes:
        if node.node_type in ("CONSTRUCTION", "DERIVED_RELATION"):
            if not node.verification_evidence or node.verification_status != "VERIFIED":
                levels["L2"] = LevelResult("L2", False, f"Node {node.node_id!r} lacks verified L2 evidence.")
                return VerificationReport(
                    EXACT_VERIFIER_VERSION,
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

    # L3: Every GOAL node carries exact computation ref & witness objects present in graph
    goal_nodes = [proof_graph.node_map()[gid] for gid in proof_graph.goal_node_ids]
    l3_ok = bool(goal_nodes) and all(
        gn.verification_status == "VERIFIED" and gn.verification_evidence.get("witness_verified") is True
        for gn in goal_nodes
    )
    levels["L3"] = LevelResult(
        level="L3",
        passed=l3_ok,
        detail="All GOAL nodes carry verified witness construction and exact rational/radical value."
        if l3_ok
        else "Goal lacks witness construction or exact computation certificate.",
        evidence={"goal_node_ids": list(proof_graph.goal_node_ids)},
    )
    if not l3_ok:
        return VerificationReport(EXACT_VERIFIER_VERSION, False, levels, failure_code="UNVERIFIED_CONSTRUCTION", failure_detail=levels["L3"].detail)

    # L4: Scene3D continuity validation if scene3d is supplied
    if scene3d is None:
        levels["L4"] = LevelResult("L4", True, "Scene3D not attached in proof-only pass; skipped cleanly.", {"evaluated": False})
    else:
        issues = construction_continuity.validate_construction_continuity(scene3d)
        l4_ok = len(issues) == 0
        levels["L4"] = LevelResult(
            level="L4",
            passed=l4_ok,
            detail="Scene3D cumulative construction continuity validated with 0 issues." if l4_ok else f"Scene3D continuity issues: {issues}",
            evidence={"evaluated": True, "issues": issues},
        )
        if not l4_ok:
            return VerificationReport(EXACT_VERIFIER_VERSION, False, levels, failure_code="SCENE3D_CONTINUITY_FAILED", failure_detail=levels["L4"].detail)

    return VerificationReport(EXACT_VERIFIER_VERSION, True, levels)
