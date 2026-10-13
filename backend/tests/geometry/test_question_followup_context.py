"""A follow-up task in the request ("rồi", "sau đó", "từ đó", "tiếp theo", "bằng cách") must not hide a changed hypothesis.

Real routes A and B, no provider. Oracle: square base side 2, SA ⊥ base, SA = 3 ⇒ SC² = 17.
The break caught: the ask grammar accepts a next-task connector after the asked phrase, so the text behind it was never
covered and the old figure was served for "Tính SC, sau đó thay SA bằng 5 và tính lại SC.". The rule is closed: a follow-up
is read like a given fragment, a length after the first request must match a validated call, and asking the same object
again is refused. Open follow-up wording outside the closed vocabulary is refused too (bounded, documented false refusals).
"""
import re

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from tests.geometry import hybrid_compiler_benchmark as HB
from tests.geometry.test_question_local_givens import run

ARMS = ["A", "B"]

CHANGED = [
    "Tính SC, sau đó thay SA bằng 5 và tính lại SC.",
    "Tính SC rồi đổi SA thành 5 và tính lại SC.",
    "Tính SC, sau đó tăng SA lên 5 và tính lại SC.",
    "Tính SC, sau đó SA = 5, tính lại SC.",
    "Tính SC, rồi SA = 5.",
    "Tính SC, từ đó thay SA bằng 4.",
    "Tính SC, tiếp theo cho SA = 5 và tính lại SC.",
    "Tính SC, tiếp theo đổi SA thành 5 rồi tính lại SC.",
    "Tính SC, rồi đổi đáy ABCD thành hình chữ nhật và tính lại SC.",
    "Tính SC, sau đó cho đáy là tam giác đều và tính lại SC.",
    "Tính SC bằng cách thay SA bằng 5.",
    "Tính SC. Sau đó thay SA bằng 5 và tính lại SC.",
    "Tính SC. Đổi SA thành 5 rồi tính lại SC.",
    "Tính SC. Tiếp theo, tăng SA lên 6 và tính lại SC.",
    # independent review of 87118b61 — a change after "tính lại …", or written without digits
    "Tính SC, sau đó tính lại SC với SA = 5.",
    "Tính SC rồi tính lại SC với SA = 5.",
    "Tính SC. Tính lại SC với SA = 5.",
    "Tính SC, sau đó tính lại SC lúc SA = 5.",
    "Tính SC rồi tính lại SC, lúc này SA = 5.",
    "Tính SC, rồi tính SC lần nữa với SA = 5.",
    "Tính SC, sau đó tính độ dài SC mới với SA = 5.",
    "Tính SC, sau đó tăng SA gấp đôi và tính lại SC.",
    "Tính SC, sau đó thay SA bằng năm và tính lại SC.",
    "Tính SC, sau đó nhân đôi SA và tính lại SC.",
    "Tính SC, sau đó thay SA bằng SB và tính lại SC.",
    "Tính SC, sau đó bỏ giả thiết SA vuông góc với (ABCD) và tính lại SC.",
    "Tính SC. Bây giờ tăng gấp đôi chiều cao và tính lại SC.",
]


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", CHANGED)
def test_follow_up_hypothesis_change_never_serves_the_old_figure(arm, sentence):
    r = run(sentence, arm)
    assert r.status == "REFUSED", (r.status, r.code, r.answers)
    assert not r.answers and not r.scene3d


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", CHANGED[:4] + CHANGED[11:13] + CHANGED[14:17])
def test_short_ask_quote_does_not_hide_the_follow_up(arm, sentence):
    r = run(sentence, arm, quote="Tính SC")
    assert r.status == "REFUSED", (r.status, r.code, r.answers)


def _section(sentence: str, arm: str):
    text, facts = HB._square()
    mid = HB._mid("mid", "M", "S", "C")
    section = HB._f("section", "section", sentence, solid="S.ABCD", points=list("MAB"))
    source = " ".join(text + mid["quotes"] + [sentence])
    payload = {"facts": facts + [mid, section]}
    return (run_fact_route(source, payload) if arm == "B" else
            run_function_route(source, {"calls": lap_ke_hoach(payload, source).calls}))


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", [
    "Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB), sau đó SA = 5.",
    "Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB), rồi đổi SA thành 5 và vẽ lại thiết diện.",
    "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MAB), sau đó cho đáy là hình chữ nhật và dựng lại.",
    "Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB), sau đó di chuyển M đến D và vẽ lại thiết diện.",
    "Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB), sau đó tăng SA gấp đôi và vẽ lại thiết diện.",
])
def test_construction_follow_up_change_is_refused(arm, sentence):
    r = _section(sentence, arm)
    assert r.status == "REFUSED", (r.status, r.code, bool(r.scene3d))


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", [
    "Tính SC rồi so sánh với SB.",
    "Tính SC, sau đó chứng minh SC vuông góc với BD.",
    "Tính SC, từ đó suy ra SC lớn hơn SA.",
    "Tính SC rồi làm tròn kết quả.",
    "Tính SC, sau đó tính SB.",
    "Tính SC, rồi tính SB, biết SA = 3.",
    "Tính SC, tiếp theo tính SB.",
    "Tính SC. Sau đó tính SB.",
    "Tính SC, sau đó, với SA = 3, tính SB.",
])
def test_multi_step_requests_without_a_change_stay_served(arm, sentence):
    r = run(sentence, arm)
    assert r.status == "SERVED", (r.status, r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", [
    "Vẽ thiết diện của hình chóp S.ABCD cắt bởi (MAB), sau đó tô màu thiết diện.",
    "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MAB), rồi quan sát thiết diện từ nhiều góc nhìn.",
])
def test_construction_follow_up_task_stays_served(arm, sentence):
    r = _section(sentence, arm)
    assert r.status == "SERVED", (r.status, r.code, r.reason)


ANGLE = HB._ask("q2", "Tính góc giữa SC và (ABCD).", "angle", points_a=["S", "C"], points_b=list("ABCD"))


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence, extra", [
    # independent review of 926c0bf9, I3: the asked object named inside another object is not a re-request
    ("Tính SC. Tính góc giữa SC và (ABCD).", [ANGLE]),
    ("a) Tính SC. b) Tính góc giữa SC và (ABCD).", [ANGLE]),
    ("Tính SC rồi so sánh SC với SB.", []),
])
def test_multi_part_requests_naming_the_object_again_stay_served(arm, sentence, extra):
    r = run(sentence, arm, extra=extra, quote="Tính SC")
    assert r.status == "SERVED", (r.status, r.code, r.reason)
    assert HB.answer_square(r.answers["q"]) == 17


@pytest.mark.parametrize("sentence", ["Tính SC. Tính khoảng cách từ A đến SC.",
                                      "Tính SC, sau đó tính khoảng cách từ A đến SC."])
def test_distance_to_the_asked_segment_is_not_a_re_request(sentence):
    q2 = HB._ask("q2", sentence.split(". ")[-1] if ". " in sentence else sentence, "distance", points_a=["A"],
                 points_b=["S", "C"])
    r = run(sentence, "B", extra=[q2], quote="Tính SC")
    assert r.status == "SERVED", (r.status, r.code, r.reason)


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", [
    # review minor 4: a goal clause does not cover a change written after ";"
    "Tính SC, sau đó chứng minh SC lớn hơn SA; đổi đáy thành hình chữ nhật.",
    "Tính SC, từ đó suy ra SC lớn hơn SA; tăng SA gấp đôi.",
])
def test_goal_clause_does_not_cover_a_later_change(arm, sentence):
    assert run(sentence, arm).status == "REFUSED"


@pytest.mark.parametrize("sentence", [
    "Tính SC, sau đó gọi M là trung điểm SC.",
    "Tính SC, sau đó so sánh SC với 4.",
    "Tính SC, sau đó kết luận tam giác SAC vuông tại A.",
])
def test_open_follow_up_wording_is_a_documented_conservative_refusal(sentence):
    # Bounded fail-closed limit: the follow-up vocabulary is closed; these are unread, so refused (served at 132e9b23).
    assert run(sentence, "B").status == "REFUSED"


@pytest.mark.parametrize("name, sentence", [
    ("_SAU_VIEC_KE_TIEP", "Tính SC, sau đó tăng SA gấp đôi và tính lại SC."),
    ("_VIEC_KE_TIEP_RE", "Tính SC, sau đó thay SA bằng SB."),
])
def test_each_follow_up_rule_carries_its_own_refusal(monkeypatch, name, sentence):
    from app.simulation.geometry_functions import registry as R
    mutant = re.compile(r"[\s\S]*") if name == "_SAU_VIEC_KE_TIEP" else re.compile(r"(?!x)x")
    monkeypatch.setattr(R, name, mutant)
    if name == "_SAU_VIEC_KE_TIEP":                    # re-request still refuses "tính lại SC"; drop it to isolate the rule
        sentence = sentence.replace(" và tính lại SC", "")
    assert run(sentence, "B").status == "SERVED"      # the fault re-opens the old false serve
