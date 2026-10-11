"""Hybrid B compiler capability benchmark — pre-registered before any compiler change (run `hybrid-compiler-capability-audit`).

Two evaluations, kept apart:
  facts    — the compiler receives VERIFIED Typed Facts (no model): does it choose and compose the right functions?
  pipeline — the Vietnamese text goes through the fact-extraction adapter with a FAKE provider returning those facts:
             schema, quotes and source grounding included. It says nothing about what a real model would extract.

Cases where mathematics determines an answer that the system does not serve today are strict xfail with the gap they
need; they turn into failures the moment the gap closes, so the record has to be updated.
"""
from __future__ import annotations

import ast
import re
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.geometry import hybrid_compiler_benchmark as HB

CASES = HB.cases()
ARMS = ("facts", "pipeline")


def test_benchmark_shape():
    assert len(CASES) == 30
    assert len({c["id"] for c in CASES}) == 30
    tiers = {c["tier"] for c in CASES}
    assert {"simple", "two_primitives", "chain", "derived_input", "reordered", "renamed", "missing_data", "contradictory",
            "multi_config", "unsupported_goal", "composition"} <= tiers


def test_oracle_imports_nothing_from_the_product():
    """Independence: the oracle module may import the product only inside `run`, never at module level."""
    tree = ast.parse(Path(HB.__file__).read_text(encoding="utf-8"))
    top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert all((getattr(n, "module", "") or "") in ("__future__", "fractions") for n in top), [ast.dump(n) for n in top]


def test_oracle_matches_hand_derived_values():
    hand = {"B01": 16, "B02": "23/9", "B03": "4/3", "B04": 27, "B05": 11, "B06": "9/4", "B07": "36/13", "B08": "36/13",
            "B09": "11/4", "B10": "17/9", "B11": "18/11", "B12": "11/4", "B26": 11, "B27": 1, "B28": "9/13",
            "B29": "8/17", "B30": 7}
    o = HB.oracle()
    assert {k: o[k]["q"] for k in hand} == {k: F(v) for k, v in hand.items()}


def test_every_refusal_code_of_the_route_is_classified():
    """A code missing from REFUSAL_CLASS would be scored as an unknown refusal — keep the taxonomy complete."""
    root = Path(__file__).resolve().parents[2] / "app"
    src = "".join(p.read_text(encoding="utf-8") for p in [*(root / "simulation" / "geometry_functions").glob("*.py"),
                                                           root / "ai" / "function_route.py", root / "ai" / "fact_extraction.py"])
    codes = set(re.findall(r'TuChoi\("([A-Z_]+)"', src)) | set(re.findall(r'KetQuaTuyen\("REFUSED", "([A-Z_]+)"', src))
    assert codes and codes <= set(HB.REFUSAL_CLASS), sorted(codes - set(HB.REFUSAL_CLASS))


def test_answer_parsing():
    assert HB.answer_square("6√13/13") == F(36, 13)
    assert HB.answer_square("cos²=8/17") == F(8, 17)
    assert HB.answer_square("4") == 16
    assert HB.answer_square("√23/3") == F(23, 9)


@pytest.mark.parametrize("result,expected", [
    (SimpleNamespace(status="SERVED", answers={"q": "√11"}, code=None), "correct_served"),
    (SimpleNamespace(status="SERVED", answers={"q": "√12"}, code=None), "wrong_served"),          # mutant: wrong value
    (SimpleNamespace(status="REFUSED", answers={}, code="UNDERDETERMINED_POINT"), "false_refusal"),
])
def test_classifier_kills_wrong_answers(result, expected):
    case = next(c for c in CASES if c["id"] == "B05")             # SO = √11
    assert HB.classify(case, result)["outcome"] == expected


def _param(c, arm):
    marks = [pytest.mark.xfail(strict=True, reason=f"GAP {c['id']}: {c['gap']}")] if c.get("gap") else []
    return pytest.param(c, arm, id=f"{c['id']}-{arm}", marks=marks)


@pytest.mark.parametrize("case,arm", [_param(c, a) for c in CASES for a in ARMS])
def test_case_outcome(case, arm):
    k = HB.classify(case, HB.run(case, arm))
    assert k["outcome"] in ("correct_served", "correct_refusal"), k


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_both_evaluations_agree_on_correct_facts(case):
    """With faithful facts the pipeline adds only parsing and grounding; it must not change the verdict."""
    a, b = (HB.classify(case, HB.run(case, arm)) for arm in ARMS)
    assert (a["outcome"], a.get("code")) == (b["outcome"], b.get("code"))
