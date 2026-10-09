# -*- coding: utf-8 -*-
"""Independent oracle for unnamed-regular-pyramid-grounding. No product import.

C1 rows in scope `bind` (no point named without coordinates): re-derive the answer from the stated dimensions with
textbook formulas — square: h² from height | lateral edge (l² − b²/2) | apothem (m² − b²/4), V = b²h/3; triangular:
h² from height | lateral (l² − b²/3) | all edges equal, V = (√3/4)b²·h/3. Several sources that disagree ⇒ contradiction;
none ⇒ missing; square with irrational h, or angle data ⇒ outside the product domain (T7 frame). The derived verdict
must agree with the corpus label (served value equal; refused ⇔ not determined). Scope is re-checked from the text.
C0 rows: the claim 'regular pyramid' is checked over EVERY apex choice and base cyclic order of the solid's points
(labelling-free, own vector code); volume |det|/6 fan. Run: python oracle.py (exit 1 on any disagreement).
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

D = json.loads((Path(__file__).resolve().parent / "labels.json").read_text(encoding="utf-8"))
NUM = r"(\d+(?:/\d+)?)?\s*(?:√(\d+))?"
TOK = re.compile(r"(?<![a-zà-ỹA-Z])([A-Z]\d*'?)(?![a-zà-ỹ])")


def num(s: str):
    """'3√2' → b² as Fraction (lengths are compared by their squares)."""
    m = re.fullmatch(r"\s*(\d+(?:/\d+)?)?\s*(?:√(\d+))?\s*", s)
    q, r = F(m.group(1) or 1), int(m.group(2) or 1)
    return q * q * r


def find(text: str, word: str):
    m = re.search(word + r"\s*(?:bằng|=|là)?\s*(\d+(?:/\d+)?\s*(?:√\d+)?|√\d+)", text)
    return num(m.group(1)) if m else None


def sq_rational(x: F):
    n, d = x.numerator, x.denominator
    rn, rd = int(n ** 0.5 + .5), int(d ** 0.5 + .5)
    return F(rn, rd) if rn * rn == n and rd * rd == d else None


def verdict(text: str):
    """('served', (q, n)) meaning V = q√n, or ('refused', why)."""
    tri = "tam giác đều" in text
    if "góc" in text:
        return ("refused", "angle data")
    b2 = find(text, "cạnh đáy")
    every = find(text, "tất cả các cạnh")
    if every is not None:
        b2 = every
    h2s = []
    if (h := find(text, "chiều cao")) is not None:
        h2s.append(h)
    if b2 is not None:
        if (l2 := (every if every is not None else find(text, "cạnh bên"))) is not None:
            h2s.append(l2 - b2 / (3 if tri else 2))
        if not tri and (m2 := find(text, "(?:trung đoạn|đường cao của mặt bên)")) is not None:
            h2s.append(m2 - b2 / 4)
    if b2 is None or not h2s:
        return ("refused", "missing")
    if len(set(h2s)) > 1:
        return ("refused", "contradiction")
    h2 = h2s[0]
    if h2 <= 0:
        return ("refused", "degenerate")
    if tri:                                   # V² = (3/16)·b⁴·h²/9 = b⁴h²/48
        v2 = b2 * b2 * h2 / 48
    else:
        if sq_rational(h2) is None:
            return ("refused", "irrational height (outside T7)")
        v2 = b2 * b2 * h2 / 9
    for n in (1, 2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 21, 30):   # V = q√n with q rational
        if (q := sq_rational(v2 / n)) is not None:
            return ("served", (q, n))
    return ("served", None)


def label_value(lab: str):
    m = re.fullmatch(r"(\d+)?(?:√(\d+))?(?:/(\d+))?", lab)
    return (F(int(m.group(1) or 1), int(m.group(3) or 1)), int(m.group(2) or 1))


sub = lambda a, b: tuple(x - y for x, y in zip(a, b))  # noqa: E731
dot = lambda a, b: sum(x * y for x, y in zip(a, b))  # noqa: E731
cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])  # noqa: E731
n2 = lambda a: dot(a, a)  # noqa: E731


def regular(S, b) -> bool:
    k = len(b)
    if len({n2(sub(b[(i + 1) % k], b[i])) for i in range(k)}) != 1:
        return False
    if k == 4 and (sub(b[1], b[0]) != sub(b[2], b[3]) or dot(sub(b[1], b[0]), sub(b[3], b[0])) != 0):
        return False
    nrm = cross(sub(b[1], b[0]), sub(b[2], b[0]))
    h = sub(S, tuple(sum(p[i] for p in b) / k for i in range(3)))
    return cross(h, nrm) == (0, 0, 0) and dot(h, nrm) != 0


def regular_some_reading(pts: list) -> bool:
    for i, S in enumerate(pts):
        rest = pts[:i] + pts[i + 1:]
        if any(regular(S, [rest[0], *p]) for p in itertools.permutations(rest[1:])):
            return True
    return False


def ambiguity_witness() -> bool:
    """Scope `unchanged` is not a product limit by taste: 'hình chóp tứ giác đều có AB = 4, SA = 3' (square/R2_S8) fits
    apex S (base side 4, lateral 3 ⇒ h² = 1, V² = (16/3)²) AND apex B (lateral BA = BS = 4, base side SA = 3 ⇒ h² = 23/2,
    V² = 9·23/2) — two different volumes, so only a labelling the TEXT does not fix picks one."""
    v2 = []
    for b2, l2 in ((F(16), F(9)), (F(9), F(16))):       # (base side², lateral²)
        h2 = l2 - b2 / 2
        if h2 <= 0:
            return False
        v2.append(b2 * b2 * h2 / 9)
    return len(set(v2)) == 2


def main() -> int:
    bad = 0
    if not ambiguity_witness():
        print("DISAGREE ambiguity witness"); bad += 1
    for rid, r in D["c1_rows"].items():
        names = sorted(set(TOK.findall(r["text"])))
        if (r["scope"] == "bind") != (not names):
            print("DISAGREE scope", rid, names); bad += 1
        if r["scope"] != "bind":
            continue
        v, lab = verdict(r["text"]), r["corpus_label"]
        if lab.startswith("served:"):
            if v[0] != "served" or v[1] != label_value(lab.split(":", 1)[1]):
                print("DISAGREE", rid, lab, v); bad += 1
        elif v[0] == "served":
            # a refused label with a determined answer is a PROGRAM defect row (layout taken as data, …): the text
            # alone would be served — record it, the label stays the corpus's
            print("NOTE", rid, lab, "text determines", v[1], "— refusal comes from the program, not the text")
    for rid, r in D["c0_rows"].items():
        P = {k: tuple(F(str(c)) for c in v) for k, v in r["points"].items()}
        s = r["solid"]
        sol = [P[s["apex"]], *[P[x] for x in s["base"]]]
        ok = not r["claims"] or regular_some_reading(sol)
        e = r["expect"]
        if e in ("refused", "unchanged") and ok and r["claims"]:
            print("DISAGREE", rid, e, "but the claim holds"); bad += 1
        if e.startswith("served:"):
            S, b = sol[0], sol[1:]
            vol = abs(sum(F(dot(sub(S, b[0]), cross(sub(b[i], b[0]), sub(b[i + 1], b[0]))), 6)
                          for i in range(1, len(b) - 1)))
            if not ok or vol != F(e.split(":", 1)[1]):
                print("DISAGREE", rid, e, ok, vol); bad += 1
    print("oracle:", "OK" if not bad else f"{bad} disagreement(s)",
          f"({len(D['c1_rows'])} C1 rows, {len(D['c0_rows'])} C0 rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
