"""Independent oracle of run `goal-directed-function-composition` — no `app.*` import, no engine layout.

Each positive case declares its OWN chart: point coordinates (rational strings) and the Gram matrix G of that chart
(Euclidean cases use G = I). Described points are rebuilt here from their definition (midpoint: mean of 2, centroid: mean
of 3) and every goal is measured with exact Fractions:

    ⟨x, y⟩ = xᵀ G y                     length²  = ⟨w, w⟩
    area²(P,Q,R)   = (⟨u,u⟩⟨v,v⟩ − ⟨u,v⟩²) / 4
    dist²(P, AB)   = ⟨w,w⟩ − ⟨w,u⟩² / ⟨u,u⟩
    dist²(P, ABC)  = det Gram(u, v, w) / det Gram(u, v)
    cos²(PQ, AB)   = ⟨w,u⟩² / (⟨w,w⟩⟨u,u⟩)
    cos²(PQ, ABC)  = 1 − det Gram(u, v, w) / (⟨w,w⟩ det Gram(u, v))

The engine never sees this chart: it chooses its own layout from the typed facts. Agreement is therefore evidence about the
served answer, not a replay of the engine's arithmetic.

    python oracle.py <corpus.json>     # prints {case_id: {goal_id: expected}} as JSON
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path


def _vec(p, q):
    return [q[i] - p[i] for i in range(3)]


class Chart:
    def __init__(self, geometry: dict):
        self.pts = {k: [F(x) for x in v] for k, v in geometry["points"].items()}
        self.G = [[F(x) for x in row] for row in geometry.get("gram") or [[1, 0, 0], [0, 1, 0], [0, 0, 1]]]
        if not (self.G[0][0] > 0 and self._det2(0, 1) > 0 and self._det3() > 0):
            raise ValueError("Gram matrix is not positive definite")

    def _det2(self, i, j):
        return self.G[i][i] * self.G[j][j] - self.G[i][j] * self.G[j][i]

    def _det3(self):
        g = self.G
        return (g[0][0] * (g[1][1] * g[2][2] - g[1][2] * g[2][1]) - g[0][1] * (g[1][0] * g[2][2] - g[1][2] * g[2][0])
                + g[0][2] * (g[1][0] * g[2][1] - g[1][1] * g[2][0]))

    def ip(self, x, y):
        return sum(x[i] * self.G[i][j] * y[j] for i in range(3) for j in range(3))

    def point(self, ref):
        """A label, or {"desc": midpoint|centroid, "of": [labels]} rebuilt from its definition."""
        if isinstance(ref, str):
            return self.pts[ref]
        ops = [self.pts[o] for o in ref["of"]]
        need = {"midpoint": 2, "centroid": 3}[ref["desc"]]
        if len(ops) != need:
            raise ValueError(f"{ref['desc']} needs {need} points")
        return [sum(p[i] for p in ops) / need for i in range(3)]

    def gram(self, *vs):
        return [[self.ip(a, b) for b in vs] for a in vs]

    @staticmethod
    def det(m):
        if len(m) == 2:
            return m[0][0] * m[1][1] - m[0][1] * m[1][0]
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def measure(chart: Chart, goal: dict) -> F:
    """`goal`: {"measure", "point", "partner"?, "target"}. Returns length²/area²/distance² or cos² (angles)."""
    m, P = goal["measure"], chart.point(goal["point"])
    t = goal.get("target")
    if m == "volume_tetrahedron":                          # apex P, base triangle t: V² = det Gram(AB, AC, AP) / 36
        a, b, c = (chart.point(x) for x in t)
        return chart.det(chart.gram(_vec(a, b), _vec(a, c), _vec(a, P))) / 36
    if m == "length":
        w = _vec(P, chart.point(t))
        return chart.ip(w, w)
    if m == "area":
        u, v = _vec(P, chart.point(t[0])), _vec(P, chart.point(t[1]))
        d = chart.det(chart.gram(u, v))
        if d <= 0:
            raise ValueError("degenerate triangle")
        return d / 4
    if m == "distance_line":
        a, b = chart.point(t[0]), chart.point(t[1])
        u, w = _vec(a, b), _vec(a, P)
        return chart.ip(w, w) - chart.ip(w, u) ** 2 / chart.ip(u, u)
    if m == "distance_plane":
        a, b, c = (chart.point(x) for x in t[:3])
        u, v, w = _vec(a, b), _vec(a, c), _vec(a, P)
        return chart.det(chart.gram(u, v, w)) / chart.det(chart.gram(u, v))
    Q = chart.point(goal["partner"]) if "partner" in goal else None
    w = _vec(P, Q)
    if chart.ip(w, w) == 0:
        raise ValueError("degenerate line")
    if m == "cos2_lines":
        a, b = chart.point(t[0]), chart.point(t[1])
        u = _vec(a, b)
        return chart.ip(w, u) ** 2 / (chart.ip(w, w) * chart.ip(u, u))
    if m == "cos2_line_plane":
        a, b, c = (chart.point(x) for x in t[:3])
        u, v = _vec(a, b), _vec(a, c)
        return 1 - chart.det(chart.gram(u, v, w)) / (chart.ip(w, w) * chart.det(chart.gram(u, v)))
    raise ValueError(f"unknown measure {m}")


def expected(case: dict) -> dict[str, str]:
    chart = Chart(case["geometry"])
    return {gid: str(measure(chart, g)) for gid, g in case["goals"].items()}


def main(path: str) -> None:
    corpus = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {c["id"]: expected(c) for c in corpus["cases"] if c.get("geometry")}
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
