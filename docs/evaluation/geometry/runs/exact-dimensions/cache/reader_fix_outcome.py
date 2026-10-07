# -*- coding: utf-8 -*-
"""exact-dimensions — does the source-length reader fix (1c8f3cb4) change a SERVED response? 0 model calls.

Run from the backend directory of a tree (before: 1c91f90d, after: this run). A regular square pyramid text whose base
is an expression ("cạnh đáy bằng 4 + 1") with an LLM-style program that lays out base 4 and declares GIVEN 4. The old
reader takes "4" from "4 + 1" and the route can serve V = 16 (true value 25); the new reader leaves the clause unread.
A served → refused change means old cache rows hold a wrong served answer ⇒ bump.

usage (in <tree>/backend): python <this file>
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F

sys.path.insert(0, ".")
from tests.geometry import test_regular_square_pyramid as RSP  # noqa: E402

try:
    from tests.geometry import route_cases as W  # noqa: E402
except ImportError:                                # before the rename (0ed6332f)
    from tests.geometry import w14_cases as W  # noqa: E402

TEXT = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 + 1, chiều cao bằng 3. Tính thể tích khối chóp S.ABCD."
contract, prog = RSP._ca("S1_side_height_volume", s=F(4), h=F(3), van=TEXT, gf=RSP._g(RSP.CANH_DAY_4, RSP.CAO_3))
_sp, out, scene = W.chay(contract, prog)
v = next((o.get("value") for o in (scene or {}).get("objects", []) if o["id"] == RSP.THE_TICH), None)
print(json.dumps({"text": TEXT, "servable": out.servable, "served_value": v if out.servable else None,
                  "stage": out.stage_reached, "reason_code": out.reason_code}, ensure_ascii=False))
