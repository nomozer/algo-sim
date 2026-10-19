"""Deterministic builder of `corpus.json` (run `source-gate-hardening`) — no `app.*` import, 0 model calls.

Groups (P4 of the run):
    A  minimal reproducer of each finding SG-1..SG-6 (the same wording as the run's tests)
    B  valid variants NOT in the tests: other labels (T.MNPQ), solids, numbers, request verbs and goal kinds
    C  negative / adversarial variants NOT in the tests
Group D (the 18 BH2A problems as a known regression) is measured separately from the owner-supplied texts.
Positive cases carry their own oracle chart (`oracle.py` computes every expected value); symbolic cases are written with
a = 1 and declare `symbolic`. Provenance: AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED.

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


SQ = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
SQF = [f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
       f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"), shape="square", value="2"),
       f("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
       f("f4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3")]
SQG = {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0], "S": [0, 0, 3]}
TQ = "Cho hình chóp T.MNPQ. Đáy MNPQ là hình vuông cạnh 2. TM vuông góc với (MNPQ). TM = 1. "
TQF = [f("f1", "solid", "Cho hình chóp T.MNPQ.", solid="T.MNPQ", solid_type="pyramid"),
       f("f2", "polygon_shape", "Đáy MNPQ là hình vuông cạnh 2.", points=list("MNPQ"), shape="square", value="2"),
       f("f3", "perpendicular", "TM vuông góc với (MNPQ).", points_a=["T", "M"], points_b=list("MNPQ")),
       f("f4", "length", "TM = 1.", points=["T", "M"], measure="segment", value="1")]
TQG = {"M": [0, 0, 0], "N": [2, 0, 0], "P": [2, 2, 0], "Q": [0, 2, 0], "T": [0, 0, 1]}
MID = lambda *o: {"desc": "midpoint", "of": list(o)}       # noqa: E731
CEN = lambda *o: {"desc": "centroid", "of": list(o)}       # noqa: E731
CASES: list[dict] = []


def pos(cid, group, sg, text, facts, geometry, goals, symbolic=False, gram=None):
    g = {"points": geometry, **({"gram": gram} if gram else {})}
    CASES.append({"id": cid, "group": group, "sg": sg, "kind": "positive", "symbolic": symbolic, "text": text,
                  "payload": {"facts": deepcopy(facts)}, "geometry": g, "goals": goals})


def neg(cid, sg, text, facts, codes, note):
    CASES.append({"id": cid, "group": "C", "sg": sg, "kind": "negative", "text": text, "payload": {"facts": deepcopy(facts)},
                  "expected_codes": codes, "note": note})


def rect_pyr(sentence, solid, base, apex_edge, apex_len, lengths, tail_ask):
    a, b = apex_edge
    return [f("f1", "solid", sentence, solid=solid, solid_type="pyramid"),
            f("f2", "polygon_shape", sentence, points=list(base), shape="rectangle"),
            *[f(f"l{i}", "length", sentence, points=list(p), measure="segment", value=v) for i, (p, v) in enumerate(lengths)],
            f("f5", "perpendicular", f"{a}{b} vuông góc với ({base})", points_a=[a, b], points_b=list(base)),
            f("f6", "length", f"{a}{b} = {apex_len}", points=[a, b], measure="segment", value=apex_len), tail_ask]


def regular_pyr(sentence, solid, measures, ask, ask_fact):
    return sentence + " " + ask, [f("f1", "solid", sentence, solid=solid, solid_type="pyramid", regular=True),
                                  *[f(f"m{i}", "length", sentence, measure=m, value=v, solid=solid)
                                    for i, (m, v) in enumerate(measures)], ask_fact]


# ── A: minimal reproducers ──────────────────────────────────────────────────────────────────────────────────────────
s = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2 và BC = 3."
ask = "Tính thể tích khối chóp S.ABCD."
pos("A-SG1", "A", "SG-1", s + " SA vuông góc với (ABCD) và SA = 1. " + ask,
    rect_pyr(s, "S.ABCD", "ABCD", "SA", "1", [("AB", "2"), ("BC", "3")], q("q", ask, quantity="volume", solid="S.ABCD")),
    {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 3, 0], "D": [0, 3, 0], "S": [0, 0, 1]},
    {"q": {"measure": "volume_pyramid", "apex": "S", "base": list("ABCD")}})
t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 3a. "
ask = "Biết đáy ABCD là hình vuông cạnh 2a, tính độ dài SC."
SYMF = [f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2a", points=list("ABCD"), shape="square", value="2a"),
        f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
        f("f4", "length", "SA = 3a", points=["S", "A"], measure="segment", value="3a")]
pos("A-SG2", "A", "SG-2", t + ask, SYMF + [q("q", ask, quantity="length", points=["S", "C"])], SQG,
    {"q": {"measure": "length", "point": "S", "target": "C"}}, symbolic=True)
text, facts = regular_pyr("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao bằng 5a.", "S.ABCD",
                          [("base_edge", "4a"), ("height", "5a")], "Tính thể tích khối chóp S.ABCD.",
                          q("q", "Tính thể tích khối chóp S.ABCD.", quantity="volume", solid="S.ABCD"))
pos("A-SG3", "A", "SG-3", text, facts, {"A": [0, 0, 0], "B": [4, 0, 0], "C": [4, 4, 0], "D": [0, 4, 0], "S": [2, 2, 5]},
    {"q": {"measure": "volume_pyramid", "apex": "S", "base": list("ABCD")}}, symbolic=True)
ask = "Tính độ dài đoạn nối đỉnh S với trung điểm của BC."
pos("A-SG4", "A", "SG-4", SQ + ask, SQF + [q("q", ask, quantity="length", point_kind="midpoint", points=["B", "C"],
                                             points_b=["S"])], SQG,
    {"q": {"measure": "length", "point": MID("B", "C"), "target": "S"}})
ask = "Tính độ dài SB và tính độ dài SC."
pos("A-SG5", "A", "SG-5", SQ + ask, SQF + [q("q1", ask, quantity="length", points=["S", "B"]),
                                             q("q2", ask, quantity="length", points=["S", "C"])], SQG,
    {"q1": {"measure": "length", "point": "S", "target": "B"}, "q2": {"measure": "length", "point": "S", "target": "C"}})
ask = "Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD)."
pos("A-SG6", "A", "SG-6", SQ + ask, SQF + [f("g", "intersection_line", ask, role="question", points_a=list("SCD"),
                                             points_b=list("ABCD")),
                                           q("q", ask, quantity="distance", points_a=["A"], line_ref="g")], SQG,
    {"q": {"measure": "distance_intersection", "point": "A", "planes": [list("SCD"), list("ABCD")]}})

# ── B: valid variants not in the tests ──────────────────────────────────────────────────────────────────────────────
s = "Cho hình chóp T.MNPQ có đáy MNPQ là hình chữ nhật, NP = 4 và MN = 3."
ask = "Tính thể tích khối chóp T.MNPQ."
pos("B-SG1-renamed", "B", "SG-1", s + " TM vuông góc với (MNPQ) và TM = 2. " + ask,
    rect_pyr(s, "T.MNPQ", "MNPQ", "TM", "2", [("MN", "3"), ("NP", "4")], q("q", ask, quantity="volume", solid="T.MNPQ")),
    {"M": [0, 0, 0], "N": [3, 0, 0], "P": [3, 4, 0], "Q": [0, 4, 0], "T": [0, 0, 2]},
    {"q": {"measure": "volume_pyramid", "apex": "T", "base": list("MNPQ")}})
s = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật có AB = 3, AD = 2."
ask = "Tính độ dài SC."
pos("B-SG1-AD-length", "B", "SG-1", s + " SA vuông góc với (ABCD) và SA = 2. " + ask,
    rect_pyr(s, "S.ABCD", "ABCD", "SA", "2", [("AB", "3"), ("AD", "2")], q("q", ask, quantity="length", points=["S", "C"])),
    {"A": [0, 0, 0], "B": [3, 0, 0], "C": [3, 2, 0], "D": [0, 2, 0], "S": [0, 0, 2]},
    {"q": {"measure": "length", "point": "S", "target": "C"}})
t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD), SA = a. "
ask = "Biết đáy ABCD là hình vuông cạnh a, tính khoảng cách từ A đến (SBC)."
pos("B-SG2-distance", "B", "SG-2", t + ask,
    [f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
     f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh a", points=list("ABCD"), shape="square", value="a"),
     f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
     f("f4", "length", "SA = a", points=["S", "A"], measure="segment", value="a"),
     q("q", ask, quantity="distance", points_a=["A"], points_b=["S", "B", "C"])],
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0], "D": [0, 1, 0], "S": [0, 0, 1]},
    {"q": {"measure": "distance_plane", "point": "A", "target": ["S", "B", "C"]}}, symbolic=True)
text, facts = regular_pyr("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 6 và chiều cao bằng 2.", "S.ABC",
                          [("base_edge", "6"), ("height", "2")], "Tính thể tích khối chóp S.ABC.",
                          q("q", "Tính thể tích khối chóp S.ABC.", quantity="volume", solid="S.ABC"))
pos("B-SG3-triangular", "B", "SG-3", text, facts,           # chart e1 = AB, e2 = AC (|6|, 60°), e3 vertical
    {"A": [0, 0, 0], "B": [1, 0, 0], "C": [0, 1, 0], "S": ["1/3", "1/3", 2]},
    {"q": {"measure": "volume_tetrahedron", "point": "S", "target": ["A", "B", "C"]}},
    gram=[[36, 18, 0], [18, 36, 0], [0, 0, 1]])
text, facts = regular_pyr("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 5 và cạnh đáy bằng 6.", "S.ABCD",
                          [("lateral_edge", "5"), ("base_edge", "6")], "Tính độ dài SA.",
                          q("q", "Tính độ dài SA.", quantity="length", points=["S", "A"]))
pos("B-SG3-lateral-and-base", "B", "SG-3", text, facts,     # h² = 25 − 18 = 7: chart z scaled by √7
    {"A": [0, 0, 0], "B": [6, 0, 0], "C": [6, 6, 0], "D": [0, 6, 0], "S": [3, 3, 1]},
    {"q": {"measure": "length", "point": "S", "target": "A"}}, gram=[[1, 0, 0], [0, 1, 0], [0, 0, 7]])
ask = "Tính góc giữa đường thẳng nối điểm A và trọng tâm của tam giác SBC với (ABCD)."
pos("B-SG4-angle", "B", "SG-4", SQ + ask,
    SQF + [q("q", ask, quantity="angle", point_kind="centroid", points=["S", "B", "C"], points_a=["A"], points_b=list("ABCD"))],
    SQG, {"q": {"measure": "cos2_line_plane", "point": CEN("S", "B", "C"), "partner": "A", "target": ["A", "B", "C"]}})
ask = "Tính diện tích tam giác có ba đỉnh là trung điểm của SC, điểm A và điểm B."
pos("B-SG4-area-three-vertices", "B", "SG-4", SQ + ask,
    SQF + [q("q", ask, quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"])],
    SQG, {"q": {"measure": "area", "point": MID("S", "C"), "target": ["A", "B"]}})
ask = "Hãy tính độ dài SB, đồng thời tìm độ dài SD."
pos("B-SG5-hay-dong-thoi", "B", "SG-5", SQ + ask,
    SQF + [q("q1", ask, quantity="length", points=["S", "B"]), q("q2", ask, quantity="length", points=["S", "D"])], SQG,
    {"q1": {"measure": "length", "point": "S", "target": "B"}, "q2": {"measure": "length", "point": "S", "target": "D"}})
ask = "Tính thể tích khối chóp S.ABCD và tính khoảng cách từ A đến (SBC)."
pos("B-SG5-mixed", "B", "SG-5", SQ + ask,
    SQF + [q("q1", ask, quantity="volume", solid="S.ABCD"),
           q("q2", ask, quantity="distance", points_a=["A"], points_b=["S", "B", "C"])], SQG,
    {"q1": {"measure": "volume_pyramid", "apex": "S", "base": list("ABCD")},
     "q2": {"measure": "distance_plane", "point": "A", "target": ["S", "B", "C"]}})
for cid, ask, a, b, p in (
        ("B-SG6-renamed-base-face", "Tính khoảng cách từ M đến giao tuyến của (TNP) và (MNPQ).", "TNP", "MNPQ", "M"),
        ("B-SG6-renamed-apex-line", "Tính khoảng cách từ P đến giao tuyến của (TMN) và (TPQ).", "TMN", "TPQ", "P")):
    pos(cid, "B", "SG-6", TQ + ask, TQF + [f("g", "intersection_line", ask, role="question", points_a=list(a), points_b=list(b)),
                                          q("q", ask, quantity="distance", points_a=[p], line_ref="g")], TQG,
        {"q": {"measure": "distance_intersection", "point": p, "planes": [list(a), list(b)]}})
ask = "Tính khoảng cách từ C tới giao tuyến của mặt phẳng (SAD) và mặt phẳng (ABCD)."
pos("B-SG6-mat-phang-toi", "B", "SG-6", SQ + ask,
    SQF + [f("g", "intersection_line", ask, role="question", points_a=list("SAD"), points_b=list("ABCD")),
           q("q", ask, quantity="distance", points_a=["C"], line_ref="g")], SQG,
    {"q": {"measure": "distance_intersection", "point": "C", "planes": [list("SAD"), list("ABCD")]}})

# ── C: negatives / adversarial not in the tests ─────────────────────────────────────────────────────────────────────
s = "Cho hình chóp T.MNPQ có đáy MNPQ là hình chữ nhật, MN = 3."
ask = "Tính thể tích khối chóp T.MNPQ."
neg("C-SG1-spoof-renamed", "SG-1", s + " TM vuông góc với (MNPQ) và TM = 2. " + ask,
    rect_pyr(s, "T.MNPQ", "MNPQ", "TM", "2", [("MN", "3"), ("NP", "3")], q("q", ask, quantity="volume", solid="T.MNPQ")),
    ["UNGROUNDED_VALUE"], "NP is never written; its value must not borrow MN's number through MNPQ")
s = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB, BC lần lượt bằng 2, 3."
ask = "Tính thể tích khối chóp S.ABCD."
neg("C-SG1-respectively", "SG-1", s + " SA vuông góc với (ABCD) và SA = 1. " + ask,
    rect_pyr(s, "S.ABCD", "ABCD", "SA", "1", [("AB", "2"), ("BC", "3")], q("q", ask, quantity="volume", solid="S.ABCD")),
    ["UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE"], "'lần lượt' binding is not read: refuse rather than guess")
t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD), SA = a. "
ask = "Biết đáy ABCD là hình vuông cạnh 1, tính độ dài SC."
neg("C-SG2-parameter-dropped-in-ask", "SG-2", t + ask,
    [f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
     f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh a", points=list("ABCD"), shape="square", value="a"),
     f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
     f("f4", "length", "SA = a", points=["S", "A"], measure="segment", value="a"),
     q("q", ask, quantity="length", points=["S", "C"])],
    ["QUESTION_LOCAL_GIVEN_UNVERIFIED", "QUESTION_LOCAL_GIVEN_CONFLICT", "NON_HOMOGENEOUS_LENGTHS"],
    "the ask restates side 1 for a side a")
text, facts = regular_pyr("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 6 và chiều cao bằng 2.", "S.ABC",
                          [("base_edge", "2"), ("height", "6")], "Tính thể tích khối chóp S.ABC.",
                          q("q", "Tính thể tích khối chóp S.ABC.", quantity="volume", solid="S.ABC"))
neg("C-SG3-swapped-triangular", "SG-3", text, facts, ["UNGROUNDED_VALUE"], "base edge and height swapped")
text, facts = regular_pyr("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, cạnh bên bằng 5 và chiều cao bằng 4.", "S.ABCD",
                          [("base_edge", "6"), ("lateral_edge", "5"), ("height", "4")], "Tính thể tích khối chóp S.ABCD.",
                          q("q", "Tính thể tích khối chóp S.ABCD.", quantity="volume", solid="S.ABCD"))
neg("C-SG3-overdetermined-inconsistent", "SG-3", text, facts, ["INCONSISTENT_FACTS", "HEIGHT_CONFLICT", "OVERDETERMINED"],
    "h² = 25 − 18 = 7 ≠ 16: the three values cannot all hold")
ask = "Tính độ dài đoạn nối đỉnh S với trung điểm của BC."
neg("C-SG4-other-midpoint", "SG-4", SQ + ask,
    SQF + [q("q", ask, quantity="length", point_kind="midpoint", points=["A", "D"], points_b=["S"])],
    ["SOURCE_OBJECT_MISMATCH"], "the fact describes the midpoint of AD")
ask = "Tính diện tích tam giác tạo bởi trung điểm của BC với hai điểm S, A."
neg("C-SG4-swapped-vertex", "SG-4", SQ + ask,
    SQF + [q("q", ask, quantity="area", point_kind="midpoint", points=["B", "C"], points_b=["S", "C"])],
    ["SOURCE_OBJECT_MISMATCH"], "C is not a vertex the source names")
ask = "Tính độ dài SB và tính độ dài SC."
neg("C-SG5-first-dropped", "SG-5", SQ + ask, SQF + [q("q2", ask, quantity="length", points=["S", "C"])],
    ["REQUEST_NOT_ANSWERED"], "the first request has no call: no partial serve")
ask = "Tính độ dài SB và tính độ dài SE."
neg("C-SG5-unknown-point", "SG-5", SQ + ask, SQF + [q("q1", ask, quantity="length", points=["S", "B"])],
    ["REQUEST_NOT_ANSWERED", "NOT_ASKED_IN_SOURCE", "UNKNOWN_LABEL", "QUESTION_CONTEXT_UNSUPPORTED"],
    "E is not a point of the problem")
cube = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. "
ask = "Tính khoảng cách từ A đến giao tuyến của (ABCD) và (A'B'C'D')."
neg("C-SG6-parallel-faces", "SG-6", cube + ask,
    [f("f1", "solid", cube.strip(), solid="ABCD.A'B'C'D'", solid_type="cube"),
     f("f2", "length", cube.strip(), solid="ABCD.A'B'C'D'", measure="edge", value="2"),
     f("g", "intersection_line", ask, role="question", points_a=list("ABCD"), points_b=["A'", "B'", "C'", "D'"]),
     q("q", ask, quantity="distance", points_a=["A"], line_ref="g")],
    ["PARALLEL_PLANES", "PARALLEL_NO_INTERSECTION", "NO_INTERSECTION"], "opposite faces of a cube do not meet")
ask = "Tính khoảng cách từ A đến giao tuyến của (SBCD) và (ABCD)."
neg("C-SG6-non-coplanar-face", "SG-6", SQ + ask,
    SQF + [f("g", "intersection_line", ask, role="question", points_a=list("SBCD"), points_b=list("ABCD")),
           q("q", ask, quantity="distance", points_a=["A"], line_ref="g")],
    ["NON_COPLANAR_POINTS"], "S, B, C, D are not coplanar")
ask = "Nếu SA = 4 thì tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD)."
neg("C-SG6-conditional", "SG-6", SQ + ask,
    SQF + [f("g", "intersection_line", ask, role="question", points_a=list("SCD"), points_b=list("ABCD")),
           q("q", ask, quantity="distance", points_a=["A"], line_ref="g")],
    ["CONDITIONAL_CLAUSE", "SOURCE_OBJECT_MISMATCH", "QUESTION_CONTEXT_UNSUPPORTED", "SOURCE_PREMISE_UNREAD"],
    "the question is conditional on a value change")

if __name__ == "__main__":
    out = HERE / "corpus.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps({"schema": "source-gate-corpus/1", "provenance": "AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED",
                               "cases": CASES}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(len(CASES), "cases →", out)
