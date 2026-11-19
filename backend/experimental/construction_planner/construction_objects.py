# -*- coding: utf-8 -*-
"""Typed geometric objects and canonical geometric identity for `verified-construction-graph/1`.

Strictly separates:
- Object origin (`GIVEN_OBJECT`, `DERIVED_OBJECT`, `AUXILIARY_CONSTRUCTION`)
- Symbol/label identity (`object_id`, `label`) vs exact canonical geometric identity (`canonical_geom_key`)
- Reuse of `app.simulation.geometry.exact` (`Vec3`, `Line3`, `Plane3`, `Segment3`) and `Fraction`
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Literal

from app.simulation.geometry import section as S
from app.simulation.geometry.exact import GeometryError, Line3, Plane3, Point3, Segment3, Vec3

ObjectOrigin = Literal["GIVEN_OBJECT", "DERIVED_OBJECT", "AUXILIARY_CONSTRUCTION"]
GeometricObjectKind = Literal[
    "point3",
    "segment3",
    "line3",
    "plane3",
    "polygon3",
    "solid",
    "section",
    "quantity",
    "relation",
]

VALID_OBJECT_ORIGINS = frozenset({"GIVEN_OBJECT", "DERIVED_OBJECT", "AUXILIARY_CONSTRUCTION"})
VALID_OBJECT_KINDS = frozenset(
    {"point3", "segment3", "line3", "plane3", "polygon3", "solid", "section", "quantity", "relation"}
)


def _fmt_frac(val: Fraction) -> str:
    val = Fraction(val)
    return str(val.numerator) if val.denominator == 1 else f"{val.numerator}/{val.denominator}"


def vec3_to_rational_list(v: Vec3) -> list[str]:
    return [_fmt_frac(v.x), _fmt_frac(v.y), _fmt_frac(v.z)]


def canonical_point_key(p: Point3) -> str:
    return f"pt({','.join(vec3_to_rational_list(p))})"


def canonical_segment_key(seg: Segment3) -> str:
    k1 = canonical_point_key(seg.point_a)
    k2 = canonical_point_key(seg.point_b)
    a, b = sorted((k1, k2))
    return f"seg({a};{b})"


def canonical_line_key(ln: Line3) -> str:
    """Affine canonicalization invariant to anchor translation along `ln` and direction reversal."""
    dx, dy, dz = ln.direction.x, ln.direction.y, ln.direction.z
    comps = (dx, dy, dz)
    pivot_idx = next((i for i, c in enumerate(comps) if c != 0), None)
    if pivot_idx is None:
        raise GeometryError("ZERO_VECTOR", "cannot canonicalize zero-direction line")
    inv = Fraction(1) / comps[pivot_idx]
    d_norm = Vec3(dx * inv, dy * inv, dz * inv)
    a_comps = (ln.point.x, ln.point.y, ln.point.z)
    t = a_comps[pivot_idx]
    reduced_anchor = ln.point - d_norm.scale(t)
    return f"ln(p={','.join(vec3_to_rational_list(reduced_anchor))}|d={','.join(vec3_to_rational_list(d_norm))})"


def canonical_plane_key(pl: Plane3) -> str:
    """Affine dual covector canonicalization `n·X + d = 0` scaled by first nonzero normal entry."""
    nx, ny, nz = pl.normal.x, pl.normal.y, pl.normal.z
    comps = (nx, ny, nz)
    pivot_idx = next((i for i, c in enumerate(comps) if c != 0), None)
    if pivot_idx is None:
        raise GeometryError("PLANE_EQUATION_DEGENERATE", "cannot canonicalize zero-normal plane")
    inv = Fraction(1) / comps[pivot_idx]
    d_raw = -(pl.normal.dot(pl.point))
    coeffs = (_fmt_frac(nx * inv), _fmt_frac(ny * inv), _fmt_frac(nz * inv), _fmt_frac(d_raw * inv))
    return f"pl({','.join(coeffs)})"


def canonical_polygon_key(vertices: tuple[Point3, ...] | list[Point3], kind: str = "poly") -> str:
    pts = [canonical_point_key(v) for v in vertices]
    if len(pts) >= 3:
        rotations = [tuple(pts[i:] + pts[:i]) for i in range(len(pts))]
        rev = list(reversed(pts))
        rotations.extend(tuple(rev[i:] + rev[:i]) for i in range(len(rev)))
        best = min(rotations)
    else:
        best = tuple(sorted(pts))
    return f"{kind}({','.join(best)})"


def canonical_relation_key(relation_kind: str, operand_keys: tuple[str, ...], symmetric: bool = False) -> str:
    ops = tuple(sorted(operand_keys)) if symmetric else operand_keys
    return f"rel:{relation_kind}({';'.join(ops)})"


def serialize_exact_value(val: Any) -> dict[str, Any]:
    """Deterministically serialize exact kernel geometry or relation payloads."""
    if isinstance(val, Vec3):
        return {"kind": "point3", "xyz": vec3_to_rational_list(val)}
    if isinstance(val, Segment3):
        return {
            "kind": "segment3",
            "point_a": vec3_to_rational_list(val.point_a),
            "point_b": vec3_to_rational_list(val.point_b),
        }
    if isinstance(val, Line3):
        return {
            "kind": "line3",
            "point": vec3_to_rational_list(val.point),
            "direction": vec3_to_rational_list(val.direction),
        }
    if isinstance(val, Plane3):
        return {
            "kind": "plane3",
            "point": vec3_to_rational_list(val.point),
            "normal": vec3_to_rational_list(val.normal),
        }
    if isinstance(val, S.Polyhedron):
        return {
            "kind": "solid",
            "vertices": [vec3_to_rational_list(v) for v in val.vertices],
            "faces": [list(f) for f in val.faces],
        }
    if isinstance(val, S.Section):
        return {
            "kind": "section",
            "polygon": [vec3_to_rational_list(v) for v in val.polygon],
        }
    if isinstance(val, tuple) and all(isinstance(x, Vec3) for x in val):
        return {"kind": "polygon3", "vertices": [vec3_to_rational_list(x) for x in val]}
    if isinstance(val, Fraction):
        return {"kind": "fraction", "value": _fmt_frac(val)}
    if isinstance(val, dict):
        return {str(k): _json_safe(v) for k, v in sorted(val.items())}
    return {"kind": "raw", "value": _json_safe(val)}


def _json_safe(val: Any) -> Any:
    if isinstance(val, Fraction):
        return _fmt_frac(val)
    if isinstance(val, Vec3):
        return vec3_to_rational_list(val)
    if isinstance(val, (list, tuple)):
        return [_json_safe(x) for x in val]
    if isinstance(val, dict):
        return {str(k): _json_safe(v) for k, v in sorted(val.items())}
    return val


@dataclass(frozen=True)
class ConstructionObject:
    """First-class typed object inside `ConstructionProofGraph`."""

    object_id: str
    object_kind: GeometricObjectKind
    origin: ObjectOrigin
    canonical_geom_key: str
    label: str
    exact_value: Any
    source_fact_refs: tuple[str, ...] = ()
    supporting_node_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.object_kind not in VALID_OBJECT_KINDS:
            raise ValueError(f"Unsupported object_kind={self.object_kind!r}")
        if self.origin not in VALID_OBJECT_ORIGINS:
            raise ValueError(f"Unsupported origin={self.origin!r}")
        if self.origin == "AUXILIARY_CONSTRUCTION" and self.source_fact_refs:
            raise ValueError(
                f"AUXILIARY_CONSTRUCTION object {self.object_id!r} cannot claim source_fact_refs={self.source_fact_refs!r}."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "object_kind": self.object_kind,
            "origin": self.origin,
            "canonical_geom_key": self.canonical_geom_key,
            "label": self.label,
            "exact_value": serialize_exact_value(self.exact_value),
            "source_fact_refs": list(self.source_fact_refs),
            "supporting_node_id": self.supporting_node_id,
            "metadata": _json_safe(self.metadata),
        }
