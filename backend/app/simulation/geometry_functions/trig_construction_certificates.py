# -*- coding: utf-8 -*-
"""Exact machine-verifiable trigonometric & right-triangle construction certificates (`trig-construction-certificate/1`).

Certifies derived lengths (heights, projections, slant edges, right-triangle legs/hypotenuses, and rhombus sides from
diagonals + vertex angles) using ONLY exact arithmetic (`Fraction`, `Radical`, rational 3x3 SPD Gram metrics, and exact
rational point coordinates). Float approximations are strictly forbidden.

Every emitted certificate is independently checkable by `verify_trig_construction_certificate(...)`, which rejects:
1. Non-SPD or float-contaminated Gram metrics / coordinates;
2. Mutated `right_angle_vertex` or degenerate/collinear triangles;
3. Swapped `hypotenuse`, `adjacent_leg`, or `opposite_leg` (including at 45° where numeric leg lengths coincide);
4. Mutated `angle_witness` vertex or rays (including non-projection base rays for `line_plane_angle`);
5. Forged or stripped `perpendicularity_justification` (accidental `<u, v>_G == 0` without deductive premise calls);
6. Mutated `trig_identity` (including `sin` <-> `cos` swap at 45° against a fixed `derived_quantity_id`);
7. Tampered `exact_length_expr` or wrong `dimension` (`dimension != "LENGTH"`);
8. Violated `positivity_domain` or ambiguous multi-branch `sin` in `(0°, 180°)`;
9. Broken `source_premises`, circular `known_inputs`, or tampered `scene_objects` / `auxiliary_witness_points`.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from app.simulation.geometry.radical import (
    ExactNumber,
    Radical,
    RadicalDomainError,
    display,
    from_json,
    parse_exact,
    sign,
    sqrt_rational,
    square,
    to_json,
)
from app.simulation.geometry_functions.certificates import (
    CertificateError,
    _point_in_plane_span,
    gram_dot,
    validate_gram_metric_spd,
    vec_cross,
    vec_sub,
)
from app.simulation.geometry_functions.registry import chuan_hoa

TRIG_CONSTRUCTION_CERTIFICATE_VERSION = "trig-construction-certificate/1"

ID_OPP_FROM_HYP_SIN = "h = c * sin(alpha)"
ID_ADJ_FROM_HYP_COS = "p = c * cos(alpha)"
ID_OPP_FROM_ADJ_TAN = "h = p * tan(alpha)"
ID_ADJ_FROM_OPP_COT = "p = h * cot(alpha)"
ID_HYP_FROM_ADJ_COS = "c = p / cos(alpha)"
ID_HYP_FROM_OPP_SIN = "c = h / sin(alpha)"
ID_PYTH_HYP_FROM_LEGS = "pythagoras_hypotenuse_from_legs"
ID_PYTH_LEG_FROM_HYP = "pythagoras_leg_from_hypotenuse"
ID_PYTH_EQUAL_LEGS = "pythagoras_equal_legs"
ID_PYTH_LEG_RATIO = "pythagoras_leg_ratio"
ID_RHOMBUS_HALF_DIAG_COS = "rhombus_half_diagonal_cos"

CLOSED_TRIG_IDENTITIES: tuple[str, ...] = (
    ID_OPP_FROM_HYP_SIN,
    ID_ADJ_FROM_HYP_COS,
    ID_OPP_FROM_ADJ_TAN,
    ID_ADJ_FROM_OPP_COT,
    ID_HYP_FROM_ADJ_COS,
    ID_HYP_FROM_OPP_SIN,
    ID_PYTH_HYP_FROM_LEGS,
    ID_PYTH_LEG_FROM_HYP,
    ID_PYTH_EQUAL_LEGS,
    ID_PYTH_LEG_RATIO,
    ID_RHOMBUS_HALF_DIAG_COS,
)

#: Exact special acute angles (in degrees) -> (sin², cos², cos_sign).
ACUTE_EXACT_DEGREES: dict[Fraction, tuple[Fraction, Fraction, int]] = {
    Fraction(30): (Fraction(1, 4), Fraction(3, 4), 1),
    Fraction(45): (Fraction(1, 2), Fraction(1, 2), 1),
    Fraction(60): (Fraction(3, 4), Fraction(1, 4), 1),
}

#: Extended exact degree table on (0°, 180°) for polygon interior and supplementary angles -> (sin², cos², cos_sign).
EXTENDED_EXACT_DEGREES: dict[Fraction, tuple[Fraction, Fraction, int]] = {
    **ACUTE_EXACT_DEGREES,
    Fraction(90): (Fraction(1), Fraction(0), 0),
    Fraction(120): (Fraction(3, 4), Fraction(1, 4), -1),
    Fraction(135): (Fraction(1, 2), Fraction(1, 2), -1),
    Fraction(150): (Fraction(1, 4), Fraction(3, 4), -1),
}

EXACT_TRIG_RATIO_UNITS: frozenset[str] = frozenset({"sin", "cos", "tan", "cot"})

VALID_DERIVED_ROLES: frozenset[str] = frozenset({"opposite_leg", "adjacent_leg", "hypotenuse", "both_legs"})

VALID_PERPENDICULARITY_RULES: frozenset[str] = frozenset({
    "explicit_right_angle",
    "explicit_perpendicular_lines",
    "line_perpendicular_to_plane",
    "orthogonal_projection_on_line",
    "rhombus_perpendicular_diagonals",
    "face_altitude_perpendicular_base",
    "deductive_two_lines_in_plane",
})

VALID_ANGLE_WITNESS_KINDS: frozenset[str] = frozenset({
    "vertex_angle",
    "line_plane_angle",
    "dihedral_angle",
    "line_line_angle",
    "rhombus_bisected_vertex_angle",
    "equal_legs_witness",
    "leg_ratio_witness",
    "pythagorean_lengths",
})

VALID_AUXILIARY_POINT_RULES: frozenset[str] = frozenset({
    "segment_midpoint",
    "orthogonal_projection_foot_on_line",
    "orthogonal_projection_foot_on_plane",
})


class TrigCertificateError(CertificateError):
    """Fail-closed exception raised when an exact trigonometric construction certificate fails verification."""


@dataclass(frozen=True)
class TrigAngleParams:
    """Exact squared trigonometric parameters `(sin², cos², cos_sign)` for a verified angle or trig ratio."""

    unit: str
    raw_value: str
    sin_sq: Fraction
    cos_sq: Fraction
    cos_sign: int


def _ir_name(label: str) -> str:
    return label.replace("'", "_prime")


def _strict_fraction(val: Any, *, field_name: str = "value") -> Fraction:
    """Convert `int | Fraction | str` to `Fraction`, strictly rejecting `bool`, `None`, and `float`."""
    if isinstance(val, bool) or val is None:
        raise TrigCertificateError("INVALID_RATIONAL_VALUE", f"{field_name}: boolean or None is not a rational number")
    if isinstance(val, float):
        raise TrigCertificateError("FLOAT_APPROXIMATION_FORBIDDEN", f"{field_name}: float values are forbidden")
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val)
    if isinstance(val, str):
        s = val.strip()
        if not s or "e" in s.lower():
            raise TrigCertificateError("INVALID_RATIONAL_VALUE", f"{field_name}: invalid rational literal {val!r}")
        try:
            return Fraction(s)
        except (ValueError, ZeroDivisionError) as exc:
            raise TrigCertificateError("INVALID_RATIONAL_VALUE", f"{field_name}: {exc}") from None
    raise TrigCertificateError("INVALID_RATIONAL_VALUE", f"{field_name}: unsupported type {type(val).__name__}")


def _strict_vec3(coords: Sequence[Any], *, label: str) -> list[Fraction]:
    if not isinstance(coords, (list, tuple)) or len(coords) != 3:
        raise TrigCertificateError("INVALID_POINT_COORDS", f"point {label!r} must have 3 exact rational coordinates")
    return [_strict_fraction(coords[i], field_name=f"{label}[{i}]") for i in range(3)]


def exact_trig_angle_params(
    value: Any,
    unit: str = "deg",
    *,
    allow_obtuse: bool = False,
    cos_sign_hint: int | None = None,
) -> TrigAngleParams:
    """Evaluate exact `(sin², cos², cos_sign)` from a degree value or trig ratio without float approximations.

    - Acute right-triangle mode (`allow_obtuse=False`): accepts degrees in `{30, 45, 60}` and positive exact
      `sin`, `cos` (`0 < r < 1`), `tan`, `cot` (`r > 0`) in `ExactNumber` (`Fraction` or `Radical` without `π`).
    - Polygon/dihedral mode (`allow_obtuse=True`): accepts degrees in `{30, 45, 60, 90, 120, 135, 150}` and unambiguous
      exact trig ratios on `(0°, 180°)`. An obtuse-allowed `sin` in `(0, 1)` without `cos_sign_hint in (-1, 1)` is
      rejected as `AMBIGUOUS_TRIG_BRANCH`.
    """
    if isinstance(value, bool) or value is None:
        raise TrigCertificateError("INVALID_ANGLE_VALUE", "angle/trig value cannot be None or boolean")
    if isinstance(value, float):
        raise TrigCertificateError("FLOAT_APPROXIMATION_FORBIDDEN", "float angle/trig value is forbidden")

    unit_norm = str(unit or "deg").strip().lower()
    if unit_norm in ("°", "degree", "degrees"):
        unit_norm = "deg"

    if unit_norm == "deg":
        parsed = parse_exact(value)
        if parsed is None:
            raise TrigCertificateError("INVALID_ANGLE_VALUE", f"cannot parse degree value {value!r}")
        if isinstance(parsed, Radical):
            raise TrigCertificateError("EXACT_DOMAIN_EXCEEDED", f"irrational degree measure {display(parsed)}° is unsupported")
        deg = Fraction(parsed)
        if deg <= 0 or deg >= 180:
            raise TrigCertificateError("NON_POSITIVE_OR_DEGENERATE_ANGLE", f"angle {deg}° must lie strictly in (0°, 180°)")
        if not allow_obtuse and deg >= 90:
            raise TrigCertificateError(
                "ACUTE_RIGHT_TRIANGLE_VIOLATION",
                f"non-right angle {deg}° in a right triangle must lie strictly in (0°, 90°)",
            )
        table = EXTENDED_EXACT_DEGREES if allow_obtuse else ACUTE_EXACT_DEGREES
        if deg not in table:
            supported = ", ".join(f"{int(k)}°" for k in sorted(table))
            raise TrigCertificateError(
                "EXACT_DOMAIN_EXCEEDED",
                f"angle {deg}° is outside exact trigonometric table ({supported})",
            )
        sin_sq, cos_sq, cos_sign = table[deg]
        return TrigAngleParams(unit="deg", raw_value=display(deg), sin_sq=sin_sq, cos_sq=cos_sq, cos_sign=cos_sign)

    if unit_norm in EXACT_TRIG_RATIO_UNITS:
        parsed = parse_exact(value)
        if parsed is None:
            raise TrigCertificateError("INVALID_TRIG_RATIO", f"cannot parse {unit_norm} value {value!r}")
        if isinstance(parsed, Radical) and parsed.mu != 0:
            raise TrigCertificateError("EXACT_DOMAIN_EXCEEDED", f"{unit_norm} value {display(parsed)} cannot contain π")
        sgn = sign(parsed)
        if not allow_obtuse:
            if sgn <= 0:
                raise TrigCertificateError(
                    "NON_POSITIVE_TRIG_RATIO",
                    f"acute right-triangle {unit_norm} must be strictly positive, got {display(parsed)}",
                )
            q = square(parsed)
            if unit_norm == "sin":
                if q >= 1:
                    raise TrigCertificateError("TRIG_RATIO_OUT_OF_RANGE", f"acute sin value has sin²={q} >= 1")
                return TrigAngleParams(unit="sin", raw_value=display(parsed), sin_sq=q, cos_sq=Fraction(1) - q, cos_sign=1)
            if unit_norm == "cos":
                if q >= 1:
                    raise TrigCertificateError("TRIG_RATIO_OUT_OF_RANGE", f"acute cos value has cos²={q} >= 1")
                return TrigAngleParams(unit="cos", raw_value=display(parsed), sin_sq=Fraction(1) - q, cos_sq=q, cos_sign=1)
            if unit_norm == "tan":
                denom = Fraction(1) + q
                return TrigAngleParams(
                    unit="tan",
                    raw_value=display(parsed),
                    sin_sq=q / denom,
                    cos_sq=Fraction(1) / denom,
                    cos_sign=1,
                )
            denom = Fraction(1) + q
            return TrigAngleParams(
                unit="cot",
                raw_value=display(parsed),
                sin_sq=Fraction(1) / denom,
                cos_sq=q / denom,
                cos_sign=1,
            )

        # allow_obtuse=True on (0°, 180°)
        if unit_norm == "sin":
            if sgn <= 0:
                raise TrigCertificateError("NON_POSITIVE_TRIG_RATIO", f"sin on (0°, 180°) must be > 0, got {display(parsed)}")
            q = square(parsed)
            if q > 1:
                raise TrigCertificateError("TRIG_RATIO_OUT_OF_RANGE", f"sin²={q} exceeds 1")
            if q == 1:
                return TrigAngleParams(unit="sin", raw_value=display(parsed), sin_sq=Fraction(1), cos_sq=Fraction(0), cos_sign=0)
            if cos_sign_hint not in (-1, 1):
                raise TrigCertificateError(
                    "AMBIGUOUS_TRIG_BRANCH",
                    f"sin={display(parsed)} on (0°, 180°) has two supplementary branches without an explicit acute/obtuse sign",
                )
            return TrigAngleParams(
                unit="sin",
                raw_value=display(parsed),
                sin_sq=q,
                cos_sq=Fraction(1) - q,
                cos_sign=cos_sign_hint,
            )
        if unit_norm == "cos":
            if sgn == 0:
                return TrigAngleParams(unit="cos", raw_value="0", sin_sq=Fraction(1), cos_sq=Fraction(0), cos_sign=0)
            q = square(parsed)
            if q >= 1:
                raise TrigCertificateError("TRIG_RATIO_OUT_OF_RANGE", f"cos²={q} >= 1 is degenerate on (0°, 180°)")
            return TrigAngleParams(
                unit="cos",
                raw_value=display(parsed),
                sin_sq=Fraction(1) - q,
                cos_sq=q,
                cos_sign=1 if sgn > 0 else -1,
            )
        if unit_norm == "tan":
            if sgn == 0:
                raise TrigCertificateError("NON_POSITIVE_OR_DEGENERATE_ANGLE", "tan=0 is degenerate on (0°, 180°)")
            q = square(parsed)
            denom = Fraction(1) + q
            return TrigAngleParams(
                unit="tan",
                raw_value=display(parsed),
                sin_sq=q / denom,
                cos_sq=Fraction(1) / denom,
                cos_sign=1 if sgn > 0 else -1,
            )
        # cot on (0°, 180°): cot(90°) == 0 is well-defined
        if sgn == 0:
            return TrigAngleParams(unit="cot", raw_value="0", sin_sq=Fraction(1), cos_sq=Fraction(0), cos_sign=0)
        q = square(parsed)
        denom = Fraction(1) + q
        return TrigAngleParams(
            unit="cot",
            raw_value=display(parsed),
            sin_sq=Fraction(1) / denom,
            cos_sq=q / denom,
            cos_sign=1 if sgn > 0 else -1,
        )

    raise TrigCertificateError("UNSUPPORTED_ANGLE_UNIT", f"unsupported angle or trig unit: {unit!r}")


def _format_symbolic_length(coef: ExactNumber, length_unit: str | None) -> str:
    """Format exact length `coef * unit^1` identically to `engine._hien_thi_ky_hieu(..., bac=1, ky_hieu=unit)`."""
    if not length_unit:
        return display(coef)
    he, can = (Fraction(coef.he), coef.can) if isinstance(coef, Radical) else (Fraction(coef), 1)
    pi = "π" if isinstance(coef, Radical) and getattr(coef, "mu", 0) else ""
    tu = "" if he.numerator == 1 else str(he.numerator)
    return (
        f"{tu}{pi}{length_unit}"
        + (f"√{can}" if can != 1 else "")
        + (f"/{he.denominator}" if he.denominator != 1 else "")
    )


def format_exact_length_expr(squared_coef: Fraction, *, length_unit: str | None = None) -> dict[str, Any]:
    """Build the canonical `exact_length_expr` structure from a positive rational squared coefficient."""
    sq = _strict_fraction(squared_coef, field_name="squared_coef")
    if sq <= 0:
        raise TrigCertificateError("NON_POSITIVE_DERIVED_LENGTH", f"derived length² must be > 0, got {sq}")
    try:
        coef = sqrt_rational(sq)
    except RadicalDomainError as exc:
        raise TrigCertificateError("EXACT_DOMAIN_EXCEEDED", f"cannot represent √({sq}) in exact radical domain: {exc}") from None
    if sign(coef) <= 0 or square(coef) != sq:
        raise TrigCertificateError("EXACT_EXPR_SELF_CHECK_FAILED", f"radical square self-check failed for {sq}")
    return {
        "coef_json": to_json(coef),
        "coef_str": display(coef),
        "squared_coef_str": str(sq),
        "unit_symbol": length_unit,
        "power": 1,
        "display": _format_symbolic_length(coef, length_unit),
    }


def _normalize_calls(calls: Sequence[Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(calls, (list, tuple)) or not calls:
        raise TrigCertificateError("MISSING_SOURCE_CALLS", "calls list must be non-empty")
    out: dict[str, dict[str, Any]] = {}
    for item in calls:
        if isinstance(item, Mapping):
            cid = item.get("id")
            fn = item.get("fn")
            raw_args = item.get("args")
            quotes = item.get("quotes")
            args = dict(raw_args) if isinstance(raw_args, Mapping) else (
                raw_args.model_dump() if hasattr(raw_args, "model_dump") else None
            )
        else:
            cid = getattr(item, "id", None)
            fn = getattr(item, "fn", None)
            raw_args = getattr(item, "args", None)
            quotes = getattr(item, "quotes", None)
            args = dict(raw_args) if isinstance(raw_args, Mapping) else (
                raw_args.model_dump() if hasattr(raw_args, "model_dump") else None
            )
        if not isinstance(cid, str) or not cid or not isinstance(fn, str) or not fn or not isinstance(args, dict):
            raise TrigCertificateError("MALFORMED_CALL_RECORD", f"malformed call record: {item!r}")
        if not isinstance(quotes, (list, tuple)) or not quotes or any(not isinstance(q, str) or not q.strip() for q in quotes):
            raise TrigCertificateError("MISSING_CALL_QUOTES", f"call {cid!r} has missing or empty source quotes")
        if cid in out:
            raise TrigCertificateError("DUPLICATE_CALL_ID", f"duplicate call id {cid!r}")
        out[cid] = {"id": cid, "fn": fn, "args": args, "quotes": list(quotes)}
    return out


def _is_zero_vec(v: list[Fraction]) -> bool:
    return v[0] == 0 and v[1] == 0 and v[2] == 0


def _collinear_vectors(u: list[Fraction], v: list[Fraction]) -> bool:
    return _is_zero_vec(vec_cross(u, v))


def _positively_collinear_rays(g_mat: list[list[Fraction]], u: list[Fraction], v: list[Fraction]) -> bool:
    """True iff `u` and `v` are non-zero and point in the exact same open half-line (`u x v == 0` and `<u, v>_G > 0`)."""
    if _is_zero_vec(u) or _is_zero_vec(v):
        return False
    return _collinear_vectors(u, v) and gram_dot(g_mat, u, v) > 0


def _point_on_line(pt: list[Fraction], a: list[Fraction], b: list[Fraction]) -> bool:
    ab = vec_sub(b, a)
    if _is_zero_vec(ab):
        return False
    return _collinear_vectors(ab, vec_sub(pt, a))


def _line_collinear_with_segment(
    line_pts: Sequence[str],
    seg_a: str,
    seg_b: str,
    pts: dict[str, list[Fraction]],
) -> bool:
    """True iff affine line `line_pts = [L0, L1]` coincides with affine line through `(seg_a, seg_b)`."""
    if len(line_pts) != 2 or line_pts[0] not in pts or line_pts[1] not in pts:
        return False
    if seg_a not in pts or seg_b not in pts or seg_a == seg_b:
        return False
    l0, l1 = pts[line_pts[0]], pts[line_pts[1]]
    if _is_zero_vec(vec_sub(l1, l0)):
        return False
    return _point_on_line(pts[seg_a], l0, l1) and _point_on_line(pts[seg_b], l0, l1)


def _plane_basis(
    plane_labels: Sequence[str],
    pts: dict[str, list[Fraction]],
) -> tuple[list[Fraction], list[Fraction], list[Fraction]]:
    """Find 3 non-collinear vertices `(p0, u1, u2)` among `plane_labels` and verify all listed vertices are coplanar."""
    coords = [pts[lbl] for lbl in plane_labels if lbl in pts]
    if len(coords) < 3 or len(set(plane_labels)) < 3:
        raise TrigCertificateError("DEGENERATE_PLANE_SUPPORT", f"plane {list(plane_labels)!r} lacks 3 placed vertices")
    p0 = coords[0]
    found: tuple[list[Fraction], list[Fraction]] | None = None
    for i in range(1, len(coords)):
        u1 = vec_sub(coords[i], p0)
        if _is_zero_vec(u1):
            continue
        for j in range(i + 1, len(coords)):
            u2 = vec_sub(coords[j], p0)
            if not _is_zero_vec(vec_cross(u1, u2)):
                found = (u1, u2)
                break
        if found is not None:
            break
    if found is None:
        raise TrigCertificateError("DEGENERATE_PLANE_SUPPORT", f"plane {list(plane_labels)!r} vertices are collinear")
    u1, u2 = found
    for c in coords[1:]:
        if not _point_in_plane_span(c, p0, u1, u2):
            raise TrigCertificateError("NON_COPLANAR_PLANE_SUPPORT", f"plane {list(plane_labels)!r} vertices are not coplanar")
    return p0, u1, u2


def _vec_perp_to_plane(
    g_mat: list[list[Fraction]],
    vec: list[Fraction],
    p0: list[Fraction],
    u1: list[Fraction],
    u2: list[Fraction],
) -> bool:
    return gram_dot(g_mat, vec, u1) == 0 and gram_dot(g_mat, vec, u2) == 0


def _resolve_and_verify_points(
    *,
    cert: Mapping[str, Any],
    points_by_label: Mapping[str, Sequence[Any]] | None,
    scene_objects: Mapping[str, Mapping[str, Any]] | None,
    g_mat: list[list[Fraction]],
) -> tuple[dict[str, list[Fraction]], set[str]]:
    """Resolve placed scene points and recompute/verify any `auxiliary_witness_points` from placed scene vertices."""
    if points_by_label is None and scene_objects is None:
        raise TrigCertificateError("MISSING_POINT_COORDINATES", "either points_by_label or scene_objects is required")

    scene_pts_by_ir: dict[str, list[Fraction]] = {}
    if scene_objects is not None:
        for oid, obj in scene_objects.items():
            if isinstance(obj, Mapping) and obj.get("type") == "point3":
                scene_pts_by_ir[oid] = _strict_vec3(obj.get("xyz", ()), label=oid)

    real_pts: dict[str, list[Fraction]] = {}
    if points_by_label is not None:
        for lbl, raw_xyz in points_by_label.items():
            vec = _strict_vec3(raw_xyz, label=lbl)
            ir = _ir_name(lbl)
            if scene_objects is not None:
                if ir not in scene_pts_by_ir:
                    raise TrigCertificateError("SCENE_POINT_MISSING", f"placed vertex {lbl!r} ({ir!r}) missing from scene_objects")
                if scene_pts_by_ir[ir] != vec:
                    raise TrigCertificateError(
                        "SCENE_POINT_MISMATCH",
                        f"point {lbl!r} coordinates {vec} differ from scene_objects[{ir!r}]={scene_pts_by_ir[ir]}",
                    )
            real_pts[lbl] = vec

    def lookup_real(lbl: str) -> list[Fraction]:
        if lbl in real_pts:
            return real_pts[lbl]
        ir = _ir_name(lbl)
        if ir in scene_pts_by_ir:
            real_pts[lbl] = scene_pts_by_ir[ir]
            return real_pts[lbl]
        raise TrigCertificateError("UNKNOWN_SCENE_VERTEX", f"vertex {lbl!r} is not a placed scene point")

    aux_raw = cert.get("auxiliary_witness_points") or {}
    if not isinstance(aux_raw, Mapping):
        raise TrigCertificateError("MALFORMED_AUXILIARY_POINTS", "auxiliary_witness_points must be a mapping")

    aux_labels: set[str] = set()
    all_pts: dict[str, list[Fraction]] = dict(real_pts)

    for aux_lbl, spec in aux_raw.items():
        if not isinstance(aux_lbl, str) or not aux_lbl or not isinstance(spec, Mapping):
            raise TrigCertificateError("MALFORMED_AUXILIARY_POINTS", f"invalid auxiliary point entry {aux_lbl!r}")
        rule = spec.get("rule")
        if rule not in VALID_AUXILIARY_POINT_RULES:
            raise TrigCertificateError("UNSUPPORTED_AUXILIARY_POINT_RULE", f"unsupported auxiliary point rule {rule!r}")
        claimed_xyz = _strict_vec3(spec.get("xyz", ()), label=aux_lbl)
        # If the auxiliary label is ALSO a real scene point, it must match scene_objects as well.
        ir_aux = _ir_name(aux_lbl)
        if ir_aux in scene_pts_by_ir and scene_pts_by_ir[ir_aux] != claimed_xyz:
            raise TrigCertificateError("SCENE_POINT_MISMATCH", f"auxiliary point {aux_lbl!r} disagrees with scene point3")

        if rule == "segment_midpoint":
            endpoints = spec.get("endpoints")
            if not isinstance(endpoints, (list, tuple)) or len(endpoints) != 2 or endpoints[0] == endpoints[1]:
                raise TrigCertificateError("MALFORMED_AUXILIARY_POINTS", f"{aux_lbl!r}: segment_midpoint needs 2 distinct endpoints")
            p_a, p_b = lookup_real(str(endpoints[0])), lookup_real(str(endpoints[1]))
            expected_xyz = [(p_a[k] + p_b[k]) * Fraction(1, 2) for k in range(3)]
            if claimed_xyz != expected_xyz:
                raise TrigCertificateError(
                    "AUXILIARY_POINT_TAMPERED",
                    f"{aux_lbl!r}: claimed midpoint {claimed_xyz} != exact midpoint {expected_xyz}",
                )
            coinc = spec.get("coincident_midpoint_of")
            if coinc is not None:
                if not isinstance(coinc, (list, tuple)) or len(coinc) != 2 or coinc[0] == coinc[1]:
                    raise TrigCertificateError("MALFORMED_AUXILIARY_POINTS", f"{aux_lbl!r}: invalid coincident_midpoint_of")
                p_c, p_d = lookup_real(str(coinc[0])), lookup_real(str(coinc[1]))
                expected_coinc = [(p_c[k] + p_d[k]) * Fraction(1, 2) for k in range(3)]
                if expected_coinc != expected_xyz:
                    raise TrigCertificateError(
                        "AUXILIARY_POINT_TAMPERED",
                        f"{aux_lbl!r}: diagonals {endpoints} and {coinc} do not share midpoint",
                    )
        elif rule == "orthogonal_projection_foot_on_line":
            from_pt_lbl = str(spec.get("from_point") or "")
            line_lbls = spec.get("line")
            if not from_pt_lbl or not isinstance(line_lbls, (list, tuple)) or len(line_lbls) != 2:
                raise TrigCertificateError("MALFORMED_AUXILIARY_POINTS", f"{aux_lbl!r}: invalid orthogonal_projection_foot_on_line")
            p_from = lookup_real(from_pt_lbl)
            l_a, l_b = lookup_real(str(line_lbls[0])), lookup_real(str(line_lbls[1]))
            if not _point_on_line(claimed_xyz, l_a, l_b):
                raise TrigCertificateError("AUXILIARY_POINT_TAMPERED", f"{aux_lbl!r} does not lie on line {line_lbls}")
            if gram_dot(g_mat, vec_sub(p_from, claimed_xyz), vec_sub(l_b, l_a)) != 0:
                raise TrigCertificateError("AUXILIARY_POINT_TAMPERED", f"{aux_lbl!r} is not orthogonal foot on line {line_lbls}")
        elif rule == "orthogonal_projection_foot_on_plane":
            from_pt_lbl = str(spec.get("from_point") or "")
            plane_lbls = spec.get("plane")
            if not from_pt_lbl or not isinstance(plane_lbls, (list, tuple)) or len(plane_lbls) < 3:
                raise TrigCertificateError("MALFORMED_AUXILIARY_POINTS", f"{aux_lbl!r}: invalid orthogonal_projection_foot_on_plane")
            p_from = lookup_real(from_pt_lbl)
            for pl in plane_lbls:
                lookup_real(str(pl))
            p0, u1, u2 = _plane_basis([str(pl) for pl in plane_lbls], real_pts)
            if not _point_in_plane_span(claimed_xyz, p0, u1, u2):
                raise TrigCertificateError("AUXILIARY_POINT_TAMPERED", f"{aux_lbl!r} does not lie in plane {plane_lbls}")
            if not _vec_perp_to_plane(g_mat, vec_sub(p_from, claimed_xyz), p0, u1, u2):
                raise TrigCertificateError("AUXILIARY_POINT_TAMPERED", f"{aux_lbl!r} is not orthogonal foot on plane {plane_lbls}")

        aux_labels.add(aux_lbl)
        all_pts[aux_lbl] = claimed_xyz

    # Populate any referenced real labels from scene_objects on demand
    def ensure_label(lbl: str) -> None:
        if lbl not in all_pts:
            all_pts[lbl] = lookup_real(lbl)

    tri = cert.get("derived_right_triangle")
    if isinstance(tri, (list, tuple)):
        for v in tri:
            if isinstance(v, str) and v:
                ensure_label(v)

    return all_pts, aux_labels


def _collect_all_call_labels(calls_by_id: Mapping[str, Mapping[str, Any]]) -> set[str]:
    labels: set[str] = set()

    def walk(val: Any) -> None:
        if isinstance(val, str) and len(val) <= 6 and val[0:1].isupper():
            labels.add(val)
        elif isinstance(val, (list, tuple)):
            for x in val:
                walk(x)
        elif isinstance(val, Mapping):
            for x in val.values():
                walk(x)

    for c in calls_by_id.values():
        walk(c["args"])
    return labels


def _verify_perpendicularity_justification(
    *,
    just: Any,
    v_right: str,
    v_adj: str,
    v_opp: str,
    calls_by_id: Mapping[str, Mapping[str, Any]],
    source_premise_ids: set[str],
    pts: dict[str, list[Fraction]],
    aux_specs: Mapping[str, Any],
    g_mat: list[list[Fraction]],
) -> None:
    """Verify both exact Gram orthogonality AND deductive justification from verified premise calls."""
    if not isinstance(just, Mapping):
        raise TrigCertificateError("MISSING_PERPENDICULARITY_JUSTIFICATION", "perpendicularity_justification must be a dict")
    rule = just.get("rule")
    if rule not in VALID_PERPENDICULARITY_RULES:
        raise TrigCertificateError("INVALID_PERPENDICULARITY_RULE", f"unsupported perpendicularity rule {rule!r}")
    if just.get("gram_dot_zero_verified") is not True:
        raise TrigCertificateError("GRAM_ORTHOGONALITY_FLAG_MISSING", "gram_dot_zero_verified must be True")

    supp_ids = just.get("supporting_calls")
    if not isinstance(supp_ids, (list, tuple)) or not supp_ids:
        raise TrigCertificateError("MISSING_PERPENDICULARITY_CALLS", "perpendicularity_justification.supporting_calls required")
    supp_calls: list[Mapping[str, Any]] = []
    for cid in supp_ids:
        if not isinstance(cid, str) or cid not in calls_by_id or cid not in source_premise_ids:
            raise TrigCertificateError(
                "UNVERIFIED_SUPPORTING_CALL",
                f"perpendicularity supporting_call {cid!r} is missing from calls or source_premises",
            )
        supp_calls.append(calls_by_id[cid])

    u_adj = vec_sub(pts[v_adj], pts[v_right])
    u_opp = vec_sub(pts[v_opp], pts[v_right])
    if gram_dot(g_mat, u_adj, u_opp) != 0:
        raise TrigCertificateError(
            "RIGHT_ANGLE_GRAM_VIOLATION",
            f"vectors at {v_right!r} are not orthogonal in Gram metric G",
        )

    deductive_ok = False

    if rule == "explicit_right_angle":
        for c in supp_calls:
            fn, a = c["fn"], c["args"]
            if fn == "right_angle" and a.get("vertex") == v_right:
                rays = a.get("rays") or ()
                if len(rays) == 2 and rays[0] in pts and rays[1] in pts:
                    r_a = vec_sub(pts[rays[0]], pts[v_right])
                    r_b = vec_sub(pts[rays[1]], pts[v_right])
                    if (_collinear_vectors(r_a, u_adj) and _collinear_vectors(r_b, u_opp)) or (
                        _collinear_vectors(r_a, u_opp) and _collinear_vectors(r_b, u_adj)
                    ):
                        deductive_ok = True
                        break
            elif fn == "vertex_angle" and a.get("vertex") == v_right:
                params = exact_trig_angle_params(a.get("value"), a.get("unit", "deg"), allow_obtuse=True)
                rays = a.get("rays") or ()
                if params.cos_sq == 0 and len(rays) == 2 and rays[0] in pts and rays[1] in pts:
                    r_a = vec_sub(pts[rays[0]], pts[v_right])
                    r_b = vec_sub(pts[rays[1]], pts[v_right])
                    if (_collinear_vectors(r_a, u_adj) and _collinear_vectors(r_b, u_opp)) or (
                        _collinear_vectors(r_a, u_opp) and _collinear_vectors(r_b, u_adj)
                    ):
                        deductive_ok = True
                        break
            elif fn == "rectangle" or (fn == "regular_polygon" and len(a.get("vertices") or ()) == 4):
                verts = list(a.get("vertices") or ())
                if len(verts) == 4 and v_right in verts:
                    idx = verts.index(v_right)
                    prev_v, next_v = verts[(idx - 1) % 4], verts[(idx + 1) % 4]
                    if prev_v in pts and next_v in pts:
                        r_a = vec_sub(pts[prev_v], pts[v_right])
                        r_b = vec_sub(pts[next_v], pts[v_right])
                        if (_collinear_vectors(r_a, u_adj) and _collinear_vectors(r_b, u_opp)) or (
                            _collinear_vectors(r_a, u_opp) and _collinear_vectors(r_b, u_adj)
                        ):
                            deductive_ok = True
                            break

    elif rule == "explicit_perpendicular_lines":
        for c in supp_calls:
            if c["fn"] == "perpendicular_lines":
                l1, l2 = c["args"].get("line1") or (), c["args"].get("line2") or ()
                if (
                    _line_collinear_with_segment(l1, v_right, v_adj, pts)
                    and _line_collinear_with_segment(l2, v_right, v_opp, pts)
                ) or (
                    _line_collinear_with_segment(l1, v_right, v_opp, pts)
                    and _line_collinear_with_segment(l2, v_right, v_adj, pts)
                ):
                    deductive_ok = True
                    break

    elif rule == "line_perpendicular_to_plane":
        for leg_perp, leg_plane in ((v_opp, v_adj), (v_adj, v_opp)):
            vec_perp = vec_sub(pts[leg_perp], pts[v_right])
            for c in supp_calls:
                fn, a = c["fn"], c["args"]
                if fn == "perpendicular_line_plane":
                    line_lbls, plane_lbls = a.get("line") or (), a.get("plane") or ()
                    if _line_collinear_with_segment(line_lbls, v_right, leg_perp, pts):
                        p0, u1, u2 = _plane_basis(plane_lbls, pts)
                        if (
                            _point_in_plane_span(pts[v_right], p0, u1, u2)
                            and _point_in_plane_span(pts[leg_plane], p0, u1, u2)
                            and _vec_perp_to_plane(g_mat, vec_perp, p0, u1, u2)
                        ):
                            deductive_ok = True
                            break
                elif fn == "orthogonal_projection":
                    plane_lbls = a.get("plane") or ()
                    pt_lbl, img_lbl = a.get("point"), a.get("image")
                    if img_lbl == v_right and pt_lbl in pts and _line_collinear_with_segment([pt_lbl, img_lbl], v_right, leg_perp, pts):
                        p0, u1, u2 = _plane_basis(plane_lbls, pts)
                        if (
                            _point_in_plane_span(pts[v_right], p0, u1, u2)
                            and _point_in_plane_span(pts[leg_plane], p0, u1, u2)
                            and _vec_perp_to_plane(g_mat, vec_perp, p0, u1, u2)
                        ):
                            deductive_ok = True
                            break
                elif fn == "altitude":
                    apex_lbl, foot_lbl = a.get("apex"), a.get("foot")
                    if foot_lbl == v_right and apex_lbl in pts and _line_collinear_with_segment([apex_lbl, foot_lbl], v_right, leg_perp, pts):
                        # Find the solid base plane in calls_by_id
                        for sc in calls_by_id.values():
                            if sc["fn"] in ("pyramid", "regular_pyramid") and sc["args"].get("apex") == apex_lbl:
                                base_lbls = sc["args"].get("base") or ()
                                p0, u1, u2 = _plane_basis(base_lbls, pts)
                                if (
                                    _point_in_plane_span(pts[v_right], p0, u1, u2)
                                    and _point_in_plane_span(pts[leg_plane], p0, u1, u2)
                                    and _vec_perp_to_plane(g_mat, vec_perp, p0, u1, u2)
                                ):
                                    deductive_ok = True
                                    break
                    if deductive_ok:
                        break
                elif fn == "prism" and a.get("right") is True:
                    base_lbls = list(a.get("base") or ())
                    top_lbls = list(a.get("top") or ())
                    lat_edges = [(base_lbls[i], top_lbls[i]) for i in range(min(len(base_lbls), len(top_lbls)))]
                    if any(_line_collinear_with_segment(le, v_right, leg_perp, pts) for le in lat_edges):
                        for face_lbls in (base_lbls, top_lbls):
                            p0, u1, u2 = _plane_basis(face_lbls, pts)
                            if (
                                _point_in_plane_span(pts[v_right], p0, u1, u2)
                                and _point_in_plane_span(pts[leg_plane], p0, u1, u2)
                                and _vec_perp_to_plane(g_mat, vec_perp, p0, u1, u2)
                            ):
                                deductive_ok = True
                                break
                    if deductive_ok:
                        break
                elif fn == "regular_pyramid":
                    apex_lbl = a.get("apex")
                    base_lbls = list(a.get("base") or ())
                    if apex_lbl == leg_perp and len(base_lbls) in (3, 4, 6) and all(b in pts for b in base_lbls):
                        # Base center of regular k-gon is the arithmetic average of its vertices
                        n_b = len(base_lbls)
                        center = [
                            sum(pts[b][k] for b in base_lbls) * Fraction(1, n_b)
                            for k in range(3)
                        ]
                        p0, u1, u2 = _plane_basis(base_lbls, pts)
                        if (
                            pts[v_right] == center
                            and _point_in_plane_span(pts[leg_plane], p0, u1, u2)
                            and _vec_perp_to_plane(g_mat, vec_perp, p0, u1, u2)
                        ):
                            deductive_ok = True
                            break
            if deductive_ok:
                break

    elif rule == "orthogonal_projection_on_line":
        for leg_perp, leg_line in ((v_opp, v_adj), (v_adj, v_opp)):
            for c in supp_calls:
                if c["fn"] == "orthogonal_projection_line":
                    a = c["args"]
                    line_lbls = a.get("line")
                    if (
                        a.get("image") == v_right
                        and a.get("point") == leg_perp
                        and isinstance(line_lbls, (list, tuple))
                        and _line_collinear_with_segment(line_lbls, v_right, leg_line, pts)
                    ):
                        deductive_ok = True
                        break
            if deductive_ok:
                break
        if not deductive_ok and v_right in aux_specs:
            spec = aux_specs[v_right]
            if spec.get("rule") == "orthogonal_projection_foot_on_line":
                from_lbl = spec.get("from_point")
                line_lbls = spec.get("line") or ()
                for leg_perp, leg_line in ((v_opp, v_adj), (v_adj, v_opp)):
                    if from_lbl == leg_perp and _line_collinear_with_segment(line_lbls, v_right, leg_line, pts):
                        deductive_ok = True
                        break

    elif rule == "rhombus_perpendicular_diagonals":
        for c in supp_calls:
            fn, a = c["fn"], c["args"]
            verts = list(a.get("vertices") or ())
            if fn in ("rhombus", "regular_polygon") and len(verts) == 4 and all(v in pts for v in verts):
                mid_02 = [(pts[verts[0]][k] + pts[verts[2]][k]) * Fraction(1, 2) for k in range(3)]
                mid_13 = [(pts[verts[1]][k] + pts[verts[3]][k]) * Fraction(1, 2) for k in range(3)]
                if pts[v_right] == mid_02 == mid_13:
                    d1 = vec_sub(pts[verts[2]], pts[verts[0]])
                    d2 = vec_sub(pts[verts[3]], pts[verts[1]])
                    if gram_dot(g_mat, d1, d2) == 0 and (
                        (_collinear_vectors(u_adj, d1) and _collinear_vectors(u_opp, d2))
                        or (_collinear_vectors(u_adj, d2) and _collinear_vectors(u_opp, d1))
                    ):
                        deductive_ok = True
                        break

    elif rule == "face_altitude_perpendicular_base":
        # (face) ⊥ (base) along shared edge E = [e0, e1], with foot v_right on E and [v_right, leg_perp] ⊥ E in (face)
        for leg_perp, leg_plane in ((v_opp, v_adj), (v_adj, v_opp)):
            vec_perp = vec_sub(pts[leg_perp], pts[v_right])
            for c in supp_calls:
                if c["fn"] == "face_perpendicular_base":
                    face_lbls = list(c["args"].get("face") or ())
                    base_lbls = list(c["args"].get("base") or ())
                    shared = [x for x in face_lbls if x in set(base_lbls)]
                    if len(shared) >= 2 and all(x in pts for x in face_lbls + base_lbls):
                        pf0, fu1, fu2 = _plane_basis(face_lbls, pts)
                        pb0, bu1, bu2 = _plane_basis(base_lbls, pts)
                        e_vec = vec_sub(pts[shared[1]], pts[shared[0]])
                        if (
                            _point_on_line(pts[v_right], pts[shared[0]], pts[shared[1]])
                            and _point_in_plane_span(pts[leg_perp], pf0, fu1, fu2)
                            and gram_dot(g_mat, vec_perp, e_vec) == 0
                            and _point_in_plane_span(pts[leg_plane], pb0, bu1, bu2)
                            and _vec_perp_to_plane(g_mat, vec_perp, pb0, bu1, bu2)
                        ):
                            deductive_ok = True
                            break
            if deductive_ok:
                break

    elif rule == "deductive_two_lines_in_plane":
        # Requires >= 2 perpendicular_lines / right_angle calls showing [v_right, leg_perp] ⊥ two non-collinear lines
        # lying in a common plane that also contains [v_right, leg_plane].
        for leg_perp, leg_plane in ((v_opp, v_adj), (v_adj, v_opp)):
            u_perp = vec_sub(pts[leg_perp], pts[v_right])
            u_target_in_plane = vec_sub(pts[leg_plane], pts[v_right])
            perp_dirs: list[list[Fraction]] = []
            for c in supp_calls:
                if c["fn"] == "perpendicular_lines":
                    l1, l2 = c["args"].get("line1") or (), c["args"].get("line2") or ()
                    if _line_collinear_with_segment(l1, v_right, leg_perp, pts) and len(l2) == 2 and all(x in pts for x in l2):
                        perp_dirs.append(vec_sub(pts[l2[1]], pts[l2[0]]))
                    elif _line_collinear_with_segment(l2, v_right, leg_perp, pts) and len(l1) == 2 and all(x in pts for x in l1):
                        perp_dirs.append(vec_sub(pts[l1[1]], pts[l1[0]]))
                elif c["fn"] == "right_angle":
                    vert = c["args"].get("vertex")
                    rays = c["args"].get("rays") or ()
                    if vert in pts and len(rays) == 2 and all(x in pts for x in rays):
                        if _line_collinear_with_segment([vert, rays[0]], v_right, leg_perp, pts):
                            perp_dirs.append(vec_sub(pts[rays[1]], pts[vert]))
                        elif _line_collinear_with_segment([vert, rays[1]], v_right, leg_perp, pts):
                            perp_dirs.append(vec_sub(pts[rays[0]], pts[vert]))
            for i in range(len(perp_dirs)):
                for j in range(i + 1, len(perp_dirs)):
                    d1, d2 = perp_dirs[i], perp_dirs[j]
                    n_plane = vec_cross(d1, d2)
                    if (
                        not _is_zero_vec(n_plane)
                        and gram_dot(g_mat, u_perp, d1) == 0
                        and gram_dot(g_mat, u_perp, d2) == 0
                        and (
                            n_plane[0] * u_target_in_plane[0]
                            + n_plane[1] * u_target_in_plane[1]
                            + n_plane[2] * u_target_in_plane[2]
                        ) == 0
                    ):
                        deductive_ok = True
                        break
                if deductive_ok:
                    break
            if deductive_ok:
                break

    if not deductive_ok:
        raise TrigCertificateError(
            "UNPROVEN_RIGHT_ANGLE",
            f"supporting_calls {list(supp_ids)!r} do not deductively prove right angle at {v_right!r} under rule {rule!r}",
        )


def _segments_equal_by_calls(
    seg1: frozenset[str],
    seg2: frozenset[str],
    supp_calls: Sequence[Mapping[str, Any]],
) -> bool:
    if seg1 == seg2:
        return True
    adj: dict[frozenset[str], set[frozenset[str]]] = {}

    def link(a: frozenset[str], b: frozenset[str]) -> None:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    for c in supp_calls:
        fn, a = c["fn"], c["args"]
        if fn == "equal_length":
            sa = frozenset(a.get("segment_a") or ())
            sb = frozenset(a.get("segment_b") or ())
            if len(sa) == 2 and len(sb) == 2:
                link(sa, sb)
        elif fn in ("regular_polygon", "rhombus"):
            verts = list(a.get("vertices") or ())
            edges = [frozenset((verts[i], verts[(i + 1) % len(verts)])) for i in range(len(verts))]
            for i in range(len(edges)):
                for j in range(i + 1, len(edges)):
                    link(edges[i], edges[j])
        elif fn == "regular_pyramid":
            apex = a.get("apex")
            base = list(a.get("base") or ())
            lat = [frozenset((apex, b)) for b in base if apex and b]
            for i in range(len(lat)):
                for j in range(i + 1, len(lat)):
                    link(lat[i], lat[j])

    seen = {seg1}
    stack = [seg1]
    while stack:
        cur = stack.pop()
        if cur == seg2:
            return True
        for nxt in adj.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def _verify_angle_witness(
    *,
    aw: Any,
    v_right: str,
    v_adj: str,
    v_opp: str,
    adj_sq: Fraction,
    opp_sq: Fraction,
    hyp_sq: Fraction,
    calls_by_id: Mapping[str, Mapping[str, Any]],
    source_premise_ids: set[str],
    pts: dict[str, list[Fraction]],
    g_mat: list[list[Fraction]],
) -> tuple[Fraction, Fraction]:
    """Verify `angle_witness` topology, Gram acuteness, cosine/sine identities, and source premise grounding."""
    if not isinstance(aw, Mapping):
        raise TrigCertificateError("MISSING_ANGLE_WITNESS", "angle_witness must be a dict")
    kind = aw.get("kind")
    if kind not in VALID_ANGLE_WITNESS_KINDS:
        raise TrigCertificateError("INVALID_ANGLE_WITNESS_KIND", f"unsupported angle_witness.kind {kind!r}")
    if aw.get("vertex") != v_adj:
        raise TrigCertificateError(
            "ANGLE_WITNESS_VERTEX_MISMATCH",
            f"angle_witness.vertex={aw.get('vertex')!r} must equal derived_right_triangle[1]={v_adj!r}",
        )
    if list(aw.get("ray_1") or ()) != [v_adj, v_right]:
        raise TrigCertificateError(
            "ANGLE_WITNESS_RAY_MISMATCH",
            f"angle_witness.ray_1={aw.get('ray_1')!r} must equal adjacent ray {[v_adj, v_right]!r}",
        )
    if list(aw.get("ray_2") or ()) != [v_adj, v_opp]:
        raise TrigCertificateError(
            "ANGLE_WITNESS_RAY_MISMATCH",
            f"angle_witness.ray_2={aw.get('ray_2')!r} must equal hypotenuse ray {[v_adj, v_opp]!r}",
        )
    if aw.get("domain") != "(0°, 90°)":
        raise TrigCertificateError("ANGLE_WITNESS_DOMAIN_INVALID", "angle_witness.domain must be '(0°, 90°)'")

    sin_sq = _strict_fraction(aw.get("sin_sq"), field_name="angle_witness.sin_sq")
    cos_sq = _strict_fraction(aw.get("cos_sq"), field_name="angle_witness.cos_sq")
    if not (Fraction(0) < sin_sq < Fraction(1) and Fraction(0) < cos_sq < Fraction(1) and sin_sq + cos_sq == Fraction(1)):
        raise TrigCertificateError(
            "ANGLE_WITNESS_DOMAIN_INVALID",
            f"invalid acute (sin², cos²)=({sin_sq}, {cos_sq}); need 0 < sin², cos² < 1 and sin² + cos² == 1",
        )

    r1 = vec_sub(pts[v_right], pts[v_adj])  # V_adj -> V_right (adjacent leg)
    r2 = vec_sub(pts[v_opp], pts[v_adj])    # V_adj -> V_opp (hypotenuse)
    dot12 = gram_dot(g_mat, r1, r2)
    if dot12 <= 0:
        raise TrigCertificateError("ANGLE_NOT_ACUTE_IN_GRAM", f"angle at {v_adj!r} is not strictly acute (<r1, r2>_G={dot12})")
    if dot12 * dot12 != cos_sq * adj_sq * hyp_sq:
        raise TrigCertificateError(
            "ANGLE_COSINE_GRAM_MISMATCH",
            f"Gram cosine² {dot12 * dot12}/{adj_sq * hyp_sq} != angle_witness.cos_sq {cos_sq}",
        )
    if opp_sq != sin_sq * hyp_sq or adj_sq != cos_sq * hyp_sq:
        raise TrigCertificateError(
            "ANGLE_TRIG_LEG_MISMATCH",
            f"triangle legs (adj²={adj_sq}, opp²={opp_sq}, hyp²={hyp_sq}) violate (sin²={sin_sq}, cos²={cos_sq})",
        )

    supp_raw = aw.get("supporting_calls")
    if supp_raw is None and aw.get("supporting_call") is not None:
        supp_raw = [aw.get("supporting_call")]
    supp_ids = list(supp_raw or ())
    for cid in supp_ids:
        if not isinstance(cid, str) or cid not in calls_by_id or cid not in source_premise_ids:
            raise TrigCertificateError(
                "UNVERIFIED_SUPPORTING_CALL",
                f"angle_witness supporting_call {cid!r} missing from calls or source_premises",
            )
    supp_calls = [calls_by_id[cid] for cid in supp_ids]

    if kind == "pythagorean_lengths":
        return sin_sq, cos_sq

    if not supp_calls:
        raise TrigCertificateError("MISSING_ANGLE_WITNESS_CALL", f"angle_witness kind={kind!r} requires supporting_calls")

    if kind == "vertex_angle":
        c = supp_calls[0]
        if c["fn"] != "vertex_angle" or c["args"].get("vertex") != v_adj:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: vertex_angle vertex != {v_adj!r}")
        rays = c["args"].get("rays") or ()
        if len(rays) != 2 or rays[0] not in pts or rays[1] not in pts:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: vertex_angle rays not placed")
        ca = vec_sub(pts[rays[0]], pts[v_adj])
        cb = vec_sub(pts[rays[1]], pts[v_adj])
        if not (
            (_positively_collinear_rays(g_mat, ca, r1) and _positively_collinear_rays(g_mat, cb, r2))
            or (_positively_collinear_rays(g_mat, ca, r2) and _positively_collinear_rays(g_mat, cb, r1))
        ):
            raise TrigCertificateError(
                "ANGLE_WITNESS_SOURCE_MISMATCH",
                f"{c['id']}: vertex_angle rays {list(rays)!r} do not match right-triangle rays at {v_adj!r}",
            )
        params = exact_trig_angle_params(c["args"].get("value"), c["args"].get("unit", "deg"), allow_obtuse=False)
        if (params.sin_sq, params.cos_sq) != (sin_sq, cos_sq):
            raise TrigCertificateError("ANGLE_WITNESS_VALUE_MISMATCH", f"{c['id']}: trig params mismatch")

    elif kind == "line_plane_angle":
        c = supp_calls[0]
        if c["fn"] != "line_plane_angle":
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: expected line_plane_angle")
        line_lbls = c["args"].get("line") or ()
        plane_lbls = c["args"].get("plane") or ()
        if not _line_collinear_with_segment(line_lbls, v_adj, v_opp, pts):
            raise TrigCertificateError(
                "ANGLE_WITNESS_SOURCE_MISMATCH",
                f"{c['id']}: line {list(line_lbls)!r} does not coincide with hypotenuse [{v_adj}, {v_opp}]",
            )
        p0, u1, u2 = _plane_basis(plane_lbls, pts)
        if not _point_in_plane_span(pts[v_adj], p0, u1, u2):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: {v_adj!r} is not in plane {list(plane_lbls)!r}")
        if not _point_in_plane_span(pts[v_right], p0, u1, u2):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: foot {v_right!r} is not in plane {list(plane_lbls)!r}")
        if _point_in_plane_span(pts[v_opp], p0, u1, u2):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: {v_opp!r} lies in plane {list(plane_lbls)!r}")
        # Critical soundness check: [v_right, v_opp] must be orthogonal to the ENTIRE plane, not merely to ray_1!
        if not _vec_perp_to_plane(g_mat, vec_sub(pts[v_opp], pts[v_right]), p0, u1, u2):
            raise TrigCertificateError(
                "NON_PROJECTION_BASE_RAY",
                f"{c['id']}: {v_right!r} is not the orthogonal projection of {v_opp!r} onto plane {list(plane_lbls)!r}",
            )
        params = exact_trig_angle_params(c["args"].get("value"), c["args"].get("unit", "deg"), allow_obtuse=False)
        if (params.sin_sq, params.cos_sq) != (sin_sq, cos_sq):
            raise TrigCertificateError("ANGLE_WITNESS_VALUE_MISMATCH", f"{c['id']}: trig params mismatch")

    elif kind == "dihedral_angle":
        c = supp_calls[0]
        fn, a = c["fn"], c["args"]
        if fn == "dihedral_angle":
            edge = list(a.get("edge") or ())
            pa, pb = a.get("point_a"), a.get("point_b")
            if len(edge) != 2 or not pa or not pb:
                raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: malformed dihedral_angle")
            plane1_lbls = [*edge, pa]
            plane2_lbls = [*edge, pb]
        elif fn == "plane_plane_angle":
            plane1_lbls = list(a.get("plane1") or ())
            plane2_lbls = list(a.get("plane2") or ())
        else:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: expected dihedral_angle or plane_plane_angle")
        p10, p1u1, p1u2 = _plane_basis(plane1_lbls, pts)
        p20, p2u1, p2u2 = _plane_basis(plane2_lbls, pts)
        if not (_point_in_plane_span(pts[v_adj], p10, p1u1, p1u2) and _point_in_plane_span(pts[v_adj], p20, p2u1, p2u2)):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: {v_adj!r} does not lie on plane intersection")
        # Intersection line direction is cross(n1, n2); both r1 and r2 must be Gram-orthogonal to the intersection edge
        n1 = vec_cross(p1u1, p1u2)
        n2 = vec_cross(p2u1, p2u2)
        edge_dir = vec_cross(n1, n2)
        if _is_zero_vec(edge_dir):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: parallel planes in dihedral witness")
        if gram_dot(g_mat, r1, edge_dir) != 0 or gram_dot(g_mat, r2, edge_dir) != 0:
            raise TrigCertificateError(
                "ANGLE_WITNESS_SOURCE_MISMATCH",
                f"{c['id']}: dihedral witness rays at {v_adj!r} are not orthogonal to intersection edge",
            )
        in_12 = _point_in_plane_span(pts[v_right], p10, p1u1, p1u2) and _point_in_plane_span(pts[v_opp], p20, p2u1, p2u2)
        in_21 = _point_in_plane_span(pts[v_right], p20, p2u1, p2u2) and _point_in_plane_span(pts[v_opp], p10, p1u1, p1u2)
        if not (in_12 or in_21):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: rays do not lie in the two planes")
        params = exact_trig_angle_params(a.get("value"), a.get("unit", "deg"), allow_obtuse=False)
        if (params.sin_sq, params.cos_sq) != (sin_sq, cos_sq):
            raise TrigCertificateError("ANGLE_WITNESS_VALUE_MISMATCH", f"{c['id']}: trig params mismatch")

    elif kind == "line_line_angle":
        c = supp_calls[0]
        if c["fn"] != "line_line_angle":
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: expected line_line_angle")
        l1 = c["args"].get("line1") or ()
        l2 = c["args"].get("line2") or ()
        if len(l1) != 2 or len(l2) != 2 or any(x not in pts for x in (*l1, *l2)):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: line endpoints not placed")
        d1 = vec_sub(pts[l1[1]], pts[l1[0]])
        d2 = vec_sub(pts[l2[1]], pts[l2[0]])
        if not ((_collinear_vectors(d1, r1) and _collinear_vectors(d2, r2)) or (_collinear_vectors(d1, r2) and _collinear_vectors(d2, r1))):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: line directions do not match rays")
        params = exact_trig_angle_params(c["args"].get("value"), c["args"].get("unit", "deg"), allow_obtuse=False)
        if (params.sin_sq, params.cos_sq) != (sin_sq, cos_sq):
            raise TrigCertificateError("ANGLE_WITNESS_VALUE_MISMATCH", f"{c['id']}: trig params mismatch")

    elif kind == "rhombus_bisected_vertex_angle":
        angle_call = next((c for c in supp_calls if c["fn"] == "vertex_angle"), None)
        rhombus_call = next((c for c in supp_calls if c["fn"] == "rhombus"), None)
        if angle_call is None or rhombus_call is None:
            raise TrigCertificateError(
                "ANGLE_WITNESS_SOURCE_MISMATCH",
                "rhombus_bisected_vertex_angle requires both vertex_angle and rhombus supporting_calls",
            )
        verts = list(rhombus_call["args"].get("vertices") or ())
        if len(verts) != 4 or v_adj not in verts or v_opp not in verts:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", "rhombus vertices do not contain v_adj and v_opp")
        i_adj = verts.index(v_adj)
        if v_opp not in (verts[(i_adj - 1) % 4], verts[(i_adj + 1) % 4]):
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"[{v_adj}, {v_opp}] is not a side of rhombus {verts}")
        a_vert = angle_call["args"].get("vertex")
        a_rays = set(angle_call["args"].get("rays") or ())
        if a_vert not in verts:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"vertex_angle at {a_vert!r} is not on rhombus {verts}")
        i_av = verts.index(a_vert)
        if a_rays != {verts[(i_av - 1) % 4], verts[(i_av + 1) % 4]}:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"vertex_angle rays {a_rays} are not rhombus sides at {a_vert!r}")
        params = exact_trig_angle_params(angle_call["args"].get("value"), angle_call["args"].get("unit", "deg"), allow_obtuse=True)
        cos_abs = sqrt_rational(params.cos_sq)
        if isinstance(cos_abs, Radical):
            raise TrigCertificateError("EXACT_DOMAIN_EXCEEDED", "rhombus vertex angle has irrational cos, outside rational Gram domain")
        signed_cos_given = Fraction(params.cos_sign) * Fraction(cos_abs)
        # Opposite rhombus vertices have equal angles; adjacent rhombus vertices have supplementary angles (cos flips sign).
        same_parity = (i_av % 2) == (i_adj % 2)
        cos_at_v_adj = signed_cos_given if same_parity else -signed_cos_given
        expected_cos_sq = (Fraction(1) + cos_at_v_adj) * Fraction(1, 2)
        expected_sin_sq = (Fraction(1) - cos_at_v_adj) * Fraction(1, 2)
        if (expected_sin_sq, expected_cos_sq) != (sin_sq, cos_sq):
            raise TrigCertificateError(
                "ANGLE_WITNESS_VALUE_MISMATCH",
                f"rhombus half-angle expected (sin², cos²)=({expected_sin_sq}, {expected_cos_sq}), got ({sin_sq}, {cos_sq})",
            )

    elif kind == "equal_legs_witness":
        if (sin_sq, cos_sq) != (Fraction(1, 2), Fraction(1, 2)):
            raise TrigCertificateError("ANGLE_WITNESS_VALUE_MISMATCH", "equal_legs_witness requires sin²=cos²=1/2")
        if not _segments_equal_by_calls(frozenset({v_right, v_adj}), frozenset({v_right, v_opp}), supp_calls):
            raise TrigCertificateError(
                "ANGLE_WITNESS_SOURCE_MISMATCH",
                f"supporting_calls do not establish |{v_right}{v_adj}| == |{v_right}{v_opp}|",
            )

    elif kind == "leg_ratio_witness":
        c = supp_calls[0]
        if c["fn"] != "segment_ratio":
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: expected segment_ratio")
        sa = frozenset(c["args"].get("segment_a") or ())
        sb = frozenset(c["args"].get("segment_b") or ())
        r_parsed = parse_exact(c["args"].get("ratio"))
        if r_parsed is None or (isinstance(r_parsed, Radical) and r_parsed.mu != 0) or sign(r_parsed) <= 0:
            raise TrigCertificateError("INVALID_TRIG_RATIO", f"{c['id']}: invalid segment_ratio value")
        r_sq = square(r_parsed)
        s_opp = frozenset({v_right, v_opp})
        s_adj = frozenset({v_right, v_adj})
        if sa == s_opp and sb == s_adj:
            exp_sin_sq, exp_cos_sq = r_sq / (Fraction(1) + r_sq), Fraction(1) / (Fraction(1) + r_sq)
        elif sa == s_adj and sb == s_opp:
            exp_sin_sq, exp_cos_sq = Fraction(1) / (Fraction(1) + r_sq), r_sq / (Fraction(1) + r_sq)
        else:
            raise TrigCertificateError("ANGLE_WITNESS_SOURCE_MISMATCH", f"{c['id']}: segment_ratio does not link the two legs")
        if (exp_sin_sq, exp_cos_sq) != (sin_sq, cos_sq):
            raise TrigCertificateError("ANGLE_WITNESS_VALUE_MISMATCH", f"{c['id']}: leg_ratio (sin², cos²) mismatch")

    return sin_sq, cos_sq


def _verify_formula_and_expression(
    *,
    cert: Mapping[str, Any],
    v_right: str,
    v_adj: str,
    v_opp: str,
    adj_sq: Fraction,
    opp_sq: Fraction,
    hyp_sq: Fraction,
    sin_sq: Fraction,
    cos_sq: Fraction,
    length_unit: str | None,
) -> None:
    """Independently recompute the exact target length from `known_inputs` and `trig_identity`, checking acyclicity."""
    trig_id = cert.get("trig_identity")
    if trig_id not in CLOSED_TRIG_IDENTITIES:
        raise TrigCertificateError("UNKNOWN_TRIG_IDENTITY", f"unsupported trig_identity {trig_id!r}")

    derived_role = cert.get("derived_role")
    if derived_role not in VALID_DERIVED_ROLES:
        raise TrigCertificateError("INVALID_DERIVED_ROLE", f"unsupported derived_role {derived_role!r}")

    dq = cert.get("derived_quantity_id")
    role_to_seg = {
        "adjacent_leg": frozenset({v_right, v_adj}),
        "opposite_leg": frozenset({v_right, v_opp}),
        "hypotenuse": frozenset({v_adj, v_opp}),
    }
    role_to_sq = {
        "adjacent_leg": adj_sq,
        "opposite_leg": opp_sq,
        "hypotenuse": hyp_sq,
    }

    if derived_role in role_to_seg:
        if not isinstance(dq, (list, tuple)) or len(dq) != 2 or frozenset(dq) != role_to_seg[derived_role]:
            raise TrigCertificateError(
                "DERIVED_QUANTITY_MISMATCH",
                f"derived_quantity_id={dq!r} does not match {derived_role} segment {sorted(role_to_seg[derived_role])}",
            )
    else:  # both_legs
        if not (
            isinstance(dq, (list, tuple))
            and len(dq) == 2
            and all(isinstance(s, (list, tuple)) and len(s) == 2 for s in dq)
            and {frozenset(dq[0]), frozenset(dq[1])} == {role_to_seg["adjacent_leg"], role_to_seg["opposite_leg"]}
        ):
            raise TrigCertificateError(
                "DERIVED_QUANTITY_MISMATCH",
                f"both_legs derived_quantity_id={dq!r} must list both leg segments",
            )

    inputs_raw = cert.get("known_inputs")
    if not isinstance(inputs_raw, (list, tuple)) or not inputs_raw:
        raise TrigCertificateError("MISSING_KNOWN_INPUTS", "known_inputs must be a non-empty list")

    side_inputs: dict[str, Fraction] = {}
    non_side_roles: set[str] = set()
    derived_seg_sets: set[frozenset[str]] = (
        {role_to_seg[derived_role]}
        if derived_role in role_to_seg
        else {role_to_seg["adjacent_leg"], role_to_seg["opposite_leg"]}
    )

    for inp in inputs_raw:
        if not isinstance(inp, Mapping):
            raise TrigCertificateError("MALFORMED_KNOWN_INPUT", f"known_input entry must be a dict: {inp!r}")
        irole = inp.get("role")
        idim = inp.get("dimension")
        if irole in role_to_seg:
            if irole == derived_role or role_to_seg[irole] in derived_seg_sets:
                raise TrigCertificateError("CIRCULAR_KNOWN_INPUT", f"known_input {irole!r} circularly uses derived output")
            if idim != "LENGTH":
                raise TrigCertificateError("WRONG_INPUT_DIMENSION", f"side known_input {irole!r} must have dimension='LENGTH'")
            seg = inp.get("segment")
            if not isinstance(seg, (list, tuple)) or len(seg) != 2 or frozenset(seg) != role_to_seg[irole]:
                raise TrigCertificateError("MISMATCHED_KNOWN_INPUT_SEGMENT", f"known_input {irole!r} segment mismatch")
            lsq = _strict_fraction(inp.get("length_sq"), field_name=f"known_inputs[{irole}].length_sq")
            if lsq <= 0 or lsq != role_to_sq[irole]:
                raise TrigCertificateError("KNOWN_INPUT_VALUE_MISMATCH", f"known_input {irole!r} length_sq={lsq} != {role_to_sq[irole]}")
            c_val = from_json(inp.get("coef_json"))
            if sign(c_val) <= 0 or square(c_val) != lsq:
                raise TrigCertificateError("KNOWN_INPUT_VALUE_MISMATCH", f"known_input {irole!r} coef_json does not square to {lsq}")
            if irole in side_inputs:
                raise TrigCertificateError("DUPLICATE_KNOWN_INPUT", f"duplicate known_input role {irole!r}")
            side_inputs[irole] = lsq
        elif irole in ("angle", "equal_legs", "leg_ratio"):
            if idim not in ("ANGLE", "SCALAR"):
                raise TrigCertificateError("WRONG_INPUT_DIMENSION", f"known_input {irole!r} must have dimension ANGLE or SCALAR")
            non_side_roles.add(irole)
        else:
            raise TrigCertificateError("UNKNOWN_KNOWN_INPUT_ROLE", f"unknown known_input role {irole!r}")

    # Strict identity -> role & algebraic formula check
    if trig_id == ID_OPP_FROM_HYP_SIN:
        if derived_role != "opposite_leg" or set(side_inputs) != {"hypotenuse"} or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=opposite_leg, inputs=(hypotenuse, angle)")
        target_sq = side_inputs["hypotenuse"] * sin_sq
    elif trig_id == ID_ADJ_FROM_HYP_COS:
        if derived_role != "adjacent_leg" or set(side_inputs) != {"hypotenuse"} or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=adjacent_leg, inputs=(hypotenuse, angle)")
        target_sq = side_inputs["hypotenuse"] * cos_sq
    elif trig_id == ID_OPP_FROM_ADJ_TAN:
        if derived_role != "opposite_leg" or set(side_inputs) != {"adjacent_leg"} or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=opposite_leg, inputs=(adjacent_leg, angle)")
        target_sq = side_inputs["adjacent_leg"] * (sin_sq / cos_sq)
    elif trig_id == ID_ADJ_FROM_OPP_COT:
        if derived_role != "adjacent_leg" or set(side_inputs) != {"opposite_leg"} or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=adjacent_leg, inputs=(opposite_leg, angle)")
        target_sq = side_inputs["opposite_leg"] * (cos_sq / sin_sq)
    elif trig_id == ID_HYP_FROM_ADJ_COS:
        if derived_role != "hypotenuse" or set(side_inputs) != {"adjacent_leg"} or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=hypotenuse, inputs=(adjacent_leg, angle)")
        target_sq = side_inputs["adjacent_leg"] / cos_sq
    elif trig_id == ID_HYP_FROM_OPP_SIN:
        if derived_role != "hypotenuse" or set(side_inputs) != {"opposite_leg"} or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=hypotenuse, inputs=(opposite_leg, angle)")
        target_sq = side_inputs["opposite_leg"] / sin_sq
    elif trig_id == ID_PYTH_HYP_FROM_LEGS:
        if derived_role != "hypotenuse" or set(side_inputs) != {"adjacent_leg", "opposite_leg"} or non_side_roles:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=hypotenuse, inputs=(adjacent_leg, opposite_leg)")
        target_sq = side_inputs["adjacent_leg"] + side_inputs["opposite_leg"]
    elif trig_id == ID_PYTH_LEG_FROM_HYP:
        if derived_role == "adjacent_leg":
            req_sides = {"hypotenuse", "opposite_leg"}
            other_sq = side_inputs.get("opposite_leg", Fraction(0))
        elif derived_role == "opposite_leg":
            req_sides = {"hypotenuse", "adjacent_leg"}
            other_sq = side_inputs.get("adjacent_leg", Fraction(0))
        else:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived in (adjacent_leg, opposite_leg)")
        if set(side_inputs) != req_sides or non_side_roles:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} inputs mismatch")
        target_sq = side_inputs["hypotenuse"] - other_sq
    elif trig_id == ID_PYTH_EQUAL_LEGS:
        if derived_role not in ("both_legs", "adjacent_leg", "opposite_leg") or set(side_inputs) != {"hypotenuse"} or non_side_roles != {"equal_legs"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires inputs=(hypotenuse, equal_legs)")
        if adj_sq != opp_sq:
            raise TrigCertificateError("EQUAL_LEGS_METRIC_MISMATCH", f"equal legs violated: adj²={adj_sq} != opp²={opp_sq}")
        target_sq = side_inputs["hypotenuse"] * Fraction(1, 2)
    elif trig_id == ID_PYTH_LEG_RATIO:
        if derived_role not in ("both_legs", "adjacent_leg", "opposite_leg") or set(side_inputs) != {"hypotenuse"} or non_side_roles != {"leg_ratio"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires inputs=(hypotenuse, leg_ratio)")
        exp_adj_sq = side_inputs["hypotenuse"] * cos_sq
        exp_opp_sq = side_inputs["hypotenuse"] * sin_sq
        if adj_sq != exp_adj_sq or opp_sq != exp_opp_sq:
            raise TrigCertificateError("LEG_RATIO_METRIC_MISMATCH", "derived legs do not match hypotenuse * (cos², sin²)")
        target_sq = exp_adj_sq if derived_role != "opposite_leg" else exp_opp_sq
    elif trig_id == ID_RHOMBUS_HALF_DIAG_COS:
        if derived_role != "hypotenuse" or non_side_roles != {"angle"}:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires derived=hypotenuse and angle input")
        if set(side_inputs) == {"adjacent_leg"}:
            target_sq = side_inputs["adjacent_leg"] / cos_sq
        elif set(side_inputs) == {"opposite_leg"}:
            target_sq = side_inputs["opposite_leg"] / sin_sq
        else:
            raise TrigCertificateError("TRIG_IDENTITY_ROLE_MISMATCH", f"{trig_id} requires exactly one half-diagonal leg input")
    else:  # pragma: no cover - guarded by CLOSED_TRIG_IDENTITIES
        raise TrigCertificateError("UNKNOWN_TRIG_IDENTITY", f"unhandled trig_identity {trig_id!r}")

    if target_sq <= 0:
        raise TrigCertificateError("NON_POSITIVE_DERIVED_LENGTH", f"recomputed target length²={target_sq} <= 0")

    if derived_role in role_to_sq and target_sq != role_to_sq[derived_role]:
        raise TrigCertificateError(
            "FORMULA_SCENE_MISMATCH",
            f"recomputed {derived_role}²={target_sq} != Gram segment length²={role_to_sq[derived_role]}",
        )

    if cert.get("dimension") != "LENGTH":
        raise TrigCertificateError("WRONG_DIMENSION", f"certificate dimension must be 'LENGTH', got {cert.get('dimension')!r}")

    expr = cert.get("exact_length_expr")
    if not isinstance(expr, Mapping):
        raise TrigCertificateError("MISSING_EXACT_LENGTH_EXPR", "exact_length_expr must be a dict")
    unit_to_check = length_unit if length_unit is not None else expr.get("unit_symbol")
    if length_unit is not None and expr.get("unit_symbol") != length_unit:
        raise TrigCertificateError("UNIT_SYMBOL_MISMATCH", f"exact_length_expr.unit_symbol={expr.get('unit_symbol')!r} != {length_unit!r}")

    expected_expr = format_exact_length_expr(target_sq, length_unit=unit_to_check)
    try:
        claimed_coef = from_json(expr.get("coef_json"))
        expected_coef = from_json(expected_expr["coef_json"])
    except RadicalDomainError as exc:
        raise TrigCertificateError("MALFORMED_EXACT_LENGTH_EXPR", f"invalid coef_json: {exc}") from None

    if (
        claimed_coef != expected_coef
        or expr.get("coef_str") != expected_expr["coef_str"]
        or _strict_fraction(expr.get("squared_coef_str"), field_name="exact_length_expr.squared_coef_str") != target_sq
        or expr.get("power") != 1
        or expr.get("display") != expected_expr["display"]
    ):
        raise TrigCertificateError(
            "EXACT_LENGTH_EXPR_MISMATCH",
            f"exact_length_expr {dict(expr)!r} != recomputed {expected_expr!r}",
        )


def verify_trig_construction_certificate(
    cert: Mapping[str, Any],
    *,
    calls: Sequence[Any],
    points_by_label: Mapping[str, Sequence[Any]] | None = None,
    scene_objects: Mapping[str, Mapping[str, Any]] | None = None,
    chart_metric: Any = None,
    length_unit: str | None = None,
) -> None:
    """Independently verify a `trig-construction-certificate/1` record. Raises `TrigCertificateError` on any violation."""
    if not isinstance(cert, Mapping):
        raise TrigCertificateError("MALFORMED_CERTIFICATE", "certificate must be a mapping")
    if cert.get("schema_version") != TRIG_CONSTRUCTION_CERTIFICATE_VERSION:
        raise TrigCertificateError("SCHEMA_VERSION_MISMATCH", f"unexpected schema_version {cert.get('schema_version')!r}")
    if cert.get("verified") is not True:
        raise TrigCertificateError("CERTIFICATE_NOT_MARKED_VERIFIED", "cert.verified must be True")
    cid_str = cert.get("certificate_id")
    if not isinstance(cid_str, str) or not cid_str.strip():
        raise TrigCertificateError("MISSING_CERTIFICATE_ID", "certificate_id must be a non-empty string")
    if cert.get("dimension") != "LENGTH":
        raise TrigCertificateError("WRONG_DIMENSION", f"dimension must be 'LENGTH', got {cert.get('dimension')!r}")

    # Reject raw floats anywhere inside chart_metric before Sylvester check
    raw_g = getattr(chart_metric, "g", chart_metric)
    if isinstance(raw_g, (list, tuple)):
        for row in raw_g:
            if isinstance(row, (list, tuple)) and any(isinstance(entry, float) for entry in row):
                raise TrigCertificateError("FLOAT_APPROXIMATION_FORBIDDEN", "float entry in chart_metric is forbidden")
    try:
        g_mat = validate_gram_metric_spd(chart_metric)
    except CertificateError as exc:
        raise TrigCertificateError(exc.code, exc.reason) from None

    calls_by_id = _normalize_calls(calls)

    # Verify source_premises against calls
    premises = cert.get("source_premises")
    if not isinstance(premises, (list, tuple)) or not premises:
        raise TrigCertificateError("MISSING_SOURCE_PREMISES", "source_premises must be a non-empty list")
    source_premise_ids: set[str] = set()
    for p in premises:
        if not isinstance(p, Mapping):
            raise TrigCertificateError("MALFORMED_SOURCE_PREMISE", f"invalid source_premise {p!r}")
        pcid = p.get("call_id")
        pfn = p.get("fn")
        pquotes = p.get("quotes")
        if not isinstance(pcid, str) or pcid not in calls_by_id:
            raise TrigCertificateError("UNKNOWN_SOURCE_PREMISE_CALL", f"source_premise call_id {pcid!r} not in calls")
        actual = calls_by_id[pcid]
        if pfn != actual["fn"]:
            raise TrigCertificateError("SOURCE_PREMISE_FN_MISMATCH", f"{pcid}: premise fn {pfn!r} != {actual['fn']!r}")
        if not isinstance(pquotes, (list, tuple)) or not pquotes:
            raise TrigCertificateError("SOURCE_PREMISE_QUOTES_MISSING", f"{pcid}: empty quotes in source_premises")
        if [chuan_hoa(str(q)) for q in pquotes] != [chuan_hoa(str(q)) for q in actual["quotes"]]:
            raise TrigCertificateError("SOURCE_PREMISE_QUOTES_MISMATCH", f"{pcid}: premise quotes do not match call quotes")
        source_premise_ids.add(pcid)

    deps = cert.get("construction_dependencies")
    if not isinstance(deps, Mapping):
        raise TrigCertificateError("MISSING_CONSTRUCTION_DEPENDENCIES", "construction_dependencies must be a dict")
    dep_calls = deps.get("prerequisite_calls")
    if not isinstance(dep_calls, (list, tuple)) or not source_premise_ids.issubset(set(dep_calls)):
        raise TrigCertificateError(
            "INCOMPLETE_CONSTRUCTION_DEPENDENCIES",
            "construction_dependencies.prerequisite_calls must cover all source_premises",
        )
    for dcid in dep_calls:
        if not isinstance(dcid, str) or dcid not in calls_by_id:
            raise TrigCertificateError("UNKNOWN_DEPENDENCY_CALL", f"dependency call {dcid!r} not in calls")

    pts, _aux_labels = _resolve_and_verify_points(
        cert=cert,
        points_by_label=points_by_label,
        scene_objects=scene_objects,
        g_mat=g_mat,
    )
    # Also resolve any placed call labels available in scene_objects so premise checks can inspect plane/line vertices
    if scene_objects is not None:
        for lbl in _collect_all_call_labels(calls_by_id):
            if lbl not in pts:
                ir = _ir_name(lbl)
                obj = scene_objects.get(ir)
                if isinstance(obj, Mapping) and obj.get("type") == "point3":
                    pts[lbl] = _strict_vec3(obj.get("xyz", ()), label=lbl)

    tri = cert.get("derived_right_triangle")
    if not isinstance(tri, (list, tuple)) or len(tri) != 3 or any(not isinstance(v, str) or not v for v in tri):
        raise TrigCertificateError("INVALID_RIGHT_TRIANGLE", "derived_right_triangle must list 3 vertex names")
    v_right, v_adj, v_opp = tri[0], tri[1], tri[2]
    if len({v_right, v_adj, v_opp}) != 3:
        raise TrigCertificateError("DEGENERATE_RIGHT_TRIANGLE", f"triangle vertices {list(tri)!r} are not distinct")
    if cert.get("right_angle_vertex") != v_right:
        raise TrigCertificateError(
            "RIGHT_ANGLE_VERTEX_MISMATCH",
            f"right_angle_vertex={cert.get('right_angle_vertex')!r} != derived_right_triangle[0]={v_right!r}",
        )

    u_adj = vec_sub(pts[v_adj], pts[v_right])
    u_opp = vec_sub(pts[v_opp], pts[v_right])
    u_hyp = vec_sub(pts[v_opp], pts[v_adj])
    adj_sq = gram_dot(g_mat, u_adj, u_adj)
    opp_sq = gram_dot(g_mat, u_opp, u_opp)
    hyp_sq = gram_dot(g_mat, u_hyp, u_hyp)
    dot_legs = gram_dot(g_mat, u_adj, u_opp)
    area_det = adj_sq * opp_sq - dot_legs * dot_legs
    if adj_sq <= 0 or opp_sq <= 0 or hyp_sq <= 0 or area_det <= 0:
        raise TrigCertificateError("DEGENERATE_RIGHT_TRIANGLE", f"triangle {list(tri)!r} has zero/degenerate Gram area")

    # Strict role incidence checks (catches leg swap at 45° and hypotenuse/leg swap)
    for role_key, expected_set, expected_sq, err_code in (
        ("hypotenuse", frozenset({v_adj, v_opp}), hyp_sq, "MISMATCHED_HYPOTENUSE"),
        ("adjacent_leg", frozenset({v_right, v_adj}), adj_sq, "MISMATCHED_ADJACENT_LEG"),
        ("opposite_leg", frozenset({v_right, v_opp}), opp_sq, "MISMATCHED_OPPOSITE_LEG"),
    ):
        role_rec = cert.get(role_key)
        if not isinstance(role_rec, Mapping):
            raise TrigCertificateError(err_code, f"{role_key} must be a dict")
        seg = role_rec.get("segment")
        if not isinstance(seg, (list, tuple)) or len(seg) != 2 or frozenset(seg) != expected_set:
            raise TrigCertificateError(
                err_code,
                f"{role_key}.segment={seg!r} must have endpoints {sorted(expected_set)!r}",
            )
        claimed_sq = _strict_fraction(role_rec.get("length_sq"), field_name=f"{role_key}.length_sq")
        if claimed_sq != expected_sq:
            raise TrigCertificateError(err_code, f"{role_key}.length_sq={claimed_sq} != Gram length²={expected_sq}")

    if hyp_sq != adj_sq + opp_sq or not (hyp_sq > adj_sq and hyp_sq > opp_sq):
        raise TrigCertificateError(
            "PYTHAGOREAN_INVARIANT_FAILED",
            f"Pythagorean identity violated: adj²={adj_sq}, opp²={opp_sq}, hyp²={hyp_sq}",
        )

    _verify_perpendicularity_justification(
        just=cert.get("perpendicularity_justification"),
        v_right=v_right,
        v_adj=v_adj,
        v_opp=v_opp,
        calls_by_id=calls_by_id,
        source_premise_ids=source_premise_ids,
        pts=pts,
        aux_specs=cert.get("auxiliary_witness_points") or {},
        g_mat=g_mat,
    )

    sin_sq, cos_sq = _verify_angle_witness(
        aw=cert.get("angle_witness"),
        v_right=v_right,
        v_adj=v_adj,
        v_opp=v_opp,
        adj_sq=adj_sq,
        opp_sq=opp_sq,
        hyp_sq=hyp_sq,
        calls_by_id=calls_by_id,
        source_premise_ids=source_premise_ids,
        pts=pts,
        g_mat=g_mat,
    )

    _verify_formula_and_expression(
        cert=cert,
        v_right=v_right,
        v_adj=v_adj,
        v_opp=v_opp,
        adj_sq=adj_sq,
        opp_sq=opp_sq,
        hyp_sq=hyp_sq,
        sin_sq=sin_sq,
        cos_sq=cos_sq,
        length_unit=length_unit,
    )

    pos = cert.get("positivity_domain")
    required_pos_flags = (
        "sin_sq_gt_0",
        "cos_sq_gt_0",
        "unit_circle_sum_eq_1",
        "hypotenuse_sq_gt_legs_sq",
        "derived_length_sq_gt_0",
        "gram_spd_verified",
    )
    if not isinstance(pos, Mapping) or any(pos.get(k) is not True for k in required_pos_flags):
        raise TrigCertificateError("POSITIVITY_DOMAIN_INVALID", f"positivity_domain flags must all be True: {pos!r}")

    uniq = cert.get("single_branch_uniqueness")
    if (
        not isinstance(uniq, Mapping)
        or uniq.get("unique_positive_root") is not True
        or uniq.get("acute_or_verified_branch") is not True
    ):
        raise TrigCertificateError("BRANCH_UNIQUENESS_INVALID", f"single_branch_uniqueness flags must be True: {uniq!r}")


def build_trig_construction_certificate(
    *,
    certificate_id: str,
    derived_role: str,
    derived_right_triangle: tuple[str, str, str] | list[str],
    perpendicularity_rule: str,
    perpendicularity_calls: Sequence[str],
    angle_witness_kind: str,
    angle_witness_calls: Sequence[str],
    sin_sq: Fraction,
    cos_sq: Fraction,
    angle_unit: str = "deg",
    angle_raw_value: str | None = None,
    trig_identity: str,
    known_side_roles: Sequence[str],
    non_side_input_role: str | None = None,
    non_side_input_dimension: str = "ANGLE",
    calls: Sequence[Any],
    points_by_label: Mapping[str, Sequence[Any]],
    chart_metric: Any = None,
    length_unit: str | None = None,
    auxiliary_witness_points: Mapping[str, Mapping[str, Any]] | None = None,
    extra_premise_calls: Sequence[str] = (),
) -> dict[str, Any]:
    """Construct and self-verify a canonical `trig-construction-certificate/1` dictionary."""
    g_mat = validate_gram_metric_spd(chart_metric)
    calls_by_id = _normalize_calls(calls)
    if len(derived_right_triangle) != 3:
        raise TrigCertificateError("INVALID_RIGHT_TRIANGLE", "derived_right_triangle must have 3 vertices")
    v_right, v_adj, v_opp = str(derived_right_triangle[0]), str(derived_right_triangle[1]), str(derived_right_triangle[2])

    aux_dict: dict[str, dict[str, Any]] = {}
    pts: dict[str, list[Fraction]] = {lbl: _strict_vec3(xyz, label=lbl) for lbl, xyz in points_by_label.items()}
    if auxiliary_witness_points:
        for albl, aspec in auxiliary_witness_points.items():
            vec = _strict_vec3(aspec["xyz"], label=albl)
            pts[albl] = vec
            aux_dict[albl] = {
                **{k: v for k, v in aspec.items() if k != "xyz"},
                "xyz": [str(vec[0]), str(vec[1]), str(vec[2])],
            }

    adj_sq = gram_dot(g_mat, vec_sub(pts[v_adj], pts[v_right]), vec_sub(pts[v_adj], pts[v_right]))
    opp_sq = gram_dot(g_mat, vec_sub(pts[v_opp], pts[v_right]), vec_sub(pts[v_opp], pts[v_right]))
    hyp_sq = gram_dot(g_mat, vec_sub(pts[v_opp], pts[v_adj]), vec_sub(pts[v_opp], pts[v_adj]))

    role_segments = {
        "adjacent_leg": [v_right, v_adj],
        "opposite_leg": [v_right, v_opp],
        "hypotenuse": [v_adj, v_opp],
    }
    role_sqs = {
        "adjacent_leg": adj_sq,
        "opposite_leg": opp_sq,
        "hypotenuse": hyp_sq,
    }

    if derived_role in role_segments:
        derived_quantity_id: Any = list(role_segments[derived_role])
        target_sq = role_sqs[derived_role]
    elif derived_role == "both_legs":
        derived_quantity_id = [[v_right, v_adj], [v_right, v_opp]]
        target_sq = adj_sq
    else:
        raise TrigCertificateError("INVALID_DERIVED_ROLE", f"unsupported derived_role {derived_role!r}")

    ordered_cids: list[str] = []
    for cid in (*perpendicularity_calls, *angle_witness_calls, *extra_premise_calls):
        if cid not in ordered_cids:
            ordered_cids.append(cid)
    source_premises = [
        {"call_id": cid, "fn": calls_by_id[cid]["fn"], "quotes": list(calls_by_id[cid]["quotes"])}
        for cid in ordered_cids
        if cid in calls_by_id
    ]

    known_inputs: list[dict[str, Any]] = []
    for srole in known_side_roles:
        lsq = role_sqs[srole]
        coef = sqrt_rational(lsq)
        known_inputs.append({
            "role": srole,
            "segment": list(role_segments[srole]),
            "length_sq": str(lsq),
            "coef_json": to_json(coef),
            "dimension": "LENGTH",
        })
    if non_side_input_role is not None:
        known_inputs.append({
            "role": non_side_input_role,
            "sin_sq": str(_strict_fraction(sin_sq, field_name="sin_sq")),
            "cos_sq": str(_strict_fraction(cos_sq, field_name="cos_sq")),
            "dimension": non_side_input_dimension,
        })

    cert: dict[str, Any] = {
        "schema_version": TRIG_CONSTRUCTION_CERTIFICATE_VERSION,
        "certificate_id": certificate_id,
        "derived_quantity_id": derived_quantity_id,
        "derived_role": derived_role,
        "source_premises": source_premises,
        "derived_right_triangle": [v_right, v_adj, v_opp],
        "right_angle_vertex": v_right,
        **({"auxiliary_witness_points": aux_dict} if aux_dict else {}),
        "perpendicularity_justification": {
            "rule": perpendicularity_rule,
            "supporting_calls": list(perpendicularity_calls),
            "gram_dot_zero_verified": True,
        },
        "angle_witness": {
            "kind": angle_witness_kind,
            "vertex": v_adj,
            "ray_1": [v_adj, v_right],
            "ray_2": [v_adj, v_opp],
            "domain": "(0°, 90°)",
            "unit": angle_unit,
            "raw_value": angle_raw_value,
            "sin_sq": str(_strict_fraction(sin_sq, field_name="sin_sq")),
            "cos_sq": str(_strict_fraction(cos_sq, field_name="cos_sq")),
            "supporting_calls": list(angle_witness_calls),
        },
        "hypotenuse": {"segment": [v_adj, v_opp], "length_sq": str(hyp_sq)},
        "adjacent_leg": {"segment": [v_right, v_adj], "length_sq": str(adj_sq)},
        "opposite_leg": {"segment": [v_right, v_opp], "length_sq": str(opp_sq)},
        "trig_identity": trig_identity,
        "known_inputs": known_inputs,
        "exact_length_expr": format_exact_length_expr(target_sq, length_unit=length_unit),
        "dimension": "LENGTH",
        "positivity_domain": {
            "sin_sq_gt_0": True,
            "cos_sq_gt_0": True,
            "unit_circle_sum_eq_1": True,
            "hypotenuse_sq_gt_legs_sq": True,
            "derived_length_sq_gt_0": True,
            "gram_spd_verified": True,
        },
        "single_branch_uniqueness": {
            "unique_positive_root": True,
            "acute_or_verified_branch": True,
        },
        "construction_dependencies": {
            "prerequisite_calls": ordered_cids,
            "vertices": [v_right, v_adj, v_opp],
        },
        "verified": True,
    }
    verify_trig_construction_certificate(
        cert,
        calls=calls,
        points_by_label=points_by_label,
        chart_metric=chart_metric,
        length_unit=length_unit,
    )
    return cert
