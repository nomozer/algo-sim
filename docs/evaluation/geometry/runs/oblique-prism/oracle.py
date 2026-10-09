# -*- coding: utf-8 -*-
"""Independent oracle for oblique-prism labels: every served volume from the TEXT sizes only.

No product import. Prism volume = base area × height (Cavalieri; the textbook formula — independent of the
product's signed-tetrahedron volume). Height h is the length of the segment the text states perpendicular to the base
(T F), or, when only a lateral edge l is given, h² = l² − d² where d = distance in the base between F and the base
vertex B0 joined to T by that lateral edge (typed here by hand from the base shape).

Run: python oracle.py  (exit 1 on any disagreement).
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent


def h_from_lateral(l: F, d2: F) -> F:
    h2 = l * l - d2
    n, m = h2.numerator, h2.denominator
    r = F(int(n ** 0.5 + 0.5), int(m ** 0.5 + 0.5))
    assert r * r == h2, "label row must have a rational height"
    return r


VOLUME = {  # row → base area × height, sizes typed from the text
    "OP01_triangle_foot_vertex_height": F(3) * F(4) / 2 * F(6),
    "OP02_no_word_oblique_height_from_lateral": F(3) * F(4) / 2 * h_from_lateral(F(5), F(3) ** 2),   # B0=A, F=B
    "OP03_renamed_right_angle_off_foot": F(2) * F(5) / 2 * F(3),
    "OP04_fractions_foot_other_vertex": F(3, 2) * F(2) / 2 * F(7, 3),
    "OP05_rectangle_foot_diagonal_from_lateral": F(4) * F(3) * h_from_lateral(F(13), F(4) ** 2 + F(3) ** 2),  # B0=A, F=C
    "OP06_square_renamed_top": F(2) * F(2) * F(3, 2),
    "ON10_wrong_llm_layout": F(3) * F(4) / 2 * F(6),
}


def main() -> int:
    rows = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))["rows"]
    bad = 0
    for rid, r in rows.items():
        for route, e in r["expect"].items():
            if not e.startswith("served:"):
                continue
            if F(e.split(":", 1)[1]) != VOLUME[rid]:
                print(f"DISAGREE {rid} {route}: label {e}, oracle {VOLUME[rid]}")
                bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
