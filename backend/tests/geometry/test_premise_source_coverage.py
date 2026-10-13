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
]


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


@pytest.mark.parametrize("arm", ARMS)
def test_relabelling_keeps_both_verdicts(arm):
    assert _with_premise("", arm, names="TEFGK").status == "SERVED"
    assert _with_premise("Đổi TE thành 5.", arm, names="TEFGK").status == "REFUSED"
