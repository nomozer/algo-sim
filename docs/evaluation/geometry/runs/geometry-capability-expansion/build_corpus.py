"""Deterministic builder of `corpus-dev.json` (run `geometry-capability-expansion`) — no `app.*` import, 0 model calls.

Development corpus only (the Gemini blind holdout BH2A-01..18 is NOT used here). Each positive case carries its own
oracle chart (`oracle.py` computes the expected values) and a `success_source` label:
    new_primitive            needs a primitive this run adds (divide_segment)
    new_composition          a chain of functions no planner rule names (incl. MAT_VUONG_DUONG from existing primitives)
    new_configuration        a solid / base the engine could not lay out before (right trapezoid, oblique prism)
    semantic_representation  needs a fact form this run adds (point_kind divide_segment, plane ⊥ a 2-label line)
Provenance: AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED.

    python build_corpus.py      # refuses to overwrite
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent


def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


def q(fid, quote, **kw):
    return f(fid, "question", quote, role="question", **kw)


# ── premise templates ────────────────────────────────────────────────────────────────────────────────────────────────
SQ1 = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 1. SA vuông góc với (ABCD). SA = 3. "
SQ1_F = [f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
         f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 1.", points=list("ABCD"), shape="square", value="1"),
         f("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
         f("f4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3")]
SQ1_G = {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 1, 0], "S": [0, 0, 3]}
SQ2 = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 2. "
SQ2_F = [f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
         f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"), shape="square", value="2"),
         f("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
         f("f4", "length", "SA = 2.", points=["S", "A"], measure="segment", value="2")]
SQ2_G = {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0], "S": [0, 0, 2]}
TZ_Q = "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B."
TZ = TZ_Q + " AB = 1. AD = 2. BC = 1. SA vuông góc với (ABCD). SA = 1. "
TZ_F = [f("f1", "solid", TZ_Q, solid="S.ABCD", solid_type="pyramid"),
        f("ra", "right_angle", TZ_Q, at="A", points=["B", "D"]), f("rb", "right_angle", TZ_Q, at="B", points=["A", "C"]),
        f("l1", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
        f("l2", "length", "AD = 2.", points=["A", "D"], measure="segment", value="2"),
        f("l3", "length", "BC = 1.", points=["B", "C"], measure="segment", value="1"),
        f("pp", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
        f("l4", "length", "SA = 1.", points=["S", "A"], measure="segment", value="1")]
TZ_G = {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 2, 0], "S": [0, 0, 1]}
TD_Q = "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và D."
TD = TD_Q + " AB = 1. AD = 2. CD = 3. SA vuông góc với (ABCD). SA = 2. "
TD_F = [f("f1", "solid", TD_Q, solid="S.ABCD", solid_type="pyramid"),
        f("ra", "right_angle", TD_Q, at="A", points=["B", "D"]), f("rd", "right_angle", TD_Q, at="D", points=["A", "C"]),
        f("l1", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
        f("l2", "length", "AD = 2.", points=["A", "D"], measure="segment", value="2"),
        f("l3", "length", "CD = 3.", points=["C", "D"], measure="segment", value="3"),
        f("pp", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
        f("l4", "length", "SA = 2.", points=["S", "A"], measure="segment", value="2")]
TD_G = {"A": [0, 0, 0], "B": [1, 0, 0], "D": [0, 2, 0], "C": [3, 2, 0], "S": [0, 0, 2]}
OP_Q = "Cho lăng trụ ABC.A'B'C' có đáy là tam giác đều ABC cạnh 1."
OP = OP_Q + " Gọi H là trung điểm của BC. Hình chiếu vuông góc của A' lên (ABC) là H. AA' = 1. "
OP_F = [f("f1", "solid", OP_Q, solid="ABC.A'B'C'", solid_type="prism"),
        f("f2", "polygon_shape", OP_Q, points=list("ABC"), shape="equilateral_triangle", value="1"),
        f("h", "point_def", "Gọi H là trung điểm của BC.", point="H", point_kind="midpoint", points=["B", "C"]),
        f("p", "projection", "Hình chiếu vuông góc của A' lên (ABC) là H.", point="A'", points=list("ABC"), at="H"),
        f("l", "length", "AA' = 1.", points=["A", "A'"], measure="segment", value="1")]
# chart: A origin, AB, AC at 60° (|AB| = |AC| = 1), vertical axis with h² = 1 − AH² = 1/4
OP_G = ({"A": [0, 0, 0], "B": [1, 0, 0], "C": [0, 1, 0], "H": ["1/2", "1/2", 0], "A'": ["1/2", "1/2", 1],
         "B'": ["3/2", "1/2", 1], "C'": ["1/2", "3/2", 1]}, [[1, "1/2", 0], ["1/2", 1, 0], [0, 0, "1/4"]])
RT_Q = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B."
RT = RT_Q + " AB = 1. BC = 1. SA vuông góc với (ABC). SA = 1. "
RT_F = [f("f1", "solid", RT_Q, solid="S.ABC", solid_type="pyramid"), f("f2", "right_angle", RT_Q, at="B", points=["A", "C"]),
        f("f3", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
        f("f4", "length", "BC = 1.", points=["B", "C"], measure="segment", value="1"),
        f("f5", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
        f("f6", "length", "SA = 1.", points=["S", "A"], measure="segment", value="1")]
RT_G = {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "S": [0, 0, 1]}


def M_DEF(wording="SM = 2MA", seg=("S", "A"), t="2/3"):
    quote = f"Gọi M là điểm thuộc cạnh SA sao cho {wording}."
    return quote, f("m", "point_def", quote, point="M", point_kind="divide_segment", points=list(seg), value=t)


def perp_q(fid, point, line, solid, name="P"):
    define = f"Dựng mặt phẳng ({name}) đi qua {point} và vuông góc với {line}."
    ask = f"Tính diện tích thiết diện của hình chóp {solid} với ({name})."
    fact = {"id": fid, "kind": "question", "role": "question", "quotes": [define, ask], "quantity": "area", "solid": solid,
            "point": point, "points_b": list(line), "plane_relation": "perpendicular"}
    return f"{define} {ask}", fact


def case(cid, text, facts, geometry, goals, source, composition, w2=None):
    pts, G = geometry if isinstance(geometry, tuple) else (geometry, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    return {"id": cid, "kind": "positive", "split": "dev", "source": w2 or "authored", "success_source": source,
            "composition": composition, "text": text.strip(), "payload": {"facts": facts},
            "geometry": {"points": pts, "gram": G}, "goals": goals}


def neg(cid, text, facts, codes, note, w2=None):
    return {"id": cid, "kind": "negative", "split": "dev", "source": w2 or "authored", "expected_codes": sorted(codes),
            "note": note, "text": text.strip(), "payload": {"facts": facts}}


def cases():
    out = []
    mq, mf = M_DEF()
    n_q = "Gọi N là trung điểm của BC."
    nf = f("n", "point_def", n_q, point="N", point_kind="midpoint", points=["B", "C"])
    a1, a2 = "Tính độ dài MN.", "Tính khoảng cách từ M đến DN."
    out.append(case("W2-EXP-03", f"{SQ1}{mq} {n_q} {a1} {a2}",
                    SQ1_F + [mf, nf, q("q1", a1, quantity="length", points=["M", "N"]),
                             q("q2", a2, quantity="distance", points_a=["M"], points_b=["D", "N"])],
                    SQ1_G, {"q1": {"measure": "length", "point": {"divide": ["S", "A"], "t": "2/3"}, "target": {"desc": "midpoint", "of": ["B", "C"]}},
                            "q2": {"measure": "distance_line", "point": {"divide": ["S", "A"], "t": "2/3"},
                                   "target": ["D", {"desc": "midpoint", "of": ["B", "C"]}]}},
                    "new_primitive", "divide_segment -> ask_length | divide_segment -> orthogonal_projection_line -> ask_length",
                    "W2-EXP-03"))
    mq3, mf3 = M_DEF("SA = 3SM", ("S", "A"), "1/3")
    a = "Tính góc giữa CM và (ABCD)."
    out.append(case("dev-ratio-angle", f"{SQ1}{mq3} {a}", SQ1_F + [mf3, q("q", a, quantity="angle", points_a=["C", "M"],
                                                                         points_b=list("ABCD"))],
                    SQ1_G, {"q": {"measure": "cos2_line_plane", "point": "C", "partner": {"divide": ["S", "A"], "t": "1/3"},
                                  "target": ["A", "B", "C"]}},
                    "new_primitive", "divide_segment -> ask_angle_line_plane"))
    a = "Tính diện tích tam giác tạo bởi trung điểm của MC và hai điểm A, B."
    out.append(case("dev-ratio-midpoint-area", f"{SQ1}{mq} {a}",
                    SQ1_F + [mf, q("q", a, quantity="area", point_kind="midpoint", points=["M", "C"], points_b=["A", "B"])],
                    {**SQ1_G, "M": [0, 0, 1]},
                    {"q": {"measure": "area", "point": {"desc": "midpoint", "of": ["M", "C"]}, "target": ["A", "B"]}},
                    "new_composition", "divide_segment -> midpoint -> ask_area"))
    a1, a2 = "Tính thể tích khối chóp S.ABCD.", "Tính góc giữa SC và (SAD)."
    out.append(case("W2-EXP-06A", f"{TZ}{a1} {a2}",
                    TZ_F + [q("q1", a1, quantity="volume", solid="S.ABCD"),
                            q("q2", a2, quantity="angle", points_a=["S", "C"], points_b=["S", "A", "D"])],
                    TZ_G, {"q1": {"measure": "volume_pyramid", "point": "S", "apex": "S", "base": list("ABCD")},
                           "q2": {"measure": "cos2_line_plane", "point": "S", "partner": "C", "target": ["S", "A", "D"]}},
                    "new_configuration", "ask_volume | ask_angle_line_plane", "W2-EXP-06A"))
    a1, a2 = "Tính khoảng cách từ A đến (SCD).", "Tính khoảng cách từ trọng tâm của tam giác SCD đến (ABCD)."
    out.append(case("dev-trapezoid-distances", f"{TZ}{a1} {a2}",
                    TZ_F + [q("q1", a1, quantity="distance", points_a=["A"], points_b=["S", "C", "D"]),
                            q("q2", a2, quantity="distance", point_kind="centroid", points=["S", "C", "D"], points_b=list("ABCD"))],
                    TZ_G, {"q1": {"measure": "distance_plane", "point": "A", "target": ["S", "C", "D"]},
                           "q2": {"measure": "distance_plane", "point": {"desc": "centroid", "of": ["S", "C", "D"]},
                                  "target": ["A", "B", "C"]}},
                    "new_configuration", "ask_distance_point_plane | centroid -> ask_distance_point_plane"))
    a = "Tính khoảng cách từ S đến đường thẳng BC."
    out.append(case("dev-trapezoid-AD", f"{TD}{a}",
                    TD_F + [q("q", a, quantity="distance", points_a=["S"], points_b=["B", "C"])], TD_G,
                    {"q": {"measure": "distance_line", "point": "S", "target": ["B", "C"]}},
                    "new_configuration", "orthogonal_projection_line -> ask_length"))
    a = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    out.append(case("W2-EXP-06B", f"{OP}{a}", OP_F + [q("q", a, quantity="volume", solid="ABC.A'B'C'")], OP_G,
                    {"q": {"measure": "volume_prism", "point": "A", "base": ["A", "B", "C"], "top": "A'"}},
                    "new_configuration", "ask_volume", "W2-EXP-06B"))
    a1, a2 = "Tính khoảng cách từ trung điểm của B'C' đến (ABC).", "Tính góc giữa A'B và (ABC)."
    out.append(case("dev-oblique-prism-compositions", f"{OP}{a1} {a2}",
                    OP_F + [q("q1", a1, quantity="distance", point_kind="midpoint", points=["B'", "C'"], points_b=list("ABC")),
                            q("q2", a2, quantity="angle", points_a=["A'", "B"], points_b=list("ABC"))],
                    OP_G, {"q1": {"measure": "distance_plane", "point": {"desc": "midpoint", "of": ["B'", "C'"]},
                                  "target": ["A", "B", "C"]},
                           "q2": {"measure": "cos2_line_plane", "point": "A'", "partner": "B", "target": ["A", "B", "C"]}},
                    "new_configuration", "midpoint -> ask_distance_point_plane | ask_angle_line_plane"))
    t, fq = perp_q("q", "A", "SC", "S.ABC")
    out.append(case("W2-EXP-07", f"{RT}{t}", RT_F + [fq], RT_G,
                    {"q": {"measure": "section_area", "point": "A", "solid": {"apex": "S", "base": list("ABC")}, "line": ["S", "C"]}},
                    "new_composition", "orthogonal_projection_line x2 -> translate_point x2 -> ask_section_area", "W2-EXP-07"))
    t, fq = perp_q("q", "A", "SC", "S.ABCD")
    out.append(case("dev-perp-square-A-SC", f"{SQ2}{t}", SQ2_F + [fq], SQ2_G,
                    {"q": {"measure": "section_area", "point": "A", "solid": {"apex": "S", "base": list("ABCD")}, "line": ["S", "C"]}},
                    "new_composition", "orthogonal_projection_line x2 -> translate_point x2 -> ask_section_area"))
    t, fq = perp_q("q", "S", "BD", "S.ABCD")
    out.append(case("dev-perp-square-S-BD", f"{SQ2}{t}", SQ2_F + [fq], SQ2_G,
                    {"q": {"measure": "section_area", "point": "S", "solid": {"apex": "S", "base": list("ABCD")}, "line": ["B", "D"]}},
                    "new_composition", "orthogonal_projection_line x2 -> translate_point x2 -> ask_section_area"))
    mq2, mf2 = M_DEF("SM = MA", ("S", "A"), "1/2")
    mq2 = mq2.replace("Gọi M là điểm thuộc cạnh SA sao cho SM = MA.", "Gọi M là điểm thuộc cạnh SA sao cho SM = MA.")
    t, fq = perp_q("q", "M", "SC", "S.ABCD")
    out.append(case("dev-ratio-then-perp-section", f"{SQ2}{mq2} {t}", SQ2_F + [mf2, fq], SQ2_G,
                    {"q": {"measure": "section_area", "point": {"divide": ["S", "A"], "t": "1/2"},
                           "solid": {"apex": "S", "base": list("ABCD")}, "line": ["S", "C"]}},
                    "new_composition", "divide_segment -> (orthogonal_projection_line x2 -> translate_point x2) -> ask_section_area"))
    # negatives
    a = "Tính độ dài MN."
    base = SQ1_F + [mf, nf, q("q", a, quantity="length", points=["M", "N"])]
    text = f"{SQ1}{mq} {n_q} {a}"
    out.append(neg("neg-ratio-mismatch", text, [{**x, "value": "1/3"} if x["id"] == "m" else x for x in deepcopy(base)],
                   {"SOURCE_OBJECT_MISMATCH"}, "fact t = 1/3 from S; the source says SM = 2MA (t = 2/3)"))
    out.append(neg("neg-ratio-outside", text, [{**x, "value": "3/2"} if x["id"] == "m" else x for x in deepcopy(base)],
                   {"INVALID_RATIO"}, "t ∉ (0, 1)"))
    a = "Tính thể tích khối chóp S.ABCD."
    tz2 = TZ.replace("BC = 1.", "BC = √2.")
    out.append(neg("neg-trapezoid-irrational", tz2 + a,
                   [{**x, "quotes": ["BC = √2."], "value": "√2"} if x["id"] == "l3" else x for x in deepcopy(TZ_F)]
                   + [q("q", a, quantity="volume", solid="S.ABCD")], {"UNSUPPORTED_IRRATIONAL_LAYOUT"},
                   "BC : AD = √2 : 2 has no exact ℚ chart"))
    out.append(neg("neg-trapezoid-one-right-angle", TZ + a, [x for x in deepcopy(TZ_F) if x["id"] != "rb"]
                   + [q("q", a, quantity="volume", solid="S.ABCD")], {"UNSUPPORTED_BASE_SHAPE"}, "one right angle only"))
    a = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    out.append(neg("neg-oblique-prism-underdetermined", OP.replace("Hình chiếu vuông góc của A' lên (ABC) là H. ", "") + a,
                   [x for x in deepcopy(OP_F) if x["id"] != "p"] + [q("q", a, quantity="volume", solid="ABC.A'B'C'")],
                   {"UNDERDETERMINED_POINT"}, "no top vertex fixed"))
    t, fq = perp_q("q", "S", "SC", "S.ABCD")
    t2 = t.replace("vuông góc với SC", "vuông góc với (ABCD)")
    fq2 = {**fq, "point": "A", "points_b": list("ABCD"), "quotes": [x.replace("vuông góc với SC", "vuông góc với (ABCD)")
                                                                   .replace("đi qua S", "đi qua A") for x in fq["quotes"]]}
    out.append(neg("neg-perp-plane-not-unique", f"{SQ2}{t2.replace('đi qua S', 'đi qua A')}", SQ2_F + [fq2],
                   {"PLANE_NOT_UNIQUE"}, "plane through A ⊥ a PLANE is not unique (unchanged)"))
    t, fq = perp_q("q", "S", "SC", "S.ABC")
    out.append(neg("neg-perp-touches-apex", f"{RT}{t}", RT_F + [fq], {"PLANE_TOUCHES_VERTEX", "PLANE_DOES_NOT_CUT"},
                   "the plane through S ⊥ SC meets the pyramid at S only"))
    t, fq = perp_q("q", "A", "SB", "S.ABC")
    fq["points_b"] = ["S", "C"]
    out.append(neg("neg-perp-wrong-line", f"{RT}{t}", RT_F + [fq], {"SOURCE_OBJECT_MISMATCH"},
                   "fact ⊥ SC, the source says ⊥ SB"))
    return out


def main() -> int:
    out = HERE / "corpus-dev.json"
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    cs = cases()
    out.write_text(json.dumps({"schema": "geometry-capability-corpus/1", "run": "geometry-capability-expansion", "split": "dev",
                               "provenance": "AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED", "cases": cs},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(cs)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
