"""Independent exact-rational mathematical oracle for Holdout Wave 2 (`hybrid-v2-independent-vietnamese-section-holdout-wave2`).

Pure Python + `fractions.Fraction` ONLY. Zero imports from `app.*`.
Supports `--write` (generates `oracle/expected.json` from `oracle/geometry.json`)
and `--check` (runs built-in self-tests and verifies `oracle/expected.json` against `oracle/geometry.json`).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

Vec3 = tuple[Fraction, Fraction, Fraction]

HERE = Path(__file__).resolve().parent
DEFAULT_GEOMETRY_PATH = HERE / "geometry.json"
DEFAULT_EXPECTED_PATH = HERE / "expected.json"


def _f(val: str | int | Fraction) -> Fraction:
    if isinstance(val, Fraction):
        return val
    s = str(val).strip()
    if s.endswith("a"):
        s = s[:-1].strip() or "1"
    return Fraction(s)


def _vec(coords: list[str | int | Fraction] | tuple[str | int | Fraction, ...]) -> Vec3:
    if len(coords) != 3:
        raise ValueError(f"Expected 3D coordinate triple, got {coords!r}")
    return (_f(coords[0]), _f(coords[1]), _f(coords[2]))


def v_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_scale(s: Fraction, a: Vec3) -> Vec3:
    return (s * a[0], s * a[1], s * a[2])


def v_dot(a: Vec3, b: Vec3) -> Fraction:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def v_norm_sq(a: Vec3) -> Fraction:
    return v_dot(a, a)


def v_is_zero(a: Vec3) -> bool:
    return a[0] == 0 and a[1] == 0 and a[2] == 0


def v_lerp(u: Vec3, v: Vec3, t: Fraction) -> Vec3:
    return v_add(v_scale(Fraction(1) - t, u), v_scale(t, v))


@dataclass(frozen=True)
class SectionVertex:
    pos: Vec3
    descriptor: dict[str, Any]
    incident_solid_vertices: frozenset[str]


def _verify_premise_checks(
    case_id: str,
    points: dict[str, Vec3],
    checks: list[dict[str, Any]],
) -> None:
    for chk in checks:
        kind = chk["kind"]
        if kind == "segment_length":
            u_lbl, v_lbl = chk["segment"]
            expected_len = _f(chk["value"])
            if expected_len <= 0:
                raise ValueError(f"{case_id}: non-positive segment_length {expected_len}")
            actual_sq = v_norm_sq(v_sub(points[v_lbl], points[u_lbl]))
            if actual_sq != expected_len * expected_len:
                raise ValueError(
                    f"{case_id}: segment {u_lbl}{v_lbl} squared length {actual_sq} != {expected_len**2}"
                )
        elif kind == "right_angle":
            v_lbl = chk["right_at"]
            u_lbl, w_lbl = [x for x in chk["vertices"] if x != v_lbl]
            dot = v_dot(v_sub(points[u_lbl], points[v_lbl]), v_sub(points[w_lbl], points[v_lbl]))
            if dot != 0:
                raise ValueError(f"{case_id}: angle at {v_lbl} in {chk['vertices']} not right (dot={dot})")
        elif kind == "perpendicular_line_plane":
            l1, l2 = chk["line"]
            p1, p2, p3 = chk["plane"][:3]
            line_vec = v_sub(points[l2], points[l1])
            if v_is_zero(line_vec):
                raise ValueError(f"{case_id}: degenerate line {chk['line']}")
            for q in chk["plane"][1:]:
                if v_dot(line_vec, v_sub(points[q], points[p1])) != 0:
                    raise ValueError(f"{case_id}: line {chk['line']} not perpendicular to plane {chk['plane']}")
            if v_is_zero(v_cross(v_sub(points[p2], points[p1]), v_sub(points[p3], points[p1]))):
                raise ValueError(f"{case_id}: degenerate plane {chk['plane']}")
        elif kind == "midpoint":
            pt = chk["point"]
            u_lbl, v_lbl = chk["segment"]
            mid = v_lerp(points[u_lbl], points[v_lbl], Fraction(1, 2))
            if points[pt] != mid:
                raise ValueError(f"{case_id}: midpoint {pt} != midpoint of {u_lbl}{v_lbl}")
        elif kind == "divide_segment":
            pt = chk["point"]
            u_lbl, v_lbl = chk["segment"]
            r = _f(chk["ratio"])
            if not (0 < r < 1):
                raise ValueError(f"{case_id}: divide_segment ratio {r} out of (0, 1)")
            expected_pt = v_lerp(points[u_lbl], points[v_lbl], r)
            if points[pt] != expected_pt:
                raise ValueError(f"{case_id}: ratio point {pt} != (1-{r}){u_lbl} + {r}{v_lbl}")
        elif kind == "centroid":
            pt = chk["point"]
            a_lbl, b_lbl, c_lbl = chk["polygon"]
            cent = v_scale(
                Fraction(1, 3),
                v_add(v_add(points[a_lbl], points[b_lbl]), points[c_lbl]),
            )
            if points[pt] != cent:
                raise ValueError(f"{case_id}: centroid {pt} mismatch")
        elif kind == "orthogonal_projection":
            pt = chk["point"]
            img = chk["image"]
            p1, p2, p3 = chk["plane"][:3]
            diff = v_sub(points[pt], points[img])
            if v_is_zero(diff):
                raise ValueError(f"{case_id}: projection point {pt} coincides with foot {img}")
            for q in chk["plane"][1:]:
                if v_dot(diff, v_sub(points[q], points[p1])) != 0:
                    raise ValueError(f"{case_id}: {pt}{img} not orthogonal to plane {chk['plane']}")
            n_plane = v_cross(v_sub(points[p2], points[p1]), v_sub(points[p3], points[p1]))
            if v_dot(n_plane, v_sub(points[img], points[p1])) != 0:
                raise ValueError(f"{case_id}: foot {img} does not lie in plane {chk['plane']}")
        else:
            raise ValueError(f"{case_id}: unknown check kind {kind!r}")


def _derive_plane(case_id: str, points: dict[str, Vec3], plane_spec: dict[str, Any]) -> tuple[Vec3, Fraction]:
    tp_label = plane_spec["through_point"]
    if tp_label not in points:
        raise ValueError(f"{case_id}: unknown through_point {tp_label!r}")
    p0 = points[tp_label]
    kind = plane_spec["kind"]
    if kind == "perpendicular_line":
        u_lbl, v_lbl = plane_spec["perpendicular_line"]
        normal = v_sub(points[v_lbl], points[u_lbl])
        if v_is_zero(normal):
            raise ValueError(f"{case_id}: degenerate perpendicular_line {u_lbl}{v_lbl}")
    elif kind == "parallel_plane":
        a_lbl, b_lbl, c_lbl = plane_spec["parallel_plane"]
        normal = v_cross(v_sub(points[b_lbl], points[a_lbl]), v_sub(points[c_lbl], points[a_lbl]))
        if v_is_zero(normal):
            raise ValueError(f"{case_id}: degenerate parallel_plane {plane_spec['parallel_plane']}")
        if v_dot(normal, points[a_lbl]) == v_dot(normal, p0):
            raise ValueError(f"{case_id}: through_point {tp_label} lies in reference parallel_plane")
    elif kind == "parallel_two_lines":
        u1, u2 = plane_spec["parallel_line_a"]
        v1, v2 = plane_spec["parallel_line_b"]
        dir_a = v_sub(points[u2], points[u1])
        dir_b = v_sub(points[v2], points[v1])
        normal = v_cross(dir_a, dir_b)
        if v_is_zero(normal):
            raise ValueError(f"{case_id}: parallel direction lines in parallel_two_lines")
    else:
        raise ValueError(f"{case_id}: unsupported plane_spec kind {kind!r}")
    d = v_dot(normal, p0)
    return normal, d


def _order_coplanar_polygon(
    case_id: str,
    verts: list[SectionVertex],
    normal: Vec3,
    faces: list[list[str]],
) -> list[SectionVertex]:
    m = len(verts)
    if m < 3:
        raise ValueError(f"{case_id}: section has fewer than 3 vertices ({m})")

    centroid = (
        sum((v.pos[0] for v in verts), Fraction(0)) / m,
        sum((v.pos[1] for v in verts), Fraction(0)) / m,
        sum((v.pos[2] for v in verts), Fraction(0)) / m,
    )
    e1 = v_sub(verts[0].pos, centroid)
    if v_is_zero(e1):
        raise ValueError(f"{case_id}: vertex coincides with centroid")
    e2 = v_cross(normal, e1)
    if v_is_zero(e2):
        raise ValueError(f"{case_id}: degenerate planar basis")

    def coords_2d(v: SectionVertex) -> tuple[Fraction, Fraction]:
        rel = v_sub(v.pos, centroid)
        return (v_dot(rel, e1), v_dot(rel, e2))

    upper: list[tuple[Fraction, Fraction, SectionVertex]] = []
    lower: list[tuple[Fraction, Fraction, SectionVertex]] = []
    for v in verts:
        x, y = coords_2d(v)
        if x == 0 and y == 0:
            raise ValueError(f"{case_id}: zero 2D projection at vertex {v.descriptor}")
        if y > 0 or (y == 0 and x > 0):
            upper.append((x, y, v))
        else:
            lower.append((x, y, v))

    def sort_half(items: list[tuple[Fraction, Fraction, SectionVertex]]) -> list[SectionVertex]:
        n_items = len(items)
        arr = list(items)
        for i in range(n_items):
            for j in range(i + 1, n_items):
                x1, y1, _ = arr[i]
                x2, y2, _ = arr[j]
                cross_2d = x1 * y2 - y1 * x2
                if cross_2d == 0:
                    raise ValueError(f"{case_id}: collinear rays from centroid in section polygon")
                if cross_2d < 0:
                    arr[i], arr[j] = arr[j], arr[i]
        return [item[2] for item in arr]

    ordered = sort_half(upper) + sort_half(lower)

    # Verify strict convexity in 3D and verify every consecutive pair lies on a common polyhedron face.
    face_sets = [frozenset(f) for f in faces]
    for i in range(m):
        p_prev = ordered[(i - 1) % m].pos
        p_curr = ordered[i].pos
        p_next = ordered[(i + 1) % m].pos
        turn = v_dot(normal, v_cross(v_sub(p_curr, p_prev), v_sub(p_next, p_curr)))
        if turn <= 0:
            raise ValueError(f"{case_id}: section polygon is not strictly convex at index {i} (turn={turn})")

        v_curr = ordered[i]
        v_nxt = ordered[(i + 1) % m]
        union_verts = v_curr.incident_solid_vertices | v_nxt.incident_solid_vertices
        if not any(union_verts <= fset for fset in face_sets):
            raise ValueError(
                f"{case_id}: consecutive section vertices {v_curr.descriptor} and {v_nxt.descriptor} do not share a solid face"
            )

    return ordered


def compute_case_oracle(case_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    points = {lbl: _vec(coords) for lbl, coords in spec["points"].items()}
    solid_vertices: list[str] = list(spec["solid_vertices"])
    edges: list[list[str]] = [list(e) for e in spec["edges"]]
    faces: list[list[str]] = [list(f) for f in spec["faces"]]

    for v in solid_vertices:
        if v not in points:
            raise ValueError(f"{case_id}: solid vertex {v!r} missing from points")

    # Verify each face is planar and has >= 3 vertices
    for f in faces:
        if len(f) < 3:
            raise ValueError(f"{case_id}: face {f} has < 3 vertices")
        f_norm = v_cross(v_sub(points[f[1]], points[f[0]]), v_sub(points[f[2]], points[f[0]]))
        if v_is_zero(f_norm):
            raise ValueError(f"{case_id}: degenerate face {f}")
        for u in f[3:]:
            if v_dot(f_norm, v_sub(points[u], points[f[0]])) != 0:
                raise ValueError(f"{case_id}: non-planar face {f}")

    _verify_premise_checks(case_id, points, spec.get("checks", []))
    normal, d = _derive_plane(case_id, points, spec["plane_spec"])

    signs = {v: v_dot(normal, points[v]) - d for v in solid_vertices}
    if not (any(s > 0 for s in signs.values()) and any(s < 0 for s in signs.values())):
        raise ValueError(f"{case_id}: cutting plane does not strictly separate solid vertices")

    for f in faces:
        if all(signs[v] == 0 for v in f):
            raise ValueError(f"{case_id}: cutting plane coincides with face {f}")

    section_verts: list[SectionVertex] = []
    for v in solid_vertices:
        if signs[v] == 0:
            section_verts.append(
                SectionVertex(
                    pos=points[v],
                    descriptor={"vertex": v},
                    incident_solid_vertices=frozenset([v]),
                )
            )

    edge_cut_lookup: dict[frozenset[str], tuple[list[str], Fraction]] = {}
    for u, v in edges:
        su, sv = signs[u], signs[v]
        if (su > 0 and sv < 0) or (su < 0 and sv > 0):
            t = su / (su - sv)
            if not (0 < t < 1):
                raise ValueError(f"{case_id}: invalid interior t={t} on edge {u}-{v}")
            pos = v_lerp(points[u], points[v], t)
            desc = {"edge": [u, v], "t": f"{t.numerator}/{t.denominator}" if t.denominator != 1 else str(t.numerator)}
            section_verts.append(
                SectionVertex(
                    pos=pos,
                    descriptor=desc,
                    incident_solid_vertices=frozenset([u, v]),
                )
            )
            edge_cut_lookup[frozenset([u, v])] = ([u, v], t)

    if spec["expected_certificate_category"] == "DINH_CAT_CANH":
        stated_edges = spec.get("stated_edges") or []
        if not stated_edges:
            raise ValueError(f"{case_id}: Category A case must declare stated_edges in geometry.json")
        for se in stated_edges:
            key = frozenset(se)
            if key not in edge_cut_lookup:
                raise ValueError(f"{case_id}: stated edge {se} is not cut strictly in its interior")

    ordered = _order_coplanar_polygon(case_id, section_verts, normal, faces)

    p0 = ordered[0].pos
    w_sum: Vec3 = (Fraction(0), Fraction(0), Fraction(0))
    for i in range(1, len(ordered) - 1):
        w_sum = v_add(
            w_sum,
            v_cross(v_sub(ordered[i].pos, p0), v_sub(ordered[i + 1].pos, p0)),
        )
    area_sq = v_norm_sq(w_sum) / Fraction(4)
    if area_sq <= 0:
        raise ValueError(f"{case_id}: non-positive area_squared {area_sq}")

    area_sq_str = (
        f"{area_sq.numerator}/{area_sq.denominator}"
        if area_sq.denominator != 1
        else str(area_sq.numerator)
    )

    return {
        "solid": spec["solid"],
        "section_id": spec["section_id"],
        "expected_certificate_category": spec["expected_certificate_category"],
        "area_goal_id": spec["area_goal_id"],
        "vertex_count": len(ordered),
        "boundary": [v.descriptor for v in ordered],
        "area_squared": area_sq_str,
    }


def run_self_tests() -> None:
    """Built-in hand-checked mathematical self-tests for the exact-Fraction oracle."""
    # Self-test 1: Right tetrahedron S.ABC with A=(0,0,0), B=(6,0,0), C=(0,8,0), S=(0,0,10).
    # Midpoint M of SA = (0,0,5). Plane through M parallel to (ABC) cuts SB at t=1/2, SC at t=1/2.
    # Right triangle section with legs 3 and 4 -> Area = 6 -> Area^2 = 36.
    st1 = compute_case_oracle(
        "SELFTEST-1",
        {
            "solid": "S.ABC",
            "section_id": "sec",
            "expected_certificate_category": "ENGINE_DERIVED_SECTION",
            "area_goal_id": "mg1",
            "solid_vertices": ["S", "A", "B", "C"],
            "edges": [["S", "A"], ["S", "B"], ["S", "C"], ["A", "B"], ["B", "C"], ["C", "A"]],
            "faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]],
            "points": {
                "A": [0, 0, 0],
                "B": [6, 0, 0],
                "C": [0, 8, 0],
                "S": [0, 0, 10],
                "M": [0, 0, 5],
            },
            "checks": [
                {"kind": "right_angle", "vertices": ["A", "B", "C"], "right_at": "A"},
                {"kind": "segment_length", "segment": ["A", "B"], "value": "6"},
                {"kind": "segment_length", "segment": ["A", "C"], "value": "8"},
                {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C"]},
                {"kind": "segment_length", "segment": ["S", "A"], "value": "10"},
                {"kind": "midpoint", "point": "M", "segment": ["S", "A"]},
            ],
            "plane_spec": {
                "kind": "parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
            },
        },
    )
    assert st1["vertex_count"] == 3, st1
    assert Fraction(st1["area_squared"]) == Fraction(36), st1

    # Self-test 2: Cube ABCD.A'B'C'D' of side 6. Plane through M (t=1/2 on AA') parallel to AB and B'C'
    # cuts AA', BB', CC', DD' or top/bottom in a rectangle. Let's test plane through A perpendicular to SC
    # in pyramid S.ABCD with square base side 6 and SA=6:
    # S=(0,0,6), A=(0,0,0), B=(6,0,0), C=(6,6,0), D=(0,6,0).
    # Normal SC = (6,6,-6) ~ (1,1,-1). Plane through A(0,0,0): x + y - z = 0.
    # Cuts SB=(6t, 0, 6(1-t)): 6t - 6 + 6t = 0 -> t = 1/2 -> (3,0,3).
    # Cuts SC=(6t, 6t, 6(1-t)): 12t - 6 + 6t = 0 -> t = 1/3 -> (2,2,4).
    # Cuts SD=(0, 6t, 6(1-t)): 6t - 6 + 6t = 0 -> t = 1/2 -> (0,3,3).
    # Quadrilateral A(0,0,0) - P_B(3,0,3) - P_C(2,2,4) - P_D(0,3,3).
    # Diagonal AC_sec = (2,2,4), BD_sec = (-3,3,0), perpendicular diagonals!
    # |AC_sec| = sqrt(24), |BD_sec| = sqrt(18), Area = 1/2 * sqrt(24*18) = 6*sqrt(3) -> Area^2 = 108.
    st2 = compute_case_oracle(
        "SELFTEST-2",
        {
            "solid": "S.ABCD",
            "section_id": "sec",
            "expected_certificate_category": "DINH_CAT_CANH",
            "area_goal_id": "mg1",
            "solid_vertices": ["S", "A", "B", "C", "D"],
            "edges": [
                ["S", "A"], ["S", "B"], ["S", "C"], ["S", "D"],
                ["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"],
            ],
            "faces": [
                ["A", "B", "C", "D"],
                ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"],
            ],
            "points": {
                "A": [0, 0, 0],
                "B": [6, 0, 0],
                "C": [6, 6, 0],
                "D": [0, 6, 0],
                "S": [0, 0, 6],
            },
            "checks": [
                {"kind": "segment_length", "segment": ["A", "B"], "value": "6"},
                {"kind": "segment_length", "segment": ["A", "D"], "value": "6"},
                {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                {"kind": "segment_length", "segment": ["S", "A"], "value": "6"},
            ],
            "plane_spec": {
                "kind": "perpendicular_line",
                "through_point": "A",
                "perpendicular_line": ["S", "C"],
            },
            "stated_edges": [["S", "B"], ["S", "C"], ["S", "D"]],
        },
    )
    assert st2["vertex_count"] == 4, st2
    assert Fraction(st2["area_squared"]) == Fraction(108), st2


def compute_all(geometry_path: Path) -> dict[str, Any]:
    raw = json.loads(geometry_path.read_text(encoding="utf-8"))
    if raw.get("schema") != "HOLDOUT_WAVE2_ORACLE_GEOMETRY/1":
        raise ValueError(f"Unexpected geometry schema: {raw.get('schema')!r}")
    cases = raw["cases"]
    if len(cases) != 48:
        raise ValueError(f"Expected exactly 48 positive oracle cases, got {len(cases)}")
    out: dict[str, Any] = {}
    for case_id, spec in cases.items():
        out[case_id] = compute_case_oracle(case_id, spec)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independent exact-Fraction oracle for Holdout Wave 2.")
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY_PATH)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED_PATH)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Write oracle/expected.json from oracle/geometry.json")
    group.add_argument("--check", action="store_true", help="Run self-tests and verify oracle/expected.json")
    args = parser.parse_args(argv)

    run_self_tests()
    computed = compute_all(args.geometry)

    if args.write:
        args.expected.parent.mkdir(parents=True, exist_ok=True)
        args.expected.write_text(
            json.dumps(computed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {len(computed)} oracle entries to {args.expected}")
        return 0

    if not args.expected.exists():
        print(f"ERROR: {args.expected} does not exist", file=sys.stderr)
        return 1
    existing = json.loads(args.expected.read_text(encoding="utf-8"))
    if existing != computed:
        print("ERROR: oracle/expected.json does not match recomputed oracle output", file=sys.stderr)
        return 1
    print(f"OK: self-tests passed and all {len(computed)} oracle entries in {args.expected.name} verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
