# -*- coding: utf-8 -*-
"""Atomic construction operator contract (`construction-operator/1`) and goal witness evaluators.

Strict separation:
- Construction operators produce geometric objects or proved geometric relations inside `app.simulation.geometry`
  with exact `Fraction` + Gram `Metric` certificates.
- Goal witness evaluators check whether the required constructed geometric witnesses and proved relations exist
  before computing any exact radical/rational answer (`metric != construction`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable

from app.simulation.geometry import exact as E
from app.simulation.geometry import kernel as K
from app.simulation.geometry import measure as MS
from app.simulation.geometry import metric as M
from app.simulation.geometry import radical as R
from app.simulation.geometry import section as S

from . import CONSTRUCTION_OPERATOR_SCHEMA
from .construction_objects import (
    _fmt_frac,
    _json_safe,
    canonical_line_key,
    canonical_plane_key,
    canonical_point_key,
    canonical_polygon_key,
    canonical_relation_key,
    canonical_segment_key,
)
from .construction_verifier import (
    VerificationError,
    format_exact_unit_answer,
    map_kernel_error_code,
    verify_dihedral_linear_angle,
    verify_line_perp_plane_gram,
    verify_lines_perpendicular,
    verify_non_collinear,
    verify_point_on_line,
    verify_point_on_plane,
    verify_points_distinct,
    verify_two_lines_deductive_perp_plane,
)


@dataclass(frozen=True)
class OperatorSpec:
    """Typed schema metadata for one operator in `construction-operator/1`."""

    operator_id: str
    category: str  # "point", "line", "segment", "plane", "section", "relation"
    input_types: tuple[str, ...]
    preconditions: tuple[str, ...]
    applicable_object_types: tuple[str, ...]
    output_types: tuple[str, ...]
    derived_relationships: tuple[str, ...]
    exact_verifier: str
    degeneracy_checks: tuple[str, ...]
    estimated_cost: float
    visualization_semantics: dict[str, Any]
    registry_backing: str  # EXISTS_IN_REGISTRY_33 | KERNEL_PRIMITIVE_MISSING_CONTRACT | PROTOTYPE_DEDUCTIVE_COMPOSITION
    executor: Callable[..., dict[str, Any]] = field(repr=False, compare=False)

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CONSTRUCTION_OPERATOR_SCHEMA,
            "operator_id": self.operator_id,
            "category": self.category,
            "input_types": list(self.input_types),
            "preconditions": list(self.preconditions),
            "applicable_object_types": list(self.applicable_object_types),
            "output_types": list(self.output_types),
            "derived_relationships": list(self.derived_relationships),
            "exact_verifier": self.exact_verifier,
            "degeneracy_checks": list(self.degeneracy_checks),
            "estimated_cost": self.estimated_cost,
            "visualization_semantics": _json_safe(self.visualization_semantics),
            "registry_backing": self.registry_backing,
        }


def _call_kernel_checked(fn: Callable[..., Any], *args: Any) -> Any:
    try:
        return fn(*args)
    except E.GeometryError as exc:
        raise VerificationError(map_kernel_error_code(exc), "L1", str(exc)) from exc


# ---------------------------------------------------------------------------
# Individual Operator Implementations (all execute inside `with M.using(metric):`)
# ---------------------------------------------------------------------------


def _exec_midpoint_segment(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    a: E.Point3 = inputs["a"]
    b: E.Point3 = inputs["b"]
    verify_points_distinct(a, b, "a", "b")
    with M.using(chart_metric):
        m = _call_kernel_checked(K.midpoint, a, b)
        ln = E.Line3.through(a, b)
        verify_point_on_line(m, ln, chart_metric)
        eq_ratio = (m - a) == (b - m)
    if not eq_ratio:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Midpoint failed vector bisection check.")
    return {
        "outputs": {"point": m},
        "canonical_keys": {"point": canonical_point_key(m)},
        "derived_constraints": [f"midpoint_of({canonical_point_key(m)})"],
        "relations": [("collinear_on_segment", (canonical_point_key(m), canonical_segment_key(E.Segment3.between(a, b))), True)],
        "verification_evidence": {"point_on_line_dist_sq": "0", "bisects_vector": True},
        "exact_computation_ref": "kernel.midpoint",
    }


def _exec_divide_segment_ratio(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    a: E.Point3 = inputs["a"]
    b: E.Point3 = inputs["b"]
    ratio = Fraction(params["ratio"])
    if ratio <= 0 or ratio >= 1:
        raise VerificationError("NON_POSITIVE_DIMENSION", "L1", f"Interior divide_segment ratio must be in (0,1), got {ratio}.")
    verify_points_distinct(a, b, "a", "b")
    with M.using(chart_metric):
        pt = _call_kernel_checked(K.divide_segment, a, b, ratio)
        ln = E.Line3.through(a, b)
        verify_point_on_line(pt, ln, chart_metric)
        ratio_ok = (pt - a) == (b - a).scale(ratio)
    if not ratio_ok:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Divided point failed exact affine ratio check.")
    return {
        "outputs": {"point": pt},
        "canonical_keys": {"point": canonical_point_key(pt)},
        "derived_constraints": [f"divide_segment_ratio={_fmt_frac(ratio)}"],
        "relations": [("collinear_on_segment", (canonical_point_key(pt), canonical_segment_key(E.Segment3.between(a, b))), True)],
        "verification_evidence": {"ratio": _fmt_frac(ratio), "affine_ratio_exact": True},
        "exact_computation_ref": "kernel.divide_segment",
    }


def _exec_triangle_centroid(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    a: E.Point3 = inputs["a"]
    b: E.Point3 = inputs["b"]
    c: E.Point3 = inputs["c"]
    verify_non_collinear(a, b, c)
    g = E.Vec3(
        (a.x + b.x + c.x) / 3,
        (a.y + b.y + c.y) / 3,
        (a.z + b.z + c.z) / 3,
    )
    pl = E.Plane3.through(a, b, c)
    verify_point_on_plane(g, pl, chart_metric)
    bary_ok = (a - g) + (b - g) + (c - g) == E.Vec3.of(0, 0, 0)
    if not bary_ok:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Centroid failed zero vector-sum invariant.")
    return {
        "outputs": {"point": g},
        "canonical_keys": {"point": canonical_point_key(g)},
        "derived_constraints": ["triangle_centroid"],
        "relations": [("point_on_plane", (canonical_point_key(g), canonical_plane_key(pl)), False)],
        "verification_evidence": {"signed_eval": "0", "zero_barycentric_sum": True},
        "exact_computation_ref": "exact.centroid",
    }


def _exec_point_reflection(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    p: E.Point3 = inputs["point"]
    center: E.Point3 = inputs["center"]
    verify_points_distinct(p, center, "point", "center")
    with M.using(chart_metric):
        img = _call_kernel_checked(K.translate, center, center - p)
        mid = _call_kernel_checked(K.midpoint, p, img)
    if mid != center:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Point reflection failed midpoint reflection invariant.")
    return {
        "outputs": {"point": img},
        "canonical_keys": {"point": canonical_point_key(img)},
        "derived_constraints": [f"point_reflection_center={canonical_point_key(center)}"],
        "relations": [],
        "verification_evidence": {"midpoint_equals_center": True},
        "exact_computation_ref": "kernel.translate(point_reflection)",
    }


def _exec_translate_point_by_vector(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    origin: E.Point3 = inputs["origin"]
    vec_a: E.Point3 = inputs["vec_from"]
    vec_b: E.Point3 = inputs["vec_to"]
    verify_points_distinct(vec_a, vec_b, "vec_from", "vec_to")
    with M.using(chart_metric):
        img = _call_kernel_checked(K.translate, origin, vec_b - vec_a)
    if (img - origin) != (vec_b - vec_a):
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Translated vector equality failed.")
    return {
        "outputs": {"point": img},
        "canonical_keys": {"point": canonical_point_key(img)},
        "derived_constraints": ["parallel_translation"],
        "relations": [],
        "verification_evidence": {"displacement_exact": True},
        "exact_computation_ref": "kernel.translate",
    }


def _exec_connect_segment(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    a: E.Point3 = inputs["a"]
    b: E.Point3 = inputs["b"]
    verify_points_distinct(a, b, "a", "b")
    seg = _call_kernel_checked(E.Segment3.between, a, b)
    with M.using(chart_metric):
        len_sq = M.norm_sq(seg.vector())
    if len_sq <= 0:
        raise VerificationError("NON_POSITIVE_DIMENSION", "L2", "Segment has non-positive squared length.")
    return {
        "outputs": {"segment": seg},
        "canonical_keys": {"segment": canonical_segment_key(seg)},
        "derived_constraints": [f"segment_length_sq={_fmt_frac(len_sq)}"],
        "relations": [],
        "verification_evidence": {"length_sq": _fmt_frac(len_sq)},
        "exact_computation_ref": "exact.Segment3.between",
    }


def _exec_line_through_points(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    a: E.Point3 = inputs["a"]
    b: E.Point3 = inputs["b"]
    verify_points_distinct(a, b, "a", "b")
    ln = _call_kernel_checked(E.Line3.through, a, b)
    ev1 = verify_point_on_line(a, ln, chart_metric)
    verify_point_on_line(b, ln, chart_metric)
    return {
        "outputs": {"line": ln},
        "canonical_keys": {"line": canonical_line_key(ln)},
        "derived_constraints": ["line_through_distinct_points"],
        "relations": [
            ("point_on_line", (canonical_point_key(a), canonical_line_key(ln)), False),
            ("point_on_line", (canonical_point_key(b), canonical_line_key(ln)), False),
        ],
        "verification_evidence": {**ev1, "two_points_incident": True},
        "exact_computation_ref": "exact.Line3.through",
    }


def _exec_line_parallel_through_point(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    pt: E.Point3 = inputs["point"]
    ref_line: E.Line3 = inputs["line"]
    with M.using(chart_metric):
        if MS.distance_sq_point_line(pt, ref_line) == 0:
            raise VerificationError(
                "DEGENERATE_POINT_ALREADY_INCIDENT",
                "L1",
                "Anchor point already lies on reference line; parallel line is identical to original.",
            )
        par_line = _call_kernel_checked(K.line_through_point_parallel_to, pt, ref_line)
        cross_zero = par_line.direction.cross(ref_line.direction).is_zero()
    if not cross_zero:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Constructed line is not parallel to reference line.")
    return {
        "outputs": {"line": par_line},
        "canonical_keys": {"line": canonical_line_key(par_line)},
        "derived_constraints": [f"parallel_line({canonical_line_key(par_line)}, {canonical_line_key(ref_line)})"],
        "relations": [
            ("point_on_line", (canonical_point_key(pt), canonical_line_key(par_line)), False),
            ("parallel_lines", (canonical_line_key(par_line), canonical_line_key(ref_line)), True),
        ],
        "verification_evidence": {"direction_cross_zero": True, "anchor_on_new_line": True},
        "exact_computation_ref": "kernel.line_through_point_parallel_to",
    }


def _exec_plane_through_three_points(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    a: E.Point3 = inputs["a"]
    b: E.Point3 = inputs["b"]
    c: E.Point3 = inputs["c"]
    verify_non_collinear(a, b, c)
    pl = _call_kernel_checked(E.Plane3.through, a, b, c)
    verify_point_on_plane(a, pl, chart_metric)
    verify_point_on_plane(b, pl, chart_metric)
    verify_point_on_plane(c, pl, chart_metric)
    plk = canonical_plane_key(pl)
    edge_rels = [
        ("line_in_plane", (canonical_line_key(E.Line3.through(u, v)), plk), False)
        for u, v in ((a, b), (b, c), (a, c))
    ]
    return {
        "outputs": {"plane": pl},
        "canonical_keys": {"plane": plk},
        "derived_constraints": ["plane_through_noncollinear_points"],
        "relations": [
            ("point_on_plane", (canonical_point_key(a), plk), False),
            ("point_on_plane", (canonical_point_key(b), plk), False),
            ("point_on_plane", (canonical_point_key(c), plk), False),
            *edge_rels,
        ],
        "verification_evidence": {"three_points_signed_eval_zero": True},
        "exact_computation_ref": "exact.Plane3.through",
    }


def _exec_plane_through_point_parallel_plane(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    pt: E.Point3 = inputs["point"]
    ref_pl: E.Plane3 = inputs["plane"]
    if ref_pl.signed_eval(pt) == 0:
        raise VerificationError(
            "DEGENERATE_POINT_ALREADY_INCIDENT",
            "L1",
            "Anchor point already lies on reference plane; parallel plane coincides.",
        )
    new_pl = _call_kernel_checked(K.plane_through_point_parallel_to, pt, ref_pl)
    verify_point_on_plane(pt, new_pl, chart_metric)
    with M.using(chart_metric):
        par_ok = MS.parallel_planes(new_pl, ref_pl)
    if not par_ok:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Constructed plane failed parallel_planes check.")
    return {
        "outputs": {"plane": new_pl},
        "canonical_keys": {"plane": canonical_plane_key(new_pl)},
        "derived_constraints": [f"parallel_planes({canonical_plane_key(new_pl)}, {canonical_plane_key(ref_pl)})"],
        "relations": [
            ("point_on_plane", (canonical_point_key(pt), canonical_plane_key(new_pl)), False),
            ("parallel_planes", (canonical_plane_key(new_pl), canonical_plane_key(ref_pl)), True),
        ],
        "verification_evidence": {"parallel_planes": True, "anchor_signed_eval": "0"},
        "exact_computation_ref": "kernel.plane_through_point_parallel_to",
    }


def _exec_plane_through_line_parallel_line(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """Construct plane containing `host_line` and strictly parallel to `parallel_to_line` (for skew lines)."""
    host_line: E.Line3 = inputs["host_line"]
    par_line: E.Line3 = inputs["parallel_to_line"]
    n = host_line.direction.cross(par_line.direction)
    if n.is_zero():
        raise VerificationError(
            "NON_UNIQUE_AUXILIARY",
            "L1",
            "Lines are parallel or coincident; plane through one parallel to the other is not unique.",
        )
    with M.using(chart_metric):
        if not MS.skew_lines(host_line, par_line):
            raise VerificationError(
                "DEGENERATE_NON_SKEW_LINES",
                "L1",
                "Lines are coplanar (intersecting); auxiliary parallel plane does not separate skew lines.",
            )
    pl = E.Plane3(host_line.point, n)
    with M.using(chart_metric):
        par_ok = MS.parallel_line_plane(par_line, pl) and pl.normal.dot(host_line.direction) == 0
    if not par_ok or pl.signed_eval(host_line.point) != 0:
        raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Auxiliary skew-transfer plane failed containment/parallelism check.")
    return {
        "outputs": {"plane": pl},
        "canonical_keys": {"plane": canonical_plane_key(pl)},
        "derived_constraints": [
            f"line_in_plane({canonical_line_key(host_line)}, {canonical_plane_key(pl)})",
            f"parallel_line_plane({canonical_line_key(par_line)}, {canonical_plane_key(pl)})",
        ],
        "relations": [
            ("line_in_plane", (canonical_line_key(host_line), canonical_plane_key(pl)), False),
            ("parallel_line_plane", (canonical_line_key(par_line), canonical_plane_key(pl)), False),
        ],
        "verification_evidence": {"host_line_contained": True, "other_line_parallel": True},
        "exact_computation_ref": "exact.Plane3(skew_parallel_span)",
    }


def _exec_plane_through_point_perp_line(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    pt: E.Point3 = inputs["point"]
    ln: E.Line3 = inputs["line"]
    if ln.direction.is_zero():
        raise VerificationError("DEGENERATE_COINCIDENT_POINTS", "L1", "Zero line direction.")
    with M.using(chart_metric):
        pl = _call_kernel_checked(K.plane_through_point_perpendicular_to, pt, ln)
    ev_pt = verify_point_on_plane(pt, pl, chart_metric)
    ev_orth = verify_line_perp_plane_gram(ln.direction, pl, chart_metric)
    return {
        "outputs": {"plane": pl},
        "canonical_keys": {"plane": canonical_plane_key(pl)},
        "derived_constraints": [f"perp_line_plane({canonical_line_key(ln)}, {canonical_plane_key(pl)})"],
        "relations": [
            ("point_on_plane", (canonical_point_key(pt), canonical_plane_key(pl)), False),
            ("perp_line_plane", (canonical_line_key(ln), canonical_plane_key(pl)), False),
        ],
        "verification_evidence": {**ev_pt, **ev_orth},
        "exact_computation_ref": "kernel.plane_through_point_perpendicular_to",
    }


def _exec_project_point_to_line(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    pt: E.Point3 = inputs["point"]
    ln: E.Line3 = inputs["line"]
    with M.using(chart_metric):
        if MS.distance_sq_point_line(pt, ln) == 0:
            raise VerificationError(
                "DEGENERATE_POINT_ALREADY_INCIDENT",
                "L1",
                "Point already lies on line; auxiliary perpendicular segment is degenerate.",
            )
        foot = _call_kernel_checked(K.project_point_onto_line, pt, ln)
        verify_point_on_line(foot, ln, chart_metric)
        seg = E.Segment3.between(pt, foot)
        orth_line = E.Line3.through(pt, foot)
        ev_orth = verify_lines_perpendicular(orth_line, ln, chart_metric)
    return {
        "outputs": {"foot": foot, "segment": seg, "line": orth_line},
        "canonical_keys": {
            "foot": canonical_point_key(foot),
            "segment": canonical_segment_key(seg),
            "line": canonical_line_key(orth_line),
        },
        "derived_constraints": [f"perp_lines({canonical_line_key(orth_line)}, {canonical_line_key(ln)})"],
        "relations": [
            ("point_on_line", (canonical_point_key(foot), canonical_line_key(ln)), False),
            ("perp_lines", (canonical_line_key(orth_line), canonical_line_key(ln)), True),
            ("perp_point_line_witness", (canonical_point_key(pt), canonical_line_key(ln), canonical_point_key(foot)), False),
        ],
        "verification_evidence": {**ev_orth, "foot_on_line": True},
        "exact_computation_ref": "kernel.project_point_onto_line",
    }


def _exec_project_point_to_plane(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    pt: E.Point3 = inputs["point"]
    pl: E.Plane3 = inputs["plane"]
    with M.using(chart_metric):
        if pl.signed_eval(pt) == 0:
            raise VerificationError(
                "DEGENERATE_POINT_ALREADY_INCIDENT",
                "L1",
                "Point already lies in plane; auxiliary altitude segment is zero.",
            )
        foot = _call_kernel_checked(K.project_point_onto_plane, pt, pl)
        verify_point_on_plane(foot, pl, chart_metric)
        seg = E.Segment3.between(pt, foot)
        orth_line = E.Line3.through(pt, foot)
        ev_orth = verify_line_perp_plane_gram(orth_line.direction, pl, chart_metric)
    return {
        "outputs": {"foot": foot, "segment": seg, "line": orth_line},
        "canonical_keys": {
            "foot": canonical_point_key(foot),
            "segment": canonical_segment_key(seg),
            "line": canonical_line_key(orth_line),
        },
        "derived_constraints": [f"perp_line_plane({canonical_line_key(orth_line)}, {canonical_plane_key(pl)})"],
        "relations": [
            ("point_on_plane", (canonical_point_key(foot), canonical_plane_key(pl)), False),
            ("perp_line_plane", (canonical_line_key(orth_line), canonical_plane_key(pl)), False),
            ("perp_point_plane_witness", (canonical_point_key(pt), canonical_plane_key(pl), canonical_point_key(foot)), False),
        ],
        "verification_evidence": {**ev_orth, "foot_on_plane": True},
        "exact_computation_ref": "kernel.project_point_onto_plane",
    }


def _exec_common_perpendicular_skew_lines(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    ln1: E.Line3 = inputs["line1"]
    ln2: E.Line3 = inputs["line2"]
    with M.using(chart_metric):
        if not MS.skew_lines(ln1, ln2):
            raise VerificationError("DEGENERATE_NON_SKEW_LINES", "L1", "Lines are not skew; unique common perpendicular segment does not exist.")
        p1, p2 = _call_kernel_checked(K.common_perpendicular_feet, ln1, ln2)
        verify_point_on_line(p1, ln1, chart_metric)
        verify_point_on_line(p2, ln2, chart_metric)
        seg = E.Segment3.between(p1, p2)
        comm_line = E.Line3.through(p1, p2)
        ev1 = verify_lines_perpendicular(comm_line, ln1, chart_metric)
        ev2 = verify_lines_perpendicular(comm_line, ln2, chart_metric)
    return {
        "outputs": {"foot1": p1, "foot2": p2, "segment": seg, "line": comm_line},
        "canonical_keys": {
            "foot1": canonical_point_key(p1),
            "foot2": canonical_point_key(p2),
            "segment": canonical_segment_key(seg),
            "line": canonical_line_key(comm_line),
        },
        "derived_constraints": [
            f"perp_lines({canonical_line_key(comm_line)}, {canonical_line_key(ln1)})",
            f"perp_lines({canonical_line_key(comm_line)}, {canonical_line_key(ln2)})",
        ],
        "relations": [
            ("point_on_line", (canonical_point_key(p1), canonical_line_key(ln1)), False),
            ("point_on_line", (canonical_point_key(p2), canonical_line_key(ln2)), False),
            ("common_perpendicular_witness", (*sorted((canonical_line_key(ln1), canonical_line_key(ln2))), canonical_segment_key(seg)), False),
        ],
        "verification_evidence": {"perp_line1": ev1, "perp_line2": ev2},
        "exact_computation_ref": "kernel.common_perpendicular_feet",
    }


def _exec_intersect_coplanar_lines(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    ln1: E.Line3 = inputs["line1"]
    ln2: E.Line3 = inputs["line2"]
    with M.using(chart_metric):
        pt = _call_kernel_checked(K.intersect_line_line, ln1, ln2)
        ev1 = verify_point_on_line(pt, ln1, chart_metric)
        ev2 = verify_point_on_line(pt, ln2, chart_metric)
    return {
        "outputs": {"point": pt},
        "canonical_keys": {"point": canonical_point_key(pt)},
        "derived_constraints": [f"intersection_point({canonical_line_key(ln1)}, {canonical_line_key(ln2)})"],
        "relations": [
            ("point_on_line", (canonical_point_key(pt), canonical_line_key(ln1)), False),
            ("point_on_line", (canonical_point_key(pt), canonical_line_key(ln2)), False),
            ("intersecting_lines_witness", (canonical_line_key(ln1), canonical_line_key(ln2), canonical_point_key(pt)), True),
        ],
        "verification_evidence": {"on_line1": ev1, "on_line2": ev2},
        "exact_computation_ref": "kernel.intersect_line_line",
    }


def _exec_intersect_line_plane(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    ln: E.Line3 = inputs["line"]
    pl: E.Plane3 = inputs["plane"]
    with M.using(chart_metric):
        pt = _call_kernel_checked(K.intersect_line_plane, ln, pl)
        ev1 = verify_point_on_line(pt, ln, chart_metric)
        ev2 = verify_point_on_plane(pt, pl, chart_metric)
    return {
        "outputs": {"point": pt},
        "canonical_keys": {"point": canonical_point_key(pt)},
        "derived_constraints": [f"intersect_line_plane({canonical_line_key(ln)}, {canonical_plane_key(pl)})"],
        "relations": [
            ("point_on_line", (canonical_point_key(pt), canonical_line_key(ln)), False),
            ("point_on_plane", (canonical_point_key(pt), canonical_plane_key(pl)), False),
            ("line_plane_intersection_witness", (canonical_line_key(ln), canonical_plane_key(pl), canonical_point_key(pt)), False),
        ],
        "verification_evidence": {"on_line": ev1, "on_plane": ev2},
        "exact_computation_ref": "kernel.intersect_line_plane",
    }


def _exec_intersect_planes(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    p1: E.Plane3 = inputs["plane1"]
    p2: E.Plane3 = inputs["plane2"]
    with M.using(chart_metric):
        edge = _call_kernel_checked(K.intersect_plane_plane, p1, p2)
        ev1 = verify_point_on_plane(edge.point, p1, chart_metric)
        ev2 = verify_point_on_plane(edge.point, p2, chart_metric)
        if p1.normal.dot(edge.direction) != 0 or p2.normal.dot(edge.direction) != 0:
            raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Intersection direction does not lie in both planes.")
    return {
        "outputs": {"line": edge},
        "canonical_keys": {"line": canonical_line_key(edge)},
        "derived_constraints": [f"intersection_line({canonical_plane_key(p1)}, {canonical_plane_key(p2)})"],
        "relations": [
            ("line_in_plane", (canonical_line_key(edge), canonical_plane_key(p1)), False),
            ("line_in_plane", (canonical_line_key(edge), canonical_plane_key(p2)), False),
            ("planes_intersection_line", (*sorted((canonical_plane_key(p1), canonical_plane_key(p2))), canonical_line_key(edge)), False),
        ],
        "verification_evidence": {"anchor_on_p1": ev1, "anchor_on_p2": ev2, "direction_in_both_planes": True},
        "exact_computation_ref": "kernel.intersect_plane_plane",
    }


def _exec_polyhedron_plane_section(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    poly: S.Polyhedron = inputs["solid"]
    pl: E.Plane3 = inputs["plane"]
    with M.using(chart_metric):
        sec = _call_kernel_checked(S.cross_section, poly, pl)
        if len(sec.polygon) < 3:
            raise VerificationError("DEGENERATE_COLLINEAR_POINTS", "L1", "Section polygon has fewer than 3 distinct vertices.")
        for v in sec.polygon:
            verify_point_on_plane(v, pl, chart_metric)
        area_ex = MS.area_section(sec)
    if area_ex == 0:
        raise VerificationError("NON_POSITIVE_DIMENSION", "L2", "Section polygon has zero area.")
    return {
        "outputs": {"section": sec},
        "canonical_keys": {"section": canonical_polygon_key(sec.polygon, kind="sec")},
        "derived_constraints": [f"closed_section({len(sec.polygon)}_vertices)"],
        "relations": [("section_of_solid_plane", (canonical_plane_key(pl),), False)],
        "verification_evidence": {"vertex_count": len(sec.polygon), "all_vertices_signed_eval_zero": True, "area": R.display(area_ex)},
        "exact_computation_ref": "section.cross_section",
    }


def _exec_deduce_line_perp_plane_two_lines(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """Synthesize proven `perp_line_plane(line, plane)` via two non-parallel planar directions `d1, d2`."""
    ln: E.Line3 = inputs["line"]
    d1_line: E.Line3 = inputs["planar_line1"]
    d2_line: E.Line3 = inputs["planar_line2"]
    pl: E.Plane3 = inputs["plane"]
    cert = verify_two_lines_deductive_perp_plane(
        ln.direction,
        d1_line.direction,
        d2_line.direction,
        pl,
        chart_metric,
    )
    gram_cert = verify_line_perp_plane_gram(ln.direction, pl, chart_metric)
    anchor_pt: E.Point3 | None = inputs.get("anchor_on_plane")
    extra_rels: list[tuple[str, tuple[str, ...], bool]] = [
        ("perp_line_plane", (canonical_line_key(ln), canonical_plane_key(pl)), False),
    ]
    if anchor_pt is not None and pl.signed_eval(anchor_pt) == 0 and canonical_point_key(anchor_pt) != canonical_point_key(ln.point):
        # Identify which endpoint of `ln` lies away from `pl` so witness points from external point -> foot on plane
        from_pt = ln.point if pl.signed_eval(ln.point) != 0 else (ln.point + ln.direction)
        if pl.signed_eval(from_pt) != 0:
            extra_rels.append(
                ("perp_point_plane_witness", (canonical_point_key(from_pt), canonical_plane_key(pl), canonical_point_key(anchor_pt)), False)
            )
    return {
        "outputs": {},
        "canonical_keys": {},
        "derived_constraints": [f"deduced_perp_line_plane({canonical_line_key(ln)}, {canonical_plane_key(pl)})"],
        "relations": extra_rels,
        "verification_evidence": {**cert, **gram_cert},
        "exact_computation_ref": "certificates.certify_deductive_line_plane_perpendicularity",
    }


def _exec_construct_dihedral_linear_angle(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """Construct dihedral linear angle at `vertex ∈ plane1 ∩ plane2`: two rays in P, Q orthogonal to edge Δ."""
    p1: E.Plane3 = inputs["plane1"]
    p2: E.Plane3 = inputs["plane2"]
    edge: E.Line3 = inputs["edge"]
    vertex: E.Point3 | None = inputs.get("vertex")
    with M.using(chart_metric):
        if MS.parallel_planes(p1, p2):
            raise VerificationError("DEGENERATE_PARALLEL_NO_INTERSECTION", "L1", "Parallel/coincident planes lack a dihedral edge.")
        # Construct plane at `anchor` orthogonal to edge Δ, intersect with P and Q
        anchor = vertex if vertex is not None else edge.point
        verify_point_on_line(anchor, edge, chart_metric)
        perp_plane = _call_kernel_checked(K.plane_through_point_perpendicular_to, anchor, edge)
        ray1 = _call_kernel_checked(K.intersect_plane_plane, p1, perp_plane)
        ray2 = _call_kernel_checked(K.intersect_plane_plane, p2, perp_plane)
        cert = verify_dihedral_linear_angle(edge, ray1, ray2, p1, p2, anchor, chart_metric)
    return {
        "outputs": {"ray1": ray1, "ray2": ray2, "perp_plane": perp_plane},
        "canonical_keys": {
            "ray1": canonical_line_key(ray1),
            "ray2": canonical_line_key(ray2),
            "perp_plane": canonical_plane_key(perp_plane),
        },
        "derived_constraints": [f"dihedral_linear_angle(cos_sq={cert['cos_sq']})"],
        "relations": [
            (
                "dihedral_linear_angle_witness",
                (*sorted((canonical_plane_key(p1), canonical_plane_key(p2))), *sorted((canonical_line_key(ray1), canonical_line_key(ray2)))),
                False,
            ),
        ],
        "verification_evidence": cert,
        "exact_computation_ref": "kernel.intersect_plane_plane(dihedral_linear_angle)",
    }


def _exec_deduce_parallel_line_plane_transfer(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """Prove `line ∥ plane` and transfer `d(line, plane)` to `d(sample_point ∈ line, plane)`."""
    ln: E.Line3 = inputs["line"]
    pl: E.Plane3 = inputs["plane"]
    pt: E.Point3 = inputs["sample_point"]
    verify_point_on_line(pt, ln, chart_metric)
    with M.using(chart_metric):
        if not MS.parallel_line_plane(ln, pl):
            raise VerificationError("IMPOSSIBLE_PERPENDICULARITY", "L2", "Line is not parallel to plane; distance cannot transfer.")
        if pl.signed_eval(pt) == 0:
            raise VerificationError("DEGENERATE_CONTAINED_INFINITE_INTERSECTION", "L1", "Line is contained inside plane (distance=0).")
    return {
        "outputs": {},
        "canonical_keys": {},
        "derived_constraints": [f"parallel_line_plane_transfer({canonical_line_key(ln)}, {canonical_plane_key(pl)})"],
        "relations": [
            ("parallel_line_plane", (canonical_line_key(ln), canonical_plane_key(pl)), False),
            ("distance_transfer_line_to_point", (canonical_line_key(ln), canonical_plane_key(pl), canonical_point_key(pt)), False),
        ],
        "verification_evidence": {"normal_dot_direction_zero": True, "sample_point_off_plane": True},
        "exact_computation_ref": "measure.parallel_line_plane",
    }


def _exec_deduce_planar_perp_from_perp_plane(
    inputs: dict[str, Any],
    params: dict[str, Any],
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    """Given `perp_line ⟂ host_plane` and `line_in_plane ⊂ host_plane`, prove `perp_line ⟂ line_in_plane`."""
    perp_ln: E.Line3 = inputs["perp_line"]
    in_ln: E.Line3 = inputs["line_in_plane"]
    host_pl: E.Plane3 = inputs["host_plane"]
    with M.using(chart_metric):
        ev_pl = verify_line_perp_plane_gram(perp_ln.direction, host_pl, chart_metric)
        if host_pl.normal.dot(in_ln.direction) != 0:
            raise VerificationError("UNVERIFIED_CONSTRUCTION", "L2", "Second line does not lie parallel to / inside host plane.")
        ev_ln = verify_lines_perpendicular(perp_ln, in_ln, chart_metric)
    return {
        "outputs": {},
        "canonical_keys": {},
        "derived_constraints": [f"deduced_perp_lines({canonical_line_key(perp_ln)}, {canonical_line_key(in_ln)})"],
        "relations": [("perp_lines", (canonical_line_key(perp_ln), canonical_line_key(in_ln)), True)],
        "verification_evidence": {"line_perp_host_plane": ev_pl, "exact_lines_perp": ev_ln},
        "exact_computation_ref": "exact.perp_plane_implies_perp_line",
    }


# ---------------------------------------------------------------------------
# Operator Registry (`construction-operator/1`)
# ---------------------------------------------------------------------------

OPERATOR_SPECS: dict[str, OperatorSpec] = {
    "op.midpoint_segment": OperatorSpec(
        operator_id="op.midpoint_segment",
        category="point",
        input_types=("point3", "point3"),
        preconditions=("distinct_points(a, b)",),
        applicable_object_types=("point3",),
        output_types=("point3",),
        derived_relationships=("collinear_on_segment",),
        exact_verifier="exact vector bisection (m - a == b - m) + point_on_line",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS",),
        estimated_cost=1.0,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "marker": "midpoint"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_midpoint_segment,
    ),
    "op.divide_segment_ratio": OperatorSpec(
        operator_id="op.divide_segment_ratio",
        category="point",
        input_types=("point3", "point3", "ratio"),
        preconditions=("distinct_points(a, b)", "0 < ratio < 1"),
        applicable_object_types=("point3",),
        output_types=("point3",),
        derived_relationships=("collinear_on_segment",),
        exact_verifier="exact affine ratio (p - a == ratio * (b - a))",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS", "NON_POSITIVE_DIMENSION"),
        estimated_cost=1.0,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "marker": "ratio_point"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_divide_segment_ratio,
    ),
    "op.triangle_centroid": OperatorSpec(
        operator_id="op.triangle_centroid",
        category="point",
        input_types=("point3", "point3", "point3"),
        preconditions=("non_collinear(a, b, c)",),
        applicable_object_types=("point3",),
        output_types=("point3",),
        derived_relationships=("point_on_plane",),
        exact_verifier="(a-g)+(b-g)+(c-g)==0 + signed_eval==0",
        degeneracy_checks=("DEGENERATE_COLLINEAR_POINTS",),
        estimated_cost=1.0,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "marker": "centroid"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_triangle_centroid,
    ),
    "op.point_reflection": OperatorSpec(
        operator_id="op.point_reflection",
        category="point",
        input_types=("point3", "point3"),
        preconditions=("distinct_points(point, center)",),
        applicable_object_types=("point3",),
        output_types=("point3",),
        derived_relationships=(),
        exact_verifier="midpoint(point, image) == center",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS",),
        estimated_cost=1.2,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "marker": "reflection"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_point_reflection,
    ),
    "op.translate_point_by_vector": OperatorSpec(
        operator_id="op.translate_point_by_vector",
        category="point",
        input_types=("point3", "point3", "point3"),
        preconditions=("distinct_points(vec_from, vec_to)",),
        applicable_object_types=("point3",),
        output_types=("point3",),
        derived_relationships=(),
        exact_verifier="(image - origin) == (vec_to - vec_from)",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS",),
        estimated_cost=1.2,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "marker": "translated_point"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_translate_point_by_vector,
    ),
    "op.connect_segment": OperatorSpec(
        operator_id="op.connect_segment",
        category="segment",
        input_types=("point3", "point3"),
        preconditions=("distinct_points(a, b)",),
        applicable_object_types=("point3",),
        output_types=("segment3",),
        derived_relationships=(),
        exact_verifier="Gram norm_sq(b - a) > 0",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS", "NON_POSITIVE_DIMENSION"),
        estimated_cost=0.5,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "render": "segment"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_connect_segment,
    ),
    "op.line_through_points": OperatorSpec(
        operator_id="op.line_through_points",
        category="line",
        input_types=("point3", "point3"),
        preconditions=("distinct_points(a, b)",),
        applicable_object_types=("point3",),
        output_types=("line3",),
        derived_relationships=("point_on_line",),
        exact_verifier="distance_sq(a, line)==0 and distance_sq(b, line)==0",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS",),
        estimated_cost=0.6,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "render": "line"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_line_through_points,
    ),
    "op.line_parallel_through_point": OperatorSpec(
        operator_id="op.line_parallel_through_point",
        category="line",
        input_types=("point3", "line3"),
        preconditions=("not point_on_line(point, line)",),
        applicable_object_types=("point3", "line3"),
        output_types=("line3",),
        derived_relationships=("point_on_line", "parallel_lines"),
        exact_verifier="d_new x d_ref == 0 and point_on_line(point, new_line)",
        degeneracy_checks=("DEGENERATE_POINT_ALREADY_INCIDENT",),
        estimated_cost=1.3,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "render": "line"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_line_parallel_through_point,
    ),
    "op.plane_through_three_points": OperatorSpec(
        operator_id="op.plane_through_three_points",
        category="plane",
        input_types=("point3", "point3", "point3"),
        preconditions=("non_collinear(a, b, c)",),
        applicable_object_types=("point3",),
        output_types=("plane3",),
        derived_relationships=("point_on_plane",),
        exact_verifier="signed_eval(a)==signed_eval(b)==signed_eval(c)==0",
        degeneracy_checks=("DEGENERATE_COLLINEAR_POINTS",),
        estimated_cost=0.8,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "render": "surface"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_plane_through_three_points,
    ),
    "op.plane_through_point_parallel_plane": OperatorSpec(
        operator_id="op.plane_through_point_parallel_plane",
        category="plane",
        input_types=("point3", "plane3"),
        preconditions=("not point_on_plane(point, plane)",),
        applicable_object_types=("point3", "plane3"),
        output_types=("plane3",),
        derived_relationships=("point_on_plane", "parallel_planes"),
        exact_verifier="parallel_planes(new, ref) and signed_eval(point)==0",
        degeneracy_checks=("DEGENERATE_POINT_ALREADY_INCIDENT",),
        estimated_cost=1.4,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "render": "surface"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_plane_through_point_parallel_plane,
    ),
    "op.plane_through_line_parallel_line": OperatorSpec(
        operator_id="op.plane_through_line_parallel_line",
        category="plane",
        input_types=("line3", "line3"),
        preconditions=("skew_lines(host_line, parallel_to_line)",),
        applicable_object_types=("line3",),
        output_types=("plane3",),
        derived_relationships=("line_in_plane", "parallel_line_plane"),
        exact_verifier="host_line contained in plane and parallel_line_plane(other, plane)",
        degeneracy_checks=("NON_UNIQUE_AUXILIARY", "DEGENERATE_NON_SKEW_LINES"),
        estimated_cost=1.6,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "render": "surface"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_plane_through_line_parallel_line,
    ),
    "op.plane_through_point_perp_line": OperatorSpec(
        operator_id="op.plane_through_point_perp_line",
        category="plane",
        input_types=("point3", "line3"),
        preconditions=("non_zero_direction(line)",),
        applicable_object_types=("point3", "line3"),
        output_types=("plane3",),
        derived_relationships=("point_on_plane", "perp_line_plane"),
        exact_verifier="plane_covector(line.dir) collinear with plane.normal",
        degeneracy_checks=("DEGENERATE_COINCIDENT_POINTS",),
        estimated_cost=1.4,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "render": "surface"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_plane_through_point_perp_line,
    ),
    "op.project_point_to_line": OperatorSpec(
        operator_id="op.project_point_to_line",
        category="point",
        input_types=("point3", "line3"),
        preconditions=("not point_on_line(point, line)", "spd_metric"),
        applicable_object_types=("point3", "line3"),
        output_types=("point3", "segment3", "line3"),
        derived_relationships=("point_on_line", "perp_lines", "perp_point_line_witness"),
        exact_verifier="dot(foot - point, line.dir) == 0 in Gram metric + foot on line",
        degeneracy_checks=("DEGENERATE_POINT_ALREADY_INCIDENT",),
        estimated_cost=1.3,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "marker": "perp_foot"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_project_point_to_line,
    ),
    "op.project_point_to_plane": OperatorSpec(
        operator_id="op.project_point_to_plane",
        category="point",
        input_types=("point3", "plane3"),
        preconditions=("not point_on_plane(point, plane)", "spd_metric"),
        applicable_object_types=("point3", "plane3"),
        output_types=("point3", "segment3", "line3"),
        derived_relationships=("point_on_plane", "perp_line_plane", "perp_point_plane_witness"),
        exact_verifier="sin_sq(line(point,foot), plane)==1 in Gram metric + signed_eval(foot)==0",
        degeneracy_checks=("DEGENERATE_POINT_ALREADY_INCIDENT",),
        estimated_cost=1.8,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "marker": "altitude_foot"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_project_point_to_plane,
    ),
    "op.common_perpendicular_skew_lines": OperatorSpec(
        operator_id="op.common_perpendicular_skew_lines",
        category="segment",
        input_types=("line3", "line3"),
        preconditions=("skew_lines(line1, line2)", "spd_metric"),
        applicable_object_types=("line3",),
        output_types=("point3", "point3", "segment3", "line3"),
        derived_relationships=("point_on_line", "common_perpendicular_witness"),
        exact_verifier="dot(p2 - p1, d1)==0 and dot(p2 - p1, d2)==0 in Gram metric",
        degeneracy_checks=("DEGENERATE_NON_SKEW_LINES",),
        estimated_cost=2.0,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "marker": "common_perp"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_common_perpendicular_skew_lines,
    ),
    "op.intersect_coplanar_lines": OperatorSpec(
        operator_id="op.intersect_coplanar_lines",
        category="point",
        input_types=("line3", "line3"),
        preconditions=("coplanar_non_parallel(line1, line2)",),
        applicable_object_types=("line3",),
        output_types=("point3",),
        derived_relationships=("point_on_line", "intersecting_lines_witness"),
        exact_verifier="point_on_line(pt, line1) and point_on_line(pt, line2)",
        degeneracy_checks=("DEGENERATE_PARALLEL_NO_INTERSECTION", "DEGENERATE_SKEW_NO_INTERSECTION", "DEGENERATE_CONTAINED_INFINITE_INTERSECTION"),
        estimated_cost=1.1,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "marker": "intersection"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_intersect_coplanar_lines,
    ),
    "op.intersect_line_plane": OperatorSpec(
        operator_id="op.intersect_line_plane",
        category="point",
        input_types=("line3", "plane3"),
        preconditions=("not parallel_or_contained(line, plane)",),
        applicable_object_types=("line3", "plane3"),
        output_types=("point3",),
        derived_relationships=("point_on_line", "point_on_plane", "line_plane_intersection_witness"),
        exact_verifier="point_on_line(pt, line) and signed_eval(pt, plane)==0",
        degeneracy_checks=("DEGENERATE_PARALLEL_NO_INTERSECTION", "DEGENERATE_CONTAINED_INFINITE_INTERSECTION"),
        estimated_cost=1.1,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "marker": "intersection"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_intersect_line_plane,
    ),
    "op.intersect_planes": OperatorSpec(
        operator_id="op.intersect_planes",
        category="line",
        input_types=("plane3", "plane3"),
        preconditions=("not parallel_planes(plane1, plane2)",),
        applicable_object_types=("plane3",),
        output_types=("line3",),
        derived_relationships=("line_in_plane", "planes_intersection_line"),
        exact_verifier="edge anchor + direction lie in both plane1 and plane2",
        degeneracy_checks=("DEGENERATE_PARALLEL_NO_INTERSECTION", "DEGENERATE_CONTAINED_INFINITE_INTERSECTION"),
        estimated_cost=1.1,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "render": "line"},
        registry_backing="EXISTS_IN_REGISTRY_33",
        executor=_exec_intersect_planes,
    ),
    "op.polyhedron_plane_section": OperatorSpec(
        operator_id="op.polyhedron_plane_section",
        category="section",
        input_types=("solid", "plane3"),
        preconditions=("plane_cuts_polyhedron_with_positive_area(solid, plane)",),
        applicable_object_types=("solid", "plane3"),
        output_types=("section",),
        derived_relationships=("section_of_solid_plane",),
        exact_verifier="all section vertices satisfy signed_eval==0 and closed area > 0",
        degeneracy_checks=("DEGENERATE_COLLINEAR_POINTS", "NON_POSITIVE_DIMENSION"),
        estimated_cost=1.5,
        visualization_semantics={"action_hint": "CONSTRUCT_DERIVED", "render": "polygon"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_polyhedron_plane_section,
    ),
    "op.deduce_line_perp_plane_two_lines": OperatorSpec(
        operator_id="op.deduce_line_perp_plane_two_lines",
        category="relation",
        input_types=("line3", "line3", "line3", "plane3"),
        preconditions=("line ⟂ d1", "line ⟂ d2", "d1 ∦ d2 in plane"),
        applicable_object_types=("line3", "plane3"),
        output_types=("relation",),
        derived_relationships=("perp_line_plane", "perp_point_plane_witness"),
        exact_verifier="Gram dot(line,d1)==0 and dot(line,d2)==0 and d1,d2 independent in plane",
        degeneracy_checks=("DEGENERATE_COLLINEAR_POINTS", "IMPOSSIBLE_PERPENDICULARITY"),
        estimated_cost=0.4,
        visualization_semantics={"action_hint": "ESTABLISH_RELATION", "theorem": "perp_two_lines"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_deduce_line_perp_plane_two_lines,
    ),
    "op.construct_dihedral_linear_angle": OperatorSpec(
        operator_id="op.construct_dihedral_linear_angle",
        category="line",
        input_types=("plane3", "plane3", "line3"),
        preconditions=("edge == plane1 ∩ plane2", "not parallel_planes(plane1, plane2)"),
        applicable_object_types=("plane3", "line3"),
        output_types=("line3", "line3", "plane3"),
        derived_relationships=("dihedral_linear_angle_witness",),
        exact_verifier="ray1 ⊂ plane1, ray2 ⊂ plane2, ray1 ⟂ edge, ray2 ⟂ edge, cos_sq(ray1,ray2)==cos_sq(plane1,plane2)",
        degeneracy_checks=("DEGENERATE_PARALLEL_NO_INTERSECTION", "IMPOSSIBLE_PERPENDICULARITY"),
        estimated_cost=1.7,
        visualization_semantics={"action_hint": "CONSTRUCT_AUXILIARY", "marker": "dihedral_angle"},
        registry_backing="KERNEL_PRIMITIVE_MISSING_CONTRACT",
        executor=_exec_construct_dihedral_linear_angle,
    ),
    "op.deduce_parallel_line_plane_transfer": OperatorSpec(
        operator_id="op.deduce_parallel_line_plane_transfer",
        category="relation",
        input_types=("line3", "plane3", "point3"),
        preconditions=("parallel_line_plane(line, plane)", "point_on_line(sample_point, line)", "not point_on_plane(sample_point, plane)"),
        applicable_object_types=("line3", "plane3", "point3"),
        output_types=("relation",),
        derived_relationships=("parallel_line_plane", "distance_transfer_line_to_point"),
        exact_verifier="normal_dot_dir==0 and sample_point off plane",
        degeneracy_checks=("DEGENERATE_CONTAINED_INFINITE_INTERSECTION", "IMPOSSIBLE_PERPENDICULARITY"),
        estimated_cost=0.5,
        visualization_semantics={"action_hint": "ESTABLISH_RELATION", "theorem": "parallel_distance_transfer"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_deduce_parallel_line_plane_transfer,
    ),
    "op.deduce_planar_perp_from_perp_plane": OperatorSpec(
        operator_id="op.deduce_planar_perp_from_perp_plane",
        category="relation",
        input_types=("line3", "line3", "plane3"),
        preconditions=("perp_line_plane(perp_line, host_plane)", "line_in_plane(line_in_plane, host_plane)"),
        applicable_object_types=("line3", "plane3"),
        output_types=("relation",),
        derived_relationships=("perp_lines",),
        exact_verifier="exact Gram perp_line_plane + dot(perp_line, line_in_plane)==0",
        degeneracy_checks=("IMPOSSIBLE_PERPENDICULARITY",),
        estimated_cost=0.35,
        visualization_semantics={"action_hint": "ESTABLISH_RELATION", "theorem": "line_perp_plane_implies_perp_line"},
        registry_backing="PROTOTYPE_DEDUCTIVE_COMPOSITION",
        executor=_exec_deduce_planar_perp_from_perp_plane,
    ),
}


def execute_operator(
    operator_id: str,
    inputs: dict[str, Any],
    params: dict[str, Any] | None,
    chart_metric: M.Metric | None,
) -> dict[str, Any]:
    spec = OPERATOR_SPECS.get(operator_id)
    if spec is None:
        raise VerificationError("UNSUPPORTED_OPERATOR", "L0", f"Unknown operator {operator_id!r}.")
    return spec.executor(inputs, params or {}, chart_metric)


# ---------------------------------------------------------------------------
# Witness-Enforcing Goal Evaluation (L3) — Never Evaluates Unwitnessed Goals
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoalSpec:
    """Explicit structured goal for dynamic planner (independent of oracle answer)."""

    goal_kind: str
    # Supported kinds:
    # "distance_point_plane", "distance_point_line", "distance_line_plane",
    # "distance_skew_lines", "point_distance", "angle_line_plane", "angle_lines",
    # "angle_plane_plane", "segment_length", "polygon_area",
    # "section_area", "solid_volume", "construct_point", "unsupported_goal"
    operands: dict[str, Any]
    length_unit: str = "a"

    def to_dict(self) -> dict[str, Any]:
        return {"goal_kind": self.goal_kind, "operands": _json_safe(self.operands), "length_unit": self.length_unit}


def evaluate_goal_if_witnessed(
    goal: GoalSpec,
    *,
    points_by_id: dict[str, E.Point3],
    lines_by_id: dict[str, E.Line3],
    planes_by_id: dict[str, E.Plane3],
    segments_by_id: dict[str, E.Segment3],
    sections_by_id: dict[str, S.Section],
    relations: set[tuple[str, tuple[str, ...]]],
    key_to_ids: dict[str, list[str]],
    chart_metric: M.Metric | None,
) -> dict[str, Any] | None:
    """Return L3 exact verification dict ONLY when the full geometric witness exists in state; else `None`."""

    gk = goal.goal_kind
    ops = goal.operands
    unit = goal.length_unit

    def _resolve_point(ref: Any) -> tuple[str, E.Point3] | None:
        if isinstance(ref, str) and ref in points_by_id:
            return ref, points_by_id[ref]
        return None

    def _resolve_line(ref: Any) -> E.Line3 | None:
        if isinstance(ref, str) and ref in lines_by_id:
            return lines_by_id[ref]
        if isinstance(ref, (list, tuple)) and len(ref) == 2:
            p1, p2 = _resolve_point(ref[0]), _resolve_point(ref[1])
            if p1 and p2 and p1[1] != p2[1]:
                return E.Line3.through(p1[1], p2[1])
        return None

    def _resolve_plane(ref: Any) -> E.Plane3 | None:
        if isinstance(ref, str) and ref in planes_by_id:
            return planes_by_id[ref]
        if isinstance(ref, (list, tuple)) and len(ref) >= 3:
            pts = [_resolve_point(x) for x in ref[:3]]
            if all(pts):
                try:
                    return E.Plane3.through(pts[0][1], pts[1][1], pts[2][1])
                except E.GeometryError:
                    return None
        return None

    with M.using(chart_metric):
        if gk == "point_distance":
            p1 = _resolve_point(ops.get("a"))
            p2 = _resolve_point(ops.get("b"))
            if not p1 or not p2:
                return None
            if p1[1] == p2[1]:
                pk = canonical_point_key(p1[1])
                return {
                    "witness_verified": True,
                    "coincident_zero_distance": True,
                    "witness_keys": [pk],
                    "witness_object_ids": list(dict.fromkeys([p1[0], p2[0]])),
                    "answer": "0",
                    "answer_exact": {"text": "0", "coef": "0", "dim": 1, "unit": unit},
                }
            seg_k = canonical_segment_key(E.Segment3.between(p1[1], p2[1]))
            if not any(canonical_segment_key(seg) == seg_k for seg in segments_by_id.values()):
                return None
            d2 = MS.distance_sq(p1[1], p2[1])
            ans = format_exact_unit_answer(MS.sqrt_rational(d2), unit=unit, dim=1)
            return {"witness_verified": True, "witness_keys": [seg_k], "answer": ans["text"], "answer_exact": ans}

        if gk == "segment_length":
            p1 = _resolve_point(ops.get("a"))
            p2 = _resolve_point(ops.get("b"))
            if not p1 or not p2:
                return None
            if p1[1] == p2[1]:
                if ops.get("allow_zero_length") is True:
                    pk = canonical_point_key(p1[1])
                    return {
                        "witness_verified": True,
                        "coincident_zero_distance": True,
                        "witness_keys": [pk],
                        "witness_object_ids": list(dict.fromkeys([p1[0], p2[0]])),
                        "answer": "0",
                        "answer_exact": {"text": "0", "coef": "0", "dim": 1, "unit": unit},
                    }
                # Non-degenerate segment construction explicitly excludes coincident endpoints.
                return None
            # Require constructed segment connecting a and b (either given solid edge or op.connect_segment)
            seg_k = canonical_segment_key(E.Segment3.between(p1[1], p2[1]))
            if not any(canonical_segment_key(seg) == seg_k for seg in segments_by_id.values()):
                return None
            d2 = MS.distance_sq(p1[1], p2[1])
            ans = format_exact_unit_answer(MS.sqrt_rational(d2), unit=unit, dim=1)
            return {"witness_verified": True, "witness_keys": [seg_k], "answer": ans["text"], "answer_exact": ans}

        if gk == "construct_point":
            target_id = ops.get("target_object_id")
            if isinstance(target_id, str) and target_id in points_by_id:
                pt = points_by_id[target_id]
                pt_k = canonical_point_key(pt)
                return {
                    "witness_verified": True,
                    "witness_keys": [pt_k],
                    "answer": f"{target_id}",
                    "answer_exact": {"text": target_id, "xyz": [str(pt.x), str(pt.y), str(pt.z)], "dim": 0, "unit": ""},
                }
            return None

        if gk == "distance_point_plane":
            p = _resolve_point(ops.get("point"))
            pl = _resolve_plane(ops.get("plane"))
            if not p or not pl:
                return None
            pk = canonical_point_key(p[1])
            plk = canonical_plane_key(pl)
            if pl.signed_eval(p[1]) == 0:
                return {
                    "witness_verified": True,
                    "witness_keys": [pk, plk],
                    "answer": "0",
                    "answer_exact": {"text": "0", "coef": "0", "dim": 1, "unit": unit},
                }
            # Must have explicit witness relation ("perp_point_plane_witness", (pk, plk, foot_k))
            feet = [rel[1][2] for rel in relations if rel[0] == "perp_point_plane_witness" and rel[1][0] == pk and rel[1][1] == plk]
            if not feet:
                return None
            fk = feet[0]
            foot_id = (key_to_ids.get(fk) or [None])[0]
            if not foot_id or foot_id not in points_by_id:
                return None
            d2 = MS.distance_sq(p[1], points_by_id[foot_id])
            d2_ref = MS.distance_sq_point_plane(p[1], pl)
            if d2 != d2_ref:
                return None
            seg_k = canonical_segment_key(E.Segment3.between(p[1], points_by_id[foot_id]))
            witness_keys = [pk, plk, fk]
            if any(canonical_segment_key(s) == seg_k for s in segments_by_id.values()):
                witness_keys.append(seg_k)
            ans = format_exact_unit_answer(MS.sqrt_rational(d2), unit=unit, dim=1)
            return {
                "witness_verified": True,
                "witness_keys": witness_keys,
                "witness_object_ids": [foot_id],
                "answer": ans["text"],
                "answer_exact": ans,
            }

        if gk == "distance_point_line":
            p = _resolve_point(ops.get("point"))
            ln = _resolve_line(ops.get("line"))
            if not p or not ln:
                return None
            pk, lnk = canonical_point_key(p[1]), canonical_line_key(ln)
            if MS.distance_sq_point_line(p[1], ln) == 0:
                return {
                    "witness_verified": True,
                    "witness_keys": [pk, lnk],
                    "answer": "0",
                    "answer_exact": {"text": "0", "coef": "0", "dim": 1, "unit": unit},
                }
            feet = [rel[1][2] for rel in relations if rel[0] == "perp_point_line_witness" and rel[1][0] == pk and rel[1][1] == lnk]
            if not feet:
                return None
            fk = feet[0]
            foot_id = (key_to_ids.get(fk) or [None])[0]
            if not foot_id or foot_id not in points_by_id:
                return None
            d2 = MS.distance_sq(p[1], points_by_id[foot_id])
            if d2 != MS.distance_sq_point_line(p[1], ln):
                return None
            seg_k = canonical_segment_key(E.Segment3.between(p[1], points_by_id[foot_id]))
            witness_keys = [pk, lnk, fk]
            if any(canonical_segment_key(s) == seg_k for s in segments_by_id.values()):
                witness_keys.append(seg_k)
            ans = format_exact_unit_answer(MS.sqrt_rational(d2), unit=unit, dim=1)
            return {
                "witness_verified": True,
                "witness_keys": witness_keys,
                "witness_object_ids": [foot_id],
                "answer": ans["text"],
                "answer_exact": ans,
            }

        if gk == "distance_line_plane":
            ln = _resolve_line(ops.get("line"))
            pl = _resolve_plane(ops.get("plane"))
            if not ln or not pl:
                return None
            lnk, plk = canonical_line_key(ln), canonical_plane_key(pl)
            transfers = [rel[1][2] for rel in relations if rel[0] == "distance_transfer_line_to_point" and rel[1][0] == lnk and rel[1][1] == plk]
            for pk in transfers:
                feet = [rel[1][2] for rel in relations if rel[0] == "perp_point_plane_witness" and rel[1][0] == pk and rel[1][1] == plk]
                if feet:
                    pt_id = (key_to_ids.get(pk) or [None])[0]
                    foot_id = (key_to_ids.get(feet[0]) or [None])[0]
                    if pt_id in points_by_id and foot_id in points_by_id:
                        d2 = MS.distance_sq(points_by_id[pt_id], points_by_id[foot_id])
                        if d2 == MS.distance_sq_line_plane(ln, pl):
                            ans = format_exact_unit_answer(MS.sqrt_rational(d2), unit=unit, dim=1)
                            return {
                                "witness_verified": True,
                                "witness_keys": [lnk, plk, pk, feet[0]],
                                "answer": ans["text"],
                                "answer_exact": ans,
                            }
            return None

        if gk == "distance_skew_lines":
            l1 = _resolve_line(ops.get("line1"))
            l2 = _resolve_line(ops.get("line2"))
            if not l1 or not l2:
                return None
            k1, k2 = canonical_line_key(l1), canonical_line_key(l2)
            pair_sorted = tuple(sorted((k1, k2)))
            d2_ref = MS.distance_sq_skew_lines(l1, l2)
            # Way 1: direct common perpendicular witness
            for rel in relations:
                if rel[0] == "common_perpendicular_witness" and tuple(sorted((rel[1][0], rel[1][1]))) == pair_sorted:
                    ans = format_exact_unit_answer(MS.sqrt_rational(d2_ref), unit=unit, dim=1)
                    return {"witness_verified": True, "witness_keys": [k1, k2, rel[1][2]], "answer": ans["text"], "answer_exact": ans}
            # Way 2: auxiliary parallel plane R containing one line and parallel to the other + perpendicular foot onto R
            for host_k, par_k in ((k1, k2), (k2, k1)):
                planes_par = [
                    rel[1][1]
                    for rel in relations
                    if rel[0] == "parallel_line_plane" and rel[1][0] == par_k
                    and ("line_in_plane", (host_k, rel[1][1])) in relations
                ]
                for plk in planes_par:
                    for rel in relations:
                        if rel[0] == "perp_point_plane_witness" and rel[1][1] == plk:
                            pt_id = (key_to_ids.get(rel[1][0]) or [None])[0]
                            foot_id = (key_to_ids.get(rel[1][2]) or [None])[0]
                            if pt_id in points_by_id and foot_id in points_by_id:
                                d2 = MS.distance_sq(points_by_id[pt_id], points_by_id[foot_id])
                                if d2 == d2_ref:
                                    ans = format_exact_unit_answer(MS.sqrt_rational(d2), unit=unit, dim=1)
                                    return {
                                        "witness_verified": True,
                                        "witness_keys": [k1, k2, plk, rel[1][0], rel[1][2]],
                                        "answer": ans["text"],
                                        "answer_exact": ans,
                                    }
            return None

        if gk == "angle_line_plane":
            ln = _resolve_line(ops.get("line"))
            pl = _resolve_plane(ops.get("plane"))
            if not ln or not pl:
                return None
            lnk, plk = canonical_line_key(ln), canonical_plane_key(pl)
            sin_sq = MS.sin_sq_line_plane(ln, pl)
            if sin_sq == 0 or sin_sq == 1:
                # Special exact boundary angles (0 deg parallel/contained or 90 deg perpendicular)
                deg_s = "0°" if sin_sq == 0 else "90°"
                has_rel = (
                    (("parallel_line_plane", (lnk, plk)) in relations)
                    or (("perp_line_plane", (lnk, plk)) in relations)
                )
                if not has_rel:
                    return None
                return {"witness_verified": True, "witness_keys": [lnk, plk], "answer": deg_s, "answer_exact": {"text": deg_s, "dim": 0, "unit": ""}}
            meets = [rel[1][2] for rel in relations if rel[0] == "line_plane_intersection_witness" and rel[1][0] == lnk and rel[1][1] == plk]
            feet = [rel[1] for rel in relations if rel[0] == "perp_point_plane_witness" and rel[1][1] == plk]
            if not meets or not feet:
                return None
            # Require projected line (intersection point, foot) constructed as a line or segment witness
            meet_id = (key_to_ids.get(meets[0]) or [None])[0]
            for src_pk, _, fk in feet:
                src_id = (key_to_ids.get(src_pk) or [None])[0]
                foot_id = (key_to_ids.get(fk) or [None])[0]
                if src_id and foot_id and meet_id and src_pk != meets[0]:
                    # Verify src_pt lies on ln and projection segment exists
                    if MS.distance_sq_point_line(points_by_id[src_id], ln) == 0:
                        proj_seg_k = canonical_segment_key(E.Segment3.between(points_by_id[meet_id], points_by_id[foot_id]))
                        proj_ln_k = canonical_line_key(E.Line3.through(points_by_id[meet_id], points_by_id[foot_id]))
                        matched_seg = any(canonical_segment_key(s) == proj_seg_k for s in segments_by_id.values())
                        matched_ln = any(canonical_line_key(l) == proj_ln_k for l in lines_by_id.values())
                        if matched_seg or matched_ln:
                            cos_sq = MS.cos_sq_line_plane(ln, pl)
                            ans = _format_angle_answer(cos_sq, mode=ops.get("output_mode", "cos_or_deg"))
                            wkeys = [lnk, plk, meets[0], fk]
                            if matched_seg:
                                wkeys.append(proj_seg_k)
                            if matched_ln:
                                wkeys.append(proj_ln_k)
                            return {"witness_verified": True, "witness_keys": wkeys, "answer": ans, "answer_exact": {"text": ans, "cos_sq": _fmt_frac(cos_sq), "dim": 0, "unit": ""}}
            return None

        if gk == "angle_lines":
            l1 = _resolve_line(ops.get("line1"))
            l2 = _resolve_line(ops.get("line2"))
            if not l1 or not l2:
                return None
            k1, k2 = canonical_line_key(l1), canonical_line_key(l2)
            # Either lines already intersect directly, or a constructed parallel line intersects the other
            cand_pairs: list[tuple[E.Line3, E.Line3, list[str]]] = [(l1, l2, [k1, k2])]
            for rel in relations:
                if rel[0] == "parallel_lines":
                    a_k, b_k = rel[1]
                    if b_k == k1:
                        id_a = (key_to_ids.get(a_k) or [None])[0]
                        if id_a in lines_by_id:
                            cand_pairs.append((lines_by_id[id_a], l2, [k1, k2, a_k]))
                    elif b_k == k2:
                        id_a = (key_to_ids.get(a_k) or [None])[0]
                        if id_a in lines_by_id:
                            cand_pairs.append((l1, lines_by_id[id_a], [k1, k2, a_k]))
            cos_sq = MS.cos_sq_between_lines(l1, l2)
            for la, lb, wk in cand_pairs:
                if la.direction.cross(lb.direction).is_zero():
                    ans = "0°"
                    return {"witness_verified": True, "witness_keys": wk, "answer": ans, "answer_exact": {"text": ans, "cos_sq": "1", "dim": 0, "unit": ""}}
                if (lb.point - la.point).dot(la.direction.cross(lb.direction)) == 0:
                    # Intersecting! Wait: require witness intersection point if constructed, or given shared vertex in points
                    try:
                        ipt = K.intersect_line_line(la, lb)
                        if canonical_point_key(ipt) in key_to_ids:
                            ans = _format_angle_answer(cos_sq, mode=ops.get("output_mode", "cos_or_deg"))
                            return {"witness_verified": True, "witness_keys": [*wk, canonical_point_key(ipt)], "answer": ans, "answer_exact": {"text": ans, "cos_sq": _fmt_frac(cos_sq), "dim": 0, "unit": ""}}
                    except E.GeometryError:
                        pass
            return None

        if gk == "angle_plane_plane":
            p1 = _resolve_plane(ops.get("plane1"))
            p2 = _resolve_plane(ops.get("plane2"))
            if not p1 or not p2:
                return None
            pk1, pk2 = canonical_plane_key(p1), canonical_plane_key(p2)
            cos_sq = MS.cos_sq_between_planes(p1, p2)
            # Way 1: Explicit dihedral linear angle witness (`op.construct_dihedral_linear_angle`)
            for rel in relations:
                if rel[0] == "dihedral_linear_angle_witness" and tuple(sorted((rel[1][0], rel[1][1]))) == tuple(sorted((pk1, pk2))):
                    ans = _format_angle_answer(cos_sq, mode=ops.get("output_mode", "cos_or_deg"))
                    return {"witness_verified": True, "witness_keys": list(rel[1]), "answer": ans, "answer_exact": {"text": ans, "cos_sq": _fmt_frac(cos_sq), "dim": 0, "unit": ""}}
            # Way 2: Planar altitude triangle witness (both planes share an edge, and perpendicular segments/rays from an anchor are constructed)
            edges = [rel[1][2] for rel in relations if rel[0] == "planes_intersection_line" and tuple(sorted((rel[1][0], rel[1][1]))) == tuple(sorted((pk1, pk2)))]
            if edges:
                ek = edges[0]
                perp_feet = [rel[1][2] for rel in relations if rel[0] == "perp_point_line_witness" and rel[1][1] == ek]
                # If a foot M on edge Δ exists AND a second point on either plane has a perpendicular plane/line to Δ, accept as alternate altitude-plane witness
                plane_perps = [
                    rel[1][1]
                    for rel in relations
                    if rel[0] == "perp_line_plane" and rel[1][0] == ek
                ]
                if perp_feet and plane_perps:
                    ans = _format_angle_answer(cos_sq, mode=ops.get("output_mode", "cos_or_deg"))
                    return {"witness_verified": True, "witness_keys": [pk1, pk2, ek, perp_feet[0], plane_perps[0]], "answer": ans, "answer_exact": {"text": ans, "cos_sq": _fmt_frac(cos_sq), "dim": 0, "unit": ""}}
            return None

        if gk == "polygon_area":
            pts = [_resolve_point(x) for x in (ops.get("points") or ())]
            if len(pts) < 3 or not all(pts):
                return None
            # Require all consecutive perimeter segments present
            verts = [p[1] for p in pts]
            seg_keys = []
            for i in range(len(verts)):
                sk = canonical_segment_key(E.Segment3.between(verts[i], verts[(i + 1) % len(verts)]))
                if not any(canonical_segment_key(s) == sk for s in segments_by_id.values()):
                    return None
                seg_keys.append(sk)
            area_ex = MS.area_polygon(verts)
            ans = format_exact_unit_answer(area_ex, unit=unit, dim=2)
            return {"witness_verified": True, "witness_keys": seg_keys, "answer": ans["text"], "answer_exact": ans}

        if gk == "section_area":
            pl = _resolve_plane(ops.get("plane"))
            if not pl:
                return None
            plk = canonical_plane_key(pl)
            for sid, sec in sections_by_id.items():
                if all(pl.signed_eval(v) == 0 for v in sec.polygon):
                    area_ex = MS.area_section(sec)
                    ans = format_exact_unit_answer(area_ex, unit=unit, dim=2)
                    return {"witness_verified": True, "witness_keys": [plk, canonical_polygon_key(sec.polygon, "sec")], "answer": ans["text"], "answer_exact": ans}
            return None

        if gk == "solid_volume":
            apex = _resolve_point(ops.get("apex"))
            base_pts = [_resolve_point(x) for x in (ops.get("base") or ())]
            if not apex or len(base_pts) < 3 or not all(base_pts):
                return None
            base_pl = _resolve_plane(ops.get("base")[:3])
            if not base_pl:
                return None
            if any(base_pl.signed_eval(p[1]) != 0 for p in base_pts):
                return None
            ak, plk = canonical_point_key(apex[1]), canonical_plane_key(base_pl)
            if base_pl.signed_eval(apex[1]) == 0:
                return None
            # Require altitude foot witness from apex onto base plane!
            feet = [rel[1][2] for rel in relations if rel[0] == "perp_point_plane_witness" and rel[1][0] == ak and rel[1][1] == plk]
            if not feet:
                return None
            base_v = [p[1] for p in base_pts]
            signed_sum = Fraction(0)
            for i in range(1, len(base_v) - 1):
                signed_sum += MS.det3(base_v[0] - apex[1], base_v[i] - apex[1], base_v[i + 1] - apex[1])
            vol_frac = abs(signed_sum) / 6
            vol_sq = vol_frac * vol_frac * M.volume_det_factor_sq()
            vol_ex = MS.sqrt_rational(vol_sq)
            ans = format_exact_unit_answer(vol_ex, unit=unit, dim=3)
            return {"witness_verified": True, "witness_keys": [ak, plk, feet[0]], "answer": ans["text"], "answer_exact": ans}

    return None


def _format_angle_answer(cos_sq: Fraction, mode: str = "cos_or_deg") -> str:
    special = {
        Fraction(1): "0°",
        Fraction(3, 4): "30°",
        Fraction(1, 2): "45°",
        Fraction(1, 4): "60°",
        Fraction(0): "90°",
    }
    if cos_sq in special:
        return special[cos_sq]
    if mode == "cos":
        return f"cos={R.display(MS.sqrt_rational(cos_sq))}"
    return f"cos²={_fmt_frac(cos_sq)}"


def export_operator_inventory() -> list[dict[str, Any]]:
    return [OPERATOR_SPECS[k].to_metadata_dict() for k in sorted(OPERATOR_SPECS)]
