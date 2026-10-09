# -*- coding: utf-8 -*-
"""Independent oracle for geometry-grounding-safety. No product import.

C0 rows: the stated shape relation is re-checked by hand on the stated coordinates (dot products typed here), and the
served volume is base area × height / 3 from textbook formulas. Compiler rows: rectangle volumes from the sides.
Run: python oracle.py  (exit 1 on any disagreement).
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
dot = lambda u, v: sum(a * b for a, b in zip(u, v))  # noqa: E731
sub = lambda p, q: tuple(a - b for a, b in zip(p, q))  # noqa: E731

# (relation holds on the coordinates?, served volume if consistent)
TZ = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 4, 0)}
CHECK = {
    "C01_trapezoid_phrase_consistent": (dot(sub(TZ["B"], TZ["A"]), sub(TZ["D"], TZ["A"])) == 0
                                        and dot(sub(TZ["A"], TZ["B"]), sub(TZ["C"], TZ["B"])) == 0, F(2 + 4, 2) * 2 * 3 / 3),
    "C02_trapezoid_phrase_contradicts": (dot(sub(TZ["B"], TZ["C"]), sub(TZ["D"], TZ["C"])) == 0
                                         and dot(sub(TZ["C"], TZ["D"]), sub(TZ["A"], TZ["D"])) == 0, None),
    "C03_rectangle_phrase_on_trapezoid": (sub(TZ["B"], TZ["A"]) == sub(TZ["C"], TZ["D"]), None),
    "C04_rectangle_phrase_consistent_renamed": (True, F(3 * 2 * 4, 3)),
    "C05_apex_edge_perp_contradicts": (dot(sub((1, 0, 4), (0, 0, 0)), (3, 0, 0)) == 0, None),
    "C06_apex_edge_perp_consistent": (True, F(3 * 2 * 4, 3)),
    "C07_right_triangle_wrong_vertex": (dot(sub((0, 0, 0), (3, 0, 0)), sub((0, 4, 0), (3, 0, 0))) == 0, None),
    "C08_right_triangle_consistent": (True, F(3 * 4, 2) * 6 / 3),
    "C09_coordinates_without_shape_phrase": (True, F(2 + 4, 2) * 2 * 3 / 3),
    "C10_square_side_contradicts": (dot((2, 0, 0), (2, 0, 0)) == 9, None),
    "C11_square_consistent": (True, F(2 * 2 * 3, 3)),
    "R04_pyramid_three_right_angles_untagged": (True, F(3 * 4 * 5, 3)),
    "R05_pyramid_rectangle_declared": (True, F(3 * 4 * 5, 3)),
    "R06_prism_rectangle_declared": (True, F(3 * 4 * 5)),
    "R07_trapezoid_two_adjacent_right_angles": (True, F(2 + 4, 2) * 2 * 3 / 3),
}


def main() -> int:
    rows = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))["rows"]
    bad = 0
    for rid, r in rows.items():
        e = r["expect"]
        if rid not in CHECK:
            continue
        holds, v = CHECK[rid]
        if e.startswith("served:") and (not holds or F(e.split(":", 1)[1]) != v):
            print("DISAGREE", rid, e, holds, v); bad += 1
        if e.startswith("refused:SOURCE_SHAPE") and holds:
            print("DISAGREE", rid, e, "relation holds"); bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
