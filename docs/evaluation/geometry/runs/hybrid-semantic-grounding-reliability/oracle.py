"""Independent oracle for run `hybrid-semantic-grounding-reliability` — no `app` import.

Reads `corpus.json`, computes for every case that must SERVE the exact squared answer of each request from the figure's
coordinates (Fractions, Euclidean), and writes `oracle.json`. The expected outcome classes (SERVE / REFUSE / acceptable
codes) are the author's semantic labels in the corpus; this file only adds the exact values and checks that every label
a SERVE case needs is well-defined (a four-label "plane" must be coplanar, a line must be non-degenerate).

    python oracle.py            # writes oracle.json next to this file; refuses to overwrite a different oracle.json
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent

FIGURES = {
    # S.ABCD, square base side 2, SA ⊥ (ABCD), SA = 3
    "pyramid": {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 3)},
    # cube ABCD.A'B'C'D' side 2
    "cube": {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0),
             "A'": (0, 0, 2), "B'": (2, 0, 2), "C'": (2, 2, 2), "D'": (0, 2, 2)},
}


def sub(a, b): return tuple(F(x) - F(y) for x, y in zip(a, b))
def dot(a, b): return sum(F(x) * F(y) for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def point(fig, p):
    if isinstance(p, str):
        return tuple(F(x) for x in FIGURES[fig][p])
    kind, *ops = p
    pts = [point(fig, o) for o in ops]
    if kind == "mid":
        return tuple((x + y) / 2 for x, y in zip(*pts))
    raise ValueError(kind)


def plane(fig, labels):
    a, b, c, *rest = [point(fig, x) for x in labels]
    n = cross(sub(b, a), sub(c, a))
    if n == (0, 0, 0):
        raise ValueError(f"degenerate plane {labels}")
    if any(dot(n, sub(r, a)) for r in rest):
        raise ValueError(f"not a plane: {labels} are not coplanar")
    return n, dot(n, a)


def d2_point_plane(fig, p, labels):
    n, c = plane(fig, labels)
    return (dot(n, point(fig, p)) - c) ** 2 / dot(n, n)


def d2_point_line(fig, p, a, d):
    v = cross(sub(point(fig, p), a), d)
    return dot(v, v) / dot(d, d)


def line_of(fig, spec):
    if spec[0] == "named":
        a, b = point(fig, spec[1][0]), point(fig, spec[1][1])
        return a, sub(b, a)
    (n1, c1), (n2, c2) = plane(fig, spec[1]), plane(fig, spec[2])
    d = cross(n1, n2)
    if d == (0, 0, 0):
        raise ValueError("parallel planes: no intersection line")
    # point on both planes with d·x = 0 (Cramer on rows n1, n2, d)
    rows, rhs = [n1, n2, d], [c1, c2, F(0)]
    det = dot(rows[0], cross(rows[1], rows[2]))
    cols = [tuple(r[i] for r in rows) for i in range(3)]
    def det3(c0, c1_, c2_): return dot(c0, cross(c1_, c2_))
    x = [det3(*[tuple(rhs) if j == i else cols[j] for j in range(3)]) / det for i in range(3)]
    return tuple(x), d


def volume_pyramid(fig, apex, base):
    s, pts = point(fig, apex), [point(fig, b) for b in base]
    v = sum(abs(dot(sub(pts[i], pts[0]), cross(sub(pts[i + 1], pts[0]), sub(s, pts[0])))) for i in range(1, len(pts) - 1)) / 6
    return v ** 2


def value(fig, r):
    q = r["q"]
    if q == "dist_point_plane":
        return d2_point_plane(fig, r["point"], r["plane"])
    if q == "dist_point_line":
        a, d = line_of(fig, r["line"])
        return d2_point_line(fig, r["point"], a, d)
    if q == "length":
        v = sub(point(fig, r["a"]), point(fig, r["b"]))
        return dot(v, v)
    if q == "volume_pyramid":
        return volume_pyramid(fig, r["apex"], r["base"])
    if q == "dist_lines":                      # skew or parallel lines through two named points each
        (a1, b1), (a2, b2) = [[point(fig, x) for x in ln] for ln in (r["l1"], r["l2"])]
        d1, d2 = sub(b1, a1), sub(b2, a2)
        n = cross(d1, d2)
        if n == (0, 0, 0):
            return d2_point_line(fig, r["l2"][0], a1, d1)
        return dot(n, sub(a2, a1)) ** 2 / dot(n, n)
    if q == "angle_line_plane_cos2":          # cos² of the angle between a line and a plane
        n, _c = plane(fig, r["plane"])
        d = sub(point(fig, r["line"][1]), point(fig, r["line"][0]))
        return 1 - dot(n, d) ** 2 / (dot(n, n) * dot(d, d))
    raise ValueError(q)


def main() -> int:
    corpus = json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))
    unseen = json.loads((HERE / "unseen" / "cases.json").read_text(encoding="utf-8"))
    out = {"run": corpus["run"], "values": {}}
    for case in corpus["cases"] + unseen["cases"]:
        if case["expect"] not in ("SERVE",):
            continue
        out["values"][case["id"]] = {r["id"]: str(value(case["figure"], r)) for r in case["requests"]}
    text = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    target = HERE / "oracle.json"
    if target.exists() and target.read_text(encoding="utf-8") != text:
        print("oracle.json exists with different content — refusing to overwrite", file=sys.stderr)
        return 1
    target.write_text(text, encoding="utf-8")
    print(f"{len(out['values'])} serve cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
