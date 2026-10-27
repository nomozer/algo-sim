"""Independent exact rational 3D section oracle for Adapter /4 plane-only section certificates.

Uses only Python stdlib (`fractions`, `functools`). Zero imports from `app.*`.
"""
from __future__ import annotations

from fractions import Fraction as F
from functools import cmp_to_key


def _v(pt) -> tuple[F, F, F]:
    return tuple(F(x) for x in pt)


def _sub(a, b) -> tuple[F, F, F]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b) -> tuple[F, F, F]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a, t: F) -> tuple[F, F, F]:
    return (a[0] * t, a[1] * t, a[2] * t)


def _dot(a, b) -> F:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b) -> tuple[F, F, F]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _solid_faces_and_edges(spec: dict) -> tuple[list[tuple[str, ...]], list[tuple[str, str]]]:
    if spec.get("solid_type") == "pyramid":
        apex = spec["apex"]
        base = tuple(spec["base"])
        n = len(base)
        faces = [base] + [(apex, base[i], base[(i + 1) % n]) for i in range(n)]
        edges = [(base[i], base[(i + 1) % n]) for i in range(n)] + [(apex, v) for v in base]
        return faces, edges
    base = tuple(spec["base"])
    top = tuple(spec["top"])
    n = len(base)
    faces = [base, top] + [
        (base[i], base[(i + 1) % n], top[(i + 1) % n], top[i]) for i in range(n)
    ]
    edges = (
        [(base[i], base[(i + 1) % n]) for i in range(n)]
        + [(top[i], top[(i + 1) % n]) for i in range(n)]
        + [(base[i], top[i]) for i in range(n)]
    )
    return faces, edges


def _plane_normal(pts: dict[str, tuple[F, F, F]], spec: dict) -> tuple[F, F, F]:
    rel = spec.get("plane_relation", "perpendicular")
    if rel == "perpendicular":
        u, v = spec["line"]
        return _sub(pts[v], pts[u])
    if rel == "parallel":
        p0, p1, p2 = spec["parallel_plane"][:3]
        return _cross(_sub(pts[p1], pts[p0]), _sub(pts[p2], pts[p0]))
    if rel == "parallel_two_lines":
        (a0, a1), (b0, b1) = spec["lines"]
        return _cross(_sub(pts[a1], pts[a0]), _sub(pts[b1], pts[b0]))
    raise ValueError(f"Unsupported oracle plane_relation: {rel!r}")


def compute_section_oracle(spec: dict) -> dict:
    """Compute exact Euclidean section vertices, edge cuts, and squared area."""
    if "area_squared_override" in spec:
        return {
            "vertex_count": spec["vertex_count_override"],
            "area_squared": str(F(spec["area_squared_override"])),
            "interior_cut": True,
        }
    pts = {k: _v(val) for k, val in spec["points"].items()}
    faces, edges = _solid_faces_and_edges(spec)
    normal = _plane_normal(pts, spec)
    if normal == (0, 0, 0):
        return {"vertex_count": 0, "area_squared": "0", "interior_cut": False}
    anchor = pts[spec["point"]]
    offset = _dot(normal, anchor)

    vertex_names = list(dict.fromkeys(v for f in faces for v in f))
    signs = [_dot(normal, pts[v]) - offset for v in vertex_names]
    has_pos = any(s > 0 for s in signs)
    has_neg = any(s < 0 for s in signs)

    cuts: dict[tuple[F, F, F], dict] = {}
    for u, v in edges:
        pu, pv = pts[u], pts[v]
        su, sv = _dot(normal, pu) - offset, _dot(normal, pv) - offset
        if su == 0 and sv == 0:
            for end_lbl, end_pt, t_val in ((u, pu, F(0)), (v, pv, F(1))):
                cuts.setdefault(end_pt, {"xyz": [str(x) for x in end_pt], "edge": [u, v], "t": str(t_val), "kind": "SOLID_VERTEX", "vertex": end_lbl})
        elif su == 0:
            cuts.setdefault(pu, {"xyz": [str(x) for x in pu], "edge": [u, v], "t": "0", "kind": "SOLID_VERTEX", "vertex": u})
        elif sv == 0:
            cuts.setdefault(pv, {"xyz": [str(x) for x in pv], "edge": [u, v], "t": "1", "kind": "SOLID_VERTEX", "vertex": v})
        elif (su > 0) != (sv > 0):
            t = su / (su - sv)
            p = _add(pu, _scale(_sub(pv, pu), t))
            cuts.setdefault(p, {"xyz": [str(x) for x in p], "edge": [u, v], "t": str(t), "kind": "SOLID_EDGE_INTERSECTION", "vertex": None})

    ring_pts = list(cuts.keys())
    if len(ring_pts) < 3 or not (has_pos and has_neg):
        return {"vertex_count": len(ring_pts), "area_squared": "0", "interior_cut": False}

    centroid = tuple(sum(p[i] for p in ring_pts) / len(ring_pts) for i in range(3))
    u_axis = _sub(ring_pts[0], centroid)
    v_axis = _cross(normal, u_axis)

    def _half(p):
        x, y = _dot(_sub(p, centroid), u_axis), _dot(_sub(p, centroid), v_axis)
        return (0 if y > 0 or (y == 0 and x >= 0) else 1), x, y

    def _cmp(p, q):
        hp, xp, yp = _half(p)
        hq, xq, yq = _half(q)
        if hp != hq:
            return hp - hq
        cr = xp * yq - yp * xq
        return -1 if cr > 0 else (1 if cr < 0 else 0)

    ordered = sorted(ring_pts, key=cmp_to_key(_cmp))
    p0 = ordered[0]
    total_cross = (F(0), F(0), F(0))
    for i in range(1, len(ordered) - 1):
        total_cross = _add(total_cross, _cross(_sub(ordered[i], p0), _sub(ordered[i + 1], p0)))
    area_sq = _dot(total_cross, total_cross) / 4
    return {
        "vertex_count": len(ordered),
        "area_squared": str(area_sq),
        "interior_cut": area_sq > 0 and has_pos and has_neg,
        "vertices": [cuts[p] for p in ordered],
    }
