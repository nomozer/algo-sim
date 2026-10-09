# -*- coding: utf-8 -*-
"""Independent oracle for general-polygon-base labels: every served volume from the TEXT sizes only.

No product import, no shoelace: base areas by textbook decomposition typed by hand from the problem —
right trapezoid (a + b)/2 · h, right triangle legs/2, the pentagon as a rectangle minus a corner triangle.
Pyramid V = S·h/3, prism V = S·h.

Run: python oracle.py  (exit 1 on any disagreement).
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent


def trapezoid(b1: F, b2: F, h: F) -> F:
    return (b1 + b2) / 2 * h


VOLUME = {
    "P01_trapezoid_pyramid": trapezoid(F(2), F(4), F(2)) * F(3) / 3,                 # BC ∥ AD, leg AB
    "P02_trapezoid_pyramid_renamed_foot_at_second_right_angle": trapezoid(F(4), F(2), F(3)) * F(5) / 3,
    "P03_trapezoid_fractions_longer_far_side": trapezoid(F(1), F(5, 2), F(3, 2)) * F(4) / 3,
    "P04_trapezoid_right_prism": trapezoid(F(2), F(4), F(2)) * F(5),
    "P05_right_triangle_foot_off_right_vertex": F(3) * F(4) / 2 * F(6) / 3,           # legs BA, BC
    # rectangle CD × BC with the corner cut: legs (CD − AB) and (BC − DE)
    "P06_pentagon_three_right_angles": (F(4) * F(3) - (F(4) - F(2)) * (F(3) - F(1)) / 2) * F(2) / 3,
    "P07_trapezoid_right_at_A_and_D": trapezoid(F(4), F(1), F(2)) * F(3) / 3,          # AB ∥ DC, leg AD
    "N07_wrong_llm_layout": trapezoid(F(2), F(4), F(2)) * F(3) / 3,
}


def main() -> int:
    rows = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))["rows"]
    bad = 0
    for rid, r in rows.items():
        for route, e in r["expect"].items():
            if e.startswith("served:") and F(e.split(":", 1)[1]) != VOLUME[rid]:
                print(f"DISAGREE {rid} {route}: label {e}, oracle {VOLUME[rid]}")
                bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
