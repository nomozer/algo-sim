"""Offline contract for the corrected hybrid A/B pilot runner.  No network provider is allowed here."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import copy
import json
from dataclasses import replace

import pytest


_p = importlib.util.spec_from_file_location("_pilot", Path(__file__).resolve().parents[2] / "scripts" / "run_hybrid_ab_pilot.py")
P = importlib.util.module_from_spec(_p)
assert _p and _p.loader
sys.modules[_p.name] = P
_p.loader.exec_module(P)


def test_locked_modes_have_separate_corpora_and_exact_schedule_sizes():
    smoke = P.load_locked_inputs(P.PilotMode.SMOKE_AB)
    full = P.load_locked_inputs(P.PilotMode.FULL_AB)
    assert len(smoke.rows) == 12
    assert len(full.rows) == 48
    assert smoke.identity.corpus_sha256 != full.identity.corpus_sha256
    assert len(P.schedule(smoke)) == 24
    assert len(P.schedule(full)) == 288
    assert [r.case_id for r in smoke.rows] == [
        "g05/X1", "g05/P09", "g05/NT2", "g05/N02", "paraphrase/P01", "paraphrase/P08",
        "expansion/X02", "expansion/X06", "hybrid/H01", "hybrid/H05", "hybrid/H07", "hybrid/H13",
    ]


def test_all_corpus_reservations_select_3072_without_relaxing_usd_caps():
    audit = P.audit_reservations()
    assert audit[3072]["smoke"]["tokens"] <= P.CAPS[P.PilotMode.SMOKE_AB].accounted_tokens
    assert audit[3072]["smoke"]["usd"] <= P.CAPS[P.PilotMode.SMOKE_AB].usd
    assert audit[3072]["full"]["tokens"] <= P.CAPS[P.PilotMode.FULL_AB].accounted_tokens
    assert audit[3072]["full"]["usd"] <= P.CAPS[P.PilotMode.FULL_AB].usd
    assert audit[8192]["smoke"]["usd"] > P.CAPS[P.PilotMode.SMOKE_AB].usd
    assert P.MAX_OUTPUT_TOKENS == 3072


class Fake:
    def __init__(self, change=None):
        self.calls = []
        self.change = change

    def send(self, arm, payload, timeout_seconds):
        self.calls.append((arm, copy.deepcopy(payload)))
        if arm == "A":
            parts = [{"functionCall": {"name": "unsupported", "args": {
                "call_id": "c1", "quotes": [], "reason": "offline apparatus fixture"}}}]
        else:
            parts = [{"text": json.dumps({"facts": []})}]
        body = {"modelVersion": "gemini-2.5-flash", "usageMetadata": {
            "promptTokenCount": 100, "candidatesTokenCount": 50, "thoughtsTokenCount": 10,
            "totalTokenCount": 160}, "candidates": [{"finishReason": "STOP", "content": {"parts": parts}}]}
        if self.change:
            return self.change(body)
        return body


@pytest.mark.parametrize("mode,count", [(P.PilotMode.SMOKE_AB, 24), (P.PilotMode.FULL_AB, 288)])
def test_runner_executes_both_real_adapters_with_separate_telemetry_and_resume(tmp_path, mode, count):
    fake = Fake()
    result = P.run_pilot(mode, fake, tmp_path)
    assert result["stop_reason"] is None
    assert len(result["rows"]) == len(fake.calls) == count
    assert result["totals"]["A"]["input_tokens"] == result["totals"]["B"]["input_tokens"] == count // 2 * 100
    assert result["totals"]["A"]["thinking_tokens"] == count // 2 * 10
    assert result["live_model_calls"] == 0
    for row, (arm, payload) in zip(result["rows"], fake.calls):
        assert row["arm"] == arm
        assert ("tools" in payload) == (arm == "A")
        assert payload["generationConfig"]["maxOutputTokens"] == 3072
        assert row["payload_sha256"] == P._sha(payload)
        assert row["latency_seconds"] >= 0
        assert row["model_version"] == "gemini-2.5-flash"
        assert row["route"]["status"] == "REFUSED"
        assert row["raw_response"]["usageMetadata"]["totalTokenCount"] == 160
    resumed = P.run_pilot(mode, fake, tmp_path, resume=True)
    assert resumed == result
    assert len(fake.calls) == count


@pytest.mark.parametrize("field,value,code", [
    ("logical_calls", 0, "LOGICAL_CAP"), ("http_attempts", 0, "HTTP_CAP"),
    ("accounted_tokens", 1, "TOKEN_CAP"), ("usd", 0.00001, "USD_CAP"),
])
def test_budget_guards_stop_before_the_provider(tmp_path, field, value, code):
    fake = Fake()
    caps = replace(P.CAPS[P.PilotMode.SMOKE_AB], **{field: value})
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path, caps=caps)
    assert result["stop_reason"] == code
    assert fake.calls == []


@pytest.mark.parametrize("change,code", [
    (lambda b: {k: v for k, v in b.items() if k != "usageMetadata"}, "USAGE_UNKNOWN"),
    (lambda b: dict(b, usageMetadata={"promptTokenCount": True}), "USAGE_UNKNOWN"),
    (lambda b: {k: v for k, v in b.items() if k != "modelVersion"}, "MODEL_VERSION_MISSING"),
    (lambda b: dict(b, modelVersion="another-model"), "MODEL_VERSION_MISMATCH"),
    (lambda b: dict(b, error={"code": 429}), "HTTP_ERROR"),
    (lambda b: dict(b, usageMetadata=dict(b["usageMetadata"], thoughtsTokenCount=99999, totalTokenCount=100149)),
     "RESERVATION_BREACH"),
    (lambda b: dict(b, candidates=[{"finishReason": "MAX_TOKENS", "content": {"parts": []}}]), "RESPONSE_TRUNCATED"),
    (lambda b: dict(b, nested={"authorization": "fake-secret-key"}), "SECRET_DETECTED"),
])
def test_unknown_cost_identity_truncation_and_secret_stop_without_retry(tmp_path, change, code):
    fake = Fake(change)
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path, secrets=("fake-secret-key",))
    assert result["stop_reason"] == code
    assert len(fake.calls) == 1
    assert result["rows"][0]["failure_source"] == "infrastructure"
    assert "fake-secret-key" not in (tmp_path / "manifest.json").read_text(encoding="utf-8")
    assert P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path, resume=True, secrets=("fake-secret-key",)) == result
    assert len(fake.calls) == 1


@pytest.mark.parametrize("exc", [TimeoutError, ConnectionError, RuntimeError])
def test_exception_cost_unknown_is_durable_and_never_retried(tmp_path, exc):
    def fail(_):
        raise exc("sensitive message")
    fake = Fake(fail)
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] == ("TIMEOUT" if exc is TimeoutError else "PROVIDER_ERROR")
    assert result["rows"][0]["usage"] is None
    assert len(fake.calls) == 1


def test_partial_pending_request_and_mode_mismatch_refuse_resume(tmp_path):
    result = P.run_pilot(P.PilotMode.SMOKE_AB, Fake(), tmp_path)
    with pytest.raises(P.PilotStopped, match="IDENTITY_MISMATCH"):
        P.run_pilot(P.PilotMode.FULL_AB, Fake(), tmp_path, resume=True)
    result["pending"] = {"position": 24}
    (tmp_path / "manifest.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(P.PilotStopped, match="REQUEST_STATE_UNKNOWN"):
        P.run_pilot(P.PilotMode.SMOKE_AB, Fake(), tmp_path, resume=True)


def test_input_hash_pin_rejects_text_tamper_before_provider(tmp_path, monkeypatch):
    read = P._read_json
    def changed(name):
        value = read(name)
        if name == "pilot_cases.json":
            value["rows"][0]["text"] += " tampered"
        return value
    monkeypatch.setattr(P, "_read_json", changed)
    fake = Fake()
    with pytest.raises(P.PilotStopped, match="INPUT_IDENTITY_MISMATCH"):
        P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert fake.calls == []


def test_response_malformed_content_has_known_usage_and_extraction_taxonomy(tmp_path):
    fake = Fake(lambda b: dict(b, candidates=[{"finishReason": "STOP", "content": {"parts": []}}]))
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] is None
    assert len(result["rows"]) == 24
    assert {r["failure_source"] for r in result["rows"]} == {"ai_extraction"}


def test_output_directory_cannot_overwrite_historical_evidence():
    with pytest.raises(P.PilotStopped, match="EVIDENCE_PATH_FORBIDDEN"):
        P.run_pilot(P.PilotMode.SMOKE_AB, Fake(), P.ROOT / "docs/evaluation/geometry/runs/hybrid-compiler-selection")


def test_unknown_usage_totals_are_unknown_not_zero(tmp_path):
    result = P.run_pilot(P.PilotMode.SMOKE_AB, Fake(lambda b: {}), tmp_path)
    assert result["totals"]["unknown_usage_rows"] == 1
    assert result["totals"]["actual_usd"] is None


def test_persistence_failure_before_request_sends_nothing(tmp_path, monkeypatch):
    persist = P._persist
    def fail_pending(path, state, secrets):
        if state["pending"] is not None:
            raise P.PilotStopped("PERSISTENCE_FAILED")
        persist(path, state, secrets)
    monkeypatch.setattr(P, "_persist", fail_pending)
    fake = Fake()
    with pytest.raises(P.PilotStopped, match="PERSISTENCE_FAILED"):
        P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert fake.calls == []


def test_completed_artifact_row_tamper_is_rejected(tmp_path):
    result = P.run_pilot(P.PilotMode.SMOKE_AB, Fake(), tmp_path)
    result["rows"][0]["arm"] = "invalid"
    (tmp_path / "manifest.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(P.PilotStopped, match="PARTIAL_ARTIFACT"):
        P.run_pilot(P.PilotMode.SMOKE_AB, Fake(), tmp_path, resume=True)


def test_provider_request_payload_larger_than_context_stops_before_send(tmp_path, monkeypatch):
    from app.ai import function_calling as a, fact_extraction as b
    for module in (a, b):
        build = module.build_request
        monkeypatch.setattr(module, "build_request", lambda text, *args, _build=build, **kwargs: dict(_build(text, *args, **kwargs), large="x" * 1_100_000))
    fake = Fake()
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] in {"TOKEN_CAP", "CONTEXT_CAP"}
    assert fake.calls == []


def test_live_gate_requires_explicit_matching_approval_before_transport(monkeypatch, tmp_path):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(P.PilotStopped, match="LIVE_NOT_APPROVED"):
        P.live_provider(P.PilotMode.SMOKE_AB, None)


def test_approved_live_factory_uses_existing_transport_without_network(monkeypatch, tmp_path):
    from app.ai import function_calling as fc
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    received = {}
    def factory(api_key, model=None, timeout_seconds=60):
        received.update(key=api_key, model=model, timeout=timeout_seconds)
        return lambda payload: {"fake": True}
    monkeypatch.setattr(fc, "live_transport", factory)
    identity = P.measurement_identity(P.load_locked_inputs(P.PilotMode.SMOKE_AB), P.CAPS[P.PilotMode.SMOKE_AB])
    monkeypatch.setattr(P, "frozen_identity", lambda mode: identity)
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps({"decision": "HUMAN_APPROVED_LIVE_EXECUTION", "identity": identity}), encoding="utf8")
    provider = P.live_provider(P.PilotMode.SMOKE_AB, approval)
    assert provider.send("A", {}, 60) == {"fake": True}
    assert received == {"key": "fake-test-key", "model": "gemini-2.5-flash", "timeout": 60}


def test_redaction_handles_secret_in_json_keys_before_writing(tmp_path):
    fake = Fake(lambda b: dict(b, **{"fake-test-key": {"message": "fake-test-key"}}))
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path, secrets=("fake-test-key",))
    assert result["stop_reason"] == "SECRET_DETECTED"
    assert "fake-test-key" not in (tmp_path / "manifest.json").read_text(encoding="utf8")


def test_provider_envelope_with_invalid_content_shape_is_durable(tmp_path):
    fake = Fake(lambda b: dict(b, candidates=[{"finishReason": "STOP", "content": "invalid"}]))
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] == "PROVIDER_RESPONSE_INVALID"
    assert len(fake.calls) == 1


def test_fixture_certifier_provider_exercises_served_geometry_and_proof_boundary(tmp_path):
    from scripts.certify_hybrid_ab_pilot import FixtureProvider
    provider = FixtureProvider()
    result = P.run_pilot(P.PilotMode.SMOKE_AB, provider, tmp_path)
    assert len(result["rows"]) == 24 and result["stop_reason"] is None
    assert any(x["route"]["scene3d"] for x in result["rows"])
    goal = next(x for x in result["rows"] if x["case_id"] == "hybrid/H07" and x["arm"] == "B")
    assert goal["route"]["planner"]["goal_checks"]["f7"]["can_present_as_proven"] is False
    assert max(provider.response_bytes.values()) < 3072


def test_live_provider_cannot_write_fake_evidence_paths(tmp_path):
    fake = Fake()
    fake.is_live = True
    with pytest.raises(P.PilotStopped, match="LIVE_EVIDENCE_FORBIDDEN"):
        P.run_pilot(P.PilotMode.SMOKE_AB, fake, P.INPUTS.parent / "fake-provider/live")


def test_full_identity_cannot_bypass_live_approval_with_empty_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    approval = tmp_path / "approval.json"
    approval.write_text("{}", encoding="utf8")
    with pytest.raises(P.PilotStopped, match="LIVE_NOT_APPROVED"):
        P.live_provider(P.PilotMode.FULL_AB, approval)


def _scoring_rows(outcomes_a="correct_served", outcomes_b="correct_served"):
    locked = P.load_locked_inputs(P.PilotMode.FULL_AB)
    return [{"case_id": c.case_id, "sample": c.sample, "arm": c.arm,
             "outcome": outcomes_a if c.arm == "A" else outcomes_b,
             "usage": {"output_tokens": 50, "thinking_tokens": 0}}
            for c in P.schedule(locked)]


def test_zero_errors_reports_finite_sample_uncertainty_and_no_proof_of_safety():
    rows = _scoring_rows()
    summary = P.score_pilot(P.PilotMode.FULL_AB, rows)
    assert summary["warning"] == "NO OBSERVED ERROR ≠ PROVED SAFE"
    assert summary["wrong_served"]["A"]["denominator"] == 144
    assert summary["wrong_served"]["A"]["iid_upper_95"] > 0
    assert summary["wrong_served"]["A"]["cluster_upper_95"] > 0
    assert summary["label"] == "NON_INFERIOR_NOT_SUPERIOR"
    assert P.score_pilot(P.PilotMode.FULL_AB, rows) == summary
    with pytest.raises(P.PilotStopped, match="SMOKE_NOT_FULL"):
        P.score_pilot(P.PilotMode.SMOKE_AB, rows)


@pytest.mark.parametrize("a,b,label", [
    ("false_refusal", "correct_served", "SUPERIOR"),
    ("correct_served", "wrong_served", "INFERIOR"),
    ("wrong_served", "false_refusal", "INFERIOR"),
    ("infrastructure", "correct_served", "INCONCLUSIVE_INFRASTRUCTURE"),
])
def test_paired_scoring_respects_safety_utility_and_infrastructure(a, b, label):
    assert P.score_pilot(P.PilotMode.FULL_AB, _scoring_rows(a, b))["label"] == label


def test_incomplete_or_duplicate_schedule_cannot_be_scored_as_full():
    rows = _scoring_rows()
    assert P.score_pilot(P.PilotMode.FULL_AB, rows[:-1])["label"] == "INCONCLUSIVE_INFRASTRUCTURE"
    assert P.score_pilot(P.PilotMode.FULL_AB, rows[:-1] + [rows[0]])["label"] == "INCONCLUSIVE_INFRASTRUCTURE"


def test_reordered_renamed_answer_calls_are_bound_to_questions_not_insertion_order():
    from types import SimpleNamespace
    route = SimpleNamespace(status="SERVED", answers={"diagonal": "a√3", "volume": "a³"},
        answer_exact={"diagonal": {"coef": "√3", "dim": 1}, "volume": {"coef": "1", "dim": 3}},
        calls=[{"id": "diagonal", "fn": "ask_length", "args": {"segment": ["A", "C'"]}},
               {"id": "volume", "fn": "ask_volume", "args": {"solid": "ABCD.A'B'C'D'"}}], planner={})
    assert P.classify_outcome("hybrid/H01", "A", route) == "correct_served"


def test_numeric_match_on_wrong_question_object_is_wrong_service():
    from types import SimpleNamespace
    route = SimpleNamespace(status="SERVED", answers={"q": "18√3"}, answer_exact={},
        calls=[{"id": "q", "fn": "ask_volume", "args": {"solid": "WRONG_OBJECT"}}], planner={})
    assert P.classify_outcome("g05/X1", "A", route) == "wrong_served"


def test_cluster_bootstrap_preserves_multiplicity_for_output_ratio(monkeypatch):
    rows = _scoring_rows()
    ids = sorted({r["case_id"] for r in rows})
    for row in rows:
        if row["arm"] == "B" and row["case_id"] == ids[0]:
            row["usage"]["output_tokens"] = 250
    monkeypatch.setattr(P.random.Random, "choices", lambda self, population, k: [ids[0]] * (k - 1) + [ids[1]])
    summary = P.score_pilot(P.PilotMode.FULL_AB, rows)
    assert summary["paired_intervals"]["output_ratio"]["upper_one_sided_95"] == 5.0


def test_failed_noninferiority_is_not_automatically_evidence_of_inferiority():
    rows = _scoring_rows()
    cases = sorted({x["case_id"] for x in rows})[:3]
    for row in rows:
        if row["arm"] == "B" and row["case_id"] in cases:
            row["outcome"] = "wrong_served"
    assert P.score_pilot(P.PilotMode.FULL_AB, rows)["label"] == "INCONCLUSIVE_STATISTICAL"


def test_provider_safety_block_is_infrastructure_not_correct_refusal(tmp_path):
    fake = Fake(lambda body: dict(body, candidates=[{"finishReason": "SAFETY", "content": {"parts": []}}]))
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] == "PROVIDER_BLOCKED"
    assert len(fake.calls) == 1
    assert result["rows"][0]["outcome"] == "infrastructure"


def test_question_oracle_tamper_stops_before_provider(tmp_path, monkeypatch):
    read = P._read_json
    def changed(name):
        data = read(name)
        if name == "question_obligations.json":
            data["rows"][0]["A"]["c5"]["args"]["solid"] = "OTHER"
        return data
    monkeypatch.setattr(P, "_read_json", changed)
    fake = Fake()
    with pytest.raises(P.PilotStopped, match="INPUT_IDENTITY_MISMATCH"):
        P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert fake.calls == []


def test_live_approval_must_match_frozen_run_not_only_current_code(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    identity = P.measurement_identity(P.load_locked_inputs(P.PilotMode.SMOKE_AB), P.CAPS[P.PilotMode.SMOKE_AB])
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps({"decision": "HUMAN_APPROVED_LIVE_EXECUTION", "identity": identity}), encoding="utf8")
    monkeypatch.setattr(P, "frozen_identity", lambda mode: {"tampered": True}, raising=False)
    with pytest.raises(P.PilotStopped, match="FROZEN_IDENTITY_MISMATCH"):
        P.live_provider(P.PilotMode.SMOKE_AB, approval)


def test_budget_audit_integer_keys_can_be_persisted_safely(tmp_path):
    path = tmp_path / "budget.json"
    P._persist(path, {"comparison": {3072: {"usd": .3107664}}}, ())
    assert json.loads(path.read_bytes()) == {"comparison": {"3072": {"usd": .3107664}}}


@pytest.mark.parametrize("case", ["H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS", "H14_REGULAR_TETRAHEDRON"])
def test_sealed_question_signatures_match_handwritten_b_geometry(case):
    from app.ai.function_route import run_fact_route
    fixture = json.loads((Path(__file__).parent / "fixtures/hybrid_holdout_cases.json").read_bytes())
    row = next(x for x in fixture["cases"] if x["id"] == case)
    route = run_fact_route(row["text"], {"facts": row["b_facts"]})
    assert route.status == "SERVED"
    assert P.classify_outcome("hybrid/" + case[:3], "B", route) == "correct_served"


def test_existing_httpx_transport_timeout_has_timeout_taxonomy(tmp_path):
    import httpx
    def fail(body):
        raise httpx.ReadTimeout("fake confidential detail")
    fake = Fake(fail)
    result = P.run_pilot(P.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] == "TIMEOUT"
    assert len(fake.calls) == 1
    assert result["totals"]["actual_usd"] is None
