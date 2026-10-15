"""Shared ask-grammar safety (run `shared-ask-grammar-safety`), offline, 0 model calls.

Closes the findings of the independent review of 2427289a (run `source-bound-result-planning-false-serve-fix`):
- CRITICAL-1: a quantity modifier before the governing question verb was never read ("Nhân đôi kết quả, tính …").
- CRITICAL-2: a bracketed note was open after its first word ("(kết quả nhân đôi)").
- IMPORTANT-1: the reused-foot branch read the question on the source with the AI quote spliced in.
The same object phrase is asked on the auxiliary point–line, point–plane and length asks, on Route B and Route A.
"""
from __future__ import annotations

import json

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from tests.geometry import hybrid_compiler_benchmark as HB

OBJ = {"line": ("khoảng cách từ S đến BD", dict(quantity="distance", points_a=["S"], points_b=["B", "D"]), "√11"),
       "plane": ("khoảng cách từ S đến (ABCD)", dict(quantity="distance", points_a=["S"], points_b=list("ABCD")), "3"),
       "length": ("độ dài SC", dict(quantity="length", points=["S", "C"]), "√17")}

ALTERED = ["Nhân đôi kết quả, tính {O}.", "Hai lần của đại lượng sau bằng bao nhiêu: {O}?",
           "Bình phương của đại lượng sau bằng bao nhiêu: {O}?", "Đáp số là bình phương của kết quả; tính {O}.",
           "Lấy bình phương, tính {O}.", "Một nửa của đại lượng sau là bao nhiêu: {O}?", "Đề hỏi bình phương; hãy tính {O}.",
           "Gấp ba kết quả rồi tính {O}.",
           "Tính {O} (kết quả nhân đôi).", "Tính {O} (kết quả lấy bình phương).", "Tính {O} (kết quả gấp đôi).",
           "Tính {O} (kết quả ghi dưới dạng bình phương).", "Tính {O} (đơn vị: một nửa cm).",
           "Tính {O} (đơn vị: cm, kết quả bình phương).", "Tính {O} (kết quả 3).", "Tính {O} (kết quả có lớn hơn 3 không).",
           "Tính {O}, làm tròn sau khi nhân đôi."]
ASKED = ["Tính {O}.", "Hơn nữa, tính {O}.", "{O} bằng bao nhiêu?", "Hãy tính {O}.", "Tìm {O}.", "Hỏi {O} bằng bao nhiêu?",
         "Khi đó, tính {O}.", "Tính {O} (làm tròn đến hàng phần trăm).", "Tính {O} (đơn vị: cm).",
         "Tính {O} (kết quả làm tròn đến hàng phần mười).", "Tính {O}, làm tròn kết quả đến hàng phần trăm.",
         "Tính {O} (đơn vị: cm; làm tròn đến 2 chữ số thập phân)."]


def _cap(s: str) -> str:
    return s[0].upper() + s[1:]


def _b(sentence: str, kind: str, quote: str | None = None, extra=()):
    phrase, kw, _v = OBJ[kind]
    q, f = HB._with(HB._square(), *extra)
    f = f + [HB._f("q", "question", quote or sentence, role="question", **kw)]
    return run_fact_route(" ".join(q + [sentence]), {"facts": f})


def _a(sentence: str, kind: str):
    """Route A replays the planner's calls for the plain question, with the probe sentence substituted."""
    phrase, kw, _v = OBJ[kind]
    plain = _cap(f"tính {phrase}.")
    q, f = HB._with(HB._square(), HB._f("q", "question", plain, role="question", **kw))
    r = run_fact_route(" ".join(q), {"facts": f})
    assert r.status == "SERVED", r.code
    calls = json.loads(json.dumps(r.planner["calls"], ensure_ascii=False).replace(
        json.dumps(plain, ensure_ascii=False)[1:-1], json.dumps(sentence, ensure_ascii=False)[1:-1]))
    return run_function_route(" ".join(q).replace(plain, sentence), {"calls": calls})


CASES_B = [(t, k) for t in ALTERED for k in OBJ]
CASES_A = [(t, k) for t in ALTERED for k in ("plane", "length")]   # Route A may not introduce the auxiliary foot (by design)


@pytest.mark.parametrize("tpl,kind", CASES_B, ids=[f"{k}:{t}" for t, k in CASES_B])
def test_route_b_does_not_answer_a_changed_quantity(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED", (r.answers, tpl)


@pytest.mark.parametrize("tpl,kind", CASES_A, ids=[f"{k}:{t}" for t, k in CASES_A])
def test_route_a_does_not_answer_a_changed_quantity(tpl, kind):
    r = _a(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED", (r.answers, tpl)


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in ASKED for k in OBJ], ids=[f"{k}:{t}" for t in ASKED for k in OBJ])
def test_plain_asks_and_closed_notes_are_still_served(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "SERVED" and r.answers == {"q": OBJ[kind][2]}, (r.code, r.reason, tpl)


@pytest.mark.parametrize("kind", ["plane", "length"])
def test_route_a_plain_ask_is_still_served(kind):
    r = _a(_cap(f"tính {OBJ[kind][0]}."), kind)
    assert r.status == "SERVED" and r.answers == {"q": OBJ[kind][2]}, r.code


@pytest.mark.parametrize("kind", list(OBJ))
def test_a_whole_problem_in_one_sentence_is_still_served(kind):
    phrase, kw, value = OBJ[kind]
    text = (f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 3, tính {phrase}.")
    facts = [HB._f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2", points=list("ABCD"), shape="square", value="2"),
             HB._f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
             HB._f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3"),
             HB._f("q", "question", f"tính {phrase}.", role="question", **kw)]
    r = run_fact_route(text, {"facts": facts})
    assert r.status == "SERVED" and r.answers == {"q": value}, (r.code, r.reason)


PROJ = HB._proj("f5", "H", "S", "BD")                       # the source defines the foot H: the planner reuses it


@pytest.mark.parametrize("source,quote", [
    ("Tính hai lần.khoảng cách từ S đến BD?", "hai lần. khoảng cách từ S đến BD?"),   # quote invents a sentence boundary
    ("Nhân đôi kết quả, tính khoảng cách từ S đến BD.", "tính khoảng cách từ S đến BD."),
    ("Tính khoảng cách từ S đến BD (kết quả nhân đôi).", "khoảng cách từ S đến BD"),
    ("Tính bình phương khoảng cách từ S đến BD.", "khoảng cách từ S đến BD.")])
def test_reused_foot_reads_the_source_not_the_spliced_quote(source, quote):
    r = _b(source, "line", quote=quote, extra=(PROJ,))
    assert r.status == "REFUSED", r.answers


@pytest.mark.parametrize("quote", ["Tính khoảng cách từ S đến BD.", "Tính khoảngcách từ S đến BD."])
def test_reused_foot_is_still_served_from_a_valid_source(quote):
    r = _b("Tính khoảng cách từ S đến BD.", "line", quote=quote, extra=(PROJ,))
    assert r.status == "SERVED" and r.answers == {"q": "√11"}, (r.code, r.reason)
