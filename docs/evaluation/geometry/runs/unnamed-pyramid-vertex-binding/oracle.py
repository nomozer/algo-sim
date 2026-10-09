# -*- coding: utf-8 -*-
"""Independent oracle for unnamed-pyramid-vertex-binding. No product import.

Model of a regular pyramid with base side b and height h: square base corners (±½, ±½)·b in cycle order, triangle
(0,0), (1,0), (½, ½√3)·b (√3 carried as a coefficient), apex over the centroid at height h. Every point the text uses
(vertex, intersection of the two base diagonals, centroid of three vertices) is an affine combination of positions, so
every squared distance is α·b² + β·h² with α, β ∈ ℚ. For EACH injective labelling of the named points onto the positions
the text's facts become linear equations in (B, H) = (b², h²) (role 'lateral XY' = one end is the apex); a labelling is
consistent iff the system has a solution with B, H > 0. Verdict over all labellings — determined / ambiguous /
contradiction / missing — must equal the label's `text_verdict`. Run: python oracle.py (exit 1 on disagreement).
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

ROWS = json.loads((Path(__file__).resolve().parent / "labels.json").read_text(encoding="utf-8"))["rows"]
HALF = F(1, 2)
# position → (x, y, y√3 part, z): b-scaled horizontal, h-scaled vertical
POS = {
    "square": [(-HALF, -HALF, 0, 0), (HALF, -HALF, 0, 0), (HALF, HALF, 0, 0), (-HALF, HALF, 0, 0), (0, 0, 0, 1)],
    "tri": [(0, 0, 0, 0), (1, 0, 0, 0), (HALF, 0, HALF, 0), (HALF, 0, F(1, 6), 1)],
}
APEX = {"square": 4, "tri": 3}


def sq(v: str) -> F:
    m = re.fullmatch(r"(\d+(?:/\d+)?)?(?:√(\d+))?", v)
    q = F(m.group(1) or 1)
    return q * q * int(m.group(2) or 1)


def mean(ps):
    return tuple(sum(F(p[i]) for p in ps) / len(ps) for i in range(4))


def d2(p, q):
    """(α, β): |p − q|² = α·b² + β·h²."""
    dx, dy, dr, dz = (F(p[i]) - F(q[i]) for i in range(4))
    return dx * dx + dy * dy + 3 * dr * dr, dz * dz


def solve(eqs):
    """eqs: [(a, b, c)] meaning a·B + b·H = c. → ('none'|'unique'|'line'|'free', data)."""
    rows = [e for e in eqs if e[0] or e[1]]
    if any(not e[0] and not e[1] and e[2] for e in eqs):
        return "none", None
    if not rows:
        return "free", None
    a0, b0, c0 = rows[0]
    for a, b, c in rows[1:]:
        det = a0 * b - b0 * a
        if det:
            B, H = (c0 * b - b0 * c) / det, (a0 * c - c0 * a) / det
            return ("unique", (B, H)) if all(a * B + b * H == c for a, b, c in rows) and B > 0 and H > 0 else ("none", None)
        if a0 * c != a * c0 or b0 * c != b * c0:          # parallel, different right side
            return "none", None
    # one line a0 B + b0 H = c0: positive solutions?
    pos = (a0 > 0 and b0 > 0 and c0 > 0) or (a0 < 0 and b0 < 0 and c0 < 0) or (a0 * b0 < 0) or \
          (a0 == 0 and c0 / b0 > 0) or (b0 == 0 and c0 / a0 > 0)
    return ("line", (a0, b0, c0)) if pos else ("none", None)


def verdict(f: dict) -> str:
    kind, names = f["kind"], f["names"]
    pos = POS[kind]
    answers, open_answer = set(), False
    for perm in itertools.permutations(range(len(pos)), len(names)):
        P = dict(zip(names, (pos[i] for i in perm)))
        idx = dict(zip(names, perm))
        ok = True
        for h, spec in f.get("helpers", {}).items():
            if "intersection" in spec:                    # two vertex segments cross only as the base diagonals
                (a, c), (b, d) = spec["intersection"]
                diag = {frozenset({0, 2}), frozenset({1, 3})} if kind == "square" else set()
                ok &= {frozenset({idx[a], idx[c]}), frozenset({idx[b], idx[d]})} == diag
                P[h] = mean([pos[0], pos[2]])
            if "centroid" in spec:
                P[h] = mean([P[x] for x in spec["centroid"]])
        if not ok:
            continue
        if any(not ({idx[x], idx[y]} & {APEX[kind]}) or idx[x] == idx[y] for role, (x, y) in f.get("roles", [])
               if role == "lateral"):
            continue
        eqs = [(*d2(P[x], P[y]), sq(v)) for (x, y), v in f.get("lengths", [])]
        for chain in f.get("equal", []):
            first = d2(P[chain[0][0]], P[chain[0][1]])
            eqs += [(d2(P[x], P[y])[0] - first[0], d2(P[x], P[y])[1] - first[1], F(0)) for x, y in chain[1:]]
        dims = f.get("dims", {})
        if "base" in dims:
            eqs.append((F(1), F(0), sq(dims["base"])))
        if "height" in dims:
            eqs.append((F(0), F(1), sq(dims["height"])))
        kind_, sol = solve(eqs)
        if kind_ == "none":
            continue
        if f["ask"] == "volume":
            if kind_ != "unique":
                open_answer = True
                continue
            B, H = sol
            answers.add(B * B * H / (9 if kind == "square" else 48))          # V²
        else:
            al, be = d2(P[f["ask"][0]], P[f["ask"][1]])
            if kind_ == "unique":
                answers.add(al * sol[0] + be * sol[1])
            elif kind_ == "line" and al * sol[1] == be * sol[0]:
                k = (al / sol[0]) if sol[0] else (be / sol[1])
                answers.add(k * sol[2])
            else:
                open_answer = True
    if not answers and not open_answer:
        return "contradiction"
    if len(answers) > 1:
        return "ambiguous"
    if open_answer:
        return "missing"
    return "determined:" + fmt(next(iter(answers)), f["ask"] == "volume")


def fmt(sq_value: F, volume: bool) -> str:
    """answer² → the corpus way of writing the answer (q√n)."""
    for n in (1, 2, 3, 5, 6, 7, 17):
        r = sq_value / n
        num, den = r.numerator, r.denominator
        a, b = round(num ** 0.5), round(den ** 0.5)
        if a * a == num and b * b == den:
            q = F(a, b)
            return (f"{q}" if n == 1 else (f"√{n}" if q == 1 else f"{q.numerator}√{n}" + (
                f"/{q.denominator}" if q.denominator != 1 else "")))
    return f"sqrt({sq_value})"


def main() -> int:
    bad = 0
    for rid, r in ROWS.items():
        v = verdict(r["facts"])
        if v != r["text_verdict"]:
            print("DISAGREE", rid, r["text_verdict"], "oracle:", v); bad += 1
        exp = ("served:" + v.split(":", 1)[1]) if v.startswith("determined") and "program_defect" not in r["facts"] \
            else "refused"
        if exp != r["expect_option_b"]:
            print("DISAGREE expect", rid, r["expect_option_b"], exp); bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)", f"({len(ROWS)} rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
