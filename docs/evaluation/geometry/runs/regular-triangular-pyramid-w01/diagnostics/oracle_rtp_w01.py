# -*- coding: utf-8 -*-
"""Oracle ĐỘC LẬP cho nhãn regular-triangular-pyramid-w01 — chỉ dữ kiện đề (chép tay dưới đây), số học `Fraction`
trên BÌNH PHƯƠNG, không import mã sản phẩm. Chạy: `python oracle_rtp_w01.py` (thoát 1 khi một nhãn lệch).

Công thức (LABELS.json `derivations`): V² = b⁴h²/48; h² = l² − b²/3; tứ diện đều h² = 2b²/3; l² = h² + b²/3.
Miền §18.2: b² ∈ {2k², 6k²}, h² = 3t² với k, t hữu tỉ.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

NHAN = json.loads((Path(__file__).parent / "corpus" / "LABELS.json").read_text(encoding="utf-8"))["rows"]

#: Dữ kiện chép tay từ `text` (bình phương): b2 cạnh đáy², h2 chiều cao², l2 cạnh bên², tu_dien (mọi cạnh = b),
#: hoi ∈ {volume, lateral}.
DU_KIEN = {
    "P1_side_height": dict(b2=F(18), h2=F(3)),
    "P2_side_lateral": dict(b2=F(18), l2=F(9)),
    "P3_tetrahedron": dict(b2=F(18), tu_dien=True),
    "P4_all_edges_equal": dict(b2=F(18), tu_dien=True),
    "P5_equal_chains": dict(b2=F(18), l2=F(9)),
    "P6_base_equilateral_phrase": dict(b2=F(18), l2=F(9)),
    "P7_renamed_vertices": dict(b2=F(18), h2=F(3)),
    "P8_phrasing_variant": dict(b2=F(18), h2=F(3)),
    "P9_named_centroid": dict(b2=F(18), h2=F(3)),
    "P10_frame_six": dict(b2=F(24), h2=F(3)),
    "P11_lateral_length": dict(b2=F(18), h2=F(3), hoi="lateral"),
    "U1_rational_side": dict(b2=F(9), h2=F(4)),
    "U2_rational_tetrahedron": dict(b2=F(9), tu_dien=True),
    "U3_height_outside_domain": dict(b2=F(18), h2=F(4)),
    "U4_side_outside_frames": dict(b2=F(14), h2=F(3)),
}


def can(q: F) -> F | None:
    a, b = isqrt(q.numerator), isqrt(q.denominator)
    return F(a, b) if q >= 0 and a * a == q.numerator and b * b == q.denominator else None


def viet(q: F) -> str:
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def giai(d: dict) -> tuple[F, F, F]:
    b2 = d["b2"]
    h2 = d.get("h2") or (2 * b2 / 3 if d.get("tu_dien") else d["l2"] - b2 / 3)
    return b2, h2, h2 + b2 / 3


def trong_mien(b2: F, h2: F) -> bool:
    return (can(b2 / 2) is not None or can(b2 / 6) is not None) and can(h2 / 3) is not None


def main() -> int:
    lech = []
    for ca, d in DU_KIEN.items():
        b2, h2, l2 = giai(d)
        mong = NHAN[ca]["expect"]
        if ca.startswith("U"):
            if trong_mien(b2, h2) or not mong.startswith("refused:"):
                lech.append((ca, "U-row must be outside the domain and refused", mong))
            continue
        if not trong_mien(b2, h2):
            lech.append((ca, "positive row outside the domain", mong))
            continue
        gia = can(l2) if d.get("hoi") == "lateral" else can(b2 * b2 * h2 / 48)
        if gia is None or mong != f"served:{viet(gia)}":
            lech.append((ca, f"oracle {gia}", mong))
    for x in lech:
        print("MISMATCH", *x)
    print(f"oracle_rtp_w01: {len(DU_KIEN) - len(lech)}/{len(DU_KIEN)} rows agree")
    return 1 if lech else 0


if __name__ == "__main__":
    sys.exit(main())
