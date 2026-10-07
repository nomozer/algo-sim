# -*- coding: utf-8 -*-
"""Independent oracle for exact-dimensions labels: every served value from the TEXT sizes only.

No product import. Sizes are typed here from the problem text (b = base edge, h = height, l = lateral edge,
a = tetrahedron edge); values are compared on their SQUARES as exact fractions, so `12√3` is checked as 432.

Formulas (textbook): base area (√3/4)·b²; V = base·h/3 ⇒ V² = b⁴h²/48; l² = b²/3 + h²;
regular tetrahedron V = a³√2/12 ⇒ V² = a⁶/72, height² = 2a²/3.

Run: python oracle.py  (exit 1 on any disagreement).
"""
from __future__ import annotations

import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sq(v: str) -> F:
    """'12√3' / '5√3/16' / '9/2' / '2√7' → the value squared, exactly."""
    m = re.fullmatch(r"(\d+)?√(\d+)(?:/(\d+))?", v)
    if m:
        k, n, d = F(m.group(1) or 1), F(m.group(2)), F(m.group(3) or 1)
        return k * k * n / (d * d)
    return F(v) ** 2


def pyramid_v2(b: F, h: F) -> F:
    return b ** 4 * h * h / 48


SIZES = {  # row → (kind, sizes) typed from the text
    "P01_base_height": ("V", pyramid_v2(F(6), F(4))),
    "P02_approx_chart": ("V", pyramid_v2(F(6), F(4))),
    "P03_unit_chart": ("V", pyramid_v2(F(6), F(4))),
    "P04_fractions": ("V", pyramid_v2(F(3, 2), F(5, 3))),
    "P05_decimal_comma": ("V", pyramid_v2(F(5, 2), F(6))),
    "P06_tetrahedron": ("V", F(6) ** 6 / 72),
    "P07_tetrahedron_fraction": ("V", F(5, 2) ** 6 / 72),
    "P08_tetrahedron_height": ("h", 2 * F(6) ** 2 / 3),
    "P09_base_lateral": ("V", F(6) ** 4 * (F(25) - F(36) / 3) / 48),
    "P10_all_edges": ("V", F(4) ** 6 / 72),
    "P11_renamed": ("V", pyramid_v2(F(6), F(4))),
    "P12_phrasing": ("V", pyramid_v2(F(6), F(4))),
    "P13_named_centroid": ("V", pyramid_v2(F(6), F(4))),
    "P14_lateral_length": ("l", F(36) / 3 + 16),
    "P15_old_radical_N1": ("V", F(18) ** 2 * 3 / 48),
    "P16_old_radical_axis": ("V", F(18) ** 2 * 3 / 48),
    "P17_radical_base_rational_height": ("V", F(12) ** 2 * 4 / 48),
    "P18_apex_drawn_over_vertex": ("V", pyramid_v2(F(6), F(4))),
}


def main() -> int:
    rows = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))["rows"]
    served = {k: r["expect"].split(":", 1)[1] for k, r in rows.items() if r["expect"].startswith("served:")}
    bad = [k for k in served if k not in SIZES] + [k for k in SIZES if k not in served]
    ok = 0
    for k, v in served.items():
        if k in SIZES and sq(v) == SIZES[k][1]:
            ok += 1
        elif k in SIZES:
            bad.append(f"{k}: label {v} (²={sq(v)}) vs oracle ²={SIZES[k][1]}")
    print(f"oracle exact-dimensions: {ok}/{len(served)} agree")
    for b in bad:
        print("DISAGREE", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
