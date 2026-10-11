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
    assert (r.status, r.code) == ("REFUSED", "NOT_ASKED_IN_SOURCE"), (r.answers, r.reason)


@pytest.mark.parametrize("question,sq", ASKED, ids=[a["quotes"][0] for a, _ in ASKED])
def test_asking_sentences_are_still_answered(question, sq):
    r = _run(question)
    assert HB.answer_square(r.answers["q"]) == sq, (r.code, r.reason)


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
    ("anchors inside the quote ignored", "positions = _moc_menh_de(c, de, dau, _c)", "positions = [dau]",
     lambda: _code(_perp("Nếu SA vuông góc với (ABCD) thì SC = 5."), _no_perpendicular) != "CONDITIONAL_CLAUSE"),
    ("consequent rule dropped", "if any(_NEU.search(de[_cau_chua(de, pos):pos]) for pos in positions):",
     "if False:", lambda: _consequent_code() != "CONDITIONAL_CLAUSE"),
    ("ask check dropped", 'if c.spec.kind == "ask" and not _hoi_trong_cau(c, de, vts):', "if False:",
     lambda: _run(NOT_ASKED[0]).code != "NOT_ASKED_IN_SOURCE"),
]


@pytest.mark.parametrize("name,old,new,killed", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(monkeypatch, name, old, new, killed):
    assert not killed(), "the unmutated code must pass the kill check"
    _mutant(monkeypatch, old, new)
    assert killed(), f"mutant survived: {name}"
