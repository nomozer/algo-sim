# -*- coding: utf-8 -*-
"""Independent oracle for regular-hexagonal-pyramid. No product import.

Regular hexagonal pyramid, base side b, height h: circumradius = b, so lateral² = h² + b²; base area = (3√3/2)·b²;
V = (1/3)·(3√3/2)·b²·h = (√3/2)·b²·h, V² = (3/4)·b⁴·h². A text is servable iff it says 'đều' (the regularity premise),
fixes b, and fixes h² > 0 by one or more consistent sources (height, lateral). The program must be a regular hexagon
with the apex above its centre (rows with a defective program must be refused). Run: python oracle.py.
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
    """value² → q√n as the product prints it."""
    for n in (1, 3, 13):
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
    if not r["text_claims_regular"] or r["program"] != "regular" or "base" not in d:
        return "refused"
    b2 = sq(d["base"])
    h2s = ([sq(d["height"])] if "height" in d else []) + ([sq(d["lateral"]) - b2] if "lateral" in d else [])
    if not h2s or len(set(h2s)) > 1 or h2s[0] <= 0:
        return "refused"
    h2 = h2s[0]
    return "served:" + fmt(F(3, 4) * b2 * b2 * h2 if r["ask"] == "volume" else h2 + b2)


def main() -> int:
    bad = [(k, r["expect"], verdict(r)) for k, r in ROWS.items() if verdict(r) != r["expect"]]
    for b in bad:
        print("DISAGREE", *b)
    print("oracle:", "OK" if not bad else f"{len(bad)} disagreement(s)", f"({len(ROWS)} rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
