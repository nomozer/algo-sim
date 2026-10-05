# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — independent oracle for corpus layer R2 (0 model calls, no product import).

Layer 1 (corpus/LABELS.json, oracle_rsp_w01.py) is unchanged. R2 rows state the lateral edge by a segment name
("SA = 3", "cạnh bên SA = 3", "SA = SB = SC = SD = 3"). This oracle reads, with its own patterns, the base side
(`AB = s` or "cạnh đáy bằng s") and every apex-to-vertex length `S<X> = l` (a chain `SA = SB = … = l` gives each of
them l), then derives V = s²h/3 with h² = l² − s²/2. Different lateral lengths ⇒ contradiction; h² not a rational
square ⇒ no rational coordinates. A row with `product_limit: true` must be determined by the text AND labelled
refused (the product refuses it for a registered reason). Exit 1 on any disagreement. Usage (repository root):
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/oracle_rsp_w01_r2.py
"""
from __future__ import annotations

import json
import re
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

LABELS = Path(__file__).resolve().parent / "corpus" / "LABELS_R2.json"
SO = r"(\d+(?:[.,]\d+)?)"


def sqrt_exact(q: F) -> F | None:
    if q < 0:
        return None
    a, b = isqrt(q.numerator), isqrt(q.denominator)
    return F(a, b) if a * a == q.numerator and b * b == q.denominator else None


def derive(text: str) -> tuple[str, str]:
    premises = text.split("Tính")[0]
    if not re.search(r"chóp tứ giác đều S\.ABCD", premises):
        return "refused", "not a regular square pyramid S.ABCD"
    m = re.search(rf"(?:cạnh đáy bằng|AB =) {SO}", premises)
    if not m:
        return "refused", "base side not stated"
    s = F(m.group(1).replace(",", "."))
    lateral: dict[str, F] = {}
    for chain in re.finditer(rf"((?:S[A-D]\s*=\s*)+){SO}", premises):
        value = F(chain.group(2).replace(",", "."))
        for name in re.findall(r"S[A-D]", chain.group(1)):
            lateral.setdefault(name, value)
            if lateral[name] != value:
                return "refused", f"contradiction: {name} stated twice"
    if not lateral:
        return "refused", "height not determined (no lateral edge)"
    if len(set(lateral.values())) > 1:
        return "refused", f"contradiction: lateral edges {sorted(set(lateral.values()))} differ"
    l = next(iter(lateral.values()))
    h2 = l * l - s * s / 2
    if h2 <= 0:
        return "refused", f"degenerate: h² = {h2}"
    h = sqrt_exact(h2)
    if h is None:
        return "refused", f"h² = {h2} is not a rational square: no rational coordinates"
    return f"served:{s * s * h / 3}", f"V = s²h/3 with s={s}, h={h} (l={l})"


def main() -> int:
    rows = json.loads(LABELS.read_text(encoding="utf-8"))["rows"]
    bad = 0
    for rid, row in rows.items():
        got, why = derive(row["text"])
        want = row["expect"]
        if row.get("product_limit"):
            ok = got.startswith("served:") and want.startswith("refused:")
            why = f"text determined ({got}); registered product limit ⇒ refused"
        else:
            ok = got == want if want.startswith("served:") else got == "refused"
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {rid}: label {want} | oracle {got} ({why})")
    print(f"ORACLE {'AGREES' if bad == 0 else 'DISAGREES'}: {len(rows) - bad}/{len(rows)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
