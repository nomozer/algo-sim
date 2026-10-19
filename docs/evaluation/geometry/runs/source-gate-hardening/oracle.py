"""Independent oracle of run `source-gate-hardening` — no `app.*` import, no engine layout.

Reuses the measures of runs `goal-directed-function-composition` / `geometry-capability-expansion` (read-only import of
their frozen `oracle.py`) and adds, on EUCLIDEAN charts only:
    distance_intersection   distance² from a point to the line where two planes meet — the line is computed HERE from
                            the two planes (each given by ≥ 3 labels; coplanarity asserted), never read from the engine
Symbolic cases are written in units of a (a = 1); `power` is the degree of a the served answer must carry
(length/distance 1, area 2, volume 3, angle 0).

    python oracle.py <corpus.json>
"""
from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction as F
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1] / "geometry-capability-expansion" / "oracle.py"
_spec = importlib.util.spec_from_file_location("capability_oracle_2b", _BASE)
_o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_o)

POWER = {"length": 1, "distance_line": 1, "distance_plane": 1, "distance_intersection": 1, "area": 2,
         "volume_pyramid": 3, "volume_prism": 3, "volume_tetrahedron": 3, "cos2_lines": 0, "cos2_line_plane": 0}


def _plane(chart, labels):
    ps = [chart.point(x) for x in labels]
    n = _o._cross(_o._sub(ps[1], ps[0]), _o._sub(ps[2], ps[0]))
    if _o._dot(n, n) == 0 or any(_o._dot(n, _o._sub(p, ps[0])) != 0 for p in ps[3:]):
        raise ValueError(f"({''.join(labels)}) is not a plane")
    return n, _o._dot(n, ps[0])


def distance_intersection2(chart, point, planes):
    chart.euclid()
    (n1, d1), (n2, d2) = (_plane(chart, p) for p in planes)
    u = _o._cross(n1, n2)
    uu = _o._dot(u, u)
    if uu == 0:
        raise ValueError("planes are parallel or equal: no unique intersection line")
    a, b, c = _o._dot(n1, n1), _o._dot(n1, n2), _o._dot(n2, n2)
    p0 = [((d1 * c - d2 * b) * n1[i] + (d2 * a - d1 * b) * n2[i]) / uu for i in range(3)]   # on both planes
    w = _o._cross(_o._sub(chart.point(point), p0), u)
    return _o._dot(w, w) / uu


def measure(chart, goal):
    if goal["measure"] == "distance_intersection":
        return distance_intersection2(chart, goal["point"], goal["planes"])
    return _o.measure(chart, goal)


def expected(case):
    chart = _o.Chart(case["geometry"])
    return {gid: str(measure(chart, g)) for gid, g in case["goals"].items()}


def power(goal):
    return POWER[goal["measure"]]


if __name__ == "__main__":
    corpus = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({c["id"]: expected(c) for c in corpus["cases"] if c.get("geometry")}, ensure_ascii=False, indent=1))
