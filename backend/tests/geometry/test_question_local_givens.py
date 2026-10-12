"""Question context must be covered before geometry is served. Real routes, no provider.

Oracle: square base side 2, SA perpendicular to base, SA=3 ⇒ SC²=17, V²=16.
The break caught is ignoring a local assertion because its ask still names SC/the same solid.
"""
from fractions import Fraction

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from tests.geometry import hybrid_compiler_benchmark as HB


def run(sentence, arm="B", extra=(), quote=None, base=None):
    text, facts = base or HB._square()
    question = HB._ask("q", quote or sentence, "length", points=["S", "C"])
    payload = {"facts": facts + list(extra) + [question]}
    text = " ".join(text) + " " + sentence
    if arm == "B":
        return run_fact_route(text, payload)
    calls = lap_ke_hoach(payload, text).calls
    return run_function_route(text, {"calls": calls})


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("sentence", [
    "Với SA = 5, tính SC.",
    "Tính SC với SA = 5.",
    "Tính SC biết SC = 5.",
    "Tính SC, biết SA = 3 và SB = 5.",
    "Cho SA = 5, tính SC.",
    "Tính SC. Với SA = 5, tính SC.",
    "SA = 5, tính SC.",
    "Tính SC, biết SB vuông góc với (ABCD).",
    "Tính SC, biết SA song song với (ABCD).",
    "Tính SC, biết SA = 3 và thay SA thành 5.",
    "Tính SC. Biết SA = 5.",
])
def test_unrepresented_local_givens_never_serve_old_geometry(sentence, arm):
    result = run(sentence, arm)
    assert result.status == "REFUSED", (sentence, result.answers)
    assert not result.answers and not result.scene3d


@pytest.mark.parametrize("quote", ["Tính SC", "SC", "Tính SC biết SA = 5."])
def test_quote_extent_does_not_hide_local_givens(quote):
    result = run("Tính SC biết SA = 5.", quote=quote)
    assert result.status == "REFUSED", result.answers


@pytest.mark.parametrize("sentence", [
    "Tính SC, biết SA = 3.",
    "Với SA = 3, tính SC.",
    "Cho SA = 3, tính SC.",
    "Tính SC, biết AS bằng 3.",
    "Tính SC, biết SA = 6/2.",
    "Tính SC, biết SA có độ dài 3.",
    "Độ dài SC bằng bao nhiêu, biết SA = 3?",
])
@pytest.mark.parametrize("arm", ["A", "B"])
def test_redundant_verified_local_length_keeps_correct_answer(sentence, arm):
    result = run(sentence, arm)
    assert result.status == "SERVED", (result.code, result.reason)
    assert HB.answer_square(result.answers["q"]) == Fraction(17)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_new_consistent_local_given_is_served_when_typed_and_verified(arm):
    sentence = "Tính SC, biết SB = √13."
    extra = HB._f("local", "length", "SB = √13", points=["S", "B"], measure="segment", value="√13")
    result = run(sentence, arm, [extra])
    assert result.status == "SERVED", (result.code, result.reason)
    assert HB.answer_square(result.answers["q"]) == Fraction(17)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_typed_conflict_is_not_an_authorized_overwrite(arm):
    sentence = "Tính SC, biết SA = 5."
    extra = HB._f("local", "length", "SA = 5", points=["S", "A"], measure="segment", value="5")
    result = run(sentence, arm, [extra])
    assert result.status == "REFUSED"
    assert result.code == "INCONSISTENT_FACTS"
    assert not result.answers and not result.scene3d


@pytest.mark.parametrize("arm", ["A", "B"])
def test_dimension_supplied_in_question_can_complete_existing_model(arm):
    text, facts = HB._square()
    sentence = "Tính SC, biết SA = 3."
    local = HB._f("local", "length", "SA = 3", points=["S", "A"], measure="segment", value="3")
    result = run(sentence, arm, [local], base=(text[:3], facts[:3]))
    assert result.status == "SERVED", (result.code, result.reason)
    assert HB.answer_square(result.answers["q"]) == Fraction(17)


@pytest.mark.parametrize("sentence", [
    "Nếu SA = 5 thì tính SC.",
    "Giả sử SA = 5, tính SC.",
    "Tính SC với điều kiện SA = 5.",
])
def test_scoped_changes_are_refused_without_replacement_geometry(sentence):
    result = run(sentence)
    assert result.status == "REFUSED"
    assert not result.answers and not result.scene3d


@pytest.mark.parametrize("arm", ["A", "B"])
def test_local_fact_cannot_replace_original_omitted_by_model(arm):
    text, facts = HB._square()
    sentence = "Tính SC, biết SA = 5."
    local = HB._f("local", "length", "SA = 5", points=["S", "A"], measure="segment", value="5")
    result = run(sentence, arm, [local], base=(text, facts[:3]))
    assert result.status == "REFUSED", result.answers
    assert not result.answers and not result.scene3d


@pytest.mark.parametrize("arm", ["A", "B"])
def test_local_length_cannot_change_explicit_source_units(arm):
    text, facts = HB._square()
    text[-1] = "SA = 3 m."
    facts[-1]["quotes"] = [text[-1]]
    result = run("Tính SC, biết SA = 3 cm.", arm, base=(text, facts))
    assert result.status == "REFUSED", result.answers


def test_repeated_explicit_source_unit_is_supported():
    text, facts = HB._square()
    text[-1] = "SA = 3 cm."
    facts[-1]["quotes"] = [text[-1]]
    result = run("Tính SC, biết SA = 3 cm.", base=(text, facts))
    assert result.status == "SERVED", (result.code, result.reason)


def test_new_typed_given_at_end_of_question_is_still_a_premise():
    sentence = "Tính SC, biết SB = √13?"
    extra = HB._f("local", "length", "SB = √13", points=["S", "B"], measure="segment", value="√13")
    result = run(sentence, extra=[extra])
    assert result.status == "SERVED", (result.code, result.reason)
    assert HB.answer_square(result.answers["q"]) == Fraction(17)


@pytest.mark.parametrize("names,scale", [("SABCD", 1), ("UVWXZ", 2), ("PQRST", 3)])
@pytest.mark.parametrize("local_multiplier,want", [(3, "SERVED"), (5, "REFUSED")])
def test_renaming_and_uniform_scale_preserve_context_decision(names, scale, local_multiplier, want):
    text, facts = HB._square(names)
    text[1] = text[1].replace("cạnh 2", f"cạnh {2 * scale}")
    facts[1]["quotes"], facts[1]["value"] = [text[1]], str(2 * scale)
    text[3] = text[3].replace("= 3", f"= {3 * scale}")
    facts[3]["quotes"], facts[3]["value"] = [text[3]], str(3 * scale)
    s, a, _b, c, _d = names
    sentence = f"Tính {s}{c}, biết {s}{a} = {local_multiplier * scale}."
    result = run_fact_route(" ".join(text) + " " + sentence,
                            {"facts": facts + [HB._ask("q", sentence, "length", points=[s, c])]})
    assert result.status == want, (result.code, result.answers)
    if want == "SERVED":
        assert HB.answer_square(result.answers["q"]) == Fraction(17 * scale * scale)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_construction_only_request_cannot_render_old_model(arm):
    text, facts = HB._square()
    mid = HB._mid("mid", "M", "S", "C")
    sentence = "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MAB), biết SA = 5."
    section = HB._f("section", "section", sentence, solid="S.ABCD", points=list("MAB"))
    source = " ".join(text + mid["quotes"] + [sentence])
    payload = {"facts": facts + [mid, section]}
    if arm == "B":
        result = run_fact_route(source, payload)
    else:
        result = run_function_route(source, {"calls": lap_ke_hoach(payload, source).calls})
    assert result.status == "REFUSED", result.scene3d
    assert not result.answers and not result.scene3d
