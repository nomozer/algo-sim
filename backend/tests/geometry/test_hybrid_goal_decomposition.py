"""Goal decomposition, slice 1 (run `hybrid-goal-decomposition`): distance(point, line) = orthogonal_projection_line onto an
AUXILIARY foot + ask_length, inside the existing planner. Approved scope: B26 only (no Typed Facts / prompt / provider
change).

Evidence classes kept apart: `facts` = verified Typed Facts → compiler; `pipeline` = text → FAKE provider → extraction
adapter → compiler. Neither says anything about what a real model extracts. Expected values come from the independent
oracle of `hybrid_compiler_benchmark` (no product import), never from engine output.
"""
from __future__ import annotations

import json
import sys
import types
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions import planner as PL
from app.simulation.geometry_functions import registry as RG
from app.simulation.geometry_functions.registry import TuChoi
from tests.geometry import hybrid_compiler_benchmark as HB

A, B, C, D, S, O = HB.A, HB.B, HB.C, HB.D, HB.S, HB.O
ARMS = ("facts", "pipeline")


def _problem(*extra, base=None):
    q, f = HB._with(base or HB._square(), *extra)
    return {"id": "q", "text": " ".join(q), "facts": f}


def _dist(qtext, p, line, fid="q", **kw):
    return HB._ask(fid, qtext, "distance", points_a=[p], points_b=list(line), **kw)


def _run(case, arm="facts"):
    return HB.run(case, arm)


def _both(case):
    rs = [_run(case, a) for a in ARMS]
    assert (rs[0].status, rs[0].code, rs[0].answers) == (rs[1].status, rs[1].code, rs[1].answers), rs
    return rs[0]


def _served(case, expected_sq, qid="q"):
    r = _both(case)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers[qid]) == expected_sq, r.answers
    return r


def _refused(case, *codes):
    r = _both(case)
    assert r.status == "REFUSED" and r.code in codes, (r.status, r.code, r.reason, r.answers)
    return r


# ── 1. served cases, oracle-checked, both evaluations ───────────────────────────────────────────────────────────

def test_point_off_the_line_b26():
    r = _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD")), HB.dist2_point_line(S, B, D))
    assert HB.dist2_point_line(S, B, D) == 11


def test_auxiliary_provenance_and_trace():
    r = _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD")), F(11))
    (aux,) = r.planner["auxiliary"]
    assert aux == {"label": "H", "rule": "distance(point,line)", "goal": "q", "construct": "q_aux", "ask": "q", "point": "S",
                   "line": ["B", "D"], "quotes": ["Tính khoảng cách từ S đến BD."], "provenance": "DERIVED",
                   "binding": "AUXILIARY"}
    assert "H" not in RG.nhan_cua_de(_problem()["text"])
    # trace: goal → decomposition rule → function calls
    dec = [t for t in r.planner["trace"] if t.get("step") == "decompose_goal"]
    assert dec == [{"fact": "q", "step": "decompose_goal", "rule": "distance(point,line)", "calls": ["q_aux", "q"],
                    "auxiliary": "H", "provenance": "DERIVED", "binding": "AUXILIARY"}]
    assert [(c["id"], c["fn"]) for c in r.planner["calls"] if "H" in json.dumps(c["args"])] == [
        ("q_aux", "orthogonal_projection_line"), ("q", "ask_length")]
    # engine placed H as a DERIVED construction, bound AUXILIARY, relation verified — never a given/layout point
    (h,) = [s for s in r.trace if s.get("object") == "H"]
    assert (h["provenance"], h["binding"], h["producer"], h["relation_verified"]) == (
        "DERIVED", "AUXILIARY", "orthogonal_projection_line", True)
    # the auxiliary never becomes a premise: no fact call mentions it, its only quote is the question
    assert all(c["fn"] in ("orthogonal_projection_line", "ask_length") for c in r.calls if "H" in json.dumps(c["args"]))
    assert {q for c in r.calls if "H" in json.dumps(c["args"]) for q in c["quotes"]} == {"Tính khoảng cách từ S đến BD."}
    # independent geometric check of the foot (oracle, not engine)
    o = next(o for o in r.scene3d["objects"] if o["id"] == "H")
    assert o["perpendicular_witness"]["from"] == "S"


def test_point_on_the_line_is_distance_zero():
    """O ∈ BD: the foot coincides with O and the distance is 0 — the same result route A gives for the STATED projection
    (contract unchanged; no special case in the decomposition)."""
    case = _problem(HB._ill("f5", "O", "AC", "BD"), _dist("Tính khoảng cách từ O đến BD.", "O", "BD"))
    assert HB.dist2_point_line(O, B, D) == 0
    r = _served(case, F(0))
    assert r.points["H"] == r.points["O"]
    stated = _problem(HB._ill("f5", "O", "AC", "BD"), HB._proj("f6", "K", "O", "BD"),
                      HB._ask("q", "Tính độ dài OK.", "length", points=["O", "K"]))
    assert _run(stated).answers == {"q": "0"}
    _served(_problem(_dist("Tính khoảng cách từ B đến BD.", "B", "BD")), F(0))     # endpoint of the line


def test_dependency_on_derived_points():
    m = HB.mid(S, C)
    _served(_problem(HB._mid("f5", "M", "S", "C"), _dist("Tính khoảng cách từ M đến BD.", "M", "BD")),
            HB.dist2_point_line(m, B, D))
    r = _served(_problem(HB._ill("f5", "O", "AC", "BD"), _dist("Tính khoảng cách từ A đến SO.", "A", "SO")),
                HB.dist2_point_line(A, S, O))
    assert r.trace.index(next(s for s in r.trace if s.get("object") == "O")) < \
           r.trace.index(next(s for s in r.trace if s.get("object") == "H"))           # foot built after its operand
    # derived point AND derived line
    _served(_problem(HB._mid("f5", "M", "S", "C"), HB._ill("f6", "O", "AC", "BD"),
                     _dist("Tính khoảng cách từ M đến AO.", "M", "AO")), HB.dist2_point_line(m, A, O))


def test_two_goals_get_distinct_auxiliaries():
    case = _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD", fid="q"),
                    _dist("Tính khoảng cách từ C đến SB.", "C", "SB", fid="r"))
    r = _served(case, HB.dist2_point_line(S, B, D))
    assert HB.answer_square(r.answers["r"]) == HB.dist2_point_line(C, S, B)
    assert [a["label"] for a in r.planner["auxiliary"]] == ["H", "H1"]


# ── 2. metamorphic ──────────────────────────────────────────────────────────────────────────────────────────────

def test_renamed_points():
    t, m, n, p, q = (HB._v(0, 0, 3), HB._v(0, 0, 0), HB._v(2, 0, 0), HB._v(2, 2, 0), HB._v(0, 2, 0))
    _served(_problem(_dist("Tính khoảng cách từ T đến NQ.", "T", "NQ"), base=HB._square("TMNPQ")),
            HB.dist2_point_line(t, n, q))


def test_reordered_clauses_and_facts():
    sents, facts = HB._with(HB._square(), HB._mid("f5", "M", "S", "C"), _dist("Tính khoảng cách từ M đến BD.", "M", "BD"))
    case = {"id": "q", "text": " ".join(reversed(sents)), "facts": list(reversed(facts))}
    r = _served(case, HB.dist2_point_line(HB.mid(S, C), B, D))
    assert [a["label"] for a in r.planner["auxiliary"]] == ["H"]


def test_scaling_multiplies_the_squared_distance():
    q, f = HB._square()
    q = [x.replace("cạnh 2", "cạnh 4").replace("= 3", "= 6") for x in q]
    f = [{**x, "quotes": [q[i]], **({"value": {"2": "4", "3": "6"}[x["value"]]} if x.get("value") else {})}
         for i, x in enumerate(f)]
    _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"), base=(q, f)), 4 * HB.dist2_point_line(S, B, D))


def test_auxiliary_label_avoids_every_label_of_the_text():
    case = _problem(HB._mid("f5", "H", "S", "C"), _dist("Tính khoảng cách từ S đến BD.", "S", "BD"))
    r = _served(case, F(11))
    assert r.planner["auxiliary"][0]["label"] == "H1"
    case = _problem(HB._mid("f5", "H", "S", "C"), HB._mid("f6", "H1", "S", "B"), _dist("Tính khoảng cách từ S đến BD.", "S", "BD"))
    assert _served(case, F(11)).planner["auxiliary"][0]["label"] == "H2"


# ── 3. refusals: the decomposition never makes a refused problem served ────────────────────────────────────────

def test_missing_data():
    sq = HB._square()
    _refused(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"), base=(sq[0][:3], sq[1][:3])),
             "MISSING_DIMENSION", "UNDERDETERMINED_POINT")


def test_contradictory_data():
    _refused(_problem(HB._f("f5", "length", "SB = 5.", points=["S", "B"], measure="segment", value="5"),
                      _dist("Tính khoảng cách từ S đến BD.", "S", "BD")), "INCONSISTENT_FACTS")


def test_several_configurations_are_refused():
    """Height given, foot unknown: the apex is not determined and the distance to BD depends on it ⇒ refuse."""
    q, f = HB._square()
    base = ([q[0], q[1], "Chiều cao của khối chóp S.ABCD bằng 3."],
            [f[0], f[1], HB._f("f3", "length", "Chiều cao của khối chóp S.ABCD bằng 3.", solid="S.ABCD", measure="height",
                               value="3")])
    _refused(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"), base=base), "UNDERDETERMINED_POINT")


def test_line_not_determined():
    _refused(_problem(_dist("Tính khoảng cách từ S đến BM.", "S", "BM")), "UNDERDETERMINED_POINT")


def test_degenerate_line():
    _refused(_problem(_dist("Tính khoảng cách từ S đến BB.", "S", "BB")), "DEGENERATE_POINTS")   # kernel, not sampled


def test_question_in_a_proof_clause_is_refused_by_the_gate():
    _refused(_problem(_dist("Chứng minh rằng khoảng cách từ S đến BD bằng √11.", "S", "BD")), "GOAL_CLAUSE_NOT_PREMISE")


def test_negated_question_is_not_decomposed():
    raw = {"facts": _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD", negated=True))["facts"]}
    with pytest.raises(TuChoi) as e:
        PL.lap_ke_hoach(raw)
    assert e.value.code == "UNSUPPORTED_CAPABILITY"


def test_proof_goal_is_not_decomposed():
    f = HB._f("q", "question", "Tính khoảng cách từ S đến BD.", role="prove", quantity="distance", points_a=["S"],
              points_b=["B", "D"])
    with pytest.raises(TuChoi) as e:
        PL.lap_ke_hoach({"facts": _problem(f)["facts"]})
    assert e.value.code == "UNSUPPORTED_CAPABILITY"


def test_conditional_fact_is_refused_before_planning():
    _refused(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD") | {"role": "condition"}), "CONDITIONAL_CLAUSE")


def test_question_inside_a_conditional_clause_is_refused_by_the_gate():
    case = _problem(_dist("Nếu khoảng cách từ S đến BD bằng √11 thì SA = 3.", "S", "BD"))
    _refused(case, "CONDITIONAL_CLAUSE")


def test_negated_quote_is_refused_by_the_gate():
    _refused(_problem(_dist("Khoảng cách từ S đến BD không phải là 3.", "S", "BD")), "NEGATED_CLAUSE")


def test_question_that_names_another_point_is_refused():
    _refused(_problem(_dist("Tính khoảng cách từ A đến BD.", "S", "BD")), "SOURCE_OBJECT_MISMATCH")


def test_question_that_names_another_line_is_refused():
    _refused(_problem(_dist("Tính khoảng cách từ S đến BC.", "S", "BD")), "SOURCE_OBJECT_MISMATCH")


def test_question_without_distance_wording_is_refused():
    _refused(_problem(_dist("Tính độ dài từ S đến BD.", "S", "BD")), "SOURCE_OBJECT_MISMATCH")


# Independent review (run `hybrid-slice1-review`), Important 1: the gate refused listed roles only. A clause the AI mis-types
# as a question — proof-only, hypothetical, asserted or negated value — must not be answered.
NOT_ASKED = [
    ("Hãy chỉ ra rằng khoảng cách từ S đến BD bằng √11.", ""),
    ("Gọi d là khoảng cách từ S đến BD.", " Chứng minh rằng d = √11."),
    ("Chứng minh rằng, biết khoảng cách từ S đến BD bằng √11, thì SA = 3.", ""),
    ("Giả sử khoảng cách từ S đến BD bằng 4.", " Tính SC."),
    ("Khi khoảng cách từ S đến BD bằng 4 thì SC bằng bao nhiêu?", ""),
    ("Biết khoảng cách từ S đến BD bằng 4.", " Tính SC."),
    ("Khoảng cách từ S đến BD không bằng 3.", ""),
    ("Khoảng cách từ S đến BD chẳng bằng 3.", ""),
    ("Khoảng cách từ S đến BD khác 3.", ""),
]


@pytest.mark.parametrize("sentence,tail", NOT_ASKED, ids=[s for s, _ in NOT_ASKED])
def test_clause_that_does_not_ask_the_distance_is_refused(sentence, tail):
    case = _problem(_dist(sentence, "S", "BD"))
    case["text"] += tail
    r = _both(case)
    assert r.status == "REFUSED", (r.answers, sentence)


ASKED = ["Tính khoảng cách từ S đến BD.", "Khoảng cách từ S đến BD bằng bao nhiêu?",
         "Tìm khoảng cách từ S đến đường thẳng BD.", "Hãy tính khoảng cách từ điểm S tới BD.",
         "Xác định khoảng cách từ S đến BD."]


@pytest.mark.parametrize("sentence", ASKED)
def test_question_wordings_are_still_served(sentence):
    _served(_problem(_dist(sentence, "S", "BD")), F(11))


def _source_vs_quote(source, quote):
    """The AI quotes `quote`; the problem actually says `source` in its place (the quote is only a locator)."""
    case = _problem(_dist(quote, "S", "BD"))
    case["text"] = case["text"].replace(quote, source)
    assert source in case["text"]
    return case


# Independent review of efb756aa (run `source-bound-result-planning-main-integration`), IMPORTANT-2: the auxiliary
# distance(point, line) ask used an open two-word denylist. Any other quantity built on the distance was answered with the
# distance itself (√11). The ask must be the bare object under the same closed grammar as every ordinary ask.
ALTERED = ["Tính bình phương khoảng cách từ S đến BD.", "Tính nửa khoảng cách từ S đến BD.",
           "Tính một nửa khoảng cách từ S đến BD.", "Tính hai lần khoảng cách từ S đến BD.",
           "Tính căn bậc hai của khoảng cách từ S đến BD.", "Tính lập phương khoảng cách từ S đến BD.",
           "Tính nghịch đảo khoảng cách từ S đến BD.", "Tính một phần ba khoảng cách từ S đến BD.",
           "Tính 1/2 khoảng cách từ S đến BD.", "Tính giá trị bình phương khoảng cách từ S đến BD.",
           "Tính khoảng cách từ S đến BD bình phương.", "TÍNH BÌNH PHƯƠNG KHOẢNG CÁCH TỪ S ĐẾN BD."]


@pytest.mark.parametrize("sentence", ALTERED)
def test_a_quantity_built_on_the_distance_is_not_answered_with_the_distance(sentence):
    _refused(_problem(_dist(sentence, "S", "BD")), "NOT_ASKED_IN_SOURCE")


# IMPORTANT-1: the modifier check read the problem with the AI quote spliced in. A quote that differs from the source only
# in whitespace (still located by `_vi_tri`), or that leaves the modifier out, hid the modifier the problem actually wrote.
SUBSTITUTED = [("Tính bình phương khoảng cách từ S đến BD.", "Tính bìnhphương khoảng cách từ S đến BD."),
               ("Tính bình phương khoảng cách từ S đến BD.", "bìnhphươngkhoảng cách từ S đến BD."),
               ("Tính bình phương khoảng cách từ S đến BD.", "khoảng cách từ S đến BD."),
               ("Tính hai lần khoảng cách từ S đến BD.", "khoảng cách từ S đến BD."),
               ("Tính hai lần khoảng cách từ S đến BD.", "Tính hailần khoảng cách từ S đến BD."),
               ("Tính khoảng cách từ S đến BD bình phương.", "Tính khoảng cách từ S đến BDbình phương.")]


@pytest.mark.parametrize("source,quote", SUBSTITUTED, ids=[q for _, q in SUBSTITUTED])
def test_the_source_not_the_quote_decides_what_is_asked(source, quote):
    _refused(_source_vs_quote(source, quote), "NOT_ASKED_IN_SOURCE")


# Independent review of 2427289a, CRITICAL-1 (regression part): the closed grammar reads only from the last question verb,
# so a modifier earlier in the sentence was no longer seen. efb756aa refused these; they must stay refused.
EARLIER_IN_SENTENCE = ["Đáp số là bình phương của kết quả; tính khoảng cách từ S đến BD.",
                       "Lấy bình phương, tính khoảng cách từ S đến BD.",
                       "Bình phương của đại lượng sau bằng bao nhiêu: khoảng cách từ S đến BD?",
                       "Một nửa của đại lượng sau là bao nhiêu: khoảng cách từ S đến BD?",
                       "Đề hỏi bình phương; hãy tính khoảng cách từ S đến BD."]


@pytest.mark.parametrize("sentence", EARLIER_IN_SENTENCE)
def test_a_modifier_earlier_in_the_sentence_is_still_read(sentence):
    # Run `shared-ask-grammar-safety`: read by the sentence-level question-context gate (shared by every ask), not by the
    # former two-word denylist of `_kiem_phu`.
    _refused(_problem(_dist(sentence, "S", "BD")), "QUESTION_CONTEXT_UNSUPPORTED")


@pytest.mark.parametrize("quote", ["Tính", "khoảng cách từ S đến B"])
def test_the_asked_phrase_must_lie_inside_the_quoted_span(quote):
    case = _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"))
    case["facts"][-1]["quotes"] = [quote]
    _refused(case, "SOURCE_OBJECT_MISMATCH")


# Controls: the closed grammar must not turn into "refuse every question".
def test_hon_nua_is_not_nua_and_a_whitespace_variant_quote_of_a_plain_question_is_served():
    _served(_problem(_dist("Hơn nữa, tính khoảng cách từ S đến BD.", "S", "BD")), F(11))
    _served(_source_vs_quote("Tính khoảng cách từ S đến BD.", "Tính khoảngcách từ S đến BD."), F(11))


def test_an_unread_second_ask_in_the_clause_is_refused_as_on_ordinary_asks():
    """Fail-closed by design, same as `ask_distance_point_plane` / `ask_length`: an ask nobody answers is unread."""
    _refused(_problem(_dist("Tính khoảng cách từ S đến BD và nửa chu vi đáy.", "S", "BD")), "NOT_ASKED_IN_SOURCE")


def test_nua_mat_phang_in_an_earlier_sentence_does_not_reach_the_question_gate():
    case = _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"))
    case["text"] = case["text"].replace("Tính khoảng cách", "Xét nửa mặt phẳng bờ BD. Tính khoảng cách")
    _refused(case, "SOURCE_PREMISE_UNREAD")    # the unread premise sentence, not the asked object


# Important 2: labels the scanner reads differently (subscript, underscore, glued to other letters) still occupy the name.
@pytest.mark.parametrize("sentence,expected", [
    ("Gọi H₁ là hình chiếu của C lên BD.", "H2"), ("Gọi H_1 là hình chiếu của C lên BD.", "H2"),
    ("Xét tam giác ΔSHD.", "H1"), ("Lấy điểmH trên SD.", "H1"), ("Hình vuông ABCD có cạnh 2.", "H")])
def test_auxiliary_label_avoids_labels_the_scanner_misreads(sentence, expected):
    q, f = HB._square()
    case = _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"), base=(q + [sentence], f))
    # the planner's label choice is the property under test
    assert PL.lap_ke_hoach({"facts": case["facts"]}, case["text"]).auxiliary[0]["label"] == expected
    # run source-grounding-completeness: the sentence is a premise no fact reads, so the route refuses it as a whole
    assert _run(case).code == "SOURCE_PREMISE_UNREAD"


def _subscript_collision_code() -> str | None:
    """A declaration (tampered past the planner) whose label H1 is written H₁ in the text."""
    text, k = _plan()
    text += " Gọi H₁ là trung điểm SC."
    k.auxiliary[0]["label"] = "H1"
    for c in k.calls:
        c["args"] = json.loads(json.dumps(c["args"]).replace('"H"', '"H1"'))
    return run_function_route(text, {"calls": k.calls}, tuple(k.auxiliary)).code


def test_gate_refuses_an_auxiliary_label_written_with_a_subscript_in_the_text():
    assert _subscript_collision_code() == "AUXILIARY_LABEL_COLLISION"


# Minor findings fixed in scope: trace attribution, construct id clash, duplicate declaration label.
def test_trace_attributes_auxiliary_calls_to_the_question_fact():
    r = _served(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD", fid="cau_2")), F(11), qid="cau_2")
    assert {t["fact"] for t in r.planner["trace"] if "cau_2" in str(t.get("call", "")) or t.get("step")} == {"cau_2"}


def test_construct_id_never_clashes_with_a_fact_id():
    case = _problem(HB._mid("q_aux", "M", "S", "C"), _dist("Tính khoảng cách từ S đến BD.", "S", "BD"))
    _served(case, F(11))


def _duplicate_label_code() -> str | None:
    p = _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD", fid="q"),
                 _dist("Tính khoảng cách từ C đến SB.", "C", "SB", fid="r"))
    k = PL.lap_ke_hoach({"facts": p["facts"]}, p["text"])
    k.auxiliary[1]["label"] = "H"
    for c in k.calls:
        if c["id"].startswith("r"):
            c["args"] = json.loads(json.dumps(c["args"]).replace('"H1"', '"H"'))
    return run_function_route(p["text"], {"calls": k.calls}, tuple(k.auxiliary)).code


def test_two_declarations_cannot_share_a_label():
    assert _duplicate_label_code() == "AUXILIARY_RULE_MISMATCH"


# ── 4. the gate: only a planner declaration admits an auxiliary; route A cannot ─────────────────────────────────

def _plan():
    p = _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"))
    k = PL.lap_ke_hoach({"facts": p["facts"]}, p["text"])
    return p["text"], k


def test_route_a_cannot_introduce_an_auxiliary():
    text, k = _plan()
    r = run_function_route(text, {"calls": k.calls})                         # same calls, no planner declaration
    assert (r.status, r.code) == ("REFUSED", "UNKNOWN_LABEL")
    src = (Path(RG.__file__).parents[2] / "ai" / "function_calling.py").read_text(encoding="utf-8")
    assert "auxiliary" not in src                                          # A has no path that could pass one


@pytest.mark.parametrize("tamper,code", [
    (lambda d, k: d.update(label="S"), "AUXILIARY_LABEL_COLLISION"),               # collides with the text
    (lambda d, k: d.update(rule="distance(point,plane)"), "AUXILIARY_RULE_MISMATCH"),  # no such rule
    (lambda d, k: d.update(point="A"), "AUXILIARY_RULE_MISMATCH"),                 # declaration ≠ calls
    (lambda d, k: d.update(construct="f1"), "AUXILIARY_RULE_MISMATCH"),            # wrong call
    (lambda d, k: d.update(quotes=["SA = 3."]), "AUXILIARY_RULE_MISMATCH"),        # quote not the question's
    (lambda d, k: k.calls.append({"id": "zz", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "H"]},
                                  "source": {"quotes": ["Tính khoảng cách từ S đến BD."]}}), "UNKNOWN_LABEL"),  # leak
])
def test_tampered_declarations_are_refused(tamper, code):
    text, k = _plan()
    (d,) = k.auxiliary
    tamper(d, k)
    r = run_function_route(text, {"calls": k.calls}, tuple(k.auxiliary))
    assert (r.status, r.code) == ("REFUSED", code), r.reason


def test_provider_surfaces_are_pinned():
    """Any change of the model-facing surface must be a deliberate, recorded decision.

    History: goal decomposition slice 1 changed nothing (A 1e3f71ea…, B a4f368cb…, declarations 41e090cd…). The
    user-approved section / intersection-line slice (run `hybrid-section-slice`) added `section`, `intersection_line`,
    `ask_section_area` (A declarations) and two Typed Fact kinds + one prompt rule (B). The goal-directed section slice
    (run `goal-directed-section-planning`) left A and the declarations byte-identical (its `translate_point` is planner-only)
    and added one optional Typed Fact field `plane_relation` + prompt rule 8 (B: 396f1c9c… → value below)."""
    import hashlib

    from app.ai import fact_extraction as FE
    from app.ai import function_calling as FC

    # source-bound-result-planning: intentional optional reference transport, approved preregistration.
    # The previous measured pins remain immutable in their historical runs; this receipt is a new correction layer.
    receipt = Path(__file__).resolve().parents[3] / 'docs/evaluation/geometry/runs/source-bound-result-planning/provider-surfaces.json'
    pins = json.loads(receipt.read_text(encoding='utf-8'))['current']
    assert FC.surface_fingerprint() == pins['A']
    assert FE.surface_fingerprint() == pins['B']
    decl = json.dumps(RG.function_declarations(), ensure_ascii=False, sort_keys=True).encode()
    assert hashlib.sha256(decl).hexdigest() == pins['declarations']


# ── 5. source mutants of the new code must be killed ───────────────────────────────────────────────────────────

def _mutant(monkeypatch, mod, old, new):
    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    m = types.ModuleType(mod.__name__ + "_mutant")
    m.__package__ = mod.__package__
    monkeypatch.setitem(sys.modules, m.__name__, m)                        # dataclasses resolve annotations through it
    exec(compile(src.replace(old, new), mod.__file__, "exec"), m.__dict__)
    m.TuChoi = RG.TuChoi                                                   # same exception class as the engine catches
    return m


def _tampered_code(**update) -> str | None:
    text, k = _plan()
    k.auxiliary[0].update(update)
    return run_function_route(text, {"calls": k.calls}, tuple(k.auxiliary)).code


def _code_of(qtext, *extra) -> str | None:
    return _run(_problem(*extra, _dist(qtext, "S", "BD"))).code


# (name, module, function, old source, mutated source, "killed" check — True when the mutant's behaviour is wrong)
MUTANTS = [
    ("gate: no collision check", RG, "_kiem_phu", "if x in chiem:", "if False:",
     lambda: _tampered_code(label="S") != "AUXILIARY_LABEL_COLLISION"),
    ("gate: scanner-only collision check", RG, "_kiem_phu", "chiem = nhan | nhan_phu_da_dung(de)", "chiem = nhan",
     lambda: _subscript_collision_code() != "AUXILIARY_LABEL_COLLISION"),
    # Kill sentences re-chosen in review 2: "Giả sử …" / "Khi … thì …" are now refused earlier as CONDITIONAL, so these
    # mutants need sentences where only the mutated check decides.
    ("gate: no 'is it asked' check", RG, "_kiem_phu", "if not all(hoi_that):", "if False:",
     lambda: _code_of("Gọi d là khoảng cách từ S đến BD.") != "NOT_ASKED_IN_SOURCE"),
    # IMPORTANT-2 of the efb756aa review: the auxiliary ask must use the closed ask grammar, not the open `_duoc_hoi`.
    ("gate: open grammar for the auxiliary ask", RG, "_kiem_phu", "hoi_that.append(_hoi_dung_cum(de, m.start(), m.end())",
     "hoi_that.append(_duoc_hoi(de, m.start(), m.end())",
     lambda: _code_of("Tính hai lần khoảng cách từ S đến BD.") != "NOT_ASKED_IN_SOURCE"),
    ("gate: duplicate labels allowed", RG, "_kiem_phu", "if x in nhan_da_khai:", "if False:",
     lambda: _duplicate_label_code() != "AUXILIARY_RULE_MISMATCH"),
    ("planner: scanner-only label choice", PL, "lap_ke_hoach", "| nhan_phu_da_dung(problem_text) |", "|",
     lambda: (lambda c: PL.lap_ke_hoach({"facts": c["facts"]}, c["text"]).auxiliary[0]["label"])(
         _problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"),
                  base=(HB._square()[0] + ["Gọi H₁ là hình chiếu của C lên BD."], HB._square()[1]))) != "H2"),
    ("gate: no structural match", RG, "_kiem_phu", "if not (dung and hoi and", "if False and not (dung and hoi and",
     lambda: _tampered_code(construct="f1") != "AUXILIARY_RULE_MISMATCH"),
    ("gate: no conditional check", RG, "_kiem_phu",
     'if "CONDITIONAL" in vai:\n            raise TuChoi("CONDITIONAL_CLAUSE", f"{hoi.id}',
     'if False:\n            raise TuChoi("CONDITIONAL_CLAUSE", f"{hoi.id}',
     lambda: _code_of("Nếu khoảng cách từ S đến BD bằng √11 thì SA = 3.") != "CONDITIONAL_CLAUSE"),
    ("gate: no proof-goal check", RG, "_kiem_phu",
     'if "GOAL" in vai:\n            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{hoi.id}',
     'if False:\n            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{hoi.id}',
     lambda: _code_of("Chứng minh rằng khoảng cách từ S đến BD bằng √11.") != "GOAL_CLAUSE_NOT_PREMISE"),
    ("gate: no negation check", RG, "_kiem_phu", "if _phu_dinh(de, vt[0], q):", "if False:",
     lambda: _code_of("Khoảng cách từ S đến BD không phải là 3.") != "NEGATED_CLAUSE"),
    ("gate: no point/line binding", RG, "_kiem_phu", "if not vai:", "if False:",
     lambda: _code_of("Tính khoảng cách từ A đến BD.") != "SOURCE_OBJECT_MISMATCH"),
    ("planner: decomposes negated goals", PL, "_cau_hoi", ' and f.role == "question" and not f.negated', "",
     lambda: _raises_code(lambda: PL.lap_ke_hoach({"facts": _problem(_dist(
         "Tính khoảng cách từ S đến BD.", "S", "BD", negated=True))["facts"]})) != "UNSUPPORTED_CAPABILITY"),
    ("planner: ignores taken labels", PL, "_EffectResolver", "if n not in self.plan.taken", "if True",
     lambda: _code_of("Tính khoảng cách từ S đến BD.", HB._mid("f5", "H", "S", "C")) is not None),
    # Run `goal-directed-function-discovery`: the asked segment is now written from the ask_length contract template; the
    # load-bearing planner step is binding each input slot to its producer's effect by position (same kill check).
    ("planner: binds a producer's effect to the wrong input slots", PL, "_EffectResolver",
     "zip(t.operands, REGISTRY[child.fn].planning.effect.operands)",
     "zip(t.operands, reversed(REGISTRY[child.fn].planning.effect.operands))",
     lambda: _run(_problem(_dist("Tính khoảng cách từ S đến BD.", "S", "BD"))).answers != {"q": "√11"}),
]


def test_equivalent_mutant_asserted_value_is_still_refused_by_the_closed_grammar(monkeypatch):
    """Since the auxiliary ask uses `_hoi_dung_cum`, dropping `_GAN_GIA_TRI` changes no outcome (it stays as defence in
    depth): an asserted value after the phrase is refused by the closed grammar itself."""
    sentence = "Ta tính được khoảng cách từ S đến BD bằng SA."
    assert _code_of(sentence) == "NOT_ASKED_IN_SOURCE"
    monkeypatch.setattr(RG, "_kiem_phu", _mutant(monkeypatch, RG, " and not _GAN_GIA_TRI.match(de[m.end():])", "")._kiem_phu)
    assert _code_of(sentence) == "NOT_ASKED_IN_SOURCE"


def _raises_code(fn):
    try:
        fn()
    except TuChoi as e:
        return e.code
    return None


@pytest.mark.parametrize("name,mod,fn,old,new,killed", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(monkeypatch, name, mod, fn, old, new, killed):
    assert not killed(), "the unmutated code must pass the kill check"
    monkeypatch.setattr(mod, fn, getattr(_mutant(monkeypatch, mod, old, new), fn))
    assert killed(), f"mutant survived: {name}"
