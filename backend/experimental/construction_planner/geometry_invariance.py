# -*- coding: utf-8 -*-
"""Geometric invariance & coordinate/chart transformation utilities (`AXO CONSTRUCTION /2`, Phase E).

Supports exact rational transformations over `InitialGeometryFrame`, `PendingConstruction`,
and `GoalSpec`:
1. Vertex relabeling (`relabel_frame_and_goal`)
2. Independent pending construction order permutation (`permute_pending_frame`)
3. Rigid coordinate translation (`translate_frame`)
4. Metric-preserving change of basis / orthonormal rotation `SO(3, Q)` and general `GL(3, Q)`
   with exact Gram tensor covariance `G' = A^-T * G * A^-1` (`transform_basis_frame`)
5. Metric-preserving geometric reflection across a coordinate/rational plane (`reflect_frame`)
6. Length unit / coordinate scaling (`scale_frame`)
7. Structural isomorphism signature of `ConstructionProofGraph` invariant to node IDs & point labels.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Any

from app.simulation.geometry import exact as E
from app.simulation.geometry import metric as M
from app.simulation.geometry import section as S

from .construction_graph import ConstructionProofGraph
from .construction_objects import (
    _fmt_frac,
    canonical_line_key,
    canonical_plane_key,
    canonical_point_key,
    canonical_polygon_key,
    canonical_segment_key,
)
from .construction_operators import GoalSpec
from .construction_state import InitialGeometryFrame, PendingConstruction


def _invert_3x3(mat: tuple[tuple[Fraction, Fraction, Fraction], ...]) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    a = [[Fraction(x) for x in row] for row in mat]
    inv = [[Fraction(1 if i == j else 0) for j in range(3)] for i in range(3)]
    for col in range(3):
        piv = next((r for r in range(col, 3) if a[r][col] != 0), None)
        if piv is None:
            raise ValueError("Basis matrix is singular; cannot invert in GL(3, Q).")
        if piv != col:
            a[col], a[piv] = a[piv], a[col]
            inv[col], inv[piv] = inv[piv], inv[col]
        p = a[col][col]
        a[col] = [x / p for x in a[col]]
        inv[col] = [x / p for x in inv[col]]
        for r in range(3):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                a[r] = [a[r][c] - f * a[col][c] for c in range(3)]
                inv[r] = [inv[r][c] - f * inv[col][c] for c in range(3)]
    return tuple(tuple(row) for row in inv)


def _mat_mul_3x3(
    a: tuple[tuple[Fraction, ...], ...],
    b: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))  # type: ignore[misc]
        for i in range(3)
    )


def _transpose_3x3(m: tuple[tuple[Fraction, ...], ...]) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))  # type: ignore[misc]


def _mat_vec(m: tuple[tuple[Fraction, ...], ...], v: E.Vec3) -> E.Vec3:
    return E.Vec3(
        m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z,
        m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z,
        m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z,
    )


def _rebuild_frame_geometry(
    frame: InitialGeometryFrame,
    *,
    new_points: dict[str, E.Point3],
    new_metric: M.Metric,
    new_poly: S.Polyhedron | None,
    suffix: str,
    new_pending: tuple[PendingConstruction, ...] | None = None,
    new_length_unit: str | None = None,
) -> InitialGeometryFrame:
    """Rebuild lines, segments, planes, and exact `given_relations` from transformed points & metric."""
    new_segs: dict[str, E.Segment3] = {}
    new_lns: dict[str, E.Line3] = {}
    new_pls: dict[str, E.Plane3] = {}

    with M.using(new_metric):
        for sid, seg in frame.segments.items():
            # Map by point names if sid is `seg_U_V`
            pts_pair = _match_point_ids(frame.points, seg.point_a, seg.point_b)
            if pts_pair:
                u, v = pts_pair
                new_segs[sid] = E.Segment3.between(new_points[u], new_points[v])
        for lid, ln in frame.lines.items():
            pts_pair = _find_collinear_pair(frame.points, ln)
            if pts_pair:
                u, v = pts_pair
                new_lns[lid] = E.Line3.through(new_points[u], new_points[v])
        for plid, pl in frame.planes.items():
            pts_triple = _find_plane_triple(frame.points, pl)
            if pts_triple:
                a, b, c = pts_triple
                new_pls[plid] = E.Plane3.through(new_points[a], new_points[b], new_points[c])

        rels: list[tuple[str, tuple[str, ...], bool]] = []
        for pid, pval in new_points.items():
            pk = canonical_point_key(pval)
            for lid, ln in new_lns.items():
                if (pval - ln.point).cross(ln.direction).is_zero():
                    rels.append(("point_on_line", (pk, canonical_line_key(ln)), False))
            for plid, pl in new_pls.items():
                if pl.signed_eval(pval) == 0:
                    rels.append(("point_on_plane", (pk, canonical_plane_key(pl)), False))
        for lid, ln in new_lns.items():
            lk = canonical_line_key(ln)
            for plid, pl in new_pls.items():
                plk = canonical_plane_key(pl)
                if pl.signed_eval(ln.point) == 0 and pl.normal.dot(ln.direction) == 0:
                    rels.append(("line_in_plane", (lk, plk), False))
                if M.plane_covector(ln.direction).cross(pl.normal).is_zero():
                    rels.append(("perp_line_plane", (lk, plk), False))
                    for ep, pval in new_points.items():
                        if (pval - ln.point).cross(ln.direction).is_zero() and pl.signed_eval(pval) == 0:
                            fk = canonical_point_key(pval)
                            for other, oval in new_points.items():
                                if other != ep and (oval - ln.point).cross(ln.direction).is_zero() and pl.signed_eval(oval) != 0:
                                    rels.append(("perp_point_plane_witness", (canonical_point_key(oval), plk, fk), False))
        ln_items = sorted(new_lns.items())
        for i, (_, l1) in enumerate(ln_items):
            for _, l2 in ln_items[i + 1 :]:
                if M.dot(l1.direction, l2.direction) == 0:
                    rels.append(("perp_lines", (canonical_line_key(l1), canonical_line_key(l2)), True))

    return InitialGeometryFrame(
        case_id=f"{frame.case_id}__{suffix}",
        problem_text=frame.problem_text,
        length_unit=new_length_unit or frame.length_unit,
        chart_metric=new_metric,
        chart_metric_strs=tuple(tuple(_fmt_frac(x) for x in row) for row in new_metric.g),
        points=new_points,
        lines=new_lns,
        segments=new_segs,
        planes=new_pls,
        polyhedron=new_poly,
        given_relations=tuple(dict.fromkeys(rels)),
        source_fact_refs=frame.source_fact_refs,
        pending_constructions=frame.pending_constructions if new_pending is None else new_pending,
        error_code=frame.error_code,
        error_detail=frame.error_detail,
    )


def _match_point_ids(points: dict[str, E.Point3], a: E.Point3, b: E.Point3) -> tuple[str, str] | None:
    id_a = next((pid for pid, p in sorted(points.items()) if p == a), None)
    id_b = next((pid for pid, p in sorted(points.items()) if p == b), None)
    if id_a and id_b and id_a != id_b:
        return id_a, id_b
    return None


def _find_collinear_pair(points: dict[str, E.Point3], ln: E.Line3) -> tuple[str, str] | None:
    on = [pid for pid, p in sorted(points.items()) if (p - ln.point).cross(ln.direction).is_zero()]
    for i in range(len(on)):
        for j in range(i + 1, len(on)):
            if points[on[i]] != points[on[j]]:
                return on[i], on[j]
    return None


def _find_plane_triple(points: dict[str, E.Point3], pl: E.Plane3) -> tuple[str, str, str] | None:
    on = [pid for pid, p in sorted(points.items()) if pl.signed_eval(p) == 0]
    for i in range(len(on)):
        for j in range(i + 1, len(on)):
            for k in range(j + 1, len(on)):
                if not (points[on[j]] - points[on[i]]).cross(points[on[k]] - points[on[i]]).is_zero():
                    return on[i], on[j], on[k]
    return None


def translate_frame(frame: InitialGeometryFrame, offset: E.Vec3) -> InitialGeometryFrame:
    """Rigid affine translation `P -> P + offset` (chart metric unchanged)."""
    new_points = {pid: p + offset for pid, p in frame.points.items()}
    new_poly = (
        S.Polyhedron(vertices=tuple(v + offset for v in frame.polyhedron.vertices), faces=frame.polyhedron.faces)
        if frame.polyhedron is not None
        else None
    )
    return _rebuild_frame_geometry(frame, new_points=new_points, new_metric=frame.chart_metric, new_poly=new_poly, suffix="translated")


def transform_basis_frame(
    frame: InitialGeometryFrame,
    matrix_a: tuple[tuple[Fraction, Fraction, Fraction], ...],
    *,
    suffix: str = "basis",
) -> InitialGeometryFrame:
    """Apply linear transformation `P' = A * P` and metric covariance `G' = A^-T * G * A^-1`.

    Preserves every exact distance, angle, area, volume, and orthogonality certificate across Q^3!
    When `A` is orthonormal in `G = I` (e.g. rational `SO(3, Q)` rotation or reflection), `G' = G`.
    """
    a_inv = _invert_3x3(matrix_a)
    a_inv_t = _transpose_3x3(a_inv)
    g_raw = tuple(tuple(Fraction(x) for x in r) for r in frame.chart_metric.g)
    g_new = _mat_mul_3x3(_mat_mul_3x3(a_inv_t, g_raw), a_inv)
    new_metric = M.Metric(g=g_new)
    new_points = {pid: _mat_vec(matrix_a, p) for pid, p in frame.points.items()}
    new_poly = (
        S.Polyhedron(vertices=tuple(_mat_vec(matrix_a, v) for v in frame.polyhedron.vertices), faces=frame.polyhedron.faces)
        if frame.polyhedron is not None
        else None
    )
    return _rebuild_frame_geometry(frame, new_points=new_points, new_metric=new_metric, new_poly=new_poly, suffix=suffix)


def scale_frame(
    frame: InitialGeometryFrame,
    goal_spec: GoalSpec,
    factor: Fraction,
    *,
    new_unit: str | None = None,
) -> tuple[InitialGeometryFrame, GoalSpec]:
    """Scale coordinates by exact rational `factor > 0` (metric unchanged)."""
    if factor <= 0:
        raise ValueError("Scale factor must be positive.")
    scaled_pts = {pid: p.scale(factor) for pid, p in frame.points.items()}
    new_poly = (
        S.Polyhedron(vertices=tuple(v.scale(factor) for v in frame.polyhedron.vertices), faces=frame.polyhedron.faces)
        if frame.polyhedron is not None
        else None
    )
    f2 = _rebuild_frame_geometry(
        frame,
        new_points=scaled_pts,
        new_metric=frame.chart_metric,
        new_poly=new_poly,
        suffix=f"scale_{_fmt_frac(factor).replace('/', '_')}",
        new_length_unit=new_unit or goal_spec.length_unit,
    )
    g2 = GoalSpec(goal_kind=goal_spec.goal_kind, operands=goal_spec.operands, length_unit=new_unit or goal_spec.length_unit)
    return f2, g2


def permute_pending_frame(frame: InitialGeometryFrame) -> InitialGeometryFrame:
    """Reverse/permute independent pending constructions (`op(A), op(B)` order swap)."""
    return replace(frame, case_id=f"{frame.case_id}__perm", pending_constructions=tuple(reversed(frame.pending_constructions)))


def relabel_frame_and_goal(
    frame: InitialGeometryFrame,
    goal_spec: GoalSpec,
    mapping: dict[str, str],
) -> tuple[InitialGeometryFrame, GoalSpec]:
    """Bijectively relabel given vertex names across frame, segments/lines/planes, pending specs, and goal."""

    def _map_pt(x: str) -> str:
        return mapping.get(x, x)

    def _map_ref(ref: Any) -> Any:
        if isinstance(ref, str):
            if ref in mapping:
                return mapping[ref]
            if ref.startswith("seg_"):
                parts = ref[4:].split("_")
                return "seg_" + "_".join(_map_pt(p) for p in parts)
            if ref.startswith("ln_"):
                parts = ref[3:].split("_")
                return "ln_" + "_".join(_map_pt(p) for p in parts)
            if ref.startswith(("day_", "mat_")):
                pfx, rest = ref[:4], ref[4:]
                return pfx + "".join(_map_pt(ch) for ch in rest)
            return ref
        if isinstance(ref, list):
            return [_map_ref(r) for r in ref]
        if isinstance(ref, tuple):
            return tuple(_map_ref(r) for r in ref)
        if isinstance(ref, dict):
            return {k: _map_ref(v) for k, v in ref.items()}
        return ref

    new_pts = {_map_pt(pid): p for pid, p in frame.points.items()}
    new_segs = {_map_ref(sid): seg for sid, seg in frame.segments.items()}
    new_lns = {_map_ref(lid): ln for lid, ln in frame.lines.items()}
    new_pls = {_map_ref(plid): pl for plid, pl in frame.planes.items()}
    new_pending = tuple(
        PendingConstruction(
            req_id=p.req_id,
            operator_id=p.operator_id,
            output_label=p.output_label,
            input_refs=_map_ref(p.input_refs),
            params=p.params,
            source_fact_ref=p.source_fact_ref,
            description=p.description,
        )
        for p in frame.pending_constructions
    )
    new_frame = InitialGeometryFrame(
        case_id=f"{frame.case_id}__relabeled",
        problem_text=frame.problem_text,
        length_unit=frame.length_unit,
        chart_metric=frame.chart_metric,
        chart_metric_strs=frame.chart_metric_strs,
        points=new_pts,
        lines=new_lns,
        segments=new_segs,
        planes=new_pls,
        polyhedron=frame.polyhedron,
        given_relations=frame.given_relations,
        source_fact_refs=frame.source_fact_refs,
        pending_constructions=new_pending,
        error_code=frame.error_code,
        error_detail=frame.error_detail,
    )
    new_goal = GoalSpec(goal_kind=goal_spec.goal_kind, operands=_map_ref(goal_spec.operands), length_unit=goal_spec.length_unit)
    return new_frame, new_goal


def graph_structural_isomorphism_signature(graph: ConstructionProofGraph) -> tuple[Any, ...]:
    """Coordinate-free & ID-free structural signature comparing two verified `ConstructionProofGraph`s.

    Two graphs differing only by vertex labels, coordinate rigid motion, or independent step ordering
    produce identical `(operator_multiset, node_type_counts, dependency_degree_multiset, aux_count)`.
    """
    node_types = tuple(sorted(n.node_type for n in graph.nodes if n.node_type != "GIVEN"))
    ops = tuple(sorted(n.producing_operation_id or "" for n in graph.nodes if n.node_type in ("CONSTRUCTION", "DERIVED_RELATION", "GOAL")))
    indegs = tuple(sorted(len(n.dependency_ids) for n in graph.nodes if n.node_type != "GIVEN"))
    aux_count = len([o for o in graph.objects.values() if o.origin == "AUXILIARY_CONSTRUCTION"])
    return (node_types, ops, indegs, aux_count)
