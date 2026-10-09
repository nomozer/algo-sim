# -*- coding: utf-8 -*-
"""Independent oracle for c0-whole-solid-grounding. No product import.

For every row: does each whole-solid claim of the TEXT hold on the given coordinates (own vector code, exact
fractions)? Served rows: the volume from textbook formulas (prism S·h, pyramid S·h/3, regular tetrahedron a³√2/12 via
its square). A row labelled `refused` must break at least one claim; a `served` row must break none and match V.
Run: python oracle.py  (exit 1 on any disagreement).
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


def claims_hold(r: dict, P: dict) -> bool:
    s, text = r["solid"], r["text"]
    day = [P[x] for x in s["base"]]
    nrm = cross(sub(day[1], day[0]), sub(day[2], day[0]))
    if s["kind"] == "prism":
        tren = [P[x] for x in s["top"]]
        v = sub(tren[0], day[0])
        tinh_tien = all(sub(t, d) == v for d, t in zip(day, tren))
        dung = tinh_tien and cross(v, nrm) == (0, 0, 0)
        if "lăng trụ đứng" in text.split("Chứng minh")[0] and "không phải" not in text and not dung:
            return False
        if "lăng trụ xiên" in text and dung:
            return False
        if ("hình hộp chữ nhật" in text or "lập phương" in text):
            a, b, c, d = day
            cn = sub(b, a) == sub(c, d) and dot(sub(b, a), sub(d, a)) == 0
            if not (dung and cn):
                return False
            if "lập phương" in text and not (n2(sub(b, a)) == n2(sub(d, a)) == n2(v)):
                return False
            if "cạnh bằng 3" in text and n2(sub(b, a)) != 9:
                return False
        if "lăng trụ ABC.A'B'C' với" in text and not tinh_tien:
            return False
        if "chiều cao bằng 6" in text and dot(v, nrm) ** 2 != 36 * n2(nrm):
            return False
        return True
    S = P[s["apex"]]
    if "tứ diện đều" in text:
        pts = [S, *day]
        return len({n2(sub(p, q)) for i, p in enumerate(pts) for q in pts[i + 1:]}) == 1
    k = len(day)
    tam = tuple(sum(p[i] for p in day) / k for i in range(3))
    if "đều" in text and cross(sub(S, tam), nrm) != (0, 0, 0):
        return False
    if "cạnh bên bằng 5" in text and n2(sub(S, day[0])) != 25:
        return False
    if "trung đoạn bằng 5" in text and n2(sub(S, tuple((a + b) / 2 for a, b in zip(day[0], day[1])))) != 25:
        return False
    if "O là tâm" in text and "O" in P and tuple(P["O"]) != tam:
        return False
    if "chiều cao bằng 4" in text and dot(sub(S, day[0]), nrm) ** 2 != 16 * n2(nrm):
        return False
    return True


def volume(r: dict, P: dict) -> F:
    s = r["solid"]
    day = [P[x] for x in s["base"]]
    nrm = cross(sub(day[1], day[0]), sub(day[2], day[0]))
    area2 = n2(cross(sub(day[1], day[0]), sub(day[2], day[0]))) if len(day) == 3 else None
    if len(day) == 4:                                  # parallelogram-like bases here: |AB × AD|
        area = abs(F(cross(sub(day[1], day[0]), sub(day[3], day[0]))[2])) if nrm[0] == nrm[1] == 0 else None
    if s["kind"] == "prism":
        h = sub(P[s["top"][0]], day[0])[2]
        base = F(abs(cross(sub(day[1], day[0]), sub(day[2], day[0]))[2]), 2) if len(day) == 3 else area
        return base * h
    S = P[s["apex"]]
    if len(day) == 3 and nrm[0] != 0:                  # tilted base: V = |det| / 6
        return abs(F(dot(sub(S, day[0]), nrm), 6))
    base = F(abs(nrm[2]), 2) if len(day) == 3 else area
    return base * S[2] / 3


def main() -> int:
    bad = 0
    for rid, r in ROWS.items():
        P = {k: tuple(F(str(c)) for c in v) for k, v in r["points"].items()}
        ok = claims_hold(r, P)
        if r["expect"] == "refused" and ok:
            print("DISAGREE", rid, "refused but every claim holds"); bad += 1
        if r["expect"].startswith("served:"):
            if not ok:
                print("DISAGREE", rid, "served but a claim breaks"); bad += 1
            elif volume(r, P) != F(r["expect"].split(":", 1)[1]):
                print("DISAGREE", rid, "volume", volume(r, P)); bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)", f"({len(ROWS)} rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
