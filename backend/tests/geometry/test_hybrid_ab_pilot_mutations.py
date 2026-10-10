"""Executable guard-removal mutants. Mutations exist only in memory and cannot alter frozen evidence."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest


def _tests(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R = _tests("test_hybrid_ab_pilot_runner")
S = _tests("test_hybrid_safety_readiness")


@pytest.mark.parametrize("mutant", ["remove_budget_precheck", "swap_arm_adapters", "accept_missing_usage",
    "smoke_as_full", "promote_configuration_to_proof", "remove_object_binding", "substring_polygon",
    "ignore_top_face", "join_unnamed_solid_to_next_clause"])
def test_safety_mutant_is_killed_by_behavioral_regression(mutant, tmp_path, monkeypatch):
    """Each original scenario passes; disabling the named guard must make that SAME assertion fail."""
    P = R.P
    if mutant == "remove_budget_precheck":
        check = lambda path: R.test_budget_guards_stop_before_the_provider(path, "logical_calls", 0, "LOGICAL_CAP")
        original = P.PilotBudget.reserve
        mutate = lambda: monkeypatch.setattr(P.PilotBudget, "reserve", lambda self, reservation, caps:
            original(self, reservation, replace(caps, logical_calls=300)))
    elif mutant == "swap_arm_adapters":
        from app.ai import function_calling as a, fact_extraction as b
        aa, bb = a.run_ai_function_route, b.run_ai_fact_route
        check = lambda path: R.test_runner_executes_both_real_adapters_with_separate_telemetry_and_resume(path, P.PilotMode.SMOKE_AB, 24)
        def mutate():
            monkeypatch.setattr(a, "run_ai_function_route", bb)
            monkeypatch.setattr(b, "run_ai_fact_route", aa)
    elif mutant == "accept_missing_usage":
        check = lambda path: R.test_unknown_cost_identity_truncation_and_secret_stop_without_retry(path,
            lambda body: {k: v for k, v in body.items() if k != "usageMetadata"}, "USAGE_UNKNOWN")
        original = P._usage
        mutate = lambda: monkeypatch.setattr(P, "_usage", lambda body, reservation: original(dict(body,
            usageMetadata={"promptTokenCount": 0, "candidatesTokenCount": 0, "totalTokenCount": 0}), reservation))
    elif mutant == "smoke_as_full":
        def check(path):
            try:
                P.score_pilot(P.PilotMode.SMOKE_AB, R._scoring_rows())
            except P.PilotStopped as error:
                assert str(error) == "SMOKE_NOT_FULL"
            else:
                assert False, "smoke produced a full comparison"
        original = P.score_pilot
        mutate = lambda: monkeypatch.setattr(P, "score_pilot", lambda mode, rows: original(P.PilotMode.FULL_AB, rows))
    elif mutant == "promote_configuration_to_proof":
        check = lambda path: S.test_true_on_configuration_is_not_reported_as_proof()
        original = S.FR._quan_sat_cau_hinh
        mutate = lambda: monkeypatch.setattr(S.FR, "_quan_sat_cau_hinh", lambda value: dict(original(value),
            proof_status="PROVED_FROM_HYPOTHESES", can_present_as_proven=True))
    elif mutant == "remove_object_binding":
        check = lambda path: S.test_grounding_oracle_is_literal_and_shared_by_both_arms("MULTIPLE_OBJECTS_CUBE")
        mutate = lambda: monkeypatch.setattr(S.RG, "_co_doi_tuong_hinh", lambda call: True)
    elif mutant == "substring_polygon":
        check = lambda path: S.test_structural_phrase_binds_either_named_face_but_not_a_mixed_face("regular_polygon")
        mutate = lambda: monkeypatch.setattr(S.RG, "_cung_da_giac", lambda a, b: bool(set(a) & set(b)))
    elif mutant == "ignore_top_face":
        check = lambda path: S.test_structural_phrase_binds_either_named_face_but_not_a_mixed_face("regular_polygon")
        original = S.RG._cung_da_giac
        mutate = lambda: monkeypatch.setattr(S.RG, "_cung_da_giac", lambda a, b:
            False if "E" in a else original(a, b))
    else:
        check = lambda path: S.test_unnamed_solid_cue_cannot_capture_polygon_in_next_clause("regular_polygon", "hình lập phương")
        def joined(q, pattern, vertices):
            return any(any(S.RG._cung_da_giac(part, vertices) for part in token)
                for match in pattern.finditer(q) for start, end, token in S.RG._tu_nhan(q) if start >= match.end())
        mutate = lambda: monkeypatch.setattr(S.RG, "_mat_cua_khoi_sau_cum", joined)
    check(tmp_path / "baseline")
    mutate()
    with pytest.raises(AssertionError):
        check(tmp_path / "mutant")
