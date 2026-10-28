"""Independent exact-Fraction 3D geometry oracle for Holdout Wave 3.

Uses ONLY the Python standard library (`argparse`, `fractions`, `functools`,
`json`, `pathlib`, `sys`, `typing`) with ZERO imports from `app.*` or `backend.*`.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
from functools import cmp_to_key
import json
from pathlib import Path
import sys
from typing import Any

Vec3 = tuple[Fraction, Fraction, Fraction]

RUN_DIR = Path(__file__).resolve().parent.parent
CORPUS_PATH = RUN_DIR / "inputs" / "holdout-wave3.json"
GEOMETRY_PATH = RUN_DIR / "oracle" / "geometry.json"
EXPECTED_PATH = RUN_DIR / "oracle" / "expected.json"


def _f(val: Any) -> Fraction:
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val)
    s = str(val).strip()
    if s.endswith("a") and s != "a":
        s = s[:-1].strip()
    elif s == "a":
        s = "1"
    return Fraction(s)


def _f_str(val: Fraction) -> str:
    return f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)


def _vec(coords: list[Any] | tuple[Any, ...]) -> Vec3:
    if len(coords) != 3:
        raise ValueError(f"Expected 3D coordinates, got {coords!r}")
    return (_f(coords[0]), _f(coords[1]), _f(coords[2]))


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(s: Fraction, v: Vec3) -> Vec3:
    return (s * v[0], s * v[1], s * v[2])


def _dot(a: Vec3, b: Vec3) -> Fraction:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm_sq(v: Vec3) -> Fraction:
    return _dot(v, v)


def _dist_sq(a: Vec3, b: Vec3) -> Fraction:
    return _norm_sq(_sub(a, b))


def _resolve_point(label: str, solid_vertices: dict[str, Vec3], named_points: dict[str, Vec3]) -> Vec3:
    if label in solid_vertices:
        return solid_vertices[label]
    if label in named_points:
        return named_points[label]
    raise KeyError(f"Unknown point label {label!r}")


def _verify_premises(
    case_id: str,
    payload: dict[str, Any],
    solid_vertices: dict[str, Vec3],
    named_points: dict[str, Vec3],
) -> None:
    premises = payload.get("premises") or []
    if not premises:
        raise ValueError(f"{case_id}: positive case has empty premises")

    for prem in premises:
        kind = prem["kind"]
        args = prem.get("args") or {}
        if kind == "segment_length":
            u_lbl, v_lbl = args["segment"]
            u = _resolve_point(u_lbl, solid_vertices, named_points)
            v = _resolve_point(v_lbl, solid_vertices, named_points)
            val = _f(args["value"])
            if val <= 0:
                raise ValueError(f"{case_id}: non-positive segment_length {val}")
            if _dist_sq(u, v) != val * val:
                raise ValueError(
                    f"{case_id}: segment_length mismatch on {u_lbl}{v_lbl}: "
                    f"dist_sq={_dist_sq(u, v)} vs expected={val * val}"
                )
        elif kind in ("right_angle", "base_is_right_triangle"):
            if "vertices" in args:
                verts = args["vertices"]
                r_lbl = args["right_at"]
                others = [x for x in verts if x != r_lbl]
            else:
                r_lbl = args["vertex"]
                others = list(args["rays"])
            if len(others) != 2:
                raise ValueError(f"{case_id}: malformed right_angle args {args!r}")
            r_pt = _resolve_point(r_lbl, solid_vertices, named_points)
            p1 = _resolve_point(others[0], solid_vertices, named_points)
            p2 = _resolve_point(others[1], solid_vertices, named_points)
            if _dot(_sub(p1, r_pt), _sub(p2, r_pt)) != 0:
                raise ValueError(f"{case_id}: right_angle violated at {r_lbl}")
        elif kind in ("rectangle", "base_is_rectangle"):
            v0, v1, v2, v3 = [_resolve_point(x, solid_vertices, named_points) for x in args["vertices"]]
            if _dot(_sub(v1, v0), _sub(v3, v0)) != 0:
                raise ValueError(f"{case_id}: rectangle angle at v0 not orthogonal")
            if _sub(v2, v1) != _sub(v3, v0):
                raise ValueError(f"{case_id}: rectangle opposite sides do not match")
        elif kind == "base_is_square":
            v0, v1, v2, v3 = [_resolve_point(x, solid_vertices, named_points) for x in args["vertices"]]
            if _dot(_sub(v1, v0), _sub(v3, v0)) != 0 or _sub(v2, v1) != _sub(v3, v0):
                raise ValueError(f"{case_id}: square orthogonality/parallelogram check failed")
            if _dist_sq(v0, v1) != _dist_sq(v0, v3):
                raise ValueError(f"{case_id}: square adjacent sides unequal")
            if "side" in args and args["side"] is not None:
                s = _f(args["side"])
                if _dist_sq(v0, v1) != s * s:
                    raise ValueError(f"{case_id}: square side mismatch")
        elif kind in ("perpendicular_line_plane", "line_perp_plane"):
            u_lbl, v_lbl = args["line"]
            u = _resolve_point(u_lbl, solid_vertices, named_points)
            v = _resolve_point(v_lbl, solid_vertices, named_points)
            line_vec = _sub(v, u)
            if _norm_sq(line_vec) == 0:
                raise ValueError(f"{case_id}: degenerate line in perpendicular_line_plane")
            plane_pts = [_resolve_point(x, solid_vertices, named_points) for x in args["plane"]]
            for p in plane_pts[1:]:
                if _dot(line_vec, _sub(p, plane_pts[0])) != 0:
                    raise ValueError(f"{case_id}: line {u_lbl}{v_lbl} not perpendicular to plane {args['plane']}")
        elif kind in ("orthogonal_projection", "point_is_foot"):
            pt = _resolve_point(args["point"], solid_vertices, named_points)
            img = _resolve_point(args["image"], solid_vertices, named_points)
            perp_vec = _sub(pt, img)
            if _norm_sq(perp_vec) == 0:
                raise ValueError(f"{case_id}: zero projection vector")
            plane_pts = [_resolve_point(x, solid_vertices, named_points) for x in args["plane"]]
            for p in plane_pts[1:]:
                if _dot(perp_vec, _sub(p, plane_pts[0])) != 0:
                    raise ValueError(f"{case_id}: orthogonal_projection not perpendicular to plane")
            n_plane = _cross(_sub(plane_pts[1], plane_pts[0]), _sub(plane_pts[2], plane_pts[0]))
            if _dot(n_plane, _sub(img, plane_pts[0])) != 0:
                raise ValueError(f"{case_id}: orthogonal_projection image does not lie in plane")
        elif kind == "right_prism":
            base_pts = [_resolve_point(x, solid_vertices, named_points) for x in args["base"]]
            top_pts = [_resolve_point(x, solid_vertices, named_points) for x in args["top"]]
            if len(base_pts) != len(top_pts) or len(base_pts) < 3:
                raise ValueError(f"{case_id}: invalid right_prism base/top lengths")
            lat = _sub(top_pts[0], base_pts[0])
            if _norm_sq(lat) == 0:
                raise ValueError(f"{case_id}: degenerate right_prism lateral vector")
            for b, t in zip(base_pts, top_pts):
                if _sub(t, b) != lat:
                    raise ValueError(f"{case_id}: right_prism lateral edges not parallel/equal")
            for b in base_pts[1:]:
                if _dot(lat, _sub(b, base_pts[0])) != 0:
                    raise ValueError(f"{case_id}: right_prism lateral edge not perpendicular to base")
        elif kind in ("midpoint", "point_is_midpoint"):
            pt = _resolve_point(args["point"], solid_vertices, named_points)
            u = _resolve_point(args["segment"][0], solid_vertices, named_points)
            v = _resolve_point(args["segment"][1], solid_vertices, named_points)
            mid = _scale(Fraction(1, 2), _add(u, v))
            if pt != mid:
                raise ValueError(f"{case_id}: midpoint mismatch for {args['point']}")
        elif kind in ("divide_segment", "point_divides_segment"):
            pt = _resolve_point(args["point"], solid_vertices, named_points)
            u = _resolve_point(args["segment"][0], solid_vertices, named_points)
            v = _resolve_point(args["segment"][1], solid_vertices, named_points)
            r = _f(args["ratio"])
            if not (Fraction(0) < r < Fraction(1)):
                raise ValueError(f"{case_id}: divide_segment ratio {r} outside (0, 1)")
            expected_pt = _add(u, _scale(r, _sub(v, u)))
            if pt != expected_pt:
                raise ValueError(f"{case_id}: divide_segment coordinate mismatch for {args['point']}")


def _plane_normal_and_d(
    case_id: str,
    plane_spec: dict[str, Any],
    solid_vertices: dict[str, Vec3],
    named_points: dict[str, Vec3],
) -> tuple[Vec3, Fraction]:
    tp_label = plane_spec["through_point"]
    tp = _resolve_point(tp_label, solid_vertices, named_points)
    kind = plane_spec["kind"]
    if kind in ("perpendicular_line", "through_point_perpendicular_line"):
        u_lbl, v_lbl = plane_spec["perpendicular_line"]
        u = _resolve_point(u_lbl, solid_vertices, named_points)
        v = _resolve_point(v_lbl, solid_vertices, named_points)
        normal = _sub(v, u)
    elif kind in ("parallel_plane", "through_point_parallel_plane"):
        p0, p1, p2 = [_resolve_point(x, solid_vertices, named_points) for x in plane_spec["parallel_plane"][:3]]
        normal = _cross(_sub(p1, p0), _sub(p2, p0))
    elif kind in ("parallel_two_lines", "through_point_parallel_two_lines"):
        if "parallel_two_lines" in plane_spec and plane_spec["parallel_two_lines"]:
            la, lb = plane_spec["parallel_two_lines"]
        else:
            la, lb = plane_spec["parallel_line_a"], plane_spec["parallel_line_b"]
        u1, v1 = _resolve_point(la[0], solid_vertices, named_points), _resolve_point(la[1], solid_vertices, named_points)
        u2, v2 = _resolve_point(lb[0], solid_vertices, named_points), _resolve_point(lb[1], solid_vertices, named_points)
        normal = _cross(_sub(v1, u1), _sub(v2, u2))
    else:
        raise ValueError(f"{case_id}: unsupported plane kind {kind!r}")

    if _norm_sq(normal) == 0:
        raise ValueError(f"{case_id}: degenerate zero plane normal")
    d = _dot(normal, tp)
    return normal, d


def _order_coplanar_polygon(case_id: str, items: list[tuple[Vec3, dict[str, Any]]], normal: Vec3) -> list[tuple[Vec3, dict[str, Any]]]:
    m = len(items)
    if m < 3:
        raise ValueError(f"{case_id}: section has fewer than 3 vertices ({m})")

    cx = sum(pt[0] for pt, _ in items) / m
    cy = sum(pt[1] for pt, _ in items) / m
    cz = sum(pt[2] for pt, _ in items) / m
    centroid: Vec3 = (cx, cy, cz)

    e1 = _sub(items[0][0], centroid)
    if _norm_sq(e1) == 0:
        raise ValueError(f"{case_id}: polygon vertex coincides with centroid")
    e2 = _cross(normal, e1)

    def _half(x: Fraction, y: Fraction) -> int:
        if x == 0 and y == 0:
            raise ValueError(f"{case_id}: degenerate zero local coordinates in section plane")
        if y > 0 or (y == 0 and x > 0):
            return 0
        return 1

    def _cmp(a: tuple[Vec3, dict[str, Any]], b: tuple[Vec3, dict[str, Any]]) -> int:
        va = _sub(a[0], centroid)
        vb = _sub(b[0], centroid)
        xa, ya = _dot(va, e1), _dot(va, e2)
        xb, yb = _dot(vb, e1), _dot(vb, e2)
        ha, hb = _half(xa, ya), _half(xb, yb)
        if ha != hb:
            return -1 if ha < hb else 1
        cross_2d = xa * yb - ya * xb
        if cross_2d > 0:
            return -1
        if cross_2d < 0:
            return 1
        return 0

    ordered = sorted(items, key=cmp_to_key(_cmp))

    for i in range(m):
        p_prev = ordered[i][0]
        p_curr = ordered[(i + 1) % m][0]
        p_next = ordered[(i + 2) % m][0]
        turn = _dot(_cross(_sub(p_curr, p_prev), _sub(p_next, p_curr)), normal)
        if turn <= 0:
            raise ValueError(f"{case_id}: section polygon is not strictly convex at index {i} (turn={turn})")

    return ordered


def compute_case_oracle(case: dict[str, Any], geom: dict[str, Any]) -> dict[str, Any]:
    case_id = case["id"]
    payload = case["payload"]
    solid_vertices = {k: _vec(v) for k, v in geom["solid_vertices"].items()}
    named_points = {k: _vec(v) for k, v in (geom.get("named_points") or {}).items()}

    _verify_premises(case_id, payload, solid_vertices, named_points)

    normal, d = _plane_normal_and_d(case_id, geom["plane"], solid_vertices, named_points)

    by_point: dict[Vec3, dict[str, Any]] = {}
    for u_lbl, v_lbl in geom["solid_edges"]:
        u = solid_vertices[u_lbl]
        v = solid_vertices[v_lbl]
        fu = _dot(normal, u) - d
        fv = _dot(normal, v) - d
        if fu == 0 and fv == 0:
            by_point[u] = {"vertex": u_lbl}
            by_point[v] = {"vertex": v_lbl}
        elif fu != fv:
            t = -fu / (fv - fu)
            if Fraction(0) <= t <= Fraction(1):
                if t == 0:
                    by_point[u] = {"vertex": u_lbl}
                elif t == 1:
                    by_point[v] = {"vertex": v_lbl}
                else:
                    pt = _add(u, _scale(t, _sub(v, u)))
                    if pt not in by_point:
                        by_point[pt] = {"edge": [u_lbl, v_lbl], "t": _f_str(t)}

    sec_spec = payload["derived_sections"][0]
    for st in sec_spec.get("stated_intersections") or ():
        u_lbl, v_lbl = st["edge"]
        u = solid_vertices[u_lbl]
        v = solid_vertices[v_lbl]
        fu = _dot(normal, u) - d
        fv = _dot(normal, v) - d
        if fu == fv:
            raise ValueError(f"{case_id}: stated lateral edge {u_lbl}{v_lbl} is parallel to cutting plane")
        t = -fu / (fv - fu)
        if not (Fraction(0) < t < Fraction(1)):
            raise ValueError(f"{case_id}: stated lateral edge {u_lbl}{v_lbl} cut at t={t}, outside (0, 1)")

    items = list(by_point.items())
    ordered = _order_coplanar_polygon(case_id, items, normal)

    p0 = ordered[0][0]
    area_vec: Vec3 = (Fraction(0), Fraction(0), Fraction(0))
    for i in range(1, len(ordered) - 1):
        pi = ordered[i][0]
        pj = ordered[i + 1][0]
        area_vec = _add(area_vec, _cross(_sub(pi, p0), _sub(pj, p0)))

    area_sq = _norm_sq(area_vec) / Fraction(4)
    if area_sq <= 0:
        raise ValueError(f"{case_id}: non-positive area_squared={area_sq}")

    math_goals = payload.get("math_goals") or []
    area_goal_id = math_goals[0]["goal_id"] if math_goals else None
    exp_cat = case.get("expected_category") or geom.get("expected_certificate_category")

    return {
        "id": case_id,
        "case_id": case_id,
        "solid": payload["solids"][0]["notation"],
        "solid_id": payload["solids"][0]["solid_id"],
        "section_id": sec_spec["section_id"],
        "expected_certificate_category": exp_cat,
        "expected_category": exp_cat,
        "question_type": case["question_type"],
        "area_goal_id": area_goal_id,
        "vertex_count": len(ordered),
        "boundary": [desc for _, desc in ordered],
        "polygon_3d": [[_f_str(c) for c in pt] for pt, _ in ordered],
        "area_squared": _f_str(area_sq),
        "plane_equation": {
            "normal": [_f_str(c) for c in normal],
            "d": _f_str(d),
        },
    }


def build_expected_payload() -> dict[str, Any]:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    geom_raw = json.loads(GEOMETRY_PATH.read_text(encoding="utf-8"))
    geom_cases = geom_raw.get("cases", geom_raw)

    positive_cases = [c for c in corpus["cases"] if c["expected_disposition"] == "SERVE"]
    if len(positive_cases) != 72:
        raise ValueError(f"Expected 72 positive cases, found {len(positive_cases)}")

    cases_dict: dict[str, Any] = {}
    for case in positive_cases:
        cid = case["id"]
        if cid not in geom_cases:
            raise KeyError(f"Missing geometry entry for {cid}")
        cases_dict[cid] = compute_case_oracle(case, geom_cases[cid])

    result: dict[str, Any] = {
        "schema": "HOLDOUT_WAVE3_EXPECTED_ORACLE/1",
        "task": "HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3",
        "positive_case_count": len(cases_dict),
        "cases": cases_dict,
    }
    for cid, entry in cases_dict.items():
        result[cid] = entry
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Holdout Wave 3 Independent Exact-Fraction Oracle")
    parser.add_argument("--write", action="store_true", help="Write oracle/expected.json")
    parser.add_argument("--check", action="store_true", help="Verify oracle/expected.json against recomputation")
    args = parser.parse_args(argv)

    if not args.write and not args.check:
        parser.error("Specify --write and/or --check")

    computed = build_expected_payload()

    if args.write:
        EXPECTED_PATH.parent.mkdir(parents=True, exist_ok=True)
        EXPECTED_PATH.write_text(
            json.dumps(computed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {len(computed['cases'])} oracle entries to {EXPECTED_PATH}")

    if args.check:
        if not EXPECTED_PATH.exists():
            raise FileNotFoundError(f"Missing {EXPECTED_PATH}")
        on_disk = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
        if on_disk != computed:
            raise AssertionError("oracle/expected.json does not match exact recomputation")
        print(f"OK: verified {len(computed['cases'])} positive cases in {EXPECTED_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
