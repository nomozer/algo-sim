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
