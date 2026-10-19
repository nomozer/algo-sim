"""Execute the W2-EXP rows the current TypedFact schema can express (run `goal-directed-function-composition`).

    python w2_exp_execute.py <out.json>     # 0 model calls; refuses to overwrite

Positive W2-EXP rows in Wave 2A scope are measured by `measure_goal_directed_composition.py` (dev corpus). This script runs
the NEGATIVE / refusal rows of the Gemini report (as corrected in the owner's handoff) through the product route and
records the EXECUTED code next to the code the report EXPECTED — the two are kept apart, never merged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "backend"))

SQ_TEXT = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "


def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


SQ = [f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
      f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"), shape="square", value="2"),
      f("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
      f("f4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3")]


def q(quote, **kw):
    return f("q", "question", quote, role="question", **kw)


ROWS = [
    ("W2-EXP-09A", ["COLLINEAR_POINTS"], SQ_TEXT + "Gọi M là trung điểm của SA. Tính diện tích thiết diện của hình chóp S.ABCD "
     "cắt bởi mặt phẳng (ASM).",
     SQ + [f("m", "point_def", "Gọi M là trung điểm của SA.", point="M", point_kind="midpoint", points=["S", "A"]),
           q("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (ASM).", quantity="area", solid="S.ABCD",
             points=["A", "S", "M"])]),
    ("W2-EXP-09B", ["PLANE_TOUCHES_VERTEX", "PLANE_DOES_NOT_CUT"], SQ_TEXT + "Tính diện tích thiết diện của hình chóp S.ABCD "
     "cắt bởi mặt phẳng qua S song song với (ABCD).",
     SQ + [q("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng qua S song song với (ABCD).",
             quantity="area", solid="S.ABCD", point="S", points_b=list("ABCD"), plane_relation="parallel")]),
    ("W2-EXP-10A-1", ["DEGENERATE_POINTS", "DEGENERATE_LINE"], SQ_TEXT + "Tính góc giữa AA và BC.",
     SQ + [q("Tính góc giữa AA và BC.", quantity="angle", points_a=["A", "A"], points_b=["B", "C"])]),
    ("W2-EXP-10B", ["PARALLEL_NO_INTERSECTION"], SQ_TEXT + "Gọi I là giao điểm của SA và BC. Tính độ dài AI.",
     SQ + [f("i", "point_def", "Gọi I là giao điểm của SA và BC.", point="I", point_kind="intersect_line_line",
             points_a=["S", "A"], points_b=["B", "C"]),
           q("Tính độ dài AI.", quantity="length", points=["A", "I"])]),
    ("W2-EXP-11A", ["INCONSISTENT_FACTS"], "Cho hình chóp S.ABC. AB = 1. BC = 2. AC = 4. SA vuông góc với (ABC). SA = 1. "
     "Tính thể tích khối chóp S.ABC.",
     [f("f1", "solid", "Cho hình chóp S.ABC.", solid="S.ABC", solid_type="pyramid"),
      f("f2", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
      f("f3", "length", "BC = 2.", points=["B", "C"], measure="segment", value="2"),
      f("f4", "length", "AC = 4.", points=["A", "C"], measure="segment", value="4"),
      f("f5", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
      f("f6", "length", "SA = 1.", points=["S", "A"], measure="segment", value="1"),
      q("Tính thể tích khối chóp S.ABC.", quantity="volume", solid="S.ABC")]),
    ("W2-EXP-11B", ["INCONSISTENT_FACTS"], "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2. SA = 1. "
     "Tính thể tích khối chóp S.ABCD.",
     [f("f1", "solid", "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2.", solid="S.ABCD", solid_type="pyramid",
        regular=True),
      f("f2", "polygon_shape", "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2.", points=list("ABCD"),
        shape="square", value="2"),
      f("f3", "length", "SA = 1.", points=["S", "A"], measure="segment", value="1"),
      q("Tính thể tích khối chóp S.ABCD.", quantity="volume", solid="S.ABCD")]),
    ("W2-EXP-11C", ["MISSING_DIMENSION"], "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2. SA vuông góc với (ABC). "
     "Tính thể tích khối chóp S.ABC.",
     [f("f1", "solid", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2.", solid="S.ABC", solid_type="pyramid"),
      f("f2", "polygon_shape", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2.", points=list("ABC"),
        shape="equilateral_triangle", value="2"),
      f("f3", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
      q("Tính thể tích khối chóp S.ABC.", quantity="volume", solid="S.ABC")]),
    ("W2-EXP-12A", ["UNSUPPORTED_CAPABILITY"], SQ_TEXT + "Tính khoảng cách giữa đường thẳng BC và mặt phẳng (SAD).",
     SQ + [q("Tính khoảng cách giữa đường thẳng BC và mặt phẳng (SAD).", quantity="distance", points_a=["B", "C"],
             points_b=["S", "A", "D"])]),
    ("W2-EXP-12B", ["UNSUPPORTED_CAPABILITY"], SQ_TEXT + "Tính khoảng cách giữa SB và (ABCD).",
     SQ + [q("Tính khoảng cách giữa SB và (ABCD).", quantity="distance", points_a=["S", "B"], points_b=list("ABCD"))]),
    ("W2-EXP-13B", ["REQUEST_NOT_ANSWERED"], SQ_TEXT + "Tính độ dài SC và tính khoảng cách từ A đến (SBC).",
     SQ + [q("Tính độ dài SC và tính khoảng cách từ A đến (SBC).", quantity="length", points=["S", "C"])]),
    ("W2-EXP-14B", ["DEPENDENCY_CYCLE"], SQ_TEXT + "Gọi M là trung điểm của NB. Gọi N là trung điểm của MB. Tính độ dài AM.",
     SQ + [f("m", "point_def", "Gọi M là trung điểm của NB.", point="M", point_kind="midpoint", points=["N", "B"]),
           f("n", "point_def", "Gọi N là trung điểm của MB.", point="N", point_kind="midpoint", points=["M", "B"]),
           q("Tính độ dài AM.", quantity="length", points=["A", "M"])]),
]


def main(out: Path) -> int:
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions.certificates import CERTIFICATE_SCHEMA, verify_perpendicular_witness

    rows = []
    for rid, expected, text, facts in ROWS:
        r = run_fact_route(text, {"facts": facts})
        rows.append({"id": rid, "expected_by_report": expected, "executed_status": r.status, "executed_code": r.code,
                     "served_nothing": r.status != "SERVED" and not r.answers and r.scene3d is None,
                     "state": ("EXECUTED_PASS" if r.status == "REFUSED" and r.code in expected else
                               "EXECUTED_REFUSED_OTHER_CODE" if r.status == "REFUSED" else "EXECUTED_FAIL_SERVED"),
                     "reason": (r.reason or "")[:200]})
    # W2-EXP-14A: a forged witness on an oblique lateral edge SB of the served base problem (Wave 1 verifier)
    base = run_fact_route(SQ_TEXT + "Tính độ dài SC.", {"facts": SQ + [q("Tính độ dài SC.", quantity="length",
                                                                         points=["S", "C"])]})
    from copy import deepcopy

    scene = base.scene3d
    seg = {frozenset(o.get("endpoint_ids") or ()): o for o in scene["objects"] if o["type"] == "segment3"}
    sa, sb = seg[frozenset({"S", "A"})], seg[frozenset({"S", "B"})]
    assert sa["perpendicular_witness"]["certificate"] == CERTIFICATE_SCHEMA and "perpendicular_witness" not in sb
    forged = deepcopy(sa["perpendicular_witness"])              # the true altitude certificate, moved to the oblique SB
    ok, why = verify_perpendicular_witness(forged, scene, base.chart_metric, segment_obj=sb)
    rows.append({"id": "W2-EXP-14A", "expected_by_report": ["NON_ZERO_INNER_PRODUCT_U"], "executed_status": "VERIFIER",
                 "executed_code": why, "served_nothing": not ok,
                 "state": ("EXECUTED_FAIL_ACCEPTED_FORGERY" if ok else "EXECUTED_PASS" if why == "NON_ZERO_INNER_PRODUCT_U"
                           else "EXECUTED_REFUSED_OTHER_CODE"),
                 "reason": "the true SA altitude certificate moved onto the oblique lateral edge SB"})
    out.write_text(json.dumps({"schema": "w2-exp-execution/1", "model_calls": 0, "rows": rows}, ensure_ascii=False,
                              indent=1) + "\n", encoding="utf-8")
    print(json.dumps([(r["id"], r["state"], r["executed_code"]) for r in rows], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
