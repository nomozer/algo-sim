"""Run `hybrid-semantic-extraction-v2`, integrated part: bounded Source Grounding fixes (dev evidence + baseline L02, the
oblique-box safety fix) with adversarial negatives, and the offline extraction-mutation ablation. Prompt v2 itself was
measured and not integrated (`disposition.md`). Real fact route, authored Typed Facts, no model."""
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


# ── provider surface guard (prompt v2 was measured and NOT integrated: `disposition.md`) ─────────────────────────────

def test_product_prompt_has_the_locked_schema_and_no_corpus_example():
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


# ── offline ablation: the measured baseline extraction failure classes never become an unsafe serve ──────────────

def _mutate(name, fs, entities):
    qs = [f for f in fs if f["kind"] == "question"]
    if name == "drop_operands":
        return [f.pop(k, None) for f in qs if f.get("quantity") != "volume" for k in ("points", "points_a", "points_b", "point_kind")]
    if name == "drop_solid":
        return [f.pop("solid", None) for f in fs if (f["kind"] == "length" and f.get("measure") not in (None, "segment"))
                or (f["kind"] == "question" and f.get("quantity") == "volume")]
    if name == "invent_label":
        f = next((f for f in qs for k in ("points", "points_a") if f.get(k)), None)
        if f:
            k = "points" if f.get("points") else "points_a"
            f[k] = ["Z"] + f[k][1:]
        return [f]
    if name == "three_point_right_angle":
        return [f["points"].append(f["at"]) or f for f in fs if f["kind"] == "right_angle" and f.get("at") and f["at"] not in (f.get("points") or [])]
    if name == "approximate_unsupported":
        f = next((f for f in fs if f["kind"] == "unsupported" and f["role"] == "question"), None)
        if f:
            f.pop("reason", None)
            f.update(kind="question", quantity="length", points=list(entities[:2]))
        return [f]
    if name == "drop_later_goal":
        idx = [i for i, f in enumerate(fs) if f["role"] in ("question", "prove")]
        return [fs.pop(idx[-1])] if len(idx) > 1 else [None]


@pytest.mark.parametrize("name", ["drop_operands", "drop_solid", "invent_label", "three_point_right_angle",
                                  "approximate_unsupported", "drop_later_goal"])
def test_baseline_failure_classes_are_refused_never_served_wrong(name):
    from copy import deepcopy
    from scripts import run_nlu_extraction_evaluation as V1
    from scripts import run_semantic_extraction_evaluation as E
    inp, applied = E.load_inputs(), 0
    for c in inp["corpus"]["cases"]:
        fs = deepcopy(V1.gold_payload(inp, c["id"])["facts"])
        if not any(x is not None for x in _mutate(name, fs, c["entities"])):
            continue
        applied += 1
        verdict = E.score_served(c["requests"], E.route_record(run_fact_route(c["source_text"], {"facts": fs})))["classification"]
        assert verdict in {"SAFE_REFUSAL", "FALSE_REFUSAL", "CORRECT_COMPLETE"}, (c["id"], name, verdict)
    assert applied > 0


# ── amendment 1 (dev01 at the GOLD route): a sentence-initial indefinite article before a solid ────────────────────

def test_sentence_initial_article_before_a_solid_is_not_an_unread_premise():
    text = "Một hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    served(text, cuboid(solid_quote="hộp chữ nhật ABCD.A'B'C'D'"), {"q": Fraction(169)})


@pytest.mark.parametrize("extra", [
    " Một cạnh khác dài 5.",                         # "một" opening a non-solid noun is content, not an article
    " Biết AB bằng một nửa AD.",                      # a numeric/fraction "một" inside a premise
    " Một hình chóp khác có thể tích 5.",             # article accepted, but the new premise itself is unread
])
def test_article_rule_never_hides_premise_content(extra):
    text = "Một hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12." + extra + " Tính độ dài AC'."
    r = run_fact_route(text, cuboid(solid_quote="hộp chữ nhật ABCD.A'B'C'D'"))
    assert (r.status, r.code) == ("REFUSED", "SOURCE_PREMISE_UNREAD"), (r.code, r.reason)


# ── whole-change review: a parallelepiped is not a right prism unless the source says so ─────────────────────────

def _box(solid_type, right, solid_quote):
    p = cuboid(solid_quote=solid_quote)
    p["facts"][0].update(solid_type=solid_type, right=right)
    return p


@pytest.mark.parametrize("solid_type,right", [("prism", True), ("cuboid", None)])
def test_bare_parallelepiped_never_becomes_right_by_assumption(solid_type, right):
    # Review repro: a "hình hộp" with a rectangular base is still possibly oblique; AC' = 13 assumes a right box.
    text = "Cho hình hộp ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    p = _box(solid_type, right, "Cho hình hộp ABCD.A'B'C'D'")
    p["facts"].insert(1, {"id": "f0", "kind": "polygon_shape", "role": "premise", "shape": "rectangle",
                          "points": list("ABCD"), "quotes": ["đáy ABCD là hình chữ nhật"]})
    r = run_fact_route(text, p)
    assert (r.status, r.code) == ("REFUSED", "PREDICATE_NOT_IN_QUOTE"), (r.answers, r.code)


@pytest.mark.parametrize("text,quote", [
    ("Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. Tính độ dài AC'.", "Cho hình hộp chữ nhật ABCD.A'B'C'D'"),
    ("Cho hình hộp đứng ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'.", None),
])
def test_rectangular_or_explicitly_right_box_is_still_right(text, quote):
    if quote:
        served(text, _box("cuboid", None, quote), {"q": Fraction(169)})
    else:
        p = _box("prism", True, "Cho hình hộp đứng ABCD.A'B'C'D'")
        p["facts"].insert(1, {"id": "f0", "kind": "polygon_shape", "role": "premise", "shape": "rectangle",
                              "points": list("ABCD"), "quotes": ["đáy ABCD là hình chữ nhật"]})
        served(text, p, {"q": Fraction(169)})


# ── candidate review: the rightness cue must name THIS solid, not merely occur in the quote ──────────────────────────

def _right_box(solid_type, right, solid_quote, text_extra=""):
    p = _box(solid_type, right, solid_quote)
    p["facts"].insert(1, {"id": "f0", "kind": "polygon_shape", "role": "premise", "shape": "rectangle",
                          "points": list("ABCD"), "quotes": ["đáy ABCD là hình chữ nhật"]})
    return p


@pytest.mark.parametrize("extra", [" và các cạnh bên đều nghiêng", " giống đáy của một hộp chữ nhật"])
@pytest.mark.parametrize("solid_type,right", [("prism", True), ("cuboid", None)])
def test_a_rightness_word_elsewhere_in_the_quote_does_not_make_the_box_right(extra, solid_type, right):
    text = f"Cho hình hộp ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật{extra}, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    quote = f"Cho hình hộp ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật{extra}"
    r = run_fact_route(text, _right_box(solid_type, right, quote))
    assert (r.status, r.code) == ("REFUSED", "PREDICATE_NOT_IN_QUOTE"), (r.answers, r.code)


@pytest.mark.parametrize("phrase", ["hình hộp đứng", "lăng trụ đứng", "hình lăng trụ đứng tứ giác", "hình lăng trụ tứ giác đứng",
                                    "lăng trụ tứ giác đều", "hình hộp chữ nhật", "hộp chữ nhật"])
def test_a_rightness_word_naming_the_solid_still_makes_it_right(phrase):
    text = f"Cho {phrase} ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    served(text, _right_box("prism", True, f"Cho {phrase} ABCD.A'B'C'D'"), {"q": Fraction(169)})


@pytest.mark.parametrize("quote,right", [
    ("ABCD.A'B'C'D' là hình lập phương", True),          # label first, as the rectangle check also accepts
    ("ABCD.A'B'C'D' là một lăng trụ đứng", True),
    ("ABCD.A'B'C'D' là hình hộp có các cạnh bên đều bằng 12", False),
])
def test_label_then_cue_order_names_the_solid_too(quote, right):
    text = f"Cho {quote}, đáy ABCD là hình chữ nhật, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    p = _right_box("prism", True, quote)
    if right:
        served(text, p, {"q": Fraction(169)})
    else:
        r = run_fact_route(text, p)
        assert (r.status, r.code) == ("REFUSED", "PREDICATE_NOT_IN_QUOTE"), (r.answers, r.code)


@pytest.mark.parametrize("other", [
    "hình hộp chữ nhật ABCD.EFGH", "ABCD.EFGH là một lăng trụ đứng",
    "hình hộp chữ nhật EFGH.A'B'C'D'", "hình hộp chữ nhật ABCD.B'C'D'A'",
    "ABCD là một lăng trụ đứng",
])
def test_rightness_cannot_be_borrowed_from_a_shared_face_or_wrong_correspondence(other):
    prefix = f"Cho hình hộp ABCD.A'B'C'D' và {other}"
    text = prefix + ", đáy ABCD là hình chữ nhật, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    r = run_fact_route(text, _right_box("prism", True, prefix))
    assert (r.status, r.code) == ("REFUSED", "PREDICATE_NOT_IN_QUOTE"), (r.answers, r.code)


@pytest.mark.parametrize("name", ["BCDA.B'C'D'A'", "ADCB.A'D'C'B'", "A'B'C'D'.ABCD"])
def test_rightness_accepts_the_same_prism_with_cyclic_reflected_or_swapped_faces(name):
    prefix = f"Cho hình hộp chữ nhật {name}"
    text = prefix + ", đáy ABCD là hình chữ nhật, AB = 3, AD = 4, AA' = 12. Tính độ dài AC'."
    served(text, _right_box("prism", True, prefix), {"q": Fraction(169)})
