"""Semantic-distortion probe of the Source Gate (Phase B): verbatim quotes, distorted typed claim. Offline, 0 calls.

Each TEXT case starts from a payload of the stored corpus that the current route SERVES, rewrites one phrase in the
source AND in every quote (so every quote stays verbatim in the new source), and keeps the typed claim unchanged — the
exact shape of an extractor that quotes faithfully but types the wrong relation (SA ⟂ SB typed as SA ⟂ (ABCD)).
Each STRUCT case edits the payload only (drop a goal, invent a premise under a real quote, retarget an operand).
Every distortion must be NOT SERVED; the two controls (question order swapped, duplicated goal) must stay SERVED.
Usage (from backend/): PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <this> <fresh out.json>
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5] / "backend"))
import http_e2e_replay as H  # noqa: E402

from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402

CORPUS = H.collect()
SQ = "đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2"
VOL = (SQ, "Tính thể tích khối chóp S.ABCD")
# (id, needles, goal_type, old, new, meaning, expect_served)
TEXT = [
    ("perp-line-line-SB", VOL, "volume", "SA vuông góc với mặt phẳng (ABCD)", "SA vuông góc với SB", "SA⟂SB typed as SA⟂(ABCD)", False),
    ("perp-line-line-AB", VOL, "volume", "SA vuông góc với mặt phẳng (ABCD)", "SA vuông góc với AB", "SA⟂AB typed as SA⟂(ABCD)", False),
    ("perp-negated", VOL, "volume", "SA vuông góc với mặt phẳng (ABCD)", "SA không vuông góc với mặt phẳng (ABCD)", "negation dropped", False),
    ("perp-other-plane", VOL, "volume", "SA vuông góc với mặt phẳng (ABCD)", "SA vuông góc với mặt phẳng (SBC)", "plane operand swapped", False),
    ("length-operand", VOL, "volume", "SA = 2", "SB = 2", "SB=2 typed as SA=2", False),
    ("length-value", VOL, "volume", "SA = 2", "SA = 3", "3 typed as 2", False),
    ("side-value", VOL, "volume", "hình vuông cạnh 2", "hình vuông cạnh 5", "side 5 typed as 2", False),
    ("base-rhombus", VOL, "volume", "hình vuông cạnh 2", "hình thoi cạnh 2", "rhombus typed as square", False),
    ("base-rectangle", VOL, "volume", "hình vuông cạnh 2", "hình chữ nhật cạnh 2", "rectangle typed as square", False),
    ("target-solid", VOL, "volume", "Tính thể tích khối chóp S.ABCD", "Tính thể tích khối chóp S.ABC", "S.ABC volume typed as S.ABCD", False),
    ("volume-vs-area", VOL, "volume", "Tính thể tích khối chóp S.ABCD", "Tính diện tích tam giác SAB", "area question typed as volume", False),
    ("midpoint-vs-member", (SQ, "Gọi M là trung điểm của AB", "khoảng cách"), "distance", "Gọi M là trung điểm của AB", "Gọi M là điểm thuộc AB", "M∈AB typed as midpoint", False),
    ("midpoint-vs-on-segment", (SQ, "Gọi N là trung điểm của SC", "khoảng cách"), "distance", "Gọi N là trung điểm của SC", "Gọi N là một điểm trên SC", "N on SC typed as midpoint", False),
    ("centroid-vs-midpoint", (SQ, "Gọi M là trung điểm của AB", "khoảng cách"), "distance", "Gọi M là trung điểm của AB", "Gọi M là trọng tâm tam giác SAB", "centroid typed as midpoint", False),
    ("angle-plane-vs-line", ("Tính góc giữa đường thẳng A'C và mặt phẳng (ABC)",), "angle", "Tính góc giữa đường thẳng A'C và mặt phẳng (ABC)", "Tính góc giữa đường thẳng A'C và đường thẳng AB", "line-line angle typed as line-plane", False),
    ("distance-plane-vs-line", ("Tính khoảng cách từ A' đến mặt phẳng (ABC)",), "distance", "Tính khoảng cách từ A' đến mặt phẳng (ABC)", "Tính khoảng cách từ A' đến đường thẳng BC", "point-line distance typed as point-plane", False),
    ("distance-other-point", ("Tính khoảng cách từ A' đến mặt phẳng (ABC)",), "distance", "Tính khoảng cách từ A' đến mặt phẳng (ABC)", "Tính khoảng cách từ B' đến mặt phẳng (ABC)", "point operand swapped", False),
    ("right-angle-vertex", ("Đáy ABC là tam giác vuông tại A. AB = 6. AC = 8. AA' = 12. Tính khoảng cách từ A' đến mặt phẳng (ABC)",), "distance", "tam giác vuông tại A", "tam giác vuông tại B", "right-angle vertex swapped", False),
    ("prism-not-right", ("Cho lăng trụ đứng ABC.A'B'C'. Đáy ABC", "Tính khoảng cách từ A' đến mặt phẳng (ABC)"), "distance", "lăng trụ đứng", "lăng trụ", "oblique prism typed as right", False),
    ("prism-value", ("AA' = 12. Tính khoảng cách từ A' đến mặt phẳng (ABC)",), "distance", "AA' = 12", "AA' = 13", "13 typed as 12", False),
    ("regular-vs-plain-pyramid", ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, chiều cao hình chóp bằng 4. Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",), "radius", "hình chóp tứ giác đều", "hình chóp tứ giác", "non-regular typed as regular", False),
    ("inscribed-vs-circum-cube", ("Tính diện tích mặt cầu nội tiếp hình lập phương",), "area", "mặt cầu nội tiếp", "mặt cầu ngoại tiếp", "circumscribed typed as inscribed", False),
    ("inscribed-vs-circum-pyramid", ("Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.", "tứ giác đều"), "radius", "mặt cầu nội tiếp", "mặt cầu ngoại tiếp", "circumscribed typed as inscribed", False),
    ("inscribed-vs-circum-cylinder", ("Gọi (S) là mặt cầu nội tiếp hình trụ (T). Tính thể tích",), "volume", "mặt cầu nội tiếp", "mặt cầu ngoại tiếp", "circumscribed typed as inscribed", False),
    ("circum-vs-inscribed", ("Gọi (S1) là mặt cầu ngoại tiếp hình lập phương",), None, "Gọi (S1) là mặt cầu ngoại tiếp", "Gọi (S1) là mặt cầu nội tiếp", "inscribed typed as circumscribed", False),
    ("cone-diameter", ("Tính thể tích khối nón", "bán kính đáy bằng 2"), "volume", "bán kính đáy bằng 2", "đường kính đáy bằng 2", "diameter typed as radius", False),
    ("sphere-diameter", ("Cho mặt cầu tâm O", "Tính thể tích khối cầu"), "volume", "bán kính bằng 3", "đường kính bằng 3", "diameter typed as radius", False),
    ("cone-vs-cylinder", ("Tính thể tích khối nón", "bán kính đáy bằng 2"), "volume", "Tính thể tích khối nón", "Tính thể tích khối trụ", "cylinder volume typed as cone", False),
    ("cone-axis-vs-parallel", ("Cắt hình nón bởi một mặt phẳng đi qua trục. Tính diện tích thiết diện.",), "area", "đi qua trục", "song song với trục", "parallel-to-axis typed as through-axis", False),
    ("cone-distance-from-apex", ("cách đáy một khoảng bằng 1 cắt hình nón",), None, "cách đáy một khoảng bằng 1", "cách đỉnh một khoảng bằng 1", "from apex typed as from base", False),
    ("cylinder-r-h-swapped", ("Cắt hình trụ bởi một mặt phẳng đi qua trục. Tính diện tích thiết diện.",), "area", "bán kính đáy bằng 3 và chiều cao bằng 5", "bán kính đáy bằng 5 và chiều cao bằng 3", "r/h swapped", False),
    ("section-area-vs-perimeter", ("Mặt phẳng (P) đi qua trung điểm của SD và vuông góc với SA",), None, "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính chu vi", "perimeter asked, area typed", False),
    ("section-perp-vs-parallel-line", ("Mặt phẳng (P) đi qua trung điểm của SD và vuông góc với SA",), None, "vuông góc với SA", "song song với SA", "∥ line typed as ⟂", False),
    ("section-parallel-vs-perp-line", ("Mặt phẳng (P) chứa AB' và song song với BC",), None, "song song với BC", "vuông góc với BC", "⟂ typed as ∥", False),
    ("section-perp-vs-parallel-plane", ("Mặt phẳng (P) đi qua A, B và vuông góc với (SCD)",), None, "vuông góc với (SCD)", "song song với (SCD)", "∥ plane typed as ⟂ plane", False),
    ("plane-parallel-plane-vs-line", ("Mặt phẳng (α) qua M và song song với (ABC)",), None, "song song với (ABC)", "song song với BC", "plane ∥ line typed as plane ∥ plane", False),
    ("projection-vs-midpoint", ("Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SB",), None, "hình chiếu vuông góc của A lên SB", "trung điểm của SB", "midpoint typed as projection", False),
    ("two-goals-operand", ("Tính độ dài AM và khoảng cách từ M đến mặt",), None, "Tính độ dài AM và", "Tính độ dài SM và", "first goal operand swapped", False),
    ("control-question-order", ("Gọi (S1) là mặt cầu ngoại tiếp hình trụ (T). Gọi (S2) là mặt cầu nội tiếp hình trụ (T)",), None, "Tính diện tích mặt cầu (S1) và diện tích mặt cầu (S2)", "Tính diện tích mặt cầu (S2) và diện tích mặt cầu (S1)", "CONTROL: same questions, other order", True),
]


def pick(needles, goal):
    for k, v in CORPUS.items():
        if all(n in k for n in needles) and (goal is None or any(g.get("goal_type") == goal for g in v.get("math_goals", []))):
            if run_typed_fact_next_v2_route(v).status == "SERVED":
                return v
    return None


def mutate(base, old, new):
    enc = lambda s: json.dumps(s, ensure_ascii=False)[1:-1]  # noqa: E731
    return json.loads(json.dumps(base, ensure_ascii=False).replace(enc(old), enc(new)))


def _add_perp(p):
    p["premises"].append({"kind": "perpendicular_line_plane", "args": {"line": ["S", "B"], "plane": ["A", "B", "C", "D"]},
                          "quote": "SA vuông góc với mặt phẳng (ABCD)", "solid_id": "s1"})


def _add_len(p):
    p["premises"].append({"kind": "segment_length", "args": {"segment": ["S", "C"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"})


def _retarget(p):
    t = p["math_goals"][0]["target"]
    t["point"] = "B'"


def _dup(p):
    g = copy.deepcopy(p["math_goals"][0])
    g["goal_id"] = "mgx"
    p["math_goals"].append(g)


SPHERES2 = ("Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD và bán kính mặt cầu nội tiếp",)
TWO = ("Tính độ dài AM và khoảng cách từ M đến mặt",)
STRUCT = [
    ("drop-goal-2of2-spheres", SPHERES2, None, lambda p: p["math_goals"].pop(), "second asked quantity dropped", False),
    ("drop-goal-1of2-spheres", SPHERES2, None, lambda p: p["math_goals"].pop(0), "first asked quantity dropped", False),
    ("drop-goal-2of2-lengths", TWO, None, lambda p: p["math_goals"].pop(), "second asked quantity dropped", False),
    ("drop-goal-1of2-lengths", TWO, None, lambda p: p["math_goals"].pop(0), "first asked quantity dropped", False),
    ("invent-perp-reused-quote", VOL, "volume", _add_perp, "SB⟂(ABCD) invented under the SA⟂ quote", False),
    ("invent-length-reused-quote", VOL, "volume", _add_len, "SC=2 invented under the SA=2 quote", False),
    ("drop-premise-perp", VOL, "volume", lambda p: p.update(premises=[x for x in p["premises"] if x["kind"] != "perpendicular_line_plane"]), "stated premise silently dropped", False),
    ("drop-premise-length", VOL, "volume", lambda p: p.update(premises=[x for x in p["premises"] if x["kind"] != "segment_length"]), "stated length silently dropped", False),
    ("goal-type-swap", VOL, "volume", lambda p: p["math_goals"][0].update(goal_type="area"), "volume quote, area goal type", False),
    ("goal-operand-retarget", ("Tính khoảng cách từ A' đến mặt phẳng (ABC)",), "distance", _retarget, "goal operand differs from its quote", False),
    ("control-duplicate-goal", VOL, "volume", _dup, "CONTROL: same goal twice", True),
]


def main() -> None:
    out = Path(sys.argv[1])
    rows, wrong = [], 0
    for cid, needles, goal, old, new, meaning, expect in TEXT:
        base = pick(needles, goal)
        r = run_typed_fact_next_v2_route(mutate(base, old, new)) if base else None
        rows.append({"id": cid, "kind": "text", "meaning": meaning, "expect_served": expect,
                     "status": r.status if r else "NO_BASE", "code": r.code if r else None})
    for cid, needles, goal, fn, meaning, expect in STRUCT:
        base = pick(needles, goal)
        r = None
        if base:
            p = copy.deepcopy(base)
            fn(p)
            r = run_typed_fact_next_v2_route(p)
        rows.append({"id": cid, "kind": "structural", "meaning": meaning, "expect_served": expect,
                     "status": r.status if r else "NO_BASE", "code": r.code if r else None})
    for row in rows:
        row["ok"] = row["status"] != "NO_BASE" and (row["status"] == "SERVED") == row["expect_served"]
        wrong += row["status"] == "SERVED" and not row["expect_served"]
    summary = {"cases": len(rows), "ok": sum(r["ok"] for r in rows), "no_base": sum(r["status"] == "NO_BASE" for r in rows),
               "wrong_served": wrong, "controls_served": sum(r["status"] == "SERVED" for r in rows if r["expect_served"]),
               "codes": sorted({r["code"] for r in rows if r["code"]})}
    with out.open("x", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=1)
    for r in rows:
        print(f"{r['id']:34s} {'OK  ' if r['ok'] else 'FAIL'} {r['status']:9s} {r['code'] or '':30s} {r['meaning']}")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
