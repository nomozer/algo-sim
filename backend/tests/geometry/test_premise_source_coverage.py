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
@pytest.mark.parametrize("extra", ["Làm tròn kết quả đến hàng phần mười.", "Đơn vị độ dài là cm.", "Bài tập 3."])
def test_closed_notes_stay_served(arm, extra):
    r = _with_premise(extra, arm)
    assert r.status == "SERVED", (r.code, r.reason)


@pytest.mark.parametrize("arm", ARMS)
def test_relabelling_keeps_both_verdicts(arm):
    assert _with_premise("", arm, names="TEFGK").status == "SERVED"
    assert _with_premise("Đổi TE thành 5.", arm, names="TEFGK").status == "REFUSED"
