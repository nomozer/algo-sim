"""S0 (run `hybrid-gate-clause-role-fix`): the shared source gate reads the clause role WHERE the predicate is, not only at
the start of the quote, and answers an `ask_*` only when the sentence asks it.

Found by the simulation capability audit (`ISSUE-ARCH-GATE-CLAUSE-ROLE-INSIDE-QUOTE`): a premise quote carrying its own
"Nếu … thì" / "Chứng minh" was used as a given — SC = √17 served where the figure is undetermined. Same gate for route A
(`run_function_route`) and route B (`run_fact_route`). Offline typed facts; no model.
"""
from __future__ import annotations

import sys
import types
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions import registry as RG
from tests.geometry import hybrid_compiler_benchmark as HB

f, ask = HB._f, HB._ask


def _no_perpendicular():
    q, facts = HB._square()
    return [q[0], q[1], q[3]], [facts[0], facts[1], facts[3]]          # SA = 3 but no SA ⊥ (ABCD)


def _no_sa_length():
    q, facts = HB._square()
    return q[:3], facts[:3]                                               # SA ⊥ (ABCD) but no SA = 3


def _run(*extra, base=None, text_extra=""):
    q, facts = HB._with(base or HB._square(), *extra)
    return run_fact_route(" ".join(q) + text_extra, {"facts": facts})


def _perp(quote):
    return f("f5", "perpendicular", quote, points_a=["S", "A"], points_b=list("ABCD"))


SC = ask("q", "Tính độ dài SC.", "length", points=["S", "C"])

# Premise quotes that are not unconditional givens — the figure must not be built from them.
NOT_GIVEN = [
    ("conditional_antecedent_in_quote", _perp("Nếu SA vuông góc với (ABCD) thì SC = 5."), _no_perpendicular, "CONDITIONAL_CLAUSE"),
    ("proof_goal_in_quote", _perp("Chứng minh rằng SA vuông góc với (ABCD)."), _no_perpendicular, "GOAL_CLAUSE_NOT_PREMISE"),
    ("conditional_consequent", _perp("SA vuông góc với (ABCD)"), _no_perpendicular, "CONDITIONAL_CLAUSE"),
    ("length_in_conditional", f("f5", "length", "Nếu SA = 3 thì SC = 5.", points=["S", "A"], measure="segment", value="3"),
     _no_sa_length, "CONDITIONAL_CLAUSE"),
]


@pytest.mark.parametrize("fact,base,code", [pytest.param(fa, b, c, id=i) for i, fa, b, c in NOT_GIVEN])
def test_clause_that_is_not_a_given_is_refused(fact, base, code):
    tail = " Nếu SB = 4 thì SA vuông góc với (ABCD)." if fact["quotes"] == ["SA vuông góc với (ABCD)"] else ""
    q, facts = HB._with(base(), SC)
    if not tail:
        q.insert(-1, fact["quotes"][0])
    facts.insert(-1, fact)
    r = run_fact_route(" ".join(q[:-1]) + tail + " " + q[-1], {"facts": facts})
    assert (r.status, r.code) == ("REFUSED", code), (r.answers, r.reason)


def test_route_a_shares_the_fix():
    t = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA = 3. Nếu SA vuông góc với (ABCD) thì SC = 5. Tính độ dài SC."
    calls = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": list("ABCD")}, "source": {"quotes": ["Cho hình chóp S.ABCD."]}},
        {"id": "c2", "fn": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"},
         "source": {"quotes": ["Đáy ABCD là hình vuông cạnh 2."]}},
        {"id": "c3", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "source": {"quotes": ["SA = 3."]}},
        {"id": "c4", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")},
         "source": {"quotes": ["Nếu SA vuông góc với (ABCD) thì SC = 5."]}},
        {"id": "c5", "fn": "ask_length", "args": {"segment": ["S", "C"]}, "source": {"quotes": ["Tính độ dài SC."]}}]
    r = run_function_route(t, {"calls": calls})
    assert (r.status, r.code) == ("REFUSED", "CONDITIONAL_CLAUSE"), r.answers


def test_premises_stay_served():
    """Controls: a plain given, a given after 'biết' inside a proof sentence, and every benchmark premise."""
    assert _run(SC).answers == {"q": "√17"}
    q, facts = _no_perpendicular()
    r = run_fact_route(" ".join(q) + " Chứng minh rằng SC = √17, biết SA vuông góc với (ABCD). Tính độ dài SC.",
                       {"facts": facts + [_perp("SA vuông góc với (ABCD)"), SC]})
    assert r.answers == {"q": "√17"}, (r.code, r.reason)


# ask_*: answer only a sentence that asks.
NOT_ASKED = [
    ask("q", "Hãy chỉ ra rằng khoảng cách từ S đến (ABCD) bằng 3.", "distance", points_a=["S"], points_b=list("ABCD")),
    ask("q", "Chứng minh rằng thể tích khối chóp S.ABCD bằng 4.", "volume", solid="S.ABCD"),
    ask("q", "Góc giữa SC và (ABCD) có cos² bằng 9/17.", "angle", points_a=["S", "C"], points_b=list("ABCD")),
]
ASKED = [
    (ask("q", "Thể tích khối chóp S.ABCD bằng bao nhiêu?", "volume", solid="S.ABCD"), F(16)),
    (ask("q", "Hỏi thể tích khối chóp S.ABCD bằng bao nhiêu?", "volume", solid="S.ABCD"), F(16)),
    (ask("q", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD"), F(16)),
    (ask("q", "Xác định khoảng cách từ S đến (ABCD).", "distance", points_a=["S"], points_b=list("ABCD")), F(9)),
]


@pytest.mark.parametrize("question", NOT_ASKED, ids=[a["quotes"][0] for a in NOT_ASKED])
def test_ask_answers_only_a_sentence_that_asks(question):
    r = _run(question)
    # Review 2: a proof sentence is now named as such (GOAL_CLAUSE_NOT_PREMISE); both codes refuse.
    assert r.status == "REFUSED" and r.code in ("NOT_ASKED_IN_SOURCE", "GOAL_CLAUSE_NOT_PREMISE"), (r.answers, r.reason)


@pytest.mark.parametrize("question,sq", ASKED, ids=[a["quotes"][0] for a, _ in ASKED])
def test_asking_sentences_are_still_answered(question, sq):
    r = _run(question)
    assert HB.answer_square(r.answers["q"]) == sq, (r.code, r.reason)


# Independent review 2 (run `hybrid-slice-review`), C1: an ask is answered only when the sentence asks FOR THAT OBJECT —
# not when the object is asserted, conditional, or a proof goal while something else is asked.
def _dist_plane(quote):
    return ask("q", quote, "distance", points_a=["S"], points_b=list("ABCD"))


def _dist_line(quote):
    return ask("q", quote, "distance", points_a=["S"], points_b=["B", "D"])


def _volume(quote):
    return ask("q", quote, "volume", solid="S.ABCD")


ASK_NOT_FOR_THIS_OBJECT = [
    _dist_plane("Khi khoảng cách từ S đến (ABCD) bằng 4 thì SC bằng bao nhiêu?"),      # required reproduction (b)
    _dist_line("Khi khoảng cách từ S đến BD bằng 4 thì SC bằng bao nhiêu?"),           # required reproduction (a)
    _dist_plane("Khoảng cách từ S đến (ABCD) bằng 3, tính SC."),
    _dist_plane("Khoảng cách từ S đến (ABCD) là 3. Hỏi SC?"),
    _dist_plane("Nếu khoảng cách từ S đến (ABCD) bằng 3 thì SC bằng bao nhiêu?"),
    _dist_plane("Nếu SB = 4 thì khoảng cách từ S đến (ABCD) bằng bao nhiêu?"),
    _dist_plane("Khi SB = 4 thì khoảng cách từ S đến (ABCD) bằng bao nhiêu?"),
    _dist_plane("Chứng minh khoảng cách từ S đến (ABCD) bằng 3 và tính SC."),
    _dist_plane("Khoảng cách từ S đến (ABCD) bằng 3 (xem câu hỏi 2)."),
    _volume("Thể tích khối chóp S.ABCD bằng 4, tính SC."),
    ask("q", "Góc giữa SC và (ABCD) có cos² bằng 9/17, tính SB.", "angle", points_a=["S", "C"], points_b=list("ABCD")),
    ask("q", "Ta tính được SC = √17.", "length", points=["S", "C"]),
    _dist_line("Khi khoảng cách từ S đến BD có giá trị 4 thì SC bằng bao nhiêu?"),
    _dist_line("Biết khoảng cách từ S đến BD được cho bằng 4, tính SC."),
]


@pytest.mark.parametrize("question", ASK_NOT_FOR_THIS_OBJECT, ids=[a["quotes"][0] for a in ASK_NOT_FOR_THIS_OBJECT])
def test_ask_for_an_object_that_is_not_asked_is_refused(question):
    r = _run(question)
    assert r.status == "REFUSED", (r.answers, question["quotes"])


ASKED_FOR_THIS_OBJECT = [
    (_dist_plane("Tính SC và khoảng cách từ S đến (ABCD)."), F(9)),
    (_volume("Tính thể tích khối chóp S.ABCD biết SA = 3."), F(16)),
    (_volume("Cho SA = 3, tính thể tích khối chóp S.ABCD."), F(16)),
    (_dist_line("Tính khoảng cách từ S đến đường thẳng BD."), F(11)),
    (ask("q", "Tính độ dài đoạn SC.", "length", points=["S", "C"]), F(17)),
    (_volume("Khi đó, thể tích khối chóp S.ABCD bằng bao nhiêu?"), F(16)),
]


@pytest.mark.parametrize("question,sq", ASKED_FOR_THIS_OBJECT, ids=[a["quotes"][0] for a, _ in ASKED_FOR_THIS_OBJECT])
def test_ask_for_the_asked_object_is_still_answered(question, sq):
    r = _run(question)
    assert r.status == "SERVED" and HB.answer_square(r.answers["q"]) == sq, (r.code, r.reason)


# C2: clauses opened by markers other than "nếu", an antecedent marked only by "thì", and question clauses are not givens.
NOT_A_GIVEN_2 = [
    "Khi SA vuông góc với (ABCD) thì SC = 5.",
    "Giả sử SA vuông góc với (ABCD), khi đó SC = 5.",
    "Trong trường hợp SA vuông góc với (ABCD), hãy so sánh SB và SD.",
    "Với điều kiện SA vuông góc với (ABCD), SC = 5.",
    "Trừ khi SA vuông góc với (ABCD), SC = 5.",
    "SA vuông góc với (ABCD) thì SC bằng bao nhiêu?",
    "Hỏi SA có vuông góc với (ABCD) không?",
    "Phải chăng SA vuông góc với (ABCD)?",
    "Hãy kiểm tra xem SA vuông góc với (ABCD) hay không.",
]


@pytest.mark.parametrize("sentence", NOT_A_GIVEN_2)
def test_conditional_or_question_clause_is_not_a_given(sentence):
    q, facts = HB._with(_no_perpendicular(), SC)
    q.insert(-1, sentence)
    facts.insert(-1, _perp(sentence))
    r = run_fact_route(" ".join(q), {"facts": facts})
    assert r.status == "REFUSED", (r.answers, sentence)


@pytest.mark.parametrize("question,sq", [
    # Re-verification of review 2: questions the stricter gate must still answer.
    (ask("q", "Chứng minh SC vuông góc BD và tính SC.", "length", points=["S", "C"]), F(17)),
    (ask("q", "Chứng minh BD vuông góc SC, từ đó tính SC.", "length", points=["S", "C"]), F(17)),
    (ask("q", "Tính độ dài SC (làm tròn đến 2 chữ số thập phân).", "length", points=["S", "C"]), F(17)),
], ids=["proof-then-ask-same-label", "proof-tu-do-ask", "rounding-number"])
def test_asked_object_after_a_proof_or_with_an_unrelated_number_is_answered(question, sq):
    r = _run(question)
    assert r.status == "SERVED" and HB.answer_square(r.answers["q"]) == sq, (r.code, r.reason)


@pytest.mark.parametrize("question", [
    # Second re-verification (N2): the question verb governs ANOTHER object; the distance is only mentioned.
    _dist_plane("Tính SC, ở đây khoảng cách từ S đến (ABCD) gấp đôi SB."),
    _dist_plane("Tính SC theo khoảng cách từ S đến (ABCD)."),
    _dist_plane("Tính tỉ số giữa SC và khoảng cách từ S đến (ABCD)."),
    _dist_plane("Tìm M sao cho khoảng cách từ S đến (ABCD) nhỏ nhất?"),
    # minor: a yes/no question is not a request for the value
    _dist_plane("Hỏi khoảng cách từ S đến (ABCD) có bằng 3 không?"),
    # final pass: a yes/no relation with no assignment verb ("vượt quá") was still answered with the value
    _volume("Thể tích khối chóp S.ABCD có vượt quá 5 không?"),
    _volume("Hỏi thể tích khối chóp S.ABCD đã vượt quá 5 hay chưa?"),
    _dist_plane("Khoảng cách từ S đến (ABCD) có đạt tới 5 không?"),
], ids=["o-day-gap-doi", "theo", "ti-so", "sao-cho-nho-nhat", "yes-no", "yes-no-vuot-qua", "yes-no-hay-chua",
        "yes-no-dat-toi"])
def test_object_that_is_not_the_question_verbs_object_is_refused(question):
    r = _run(question)
    assert r.status == "REFUSED", (r.answers, question["quotes"])


@pytest.mark.parametrize("sentence", ["Khi đó, SA vuông góc với (ABCD).", "Biết rằng SA vuông góc với (ABCD).",
                                      "Ta có SA vuông góc với (ABCD).", "Cho biết SA vuông góc với (ABCD)."])
def test_ordinary_premises_stay_givens(sentence):
    q, facts = HB._with(_no_perpendicular(), SC)
    q.insert(-1, sentence)
    facts.insert(-1, _perp(sentence))
    r = run_fact_route(" ".join(q), {"facts": facts})
    assert r.answers == {"q": "√17"}, (r.code, r.reason)


# Source mutants of the fix must be killed.
def _mutant(monkeypatch, old, new):
    src = Path(RG.__file__).read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    m = types.ModuleType(RG.__name__ + "_mutant")
    m.__package__ = RG.__package__
    monkeypatch.setitem(sys.modules, m.__name__, m)
    exec(compile(src.replace(old, new), RG.__file__, "exec"), m.__dict__)
    m.TuChoi = RG.TuChoi
    from app.simulation.geometry_functions import engine as EN

    monkeypatch.setattr(EN, "kiem_nguon", m.kiem_nguon)                  # the engine holds its own reference


def _code(fact, base):
    q, facts = HB._with(base(), SC)
    q.insert(-1, fact["quotes"][0])
    facts.insert(-1, fact)
    return run_fact_route(" ".join(q), {"facts": facts}).code


def _consequent_code():
    """'Nếu SB = 4 thì SA vuông góc với (ABCD).' with the premise quote starting after 'thì'."""
    q, facts = HB._with(_no_perpendicular(), SC)
    text = " ".join(q[:-1]) + " Nếu SB = 4 thì SA vuông góc với (ABCD). " + q[-1]
    facts.insert(-1, _perp("SA vuông góc với (ABCD)"))
    return run_fact_route(text, {"facts": facts}).code


MUTANTS = [
    # Mutants re-pointed to the shared clause analyser of review 2 (`_vai_tro_tai`, `_kiem_cau_hoi`, `_duoc_hoi`).
    ("anchors inside the quote ignored", "for pos in _moc_menh_de(c, de, dau, _c)}", "for pos in [dau]}",
     lambda: _code(_perp("Chứng minh rằng SA vuông góc với (ABCD)."), _no_perpendicular) != "GOAL_CLAUSE_NOT_PREMISE"),
    ("condition markers dropped", "if _DIEU_KIEN.search(truoc) or _THI.search(de[p:b]):", "if False:",
     lambda: _consequent_code() != "CONDITIONAL_CLAUSE"),
    ("ask check dropped", "            _kiem_cau_hoi(c, de, vts)\n", "            pass\n",
     lambda: _run(NOT_ASKED[0]).code != "NOT_ASKED_IN_SOURCE"),
    ("question-clause role dropped", "if _HOI_QUAN_HE.search(de[ma:mb]):", "if False:",
     lambda: _code(_perp("Phải chăng SA vuông góc với (ABCD)?"), _no_perpendicular) != "QUESTION_CLAUSE_NOT_PREMISE"),
    ("asserted-value check dropped", "if (so := _GIA_TRI.search(gan)) and not _HOI_SAU.search(gan[:so.start()]):", "if False:",
     lambda: _run(_dist_plane("Ta tính được khoảng cách từ S đến (ABCD) bằng 3.")).status != "REFUSED"),
    ("object blocker between verb and object dropped",
     "qua_dong_tu = bool(dong_tu) and not _CHAN_TAN_NGU.search(", "qua_dong_tu = bool(dong_tu) or not _CHAN_TAN_NGU.search(",
     lambda: _run(_dist_plane("Tính SC theo khoảng cách từ S đến (ABCD).")).status != "REFUSED"),
    ("label anchor by any shared label", "if frozenset(n for p in phan for n in p) in toan_hang]",
     "if any(n in nhan_cua_loi_goi(c) for p in phan for n in p)]",
     lambda: _run(_dist_plane("Khoảng cách từ S đến (ABCD) bằng 3, tính SC.")).status != "REFUSED"),
    ("yes/no relation check dropped", "    if _CO_KHONG.search(gan) and not", "    if False and not",
     lambda: _run(_volume("Thể tích khối chóp S.ABCD có vượt quá 5 không?")).status != "REFUSED"),
]


@pytest.mark.parametrize("name,old,new,killed", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(monkeypatch, name, old, new, killed):
    assert not killed(), "the unmutated code must pass the kill check"
    _mutant(monkeypatch, old, new)
    assert killed(), f"mutant survived: {name}"
