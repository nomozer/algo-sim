"""Premise source coverage (run `source-grounding-completeness`): a premise that could change the figure must be read.

Real routes A and B, no provider. Oracle: square base side 2, SA ⊥ base, SA = 3 ⇒ SC² = 17.
The break caught: premise sentences before the first request were never read unless a call quoted them, so
"… SA = 3. Đổi SA thành 5. Tính SC." served SC = √17 from the old figure; a long quote could also carry a change.
Rule (bounded): in the premise region, text outside sentence-local quotes of validated calls may only be closed
connector vocabulary, a goal clause or a non-geometric note; every number must be a value of a validated call.
"""
import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from tests.geometry import hybrid_compiler_benchmark as HB

ARMS = ["A", "B"]
ASK = "Tính SC."


def _route(text, facts, arm):
    payload = {"facts": facts}
    return (run_fact_route(text, payload) if arm == "B" else
            run_function_route(text, {"calls": lap_ke_hoach(payload, text).calls}))


def _with_premise(extra: str, arm: str, names: str = "SABCD"):
    base, facts = HB._square(names)
    s, c = names[0], names[3]
    ask = f"Tính {s}{c}."
    q = HB._ask("q", ask, "length", points=[s, c])
    return _route(" ".join(base) + " " + extra + " " + ask, facts + [q], arm)


CHANGES = [
    "Đổi SA thành 5.",
    "Bây giờ SA = 5.",
    "Đổi đáy thành hình vuông cạnh 4.",
    "Thay đáy bằng hình chữ nhật.",
    "Cho đáy là hình chữ nhật.",
    "SB vuông góc với (ABCD).",
    "Tăng chiều cao lên gấp đôi.",
    "Biết thêm SB = 7.",
    "Giả sử SA = 5.",
    "Chứng minh SC vuông góc với BD, biết SA = 5.",          # a given hidden inside a goal sentence
    # interrupted independent review (partial probes): changes with no label, number or listed geometry word, and
    # hypotheses after a goal clause, were served
    "Nhân đôi mọi kích thước.",
    "Bỏ giả thiết thứ ba.",
    "Phóng to gấp ba lần.",
    "Đỉnh được nâng lên gấp đôi.",
    "Chứng minh SC ⊥ BD trường hợp SA = 5.",
    "Chứng minh SC ⊥ BD lúc SA = 5.",
    "Chứng minh SC ⊥ BD, đáy ABCD là hình chữ nhật.",
]


@pytest.mark.parametrize("sentence", ["Chứng minh SC vuông góc với BD, biết SA = 5.",
                                      "Chứng minh SC vuông góc với BD trong khi SA = 5.",
                                      "Chứng minh SC vuông góc với BD và đáy là hình chữ nhật."])
def test_goal_fact_quote_does_not_cover_a_hypothesis(sentence):
    # route B: the whole sentence extracted as ONE prove fact must not make its given part "read"
    base, facts = HB._square()
    goal = HB._f("g", "perpendicular", sentence, role="prove", points_a=["S", "C"], points_b=["B", "D"])
    q = HB._ask("q", ASK, "length", points=["S", "C"])
    r = run_fact_route(" ".join(base) + " " + sentence + " " + ASK, {"facts": facts + [goal, q]})
    if "và đáy" in sentence:
        pytest.xfail("bounded: a hypothesis joined to a goal by 'và' with no marker stays inside the goal clause")
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", CHANGES)
def test_unquoted_premise_change_is_never_ignored(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "REFUSED", (r.status, r.code, r.answers)
    assert not r.answers and not r.scene3d


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence, quotes", [
    # a premise sentence quoted only in part: the rest of the clause list is unread
    ("Đáy ABCD là hình vuông cạnh 2 và SB = 7.", ["Đáy ABCD là hình vuông cạnh 2"]),
    ("Đáy ABCD là hình vuông cạnh 2, đổi SA thành 5.", ["Đáy ABCD là hình vuông cạnh 2"]),
    # a long single-sentence quote carrying a change: its number is not a value of any call
    ("Đáy ABCD là hình vuông cạnh 2 và đổi SA thành 5.", ["Đáy ABCD là hình vuông cạnh 2 và đổi SA thành 5."]),
])
def test_partly_quoted_or_long_quoted_premise_is_read(arm, sentence, quotes):
    base, facts = HB._square()
    base[1] = sentence
    facts[1] = {**facts[1], "quotes": quotes}
    q = HB._ask("q", ASK, "length", points=["S", "C"])
    r = _route(" ".join(base) + " " + ASK, facts + [q], arm)
    assert r.status == "REFUSED", (r.status, r.code, r.answers)


@pytest.mark.parametrize("arm", ARMS)
def test_quote_spanning_sentences_does_not_cover_the_second(arm):
    base, facts = HB._square()
    text = " ".join(base) + " Đổi SA thành 5. " + ASK
    facts[3] = {**facts[3], "quotes": ["SA = 3. Đổi SA thành 5."]}
    q = HB._ask("q", ASK, "length", points=["S", "C"])
    assert _route(text, facts + [q], arm).status == "REFUSED"


@pytest.mark.parametrize("arm", ARMS)
def test_construction_only_request_reads_its_premises(arm):
    base, facts = HB._square()
    mid = HB._mid("mid", "M", "S", "C")
    build = "Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB)."
    section = HB._f("section", "section", build, solid="S.ABCD", points=list("MAB"))
    text = " ".join(base + mid["quotes"] + ["Đổi đáy thành hình vuông cạnh 4.", build])
    assert _route(text, facts + [mid, section], arm).status == "REFUSED"


def test_auxiliary_decomposition_reads_its_premises():
    base, facts = HB._square()
    ask = "Tính khoảng cách từ S đến BD."
    q = HB._ask("q", ask, "distance", points_a=["S"], points_b=["B", "D"])
    text = " ".join(base) + " Đổi SA thành 5. " + ask
    assert _route(text, facts + [q], "B").status == "REFUSED"


def test_goal_directed_decomposition_reads_its_premises():
    from tests.geometry.test_goal_directed_section_planning import _pyramid_problem
    text, payload = _pyramid_problem()
    text = text.replace("Gọi M là trung điểm SC.", "Gọi M là trung điểm SC. Đổi SA thành 5.")
    assert run_fact_route(text, payload).status == "REFUSED"


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", [
    "",                                                   # the plain problem
    "Chứng minh SC vuông góc với BD.",                    # a goal: something to show, never a hypothesis
    "Hãy trình bày lời giải ngắn gọn.",                   # a note with no geometry
    "Lưu ý: kết quả để ở dạng căn thức.",
    "Hãy vẽ hình minh hoạ.",                               # a display request
    "Bài 5.",                                             # scaffolding
])
def test_non_hypothesis_premise_text_stays_served(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


@pytest.mark.parametrize("arm", ARMS)
def test_one_sentence_quoted_by_several_facts_stays_served(arm):
    sentence = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 3."
    facts = [HB._f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2", points=list("ABCD"), shape="square", value="2"),
             HB._f("f3", "perpendicular", "SA vuông góc với (ABCD)", points_a=["S", "A"], points_b=list("ABCD")),
             HB._f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3"),
             HB._ask("q", ASK, "length", points=["S", "C"])]
    r = _route(sentence + " " + ASK, facts, arm)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


# ── independent review of 996f9bc8 (BLOCKING): I1 note body, I2 goal markers, I3 role trust, I4 object names, I5 binding
@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", [
    "Lưu ý: bỏ giả thiết thứ ba.", "Lưu ý: mọi kích thước nhân đôi.", "Chú ý: phóng to gấp ba lần.",
    "Hãy giải khi mọi kích thước gấp đôi.", "Hãy làm lại với dữ kiện khác.",                       # I1
    "Chứng minh SC vuông góc BD với SA = 5.", "Chứng minh SC vuông góc BD với điều kiện SA = 5.",
    "Chứng minh SC vuông góc BD, coi như SA = 5.", "Chứng minh SC vuông góc BD đồng thời SB vuông góc (ABCD).",
    "Suy ra SA = 5.",                                                                                # I2
])
def test_review_996f9bc8_false_serves_are_refused(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("extra, fact", [
    ("SA = 5.", HB._f("g", "length", "SA = 5.", role="prove", points=["S", "A"], measure="segment", value="5")),
    ("SB vuông góc với (ABCD).", HB._f("g", "perpendicular", "SB vuông góc với (ABCD).", role="prove",
                                        points_a=["S", "B"], points_b=list("ABCD"))),
])
def test_prove_label_does_not_make_a_premise_read(extra, fact):
    # I3: the gate reads the clause role itself; an AI "prove" label on a plain premise does not cover it
    base, facts = HB._square()
    q = HB._ask("q", ASK, "length", points=["S", "C"])
    r = run_fact_route(" ".join(base) + " " + extra + " " + ASK, {"facts": facts + [fact, q]})
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence, quote3", [
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 3.",
     "SA vuông góc với mặt phẳng đáy"),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, đường thẳng SA vuông góc với mặt phẳng (ABCD), độ dài SA = 3.",
     "SA vuông góc với mặt phẳng (ABCD)"),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2 cm, SA vuông góc với mặt phẳng đáy. Chiều cao SA = 3.",
     "SA vuông góc với mặt phẳng đáy"),
])
def test_canonical_premise_wording_stays_served(arm, sentence, quote3):
    # I4: object nouns next to quoted labels ("cạnh bên SA", "độ dài SA", "chiều cao SA") and units name, never assert
    facts = [HB._f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
             HB._f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2", points=list("ABCD"), shape="square", value="2"),
             HB._f("f3", "perpendicular", quote3, points_a=["S", "A"], points_b=list("ABCD")),
             HB._f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3"),
             HB._ask("q", ASK, "length", points=["S", "C"])]
    r = _route(sentence + " " + ASK, facts, arm)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("idx, quote", [
    (2, "SA vuông góc với (ABCD) và SB = 3."),        # a length hidden in another call's quote, value coincides with SA
])
def test_number_must_be_bound_to_its_own_call(arm, idx, quote):
    # I5: a number must sit inside the quote of a call that carries that value, not merely equal some call's value
    base, facts = HB._square()
    base[idx] = quote
    facts[idx] = {**facts[idx], "quotes": [quote]}
    r = _route(" ".join(base) + " " + ASK, facts + [HB._ask("q", ASK, "length", points=["S", "C"])], arm)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", ["Hãy trình bày lời giải ngắn gọn.", "Đơn vị độ dài là cm.", "Bài tập 3."])
def test_closed_notes_stay_served(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "SERVED", (r.code, r.reason)


# ── verification of c56ccc67 (BLOCKING): goal continuations, read-range start, same-call coincidence, role nouns ──────
@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", [
    "Chứng minh SC ⊥ BD rồi đổi SA thành 5.", "Chứng minh SC ⊥ BD nhưng đáy là hình chữ nhật.",
    "Chứng minh SC ⊥ BD sau đó SB ⊥ (ABCD).",
    "Hình chóp S.ABCD có đường cao SB.", "Chiều cao SB.", "Đường cao SC.", "Hình chóp S.ABCD có mặt đáy SBC.",
    "Cạnh đáy SA.", "Lưu ý: độ dài là 5.",
])
def test_verification_c56ccc67_false_serves_are_refused(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("sentence", ["SA = 5 và chứng minh SC ⊥ BD.", "Đổi SA thành 5 rồi chứng minh SC ⊥ BD."])
def test_read_range_starts_at_the_goal_opener(sentence):
    base, facts = HB._square()
    quote = sentence.rstrip(".")
    goal = HB._f("g", "perpendicular", quote, role="prove", points_a=["S", "C"], points_b=["B", "D"])
    q = HB._ask("q", ASK, "length", points=["S", "C"])
    r = run_fact_route(" ".join(base) + " " + sentence + " " + ASK, {"facts": facts + [goal, q]})
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", ["SA = 3, đổi AB thành 3.", "SA = 3 và SB = 3."])
def test_a_call_value_backs_one_occurrence_only(arm, sentence):
    base, facts = HB._square()
    base[3] = sentence
    facts[3] = {**facts[3], "quotes": [sentence]}
    r = _route(" ".join(base) + " " + ASK, facts + [HB._ask("q", ASK, "length", points=["S", "C"])], arm)
    assert r.status == "REFUSED", (r.code, r.answers)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", ["SA = 3 và SB = 3.", "SA = 3, đổi AB thành 3."])
@pytest.mark.parametrize("quote_order", ["short_first", "long_first", "duplicate"])
def test_overlapping_quotes_do_not_multiply_a_call_value(arm, sentence, quote_order):
    base, facts = HB._square()
    base[3] = sentence
    quotes = {"short_first": ["SA = 3", sentence], "long_first": [sentence, "SA = 3"],
              "duplicate": [sentence, sentence]}[quote_order]
    facts[3] = {**facts[3], "quotes": quotes}
    r = _route(" ".join(base) + " " + ASK, facts + [HB._ask("q", ASK, "length", points=["S", "C"])], arm)
    assert r.status == "REFUSED", (r.code, r.answers)
    assert r.code == "SOURCE_PREMISE_UNREAD"
    assert not r.answers and not r.scene3d


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("quotes", [["SA = 3", "SA = 3."], ["SA = 3.", "SA = 3"], ["SA = 3.", "SA = 3."]])
def test_overlapping_quotes_of_one_verified_occurrence_stay_served(arm, quotes):
    base, facts = HB._square()
    facts[3] = {**facts[3], "quotes": quotes}
    r = _route(" ".join(base) + " " + ASK, facts + [HB._ask("q", ASK, "length", points=["S", "C"])], arm)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


P_ = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy, SA = 3."
F_ = [HB._f("f1", "solid", "Cho hình chóp S.ABCD", solid="S.ABCD", solid_type="pyramid"),
      HB._f("f2", "polygon_shape", "đáy ABCD là hình vuông cạnh 2", points=list("ABCD"), shape="square", value="2"),
      HB._f("f3", "perpendicular", "SA vuông góc với đáy", points_a=["S", "A"], points_b=list("ABCD")),
      HB._f("f4", "length", "SA = 3", points=["S", "A"], measure="segment", value="3")]


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("text, f4quote", [
    (P_ + " a) Chứng minh SC vuông góc với BD. b) Tính SC.", "SA = 3"),
    (P_ + " 1) Chứng minh SC vuông góc với BD. 2) Tính SC.", "SA = 3"),
    (P_ + " Câu a: Chứng minh SC vuông góc với BD. Câu b: Tính SC.", "SA = 3"),
    (P_.replace("SA = 3.", "độ dài cạnh SA bằng 3.") + " Tính SC.", "SA bằng 3"),
    (P_.replace("SA = 3.", "SA = 3 (đơn vị: cm).") + " Tính SC.", "SA = 3"),
    (P_.replace("SA vuông góc với đáy", "cạnh bên SA vuông góc với đáy") + " Đường cao SA. Tính SC.", "SA = 3"),
])
def test_exam_layouts_and_verified_role_nouns_stay_served(arm, text, f4quote):
    facts = [*F_[:3], {**F_[3], "quotes": [f4quote]}, HB._ask("q", "Tính SC.", "length", points=["S", "C"])]
    r = _route(text, facts, arm)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


# ── final verification of 90ce6497: chained goals and solid heights were refused (Important), lead-ins before a goal ──
CHAINED = ["Chứng minh BD ⊥ (SAC) rồi suy ra BD ⊥ SC.", "Chứng minh SC ⊥ BD rồi suy ra BD ⊥ SC.",
           "Chứng minh BD ⊥ (SAC), từ đó suy ra BD ⊥ SC.", "Hãy chứng minh SC ⊥ BD.", "Em hãy chứng minh SC ⊥ BD.",
           "Từ đó suy ra SC ⊥ BD.", "Chứng minh BD ⊥ (SAC), do đó suy ra BD ⊥ SC.", "Giải thích vì sao SC ⊥ BD.",
           "Chứng minh BC song song với (SAD)."]


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", CHAINED)
def test_chained_goals_and_goal_lead_ins_stay_served(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "SERVED", (r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


@pytest.mark.parametrize("extra", CHAINED)
def test_chained_goal_with_a_prove_fact_stays_served(extra):
    base, facts = HB._square()
    goal = HB._f("g", "perpendicular", extra.rstrip("."), role="prove", points_a=["S", "C"], points_b=["B", "D"])
    r = run_fact_route(" ".join(base) + " " + extra + " " + ASK, {"facts": facts + [goal, HB._ask("q", ASK, "length",
                                                                                                   points=["S", "C"])]})
    assert r.status == "SERVED", (r.code, r.reason)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra", [
    "Chứng minh SC ⊥ BD rồi suy ra SA = 5.", "Chứng minh SC ⊥ BD, từ đó đổi SA thành 5.", "Hãy đổi SA thành 5.",
    "Chứng minh SC ⊥ BD rồi chứng minh BD ⊥ SA với SA = 5.", "Chứng minh SC ⊥ BD rồi suy ra đáy là hình chữ nhật, SA = 5.",
    # causal / contrast continuations carried a hypothesis (pre-existing at 7767c7e1; final verification of 90ce6497)
    "Chứng minh SC ⊥ BD do SB ⊥ (ABCD).", "Chứng minh SC ⊥ BD vì SB ⊥ (ABCD).",
    "Chứng minh SC ⊥ BD bởi vì SB ⊥ (ABCD).", "Chứng minh SC ⊥ BD còn đáy là hình chữ nhật.",
    "Chứng minh SC ⊥ BD, ngoài ra đáy là hình chữ nhật.", "Chứng minh SC ⊥ BD nhờ SB ⊥ (ABCD).",
])
def test_a_chained_goal_does_not_carry_a_change(arm, extra):
    assert _with_premise(extra, arm).status == "REFUSED"


def _bench(cid: str, sentence: str, before: str, quote_of: tuple[str, str] | None = None):
    c = next(x for x in HB.cases() if x["id"] == cid)
    assert before in c["text"]
    facts = [dict(f) for f in c["facts"]]
    if quote_of:
        facts = [{**f, "quotes": [quote_of[1]]} if f["id"] == quote_of[0] else f for f in facts]
    return c["text"].replace(before, sentence + " " + before), facts


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("cid, text, before, quote_of", [
    ("B04", "Chiều cao AA' = 3.", "AA' = 3.", ("f3", "AA' = 3")),          # right prism: lateral edge is the height
    ("B04", "Đường cao AA'.", "Tính thể tích", None),
    ("B30", "Đường cao SO.", "Tính độ dài SO.", None),                       # regular pyramid: apex → base centre
    ("B30", "Chiều cao SO.", "Tính độ dài SO.", None),
])
def test_heights_of_right_prisms_and_regular_pyramids_stay_served(arm, cid, text, before, quote_of):
    t, facts = _bench(cid, text, before, quote_of)
    if quote_of:
        t = t.replace(text + " " + before, text)
    r = _route(t, facts, arm)
    assert r.status == "SERVED", (r.code, r.reason)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("cid, text, before", [
    ("B04", "Đường cao AB'.", "Tính thể tích"), ("B30", "Đường cao SA.", "Tính độ dài SO."),
    ("B30", "Chiều cao AO.", "Tính độ dài SO."),
])
def test_a_wrong_height_of_a_solid_is_refused(arm, cid, text, before):
    t, facts = _bench(cid, text, before)
    assert _route(t, facts, arm).status == "REFUSED"


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("extra, code", [
    # Policy override (run `shared-ask-grammar-safety`, §6): a digit-count rounding note passes the premise number gate
    # (not `SOURCE_PREMISE_UNREAD`) and is refused by the formatting policy gate (`QUESTION_CONTEXT_UNSUPPORTED`),
    # whereas a length claim hidden inside a note still fails at the premise gate (`SOURCE_PREMISE_UNREAD`).
    ("Làm tròn kết quả đến hàng phần mười.", "QUESTION_CONTEXT_UNSUPPORTED"),
    ("Làm tròn đến 2 chữ số thập phân.", "QUESTION_CONTEXT_UNSUPPORTED"),
    ("Ghi kết quả đến 2 chữ số sau dấu phẩy.", "QUESTION_CONTEXT_UNSUPPORTED"),
    ("Làm tròn kết quả, độ dài là 5.", "SOURCE_PREMISE_UNREAD"),
    ("Làm tròn đến hàng phần mười, đơn vị độ dài là 5 cm.", "SOURCE_PREMISE_UNREAD"),
])
def test_a_note_holds_a_number_only_as_a_digit_count(arm, extra, code):
    r = _with_premise(extra, arm)
    assert r.status == "REFUSED" and r.code == code, (r.status, r.code, r.reason)


@pytest.mark.parametrize("arm", ARMS)
def test_lateral_edge_of_an_oblique_prism_is_not_a_height(arm):
    # the engine would refuse the layout anyway (UNDERDETERMINED_POINT); the premise gate must refuse the claim first
    t, facts = _bench("B04", "Đường cao AA'.", "Tính thể tích")
    t = t.replace("lăng trụ đứng", "lăng trụ")
    facts = [{**f, "quotes": [q.replace("lăng trụ đứng", "lăng trụ") for q in f["quotes"]],
              **({"right": False} if f["id"] == "f1" else {})} for f in facts]
    assert _route(t, facts, arm).code == "SOURCE_PREMISE_UNREAD"


@pytest.mark.parametrize("arm", ARMS)
def test_relabelling_keeps_both_verdicts(arm):
    assert _with_premise("", arm, names="TEFGK").status == "SERVED"
    assert _with_premise("Đổi TE thành 5.", arm, names="TEFGK").status == "REFUSED"
