# -*- coding: utf-8 -*-
"""Authored /4 responses for the B3 distance browser check (run `b3-distance-browser-e2e`). 0 model calls.

Every response is produced by the real offline wrapper (`run_typed_fact_next_v2_route` → `build_adapter4_response`)
from the authored `typed-fact-next/2` payloads of `test_typed_fact_next_v2_distance_bridge.py`. `oracle_sq` is the
closed-form squared answer from the stated facts (see that test's docstring), never read from the engine.
Authored development cases: not a holdout, not an extraction-quality measurement.

    cd backend && python ../docs/evaluation/geometry/runs/b3-distance-browser-e2e/build_fixtures.py <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism  # noqa: E402


def _without(p, pred):
    gone = [x for x in p["premises"] if pred(x)]
    p["premises"] = [x for x in p["premises"] if not pred(x)]
    for x in gone:
        p["problem_text"] = p["problem_text"].replace(x["quote"], "")
    return p


CASES = [
    ("B3-D1-point-plane-right", "SERVE", _prism(), F(144)),
    ("B3-D2-skew-lines", "SERVE", _prism(ask=("Tính khoảng cách giữa hai đường thẳng AA' và BC.",
                                             {"line1": ["A", "A'"], "line2": ["B", "C"]})), F(36 * 64, 100)),
    ("B3-D3-point-plane-oblique", "SERVE", _prism("DEF", 12, 16, 24, oblique=True), F(576)),
    ("B3-R1-malformed-target", "REFUSE", _prism(ask=("Tính khoảng cách từ A' đến mặt phẳng (ABC).",
                                                    {"point": "A'", "plane": ["A", "B"]})), None),
    ("B3-R2-missing-height", "REFUSE",
     _without(_prism(), lambda x: x["kind"] == "segment_length" and x["args"]["segment"] == ["A", "A'"]), None),
]


def main() -> int:
    rows = []
    for cid, expected, payload, oracle_sq in CASES:
        r = run_typed_fact_next_v2_route(payload)
        resp = build_adapter4_response(r, payload["problem_text"])
        assert (resp["route_d"]["status"] == "SERVED") == (expected == "SERVE"), (cid, resp["route_d"]["status"])
        rows.append({"id": cid, "expected": expected, "problem_text": payload["problem_text"],
                     "input_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                     "oracle_value_squared": None if oracle_sq is None else str(oracle_sq),
                     "schema_version": resp["schema_version"], "route_d": resp["route_d"], "envelope": resp["envelope"]})
        print(cid, resp["route_d"]["status"], resp["route_d"].get("answers"), (resp["route_d"].get("refusal") or {}).get("code"))
    Path(sys.argv[1]).write_text(json.dumps({"schema": "b3-distance-browser-fixtures/1", "provider_calls": 0,
                                             "classification": "OFFLINE_AUTHORED_TYPEDFACTS_NOT_HOLDOUT",
                                             "fixtures": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
