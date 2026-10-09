# -*- coding: utf-8 -*-
"""Independent oracle for regular-prisms. No product import.

Right prism with a regular k-gon base of side b and height h: base area = (3√3/2)·b² (k = 6), (√3/4)·b² (k = 3); the
lateral edge of a right prism IS the height; V = area·h, so V² = (27/4)·b⁴·h² (k = 6) or (3/16)·b⁴·h² (k = 3). A text is
servable iff it states a regular right prism with k ∈ {3, 6}, fixes b and fixes h by one or more consistent sources
(height, lateral edge), and the program is an affine regular prism. Run: python oracle.py (exit 1 on disagreement).
"""
from __future__ import annotations

import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

ROWS = json.loads((Path(__file__).resolve().parent / "labels.json").read_text(encoding="utf-8"))["rows"]


def sq(v: str) -> F:
    m = re.fullmatch(r"(\d+(?:/\d+)?)?(?:√(\d+))?", v)
    q = F(m.group(1) or 1)
    return q * q * int(m.group(2) or 1)


def fmt(x2: F) -> str:
    for n in (1, 3):
        r = x2 / n
        a, b = round(r.numerator ** 0.5), round(r.denominator ** 0.5)
        if a * a == r.numerator and b * b == r.denominator:
            q = F(a, b)
            if n == 1:
                return str(q)
            head = "" if q.numerator == 1 else str(q.numerator)
            return f"{head}√{n}" + (f"/{q.denominator}" if q.denominator != 1 else "")
    raise ValueError(x2)


def verdict(r: dict) -> str:
    d = r["dims"]
    if not r["text_states_regular_right_prism"] or r["k"] not in (3, 6) or r["program"] != "regular" or "base" not in d:
        return "refused"
    h2s = {sq(d[x]) for x in ("height", "lateral") if x in d}
    if len(h2s) != 1:
        return "refused"
    b2, h2 = sq(d["base"]), h2s.pop()
    return "served:" + fmt((F(27, 4) if r["k"] == 6 else F(3, 16)) * b2 * b2 * h2)


def main() -> int:
    bad = [(k, r["expect"], verdict(r)) for k, r in ROWS.items() if verdict(r) != r["expect"]]
    for b in bad:
        print("DISAGREE", *b)
    print("oracle:", "OK" if not bad else f"{len(bad)} disagreement(s)", f"({len(ROWS)} rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
