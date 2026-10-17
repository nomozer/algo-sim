"""Run `hybrid-semantic-extraction-v2`: two bounded Source Grounding vocabulary gaps (dev evidence + baseline L02) and the
extraction contract rules of prompt v2. Real fact route, authored Typed Facts, no model."""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.ai.function_route import run_fact_route

CUBOID = "Cho hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Đường chéo AC' dài bao nhiêu?"


def squared(v):
    from app.simulation.geometry.radical import Radical
    return Fraction(v.he) ** 2 * v.can if isinstance(v, Radical) else Fraction(v) ** 2


def L(i, a, b, v, q):
    return {"id": i, "kind": "length", "role": "premise", "measure": "segment", "points": [a, b], "value": v, "quotes": [q]}


def cuboid(solid_quote="Cho hộp chữ nhật ABCD.A'B'C'D'", ask=("A", "C'"), ask_quote="Tính độ dài AC'."):
    return {"facts": [
        {"id": "f1", "kind": "solid", "role": "premise", "solid": "ABCD.A'B'C'D'", "solid_type": "cuboid", "quotes": [solid_quote]},
        L("f2", "A", "B", "3", "AB = 3"), L("f3", "A", "D", "4", "AD = 4"), L("f4", "A", "A'", "12", "AA' = 12"),
        {"id": "q", "kind": "question", "role": "question", "quantity": "length", "points": list(ask), "quotes": [ask_quote]}]}


def cube(ask=("A", "C'"), ask_quote="Đường chéo AC' dài bao nhiêu?"):
    return {"facts": [
        {"id": "f1", "kind": "solid", "role": "premise", "solid": "ABCD.A'B'C'D'", "solid_type": "cube", "quotes": ["Cho hình lập phương ABCD.A'B'C'D'"]},
        {"id": "f2", "kind": "length", "role": "premise", "measure": "edge", "solid": "ABCD.A'B'C'D'", "value": "2", "quotes": ["có cạnh bằng 2"]},
        {"id": "q", "kind": "question", "role": "question", "quantity": "length", "points": list(ask), "quotes": [ask_quote]}]}


def served(text, payload, want):
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert {q: squared(r.exec_result.final_memory[f"kq_{q}"]) for q in r.answers} == want
    return r


def test_rectangular_box_without_the_word_hinh_names_a_cuboid():
    served(CUBOID, cuboid(), {"q": Fraction(169)})


@pytest.mark.parametrize("text,quote", [
    ("Cho đáy chữ nhật ABCD của khối ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài AC'.", "đáy chữ nhật ABCD của khối ABCD.A'B'C'D'"),
    ("Cho hộp ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài AC'.", "Cho hộp ABCD.A'B'C'D'"),
])
def test_a_rectangle_or_a_bare_box_is_not_a_cuboid(text, quote):
    r = run_fact_route(text, cuboid(solid_quote=quote))
    assert (r.status, r.code) == ("REFUSED", "PREDICATE_NOT_IN_QUOTE"), (r.code, r.reason)


def test_dai_bao_nhieu_asks_a_length():
    served(CUBE, cube(), {"q": Fraction(12)})


@pytest.mark.parametrize("text,ask,quote", [
    ("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Đường chéo AC' dài 3.", ("A", "C'"), "Đường chéo AC' dài 3."),
    ("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Đường chéo AC' dài bao nhiêu?", ("B", "D'"), "Đường chéo AC' dài bao nhiêu?"),
    ("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2. Đường chéo AC' dài hơn cạnh bao nhiêu?", ("A", "C'"), "Đường chéo AC' dài hơn cạnh bao nhiêu?"),
])
def test_dai_without_a_question_or_for_another_object_or_a_comparison_is_refused(text, ask, quote):
    r = run_fact_route(text, cube(ask=ask, ask_quote=quote))
    assert r.status == "REFUSED", (r.answers, r.code)


# ── prompt v2 contract: one rule per measured baseline failure class (no new schema field) ───────────────────────

@pytest.mark.parametrize("failure,needle", [
    ("multi-goal omission", "không bỏ yêu cầu sau"),
    ("request without operands", "Câu hỏi mang ĐỦ toán hạng"),
    ("measure without its solid", "`solid` = ký hiệu khối mà nó thuộc về"),
    ("three-point right angle", "points = HAI điểm trên hai cạnh góc"),
    ("unnamed point given a name", "không point, không points_a"),
    ("invented label / property", "Chỉ dùng nhãn có trong đề"),
    ("approximated unsupported request", "KHÔNG thay bằng đại lượng gần giống"),
    ("plane operand truncated to three labels", "MỌI nhãn của mặt"),
])
def test_prompt_v2_states_a_rule_for_each_baseline_failure(failure, needle):
    from app.ai.fact_extraction import SYSTEM_PROMPT
    assert needle in SYSTEM_PROMPT, failure


def test_prompt_v2_adds_no_schema_and_no_corpus_example():
    import json
    from pathlib import Path
    from app.ai import fact_extraction as fx
    run = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-semantic-extraction-v2/inputs"
    assert fx.facts_response_schema() == json.loads((run / "baseline_schema.json").read_text(encoding="utf-8"))
    corpus = json.loads((run / "corpus.json").read_text(encoding="utf-8"))["cases"]
    labels = {c["id"]: c["source_text"] for c in corpus}
    for cid, text in labels.items():   # no corpus sentence copied into the prompt (overlap guard)
        for sentence in filter(None, (s.strip() for s in text.split("."))):
            assert len(sentence) < 25 or sentence not in fx.SYSTEM_PROMPT, cid
