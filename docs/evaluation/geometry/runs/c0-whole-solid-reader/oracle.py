# -*- coding: utf-8 -*-
"""Independent oracle for c0-whole-solid-reader. No product import.

For every row: does each hand-written whole-solid premise in `claims` hold on the given coordinates (own vector code,
exact fractions)? A regular pyramid: base regular (square: equal sides + right angle + parallelogram; triangle: three
equal sides) and apex on the base normal through the base centroid, off the base plane. An unnamed claim (P2 rows) is
checked on the row's `solid`. Volume: |det| / 6 summed over a fan of the base.
`refused` rows must break a claim; `served:<V>` rows must break none and match V; `baseline` rows must break a claim
(they document a contradiction that stays served on purpose). Run: python oracle.py  (exit 1 on any disagreement).
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROWS = json.loads((Path(__file__).resolve().parent / "labels.json").read_text(encoding="utf-8"))["rows"]
sub = lambda a, b: tuple(x - y for x, y in zip(a, b))  # noqa: E731
dot = lambda a, b: sum(x * y for x, y in zip(a, b))  # noqa: E731
cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])  # noqa: E731
n2 = lambda a: dot(a, a)  # noqa: E731


def regular(P: dict, S: str, base: list) -> bool:
    b = [P[x] for x in base]
    k = len(b)
    sides = {n2(sub(b[(i + 1) % k], b[i])) for i in range(k)}
    if len(sides) != 1:
        return False
    if k == 4 and (sub(b[1], b[0]) != sub(b[2], b[3]) or dot(sub(b[1], b[0]), sub(b[3], b[0])) != 0):
        return False
    nrm = cross(sub(b[1], b[0]), sub(b[2], b[0]))
    g = tuple(sum(p[i] for p in b) / k for i in range(3))
    h = sub(P[S], g)
    return cross(h, nrm) == (0, 0, 0) and dot(h, nrm) != 0


def holds(r: dict, P: dict) -> bool:
    for c in r["claims"]:
        if "regular_pyramid" in c and not regular(P, c["regular_pyramid"][0], c["regular_pyramid"][1]):
            return False
        if c.get("regular_pyramid_unnamed") and not regular(P, r["solid"]["apex"], r["solid"]["base"]):
            return False
    return True


def volume(r: dict, P: dict) -> F:
    S, b = P[r["solid"]["apex"]], [P[x] for x in r["solid"]["base"]]
    return abs(sum(F(dot(sub(S, b[0]), cross(sub(b[i], b[0]), sub(b[i + 1], b[0]))), 6) for i in range(1, len(b) - 1)))


def main() -> int:
    bad = 0
    for rid, r in ROWS.items():
        P = {k: tuple(F(str(c)) for c in v) for k, v in r["points"].items()}
        ok, e = holds(r, P), r["expect"]
        if e in ("refused", "baseline") and ok:
            print("DISAGREE", rid, e, "but every claim holds"); bad += 1
        if e.startswith("served:"):
            if not ok:
                print("DISAGREE", rid, "served but a claim breaks"); bad += 1
            elif volume(r, P) != F(e.split(":", 1)[1]):
                print("DISAGREE", rid, "volume", volume(r, P)); bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)", f"({len(ROWS)} rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
