# -*- coding: utf-8 -*-
"""Stated-vs-derived / provenance probe of run `hybrid-v2-nl-certificates-e2e` (P2). An ad hoc audit, NOT a test and NOT a
dataset: unfaithful extractions of one pyramid problem, each of which must be refused. DEV_AUTHORED by the implementing agent.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/hybrid-v2-nl-certificates-e2e/audit/provenance_probe.py
"""
from __future__ import annotations

import copy
import json
import sys

sys.path.insert(0, ".")
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402

SOLID, BASE, PERP, LEN, GOAL = ("Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 4.", "SA vuông góc với mặt phẳng (ABCD).",
                                "SA = 3.", "Tính khoảng cách từ S đến BD.")
BASE_PAYLOAD = {
    "schema_version": "typed-fact-next/2", "problem_text": " ".join((SOLID, BASE, PERP, LEN, GOAL)), "length_unit": "1",
    "solids": [{"solid_id": "py", "solid_type": "pyramid", "notation": "S.ABCD", "quote": SOLID}],
    "premises": [{"kind": "base_is_square", "args": {"vertices": list("ABCD"), "side": "4"}, "quote": BASE},
                 {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")}, "quote": PERP},
                 {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "quote": LEN}],
    "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "py", "quote": SOLID}],
    "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "distance",
                    "target": {"point": "S", "line": ["B", "D"]}, "quote": GOAL}]}

CASES = [
    # a CONSEQUENCE of a stated relation presented as a stated one (kinds the V2 contract does not carry as premises)
    ("derived SA ⊥ BD quoted from 'SA ⊥ (ABCD)'", lambda p: p["premises"].append(
        {"kind": "perpendicular_lines", "args": {"lines": [["S", "A"], ["B", "D"]]}, "quote": PERP})),
    ("derived SB = SD quoted from the side sentence", lambda p: p["premises"].append(
        {"kind": "equal_lengths", "args": {"segments": [["S", "B"], ["S", "D"]]}, "quote": BASE})),
    # a stated kind whose quote does not state it
    ("height 3 quoted from the side sentence", lambda p: p["premises"][2].update(quote=BASE)),
    ("invented quote", lambda p: p["premises"][2].update(quote="SA = 3 theo giả thiết.")),
    ("height value taken from the question sentence", lambda p: p["premises"][2].update(quote=GOAL)),
    ("perpendicularity quoted from the length sentence", lambda p: p["premises"][1].update(quote=LEN)),
]


def main() -> int:
    ok = run_typed_fact_next_v2_route(copy.deepcopy(BASE_PAYLOAD))
    rows = [{"case": "faithful extraction (control)", "status": ok.status, "code": ok.code, "answers": ok.answers}]
    for label, mutate in CASES:
        p = copy.deepcopy(BASE_PAYLOAD)
        mutate(p)
        r = run_typed_fact_next_v2_route(p)
        rows.append({"case": label, "status": r.status, "code": r.code, "answers": r.answers if r.status == "SERVED" else None})
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    bad = [r for r in rows[1:] if r["status"] == "SERVED"]
    print("SERVED_UNEXPECTED" if bad or ok.status != "SERVED" else "CONTROL_SERVED_ALL_UNFAITHFUL_REFUSED", len(rows))
    return 1 if bad or ok.status != "SERVED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
