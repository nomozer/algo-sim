"""Source gate hardening (run `source-gate-hardening`): six finding groups SG-1..SG-6 on route D's source gate.

Each group: the minimal reproducer (RED on `6973c4b6`), unseen valid variants, and adversarial negatives that must stay
refused. Expected values are hand-derived from Euclidean coordinates written here, never read from the engine.
Base pyramid (`SQ`): A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,3).
"""
from __future__ import annotations

import json

import pytest

from app.ai.function_route import run_fact_route


def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


def q(fid, quote, **kw):
    return f(fid, "question", quote, role="question", **kw)


def run(text, facts):
    return run_fact_route(text, {"facts": json.loads(json.dumps(facts))})


SQ = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
SQF = [f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
       f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=list("ABCD"), shape="square", value="2"),
       f("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
       f("f4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3")]


def served(r, answers):
    assert r.status == "SERVED", (r.code, r.reason)
    assert r.answers == answers, r.answers


def refused(r, *codes):
    assert r.status == "REFUSED" and not r.answers and r.scene3d is None, (r.status, r.answers)
    assert not codes or r.code in codes, (r.code, r.reason)


# ── SG-1: a segment label is a whole word, never two letters inside S.ABCD / ABCD ─────────────────────────────────────
RECT_TAIL = " SA vuông góc với (ABCD) và SA = 1. Tính thể tích khối chóp S.ABCD."


def rect(sentence, lengths):
    return run(sentence + RECT_TAIL, [
        f("f1", "solid", sentence, solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", sentence, points=list("ABCD"), shape="rectangle"),
        *[f(f"l{i}", "length", sentence, points=list(p), measure="segment", value=v) for i, (p, v) in enumerate(lengths)],
        f("f5", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
        f("f6", "length", "SA = 1", points=["S", "A"], measure="segment", value="1"),
        q("q", "Tính thể tích khối chóp S.ABCD.", quantity="volume", solid="S.ABCD")])


@pytest.mark.parametrize("sentence,lengths", [
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2 và BC = 3.", [("AB", "2"), ("BC", "3")]),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, BC = 3, AB = 2.", [("AB", "2"), ("BC", "3")]),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2, BC = 3, CD = 2, DA = 3.",
     [("AB", "2"), ("BC", "3"), ("CD", "2"), ("DA", "3")]),
])
def test_sg1_segment_values_bind_to_the_atomic_label(sentence, lengths):
    served(rect(sentence, lengths), {"q": "2"})                       # V = ⅓ · 2 · 3 · 1


@pytest.mark.parametrize("sentence,lengths,codes", [
    # BC never named on its own in the quote: no value may borrow AB's number. Refused on 6973c4b6; the atomic-label change
    # alone SERVED it (one-number fallback) until the role guard `_doan_theo_vai_tro` — this case caught that regression.
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2.", [("AB", "2"), ("BC", "2")], ("UNGROUNDED_VALUE",)),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2 và BC = 3.", [("AB", "3"), ("BC", "2")],
     ("UNGROUNDED_VALUE",)),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 2, BC = 3, CD = 5, DA = 3.",
     [("AB", "2"), ("BC", "3"), ("CD", "5"), ("DA", "3")], ("INCONSISTENT_FACTS",)),
])
def test_sg1_spoofed_or_swapped_segment_values_are_refused(sentence, lengths, codes):
    refused(rect(sentence, lengths), *codes)


@pytest.mark.parametrize("quote,seg,codes", [
    ("Đáy ABCD là hình vuông cạnh 2.", ["S", "A"], ("UNGROUNDED_VALUE",)),   # a lateral edge is not the base's "cạnh"
    ("Cạnh bên bằng 2.", ["A", "B"], ("UNGROUNDED_VALUE",)),                 # "cạnh bên" is not a base side
])
def test_sg1_a_role_noun_grounds_only_segments_of_that_role(quote, seg, codes):
    t = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). Cạnh bên bằng 2. "
    facts = SQF[:3] + [f("x", "length", quote, points=seg, measure="segment", value="2"),
                       q("q", "Tính độ dài SC.", quantity="length", points=["S", "C"])]
    refused(run(t + "Tính độ dài SC.", facts), *codes)


# ── SG-2: 2a is not 2 — the shape reader's coefficient keeps its parameter ────────────────────────────────────────────
def local_given(premise_side, ask_side, sa):
    t = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {premise_side}, SA vuông góc với (ABCD), SA = {sa}. "
    ask = f"Biết đáy ABCD là hình vuông cạnh {ask_side}, tính độ dài SC."
    return run(t + ask, [f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
                         f("f2", "polygon_shape", f"đáy ABCD là hình vuông cạnh {premise_side}", points=list("ABCD"),
                           shape="square", value=premise_side),
                         f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
                         f("f4", "length", f"SA = {sa}", points=["S", "A"], measure="segment", value=sa),
                         q("q", ask, quantity="length", points=["S", "C"])])


def test_sg2_symbolic_local_given_is_read_like_its_numeric_twin():
    served(local_given("2", "2", "3"), {"q": "√17"})                 # SC² = 4 + 4 + 9
    served(local_given("2a", "2a", "3a"), {"q": "a√17"})


@pytest.mark.parametrize("premise,ask,sa", [("2a", "2", "3a"), ("2", "2a", "3")])
def test_sg2_a_restated_measure_that_drops_or_adds_the_parameter_is_refused(premise, ask, sa):
    refused(local_given(premise, ask, sa), "QUESTION_LOCAL_GIVEN_UNVERIFIED")


@pytest.mark.parametrize("premise,ask,serve", [
    # "cạnh a" (no coefficient): the shape reader keeps no value; the side token is read and compared all the same
    ("a", "a", "a√2/2"), ("2", "a", None), ("a", "2a", None), ("a", "1", None)])
def test_sg2_a_side_written_without_a_coefficient(premise, ask, serve):
    t = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {premise}, SA vuông góc với (ABCD), SA = {premise}. "
    a = f"Biết đáy ABCD là hình vuông cạnh {ask}, tính khoảng cách từ A đến (SBC)."
    r = run(t + a, [f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
                    f("f2", "polygon_shape", f"đáy ABCD là hình vuông cạnh {premise}", points=list("ABCD"), shape="square",
                      value=premise),
                    f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
                    f("f4", "length", f"SA = {premise}", points=["S", "A"], measure="segment", value=premise),
                    q("q", a, quantity="distance", points_a=["A"], points_b=["S", "B", "C"])])
    if serve:
        served(r, {"q": serve})                                        # d²(A, (SBC)) = 1/2 at a = 1
    else:
        refused(r, "QUESTION_LOCAL_GIVEN_UNVERIFIED")


def test_sg2_a_fact_value_without_the_source_parameter_is_refused():
    t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 3a. "
    r = run(t + "Tính độ dài SC.", [
        f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2a", points=list("ABCD"), shape="square", value="2"),
        f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
        f("f4", "length", "SA = 3a", points=["S", "A"], measure="segment", value="3a"),
        q("q", "Tính độ dài SC.", quantity="length", points=["S", "C"])])
    refused(r, "UNGROUNDED_VALUE")


def cube_line_ref(text_edge, fact_edge):
    cube = f"Cho hình lập phương ABCD.A'B'C'D' cạnh {text_edge}."
    gt = "Tìm giao tuyến của (A'BD) và (ABCD)."
    ask = "Tính khoảng cách từ C đến giao tuyến của (A'BD) và (ABCD)."
    return run(f"{cube} {gt} {ask}", [
        f("f1", "solid", cube, solid="ABCD.A'B'C'D'", solid_type="cube"),
        f("f2", "length", cube, solid="ABCD.A'B'C'D'", measure="edge", value=fact_edge),
        f("g", "intersection_line", gt, role="question", points_a=["A'", "B", "D"], points_b=list("ABCD")),
        q("q", ask, quantity="distance", points_a=["C"], line_ref="g")])


def test_sg2_cube_edge_with_a_parameter_on_the_line_ref_path():
    served(cube_line_ref("2", "2"), {"q": "√2"})                     # (A'BD) ∩ (ABCD) = BD; d(C, BD) = half the diagonal
    served(cube_line_ref("2a", "2a"), {"q": "a√2"})
    refused(cube_line_ref("2a", "2"))                                # the closed slice compares (value², parameter)


# ── SG-3: several values in one sentence, each bound to its own role noun ─────────────────────────────────────────────
def regular(sentence, base, height):
    return run(sentence + " Tính thể tích khối chóp S.ABCD.", [
        f("f1", "solid", sentence, solid="S.ABCD", solid_type="pyramid", regular=True),
        f("f2", "length", sentence, measure="base_edge", value=base, solid="S.ABCD"),
        f("f3", "length", sentence, measure="height", value=height, solid="S.ABCD"),
        q("q", "Tính thể tích khối chóp S.ABCD.", quantity="volume", solid="S.ABCD")])


@pytest.mark.parametrize("sentence,base,height,v", [
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao bằng 5a.", "4a", "5a", "80a³/3"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và chiều cao bằng 5.", "4", "5", "80/3"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a, chiều cao bằng 5a.", "4a", "5a", "80a³/3"),
    ("Cho hình chóp tứ giác đều S.ABCD có chiều cao bằng 5a và cạnh đáy bằng 4a.", "4a", "5a", "80a³/3"),
])
def test_sg3_each_number_binds_to_its_role(sentence, base, height, v):
    served(regular(sentence, base, height), {"q": v})                 # V = ⅓ · 16 · 5


@pytest.mark.parametrize("sentence,base,height,codes", [
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao bằng 5a.", "5a", "4a", ("UNGROUNDED_VALUE",)),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao bằng 5a.", "4", "5a", ("UNGROUNDED_VALUE",)),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy và chiều cao lần lượt bằng 4a, 5a.", "4a", "5a", ("AMBIGUOUS_VALUE_QUOTE",)),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao lớn hơn 5a.", "4a", "5a", ("AMBIGUOUS_VALUE_QUOTE",)),
    ("Cho hình chóp tứ giác đều S.ABCD có chiều cao bằng 5a và chiều cao bằng 6a.", "4a", "5a", ("AMBIGUOUS_VALUE_QUOTE",)),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao bằng 5a hoặc 6a.", "4a", "5a", ()),
    ("Nếu hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4a và chiều cao bằng 5a.", "4a", "5a", ("CONDITIONAL_CLAUSE",)),
])
def test_sg3_swapped_unbound_or_conflicting_values_are_refused(sentence, base, height, codes):
    refused(regular(sentence, base, height), *codes)


# ── SG-4: "đỉnh"/"điểm" before a named point, "với"/"và" between operands, in every goal contract ──────────────────────
MID_S = dict(quantity="length", point_kind="midpoint", points=["B", "C"], points_b=["S"])
TRI_SA = dict(quantity="area", point_kind="midpoint", points=["B", "C"], points_b=["S", "A"])


@pytest.mark.parametrize("ask,kw,v", [
    ("Tính độ dài đoạn nối đỉnh S với trung điểm của BC.", MID_S, "√14"),           # M(2,1,0): 4 + 1 + 9
    ("Tính độ dài đoạn nối trung điểm của BC với đỉnh S.", MID_S, "√14"),
    ("Tính độ dài đoạn nối trung điểm của BC và điểm S.", MID_S, "√14"),
    ("Tính độ dài đoạn thẳng nối điểm S và trung điểm của BC.", MID_S, "√14"),
    ("Tính diện tích tam giác tạo bởi trung điểm của BC với hai điểm S, A.", TRI_SA, "3√5/2"),   # ½|(2,1,0)×(0,0,3)|
    ("Tính diện tích tam giác tạo bởi trung điểm của BC cùng với hai đỉnh S và A.", TRI_SA, "3√5/2"),
    ("Tính diện tích tam giác có ba đỉnh là trung điểm của BC, điểm S và điểm A.", TRI_SA, "3√5/2"),
])
def test_sg4_wording_alternatives_bind_the_same_operands(ask, kw, v):
    served(run(SQ + ask, SQF + [q("q", ask, **kw)]), {"q": v})


@pytest.mark.parametrize("ask,kw,codes", [
    ("Tính độ dài đoạn nối đỉnh S với trung điểm của BC.", {**MID_S, "points_b": ["A"]}, ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính độ dài đoạn nối đỉnh S với trung điểm của BC.", {**MID_S, "points": ["C", "D"]}, ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính độ dài đoạn nối đỉnh S với trung điểm của BC.",
     {**MID_S, "point_kind": "centroid", "points": ["S", "B", "C"]}, ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính diện tích tam giác tạo bởi trung điểm của BC với hai điểm S, A.", {**TRI_SA, "points_b": ["S", "D"]},
     ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính độ dài đoạn nối đỉnh S với trung điểm của BC.", {**MID_S, "points_b": ["S", "A"]}, ("FACT_INCOMPLETE",)),
    ("Tính độ dài đoạn nối mặt phẳng (SAB) với trung điểm của BC.", MID_S, ("SOURCE_OBJECT_MISMATCH",)),
    ("Không cần tính độ dài đoạn nối đỉnh S với trung điểm của BC.", MID_S, ()),
])
def test_sg4_unasked_or_mistyped_operands_are_refused(ask, kw, codes):
    refused(run(SQ + ask, SQF + [q("q", ask, **kw)]), *codes)


# ── SG-5: several requests, each answered or the whole problem refused ────────────────────────────────────────────────
def asks(ask, items):
    return run(SQ + ask, SQF + [q(i, ask, **kw) for i, kw in items])


L = lambda *p: dict(quantity="length", points=list(p))  # noqa: E731


@pytest.mark.parametrize("ask,items,answers", [
    ("Tính độ dài SB và tính độ dài SC.", [("q1", L("S", "B")), ("q2", L("S", "C"))], {"q1": "√13", "q2": "√17"}),
    ("Tính độ dài SB, đồng thời tính độ dài SC.", [("q1", L("S", "B")), ("q2", L("S", "C"))], {"q1": "√13", "q2": "√17"}),
    ("Tính độ dài SB và hãy tính độ dài SC.", [("q1", L("S", "B")), ("q2", L("S", "C"))], {"q1": "√13", "q2": "√17"}),
    ("Tính độ dài SB và SC.", [("q1", L("S", "B")), ("q2", L("S", "C"))], {"q1": "√13", "q2": "√17"}),
    ("Tính độ dài SB. Tính độ dài SC.", [("q1", L("S", "B")), ("q2", L("S", "C"))], {"q1": "√13", "q2": "√17"}),
    ("Tính độ dài SB, tính độ dài SC và tính độ dài SD.", [("q1", L("S", "B")), ("q2", L("S", "C")), ("q3", L("S", "D"))],
     {"q1": "√13", "q2": "√17", "q3": "√13"}),
    ("Tính độ dài SB và tính thể tích khối chóp S.ABCD.",
     [("q1", L("S", "B")), ("q2", dict(quantity="volume", solid="S.ABCD"))], {"q1": "√13", "q2": "4"}),
])
def test_sg5_every_request_of_a_list_is_answered(ask, items, answers):
    served(asks(ask, items), answers)


@pytest.mark.parametrize("ask,items,codes", [
    ("Tính độ dài SB và tính độ dài SC.", [("q1", L("S", "B"))], ("REQUEST_NOT_ANSWERED",)),        # no partial serve
    ("Tính độ dài SB và tính độ dài SC.", [("q1", L("S", "B")), ("q2", L("S", "D"))], ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính độ dài SB và tính bình phương độ dài SC.", [("q1", L("S", "B")), ("q2", L("S", "C"))], ()),
    ("Tính độ dài SB và tính độ dài SC nếu SC = 5.", [("q1", L("S", "B")), ("q2", L("S", "C"))], ()),
    ("Tính độ dài SB và chứng minh SC vuông góc với BD.", [("q1", L("S", "B"))], ()),
])
def test_sg5_missing_unasked_or_conditional_requests_are_refused(ask, items, codes):
    refused(asks(ask, items), *codes)


# ── SG-6: line_ref with a four-vertex face, the intersection named as the target of the question ─────────────────────
def distance_to_intersection(ask, a, b, point="A", consumer_line_ref=True):
    target = dict(line_ref="g") if consumer_line_ref else dict(points_b=list("SCD"))
    return run(SQ + ask, SQF + [f("g", "intersection_line", ask, role="question", points_a=list(a), points_b=list(b)),
                                q("q", ask, quantity="distance", points_a=[point], **target)])


@pytest.mark.parametrize("ask,a,b,point,v", [
    ("Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD).", "SCD", "ABCD", "A", "2"),       # line CD: y = 2, z = 0
    ("Tính khoảng cách từ A đến giao tuyến của (SBC) và (ABCD).", "SBC", "ABCD", "A", "2"),       # line BC: x = 2, z = 0
    ("Tính khoảng cách từ A đến giao tuyến của (SAB) và (SCD).", "SAB", "SCD", "A", "3"),         # through S, ∥ AB
    ("Tính khoảng cách từ điểm A tới giao tuyến của (SCD) và (ABCD).", "SCD", "ABCD", "A", "2"),
    ("Tính khoảng cách từ A đến giao tuyến của mặt phẳng (SCD) và mặt phẳng (ABCD).", "SCD", "ABCD", "A", "2"),
    ("Tính khoảng cách từ S đến giao tuyến của (ABCD) và (SBC).", "ABCD", "SBC", "S", "√13"),     # 2² + 3²
])
def test_sg6_intersection_named_in_the_question_with_a_four_vertex_face(ask, a, b, point, v):
    r = distance_to_intersection(ask, a, b, point)
    served(r, {"q": v})
    assert any(o["type"] == "line3" and o["id"].startswith("gt_") for o in r.scene3d["objects"])


@pytest.mark.parametrize("ask,a,b,point,codes", [
    ("Tính khoảng cách từ S đến giao tuyến của (ABC) và (ABCD).", "ABC", "ABCD", "S", ("CONTAINED_INFINITE_INTERSECTION",)),
    ("Tính khoảng cách từ D đến giao tuyến của (SABC) và (SCD).", "SABC", "SCD", "D", ("NON_COPLANAR_POINTS",)),
    ("Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD).", "SBC", "ABCD", "A", ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD).", "SCD", "ABCD", "B", ("SOURCE_OBJECT_MISMATCH",)),
    ("Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD) khi SA = 4.", "SCD", "ABCD", "A", ("CONDITIONAL_CLAUSE",)),
    ("Không tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD).", "SCD", "ABCD", "A", ()),
    ("Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCA).", "SCD", "ABCA", "A", ("FACT_INCOMPLETE",)),
])
def test_sg6_undetermined_degenerate_or_unbound_intersections_are_refused(ask, a, b, point, codes):
    refused(distance_to_intersection(ask, a, b, point), *codes)


def test_sg6_an_inline_intersection_needs_an_ask_that_reads_it():
    ask = "Tính khoảng cách từ A đến giao tuyến của (SCD) và (ABCD)."
    refused(distance_to_intersection(ask, "SCD", "ABCD", consumer_line_ref=False))


# ── BH2A known regression (P4-D) exposed three more cases of the same groups; renamed wordings here ─────────────────
def inline_described(points, ask="Tính khoảng cách từ trọng tâm của tam giác SAB đến giao tuyến của hai mặt phẳng "
                                 "(SCD) và (ABCD)."):
    return run(SQ + ask, SQF + [f("g", "intersection_line", ask, role="question", points_a=list("SCD"), points_b=list("ABCD")),
                                q("q", ask, quantity="distance", point_kind="centroid", points=list(points), line_ref="g")])


def test_sg6_inline_intersection_from_a_described_point():
    served(inline_described("SAB"), {"q": "√5"})        # G = (2/3, 0, 1); line CD: y = 2, z = 0 ⇒ d² = 2² + 1² = 5
    refused(inline_described("SAD"), "SOURCE_OBJECT_MISMATCH")      # the fact describes another centroid


def test_sg3_a_number_owned_by_a_segment_label_does_not_make_a_role_ambiguous():
    s = "Cho hình lăng trụ tam giác đều MNP.M'N'P' có cạnh đáy bằng 4 và cạnh bên MM' = 2."
    ask = "Tính thể tích khối lăng trụ MNP.M'N'P'."
    facts = [f("f1", "solid", s, solid="MNP.M'N'P'", solid_type="prism", regular=True),
             f("f2", "length", s, measure="base_edge", solid="MNP.M'N'P'", value="4"),
             f("f3", "length", s, points=["M", "M'"], measure="segment", value="2"),
             q("q", ask, quantity="volume", solid="MNP.M'N'P'")]
    served(run(s + " " + ask, facts), {"q": "8√3"})                 # (√3/4 · 16) · 2
    facts[1]["value"] = "2"                                          # the 2 belongs to MM', not to the base edge
    refused(run(s + " " + ask, facts), "UNGROUNDED_VALUE")


@pytest.mark.parametrize("fact_side,v,codes", [
    ("3", "3√3/2", None),                                            # V = ⅓ · (9√3/4) · 2
    ("2", None, ("UNGROUNDED_VALUE",)),                              # borrows SA's number: not the side
])
def test_sg3_regular_base_side_next_to_a_segment_value(fact_side, v, codes):
    s = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3, SA vuông góc với mặt phẳng (ABC) và SA = 2."
    sa = "2"
    ask = "Tính thể tích khối chóp S.ABC."
    facts = [f("f1", "solid", s, solid="S.ABC", solid_type="pyramid"),
             f("f2", "polygon_shape", s, points=list("ABC"), shape="equilateral_triangle", value=fact_side),
             f("f3", "perpendicular", s, points_a=["S", "A"], points_b=list("ABC")),
             f("f4", "length", s, points=["S", "A"], measure="segment", value=sa), q("q", ask, quantity="volume", solid="S.ABC")]
    r = run(s + " " + ask, facts)
    served(r, {"q": v}) if v else refused(r, *codes)


def test_sg5_a_right_triangle_base_is_a_preserved_premise_of_a_two_request_sentence():
    s0 = "Cho hình chóp T.MNP có đáy MNP là tam giác vuông tại M với MN = 4, MP = 4."
    s1 = "Gọi K là trung điểm của cạnh NP, biết TK vuông góc với MN, TK vuông góc với MP và TK = 3."
    s2 = ("Tính khoảng cách từ trọng tâm của tam giác TMN đến mặt phẳng (MNP) và tính góc giữa hai đường thẳng TK và "
          "NP.")
    facts = [f("f0", "solid", s0, solid="T.MNP", solid_type="pyramid"), f("f1", "right_angle", s0, at="M", points=["N", "P"]),
             f("f2", "length", s0, points=["M", "N"], measure="segment", value="4"),
             f("f3", "length", s0, points=["M", "P"], measure="segment", value="4"),
             f("f4", "point_def", s1, point="K", point_kind="midpoint", points=["N", "P"]),
             f("f5", "perpendicular", s1, points_a=["T", "K"], points_b=["M", "N"]),
             f("f6", "perpendicular", s1, points_a=["T", "K"], points_b=["M", "P"]),
             f("f7", "length", s1, points=["T", "K"], measure="segment", value="3"),
             q("q1", s2, quantity="distance", point_kind="centroid", points=list("TMN"), points_b=list("MNP")),
             q("q2", s2, quantity="angle", points_a=["T", "K"], points_b=["N", "P"])]
    served(run(" ".join((s0, s1, s2)), facts), {"q1": "1", "q2": "cos²=0"})     # TK ⊥ base: z_G = 3/3; TK ⊥ NP


# ── independent review (REQUEST: INDEPENDENT_REVIEW_FAIL on c228bf4e): a role noun belongs to ONE owner ──────────────────
@pytest.mark.parametrize("sentence,base,height", [
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và tam giác SAB có chiều cao bằng 5.", "4", "5"),   # slant height
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, mặt bên có đường cao bằng 5.", "4", "5"),
    ("Cho hình chóp tứ giác đều S.ABCD có đường cao bằng 5, hình vuông MNPQ có cạnh bằng 4.", "4", "5"),     # another square
])
def test_review_a_role_of_another_object_never_fills_the_slot(sentence, base, height):
    refused(regular(sentence, base, height), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


def test_review_a_single_number_of_another_objects_height_is_refused():
    s0, s1 = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4.", "Tam giác SAB có chiều cao bằng 5."
    ask = "Tính thể tích khối chóp S.ABCD."
    refused(run(f"{s0} {s1} {ask}", [f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid", regular=True),
                                     f("f2", "length", s0, measure="base_edge", solid="S.ABCD", value="4"),
                                     f("f3", "length", s1, measure="height", solid="S.ABCD", value="5"),
                                     q("q", ask, quantity="volume", solid="S.ABCD")]), "UNGROUNDED_VALUE")


@pytest.mark.parametrize("sentence,facts_extra", [
    # "cạnh" followed by a segment label is not the square's side (P2)
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông, cạnh SA bằng 3.", [("AB", "3"), ("SA", "3")]),
    # "cạnh bên SB" grounds SB only, never SA (P1)
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và cạnh bên SB bằng 3.", [("SA", "3")]),
    # "cạnh bên bằng 3" on a pyramid not stated regular: lateral edges need not be equal (P3)
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 và cạnh bên bằng 3.", [("SA", "3")]),
])
def test_review_a_segment_value_needs_its_own_role(sentence, facts_extra):
    shape = dict(value="2") if "cạnh 2" in sentence else {}
    facts = [f("f1", "solid", sentence, solid="S.ABCD", solid_type="pyramid"),
             f("f2", "polygon_shape", sentence, points=list("ABCD"), shape="square", **shape),
             *[f(f"l{i}", "length", sentence, points=list(p), measure="segment", value=v) for i, (p, v) in enumerate(facts_extra)],
             f("f5", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
             q("q", "Tính độ dài SC.", quantity="length", points=["S", "C"])]
    refused(run(sentence + " SA vuông góc với (ABCD). Tính độ dài SC.", facts), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


@pytest.mark.parametrize("sentence", [   # review round 2: no owner inferred from free prose — the sentence must parse
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, SAB là tam giác cân có chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và biết SAB là tam giác có đường cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có chiều cao bằng 5, SAC là tam giác cân có cạnh đáy bằng 4.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và khối hộp có chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có chiều cao bằng 5 và hình lăng trụ có cạnh đáy bằng 4.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và khối nón đỉnh S có chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có chiều cao bằng 5 và (SAB) có cạnh đáy bằng 4.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh bằng 4 và chiều cao bằng 5, đặt cạnh một hình lập phương.",
])
def test_review_round2_a_role_inside_unparsed_prose_binds_nothing(sentence):
    refused(regular(sentence, "4", "5"), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


@pytest.mark.parametrize("sentence", [   # review round 3: "của <solid>" must name the bound solid; trailing opaque clauses
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao của hình chóp T.MNPQ bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao của khối lăng trụ bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và chiều cao của khối lập phương bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đường cao bằng 5, hạ từ S xuống cạnh AB.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao bằng 5, đó là chiều cao của mặt bên.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao bằng 5, hạ từ S xuống AB.",
])
def test_review_round3_a_role_owned_by_another_solid_or_reworded_after_binds_nothing(sentence):
    refused(regular(sentence, "4", "5"), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


def test_review_round3_height_of_another_solid_in_its_own_sentence():
    s0, s1 = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4.", "Chiều cao của lăng trụ MNP.M'N'P' bằng 5."
    ask = "Tính thể tích khối chóp S.ABCD."
    refused(run(f"{s0} {s1} {ask}", [f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid", regular=True),
                                     f("f2", "length", s0, measure="base_edge", solid="S.ABCD", value="4"),
                                     f("f3", "length", s1, measure="height", solid="S.ABCD", value="5"),
                                     q("q", ask, quantity="volume", solid="S.ABCD")]))


@pytest.mark.parametrize("sentence", [   # review round 4: any clause outside the closed grammar unbinds the sentence
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đường cao bằng 5, H là chân của nó trên cạnh AB.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đường cao bằng 5 và M là điểm nó hạ xuống trên AB.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đường cao bằng 5, H là chân của đoạn vừa nêu trên cạnh AB.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đường cao bằng 5, H là chân của đường vuông góc hạ từ S xuống AB.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao của tứ diện bằng 5.",
])
def test_review_round4_no_exemption_for_unread_clauses(sentence):
    refused(regular(sentence, "4", "5"), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


@pytest.mark.parametrize("sentence", [   # review round 5: a face / triangle / projection clause changes the subject
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, mặt bên SAB là tam giác cân và có chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, tam giác SAB cân và có đường cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có chiều cao bằng 5, tam giác SAC cân và có cạnh đáy bằng 4.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, tam giác SMN đều và có chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, mặt bên SAB là tam giác đều và chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, tam giác SAB cân, chiều cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đường cao bằng 5, H là hình chiếu của S lên AB.",
    # review round 6 (debatable, hardened): "và có <role>" right after a point definition
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, G là trọng tâm của tam giác SAB và có đường cao bằng 5.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, M là trung điểm của AB và có chiều cao bằng 5.",
])
def test_review_round5_a_subject_changing_clause_unbinds_the_sentence(sentence):
    refused(regular(sentence, "4", "5"), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


def test_t3_a_premise_sentence_ending_with_its_request_still_binds():
    """Full T3 on 72d1595f: the request part of a one-sentence problem ends the premises (it was read as opaque)."""
    ask = "tính độ dài SC."
    t = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 3, {ask}"
    facts = [f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
             f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2", points=list("ABCD"), shape="square", value="2"),
             f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
             f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3"),
             q("q", ask, quantity="length", points=["S", "C"])]
    served(run(t, facts), {"q": "√17"})


def test_t3_a_named_polygon_with_its_side_binds_that_polygon_only():
    """Full T3 on 72d1595f: "Tam giác ABC đều cạnh 2." binds the named triangle's side (served: test_projection_scene_topology);
    an unlabelled role after such a clause in the same sentence is not bound (the triangle may own it)."""
    s ="Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, tam giác SAB đều cạnh 4 và có chiều cao bằng 5."
    refused(regular(s, "4", "5"), "UNGROUNDED_VALUE", "AMBIGUOUS_VALUE_QUOTE")


@pytest.mark.parametrize("tail", [", nhưng đó là cạnh của tam giác khác", ", đó là ảnh thu nhỏ"])
def test_review_round4_a_labelled_base_side_is_unbound_by_an_unread_clause(tail):
    s = f"Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3{tail}, SA vuông góc với (ABC) và SA = 2."
    ask = "Tính thể tích khối chóp S.ABC."
    refused(run(s + " " + ask, [f("f1", "solid", s, solid="S.ABC", solid_type="pyramid"),
                                f("f2", "polygon_shape", s, points=list("ABC"), shape="equilateral_triangle", value="3"),
                                f("f3", "perpendicular", s, points_a=["S", "A"], points_b=list("ABC")),
                                f("f4", "length", s, points=["S", "A"], measure="segment", value="2"),
                                q("q", ask, quantity="volume", solid="S.ABC")]))


@pytest.mark.parametrize("sentence,v", [   # controls: closed point definitions keep the sentence readable
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao bằng 5, H là trung điểm của cạnh AB.", "80/3"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao bằng 5, gọi O là tâm của đáy ABCD.", "80/3"),
])
def test_review_round4_closed_point_definitions_keep_roles(sentence, v):
    served(regular(sentence, "4", "5"), {"q": v})


@pytest.mark.parametrize("sentence,v", [   # controls: the solid's own roles still bind
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao của hình chóp bằng 5.", "80/3"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao của hình chóp S.ABCD bằng 5.", "80/3"),
])
def test_review_round3_own_solid_roles_still_bind(sentence, v):
    served(regular(sentence, "4", "5"), {"q": v})


@pytest.mark.parametrize("height_sentence", ["Đường cao của mặt bên bằng 5.", "Chiều cao của tam giác SAB bằng 5."])
def test_review_round2_a_height_of_another_object_is_refused(height_sentence):
    s0 = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4."
    ask = "Tính thể tích khối chóp S.ABCD."
    refused(run(f"{s0} {height_sentence} {ask}", [
        f("f1", "solid", s0, solid="S.ABCD", solid_type="pyramid", regular=True),
        f("f2", "length", s0, measure="base_edge", solid="S.ABCD", value="4"),
        f("f3", "length", height_sentence, measure="height", solid="S.ABCD", value="5"),
        q("q", ask, quantity="volume", solid="S.ABCD")]), "UNGROUNDED_VALUE")


def test_review_lateral_edge_of_a_regular_pyramid_still_serves():
    s = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2 và cạnh bên bằng 3."
    r = run(s + " Tính độ dài SC.", [f("f1", "solid", s, solid="S.ABCD", solid_type="pyramid", regular=True),
                                     f("f2", "length", s, measure="base_edge", solid="S.ABCD", value="2"),
                                     f("f3", "length", s, measure="lateral_edge", solid="S.ABCD", value="3"),
                                     q("q", "Tính độ dài SC.", quantity="length", points=["S", "C"])])
    served(r, {"q": "3"})


# ── independent review of 81e91ebb: the shape noun must name as many vertices as the polygon has ───────────────────────
def right_prism(sentence, shape, base):
    top = "".join(c + "'" for c in base)
    sol = f"{base}.{top}"
    ask = f"Tính thể tích khối lăng trụ {sol}."
    return run(f"Cho lăng trụ đứng {sol} có AA' = 3. {sentence} {ask}", [
        f("f1", "solid", f"Cho lăng trụ đứng {sol}", solid=sol, solid_type="prism", right=True),
        f("f4", "length", "AA' = 3", points=["A", "A'"], measure="segment", value="3"),
        f("f2", "polygon_shape", sentence, points=list(base), shape=shape, value="2"),
        q("q", ask, quantity="volume", solid=sol)])


TRI, SQ4, HEX = ("equilateral_triangle", "ABC"), ("square", "ABCD"), ("regular_hexagon", "ABCDEF")


@pytest.mark.parametrize("sentence,spec", [
    ("Hình vuông ABC cạnh 2.", TRI), ("Hình vuông ABC có cạnh bằng 2.", TRI), ("Tam giác ABC là hình vuông cạnh 2.", TRI),
    ("Tam giác ABC là lục giác đều cạnh 2.", TRI), ("Lục giác ABC đều cạnh 2.", TRI),
    ("Tam giác ABCD đều cạnh 2.", SQ4), ("Lục giác ABCD đều cạnh 2.", SQ4),
    ("Hình vuông ABCDEF cạnh 2.", HEX), ("Tam giác ABCDEF đều cạnh 2.", HEX),
    # the same contradiction through the base clause (served on 1beeec0b as well)
    ("Đáy ABC là hình vuông cạnh 2.", TRI), ("Đáy ABC là lục giác đều cạnh 2.", TRI), ("Đáy ABCD là tam giác đều cạnh 2.", SQ4),
])
def test_review_t3_a_shape_noun_with_the_wrong_vertex_count_is_refused(sentence, spec):
    refused(right_prism(sentence, *spec))


@pytest.mark.parametrize("sentence,spec,v", [
    ("Tam giác ABC đều cạnh 2.", TRI, "3√3"), ("Tam giác ABC là tam giác đều có cạnh bằng 2.", TRI, "3√3"),
    ("Đáy ABC là tam giác đều cạnh 2.", TRI, "3√3"), ("Hình vuông ABCD cạnh 2.", SQ4, "12"),
    ("Đáy ABCD là hình vuông cạnh 2.", SQ4, "12"), ("Lục giác ABCDEF đều cạnh 2.", HEX, "18√3"),
])
def test_review_t3_a_shape_noun_with_the_right_vertex_count_is_served(sentence, spec, v):
    served(right_prism(sentence, *spec), {"q": v})


def test_review_t3b_legacy_unlabelled_base_shape_must_match_the_base():
    """Review of b6a9fcc6 (a): "Đáy là tam giác đều" resolved to the 4-vertex base S.ABCD (and "tứ giác đều" to ABC)."""
    for solid, base, shape, noun in (("S.ABCD", "ABCD", "square", "tam giác"), ("S.ABC", "ABC", "equilateral_triangle", "tứ giác")):
        s1, s2 = f"Cho hình chóp {solid} có cạnh đáy bằng 2", f"Đáy là {noun} đều"
        ask = f"Tính thể tích khối chóp {solid}."
        r = run(f"{s1}. {s2}. SA vuông góc với ({base}) và SA = 3. {ask}", [
            f("f1", "solid", f"Cho hình chóp {solid}", solid=solid, solid_type="pyramid"),
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": [s1, s2], "points": list(base), "shape": shape,
             "value": "2"},
            f("f3", "perpendicular", f"SA vuông góc với ({base})", points_a=["S", "A"], points_b=list(base)),
            f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3"),
            q("q", ask, quantity="volume", solid=solid)])
        refused(r)


def test_review_t3b_a_cube_does_not_have_triangular_faces():
    s = "Cho hình lập phương ABC.A'B'C' cạnh 2."
    ask = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    refused(run(f"{s} {ask}", [
        f("f1", "solid", s, solid="ABC.A'B'C'", solid_type="prism", right=True),
        f("f2", "polygon_shape", s, points=list("ABC"), shape="equilateral_triangle", value="2"),
        f("f3", "length", s, points=["A", "A'"], measure="segment", value="2"),
        q("q", ask, quantity="volume", solid="ABC.A'B'C'")]))


def test_review_t3b_every_mention_of_the_polygon_is_count_checked():
    refused(right_prism("Đáy ABC đều cạnh 2, và đáy ABC là hình vuông.", *TRI))


@pytest.mark.parametrize("solid,sentence,base,height", [
    ("S.ABC", "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, đáy là hình vuông và chiều cao bằng 3.", "2", "3"),
    ("S.ABC", "Cho hình chóp tam giác đều S.ABC có đáy là hình vuông, cạnh đáy bằng 2 và chiều cao bằng 3.", "2", "3"),
    ("S.ABCD", "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đáy là tam giác đều và chiều cao bằng 5.", "4", "5"),
])
def test_review_t3c_an_unlabelled_base_noun_contradicting_the_solid_binds_nothing(solid, sentence, base, height):
    """Review of 08bad12f: a number-free "đáy là <shape>" names the bound solid's base; a wrong count unreads the sentence."""
    ask = f"Tính thể tích khối chóp {solid}."
    refused(run(f"{sentence} {ask}", [
        f("f1", "solid", sentence, solid=solid, solid_type="pyramid", regular=True),
        f("f2", "length", sentence, measure="base_edge", value=base, solid=solid),
        f("f3", "length", sentence, measure="height", value=height, solid=solid),
        q("q", ask, quantity="volume", solid=solid)]))


def test_review_t3c_regular_prism_with_a_contradicting_base_noun():
    s = "Cho hình lăng trụ tam giác đều MNP.M'N'P' có cạnh đáy bằng 4, đáy là hình vuông và cạnh bên MM' = 2."
    ask = "Tính thể tích khối lăng trụ MNP.M'N'P'."
    refused(run(f"{s} {ask}", [
        f("f1", "solid", s, solid="MNP.M'N'P'", solid_type="prism", regular=True),
        f("f2", "length", s, measure="base_edge", value="4", solid="MNP.M'N'P'"),
        f("f3", "length", s, points=["M", "M'"], measure="segment", value="2"),
        q("q", ask, quantity="volume", solid="MNP.M'N'P'")]))


@pytest.mark.parametrize("sentence", ["Đáy ABC đều cạnh 2 và đáy là hình vuông.", "Đáy ABC đều cạnh 2 và mặt đáy là hình vuông.",
                                      "Đáy ABC là tam giác đều cạnh 2, đáy là lục giác đều."])
def test_review_t3c_a_later_unlabelled_base_noun_is_count_checked(sentence):
    refused(right_prism(sentence, *TRI))


@pytest.mark.parametrize("sentence,v", [
    ("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, đáy là tam giác đều và chiều cao bằng 3.", "√3"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, đáy là hình vuông và chiều cao bằng 5.", "80/3"),
])
def test_review_t3c_a_consistent_unlabelled_base_noun_is_still_served(sentence, v):
    solid = "S.ABCD" if "S.ABCD" in sentence else "S.ABC"
    base, height = ("4", "5") if solid == "S.ABCD" else ("2", "3")
    ask = f"Tính thể tích khối chóp {solid}."
    served(run(f"{sentence} {ask}", [
        f("f1", "solid", sentence, solid=solid, solid_type="pyramid", regular=True),
        f("f2", "length", sentence, measure="base_edge", value=base, solid=solid),
        f("f3", "length", sentence, measure="height", value=height, solid=solid),
        q("q", ask, quantity="volume", solid=solid)]), {"q": v})


# ── review of 6f58c0f5: the vertex-count check is a SOURCE-level gate, whatever path grounds the values ─────────────────
PRISM_T3 = "Cho lăng trụ đứng ABC.A'B'C' có AA' = 3. "
ASK_T3 = "Tính thể tích khối lăng trụ ABC.A'B'C'."


def prism_t3(body, extra, solid_quotes=("Cho lăng trụ đứng ABC.A'B'C'",)):
    return run(PRISM_T3 + body + ASK_T3, [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": list(solid_quotes), "solid": "ABC.A'B'C'",
         "solid_type": "prism", "right": True},
        f("f4", "length", "AA' = 3", points=["A", "A'"], measure="segment", value="3"), *extra,
        q("q", ASK_T3, quantity="volume", solid="ABC.A'B'C'")])


def test_review_t3d_contradicting_base_noun_with_labelled_segment_values():
    s = "Đáy ABC là tam giác đều và đáy là hình vuông, AB = 2. "
    refused(prism_t3(s, [f("f2", "polygon_shape", s.strip(), points=list("ABC"), shape="equilateral_triangle"),
                         f("f3", "length", s.strip(), points=["A", "B"], measure="segment", value="2")]))
    s1, s2 = "Đáy ABC là tam giác đều và đáy là hình vuông.", "AB = 2."
    refused(prism_t3(f"{s1} {s2} ", [f("f2", "polygon_shape", s1, points=list("ABC"), shape="equilateral_triangle"),
                                     f("f3", "length", s2, points=["A", "B"], measure="segment", value="2")]))


def test_review_t3d_contradicting_base_noun_in_another_quoted_sentence():
    s1, s2 = "Đáy ABC là tam giác đều cạnh 2.", "Đáy là hình vuông."
    refused(prism_t3(f"{s1} {s2} ", [f("f2", "polygon_shape", s1, points=list("ABC"), shape="equilateral_triangle",
                                       value="2")], solid_quotes=("Cho lăng trụ đứng ABC.A'B'C'", s2)))
    refused(prism_t3(f"{s1} {s2} ", [{"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": [s1, s2],
                                      "points": list("ABC"), "shape": "equilateral_triangle", "value": "2"}]))


@pytest.mark.parametrize("s,solid,segs,ask,quantity", [
    ("Cho hình chóp tam giác đều S.ABC có đáy là hình vuông, AB = 2 và SA = 3.", "S.ABC", [("AB", "2"), ("SA", "3")],
     "Tính thể tích khối chóp S.ABC.", {"quantity": "volume", "solid": "S.ABC"}),
    ("Cho hình chóp tứ giác đều S.ABCD có đáy là tam giác đều, AB = 4 và SA = 5.", "S.ABCD", [("AB", "4"), ("SA", "5")],
     "Tính độ dài SC.", {"quantity": "length", "points": ["S", "C"]}),
])
def test_review_t3d_regular_pyramid_with_labelled_segments_and_a_contradicting_base(s, solid, segs, ask, quantity):
    refused(run(f"{s} {ask}", [f("f1", "solid", s, solid=solid, solid_type="pyramid", regular=True),
                               *[f(f"l{i}", "length", s, points=list(p), measure="segment", value=v)
                                 for i, (p, v) in enumerate(segs)],
                               q("q", ask, **quantity)]))


@pytest.mark.parametrize("second", ["Đáy là hình vuông.", "Mặt đáy của nó là hình vuông."])
def test_review_t3d_regular_pyramid_with_a_contradicting_second_sentence(second):
    s1 = "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2 và chiều cao bằng 3."
    ask = "Tính thể tích khối chóp S.ABC."
    refused(run(f"{s1} {second} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, second], "solid": "S.ABC", "solid_type": "pyramid",
         "regular": True},
        f("f2", "length", s1, measure="base_edge", value="2", solid="S.ABC"),
        f("f3", "length", s1, measure="height", value="3", solid="S.ABC"),
        q("q", ask, quantity="volume", solid="S.ABC")]))


def test_review_t3d_consistent_wordings_still_served():
    s1, s2 = "Đáy ABC là tam giác đều.", "AB = 2."
    served(prism_t3(f"{s1} {s2} ", [f("f2", "polygon_shape", s1, points=list("ABC"), shape="equilateral_triangle"),
                                    f("f3", "length", s2, points=["A", "B"], measure="segment", value="2")]), {"q": "3√3"})
    s1 = "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2 và chiều cao bằng 3."
    ask = "Tính thể tích khối chóp S.ABC."
    served(run(f"{s1} Đáy là tam giác đều. {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, "Đáy là tam giác đều."], "solid": "S.ABC",
         "solid_type": "pyramid", "regular": True},
        f("f2", "length", s1, measure="base_edge", value="2", solid="S.ABC"),
        f("f3", "length", s1, measure="height", value="3", solid="S.ABC"),
        q("q", ask, quantity="volume", solid="S.ABC")]), {"q": "√3"})


# ── review of 57701200: every count noun is attributed; an unattributable base / solid noun is checked or refused ───────
def test_review_t3e_single_sentence_hinh_tu_giac_base_with_labelled_segments():
    s = "Cho hình chóp tam giác đều S.ABC có đáy là hình tứ giác đều, AB = 2 và SA = 3."
    ask = "Tính thể tích khối chóp S.ABC."
    refused(run(f"{s} {ask}", [f("f1", "solid", s, solid="S.ABC", solid_type="pyramid", regular=True),
                               f("l1", "length", s, points=["A", "B"], measure="segment", value="2"),
                               f("l2", "length", s, points=["S", "A"], measure="segment", value="3"),
                               q("q", ask, quantity="volume", solid="S.ABC")]))


def regular_two_sentences(second):
    s1 = "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2 và chiều cao bằng 3."
    ask = "Tính thể tích khối chóp S.ABC."
    return run(f"{s1} {second} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, second], "solid": "S.ABC", "solid_type": "pyramid",
         "regular": True},
        f("f2", "length", s1, measure="base_edge", value="2", solid="S.ABC"),
        f("f3", "length", s1, measure="height", value="3", solid="S.ABC"),
        q("q", ask, quantity="volume", solid="S.ABC")])


@pytest.mark.parametrize("second", [
    "Đáy là hình tứ giác đều.", "Đáy là hình lục giác đều.", "Đáy của khối là hình vuông.", "Đáy của chóp là hình vuông.",
    "Đáy của hình chóp đó là hình vuông.", "Hình chóp S.ABC là hình chóp tứ giác đều.", "S.ABC là hình chóp tứ giác.",
    "Đáy nó là hình vuông.", "Đáy có dạng hình vuông.", "Mặt đáy vốn là hình vuông.", "Đáy là tứ-giác đều."])
def test_review_t3e_a_base_or_solid_noun_in_any_wording_is_count_checked(second):
    refused(regular_two_sentences(second))


@pytest.mark.parametrize("second", ["Đáy là hình tam giác đều.", "Các mặt bên là tam giác cân.",
                                    "S.ABC là hình chóp tam giác đều."])
def test_review_t3e_consistent_or_lateral_face_nouns_still_served(second):
    served(regular_two_sentences(second), {"q": "√3"})


def test_review_t3e_square_pyramid_with_triangular_lateral_faces_still_served():
    """A lateral-face noun ("tam giác") names no base: a 3-noun beside a 4-vertex base is not a contradiction."""
    s1, s2 = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và chiều cao bằng 5.", "Các mặt bên là tam giác cân."
    ask = "Tính thể tích khối chóp S.ABCD."
    served(run(f"{s1} {s2} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, s2], "solid": "S.ABCD", "solid_type": "pyramid",
         "regular": True},
        f("f2", "length", s1, measure="base_edge", value="4", solid="S.ABCD"),
        f("f3", "length", s1, measure="height", value="5", solid="S.ABCD"),
        q("q", ask, quantity="volume", solid="S.ABCD")]), {"q": "80/3"})


# ── review of c6592ac2: fail-closed attribution — a base noun agrees with its label AND the solid; unattributed refuses ──
def regular_segments(s, ask="Tính thể tích khối chóp S.ABC."):
    return run(f"{s} {ask}", [f("f1", "solid", s, solid="S.ABC", solid_type="pyramid", regular=True),
                              f("l1", "length", s, points=["A", "B"], measure="segment", value="2"),
                              f("l2", "length", s, points=["S", "A"], measure="segment", value="3"),
                              q("q", ask, quantity="volume", solid="S.ABC")])


@pytest.mark.parametrize("s", [
    "Cho hình chóp tam giác đều S.ABC có đáy là hình vuông ABCD, AB = 2 và SA = 3.",
    "Cho hình chóp tam giác đều S.ABC có đáy là hình vuông MNPQ, AB = 2 và SA = 3.",
    "Cho hình chóp tam giác đều S.ABC có AB = 2 và SA = 3 và đáy bên dưới là hình tứ giác đều.",
    "Cho hình chóp tam giác đều S.ABC với hình vuông làm đáy, AB = 2 và SA = 3.",
    "Cho hình chóp tam giác đều S.ABC có AB = 2 và SA = 3, hình vuông là đáy của nó.",
    "Cho hình chóp tam giác đều S.ABC có hình tứ giác đều làm đáy, AB = 2 và SA = 3.",
])
def test_review_t3f_single_sentence_contradictions(s):
    refused(regular_segments(s))


@pytest.mark.parametrize("second", [
    "Hình vuông là đáy của nó.", "Đáy, như đã nói, là hình vuông.", "Đáy bên dưới là hình vuông.",
    "Đáy là tam giác đều và cũng là hình vuông.", "Mặt dưới của khối chóp là hình vuông.", "Phần đáy: hình vuông.",
    "Nó có một hình vuông làm đáy.", "Đáy của nó, thực ra, là tứ giác đều.", "Mặt đáy ở phía bên dưới là hình vuông."])
def test_review_t3f_unattributed_base_nouns_are_refused(second):
    refused(regular_two_sentences(second))


def square_two_sentences(second):
    s1 = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4 và chiều cao bằng 5."
    ask = "Tính thể tích khối chóp S.ABCD."
    return run(f"{s1} {second} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, second], "solid": "S.ABCD", "solid_type": "pyramid",
         "regular": True},
        f("f2", "length", s1, measure="base_edge", value="4", solid="S.ABCD"),
        f("f3", "length", s1, measure="height", value="5", solid="S.ABCD"),
        q("q", ask, quantity="volume", solid="S.ABCD")])


@pytest.mark.parametrize("second", [
    "Hình chiếu của S lên đáy là trọng tâm tam giác ABD.", "Đáy gồm hai tam giác vuông cân ABC và ACD.",
    "Mặt phẳng đáy chứa tam giác ABC.", "Tâm O của đáy là trung điểm cạnh huyền của tam giác vuông cân ABC.",
    "Mặt đáy là hình vuông ABCD.", "Các mặt bên là tam giác cân."])
def test_review_t3f_labelled_or_face_nouns_in_a_base_sentence_are_still_served(second):
    served(square_two_sentences(second), {"q": "80/3"})


# ── review of c3b1f905: base / face / section attributions for common wordings; any unattributed noun refuses ──────────
@pytest.mark.parametrize("s", ["Cho hình chóp tam giác đều S.ABC với tứ giác SABC làm đáy, AB = 2 và SA = 3.",
                               "Cho hình chóp tam giác đều S.ABC với hình vuông SABC làm đáy, AB = 2 và SA = 3."])
def test_review_t3g_a_labelled_polygon_made_the_base_must_match_the_solid(s):
    refused(regular_segments(s))


@pytest.mark.parametrize("second", ["Hình vuông SABC là đáy của nó.", "Mặt dưới của nó là hình vuông.",
                                    "Phần dưới cùng là một hình vuông.", "Ba mặt bên là ba hình vuông."])
def test_review_t3g_more_base_and_face_wordings_are_count_checked(second):
    refused(regular_two_sentences(second))


def regular_prism_two_sentences(second):
    s1 = "Cho hình lăng trụ tam giác đều MNP.M'N'P' có cạnh đáy bằng 4 và cạnh bên MM' = 2."
    ask = "Tính thể tích khối lăng trụ MNP.M'N'P'."
    return run(f"{s1} {second} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, second], "solid": "MNP.M'N'P'",
         "solid_type": "prism", "regular": True},
        f("f2", "length", s1, measure="base_edge", value="4", solid="MNP.M'N'P'"),
        f("f3", "length", s1, points=["M", "M'"], measure="segment", value="2"),
        q("q", ask, quantity="volume", solid="MNP.M'N'P'")])


@pytest.mark.parametrize("second", ["Mặt trên là hình vuông.", "Mặt trên là tứ giác đều."])
def test_review_t3g_a_prism_top_is_count_checked(second):
    refused(regular_prism_two_sentences(second))


def test_review_t3g_a_prism_with_two_equal_triangular_bases_is_served():
    served(regular_prism_two_sentences("Hai đáy là hai tam giác đều bằng nhau."), {"q": "8√3"})


@pytest.mark.parametrize("second", [
    "Hình chiếu của S lên mặt đáy trùng với trọng tâm tam giác đáy.", "Gọi G là trọng tâm của tam giác đáy.",
    "Các mặt bên của hình chóp là các tam giác cân.", "Mỗi mặt bên của khối chóp là một tam giác cân.",
    "Ba mặt bên là ba tam giác cân bằng nhau.", "Tam giác SAB có đáy AB và là tam giác cân."])
def test_review_t3g_common_triangular_pyramid_wordings_are_served(second):
    served(regular_two_sentences(second), {"q": "√3"})


@pytest.mark.parametrize("second", ["Gọi O là tâm của hình vuông đáy.", "Mặt phẳng (SAC) cắt khối chóp theo một tam giác cân.",
                                    "Mỗi mặt bên tạo với đáy một tam giác cân."])
def test_review_t3g_common_square_pyramid_wordings_are_served(second):
    served(square_two_sentences(second), {"q": "80/3"})


@pytest.mark.parametrize("second", ["Mặt phẳng (A'BD) cắt hình lập phương theo thiết diện là một tam giác đều.",
                                    "Các mặt của hình lập phương là hình vuông."])
def test_review_t3g_cube_section_and_face_wordings_are_served(second):
    s1 = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2."
    ask = "Tính thể tích khối lập phương ABCD.A'B'C'D'."
    r = run(f"{s1} {second} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, second], "solid": "ABCD.A'B'C'D'",
         "solid_type": "cube"},
        f("f2", "length", s1, solid="ABCD.A'B'C'D'", measure="edge", value="2"),
        q("q", ask, quantity="volume", solid="ABCD.A'B'C'D'")])
    served(r, {"q": "8"})


# ── review of c7b79cce: ownership from the declared solid; an unidentified face is refused, never passed ───────────────
@pytest.mark.parametrize("s", ["Cho hình chóp tam giác đều S.ABC có AB = 2 và SA = 3, mặt nằm dưới là hình vuông.",
                               "Cho hình chóp tam giác đều S.ABC có AB = 2, SA = 3 và mặt chứa A, B, C là một hình vuông."])
def test_review_t3h_an_unidentified_face_is_refused(s):
    refused(regular_segments(s))


@pytest.mark.parametrize("second", ["Mặt nằm dưới là hình vuông.", "Mặt chứa ba điểm A, B, C là hình vuông.",
                                    "Mặt tiếp đất của nó là một hình vuông.", "Mặt không chứa S là tứ giác đều."])
def test_review_t3h_unidentified_faces_of_a_pyramid(second):
    refused(regular_two_sentences(second))


@pytest.mark.parametrize("second", ["Mặt nằm trên là hình vuông.", "Mặt chứa M, N, P là hình vuông."])
def test_review_t3h_unidentified_faces_of_a_prism(second):
    refused(regular_prism_two_sentences(second))


def test_review_t3h_a_sub_solid_named_in_the_text_does_not_defer_the_base_check():
    s1 = "Cho hình chóp tứ giác đều S.ABCD có đáy là tam giác đều, AB = 4 và SA = 5."
    s2 = "Mặt phẳng (SAC) chia khối chóp thành hai khối chóp S.ABC và S.ACD."
    ask = "Tính độ dài SC."
    refused(run(f"{s1} {s2} {ask}", [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1, s2], "solid": "S.ABCD", "solid_type": "pyramid",
         "regular": True},
        f("l1", "length", s1, points=["A", "B"], measure="segment", value="4"),
        f("l2", "length", s1, points=["S", "A"], measure="segment", value="5"),
        q("q", ask, quantity="length", points=["S", "C"])]))


def test_review_t3h_an_enumeration_of_labelled_triangles_is_served():
    served(regular_two_sentences("Tam giác SAB, SBC, SCA là các tam giác cân."), {"q": "√3"})


# ── review of 26e1040a: "mặt bên dưới/trên" is the bottom/top face, not a lateral face; "(SBC) là" predicates a label ───
def test_review_t3i_bottom_or_top_face_is_not_a_lateral_face():
    s = "Cho hình chóp tứ giác đều S.ABCD có AB = 4, SA = 5 và mặt bên dưới là tam giác đều."
    ask = "Tính độ dài SC."
    refused(run(f"{s} {ask}", [f("f1", "solid", s, solid="S.ABCD", solid_type="pyramid", regular=True),
                               f("l1", "length", s, points=["A", "B"], measure="segment", value="4"),
                               f("l2", "length", s, points=["S", "A"], measure="segment", value="5"),
                               q("q", ask, quantity="length", points=["S", "C"])]))
    for second in ("Mặt bên dưới là tam giác đều.", "Mặt bên phía dưới là tam giác."):
        refused(square_two_sentences(second))
    for second in ("Mặt bên dưới là hình vuông.", "Mặt bên trên là tứ giác đều.", "Mặt bên dưới cùng là một hình vuông."):
        refused(regular_prism_two_sentences(second))


def test_review_t3i_a_parenthesised_face_label_is_served():
    served(regular_two_sentences("Mặt (SBC) là tam giác đều."), {"q": "√3"})
    served(regular_two_sentences("Tam giác ΔSBC là tam giác đều."), {"q": "√3"})
    for bad in ("Tam giác ΔABCD là tam giác đều.", "Hình vuông ΔSBC là tam giác đều.", "ΔSBC là hình vuông."):
        refused(regular_two_sentences(bad))


# ── Follow-up A (P1): multi-goal question boundaries with unnamed-point contracts (SGH-04, SGH-09) ────────────────────
def _seg(fid, quote, seg, v):
    return f(fid, "length", quote, points=list(seg), measure="segment", value=v)


def _sgh04_case(ask_sentence: str | None = None, goals: list[dict] | None = None):
    s0 = "Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 6a và cạnh bên AA' = 3a."
    s1 = ask_sentence or (
        "Tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC) "
        "và tính góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC)."
    )
    qs = goals if goals is not None else [
        q("q1", s1, quantity="distance", point_kind="centroid", points=["A'", "B'", "C'"], points_b=list("ABC")),
        q("q2", s1, quantity="angle", point_kind="midpoint", points=["B", "C"], points_a=["A'"], points_b=list("ABC")),
    ]
    return f"{s0} {s1}", [
        f("f1", "solid", s0, solid="ABC.A'B'C'", solid_type="prism", regular=True),
        f("f2", "length", s0, solid="ABC.A'B'C'", measure="base_edge", value="6a"),
        _seg("f3", s0, ["A", "A'"], "3a"),
        *qs,
    ]


def _sgh09_case(ask_sentence: str | None = None, goals: list[dict] | None = None):
    s0 = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A với AB = 3a, AC = 3a."
    s0b = "Gọi H là trung điểm của cạnh AB, biết SH vuông góc với AB, SH vuông góc với AC và SH = 6a."
    s1 = ask_sentence or (
        "Tính khoảng cách từ trọng tâm của tam giác SBC đến mặt phẳng (ABC) "
        "và tính góc giữa đường thẳng nối đỉnh A với trọng tâm của tam giác SBC và mặt phẳng (ABC)."
    )
    qs = goals if goals is not None else [
        q("q1", s1, quantity="distance", point_kind="centroid", points=list("SBC"), points_b=list("ABC")),
        q("q2", s1, quantity="angle", point_kind="centroid", points=list("SBC"), points_a=["A"], points_b=list("ABC")),
    ]
    return f"{s0} {s0b} {s1}", [
        f("f1", "solid", s0, solid="S.ABC", solid_type="pyramid"),
        f("f1_ra", "right_angle", s0, at="A", points=["B", "C"]),
        _seg("f2", s0, "AB", "3a"),
        _seg("f3", s0, "AC", "3a"),
        f("f4", "point_def", s0b, point="H", point_kind="midpoint", points=["A", "B"]),
        f("f5", "perpendicular", s0b, points_a=["S", "H"], points_b=["A", "B"]),
        f("f6", "perpendicular", s0b, points_a=["S", "H"], points_b=["A", "C"]),
        _seg("f7", s0b, "SH", "6a"),
        *qs,
    ]


@pytest.mark.parametrize("ask_sgh04", [
    "Tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC) và tính góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC).",
    "Tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC) và góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC).",
    "Hãy tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC), đồng thời tính góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC).",
])
def test_followup_a_sgh04_multi_goal_boundaries_served(ask_sgh04):
    text, facts = _sgh04_case(ask_sgh04)
    served(run(text, facts), {"q1": "3a", "q2": "cos²=3/4"})


@pytest.mark.parametrize("ask_sgh09", [
    "Tính khoảng cách từ trọng tâm của tam giác SBC đến mặt phẳng (ABC) và tính góc giữa đường thẳng nối đỉnh A với trọng tâm của tam giác SBC và mặt phẳng (ABC).",
    "Tính khoảng cách từ trọng tâm của tam giác SBC đến mặt phẳng (ABC) và góc giữa đường thẳng nối đỉnh A với trọng tâm của tam giác SBC và mặt phẳng (ABC).",
    "Hãy tính khoảng cách từ trọng tâm của tam giác SBC đến mặt phẳng (ABC), đồng thời tính góc giữa đường thẳng nối đỉnh A với trọng tâm của tam giác SBC và mặt phẳng (ABC).",
])
def test_followup_a_sgh09_multi_goal_boundaries_served(ask_sgh09):
    text, facts = _sgh09_case(ask_sgh09)
    served(run(text, facts), {"q1": "2a", "q2": "cos²=13/29"})


def test_followup_a_negative_controls_stay_refused():
    # 1. Invalid degree unit note on multi-goal sentence -> QUESTION_CONTEXT_UNSUPPORTED
    s_deg = (
        "Tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC) "
        "và tính góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC) (đơn vị: độ)."
    )
    refused(run(*_sgh04_case(s_deg)), "QUESTION_CONTEXT_UNSUPPORTED")

    # 2. Rounding note on multi-goal sentence -> QUESTION_CONTEXT_UNSUPPORTED
    s_round = (
        "Tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC) "
        "và tính góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC), làm tròn đến hàng phần mười."
    )
    refused(run(*_sgh04_case(s_round)), "QUESTION_CONTEXT_UNSUPPORTED")

    # 3. 2 goals in source text, only 1 question extracted in payload -> REQUEST_NOT_ANSWERED
    s_two = (
        "Tính khoảng cách từ trọng tâm của tam giác A'B'C' đến mặt phẳng (ABC) "
        "và tính góc giữa đường thẳng nối đỉnh A' với trung điểm của cạnh BC và mặt phẳng (ABC)."
    )
    only_q1 = [q("q1", s_two, quantity="distance", point_kind="centroid", points=["A'", "B'", "C'"], points_b=list("ABC"))]
    refused(run(*_sgh04_case(s_two, goals=only_q1)), "REQUEST_NOT_ANSWERED")

    # 4. Spoofed plane (A'BC) instead of (ABC) on second goal -> SOURCE_OBJECT_MISMATCH
    spoofed_q2 = [
        q("q1", s_two, quantity="distance", point_kind="centroid", points=["A'", "B'", "C'"], points_b=list("ABC")),
        q("q2", s_two, quantity="angle", point_kind="midpoint", points=["B", "C"], points_a=["A'"], points_b=["A'", "B", "C"]),
    ]
    refused(run(*_sgh04_case(s_two, goals=spoofed_q2)), "SOURCE_OBJECT_MISMATCH")


# ── Follow-up B (P2): compound premise with line_ref (SGH-02, SGH-10, BH2A-03-variant-ABCD) ──────────────────────────
def _sgh02_exact_case():
    p0 = "Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 6a, cạnh bên SM vuông góc với mặt phẳng (MNPQ) và SM = 3a."
    p1 = "Tính khoảng cách từ trọng tâm của tam giác SMN đến giao tuyến của hai mặt phẳng (SPQ) và (MNPQ)."
    return f"{p0} {p1}", [
        f("f1", "solid", p0, solid="S.MNPQ", solid_type="pyramid"),
        f("f2", "polygon_shape", "Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 6a", points=list("MNPQ"), shape="square", value="6a"),
        f("f3", "perpendicular", "cạnh bên SM vuông góc với mặt phẳng (MNPQ)", points_a=["S", "M"], points_b=list("MNPQ")),
        _seg("f4", "SM = 3a.", "SM", "3a"),
        f("f_gt", "intersection_line", p1, points_a=list("SPQ"), points_b=list("MNPQ")),
        q("q1", p1, quantity="distance", point_kind="centroid", points=list("SMN"), line_ref="f_gt"),
    ]


def _sgh10_exact_case():
    p0 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4a, cạnh bên SA vuông góc với mặt phẳng (ABCD) và SA = 4a."
    p1 = "Tính khoảng cách từ trung điểm của cạnh SC đến giao tuyến của hai mặt phẳng (SAB) và (ABCD)."
    return f"{p0} {p1}", [
        f("f1", "solid", p0, solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", p0, points=list("ABCD"), shape="square", value="4a"),
        f("f3", "perpendicular", p0, points_a=["S", "A"], points_b=list("ABCD")),
        _seg("f4", p0, "SA", "4a"),
        f("f_gt", "intersection_line", p1, points_a=list("SAB"), points_b=list("ABCD")),
        q("q1", p1, quantity="distance", point_kind="midpoint", points=["S", "C"], line_ref="f_gt"),
    ]


def _rect_compound_line_ref_case(s0: str | None = None, s1: str | None = None, ab="4a", ad="2a", sa="6a",
                                 planes=(("S", "B", "C"), ("S", "C", "D"))):
    p0 = s0 or "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 4a, AD = 2a, cạnh bên SA vuông góc với mặt phẳng (ABCD) và SA = 6a."
    p1 = s1 or "Tính khoảng cách từ trung điểm của cạnh SA đến giao tuyến của hai mặt phẳng (SBC) và (SCD)."
    return f"{p0} {p1}", [
        f("f1", "solid", p0, solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", p0, points=list("ABCD"), shape="rectangle"),
        _seg("f3", p0, "AB", ab),
        _seg("f4", p0, "AD", ad),
        f("f5", "perpendicular", p0, points_a=["S", "A"], points_b=list("ABCD")),
        _seg("f6", p0, "SA", sa),
        f("f7", "intersection_line", p1, points_a=list(planes[0]), points_b=list(planes[1])),
        q("q1", p1, quantity="distance", point_kind="midpoint", points=["S", "A"], line_ref="f7"),
    ]


def _right_prism_compound_line_ref_case():
    p0 = "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A với AB = 4a, AC = 4a và cạnh bên AA' = 4a."
    p1 = "Tính khoảng cách từ trung điểm của cạnh A'C' đến giao tuyến của hai mặt phẳng (A'BC) và (ABC)."
    return f"{p0} {p1}", [
        f("f1", "solid", p0, solid="ABC.A'B'C'", solid_type="prism", right=True),
        f("f2", "right_angle", p0, at="A", points=["B", "C"]),
        _seg("f3", p0, "AB", "4a"),
        _seg("f4", p0, "AC", "4a"),
        _seg("f5", p0, ["A", "A'"], "4a"),
        f("f6", "intersection_line", p1, points_a=["A'", "B", "C"], points_b=list("ABC")),
        q("q1", p1, quantity="distance", point_kind="midpoint", points=["A'", "C'"], line_ref="f6"),
    ]


def _bh2a03_case(base_plane=("A", "B", "C", "D")):
    p0 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3a, cạnh bên SA vuông góc với mặt phẳng (ABCD) và SA = 3a."
    p1 = "Tính khoảng cách từ trọng tâm của tam giác SAB đến giao tuyến của hai mặt phẳng (SCD) và (ABCD)."
    return f"{p0} {p1}", [
        f("f1", "solid", p0, solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", p0, points=list("ABCD"), shape="square", value="3a"),
        f("f3", "perpendicular", p0, points_a=["S", "A"], points_b=list("ABCD")),
        _seg("f4", p0, "SA", "3a"),
        f("f_gt", "intersection_line", p1, points_a=list("SCD"), points_b=list(base_plane)),
        q("q1", p1, quantity="distance", point_kind="centroid", points=list("SAB"), line_ref="f_gt"),
    ]


def test_followup_b_sgh02_sgh10_bh2a03_compound_premise_with_line_ref_served():
    served(run(*_sgh02_exact_case()), {"q1": "a√37"})
    served(run(*_sgh10_exact_case()), {"q1": "2a√2"})
    served(run(*_bh2a03_case(base_plane=("A", "B", "C", "D"))), {"q1": "a√10"})
    served(run(*_rect_compound_line_ref_case()), {"q1": "3a√70/14"})
    served(run(*_right_prism_compound_line_ref_case()), {"q1": "3a√2"})

    # Explicit intersection_line sentence + distance question after a compound premise sentence:
    p0 = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 4a, AD = 2a, cạnh bên SA vuông góc với mặt phẳng (ABCD) và SA = 6a."
    p_gt = "Tìm giao tuyến của (SBC) và (SCD)."
    p_q = "Tính khoảng cách từ trung điểm của cạnh SA đến giao tuyến của (SBC) và (SCD)."
    served(run(f"{p0} {p_gt} {p_q}", [
        f("f1", "solid", p0, solid="S.ABCD", solid_type="pyramid"),
        f("f2", "polygon_shape", p0, points=list("ABCD"), shape="rectangle"),
        _seg("f3", p0, "AB", "4a"),
        _seg("f4", p0, "AD", "2a"),
        f("f5", "perpendicular", p0, points_a=["S", "A"], points_b=list("ABCD")),
        _seg("f6", p0, "SA", "6a"),
        f("f7", "intersection_line", p_gt, points_a=list("SBC"), points_b=list("SCD")),
        q("q1", p_q, quantity="distance", point_kind="midpoint", points=["S", "A"], line_ref="f7"),
    ]), {"q1": "3a√70/14"})


def test_followup_b_negative_controls_stay_refused():
    # 1. Unread clause in compound premise ("và mặt bên SBC là tam giác đều") -> SOURCE_PREMISE_UNREAD
    s0_unread = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 4a, AD = 2a, "
        "cạnh bên SA vuông góc với mặt phẳng (ABCD), SA = 6a và mặt bên SBC là tam giác đều."
    )
    refused(run(*_rect_compound_line_ref_case(s0=s0_unread)), "SOURCE_PREMISE_UNREAD")

    # 2. Swapped values AB = 2a, AD = 4a -> UNGROUNDED_VALUE
    refused(run(*_rect_compound_line_ref_case(ab="2a", ad="4a")), "UNGROUNDED_VALUE")

    # 3. Parameter 'a' mismatch (4 instead of 4a) -> UNGROUNDED_VALUE
    refused(run(*_rect_compound_line_ref_case(ab="4")), "UNGROUNDED_VALUE")

    # 4. Spoofed line_ref planes -> SOURCE_OBJECT_MISMATCH
    refused(run(*_rect_compound_line_ref_case(planes=(("S", "A", "B"), ("S", "C", "D")))), "SOURCE_OBJECT_MISMATCH")

    # 5. 3-label base plane ["A", "B", "C"] when source writes (ABCD) -> SOURCE_OBJECT_MISMATCH
    refused(run(*_bh2a03_case(base_plane=("A", "B", "C"))), "SOURCE_OBJECT_MISMATCH")

    # 6. Cross-sentence point construction must not validate an unencoded/contradictory point or projection clause in compound premise (Review B-1)
    s_m = "Gọi M là trung điểm của SA."
    p_gt = "Tìm giao tuyến của (SBC) và (SCD)."
    p_q = "Tính khoảng cách từ điểm M đến giao tuyến của (SBC) và (SCD)."
    for bad_clause in (
        "và M là điểm di động trên cạnh SC",
        "và M là trung điểm của SB",
        "và M là hình chiếu vuông góc của S lên BD",
    ):
        s0_bad = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4a, SA vuông góc với mặt phẳng (ABCD), SA = 4a {bad_clause}."
        refused(run(f"{s0_bad} {s_m} {p_gt} {p_q}", [
            f("f1", "solid", s0_bad, solid="S.ABCD", solid_type="pyramid"),
            f("f2", "polygon_shape", s0_bad, points=list("ABCD"), shape="square", value="4a"),
            f("f3", "perpendicular", s0_bad, points_a=["S", "A"], points_b=list("ABCD")),
            _seg("f4", s0_bad, "SA", "4a"),
            f("f_m", "point_def", s_m, point="M", point_kind="midpoint", points=["S", "A"]),
            f("f_gt", "intersection_line", p_gt, points_a=list("SBC"), points_b=list("SCD")),
            q("q1", p_q, quantity="distance", points_a=["M"], line_ref="f_gt"),
        ]), "SOURCE_PREMISE_UNREAD")
