# -*- coding: utf-8 -*-
"""Routing integrity of the deterministic parser (run `model1-integration-readiness`, AXO /17 §9–§10).

Two parser defects sent problems the deterministic path can read exactly to the local SLM (4–27 s instead of ~0.1 s):

1. A length *assignment* sentence ("Độ dài KL = 7.") was classified as a length *goal* (the `độ dài XY` goal rule needed
   no question verb and did not exclude `= value`), so the Source Gate refused the parse with `NOT_ASKED_IN_SOURCE`.
2. The pairwise-perpendicular synonym "XY, XZ, XT vuông góc (với nhau) từng đôi (một)" was not read, although the SLM
   prompt canonicalizer and the v3 normalizer already treat it as "đôi một vuông góc". `/16` kept it out of the parser on
   purpose to preserve the SLM-required denominator (`LANGUAGE_GAP_RECOVERY.json` → `denominator_preservation_policy`).

Production routing optimises correctness, safety and latency — never an SLM-contribution metric. Labels below are
arbitrary; every assertion is about the construction, not a case.
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input_local_slm
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally


@pytest.fixture(autouse=True)
def _zero_live_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")


class _ForbiddenRuntime:
    """A runtime that fails the test if the router reaches the SLM."""

    def chat_completion_json(self, **_kw):  # pragma: no cover - reaching it is the failure
        raise AssertionError("deterministic input reached the local SLM")


class _UnavailableRuntime:
    """A runtime that is down: whatever reaches the SLM fails closed as infrastructure, never as a served scene."""

    def chat_completion_json(self, **_kw):
        from app.ai.local_slm_runtime import LocalSlmRuntimeError

        raise LocalSlmRuntimeError("MODEL_RUNTIME_UNAVAILABLE", "test: runtime down")


def _route(text: str, runtime=None):
    return route_text_input_local_slm(text, model_key="v9", closure_mode="v9", normalizer_version="v3",
                                      runtime=runtime or _ForbiddenRuntime(), use_cache=False, allow_download=False)


def _goals(p):
    return [g.get("goal_type") for g in (p.payload or {}).get("math_goals") or []]


def _premise_kinds(p):
    return [x.get("kind") for x in (p.payload or {}).get("premises") or []]


# ── 1. "Độ dài XY = v" is a premise ────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "Cho tứ diện NPRV. Các cạnh NP, NR, NV đôi một vuông góc. Độ dài NP = 5, NR = 8, NV = 12. Tính thể tích khối tứ diện NPRV.",
        "Cho hình chóp E.KLMN với đáy KLMN là hình vuông. Độ dài KL = 7. Cạnh bên EK vuông góc với (KLMN) và EK = 9. "
        "Tính thể tích khối chóp E.KLMN.",
        "Cho hình hộp chữ nhật ABCD.A'B'C'D'. Độ dài AB = 3, AD = 4, AA' = 5. Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.",
    ],
)
def test_length_assignment_sentence_is_a_premise_not_a_goal(text: str) -> None:
    p = parse_geometry_problem_locally(text, use_cache=False)
    assert p.status == LOCAL_PARSE_COMPLETE, (p.status, p.reason_code)
    assert _goals(p) == ["volume"]
    assert "segment_length" in _premise_kinds(p)


@pytest.mark.parametrize(
    "text, goal",
    [
        ("Cho tứ diện RSTX có RS, RT, RX đôi một vuông góc, RS = 8, RT = 15, RX = 6. Tính độ dài ST.", "distance"),
        ("Cho tứ diện RSTX có RS, RT, RX đôi một vuông góc, RS = 8, RT = 15, RX = 6. Độ dài ST bằng bao nhiêu?", "distance"),
    ],
)
def test_a_length_question_is_still_a_goal(text: str, goal: str) -> None:
    p = parse_geometry_problem_locally(text, use_cache=False)
    assert p.status == LOCAL_PARSE_COMPLETE, (p.status, p.reason_code)
    assert _goals(p) == [goal]


# ── 2. "vuông góc (với nhau) từng đôi (một)" reads the same three pairs as "đôi một vuông góc" ────────────────────────

@pytest.mark.parametrize(
    "phrase",
    ["vuông góc với nhau từng đôi một", "vuông góc từng đôi một", "vuông góc với nhau từng đôi", "vuông góc từng đôi"],
)
def test_pairwise_perpendicular_synonym_reads_three_pairs(phrase: str) -> None:
    p = parse_geometry_problem_locally(f"Cho tứ diện DEGK có DE, DG, DK {phrase} và DE = 5, DG = 6, DK = 11. Vẽ hình.",
                                       use_cache=False)
    assert p.status == LOCAL_PARSE_COMPLETE, (p.status, p.reason_code)
    pairs = {frozenset((tuple(x["args"]["line1"]), tuple(x["args"]["line2"])))
             for x in p.payload["premises"] if x["kind"] == "perpendicular_lines"}
    assert pairs == {frozenset({("D", "E"), ("D", "G")}), frozenset({("D", "E"), ("D", "K")}),
                     frozenset({("D", "G"), ("D", "K")})}


# ── 3. Route level: served deterministically, exact answer, the SLM is never reached ─────────────────────────────────

@pytest.mark.parametrize(
    "text, answer",
    [
        ("Cho tứ diện NPRV. Các cạnh NP, NR, NV đôi một vuông góc. Độ dài NP = 5, NR = 8, NV = 12. "
         "Tính thể tích khối tứ diện NPRV.", "80"),
        ("Cho tứ diện DEGK có DE, DG, DK vuông góc với nhau từng đôi một và DE = 5, DG = 6, DK = 12. "
         "Tính thể tích khối tứ diện DEGK.", "60"),
    ],
)
def test_router_serves_these_deterministically_without_the_slm(text: str, answer: str) -> None:
    out = _route(text)
    rd = out.response["route_d"]
    assert out.status == "SERVED", rd.get("refusal")
    assert rd["extraction_mode"] == "LOCAL_DETERMINISTIC_PARSER"
    assert list(rd["answers"].values()) == [answer]


def test_cache_158_policy_isolates_cache_157_rows() -> None:
    """Envelopes cached by candidate 157 came from the SLM route for these texts; 158 must not serve them."""
    from tests.cache_policy import assert_cache_policy_at_least, assert_route_d_row_misses

    assert_cache_policy_at_least(158)
    assert_route_d_row_misses("157:route-d")


# ── 4. Safety: negation, condition and mismatched lists still fail closed ────────────────────────────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "Cho tứ diện DEGK có DE, DG, DK không vuông góc với nhau từng đôi một và DE = 5, DG = 6, DK = 11. Vẽ hình.",
        "Cho tứ diện DEGK. Nếu DE, DG, DK vuông góc với nhau từng đôi một thì DE = 5, DG = 6, DK = 11. Vẽ hình.",
        "Cho tứ diện NPRV. Các cạnh NP, NR, NV đôi một vuông góc. Nếu độ dài NP = 5 thì NR = 8. Tính thể tích khối tứ diện NPRV.",
        "Cho tứ diện NPRV. Các cạnh NP, NR, NV không đôi một vuông góc. Độ dài NP = 5, NR = 8, NV = 12. "
        "Tính thể tích khối tứ diện NPRV.",
    ],
)
def test_negated_or_conditional_wording_is_never_served(text: str) -> None:
    p = parse_geometry_problem_locally(text, use_cache=False)
    out = _route(text, runtime=_UnavailableRuntime())
    assert out.status != "SERVED", (p.status, p.reason_code)
