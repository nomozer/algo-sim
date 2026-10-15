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
         "Khi đó, tính {O}.", "Tính {O} (đơn vị: cm)."]
# §6 policy override (correction wave of `shared-ask-grammar-safety`, closing review of 4acfc731): the deterministic
# engine returns exact radical/rational expressions and never rounds; requests for rounding (including historical
# positive probe templates P5 and P7 of `grammar_probe.py`) must fail closed (`QUESTION_CONTEXT_UNSUPPORTED`).
ROUNDING_REFUSED = [
    "Tính {O} (làm tròn đến hàng phần trăm).",
    "Tính {O} (kết quả làm tròn đến hàng phần mười).",
    "Tính {O}, làm tròn kết quả đến hàng phần trăm.",
    "Tính {O} (đơn vị: cm; làm tròn đến 2 chữ số thập phân).",
    "Tính {O} (làm tròn đến 0,01).",
    "Tính {O} (làm tròn đến 0,1).",
    "Tính {O} (làm tròn đến chữ số thập phân thứ hai).",
    "Tính {O} (làm tròn đến chữ số thập phân thứ nhất).",
    "Tính {O}, làm tròn đến 0,01.",
    "Tính {O}, làm tròn đến chữ số thập phân thứ hai.",
    "Làm tròn kết quả đến hàng phần mười. Tính {O}.",
    "Tính {O} rồi làm tròn kết quả.",
]


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


# ── Stage A: C1 (goal clause swallows modifiers), C4 (unit policy), I2 (construction + ask), I3 (rounding/unit notes) ──

C1_REFUSED = [
    "Chứng minh BD ⊥ SC; kết quả lấy bình phương; tính {O}.",
    "Chứng minh BD ⊥ SC, nhân đôi kết quả và tính {O}.",
    "Tính {O} rồi suy ra đáp số là bình phương của nó.",
    "Chỉ ra đáp số gấp đôi: tính {O}.",
    "Chứng minh BD ⊥ SC và nhân đôi kết quả, tính {O}.",
]

C1_SERVED = [
    "Chứng minh BD ⊥ SC và tính {O}.",
    "Chứng minh BD ⊥ SC, từ đó tính {O}.",
    "Chứng minh BD ⊥ SC; từ đó tính {O}.",
    "Tính {O}, từ đó suy ra SC > SA.",
]


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in C1_REFUSED for k in OBJ], ids=[f"{k}:{t}" for t in C1_REFUSED for k in OBJ])
def test_stage_a_c1_goal_clause_does_not_swallow_quantity_modifiers_route_b(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED", (r.answers, tpl, kind)


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in C1_REFUSED for k in ("plane", "length")],
                         ids=[f"{k}:{t}" for t in C1_REFUSED for k in ("plane", "length")])
def test_stage_a_c1_goal_clause_does_not_swallow_quantity_modifiers_route_a(tpl, kind):
    r = _a(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED", (r.answers, tpl, kind)


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in C1_SERVED for k in OBJ], ids=[f"{k}:{t}" for t in C1_SERVED for k in OBJ])
def test_stage_a_c1_valid_goal_clauses_with_asks_stay_served(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "SERVED" and r.answers == {"q": OBJ[kind][2]}, (r.code, r.reason, tpl, kind)


def _cm_base():
    base = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2 cm.", "SA vuông góc với (ABCD).", "SA = 3 cm."]
    facts = [HB._f("f1", "solid", base[0], solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", base[1], points=list("ABCD"), shape="square", value="2"),
             HB._f("f3", "perpendicular", base[2], points_a=["S", "A"], points_b=list("ABCD")),
             HB._f("f4", "length", base[3], points=["S", "A"], measure="segment", value="3")]
    return base, facts


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("sentence,expected", [
    ("Tính độ dài SC.", "SERVED"),
    ("Tính độ dài SC (đơn vị: cm).", "SERVED"),
    ("Tính độ dài SC theo đơn vị cm.", "SERVED"),
    ("Tính độ dài SC (cm).", "SERVED"),
    ("Tính độ dài SC (đơn vị: mm).", "REFUSED"),
    ("Tính độ dài SC theo đơn vị mm.", "REFUSED"),
    ("Tính độ dài SC (mm).", "REFUSED"),
    ("Tính độ dài SC (đơn vị m).", "REFUSED"),
    ("Tính độ dài SC (dm; làm tròn đến hàng phần trăm).", "REFUSED"),
])
def test_stage_a_c4_metric_unit_mismatch_against_givens(arm, sentence, expected):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    base, facts = _cm_base()
    q = HB._f("q", "question", sentence, role="question", quantity="length", points=["S", "C"])
    text = " ".join(base + [sentence])
    payload = {"facts": facts + [q]}
    r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
    assert r.status == expected, (arm, sentence, r.status, r.code, r.answers)
    if expected == "SERVED":
        assert r.answers == {"q": "√17"}


@pytest.mark.parametrize("sentence,kw,expected", [
    ("Tính diện tích tam giác SAC (đơn vị diện tích).", dict(quantity="area", points=list("SAC")), "SERVED"),
    ("Tính diện tích tam giác SAC (cm²).", dict(quantity="area", points=list("SAC")), "SERVED"),
    ("Tính diện tích tam giác SAC (mm²).", dict(quantity="area", points=list("SAC")), "REFUSED"),
    ("Tính diện tích tam giác SAC (đơn vị: cm).", dict(quantity="area", points=list("SAC")), "REFUSED"),
    ("Tính diện tích tam giác SAC (đơn vị độ dài).", dict(quantity="area", points=list("SAC")), "REFUSED"),
    ("Tính diện tích tam giác SAC (cm³).", dict(quantity="area", points=list("SAC")), "REFUSED"),
    ("Tính thể tích khối chóp S.ABCD (đơn vị thể tích).", dict(quantity="volume", solid="S.ABCD"), "SERVED"),
    ("Tính thể tích khối chóp S.ABCD (cm³).", dict(quantity="volume", solid="S.ABCD"), "SERVED"),
    ("Tính thể tích khối chóp S.ABCD (mm³).", dict(quantity="volume", solid="S.ABCD"), "REFUSED"),
    ("Tính thể tích khối chóp S.ABCD (đơn vị: cm).", dict(quantity="volume", solid="S.ABCD"), "REFUSED"),
    ("Tính thể tích khối chóp S.ABCD (đơn vị diện tích).", dict(quantity="volume", solid="S.ABCD"), "REFUSED"),
    ("Tính độ dài SC (đơn vị diện tích).", dict(quantity="length", points=["S", "C"]), "REFUSED"),
    ("Tính độ dài SC (cm²).", dict(quantity="length", points=["S", "C"]), "REFUSED"),
    ("Tính độ dài SC (cm³).", dict(quantity="length", points=["S", "C"]), "REFUSED"),
])
def test_stage_a_c4_unit_dimension_vs_quantity_type(sentence, kw, expected):
    base, facts = _cm_base()
    q = HB._f("q", "question", sentence, role="question", **kw)
    r = run_fact_route(" ".join(base + [sentence]), {"facts": facts + [q]})
    assert r.status == expected, (sentence, r.status, r.code, r.answers)


MID = HB._mid("f5", "M", "S", "C")


@pytest.mark.parametrize("sentence", [
    "Xác định thiết diện của hình chóp S.ABCD cắt bởi (MAB) và tính diện tích thiết diện đó.",
    "Xác định thiết diện của hình chóp S.ABCD cắt bởi (MAB), rồi tính diện tích thiết diện đó.",
    "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB) và tính diện tích thiết diện đó.",
])
def test_stage_a_i2_section_construction_followed_by_area_ask_is_served(sentence):
    from fractions import Fraction
    q, fs = HB._with(HB._square(), MID)
    sec = HB._f("f6", "section", sentence, role="question", solid="S.ABCD", points=list("MAB"))
    area = HB._ask("q", sentence, "area", solid="S.ABCD", points=list("MAB"))
    r = run_fact_route(" ".join(q + [sentence]), {"facts": fs + [sec, area]})
    assert r.status == "SERVED" and HB.answer_square(r.answers["q"]) == Fraction(117, 16), (r.code, r.reason)
    # Also when only the area question fact is extracted with the compound sentence as its quote:
    r2 = run_fact_route(" ".join(q + [sentence]), {"facts": fs + [area]})
    assert r2.status == "SERVED" and HB.answer_square(r2.answers["q"]) == Fraction(117, 16), (r2.code, r2.reason)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_stage_a_i2_projection_construction_followed_by_length_ask_is_served(arm):
    from tests.geometry.test_question_local_givens import run as run_local
    r = run_local("Dựng hình chiếu của S lên (ABCD) và tính SC.", arm)
    assert r.status == "SERVED" and r.answers == {"q": "√17"}, (arm, r.code, r.reason)


@pytest.mark.parametrize("kind", list(OBJ))
def test_stage_a_i2_same_sentence_midpoint_premise_before_ask_is_served(kind):
    phrase, kw, value = OBJ[kind]
    sent = f"Gọi M là trung điểm SC, tính {phrase}."
    q, f = HB._with(HB._square())
    f = f + [HB._f("f5", "point_def", "Gọi M là trung điểm SC", point="M", point_kind="midpoint", points=["S", "C"]),
             HB._f("q", "question", f"tính {phrase}.", role="question", **kw)]
    r = run_fact_route(" ".join(q + [sent]), {"facts": f})
    assert r.status == "SERVED" and r.answers == {"q": value}, (kind, r.code, r.reason)


@pytest.mark.parametrize("tpl", ROUNDING_REFUSED)
@pytest.mark.parametrize("kind", list(OBJ))
def test_policy_rounding_requests_on_quantitative_asks_are_refused_route_b(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (tpl, kind, r.status, r.code, r.answers)


@pytest.mark.parametrize("tpl", ROUNDING_REFUSED)
@pytest.mark.parametrize("kind", ["plane", "length"])
def test_policy_rounding_requests_on_quantitative_asks_are_refused_route_a(tpl, kind):
    r = _a(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (tpl, kind, r.status, r.code, r.answers)


# ── STAGE B: C2 (multi-sentence question semantics) and C3 (derived-plane section-area ask) ──────────────────────────
C2_MULTI_SENTENCE = [
    ("Tính {O}. Hãy tính kết quả dưới dạng bình phương.", "Tính {O}."),
    ("Tính {O}. Đáp số nhân đôi, biết SA = 3.", "Tính {O}."),
    ("Tính {O}. Hỏi kết quả nhân đôi bằng bao nhiêu?", "Tính {O}."),
    ("Tính hai lần {O}. Tính {O}.", "Tính {O}."),
    ("Nhân đôi kết quả. Tính {O}.", "Tính {O}."),
    ("Tính {O}. Kết quả lấy bình phương.", "Tính {O}."),
]


@pytest.mark.parametrize("tpl,quote_tpl", C2_MULTI_SENTENCE, ids=[t for t, _q in C2_MULTI_SENTENCE])
@pytest.mark.parametrize("kind", list(OBJ))
def test_stage_b_c2_route_b_refuses_multi_sentence_modifier(tpl, quote_tpl, kind):
    phrase = OBJ[kind][0]
    r = _b(_cap(tpl.format(O=phrase)), kind, quote=_cap(quote_tpl.format(O=phrase)))
    assert r.status == "REFUSED" and not r.answers and not r.scene3d, (tpl, kind, r.status, r.code, r.answers)


@pytest.mark.parametrize("tpl,quote_tpl", C2_MULTI_SENTENCE, ids=[t for t, _q in C2_MULTI_SENTENCE])
@pytest.mark.parametrize("kind", ["plane", "length"])
def test_stage_b_c2_route_a_refuses_multi_sentence_modifier(tpl, quote_tpl, kind):
    phrase = OBJ[kind][0]
    plain = _cap(quote_tpl.format(O=phrase))
    full = _cap(tpl.format(O=phrase))
    q, f = HB._with(HB._square(), HB._f("q", "question", plain, role="question", **OBJ[kind][1]))
    r0 = run_fact_route(" ".join(q), {"facts": f})
    assert r0.status == "SERVED"
    r = run_function_route(" ".join(q[:-1] + [full]), {"calls": r0.planner["calls"]})
    assert r.status == "REFUSED" and not r.answers and not r.scene3d, (tpl, kind, r.status, r.code, r.answers)


@pytest.mark.parametrize("tpl,quote_tpl,expected", [
    ("Tính {O}.", "Tính {O}.", "SERVED"),
    ("Tính {O}. Hãy tính kết quả dưới dạng bình phương.", "Tính {O}.", "REFUSED"),
    ("Tính {O}. Đáp số nhân đôi, biết SA = 3.", "Tính {O}.", "REFUSED"),
    ("Tính {O}. Hỏi kết quả nhân đôi bằng bao nhiêu?", "Tính {O}.", "REFUSED"),
    ("Tính hai lần {O}. Tính {O}.", "Tính {O}.", "REFUSED"),
])
def test_stage_b_c2_line_ref_multi_sentence_modifier(tpl, quote_tpl, expected):
    from copy import deepcopy
    from tests.geometry.test_result_binding_planning import CORPUS
    c = deepcopy(CORPUS["positive"][0])
    phrase = "khoảng cách từ M đến giao tuyến của (SAC) và (SBD)"
    old_q = "Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD)."
    q_sent = _cap(tpl.format(O=phrase))
    q_quote = _cap(quote_tpl.format(O=phrase))
    c["text"] = c["text"].replace(old_q, q_sent)
    c["payload"]["facts"][-1]["quotes"] = [q_quote]
    r = run_fact_route(c["text"], c["payload"])
    assert r.status == expected, (tpl, r.status, r.code, r.answers)
    if expected == "SERVED":
        assert r.answers == {"q": "√110/11"}


@pytest.mark.parametrize("new_ask,expected", [
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P).", "SERVED"),
    ("Xác định thiết diện của hình chóp S.ABCD với (P) và tính diện tích thiết diện đó.", "SERVED"),
    ("Xác định thiết diện của hình chóp S.ABCD với (P), rồi tính diện tích thiết diện của hình chóp S.ABCD với (P).", "SERVED"),
    ("Xác định thiết diện của hình chóp S.ABCD với (P). Tính diện tích thiết diện của hình chóp S.ABCD với (P).", "SERVED"),
    ("a) Tính diện tích thiết diện của hình chóp S.ABCD với (P) (làm tròn đến hàng phần trăm).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (đơn vị diện tích).", "SERVED"),
    ("Nhân đôi kết quả, tính diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính nửa diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính bình phương diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính hai lần diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (kết quả nhân đôi).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P). Hãy tính kết quả nhân đôi.", "REFUSED"),
    ("Chứng minh SA ⊥ BD, nhân đôi kết quả và tính diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (đơn vị: cm).", "REFUSED"),
])
def test_stage_b_c3_mat_song_song_ask_section_area_shared_grammar(new_ask, expected):
    from tests.geometry.test_goal_directed_section_planning import _pyramid_problem
    old = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
    text, payload = _pyramid_problem()
    text = text.replace(old, new_ask)
    quote_ask = old if ". Hãy tính" in new_ask else new_ask
    for f in payload["facts"]:
        f["quotes"] = [quote_ask if x == old else x for x in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == expected, (new_ask, r.status, r.code, r.answers)
    if expected == "SERVED":
        assert r.answers == {"q": "1"}


@pytest.mark.parametrize("new_ask,expected", [
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P).", "SERVED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (làm tròn đến hàng phần trăm).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (đơn vị diện tích).", "SERVED"),
    ("Nhân đôi kết quả, tính diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính hai lần diện tích thiết diện của hình chóp S.ABCD với (P).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (kết quả nhân đôi).", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P). Hãy tính kết quả nhân đôi.", "REFUSED"),
    ("Tính diện tích thiết diện của hình chóp S.ABCD với (P) (đơn vị: cm).", "REFUSED"),
])
def test_stage_b_c3_mat_hai_duong_ask_section_area_shared_grammar(new_ask, expected):
    from tests.geometry.test_two_line_plane_section import problem
    old = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
    text, payload = problem()
    text = text.replace(old, new_ask)
    quote_ask = old if ". Hãy tính" in new_ask else new_ask
    for f in payload["facts"]:
        f["quotes"] = [quote_ask if x == old else x for x in f["quotes"]]
    r = run_fact_route(text, payload)
    assert r.status == expected, (new_ask, r.status, r.code, r.answers)


# ── Review of 4acfc731 closure: CR-1 (unit note sentences), CR-2 (theo X), IM-1 (goal relations), §6 (angle/rounding) ──

@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("note,ask_sent,kw,expected,ans", [
    # CR-1: Unit conversion in note sentence before/after/beside the question must fail closed.
    ("Kết quả ghi ở đơn vị mm.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Kết quả tính theo đơn vị mm.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Lưu ý: kết quả để ở đơn vị m.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Đáp số ghi ở đơn vị dm.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Đơn vị của kết quả là mm.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Đơn vị độ dài là mm.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Kết quả ghi ở đơn vị mm².", "Tính diện tích tam giác SAC.", dict(quantity="area", points=list("SAC")), "REFUSED", None),
    ("Kết quả ghi ở đơn vị cm.", "Tính diện tích tam giác SAC.", dict(quantity="area", points=list("SAC")), "REFUSED", None),
    ("Kết quả ghi ở đơn vị độ dài.", "Tính diện tích tam giác SAC.", dict(quantity="area", points=list("SAC")), "REFUSED", None),
    ("Kết quả ghi ở đơn vị mm³.", "Tính thể tích khối chóp S.ABCD.", dict(quantity="volume", solid="S.ABCD"), "REFUSED", None),
    ("Kết quả ghi ở đơn vị cm².", "Tính thể tích khối chóp S.ABCD.", dict(quantity="volume", solid="S.ABCD"), "REFUSED", None),
    ("Kết quả ghi ở đơn vị diện tích.", "Tính thể tích khối chóp S.ABCD.", dict(quantity="volume", solid="S.ABCD"), "REFUSED", None),
    ("Kết quả ghi ở đơn vị diện tích.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    # Valid note sentences matching given scale and asked dimension stay SERVED.
    ("Kết quả ghi ở đơn vị cm.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "SERVED", "√17"),
    ("Kết quả ghi ở đơn vị cm².", "Tính diện tích tam giác SAC.", dict(quantity="area", points=list("SAC")), "SERVED", "3√2"),
    ("Kết quả ghi ở đơn vị cm³.", "Tính thể tích khối chóp S.ABCD.", dict(quantity="volume", solid="S.ABCD"), "SERVED", "4"),
    ("Đơn vị độ dài là cm.", "Tính diện tích tam giác SAC.", dict(quantity="area", points=list("SAC")), "SERVED", "3√2"),
    ("Hãy trình bày lời giải ngắn gọn.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "SERVED", "√17"),
    # Policy closure (§4 CR-B): "dạng căn thức" / "dạng phân số" is not guaranteed to match every output (e.g. integer volume 4).
    ("Lưu ý: kết quả để ở dạng căn thức.", "Tính độ dài SC.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Lưu ý: kết quả để ở dạng căn thức.", "Tính thể tích khối chóp S.ABCD.", dict(quantity="volume", solid="S.ABCD"), "REFUSED", None),
])
def test_cr1_unit_in_note_sentence_before_or_after_ask(arm, note, ask_sent, kw, expected, ans):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    base, facts = _cm_base()
    q = HB._f("q", "question", ask_sent, role="question", **kw)
    payload = {"facts": facts + [q]}
    for text in (" ".join(base + [note, ask_sent]), " ".join(base + [ask_sent, note])):
        r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
        assert r.status == expected, (arm, text, r.status, r.code, r.answers)
        if expected == "SERVED":
            assert r.answers == {"q": ans}
        else:
            assert r.code == "QUESTION_CONTEXT_UNSUPPORTED"


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("sentence,kw", [
    ("Tính độ dài SC theo m.", dict(quantity="length", points=["S", "C"])),
    ("Tính độ dài SC theo mm.", dict(quantity="length", points=["S", "C"])),
    ("Tính độ dài SC theo x.", dict(quantity="length", points=["S", "C"])),
    ("Tính độ dài SC theo b.", dict(quantity="length", points=["S", "C"])),
    ("Tính độ dài SC theo a.", dict(quantity="length", points=["S", "C"])),
    ("Tính diện tích tam giác SAC theo a.", dict(quantity="area", points=list("SAC"))),
    ("Tính thể tích khối chóp S.ABCD theo a.", dict(quantity="volume", solid="S.ABCD")),
])
def test_cr2_theo_unit_or_undeclared_parameter_is_refused(arm, sentence, kw):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    for base, facts in (_cm_base(), HB._square()):
        q = HB._f("q", "question", sentence, role="question", **kw)
        text = " ".join(base + [sentence])
        payload = {"facts": facts + [q]}
        r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
        assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (arm, text, r.status, r.code, r.answers)


def _symbolic_a_base():
    base = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2a.", "SA vuông góc với (ABCD).", "SA = 3a."]
    facts = [HB._f("f1", "solid", base[0], solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", base[1], points=list("ABCD"), shape="square", value="2a"),
             HB._f("f3", "perpendicular", base[2], points_a=["S", "A"], points_b=list("ABCD")),
             HB._f("f4", "length", base[3], points=["S", "A"], measure="segment", value="3a")]
    return base, facts


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("sentence,kw,expected,ans", [
    ("Tính độ dài SC theo a.", dict(quantity="length", points=["S", "C"]), "SERVED", "a√17"),
    ("Tính diện tích tam giác SAC theo a.", dict(quantity="area", points=list("SAC")), "SERVED", "3a²√2"),
    ("Tính thể tích khối chóp S.ABCD theo a.", dict(quantity="volume", solid="S.ABCD"), "SERVED", "4a³"),
    ("Tính độ dài SC theo m.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Tính độ dài SC theo x.", dict(quantity="length", points=["S", "C"]), "REFUSED", None),
    ("Tính góc giữa SC và (ABCD) theo a.", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
])
def test_cr2_theo_a_served_when_declared_in_givens_and_refused_otherwise(arm, sentence, kw, expected, ans):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    base, facts = _symbolic_a_base()
    q = HB._f("q", "question", sentence, role="question", **kw)
    text = " ".join(base + [sentence])
    payload = {"facts": facts + [q]}
    r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
    assert r.status == expected, (arm, sentence, r.status, r.code, r.answers)
    if expected == "SERVED":
        assert r.answers == {"q": ans}
    else:
        assert r.code == "QUESTION_CONTEXT_UNSUPPORTED"


IM1_SERVED = [
    "Chứng minh SB và SD bằng nhau và tính {O}.",
    "Chứng minh AC và BD cắt nhau và tính {O}.",
    "Chứng minh BD vuông góc SC bằng hai cách và tính {O}.",
    "Chứng minh SC bằng hai lần SA, tính {O}.",
    "Chứng minh SC bằng gấp đôi SA, tính {O}.",
    "Chứng minh SC bằng một nửa SA, tính {O}.",
    "Chứng minh SC = 2 SA, tính {O}.",
    "Chứng minh tam giác SAB vuông, SC bằng hai lần SA, tính {O}.",
    "Chứng minh ΔSAB vuông, SC bằng hai lần SA và tính {O}.",
    "Chứng minh SA ⊥ (ABCD), SB = SD rồi tính {O}.",
]

IM1_REFUSED = [
    "Chứng minh SB và SD bằng nhau, nhân đôi kết quả và tính {O}.",
    "Chứng minh AC và BD cắt nhau, lấy bình phương kết quả và tính {O}.",
    "Chứng minh BD vuông góc SC bằng hai cách; nhân đôi kết quả; tính {O}.",
]


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in IM1_SERVED for k in OBJ], ids=[f"{k}:{t}" for t in IM1_SERVED for k in OBJ])
def test_im1_valid_goal_clause_structures_are_served_route_b(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "SERVED" and r.answers == {"q": OBJ[kind][2]}, (tpl, kind, r.code, r.reason)


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in IM1_SERVED for k in ("plane", "length")],
                         ids=[f"{k}:{t}" for t in IM1_SERVED for k in ("plane", "length")])
def test_im1_valid_goal_clause_structures_are_served_route_a(tpl, kind):
    r = _a(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "SERVED" and r.answers == {"q": OBJ[kind][2]}, (tpl, kind, r.code, r.reason)


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in IM1_REFUSED for k in OBJ], ids=[f"{k}:{t}" for t in IM1_REFUSED for k in OBJ])
def test_im1_goal_clause_with_modifier_stays_refused(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (tpl, kind, r.status, r.code, r.answers)


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("sentence,kw,expected,ans", [
    ("Tính góc giữa SC và (ABCD).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "SERVED", "cos²=8/17"),
    ("Tính góc giữa hai mặt phẳng (SBC) và (ABCD).", dict(quantity="angle", points_a=list("SBC"), points_b=list("ABCD")), "SERVED", "cos²=4/13"),
    ("Tính góc giữa SC và (ABCD) theo độ.", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính góc giữa SC và (ABCD) theo radian.", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính góc giữa SC và (ABCD) (độ).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính góc giữa SC và (ABCD) (radian).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính góc giữa SC và (ABCD) (đơn vị: độ).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính góc giữa hai mặt phẳng (SBC) và (ABCD) theo độ.", dict(quantity="angle", points_a=list("SBC"), points_b=list("ABCD")), "REFUSED", None),
])
def test_policy_angle_degree_or_radian_representation_is_refused_while_plain_cos2_is_served(arm, sentence, kw, expected, ans):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    base, facts = HB._square()
    q = HB._f("q", "question", sentence, role="question", **kw)
    text = " ".join(base + [sentence])
    payload = {"facts": facts + [q]}
    r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
    assert r.status == expected, (arm, sentence, r.status, r.code, r.answers)
    if expected == "SERVED":
        assert r.answers == {"q": ans}
    else:
        assert r.code == "QUESTION_CONTEXT_UNSUPPORTED"


# ── Review of 34a04eaf closure: CR-A (goal-clause quantity modifiers), CR-B (closed note semantics), IM-A (số đo góc) ──

CRA_REFUSED = [
    "Chứng minh BD ⊥ SC, SC gấp đôi, tính {O}.",
    "Chứng minh BD ⊥ SC và gấp đôi, tính {O}.",
    "Chứng minh BD ⊥ SC, một nửa SC, tính {O}.",
    "Chứng minh BD ⊥ SC, hai lần SC, rồi tính {O}.",
    "Chứng minh BD ⊥ SC, 2 lần SC, tính {O}.",
    "Chứng minh BD ⊥ SC, gấp đôi {O}, tính {O}.",
    "Chứng minh BD ⊥ SC, một nửa {O}, tính {O}.",
    "Chứng minh BD ⊥ SC, ba lần SC, tính {O}.",
    "Chứng minh BD ⊥ SC, 2 SC, tính {O}.",
    "Chứng minh BD ⊥ SC, SC, tính {O}.",
    "Chứng minh SC gấp đôi, tính {O}.",
    "Chứng minh một nửa SC, tính {O}.",
    "Chứng minh hai lần SC, tính {O}.",
    "Chứng minh BD ⊥ SC, SC bằng gấp đôi, tính {O}.",
    "Chứng minh BD ⊥ SC, SC bằng hai lần, tính {O}.",
]


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in CRA_REFUSED for k in OBJ], ids=[f"{k}:{t}" for t in CRA_REFUSED for k in OBJ])
def test_cra_goal_clause_does_not_hide_bare_quantifier_or_incomplete_clause_route_b(tpl, kind):
    r = _b(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED" and r.code in ("QUESTION_CONTEXT_UNSUPPORTED", "GOAL_CLAUSE_NOT_PREMISE"), (
        tpl, kind, r.status, r.code, r.answers)


@pytest.mark.parametrize("tpl,kind", [(t, k) for t in CRA_REFUSED for k in ("plane", "length")],
                         ids=[f"{k}:{t}" for t in CRA_REFUSED for k in ("plane", "length")])
def test_cra_goal_clause_does_not_hide_bare_quantifier_or_incomplete_clause_route_a(tpl, kind):
    r = _a(_cap(tpl.format(O=OBJ[kind][0])), kind)
    assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (tpl, kind, r.status, r.code, r.answers)


@pytest.mark.parametrize("tpl", CRA_REFUSED[:5])
def test_cra_reused_foot_and_derived_sections_refuse_goal_clause_quantifier(tpl):
    from tests.geometry.test_goal_directed_section_planning import _pyramid_problem
    from tests.geometry.test_two_line_plane_section import problem
    sent_line = _cap(tpl.format(O=OBJ["line"][0]))
    r_foot = _b(sent_line, "line", quote="tính khoảng cách từ S đến BD.", extra=(PROJ,))
    assert r_foot.status == "REFUSED" and r_foot.code == "QUESTION_CONTEXT_UNSUPPORTED", (tpl, r_foot.status, r_foot.code)
    for fn_prob in (_pyramid_problem, problem):
        old = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
        phrase = "diện tích thiết diện của hình chóp S.ABCD với (P)"
        new_ask = _cap(tpl.format(O=phrase))
        text, payload = fn_prob()
        text = text.replace(old, new_ask)
        for f in payload["facts"]:
            f["quotes"] = [new_ask if x == old else x for x in f["quotes"]]
        r_sec = run_fact_route(text, payload)
        assert r_sec.status == "REFUSED", (fn_prob.__name__, tpl, r_sec.status, r_sec.code, r_sec.answers)


CRB_REFUSED_NOTES = [
    "Kết quả đến hàng phần trăm.",
    "Ghi kết quả đến hàng phần mười.",
    "Ghi đáp số ở hàng phần trăm.",
    "Viết kết quả dưới dạng phân số.",
    "Đáp số là phần mười của kết quả.",
    "Ghi kết quả theo hàng nghìn.",
    "Lưu ý: kết quả để ở dạng căn thức.",
    "Lưu ý: viết đáp số dưới dạng phân số.",
    "Chú ý: kết quả ở hàng phần mười.",
    "Đáp số lấy đến hàng phần trăm.",
    "Kết quả là một phần mười.",
    "Ghi kết quả dưới dạng số thập phân.",
]


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("note", CRB_REFUSED_NOTES)
@pytest.mark.parametrize("kind", ["plane", "length"])
def test_crb_note_sentences_altering_format_or_scale_are_refused_before_and_after_ask(arm, note, kind):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    phrase, kw, _v = OBJ[kind]
    ask_sent = f"Tính {phrase}."
    base, facts = _cm_base()
    q = HB._f("q", "question", ask_sent, role="question", **kw)
    payload = {"facts": facts + [q]}
    for text in (" ".join(base + [note, ask_sent]), " ".join(base + [ask_sent, note])):
        r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
        assert r.status == "REFUSED" and r.code == "QUESTION_CONTEXT_UNSUPPORTED", (arm, text, r.status, r.code, r.answers)


@pytest.mark.parametrize("note", CRB_REFUSED_NOTES[:6])
def test_crb_note_sentences_refused_on_auxiliary_line_and_derived_sections(note):
    from tests.geometry.test_goal_directed_section_planning import _pyramid_problem
    from tests.geometry.test_two_line_plane_section import problem
    r_line = _b(f"Tính khoảng cách từ S đến BD. {note}", "line", quote="Tính khoảng cách từ S đến BD.")
    assert r_line.status == "REFUSED" and r_line.code == "QUESTION_CONTEXT_UNSUPPORTED", (note, r_line.status, r_line.code)
    for fn_prob in (_pyramid_problem, problem):
        old = "Tính diện tích thiết diện của hình chóp S.ABCD với (P)."
        text, payload = fn_prob()
        r_sec = run_fact_route(text.replace(old, f"{old} {note}"), payload)
        assert r_sec.status == "REFUSED" and r_sec.code == "QUESTION_CONTEXT_UNSUPPORTED", (fn_prob.__name__, note, r_sec.status, r_sec.code)


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("sentence,kw,expected,ans", [
    ("Tính số đo góc giữa SC và (ABCD).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính số đo của góc giữa SC và (ABCD).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính số đo góc giữa SC và mặt đáy.", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Số đo góc giữa SC và (ABCD) bằng bao nhiêu?", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "REFUSED", None),
    ("Tính số đo góc giữa hai mặt phẳng (SBC) và (ABCD).", dict(quantity="angle", points_a=list("SBC"), points_b=list("ABCD")), "REFUSED", None),
    ("Tính số đo của góc tạo bởi (SBC) và (ABCD).", dict(quantity="angle", points_a=list("SBC"), points_b=list("ABCD")), "REFUSED", None),
    ("Tính góc giữa SC và (ABCD).", dict(quantity="angle", points_a=["S", "C"], points_b=list("ABCD")), "SERVED", "cos²=8/17"),
    ("Tính góc giữa hai mặt phẳng (SBC) và (ABCD).", dict(quantity="angle", points_a=list("SBC"), points_b=list("ABCD")), "SERVED", "cos²=4/13"),
])
def test_ima_angle_measure_so_do_goc_is_refused_while_plain_angle_cos2_is_served(arm, sentence, kw, expected, ans):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    base, facts = HB._square()
    q = HB._f("q", "question", sentence, role="question", **kw)
    text = " ".join(base + [sentence])
    payload = {"facts": facts + [q]}
    r = run_fact_route(text, payload) if arm == "B" else run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls})
    assert r.status == expected, (arm, sentence, r.status, r.code, r.answers)
    if expected == "SERVED":
        assert r.answers == {"q": ans}
    else:
        assert r.code == "QUESTION_CONTEXT_UNSUPPORTED"


@pytest.mark.parametrize("mutant_id", [
    "cra_allow_bare_quantifier_in_goal",
    "cra_skip_relational_predicate_after_comma",
    "crb_permissive_note_fallback_true",
    "ima_allow_so_do_goc_as_cos2",
])
def test_cra_crb_ima_mutants_are_killed_by_regression_suite(monkeypatch, mutant_id):
    import re as _re
    from app.simulation.geometry_functions import registry as RG

    if mutant_id == "cra_allow_bare_quantifier_in_goal":
        monkeypatch.setattr(
            RG,
            "_THAN_MUC_TIEU_CON",
            _re.compile(RG._THAN_MUC_TIEU_CON.pattern.replace("nhau|", "nhau|gấp\\s+đôi|một\\s+nửa|hai\\s+lần|"), _re.IGNORECASE),
        )
        r = _b("Chứng minh BD ⊥ SC và gấp đôi, tính độ dài SC.", "length")
        assert r.status == "SERVED"  # mutant re-opens the CR-A false serve
    elif mutant_id == "cra_skip_relational_predicate_after_comma":
        monkeypatch.setattr(RG, "_VI_TU_MUC_TIEU", _re.compile(r""))
        r = _b("Chứng minh BD ⊥ SC, SC, tính độ dài SC.", "length")
        assert r.status == "SERVED"  # mutant re-opens incomplete comma goal clause
    elif mutant_id == "crb_permissive_note_fallback_true":
        monkeypatch.setattr(RG, "_kiem_ghi_chu", lambda note, calls, don_vi_de: True)
        base, facts = _cm_base()
        q = HB._f("q", "question", "Tính độ dài SC.", role="question", quantity="length", points=["S", "C"])
        r = run_fact_route(" ".join(base + ["Tính độ dài SC.", "Kết quả đến hàng phần trăm."]), {"facts": facts + [q]})
        assert r.status == "SERVED"  # mutant re-opens the CR-B false serve
    elif mutant_id == "ima_allow_so_do_goc_as_cos2":
        orig = RG._kiem_don_vi_hoi
        monkeypatch.setattr(RG, "_kiem_don_vi_hoi", lambda fn, de, a, b, dv, calls=(): True if fn == "ask_angle_line_plane" else orig(fn, de, a, b, dv, calls))
        base, facts = HB._square()
        sent = "Tính số đo góc giữa SC và (ABCD)."
        q = HB._f("q", "question", sent, role="question", quantity="angle", points_a=["S", "C"], points_b=list("ABCD"))
        r = run_fact_route(" ".join(base + [sent]), {"facts": facts + [q]})
        assert r.status == "SERVED"  # mutant re-opens the IM-A false serve

