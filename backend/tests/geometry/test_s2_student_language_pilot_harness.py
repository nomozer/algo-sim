# -*- coding: utf-8 -*-
"""Continuation 11 (§5.2) — Offline S-2 Student Language Pilot Scorer & Protocol Tests."""
from __future__ import annotations

import pytest

from scripts.score_s2_student_language_pilot import score_s2_pilot_records


def test_s2_empty_records_reports_not_measured_never_zero():
    rep = score_s2_pilot_records([])
    assert rep["live_provider_calls"] == 0
    assert rep["measurement_status"] == "NOT_MEASURED"
    for metric_val in rep["metrics"].values():
        assert metric_val["rate"] == "NOT_MEASURED"
        assert metric_val["numerator"] == "UNKNOWN"


def test_s2_scores_all_eight_metrics_and_handles_not_recoverable_honestly():
    records = [
        # 1. Clean SERVED case
        {
            "case_id": "SL-P01",
            "expected": {
                "outcome": "SERVED",
                "is_ambiguous": False,
                "expected_facts_signature": "pyr_S.ABCD_sq2_sa2",
                "expected_goals": ["volume:S.ABCD"],
                "expected_operands": ["S.ABCD", "2", "2"],
                "expected_answers": {"q1": "8/3"},
            },
            "observed": {
                "status": "SERVED",
                "facts_signature": "pyr_S.ABCD_sq2_sa2",
                "extracted_goals": ["volume:S.ABCD"],
                "operands": ["S.ABCD", "2", "2"],
                "quotes_verbatim_in_raw": True,
                "answers": {"q1": "8/3"},
                "certificate_verified": True,
            },
        },
        # 2. Ambiguous student prompt -> valid CLARIFY
        {
            "case_id": "SL-P02",
            "expected": {
                "outcome": "CLARIFY",
                "is_ambiguous": True,
                "allowed_clarification_codes": ["INCOMPLETE_GOAL_OPERAND", "AMBIGUOUS_FACT"],
            },
            "observed": {
                "status": "CLARIFY",
                "unresolved_flagged": True,
                "clarification_code": "INCOMPLETE_GOAL_OPERAND",
            },
        },
        # 3. Unambiguous prompt falsely clarified (counts as false_clarification)
        {
            "case_id": "SL-P03",
            "expected": {
                "outcome": "SERVED",
                "is_ambiguous": False,
                "expected_facts_signature": "cube_2",
                "expected_goals": ["volume:ABCD.A'B'C'D'"],
                "expected_operands": ["ABCD.A'B'C'D'", "2"],
                "expected_answers": {"q1": "8"},
            },
            "observed": {
                "status": "CLARIFY",
                "unresolved_flagged": True,
                "clarification_code": "AMBIGUOUS_FACT",
            },
        },
        # 4. Unsupported prompt properly refused
        {
            "case_id": "SL-P04",
            "expected": {
                "outcome": "REFUSED_UNSUPPORTED",
                "is_ambiguous": False,
            },
            "observed": {
                "status": "REFUSED",
                "is_unsupported_code": True,
            },
        },
        # 5. Wrong-served case (dropped second goal)
        {
            "case_id": "SL-P05",
            "expected": {
                "outcome": "SERVED",
                "is_ambiguous": False,
                "expected_facts_signature": "pyr_two_goals",
                "expected_goals": ["volume:S.ABCD", "length:SC"],
                "expected_operands": ["S.ABCD", "S", "C"],
                "expected_answers": {"q1": "8/3", "q2": "2√3"},
            },
            "observed": {
                "status": "SERVED",
                "facts_signature": "pyr_one_goal",
                "extracted_goals": ["volume:S.ABCD"],
                "operands": ["S.ABCD"],
                "quotes_verbatim_in_raw": True,
                "answers": {"q1": "8/3"},
                "certificate_verified": True,
            },
        },
        # 6. Provider timeout / missing output -> NOT_RECOVERABLE (excluded from denominator, never 0)
        {
            "case_id": "SL-P06",
            "expected": {"outcome": "SERVED", "is_ambiguous": False},
            "observed": {"status": "NOT_RECOVERABLE"},
        },
    ]

    rep = score_s2_pilot_records(records)
    assert rep["live_provider_calls"] == 0
    assert rep["total_records"] == 6
    assert rep["evaluable_records"] == 5
    assert rep["not_recoverable_records"] == 1
    m = rep["metrics"]
    assert m["extraction_accuracy"] == {"numerator": 1, "denominator": 3, "rate": 0.333333}
    assert m["goal_completeness"] == {"numerator": 1, "denominator": 3, "rate": 0.333333}
    assert m["operand_preservation"] == {"numerator": 1, "denominator": 3, "rate": 0.333333}
    assert m["ambiguity_detection"] == {"numerator": 1, "denominator": 1, "rate": 1.0}
    assert m["clarification_correctness"] == {"numerator": 1, "denominator": 2, "rate": 0.5}
    assert m["false_clarification"] == {"numerator": 1, "denominator": 4, "rate": 0.25}
    assert m["unsupported_classification"] == {"numerator": 1, "denominator": 1, "rate": 1.0}
    assert m["wrong_served_end_to_end"] == {"numerator": 1, "denominator": 5, "rate": 0.2}


def test_s2_refuses_to_run_if_allow_live_ai_is_enabled(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    with pytest.raises(RuntimeError):
        score_s2_pilot_records([])
