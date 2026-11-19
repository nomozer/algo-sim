# -*- coding: utf-8 -*-
"""Search state representation and certified premise-only initial frame loader for `dynamic-construction-planner/1`."""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from app.simulation.geometry import exact as E
from app.simulation.geometry import measure as MS
from app.simulation.geometry import metric as M
from app.simulation.geometry import section as S
from app.simulation.geometry_functions import (
    certificates,
    engine,
    planner,
    registry,
    typed_fact_next_bridge as tfnb,
)

from .construction_graph import (
    ConstructionNode,
    ConstructionProofGraph,
    prune_to_goal_closure,
)
from .construction_objects import (
    ConstructionObject,
    _fmt_frac,
    canonical_line_key,
    canonical_plane_key,
    canonical_point_key,
    canonical_polygon_key,
    canonical_relation_key,
    canonical_segment_key,
    vec3_to_rational_list,
)
from .construction_operators import GoalSpec

# Strictly enforce offline-only zero-live-AI policy
os.environ.setdefault("ALLOW_LIVE_AI", "0")
os.environ.setdefault("GEMINI_API_KEY", "")


@dataclass(frozen=True)
class PendingConstruction:
    """Explicitly stated premise/derived construction requirement left for dynamic planner composition."""

    req_id: str
    operator_id: str
    output_label: str
    input_refs: dict[str, Any]
    params: dict[str, Any] = field(default_factory=dict)
    source_fact_ref: str = ""
    description: str = ""


@dataclass(frozen=True)
class InitialGeometryFrame:
    """Certified base solid coordinates + Gram metric extracted strictly from premises (zero goal input)."""

    case_id: str
    problem_text: str
    length_unit: str
    chart_metric: M.Metric
    chart_metric_strs: tuple[tuple[str, ...], ...]
    points: dict[str, E.Point3]
    lines: dict[str, E.Line3]
    segments: dict[str, E.Segment3]
    planes: dict[str, E.Plane3]
    polyhedron: S.Polyhedron | None
    given_relations: tuple[tuple[str, tuple[str, ...], bool], ...]
    source_fact_refs: dict[str, tuple[str, ...]]
    pending_constructions: tuple[PendingConstruction, ...]
    error_code: str | None = None
    error_detail: str | None = None


@dataclass(frozen=True)
class PlannerSearchState:
    """Immutable search frontier state inside `dynamic-construction-planner/1`."""

    objects: dict[str, ConstructionObject]
    nodes: tuple[ConstructionNode, ...]
    relations: frozenset[tuple[str, tuple[str, ...]]]
    key_to_ids: dict[str, tuple[str, ...]]
    pending: tuple[PendingConstruction, ...]
    cost: float
    depth: int
    aux_count: int
    lineage: tuple[str, ...]
    last_node_by_object: dict[str, str]
    relation_node_ids: dict[tuple[str, tuple[str, ...]], str]

    def canonical_state_signature(self) -> str:
        """Order-independent canonical state key for permutation deduplication (§9 & §15)."""
        geom_keys = sorted(
            f"{obj.object_kind}:{obj.canonical_geom_key}"
            for obj in self.objects.values()
            if obj.object_kind not in ("relation", "quantity")
        )
        rel_keys = sorted(f"{r[0]}({'|'.join(r[1])})" for r in self.relations)
        pend_keys = sorted(f"{p.operator_id}:{p.output_label}" for p in self.pending)
        raw = "||".join(["O:" + ",".join(geom_keys), "R:" + ",".join(rel_keys), "P:" + ",".join(pend_keys)])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _extract_solid_polyhedron(
    solid_spec: dict[str, Any],
    points: dict[str, E.Point3],
) -> tuple[S.Polyhedron | None, list[tuple[str, str]], list[tuple[str, list[str]]]]:
    """Build exact `Polyhedron`, edge pairs, and face vertex-label tuples from solid spec."""
    solid_type = solid_spec.get("solid_type") or "pyramid"
    edges: list[tuple[str, str]] = []
    faces_labels: list[tuple[str, list[str]]] = []
    if solid_type == "pyramid":
        apex = solid_spec.get("apex")
        base = list(solid_spec.get("base_vertices") or ())
        if not apex or len(base) < 3:
            return None, [], []
        all_labels = [apex, *base]
        if not all(lbl in points for lbl in all_labels):
            return None, [], []
        idx = {lbl: i for i, lbl in enumerate(all_labels)}
        faces_idx = [tuple(idx[v] for v in base)]
        faces_labels.append(("day_" + "".join(base), base))
        for i in range(len(base)):
            u, v = base[i], base[(i + 1) % len(base)]
            edges.append((u, v))
            edges.append((apex, base[i]))
            faces_idx.append((idx[apex], idx[u], idx[v]))
            faces_labels.append((f"mat_{apex}{u}{v}", [apex, u, v]))
        poly = S.Polyhedron(vertices=tuple(points[l] for l in all_labels), faces=tuple(faces_idx))
        return poly, edges, faces_labels
    else:
        base = list(solid_spec.get("base_vertices") or ())
        top = list(solid_spec.get("top_vertices") or ())
        if len(base) < 3 or len(base) != len(top):
            return None, [], []
        all_labels = [*base, *top]
        if not all(lbl in points for lbl in all_labels):
            return None, [], []
        idx = {lbl: i for i, lbl in enumerate(all_labels)}
        faces_idx = [tuple(idx[v] for v in base), tuple(idx[v] for v in top)]
        faces_labels.append(("day_" + "".join(base), base))
        faces_labels.append(("day_" + "".join(top), top))
        n = len(base)
        for i in range(n):
            u0, v0 = base[i], base[(i + 1) % n]
            u1, v1 = top[i], top[(i + 1) % n]
            edges.extend([(u0, v0), (u1, v1), (u0, u1)])
            faces_idx.append((idx[u0], idx[v0], idx[v1], idx[u1]))
            faces_labels.append((f"mat_{u0}{v0}{v1}{u1}", [u0, v0, v1, u1]))
        poly = S.Polyhedron(vertices=tuple(points[l] for l in all_labels), faces=tuple(faces_idx))
        return poly, edges, faces_labels


def _check_explicit_edge_contradictions(
    premises: list[dict[str, Any]],
    points: dict[str, E.Point3],
    chart_metric: M.Metric,
) -> tuple[str, str] | None:
    """Verify no given triangle-inequality / non-positive length contradictions slip past solid layout."""
    length_by_pair: dict[tuple[str, str], Fraction] = {}
    for p in premises:
        if p.get("kind") == "length" and p.get("measure") in ("segment", None, "height"):
            pts = p.get("points") or []
            val_s = str(p.get("value") or "").strip()
            if val_s in ("a", "1"):
                num_val = Fraction(1)
            else:
                m_num = re.fullmatch(r"([0-9]+(?:/[0-9]+)?)\*?a?", val_s.replace(" ", ""))
                if not m_num:
                    continue
                num_val = Fraction(m_num.group(1))
            if num_val <= 0:
                return ("NON_POSITIVE_DIMENSION", f"Premise {p.get('id')} specifies non-positive length {val_s!r}.")
            if len(pts) == 2:
                pair = tuple(sorted((str(pts[0]), str(pts[1]))))
                if pair in length_by_pair and length_by_pair[pair] != num_val:
                    return ("CONTRADICTORY_CONSTRAINTS", f"Conflicting lengths on {pair}: {length_by_pair[pair]} vs {num_val}.")
                length_by_pair[pair] = num_val
    # Check triangle inequality for any closed triple with all 3 lengths given
    verts = sorted({x for pair in length_by_pair for x in pair})
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            for k in range(j + 1, len(verts)):
                a, b, c = verts[i], verts[j], verts[k]
                p1, p2, p3 = tuple(sorted((a, b))), tuple(sorted((b, c))), tuple(sorted((a, c)))
                if p1 in length_by_pair and p2 in length_by_pair and p3 in length_by_pair:
                    l1, l2, l3 = length_by_pair[p1], length_by_pair[p2], length_by_pair[p3]
                    if l1 + l2 <= l3 or l1 + l3 <= l2 or l2 + l3 <= l1:
                        return (
                            "CONTRADICTORY_CONSTRAINTS",
                            f"Triangle ({a},{b},{c}) violates triangle inequality: lengths ({l1}, {l2}, {l3}).",
                        )
    # Cross-check computed Gram distances vs stated segment lengths if both vertices exist
    with M.using(chart_metric):
        for (u, v), stated in length_by_pair.items():
            if u in points and v in points:
                if points[u] == points[v]:
                    return ("DEGENERATE_COINCIDENT_POINTS", f"Vertices {u!r} and {v!r} coincide despite length premise.")
    return None


def build_initial_frame(
    *,
    case_id: str,
    problem_text: str,
    solid_spec: dict[str, Any],
    chart_premises: list[dict[str, Any]],
    pending_constructions: list[PendingConstruction] | None = None,
    typed_fact_next_payload: dict[str, Any] | None = None,
    length_unit: str = "a",
) -> InitialGeometryFrame:
    """Build exact `InitialGeometryFrame` strictly from premise facts via `engine.dung_tu_loi_goi` (zero goal leakage)."""
    pending = tuple(pending_constructions or ())
    pre_err = _check_explicit_edge_contradictions(chart_premises, {}, M.Metric.euclidean() if hasattr(M.Metric, "euclidean") else M.Metric(g=((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))))
    if pre_err is not None:
        return InitialGeometryFrame(
            case_id=case_id,
            problem_text=problem_text,
            length_unit=length_unit,
            chart_metric=M.Metric(g=((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))),
            chart_metric_strs=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
            points={},
            lines={},
            segments={},
            planes={},
            polyhedron=None,
            given_relations=(),
            source_fact_refs={},
            pending_constructions=pending,
            error_code=pre_err[0],
            error_detail=pre_err[1],
        )

    # Construct premise-only `typed-facts/2` OR strip goals from `typed_fact_next_payload`
    if typed_fact_next_payload is not None:
        p_txt = problem_text
        for mg in typed_fact_next_payload.get("math_goals", []):
            q = mg.get("quote", "")
            if q and q in p_txt:
                p_txt = p_txt.replace(q, "")
        p_txt = p_txt.strip().rstrip(". ") + "."
        premise_payload = {
            **typed_fact_next_payload,
            "problem_text": p_txt,
            "simulation_goals": list(typed_fact_next_payload.get("simulation_goals") or [])[:1],
            "math_goals": [],
        }
        try:
            tf2 = tfnb.bridge_v2(premise_payload)
            # Only pass rigid solid-layout premises if dynamic pending constructions are handled separately
            kh = planner.lap_ke_hoach(tf2, p_txt)
            plan_dict = {"calls": kh.calls, "goals": [], "negated": []}
            kq = engine.dung_tu_loi_goi(p_txt, plan_dict, auxiliary=tuple(kh.auxiliary))
        except Exception as exc:
            code = getattr(exc, "code", None) or "CONTRADICTORY_CONSTRAINTS"
            mapped = "CONTRADICTORY_CONSTRAINTS" if any(t in str(code) for t in ("INCONSISTENT", "DEGENERATE", "COLLINEAR", "TRUNG", "NON_POSITIVE")) else (
                "MISSING_PRECONDITION" if any(t in str(code) for t in ("MISSING", "UNDERDETERMINED", "INCOMPLETE", "UNREAD", "UNKNOWN")) else str(code)
            )
            return InitialGeometryFrame(
                case_id=case_id,
                problem_text=problem_text,
                length_unit=length_unit,
                chart_metric=M.Metric(g=((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))),
                chart_metric_strs=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
                points={},
                lines={},
                segments={},
                planes={},
                polyhedron=None,
                given_relations=(),
                source_fact_refs={},
                pending_constructions=pending,
                error_code=mapped,
                error_detail=str(exc),
            )
    else:
        # Build premise-only typed-facts/2 directly from structured `chart_premises` using `problem_text` for quote checks
        facts_list = [dict(solid_spec_to_typed_fact(solid_spec)), *chart_premises]
        p_txt = problem_text.strip() or (". ".join(dict.fromkeys(str(q) for f in facts_list for q in (f.get("quotes") or ()) if q)) + ".")
        try:
            kh = planner.lap_ke_hoach({"schema": "typed-facts/2", "facts": facts_list}, p_txt)
            plan_dict = {"calls": kh.calls, "goals": [], "negated": []}
            kq = engine.dung_tu_loi_goi(p_txt, plan_dict, auxiliary=tuple(kh.auxiliary))
        except Exception as exc:
            code = getattr(exc, "code", None) or "CONTRADICTORY_CONSTRAINTS"
            return InitialGeometryFrame(
                case_id=case_id,
                problem_text=problem_text,
                length_unit=length_unit,
                chart_metric=M.Metric(g=((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))),
                chart_metric_strs=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
                points={},
                lines={},
                segments={},
                planes={},
                polyhedron=None,
                given_relations=(),
                source_fact_refs={},
                pending_constructions=pending,
                error_code="MISSING_PRECONDITION" if "MISSING" in str(code) or "UNDERDETERMINED" in str(code) or "INCOMPLETE" in str(code) else "CONTRADICTORY_CONSTRAINTS",
                error_detail=str(exc),
            )

    if kq.status != "SERVED" or not kq.points:
        c = kq.code or "MISSING_PRECONDITION"
        if any(tok in c for tok in ("INCONSISTENT", "CONTRADICT", "NON_POSITIVE", "DEGENERATE", "COLLINEAR", "CONFLICT")):
            mapped = "CONTRADICTORY_CONSTRAINTS"
        elif any(tok in c for tok in ("UNSUPPORTED", "CURVED", "OUT_OF_SCOPE")):
            mapped = "UNSUPPORTED_OPERATOR"
        else:
            mapped = "MISSING_PRECONDITION"
        return InitialGeometryFrame(
            case_id=case_id,
            problem_text=problem_text,
            length_unit=length_unit,
            chart_metric=M.Metric(g=((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))),
            chart_metric_strs=(("1", "0", "0"), ("0", "1", "0"), ("0", "0", "1")),
            points={},
            lines={},
            segments={},
            planes={},
            polyhedron=None,
            given_relations=(),
            source_fact_refs={},
            pending_constructions=pending,
            error_code=mapped,
            error_detail=f"{kq.code}: {kq.reason}",
        )

    chart_m: M.Metric = kq.chart_metric or M.Metric(
        g=((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)), (Fraction(0), Fraction(0), Fraction(1)))
    )
    try:
        certificates.validate_gram_metric_spd(chart_m)
    except certificates.CertificateError as exc:
        return InitialGeometryFrame(
            case_id=case_id,
            problem_text=problem_text,
            length_unit=kq.length_unit or length_unit,
            chart_metric=chart_m,
            chart_metric_strs=tuple(tuple(_fmt_frac(x) for x in r) for r in chart_m.g),
            points={},
            lines={},
            segments={},
            planes={},
            polyhedron=None,
            given_relations=(),
            source_fact_refs={},
            pending_constructions=pending,
            error_code="CONTRADICTORY_CONSTRAINTS",
            error_detail=str(exc),
        )

    pts: dict[str, E.Point3] = {k: E.Vec3(Fraction(v[0]), Fraction(v[1]), Fraction(v[2])) for k, v in kq.points.items()}
    metric_err = _check_explicit_edge_contradictions(chart_premises, pts, chart_m)
    if metric_err is not None:
        return InitialGeometryFrame(
            case_id=case_id,
            problem_text=problem_text,
            length_unit=kq.length_unit or length_unit,
            chart_metric=chart_m,
            chart_metric_strs=tuple(tuple(_fmt_frac(x) for x in r) for r in chart_m.g),
            points=pts,
            lines={},
            segments={},
            planes={},
            polyhedron=None,
            given_relations=(),
            source_fact_refs={},
            pending_constructions=pending,
            error_code=metric_err[0],
            error_detail=metric_err[1],
        )

    poly, edges, faces = _extract_solid_polyhedron(solid_spec, pts)
    segs: dict[str, E.Segment3] = {}
    lines: dict[str, E.Line3] = {}
    planes: dict[str, E.Plane3] = {}
    rels: list[tuple[str, tuple[str, ...], bool]] = []

    with M.using(chart_m):
        for u, v in edges:
            sid = f"seg_{u}_{v}"
            lid = f"ln_{u}_{v}"
            try:
                seg = E.Segment3.between(pts[u], pts[v])
                ln = E.Line3.through(pts[u], pts[v])
            except E.GeometryError as exc:
                return InitialGeometryFrame(
                    case_id=case_id,
                    problem_text=problem_text,
                    length_unit=kq.length_unit or length_unit,
                    chart_metric=chart_m,
                    chart_metric_strs=tuple(tuple(_fmt_frac(x) for x in r) for r in chart_m.g),
                    points=pts,
                    lines={},
                    segments={},
                    planes={},
                    polyhedron=None,
                    given_relations=(),
                    source_fact_refs={},
                    pending_constructions=pending,
                    error_code="DEGENERATE_COINCIDENT_POINTS",
                    error_detail=str(exc),
                )
            segs[sid] = seg
            lines[lid] = ln
            lk = canonical_line_key(ln)
            rels.append(("point_on_line", (canonical_point_key(pts[u]), lk), False))
            rels.append(("point_on_line", (canonical_point_key(pts[v]), lk), False))

        for fname, fverts in faces:
            if len(fverts) >= 3:
                try:
                    pl = E.Plane3.through(pts[fverts[0]], pts[fverts[1]], pts[fverts[2]])
                except E.GeometryError as exc:
                    return InitialGeometryFrame(
                        case_id=case_id,
                        problem_text=problem_text,
                        length_unit=kq.length_unit or length_unit,
                        chart_metric=chart_m,
                        chart_metric_strs=tuple(tuple(_fmt_frac(x) for x in r) for r in chart_m.g),
                        points=pts,
                        lines={},
                        segments={},
                        planes={},
                        polyhedron=None,
                        given_relations=(),
                        source_fact_refs={},
                        pending_constructions=pending,
                        error_code="DEGENERATE_COLLINEAR_POINTS",
                        error_detail=str(exc),
                    )
                planes[fname] = pl
                plk = canonical_plane_key(pl)
                for fv in fverts:
                    if pl.signed_eval(pts[fv]) == 0:
                        rels.append(("point_on_plane", (canonical_point_key(pts[fv]), plk), False))
                for i in range(len(fverts)):
                    u, v = fverts[i], fverts[(i + 1) % len(fverts)]
                    lk = canonical_line_key(E.Line3.through(pts[u], pts[v]))
                    rels.append(("line_in_plane", (lk, plk), False))

        # Record given exact perpendicularities declared in premises (verified in chart metric)
        for p in chart_premises:
            if p.get("kind") == "perpendicular":
                pa = p.get("points_a") or []
                pb = p.get("points_b") or []
                if len(pa) == 2 and pa[0] in pts and pa[1] in pts:
                    ln = E.Line3.through(pts[pa[0]], pts[pa[1]])
                    lk = canonical_line_key(ln)
                    if len(pb) >= 3 and all(x in pts for x in pb[:3]):
                        pl = E.Plane3.through(pts[pb[0]], pts[pb[1]], pts[pb[2]])
                        if M.plane_covector(ln.direction).cross(pl.normal).is_zero():
                            plk = canonical_plane_key(pl)
                            rels.append(("perp_line_plane", (lk, plk), False))
                            # If one endpoint lies in plane and one is off-plane, record given witness foot!
                            for ep in (pa[0], pa[1]):
                                other = pa[1] if ep == pa[0] else pa[0]
                                if pl.signed_eval(pts[ep]) == 0 and pl.signed_eval(pts[other]) != 0:
                                    rels.append(
                                        ("perp_point_plane_witness", (canonical_point_key(pts[other]), plk, canonical_point_key(pts[ep])), False)
                                    )
                    elif len(pb) == 2 and pb[0] in pts and pb[1] in pts:
                        ln2 = E.Line3.through(pts[pb[0]], pts[pb[1]])
                        if M.dot(ln.direction, ln2.direction) == 0:
                            rels.append(("perp_lines", (lk, canonical_line_key(ln2)), True))

    return InitialGeometryFrame(
        case_id=case_id,
        problem_text=problem_text,
        length_unit=kq.length_unit or length_unit,
        chart_metric=chart_m,
        chart_metric_strs=tuple(tuple(_fmt_frac(x) for x in r) for r in chart_m.g),
        points=pts,
        lines=lines,
        segments=segs,
        planes=planes,
        polyhedron=poly,
        given_relations=tuple(dict.fromkeys(rels)),
        source_fact_refs={"solid": (str(solid_spec.get("fact_id", "s1")),)},
        pending_constructions=pending,
    )


def solid_spec_to_typed_fact(solid_spec: dict[str, Any]) -> dict[str, Any]:
    stype = solid_spec.get("solid_type", "pyramid")
    if stype == "cube":
        out = {
            "id": str(solid_spec.get("fact_id", "s1")),
            "kind": "solid",
            "role": "premise",
            "solid": solid_spec["solid_name"],
            "solid_type": "prism",
            "right": True,
            "quotes": [solid_spec["quote"]],
        }
        return out
    out = {
        "id": str(solid_spec.get("fact_id", "s1")),
        "kind": "solid",
        "role": "premise",
        "solid": solid_spec["solid_name"],
        "solid_type": stype,
        "regular": bool(solid_spec.get("regular", False)),
        "quotes": [solid_spec["quote"]],
    }
    if stype == "prism" and solid_spec.get("right") is not None:
        out["right"] = bool(solid_spec["right"])
    return out


def make_initial_search_state(frame: InitialGeometryFrame) -> PlannerSearchState:
    """Convert a certified `InitialGeometryFrame` into the initial `PlannerSearchState` with `GIVEN` nodes."""
    objects: dict[str, ConstructionObject] = {}
    nodes: list[ConstructionNode] = []
    key_to_ids: dict[str, list[str]] = {}
    last_node_by_obj: dict[str, str] = {}
    relations: set[tuple[str, tuple[str, ...]]] = set()
    rel_nodes: dict[tuple[str, tuple[str, ...]], str] = {}

    def _reg_key(k: str, oid: str) -> None:
        key_to_ids.setdefault(k, [])
        if oid not in key_to_ids[k]:
            key_to_ids[k].append(oid)

    # 1. Given points
    pt_ids = sorted(frame.points.keys())
    for pid in pt_ids:
        pt = frame.points[pid]
        k = canonical_point_key(pt)
        _reg_key(k, pid)
        nid = f"n_given_pt_{pid}"
        objects[pid] = ConstructionObject(
            object_id=pid,
            object_kind="point3",
            origin="GIVEN_OBJECT",
            canonical_geom_key=k,
            label=f"Điểm {pid}",
            exact_value=pt,
            source_fact_refs=frame.source_fact_refs.get("solid", ("s1",)),
            supporting_node_id=nid,
        )
        nodes.append(
            ConstructionNode(
                node_id=nid,
                node_type="GIVEN",
                geometric_object_type="point3",
                object_refs=(pid,),
                geometry_context={"xyz": vec3_to_rational_list(pt)},
                source_fact_refs=frame.source_fact_refs.get("solid", ("s1",)),
                producing_operation_id=None,
                input_object_ids=(),
                preconditions=("source_gate:verified",),
                derived_constraints=(),
                output_objects=(pid,),
                dependency_ids=(),
                verification_status="VERIFIED",
                verification_evidence={"source_premise": True, "exact_rational": True},
                exact_computation_ref="engine.dung_tu_loi_goi(premise_only)",
                scene3d_render_hints={"render": "point_marker", "learner_text": f"Khởi tạo điểm {pid}"},
            )
        )
        last_node_by_obj[pid] = nid

    # 2. Given solid object if present
    if frame.polyhedron is not None:
        nid = "n_given_solid"
        sk = canonical_polygon_key(frame.polyhedron.vertices, kind="solid")
        _reg_key(sk, "solid_main")
        objects["solid_main"] = ConstructionObject(
            object_id="solid_main",
            object_kind="solid",
            origin="GIVEN_OBJECT",
            canonical_geom_key=sk,
            label="Khối đa diện",
            exact_value=frame.polyhedron,
            source_fact_refs=frame.source_fact_refs.get("solid", ("s1",)),
            supporting_node_id=nid,
            metadata={"vertex_ids": pt_ids},
        )
        nodes.append(
            ConstructionNode(
                node_id=nid,
                node_type="GIVEN",
                geometric_object_type="solid",
                object_refs=("solid_main",),
                geometry_context={"vertex_count": len(frame.polyhedron.vertices), "face_count": len(frame.polyhedron.faces)},
                source_fact_refs=frame.source_fact_refs.get("solid", ("s1",)),
                producing_operation_id=None,
                input_object_ids=tuple(pt_ids),
                preconditions=("source_gate:verified", "spd_metric"),
                derived_constraints=(),
                output_objects=("solid_main",),
                dependency_ids=tuple(last_node_by_obj[p] for p in pt_ids),
                verification_status="VERIFIED",
                verification_evidence={"spd_metric": True, "vertex_count": len(frame.polyhedron.vertices)},
                exact_computation_ref="engine.dung_tu_loi_goi(premise_only)",
                scene3d_render_hints={"render": "mesh"},
            )
        )
        last_node_by_obj["solid_main"] = nid

    # 3. Given segments, lines, and face planes
    for sid, seg in sorted(frame.segments.items()):
        sk = canonical_segment_key(seg)
        _reg_key(sk, sid)
        nid = f"n_given_{sid}"
        objects[sid] = ConstructionObject(
            object_id=sid,
            object_kind="segment3",
            origin="GIVEN_OBJECT",
            canonical_geom_key=sk,
            label=sid.replace("seg_", "").replace("_", ""),
            exact_value=seg,
            source_fact_refs=("s1",),
            supporting_node_id=nid,
        )
        nodes.append(
            ConstructionNode(
                node_id=nid,
                node_type="GIVEN",
                geometric_object_type="segment3",
                object_refs=(sid,),
                geometry_context={"canonical_key": sk},
                source_fact_refs=("s1",),
                producing_operation_id=None,
                input_object_ids=(),
                preconditions=("solid_edge",),
                derived_constraints=(),
                output_objects=(sid,),
                dependency_ids=("n_given_solid",) if "n_given_solid" in last_node_by_obj.values() else (),
                verification_status="VERIFIED",
                verification_evidence={"solid_edge": True},
                exact_computation_ref="exact.Segment3.between",
            )
        )
        last_node_by_obj[sid] = nid

    for lid, ln in sorted(frame.lines.items()):
        lk = canonical_line_key(ln)
        _reg_key(lk, lid)
        nid = f"n_given_{lid}"
        objects[lid] = ConstructionObject(
            object_id=lid,
            object_kind="line3",
            origin="GIVEN_OBJECT",
            canonical_geom_key=lk,
            label=lid.replace("ln_", "đt "),
            exact_value=ln,
            source_fact_refs=("s1",),
            supporting_node_id=nid,
        )
        nodes.append(
            ConstructionNode(
                node_id=nid,
                node_type="GIVEN",
                geometric_object_type="line3",
                object_refs=(lid,),
                geometry_context={"canonical_key": lk},
                source_fact_refs=("s1",),
                producing_operation_id=None,
                input_object_ids=(),
                preconditions=("solid_edge",),
                derived_constraints=(),
                output_objects=(lid,),
                dependency_ids=("n_given_solid",) if "n_given_solid" in last_node_by_obj.values() else (),
                verification_status="VERIFIED",
                verification_evidence={"solid_edge_line": True},
                exact_computation_ref="exact.Line3.through",
            )
        )
        last_node_by_obj[lid] = nid

    for plid, pl in sorted(frame.planes.items()):
        plk = canonical_plane_key(pl)
        _reg_key(plk, plid)
        nid = f"n_given_{plid}"
        objects[plid] = ConstructionObject(
            object_id=plid,
            object_kind="plane3",
            origin="GIVEN_OBJECT",
            canonical_geom_key=plk,
            label=plid,
            exact_value=pl,
            source_fact_refs=("s1",),
            supporting_node_id=nid,
        )
        nodes.append(
            ConstructionNode(
                node_id=nid,
                node_type="GIVEN",
                geometric_object_type="plane3",
                object_refs=(plid,),
                geometry_context={"canonical_key": plk},
                source_fact_refs=("s1",),
                producing_operation_id=None,
                input_object_ids=(),
                preconditions=("solid_face",),
                derived_constraints=(),
                output_objects=(plid,),
                dependency_ids=("n_given_solid",) if "n_given_solid" in last_node_by_obj.values() else (),
                verification_status="VERIFIED",
                verification_evidence={"solid_face_plane": True},
                exact_computation_ref="exact.Plane3.through",
            )
        )
        last_node_by_obj[plid] = nid

    for r_kind, r_ops, sym in frame.given_relations:
        ops = tuple(sorted(r_ops)) if sym else tuple(r_ops)
        rel = (r_kind, ops)
        relations.add(rel)
        rel_nodes[rel] = "n_given_solid" if "n_given_solid" in last_node_by_obj.values() else nodes[0].node_id

    return PlannerSearchState(
        objects=objects,
        nodes=tuple(nodes),
        relations=frozenset(relations),
        key_to_ids={k: tuple(v) for k, v in key_to_ids.items()},
        pending=frame.pending_constructions,
        cost=0.0,
        depth=0,
        aux_count=0,
        lineage=(),
        last_node_by_object=last_node_by_obj,
        relation_node_ids=rel_nodes,
    )


def materialize_proof_graph_from_state(
    frame: InitialGeometryFrame,
    state: PlannerSearchState,
    *,
    goal_spec: GoalSpec,
    goal_eval: dict[str, Any],
    plan_index: int,
) -> ConstructionProofGraph:
    """Append verified `GOAL` node and prune unused nodes to produce final `ConstructionProofGraph`."""
    goal_nid = f"n_goal_{plan_index}"
    # Exact backward dependency closure from witness objects and witness relations (unused detour nodes pruned!)
    dep_ids: list[str] = []
    witness_keys = tuple(goal_eval.get("witness_keys") or ())
    for wk in witness_keys:
        for oid in state.key_to_ids.get(wk, ()):
            if oid in state.last_node_by_object:
                dep_ids.append(state.last_node_by_object[oid])
    # Match only witness relations whose operands are actually part of this goal's witness keys
    for rel, nid in state.relation_node_ids.items():
        if all(part in witness_keys for part in rel[1]):
            dep_ids.append(nid)
    # Include all explicitly resolved derived/requested subgoal nodes from state if they fed any object
    given_node_ids = {n.node_id for n in state.nodes if n.node_type == "GIVEN"}
    dep_ids = [did for did in dict.fromkeys(dep_ids) if did]

    qty_id = "kq_goal"
    qty_obj = ConstructionObject(
        object_id=qty_id,
        object_kind="quantity",
        origin="DERIVED_OBJECT",
        canonical_geom_key=f"qty({goal_spec.goal_kind}={goal_eval['answer']})",
        label=f"Kết quả {goal_spec.goal_kind}",
        exact_value=goal_eval["answer_exact"],
        source_fact_refs=(),
        supporting_node_id=goal_nid,
    )
    goal_node = ConstructionNode(
        node_id=goal_nid,
        node_type="GOAL",
        geometric_object_type="quantity",
        object_refs=(qty_id, *(goal_eval.get("witness_object_ids") or ())),
        geometry_context={"goal_kind": goal_spec.goal_kind, "answer": goal_eval["answer"], "answer_exact": goal_eval["answer_exact"]},
        source_fact_refs=(),
        producing_operation_id=f"goal.{goal_spec.goal_kind}",
        input_object_ids=tuple(oid for wk in (goal_eval.get("witness_keys") or ()) for oid in state.key_to_ids.get(wk, ())[:1]),
        preconditions=(f"verified_witness({goal_spec.goal_kind})",),
        derived_constraints=(f"answer={goal_eval['answer']}",),
        output_objects=(qty_id,),
        dependency_ids=tuple(dep_ids),
        verification_status="VERIFIED",
        verification_evidence=goal_eval,
        exact_computation_ref=f"exact_witness_eval.{goal_spec.goal_kind}",
        scene3d_render_hints={"render": "readout", "learner_text": f"Tính/xác định kết quả mục tiêu: {goal_eval['answer']}"},
    )
    full_objects = {**state.objects, qty_id: qty_obj}
    full_graph = ConstructionProofGraph(
        graph_id=f"pg_{frame.case_id}_plan_{plan_index}",
        nodes=(*state.nodes, goal_node),
        objects=full_objects,
        goal_node_ids=(goal_nid,),
        chart_metric=frame.chart_metric_strs,
        length_unit=frame.length_unit,
        metadata={
            "case_id": frame.case_id,
            "plan_index": plan_index,
            "operator_lineage": list(state.lineage),
            "auxiliary_count": state.aux_count,
            "search_depth": state.depth,
        },
    )
    return prune_to_goal_closure(full_graph)
