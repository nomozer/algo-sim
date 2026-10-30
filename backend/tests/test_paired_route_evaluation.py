# -*- coding: utf-8 -*-
"""Paired LLM_ONLY vs Hybrid harness (`scripts/run_paired_route_evaluation.py`): scoring, statistics and the live gate.

All offline. Dry runs read recorded arm outputs. The live path runs against a MOCK provider (`httpx.post` replaced; the
conftest transport guard still blocks the real network underneath) with approved TERMS passed in memory — automation
never writes an approval value (AGENTS.md). A mock run is never live evidence.
"""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import httpx
import pytest

from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

_spec = importlib.util.spec_from_file_location(
    "run_paired_route_evaluation", Path(__file__).resolve().parents[1] / "scripts/run_paired_route_evaluation.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

SERVED = _prism()


def _quantity(producer, exact, group=("target",)):
    return {"type": "quantity", "display_group": list(group), "producer": producer, "exact": exact}


def _ok(*objects):
    return {"status": "ok", "scene3d": {"objects": list(objects)}}


def _write(tmp_path, cases, name="corpus.json"):
    path = tmp_path / name
    path.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8")
    return path


def _corpus(tmp_path):
    contradiction = deepcopy(SERVED)
    contradiction["premises"][1]["args"]["value"] = "7"                        # text says AB = 6
    contradiction["problem_text"] = SERVED["problem_text"] + " (bản hai)"
    twelve = _quantity("measure.distance", {"kind": "rational", "value": "12"})
    return _write(tmp_path, [
        {"id": "C1", "problem_text": SERVED["problem_text"], "expect": "SERVE", "oracle": {"distance": ["144"]},
         "dry_run": {"hybrid_extraction": SERVED, "llm_only_envelope": _ok(twelve)}},
        {"id": "C2", "problem_text": SERVED["problem_text"] + " ", "expect": "SERVE", "oracle": {"distance": ["144"]},
         "dry_run": {"hybrid_extraction": None,                                 # Hybrid: nothing extracted → refusal
                     "llm_only_envelope": _ok(_quantity("measure.distance", {"kind": "rational", "value": "13"}))}},
        {"id": "C3", "problem_text": contradiction["problem_text"], "expect": "REFUSE",
         "acceptable_refusal_codes": ["UNGROUNDED_VALUE", "GATE_INCONSISTENT"],
         "dry_run": {"hybrid_extraction": contradiction,
                     "llm_only_envelope": {"status": "unsupported", "error_code": "GATE_INCONSISTENT"}}},
    ])


def _terms(corpus_path, **over):
    return {"corpus_sha256": E.sha256_file(corpus_path), "max_requests": 40, "max_usd": 7.0, "model": "gemini-2.5-flash",
            "input_usd_per_million": 0.30, "output_usd_per_million": 2.50,
            "llm_only_output_reservation_tokens": 65536, **over}


# ── scoring and statistics ───────────────────────────────────────────────────────────────────────────────────────────

def test_one_scorer_reads_learner_visible_targets_by_kind_as_exact_multisets():
    env = _ok(_quantity("measure.distance", {"kind": "radical", "coefficient": "2/3", "radicand": 6}),
              _quantity("measure.angle_cos_sq", {"kind": "rational", "value": "1/2"}),
              _quantity("measure.volume", {"kind": "rational", "value": "5"}, group=("given",)))   # not a target
    assert E.served_quantities(env) == {"distance": [Fraction(8, 3)], "angle_cos_sq": [Fraction(1, 2)]}
    case = {"expect": "SERVE", "oracle": {"distance": ["8/3"], "angle_cos_sq": ["1/2"]}}
    assert E.score(case, env)["served_correct"] is True
    extra = _ok(*env["scene3d"]["objects"], _quantity("measure.area", {"kind": "rational", "value": "3"}))
    assert E.score(case, extra)["wrong_served"] is True                       # an unasked served target is not correct
    assert E.score({"expect": "REFUSE"}, {"status": "unsupported", "error_code": "X"})["refusal_reason_correct"] is False


def test_dry_run_scores_both_arms_pairs_them_and_never_touches_a_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("dry run sent a provider request"))
    out = E.evaluate(_corpus(tmp_path), tmp_path / "rows.json", None)
    assert out["measurement_class"] == "OFFLINE_DETERMINISTIC_FIXTURE_TEST" and out["http_requests"] == 0
    rows = {(r["case_id"], r["arm"]): r for r in out["rows"]}
    assert rows["C1", "HYBRID"]["served_correct"] and rows["C1", "LLM_ONLY"]["served_correct"]
    assert rows["C2", "HYBRID"]["false_refusal"] and rows["C2", "LLM_ONLY"]["wrong_served"]
    assert rows["C3", "HYBRID"]["refusal_code"] == "UNGROUNDED_VALUE" and rows["C3", "HYBRID"]["refusal_reason_correct"]
    assert rows["C1", "HYBRID"]["source_references"]                          # provenance from the receipt
    s = out["summary"]
    assert (s["HYBRID"]["served_correct"], s["HYBRID"]["wrong_served"], s["HYBRID"]["false_refusal"]) == (1, 0, 1)
    assert (s["LLM_ONLY"]["served_correct"], s["LLM_ONLY"]["wrong_served"]) == (1, 1)
    assert s["paired"]["mcnemar_p"] == 1.0 and s["HYBRID"]["usd_total"] == "UNKNOWN"   # no usage ⇒ UNKNOWN, not 0
    assert out["completed"] is True and out["runtime_identity"]["cache_version"] == "131"


def test_statistics():
    lo, hi = E.wilson(9, 10)
    assert 0.59 < lo < 0.60 and 0.98 < hi < 0.99
    assert E.wilson(0, 0) is None
    assert E.mcnemar_exact(0, 6) == pytest.approx(2 / 64) and E.mcnemar_exact(3, 3) == 1.0


# ── authorization and corpus integrity: refused before any request ───────────────────────────────────────────────────

def test_live_is_refused_before_any_request(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("a refused run sent a request"))
    corpus = _corpus(tmp_path)
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(E.LiveRefused):
        E.authorize_live(corpus, None)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    with pytest.raises(E.LiveRefused):
        E.authorize_live(corpus, None)
    pending = tmp_path / "approval.json"
    pending.write_text(json.dumps({**_terms(corpus), "owner_decision": "PENDING_OWNER_DECISION"}), encoding="utf-8")
    with pytest.raises(E.LiveRefused):
        E.authorize_live(corpus, pending)
    for bad in ({"corpus_sha256": "0" * 64}, {"model": "another-model"}, {"max_requests": 10_000},
                {"llm_only_output_reservation_tokens": 8192}):       # below the model limit LLM_ONLY can use
        with pytest.raises(E.LiveRefused):
            E.check_approval_terms(corpus, _terms(corpus, **bad))
    assert E.check_approval_terms(corpus, _terms(corpus))["max_requests"] == 40


@pytest.mark.parametrize("mutate", [
    lambda cs: cs.append(dict(cs[0], id="dup-text")),                    # duplicate request (same text)
    lambda cs: cs.append(dict(cs[1], problem_text="khác")) or cs[-1].update(id=cs[0]["id"]),   # duplicate id
    lambda cs: cs[0].update(oracle={}),                                   # expected-serve without oracle
    lambda cs: cs[0].update(oracle={"perimeter": ["4"]}),                 # unknown kind
    lambda cs: cs[2].update(acceptable_refusal_codes=[]),                 # expected-refuse without codes
])
def test_an_invalid_corpus_is_refused_before_any_request(tmp_path, mutate):
    cases = json.loads(_corpus(tmp_path).read_text(encoding="utf-8"))["cases"]
    mutate(cases)
    bad = _write(tmp_path, cases, "bad.json")
    with pytest.raises(E.LiveRefused):
        E.evaluate(bad, tmp_path / "out.json", None)
    assert not (tmp_path / "out.json").exists()


# ── mock provider: every live failure mode is contained, counted and never scored as a model result ──────────────────

def _body(payload=None, finish="STOP", text=None, block=None):
    if block:
        return {"promptFeedback": {"blockReason": block}}
    return {"candidates": [{"content": {"parts": [{"text": text if text is not None else json.dumps(payload,
                                                                                                    ensure_ascii=False)}]},
                            "finishReason": finish}],
            "usageMetadata": {"promptTokenCount": 9000, "candidatesTokenCount": 700, "totalTokenCount": 9700}}


class Provider:
    """Scripted `httpx.post` replacement: each call pops the next action (a body dict, an int status, or an exception)."""

    def __init__(self, *script, default=None):
        self.script, self.default, self.calls = list(script), default, 0

    def __call__(self, url, **kwargs):
        assert "key=" not in url and kwargs["headers"]["x-goog-api-key"]          # the key travels in a header
        self.calls += 1
        step = self.script.pop(0) if self.script else self.default
        if isinstance(step, Exception):
            raise step
        request = httpx.Request("POST", url)
        if isinstance(step, int):
            return httpx.Response(step, json={"error": {"code": step}}, request=request)
        return httpx.Response(200, json=step, request=request)


def _live(tmp_path, monkeypatch, provider, cases=None, llm_only=None, **terms):
    corpus = _write(tmp_path, cases) if cases is not None else _corpus(tmp_path)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", provider)

    async def fake_llm_only(text, api_key):
        return llm_only or {"status": "unsupported", "error_code": "FAKE_LLM_ONLY"}

    monkeypatch.setattr(E, "run_llm_only", fake_llm_only)
    return E.evaluate(corpus, tmp_path / "live.json", _terms(corpus, **terms), sleep=lambda s: None)


def _one(case_id="L1", payload=SERVED, expect="SERVE"):
    c = {"id": case_id, "problem_text": payload["problem_text"], "expect": expect}
    return c | ({"oracle": {"distance": ["144"]}} if expect == "SERVE" else {"acceptable_refusal_codes": ["X"]})


def test_mock_success_is_scored_with_usage_and_cost(tmp_path, monkeypatch):
    out = _live(tmp_path, monkeypatch, Provider(_body(SERVED)), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["served_correct"] and row["http_requests"] == 1 and row["requests_with_usage"] == 1
    assert row["usd"] == pytest.approx(9000 * 0.30e-6 + 700 * 2.50e-6)
    assert out["measurement_class"] == "PREREGISTERED_LIVE_PAIRED_EVALUATION" and out["completed"]


def test_mock_rate_limit_is_retried_like_call_gemini_and_each_retry_is_budgeted(tmp_path, monkeypatch):
    out = _live(tmp_path, monkeypatch, Provider(429, 503, _body(SERVED)), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["served_correct"] and row["http_requests"] == 3


@pytest.mark.parametrize("action,code", [
    (httpx.ReadTimeout("mock timeout"), "PROVIDER_ERROR"),
    (500, "PROVIDER_ERROR"),
    (400, "PROVIDER_ERROR"),
])
def test_mock_transport_failures_are_technical_never_model_or_geometry_outcomes(tmp_path, monkeypatch, action, code):
    out = _live(tmp_path, monkeypatch, Provider(default=action), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["technical_failure"] and row["hybrid_code"] == code and not row["served"]
    assert row["false_refusal"] is False                                        # infrastructure is not a false refusal
    assert row["http_requests"] == (1 if action == 400 else 4)                  # 4xx is not retried; transient is


@pytest.mark.parametrize("body,code", [
    (_body(SERVED, finish="MAX_TOKENS"), "RESPONSE_TRUNCATED"),                # partial / truncated output
    (_body(text='{"schema_version": "typed-fact-next/2", "problem_text": '), "JSON_INVALID"),   # invalid JSON
    (_body(block="SAFETY"), "PROVIDER_BLOCKED"),                                # provider refusal (prompt)
    (_body(SERVED, finish="SAFETY"), "PROVIDER_REFUSED"),                       # provider refusal (response)
])
def test_mock_bad_provider_outputs_are_typed_technical_failures(tmp_path, monkeypatch, body, code):
    out = _live(tmp_path, monkeypatch, Provider(body), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["technical_failure"] and row["hybrid_code"] == code and not row["served"]


def test_request_cap_blocks_the_next_request_before_it_is_sent(tmp_path, monkeypatch):
    provider = Provider(default=httpx.ConnectError("mock: unreachable"))
    out = _live(tmp_path, monkeypatch, provider, max_requests=1)
    assert provider.calls == 1 and out["http_requests"] == 1
    assert out["stop_reason"] == "REQUEST_CAP" and out["completed"] is False
    assert out["summary"]["paired"]["unpaired_cases"] == ["C1"]               # stopped inside the first arm
    assert out["summary"]["paired"]["complete_pairs"] == 0
    from app.ai import gemini
    assert gemini.BUDGET is None                                                # the cap never leaks into production


def test_cost_ceiling_blocks_a_request_that_could_exceed_the_cap(tmp_path, monkeypatch):
    provider = Provider(_body(SERVED))
    out = _live(tmp_path, monkeypatch, provider, cases=[_one()], max_usd=0.01)   # Hybrid request ceiling ≈ 0.024
    assert provider.calls == 0 and out["stop_reason"] == "COST_CEILING" and out["http_requests"] <= 1


def test_the_ceiling_is_the_exact_payload_bound_per_request(tmp_path, monkeypatch):
    """A capped Hybrid request (8192 output) fits under USD 0.10; the real LLM_ONLY request (no output cap ⇒ 65 536,
    ≥ USD 0.164) does not, so it is blocked BEFORE `call_gemini` sends it."""
    async_calls = []

    async def never(self, url, *a, **k):
        async_calls.append(url)
        raise AssertionError("an over-ceiling LLM_ONLY request was sent")

    monkeypatch.setattr(httpx.AsyncClient, "post", never)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    provider = Provider(default=_body(SERVED))
    monkeypatch.setattr(httpx, "post", provider)
    corpus = _write(tmp_path, [_one()])
    out = E.evaluate(corpus, tmp_path / "live.json", _terms(corpus, max_usd=0.10), sleep=lambda s: None)
    assert provider.calls == 1 and async_calls == [] and out["stop_reason"] == "COST_CEILING"
    hybrid = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert hybrid["served_correct"] and hybrid["usd_upper"] < 0.10
    terms = _terms(corpus)
    assert E.request_ceiling_usd({"generationConfig": {"maxOutputTokens": 8192}}, terms) < 0.021
    assert E.request_ceiling_usd({"generationConfig": {}}, terms) >= 65536 * 2.50e-6


def test_infrastructure_streak_stops_the_run(tmp_path, monkeypatch):
    cases = [_one(f"L{i}", dict(SERVED, problem_text=SERVED["problem_text"] + " " * i)) for i in range(4)]

    async def broken(text, api_key):
        raise RuntimeError("mock: provider down")

    provider = Provider(default=500)
    corpus = _write(tmp_path, cases)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(E, "run_llm_only", broken)
    out = E.evaluate(corpus, tmp_path / "live.json", _terms(corpus), sleep=lambda s: None)
    assert out["stop_reason"] == "INFRASTRUCTURE_STREAK" and len(out["rows"]) == 3


def test_a_served_expected_refusal_stops_the_run(tmp_path, monkeypatch):
    out = _live(tmp_path, monkeypatch, Provider(default=_body(SERVED)),
                cases=[_one("R1", expect="REFUSE"), _one("L2", dict(SERVED, problem_text=SERVED["problem_text"] + " x"))])
    assert out["stop_reason"] == "SERVED_EXPECTED_REFUSAL" and [r["case_id"] for r in out["rows"]] == ["R1"]


def test_an_identity_change_mid_run_stops_before_the_next_request(tmp_path, monkeypatch):
    identities = iter([{"measured_system": "a"}, {"measured_system": "a"}, {"measured_system": "b"}])
    monkeypatch.setattr(E, "runtime_identity", lambda: next(identities))
    provider = Provider(default=_body(SERVED))
    cases = [_one(), _one("L2", dict(SERVED, problem_text=SERVED["problem_text"] + " x"))]
    out = _live(tmp_path, monkeypatch, provider, cases=cases)
    assert out["stop_reason"] == "IDENTITY_CHANGED" and provider.calls == 1


def test_the_real_llm_only_arm_is_held_by_the_same_request_cap(tmp_path, monkeypatch):
    """Production `run_pipeline` → `call_gemini` (not a fake): its HTTP attempts pass the same budget, so the cap holds
    across both arms. The mock provider answers 429 forever; nothing reaches the network (conftest guard)."""
    async_calls = []

    async def rate_limited(self, url, *a, **k):
        async_calls.append(url)
        return httpx.Response(429, json={"error": {"code": 429}}, request=httpx.Request("POST", url))

    import app.ai.gemini as gemini
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)
    monkeypatch.setattr(httpx.AsyncClient, "post", rate_limited)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", Provider(default=_body(SERVED)))
    corpus = _write(tmp_path, [_one()])
    out = E.evaluate(corpus, tmp_path / "live.json", _terms(corpus, max_requests=3), sleep=lambda s: None)
    llm = next(r for r in out["rows"] if r["arm"] == "LLM_ONLY")
    assert llm["technical_failure"] and not llm["served"]
    assert len(async_calls) == 2 and out["http_requests"] == 3                  # 1 Hybrid + 2 LLM_ONLY, then the cap
    assert out["stop_reason"] == "REQUEST_CAP"


def test_contamination_scan_finds_opened_text_whatever_the_escaping(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs/evaluation/run").mkdir(parents=True)
    (repo / "backend/tests").mkdir(parents=True)
    (repo / "frontend/src/data").mkdir(parents=True)
    opened = "Cho hình chóp S.ABC có SA = 3. Tính thể tích."
    (repo / "docs/evaluation/run/cases.json").write_text(json.dumps({"t": opened}, ensure_ascii=True), encoding="utf-8")
    corpus = {"cases": [{"id": "copied", "problem_text": "  cho HÌNH chóp S.ABC  có SA = 3. Tính thể tích.  "},
                        {"id": "fresh", "problem_text": "Cho lăng trụ đứng ABC.A'B'C' có AA' = 5."}]}
    assert E.contamination_scan(corpus, repo) == {"copied": ["docs/evaluation/run/cases.json"]}


def test_a_finished_run_is_never_overwritten(tmp_path):
    corpus = _corpus(tmp_path)
    E.evaluate(corpus, tmp_path / "rows.json", None)
    with pytest.raises(FileExistsError):
        E.evaluate(corpus, tmp_path / "rows.json", None)
