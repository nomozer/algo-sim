"""A follow-up task in the request ("rồi", "sau đó", "từ đó", "tiếp theo", "bằng cách") must not hide a changed hypothesis.

Real routes A and B, no provider. Oracle: square base side 2, SA ⊥ base, SA = 3 ⇒ SC² = 17.
The break caught: the ask grammar accepts a next-task connector after the asked phrase, so the text behind it was never
covered and the old figure was served for "Tính SC, sau đó thay SA bằng 5 và tính lại SC.".
"""
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
]


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", CHANGED)
def test_follow_up_hypothesis_change_never_serves_the_old_figure(arm, sentence):
    r = run(sentence, arm)
    assert r.status == "REFUSED", (r.status, r.code, r.answers)
    assert not r.answers and not r.scene3d


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("sentence", CHANGED[:4] + CHANGED[11:13])
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
    "Tính SC, sau đó thay số và kiểm tra lại.",
    "Tính SC, tiếp theo tính SB.",
    "Tính SC. Sau đó tính SB.",
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


@pytest.mark.parametrize("name, sentence", [
    ("_VIEC_KE_TIEP_RE", "Tính SC, sau đó thay SA bằng 5 và tính lại SC."),
    ("_SO_TU_DO", "Tính SC rồi đổi SA thành 5 và tính lại SC."),
    ("_VI_TU_TIEN_DE", "Tính SC, rồi đổi đáy ABCD thành hình chữ nhật và tính lại SC."),
])
def test_each_follow_up_rule_carries_its_own_refusal(monkeypatch, name, sentence):
    import re
    from app.simulation.geometry_functions import registry as R
    monkeypatch.setattr(R, name, re.compile(r"(?!x)x"))
    assert run(sentence, "B").status == "SERVED"     # the fault re-opens the old false serve


@pytest.mark.parametrize("arm", ARMS)
def test_follow_up_restating_the_same_given_stays_served(arm):
    r = run("Tính SC, sau đó, với SA = 3, tính lại SC.", arm)
    assert r.status == "SERVED", (r.status, r.code, r.reason)
