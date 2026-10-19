"""Independent oracle of run `geometry-capability-expansion` — no `app.*` import, no engine layout.

Reuses the Gram chart / measures of run `goal-directed-function-composition` (read-only import of its frozen `oracle.py`)
and adds, on EUCLIDEAN charts only (G = I, asserted):
    area2_polygon    vector area of a planar polygon given in cyclic order
    volume_pyramid   (S_base · h / 3)², base any planar polygon
    volume_prism     (S_base · h)², h = distance of a top vertex to the base plane
    section_area     the section of a pyramid by the plane through a point ⊥ a line, computed here: plane ∩ edges,
                     convex ordering, vector area — the engine's construction is never consulted
Points may also be {"divide": [A, B], "t": "p/q"} = (1 − t)A + tB.

    python oracle.py <corpus.json>
"""
from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction as F
from functools import cmp_to_key
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1] / "goal-directed-function-composition" / "oracle.py"
_spec = importlib.util.spec_from_file_location("composition_oracle_2a", _BASE)
_o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_o)


class Chart(_o.Chart):
    def point(self, ref):
        if isinstance(ref, dict) and "divide" in ref:
            a, b, t = self.point(ref["divide"][0]), self.point(ref["divide"][1]), F(ref["t"])
            return [(1 - t) * a[i] + t * b[i] for i in range(3)]
        return super().point(ref)

    def euclid(self):
        if self.G != [[F(1), 0, 0], [0, F(1), 0], [0, 0, F(1)]]:
            raise ValueError("Euclidean chart required")


def _cross(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def _dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def area2_polygon(ps):
    s = [F(0)] * 3
    for i in range(len(ps)):
        c = _cross(ps[i], ps[(i + 1) % len(ps)])
        s = [s[j] + c[j] for j in range(3)]
    return _dot(s, s) / 4


def _convex_order(ps, normal):
    c = [sum(p[i] for p in ps) / len(ps) for i in range(3)]
    ref = _sub(ps[0], c)

    def half(v):                                          # 0: angle in [0, π), 1: [π, 2π) around `normal` from `ref`
        s = _dot(_cross(ref, v), normal)
        return 0 if s > 0 or (s == 0 and _dot(ref, v) > 0) else 1

    def cmp(a, b):
        va, vb = _sub(a, c), _sub(b, c)
        ha, hb = half(va), half(vb)
        if ha != hb:
            return ha - hb
        s = _dot(_cross(va, vb), normal)
        return -1 if s > 0 else 1 if s < 0 else 0

    return sorted(ps, key=cmp_to_key(cmp))


def section_area2(chart, solid, point, line):
    """Pyramid `solid` = {"apex": S, "base": [..]}: plane through `point` ⊥ line(line[0], line[1])."""
    chart.euclid()
    p, n = chart.point(point), _sub(chart.point(line[1]), chart.point(line[0]))
    base, apex = solid["base"], solid["apex"]
    edges = [(base[i], base[(i + 1) % len(base)]) for i in range(len(base))] + [(apex, v) for v in base]
    pts = []
    for a, b in edges:
        A, B = chart.point(a), chart.point(b)
        fa, fb = _dot(_sub(A, p), n), _dot(_sub(B, p), n)
        cand = [A] if fa == 0 else []
        cand += [B] if fb == 0 else []
        if fa * fb < 0:
            t = fa / (fa - fb)
            cand.append([A[i] + t * (B[i] - A[i]) for i in range(3)])
        for x in cand:
            if x not in pts:
                pts.append(x)
    if len(pts) < 3:
        raise ValueError("plane does not cut the solid in a polygon")
    return area2_polygon(_convex_order(pts, n))


def measure(chart, goal):
    m = goal["measure"]
    if m == "volume_pyramid":
        chart.euclid()
        base = [chart.point(v) for v in goal["base"]]
        nn = _cross(_sub(base[1], base[0]), _sub(base[2], base[0]))
        h2 = _dot(nn, _sub(chart.point(goal["apex"]), base[0])) ** 2 / _dot(nn, nn)
        return area2_polygon(base) * h2 / 9
    if m == "volume_prism":
        a, b, c = (chart.point(x) for x in goal["base"][:3])   # triangular base, Gram form (any chart)
        uu, vv = _o._vec(a, b), _o._vec(a, c)
        s2 = chart.det(chart.gram(uu, vv)) / 4
        h2 = chart.det(chart.gram(uu, vv, _o._vec(a, chart.point(goal["top"])))) / chart.det(chart.gram(uu, vv))
        return s2 * h2
    if m == "section_area":
        return section_area2(chart, goal["solid"], goal["point"], goal["line"])
    return _o.measure(chart, goal)


def expected(case):
    chart = Chart(case["geometry"])
    return {gid: str(measure(chart, g)) for gid, g in case["goals"].items()}


if __name__ == "__main__":
    corpus = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({c["id"]: expected(c) for c in corpus["cases"] if c.get("geometry")}, ensure_ascii=False, indent=1))
