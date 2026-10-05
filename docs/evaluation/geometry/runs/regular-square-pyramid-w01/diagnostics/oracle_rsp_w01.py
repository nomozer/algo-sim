# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — independent oracle for the corpus labels (0 model calls, no product import).

Reads every row of corpus/LABELS.json, extracts the stated data with its own patterns (not the product's reader),
and derives, by the formulas written in LABELS.json `derivations`, either the exact answer or the reason the
answer is not determined by the text. Served rows must match their label exactly; refused rows must have a
mathematical or registered-scope reason. Exit 1 on any disagreement. Usage (repository root):
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/oracle_rsp_w01.py
"""
from __future__ import annotations

import json
import re
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

LABELS = Path(__file__).resolve().parent / "corpus" / "LABELS.json"
SO = r"(\d+(?:[.,]\d+)?)"


def num(t: str) -> F:
    return F(t.replace(",", "."))


def grab(text: str, pattern: str) -> F | None:
    m = re.search(pattern, text)
    return num(m.group(1)) if m else None


def sqrt_exact(q: F) -> F | None:
    """√q in ℚ, or None."""
    if q < 0:
        return None
    a, b = isqrt(q.numerator), isqrt(q.denominator)
    return F(a, b) if a * a == q.numerator and b * b == q.denominator else None


def radical(q: F) -> str:
    """Exact text of √q for an integer q (enough for this corpus)."""
    r = sqrt_exact(q)
    if r is not None:
        return str(r)
    n = int(q)
    out, inner = 1, n
    for k in range(2, isqrt(n) + 1):
        while inner % (k * k) == 0:
            out, inner = out * k, inner // (k * k)
    return f"{'' if out == 1 else out}√{inner}"


def derive(text: str) -> tuple[str, str]:
    """→ (outcome, reason): outcome `served:<v>` or `refused`."""
    premises = re.split(r"(?i)chứng\s+minh", text)[0]          # a 'Chứng minh …' clause is a goal
    regular = bool(re.search(r"chóp tứ giác đều", premises))
    if re.search(r"chóp tam giác đều", premises):
        return "refused", "regular triangular pyramid: equilateral base needs √3 (outside W1)"
    s = grab(premises, rf"cạnh đáy bằng {SO}") or grab(premises, rf"hình vuông cạnh {SO}") \
        or grab(premises, rf"AB = {SO}")
    h_given = grab(premises, rf"chiều cao bằng {SO}") or grab(premises, rf"SO = {SO}")
    m = grab(premises, rf"(?:trung đoạn|đường cao của mặt bên) bằng {SO}")
    l = grab(premises, rf"cạnh bên bằng {SO}")
    if re.search(r"góc", premises):
        return "refused", "angle data: not grounded, and h = 2√6 would be irrational"
    if not regular:
        return "refused", "apex foot not determined by the premises (no 'đều')"
    if s is None:
        return "refused", "base side not stated"
    cands = []
    if h_given is not None:
        cands.append(("height", h_given * h_given))
    if m is not None:
        cands.append(("apothem", m * m - (s / 2) ** 2))
    if l is not None:
        cands.append(("lateral edge", l * l - s * s / 2))
    if not cands:
        return "refused", "height not determined (no height, apothem or lateral edge)"
    if len({c[1] for c in cands}) > 1:
        return "refused", "contradiction: " + ", ".join(f"{k}⇒h²={v}" for k, v in cands)
    h2 = cands[0][1]
    if h2 <= 0:
        return "refused", f"degenerate: h² = {h2}"
    h = sqrt_exact(h2)
    if h is None:
        return "refused", f"h² = {h2} is not a rational square: no rational coordinates"
    if "độ dài" in text and ("SA" in text.split("Tính")[-1] or "cạnh bên" in text.split("Tính")[-1]):
        return f"served:{radical(h2 + s * s / 2)}", f"SA² = h² + s²/2 = {h2 + s * s / 2}"
    return f"served:{s * s * h / 3}", f"V = s²h/3 with s={s}, h={h}"


def main() -> int:
    rows = json.loads(LABELS.read_text(encoding="utf-8"))["rows"]
    bad = 0
    for rid, row in rows.items():
        got, why = derive(row["text"])
        want = row["expect"]
        if row.get("program_fault"):
            # the text is determined; the product must refuse the faulty PROGRAM
            ok = got.startswith("served:") and want.startswith("refused:")
            why = f"text determined ({got}); program fault ⇒ refuse"
        else:
            ok = got == want if want.startswith("served:") else got == "refused"
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {rid}: label {want} | oracle {got} ({why})")
    print(f"ORACLE {'AGREES' if bad == 0 else 'DISAGREES'}: {len(rows) - bad}/{len(rows)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
