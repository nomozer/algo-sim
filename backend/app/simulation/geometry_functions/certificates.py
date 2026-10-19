# -*- coding: utf-8 -*-
"""Exact Gram-metric geometry certificates (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING`).

Provides exact rational / Gram-metric verification and provenance validation for:
- Line-plane perpendicularity witnesses (`perpendicular_witness`) on `segment3` and `point3` objects;
- Symmetric positive-definite (SPD) validation of 3x3 rational Gram metrics via Sylvester's criterion;
- Deductive two-intersecting-lines line-plane perpendicularity certificates (`PROVEN` vs `DERIVED`);
- Epistemic status distinction (`GIVEN`, `ENGINE_VERIFIED`, `DERIVED`, `UNVERIFIABLE`, `PROVEN`);
- Fail-closed tamper verification (`verify_perpendicular_witness`).
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

CERTIFICATE_SCHEMA = "exact-gram-line-plane-orthogonality/1"
DEDUCTIVE_THEOREM_SCHEMA = "line_perpendicular_two_intersecting_lines_in_plane/1"

VALID_EPISTEMIC_STATUSES = frozenset({"GIVEN", "ENGINE_VERIFIED", "DERIVED", "UNVERIFIABLE", "PROVEN"})
CERTIFIABLE_STATUSES = frozenset({"GIVEN", "ENGINE_VERIFIED", "DERIVED", "PROVEN"})


class CertificateError(ValueError):
    """Fail-closed exception raised when an exact geometry certificate check fails."""

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason


def _to_fraction(val: Any) -> Fraction:
    if isinstance(val, bool) or val is None:
        raise ValueError("boolean or None is not a rational number")
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val)
    return Fraction(str(val))


def validate_gram_metric_spd(chart_metric: Any = None) -> list[list[Fraction]]:
    """Validate and return a 3x3 symmetric positive-definite (SPD) rational Gram matrix G.

    Uses Sylvester's criterion in exact rational arithmetic:
      - G is 3x3 and symmetric: G[i][j] == G[j][i]
      - Delta_1 = G[0][0] > 0
      - Delta_2 = G[0][0]*G[1][1] - G[0][1]^2 > 0
      - Delta_3 = det(G) > 0
    Raises CertificateError("NON_SPD_METRIC", ...) on any violation.
    """
    if chart_metric is None:
        return [[Fraction(1 if i == j else 0) for j in range(3)] for i in range(3)]
    raw = getattr(chart_metric, "g", chart_metric)
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        raise CertificateError("NON_SPD_METRIC", "chart_metric must be a 3x3 matrix")
    g_mat: list[list[Fraction]] = []
    try:
        for row in raw:
            if not isinstance(row, (list, tuple)) or len(row) != 3:
                raise CertificateError("NON_SPD_METRIC", "chart_metric row must have length 3")
            g_mat.append([_to_fraction(x) for x in row])
    except (ValueError, ZeroDivisionError, TypeError) as exc:
        if isinstance(exc, CertificateError):
            raise
        raise CertificateError("NON_SPD_METRIC", f"invalid rational entry in chart_metric: {exc}") from None

    for i in range(3):
        for j in range(i + 1, 3):
            if g_mat[i][j] != g_mat[j][i]:
                raise CertificateError("NON_SPD_METRIC", f"chart_metric is not symmetric at ({i}, {j})")

    delta1 = g_mat[0][0]
    delta2 = g_mat[0][0] * g_mat[1][1] - g_mat[0][1] * g_mat[1][0]
    delta3 = (
        g_mat[0][0] * (g_mat[1][1] * g_mat[2][2] - g_mat[1][2] * g_mat[2][1])
        - g_mat[0][1] * (g_mat[1][0] * g_mat[2][2] - g_mat[1][2] * g_mat[2][0])
        + g_mat[0][2] * (g_mat[1][0] * g_mat[2][1] - g_mat[1][1] * g_mat[2][0])
    )
    if not (delta1 > 0 and delta2 > 0 and delta3 > 0):
        raise CertificateError(
            "NON_SPD_METRIC",
            f"chart_metric fails Sylvester SPD criterion (d1={delta1}, d2={delta2}, d3={delta3})",
        )
    return g_mat


def gram_dot(g_mat: list[list[Fraction]], u: list[Fraction], v: list[Fraction]) -> Fraction:
    return sum(u[i] * g_mat[i][j] * v[j] for i in range(3) for j in range(3))


def vec_sub(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def vec_cross(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _point_in_plane_span(
    pt: list[Fraction],
    origin: list[Fraction],
    u1: list[Fraction],
    u2: list[Fraction],
) -> bool:
    """Exact check that `pt - origin` lies in span(u1, u2): (u1 x u2) . (pt - origin) == 0."""
    n = vec_cross(u1, u2)
    diff = vec_sub(pt, origin)
    return n[0] * diff[0] + n[1] * diff[1] + n[2] * diff[2] == 0


def certify_line_plane_perpendicularity(
    *,
    from_id: str,
    foot_id: str,
    plane_id: str,
    plane_vertex_ids: list[str],
    points_by_id: dict[str, list[Fraction]],
    chart_metric: Any = None,
    provenance_status: str = "ENGINE_VERIFIED",
    rule: str = "solid_or_projection_altitude",
    supporting_calls: list[str] | None = None,
    supporting_step_index: int | None = None,
    conclusion_step_index: int | None = None,
    direction_vectors: tuple[list[Fraction], list[Fraction]] | None = None,
) -> dict[str, Any]:
    """Certify exact line-plane perpendicularity in Gram metric G with full provenance validation."""
    g_mat = validate_gram_metric_spd(chart_metric)

    if not rule or "unsupported" in rule.lower():
        raise CertificateError("UNSUPPORTED_ASSUMPTION", f"unsupported rule or assumption: {rule!r}")
    if provenance_status not in VALID_EPISTEMIC_STATUSES:
        raise CertificateError("MISSING_PROVENANCE", f"unknown provenance status: {provenance_status!r}")
    if provenance_status == "UNVERIFIABLE":
        raise CertificateError(
            "MISSING_PROVENANCE",
            "relationship is UNVERIFIABLE (layout-derived without premise or construction justification)",
        )
    if supporting_step_index is not None or conclusion_step_index is not None:
        if (
            supporting_step_index is None
            or conclusion_step_index is None
            or type(supporting_step_index) is not int
            or type(conclusion_step_index) is not int
            or supporting_step_index < 0
            or conclusion_step_index <= supporting_step_index
        ):
            raise CertificateError(
                "WRONG_CONSTRUCTION_STEP",
                f"invalid construction step ordering: supporting={supporting_step_index}, conclusion={conclusion_step_index}",
            )

    if from_id not in points_by_id or foot_id not in points_by_id:
        raise CertificateError("MISMATCHED_OPERANDS", f"missing point operands: from={from_id!r}, foot={foot_id!r}")
    if from_id == foot_id:
        raise CertificateError("DEGENERATE_LINE_DIRECTION", f"from_id and foot_id coincide ({from_id!r})")

    plane_pts = [points_by_id[vid] for vid in plane_vertex_ids if vid in points_by_id]
    if len(plane_pts) < 3 or len(set(plane_vertex_ids)) < 3:
        raise CertificateError("DEGENERATE_PLANE_DIRECTIONS", f"plane {plane_id!r} needs at least 3 distinct vertices")

    foot_pt = points_by_id[foot_id]
    from_pt = points_by_id[from_id]
    v_seg = vec_sub(from_pt, foot_pt)
    norm_seg_sq = gram_dot(g_mat, v_seg, v_seg)
    if norm_seg_sq <= 0:
        raise CertificateError("DEGENERATE_LINE_DIRECTION", f"segment {from_id}{foot_id} has zero length in Gram metric")

    if direction_vectors is not None:
        u1, u2 = direction_vectors
    elif foot_id in plane_vertex_ids:
        idx = plane_vertex_ids.index(foot_id)
        next_pt = points_by_id[plane_vertex_ids[(idx + 1) % len(plane_vertex_ids)]]
        prev_pt = points_by_id[plane_vertex_ids[(idx - 1) % len(plane_vertex_ids)]]
        u1 = vec_sub(next_pt, foot_pt)
        u2 = vec_sub(prev_pt, foot_pt)
    else:
        u1 = vec_sub(plane_pts[1], plane_pts[0])
        u2 = vec_sub(plane_pts[-1], plane_pts[0])
        if gram_dot(g_mat, u1, u1) * gram_dot(g_mat, u2, u2) - (gram_dot(g_mat, u1, u2) ** 2) <= 0:
            for i_pt in range(1, len(plane_pts)):
                cand_u1 = vec_sub(plane_pts[i_pt], plane_pts[0])
                for j_pt in range(i_pt + 1, len(plane_pts)):
                    cand_u2 = vec_sub(plane_pts[j_pt], plane_pts[0])
                    if gram_dot(g_mat, cand_u1, cand_u1) * gram_dot(g_mat, cand_u2, cand_u2) - (gram_dot(g_mat, cand_u1, cand_u2) ** 2) > 0:
                        u1, u2 = cand_u1, cand_u2
                        break

    gram_det_plane = gram_dot(g_mat, u1, u1) * gram_dot(g_mat, u2, u2) - (gram_dot(g_mat, u1, u2) ** 2)
    if gram_det_plane <= 0:
        raise CertificateError(
            "DEGENERATE_PLANE_DIRECTIONS",
            f"plane directions in {plane_id!r} are collinear or degenerate (det_G={gram_det_plane})",
        )

    if not _point_in_plane_span(foot_pt, plane_pts[0], u1, u2):
        raise CertificateError("MISMATCHED_OPERANDS", f"foot {foot_id!r} does not lie in plane {plane_id!r}")

    dot1 = gram_dot(g_mat, v_seg, u1)
    dot2 = gram_dot(g_mat, v_seg, u2)
    if dot1 != 0 or dot2 != 0:
        raise CertificateError(
            "NOT_ORTHOGONAL",
            f"segment {from_id}{foot_id} is not orthogonal to plane {plane_id!r} (dot1={dot1}, dot2={dot2})",
        )

    cert: dict[str, Any] = {
        "from": from_id,
        "foot_id": foot_id,
        "foot": [str(x) for x in foot_pt],
        "on": plane_id,
        "marker": {
            "u": [str(x) for x in u1],
            "v": [str(x) for x in v_seg],
        },
        "plane_directions": [[str(x) for x in u1], [str(x) for x in u2]],
        "certificate": CERTIFICATE_SCHEMA,
        "status": provenance_status,
        "rule": rule,
        "metric_spd": True,
        "can_present_as_proven": provenance_status == "PROVEN",
    }
    if supporting_calls is not None:
        cert["supporting_calls"] = list(supporting_calls)
    if supporting_step_index is not None:
        cert["supporting_step_index"] = supporting_step_index
    if conclusion_step_index is not None:
        cert["conclusion_step_index"] = conclusion_step_index
    return cert


def certify_deductive_line_plane_perpendicularity(
    *,
    goal_call: dict[str, Any],
    calls: list[dict[str, Any]],
    points_by_id: dict[str, list[Fraction]],
    chart_metric: Any = None,
    supporting_step_index: int | None = None,
    conclusion_step_index: int | None = None,
) -> dict[str, Any]:
    """Certify a deductive line-plane perpendicularity obligation (`line ⊥ plane`) via the
    two-intersecting-lines theorem:
      1. Premise 1 establishes `line ⊥ d1` for a line `d1 ⊂ plane` (via `right_angle`, `perpendicular_lines`, or `rectangle`).
      2. Premise 2 establishes `line ⊥ d2` for a line `d2 ⊂ plane` (via `perpendicular_line_plane(d2, base)` with `line ⊂ base`,
         `altitude`, or `perpendicular_lines`).
      3. `d1` and `d2` are two independent directions in `plane` (`det_G(u_d1, u_d2) > 0`), and `line` is orthogonal to both
         in exact Gram arithmetic.
    """
    args = goal_call.get("args") or {}
    line = list(args.get("line") or [])
    plane = list(args.get("plane") or [])
    if len(line) != 2 or len(plane) < 3:
        raise CertificateError("MISMATCHED_OPERANDS", "goal_call requires 2 line points and >=3 plane points")
    plane_set = set(plane)
    in_plane = [p for p in line if p in plane_set]
    if len(in_plane) != 1:
        raise CertificateError("MISMATCHED_OPERANDS", f"line {line} must intersect plane {plane} at a single vertex")
    foot_id = in_plane[0]
    from_id = line[0] if line[1] == foot_id else line[1]
    line_set = frozenset(line)
    goal_id = goal_call.get("id")

    dir_candidates: list[tuple[tuple[str, str], str]] = []
    for c in calls:
        if c is goal_call or (isinstance(goal_id, str) and goal_id and c.get("id") == goal_id):
            continue
        if c.get("role") not in (None, "premise"):
            continue
        if c.get("negated") is True or c.get("conditional") is True:
            continue
        cid = c.get("id") or ""
        fn = c.get("fn") or ""
        cargs = c.get("args") or {}
        if fn == "right_angle":
            v = cargs.get("vertex")
            rays = list(cargs.get("rays") or [])
            if v and len(rays) == 2:
                r1, r2 = (v, rays[0]), (v, rays[1])
                if frozenset(r1) == line_set and set(r2) <= plane_set:
                    dir_candidates.append((r2, cid))
                elif frozenset(r2) == line_set and set(r1) <= plane_set:
                    dir_candidates.append((r1, cid))
        elif fn == "perpendicular_lines":
            l1 = tuple(cargs.get("line1") or [])
            l2 = tuple(cargs.get("line2") or [])
            if len(l1) == 2 and len(l2) == 2:
                if frozenset(l1) == line_set and set(l2) <= plane_set:
                    dir_candidates.append(((l2[0], l2[1]), cid))
                elif frozenset(l2) == line_set and set(l1) <= plane_set:
                    dir_candidates.append(((l1[0], l1[1]), cid))
        elif fn == "perpendicular_line_plane":
            pline = tuple(cargs.get("line") or [])
            pplane = set(cargs.get("plane") or [])
            if (
                len(pline) == 2
                and line_set <= pplane
                and set(pline) <= plane_set
                and not (frozenset(pline) == line_set and pplane == plane_set)
            ):
                dir_candidates.append(((pline[0], pline[1]), cid))

    g_mat = validate_gram_metric_spd(chart_metric)
    chosen_dirs: tuple[list[Fraction], list[Fraction]] | None = None
    supporting_ids: list[str] = []
    for i in range(len(dir_candidates)):
        (a1, b1), id1 = dir_candidates[i]
        if a1 not in points_by_id or b1 not in points_by_id:
            continue
        u1 = vec_sub(points_by_id[b1], points_by_id[a1]) if a1 == foot_id else vec_sub(points_by_id[a1], points_by_id[b1])
        for j in range(i + 1, len(dir_candidates)):
            (a2, b2), id2 = dir_candidates[j]
            if a2 not in points_by_id or b2 not in points_by_id:
                continue
            u2 = vec_sub(points_by_id[b2], points_by_id[a2]) if a2 == foot_id else vec_sub(points_by_id[a2], points_by_id[b2])
            det2 = gram_dot(g_mat, u1, u1) * gram_dot(g_mat, u2, u2) - (gram_dot(g_mat, u1, u2) ** 2)
            if det2 > 0:
                chosen_dirs = (u1, u2)
                supporting_ids = [id1, id2]
                break
        if chosen_dirs is not None:
            break

    if chosen_dirs is None:
        raise CertificateError(
            "MISSING_PROVENANCE",
            f"cannot deductively certify {line} ⊥ ({''.join(plane)}): fewer than 2 independent perpendicular directions in plane",
        )

    role = goal_call.get("role") or "prove"
    status = "PROVEN" if role == "prove" else "DERIVED"
    cert = certify_line_plane_perpendicularity(
        from_id=from_id,
        foot_id=foot_id,
        plane_id=f"plane_{''.join(plane)}",
        plane_vertex_ids=plane,
        points_by_id=points_by_id,
        chart_metric=g_mat,
        provenance_status=status,
        rule=DEDUCTIVE_THEOREM_SCHEMA,
        supporting_calls=supporting_ids,
        supporting_step_index=supporting_step_index,
        conclusion_step_index=conclusion_step_index,
        direction_vectors=chosen_dirs,
    )
    cert["theorem"] = DEDUCTIVE_THEOREM_SCHEMA
    return cert


def verify_perpendicular_witness(
    witness: Any,
    canh: dict[str, Any],
    chart_metric: Any = None,
    *,
    segment_obj: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Fail-closed verifier for a `perpendicular_witness` dictionary against a Scene3D payload."""
    if not isinstance(witness, dict):
        return False, "MALFORMED_WITNESS"
    try:
        g_mat = validate_gram_metric_spd(chart_metric if chart_metric is not None else canh.get("chart_metric"))
    except CertificateError as exc:
        return False, exc.code

    rule = str(witness.get("rule") or "")
    if "unsupported" in rule.lower():
        return False, "UNSUPPORTED_ASSUMPTION"

    status = witness.get("status", "ENGINE_VERIFIED")
    if status not in CERTIFIABLE_STATUSES:
        return False, "MISSING_PROVENANCE"

    supp_step = witness.get("supporting_step_index")
    conc_step = witness.get("conclusion_step_index")
    if supp_step is not None or conc_step is not None:
        if (
            supp_step is None
            or conc_step is None
            or type(supp_step) is not int
            or type(conc_step) is not int
            or supp_step < 0
            or conc_step <= supp_step
        ):
            return False, "WRONG_CONSTRUCTION_STEP"

    objects = canh.get("objects") or []
    points_by_id: dict[str, list[Fraction]] = {}
    objects_by_id: dict[str, dict[str, Any]] = {}
    for o in objects:
        if isinstance(o, dict) and isinstance(o.get("id"), str):
            objects_by_id[o["id"]] = o
            if o.get("type") == "point3" and isinstance(o.get("xyz"), list) and len(o["xyz"]) == 3:
                try:
                    points_by_id[o["id"]] = [_to_fraction(x) for x in o["xyz"]]
                except (ValueError, ZeroDivisionError):
                    return False, "MALFORMED_WITNESS"

    from_id = witness.get("from")
    on_id = witness.get("on")
    if not isinstance(from_id, str) or from_id not in points_by_id:
        return False, "MISMATCHED_OPERANDS"
    if not isinstance(on_id, str) or on_id not in objects_by_id:
        return False, "MISMATCHED_OPERANDS"

    target_obj = objects_by_id[on_id]
    try:
        foot_pt = [_to_fraction(x) for x in (witness.get("foot") or [])]
        marker = witness.get("marker") or {}
        u_vec = [_to_fraction(x) for x in (marker.get("u") or [])]
        v_vec = [_to_fraction(x) for x in (marker.get("v") or [])]
    except (ValueError, ZeroDivisionError, TypeError):
        return False, "MALFORMED_WITNESS"
    if len(foot_pt) != 3 or len(u_vec) != 3 or len(v_vec) != 3:
        return False, "MALFORMED_WITNESS"

    if segment_obj is not None:
        ep_ids = list(segment_obj.get("endpoint_ids") or [])
        if len(ep_ids) != 2 or from_id not in ep_ids:
            return False, "MISMATCHED_OPERANDS"
        expected_foot_id = ep_ids[1] if ep_ids[0] == from_id else ep_ids[0]
        if expected_foot_id not in points_by_id:
            return False, "MISMATCHED_OPERANDS"
        if foot_pt != points_by_id[expected_foot_id]:
            return False, "TAMPERED_WITNESS_FOOT"

    foot_id = witness.get("foot_id")
    if isinstance(foot_id, str):
        if foot_id not in points_by_id or foot_id == from_id:
            return False, "MISMATCHED_OPERANDS"
        if foot_pt != points_by_id[foot_id]:
            return False, "TAMPERED_WITNESS_FOOT"

    if target_obj.get("type") == "polygon3":
        vids = [vid for vid in (target_obj.get("vertex_ids") or []) if vid in points_by_id]
        if len(vids) < 3:
            return False, "DEGENERATE_PLANE_DIRECTIONS"
        u1_plane = vec_sub(points_by_id[vids[1]], points_by_id[vids[0]])
        u2_plane = vec_sub(points_by_id[vids[-1]], points_by_id[vids[0]])
        if not _point_in_plane_span(foot_pt, points_by_id[vids[0]], u1_plane, u2_plane):
            return False, "TAMPERED_WITNESS_FOOT"

    from_pt = points_by_id[from_id]
    expected_v = vec_sub(from_pt, foot_pt)
    if v_vec != expected_v:
        return False, "TAMPERED_WITNESS_MARKER"
    if gram_dot(g_mat, u_vec, u_vec) <= 0 or gram_dot(g_mat, v_vec, v_vec) <= 0:
        return False, "TAMPERED_WITNESS_MARKER"
    if gram_dot(g_mat, u_vec, v_vec) != 0:
        return False, "TAMPERED_WITNESS_MARKER"

    plane_dirs = witness.get("plane_directions")
    if plane_dirs is not None:
        if not isinstance(plane_dirs, list) or len(plane_dirs) != 2:
            return False, "TAMPERED_WITNESS_MARKER"
        try:
            d1 = [_to_fraction(x) for x in plane_dirs[0]]
            d2 = [_to_fraction(x) for x in plane_dirs[1]]
        except (ValueError, ZeroDivisionError, TypeError):
            return False, "TAMPERED_WITNESS_MARKER"
        if len(d1) != 3 or len(d2) != 3:
            return False, "TAMPERED_WITNESS_MARKER"
        det2 = gram_dot(g_mat, d1, d1) * gram_dot(g_mat, d2, d2) - (gram_dot(g_mat, d1, d2) ** 2)
        if det2 <= 0 or gram_dot(g_mat, v_vec, d1) != 0 or gram_dot(g_mat, v_vec, d2) != 0:
            return False, "TAMPERED_WITNESS_MARKER"

    return True, "OK"


def _infer_segment_provenance(
    seg: dict[str, Any],
    from_id: str,
    foot_id: str,
    objects_by_id: dict[str, dict[str, Any]],
    trace: list[dict[str, Any]] | None,
) -> tuple[str, str, list[str]]:
    """Determine epistemic status and rule for a candidate perpendicular segment.

    Returns ("UNVERIFIABLE", ..., []) if the segment or its apex is explicitly marked as
    unjustified layout-derived coordinates or lacks justified height provenance on Path A.
    """
    for obj in (seg, objects_by_id.get(from_id) or {}, objects_by_id.get(foot_id) or {}):
        src = obj.get("source") or {}
        if isinstance(src, dict) and src.get("unjustified_layout") is True:
            return "UNVERIFIABLE", "unjustified_layout", []
        if obj.get("provenance") == "UNVERIFIABLE":
            return "UNVERIFIABLE", "unjustified_layout", []

    if trace:
        for step in trace:
            if step.get("step") == "place_point" and step.get("object") == from_id:
                rule = str(step.get("rule") or "")
                calls = list(step.get("calls") or [])
                if rule.startswith("perpendicular_foot_at_") or rule.startswith("altitude_normalized_to_"):
                    return "GIVEN", rule, calls
                if rule in ("apex_over_center", "right_prism_translate") or rule.startswith(
                    ("orthogonal_projection_normalized_to_", "face_perpendicular_base_foot_on_", "line_perpendicular_to_two_")
                ):
                    return "ENGINE_VERIFIED", rule, calls

    if "formation_roles" in seg:
        roles = set(seg.get("formation_roles") or ())
        if "CONSTRUCT_HEIGHT" in roles:
            return "GIVEN", "formation_construct_height", []
        if "CONSTRUCT_LATERAL_BOUNDARY" in roles and any(
            o.get("shape_class") == "PRISM_LIKE" for o in objects_by_id.values() if isinstance(o, dict)
        ):
            return "ENGINE_VERIFIED", "prism_lateral_altitude", []
        if trace is None and any(
            o.get("shape_class") == "PYRAMID_LIKE" for o in objects_by_id.values() if isinstance(o, dict)
        ):
            return "UNVERIFIABLE", "missing_height_provenance", []

    return "ENGINE_VERIFIED", "exact_gram_base_altitude", []


def attach_scene_perpendicular_certificates(
    canh: dict[str, Any],
    chart_metric: Any = None,
    *,
    trace: list[dict[str, Any]] | None = None,
) -> None:
    """Attach exact Gram-metric `perpendicular_witness` certificates onto `segment3` objects that are
    mathematically orthogonal to the base polygon under an SPD `chart_metric` and have valid provenance."""
    objects = canh.get("objects") or []
    metric_src = chart_metric if chart_metric is not None else canh.get("chart_metric")
    try:
        g_mat = validate_gram_metric_spd(metric_src)
    except CertificateError:
        return

    points_by_id: dict[str, list[Fraction]] = {}
    objects_by_id: dict[str, dict[str, Any]] = {}
    for o in objects:
        if isinstance(o, dict) and isinstance(o.get("id"), str):
            objects_by_id[o["id"]] = o
            if o.get("type") == "point3" and isinstance(o.get("xyz"), list) and len(o["xyz"]) == 3:
                try:
                    points_by_id[o["id"]] = [_to_fraction(x) for x in o["xyz"]]
                except (ValueError, ZeroDivisionError):
                    continue

    base_polys = [
        o
        for o in objects
        if isinstance(o, dict)
        and o.get("type") == "polygon3"
        and "CONSTRUCT_BASE" in (o.get("formation_roles") or [])
    ]
    if not base_polys:
        solid_base_faces: list[frozenset[str]] = []
        for o in objects:
            if isinstance(o, dict) and o.get("type") == "solid":
                vids = o.get("vertex_ids") or []
                faces = o.get("faces") or []
                if vids and faces and isinstance(faces[0], list) and len(faces[0]) >= 3:
                    if all(isinstance(idx, int) and 0 <= idx < len(vids) for idx in faces[0]):
                        solid_base_faces.append(frozenset(vids[idx] for idx in faces[0]))
        if solid_base_faces:
            base_polys = [
                o
                for o in objects
                if isinstance(o, dict)
                and o.get("type") == "polygon3"
                and frozenset(o.get("vertex_ids") or ()) in solid_base_faces
            ]
    if not base_polys:
        return

    base = base_polys[0]
    base_vids = [vid for vid in (base.get("vertex_ids") or []) if vid in points_by_id]
    if len(base_vids) < 3:
        return
    base_pts = [points_by_id[vid] for vid in base_vids]
    u1_base = vec_sub(base_pts[1], base_pts[0])
    u2_base = vec_sub(base_pts[-1], base_pts[0])

    segments = [o for o in objects if isinstance(o, dict) and o.get("type") == "segment3"]
    for seg in segments:
        if seg.get("perpendicular_witness") is not None:
            continue
        ep_ids = seg.get("endpoint_ids") or []
        if len(ep_ids) != 2 or ep_ids[0] not in points_by_id or ep_ids[1] not in points_by_id:
            continue
        p0_id, p1_id = ep_ids[0], ep_ids[1]
        p0_in_base = p0_id in base_vids or _point_in_plane_span(points_by_id[p0_id], base_pts[0], u1_base, u2_base)
        p1_in_base = p1_id in base_vids or _point_in_plane_span(points_by_id[p1_id], base_pts[0], u1_base, u2_base)
        if p0_in_base == p1_in_base:
            continue

        foot_id = p1_id if p1_in_base else p0_id
        from_id = p0_id if p1_in_base else p1_id
        status, rule, supp_calls = _infer_segment_provenance(seg, from_id, foot_id, objects_by_id, trace)
        if status == "UNVERIFIABLE":
            continue
        try:
            cert = certify_line_plane_perpendicularity(
                from_id=from_id,
                foot_id=foot_id,
                plane_id=base["id"],
                plane_vertex_ids=base_vids,
                points_by_id=points_by_id,
                chart_metric=g_mat,
                provenance_status=status,
                rule=rule,
                supporting_calls=supp_calls if supp_calls else None,
            )
        except CertificateError:
            continue
        seg["perpendicular_witness"] = cert
