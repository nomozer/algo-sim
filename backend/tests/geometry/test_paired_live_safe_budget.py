# -*- coding: utf-8 -*-
"""C27 mandatory RED->GREEN tests for SafeCampaignBudget (exact Decimal, per-request reservation,
timeout/retry/partial-usage conservative settlement, concurrency safety, and campaign isolation)."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import threading

import httpx
import pytest

from scripts import run_paired_route_evaluation as E
from scripts import score_independent_holdout_equivalence as S
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

REPO = Path(__file__).resolve().parents[3]

SERVED_FIXTURE = _prism()


def _make_60_case_corpus(tmp_path: Path, name: str = "h1-60.json") -> Path:
    cases = []
    for i in range(45):
        p = deepcopy(SERVED_FIXTURE)
        p["problem_text"] = p["problem_text"].replace("AB = 6", f"AB = {6 + i}")
        cases.append({
            "id": f"H1-S{i + 1:02d}",
            "problem_text": p["problem_text"],
            "expect": "SERVE",
            "oracle": {"distance": ["12"]},
        })
    for idx, klass in enumerate(("OUT_OF_DOMAIN",) * 5 + ("CONTRADICTORY_DATA",) * 5 + ("MISSING_DATA",) * 5):
        cases.append({
            "id": f"H1-R{idx + 1:02d}",
            "problem_text": f"Đề kiểm định từ chối độc lập số {idx + 1} thuộc nhóm {klass}.",
            "expect": "REFUSE",
            "refusal_class": klass,
        })
    path = tmp_path / name
    path.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


def _make_1_case_corpus(tmp_path: Path, case_id: str | None = None, expect: str = "SERVE") -> Path:
    cid = case_id or next(f"H{i}" for i in range(100) if E.arm_order(f"H{i}")[0] == "HYBRID")
    c = {"id": cid, "problem_text": SERVED_FIXTURE["problem_text"], "expect": expect}
    if expect == "SERVE":
        c["oracle"] = {"distance": ["12"]}
    else:
        c["refusal_class"] = "CONTRADICTORY_DATA"
    path = tmp_path / f"{cid}.json"
    path.write_text(json.dumps({"cases": [c]}, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


def _approval_terms(corpus_path: Path, **overrides) -> dict:
    ident = E.runtime_identity()
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    base = {
        "corpus_sha256": E.sha256_file(corpus_path),
        "oracle_sha256": S.compute_oracle_sha256(corpus["cases"]),
        "paid_project_confirmed": True,
        "campaign_max_requests": 300,
        "max_requests": 300,
        "campaign_max_usd": 5.0,
        "max_usd": 5.0,
        "model": ident["model"],
        "measured_system": ident["measured_system"],
        "harness_sha256": ident["harness_sha256"],
        "input_usd_per_million": 0.30,
        "output_usd_per_million": 2.50,
        "llm_only_output_reservation_tokens": 65536,
        "corpus_author": "Independent Teacher",
        "authoring_independence": "ESTABLISHED",
        "evaluator_independence": "ESTABLISHED",
    }
    base.update(overrides)
    return base


def _ok_body(payload=SERVED_FIXTURE, *, usage: dict | None = None, omit_usage: bool = False) -> dict:
    body: dict = {
        "candidates": [{
            "content": {"parts": [{"text": json.dumps(payload, ensure_ascii=False)}]},
            "finishReason": "STOP",
        }],
    }
    if not omit_usage:
        body["usageMetadata"] = usage if usage is not None else {
            "promptTokenCount": 9000,
            "candidatesTokenCount": 700,
            "thoughtsTokenCount": 200,
            "totalTokenCount": 9900,
        }
    return body


class ScriptedProvider:
    def __init__(self, *steps, default=None):
        self.steps = list(steps)
        self.default = default
        self.calls = 0

    def __call__(self, url, **kwargs):
        self.calls += 1
        step = self.steps.pop(0) if self.steps else self.default
        if isinstance(step, BaseException):
            raise step
        req = httpx.Request("POST", url)
        if isinstance(step, int):
            return httpx.Response(step, json={"error": {"code": step}}, request=req)
        return httpx.Response(200, json=step, request=req)


# 1. Preflight accepts 5 USD when single request reservation fits, rejects when < 1 request worst case
def test_01_preflight_accepts_5_usd_campaign_budget_and_rejects_under_single_request_ceiling(tmp_path):
    corpus_path = _make_60_case_corpus(tmp_path)
    raw = corpus_path.read_bytes()

    checked = E.check_approval_terms(raw, _approval_terms(corpus_path, campaign_max_requests=300, max_requests=300,
                                                          campaign_max_usd=5.0, max_usd=5.0))
    assert checked["campaign_max_requests"] == 300
    assert Decimal(str(checked["campaign_max_usd"])) == Decimal("5.0")

    # 0.10 USD cannot cover 1 uncapped LLM_ONLY worst-case request (~0.169 USD) -> fail-closed at preflight
    with pytest.raises(E.LiveRefused, match="worst-case|ceiling|campaign_max_usd|max_usd"):
        E.check_approval_terms(raw, _approval_terms(corpus_path, campaign_max_usd=0.10, max_usd=0.10))

    # Mismatched alias fields (campaign_max_usd != max_usd) must fail closed
    with pytest.raises(E.LiveRefused):
        E.check_approval_terms(raw, _approval_terms(corpus_path, campaign_max_usd=5.0, max_usd=6.0))


# 2. Request cannot exceed remaining_usd (checked BEFORE wire send; stops with INCOMPLETE_PAIRED_EVALUATION)
def test_02_request_cannot_exceed_remaining_usd_and_marks_incomplete_paired_evaluation(tmp_path, monkeypatch):
    # 2 cases: Hybrid has 8192 output cap (~$0.0235 worst case); LLM_ONLY has 65536 (~$0.168 worst case).
    # Set campaign_max_usd = 0.25 and have Case 1 LLM_ONLY consume $0.16 in verified large output tokens,
    # leaving remaining_usd (~$0.085) < Case 2 LLM_ONLY request_worst_case_usd (~$0.168).
    c1 = deepcopy(SERVED_FIXTURE)
    c2 = deepcopy(SERVED_FIXTURE)
    c2["problem_text"] = c2["problem_text"].replace("AB = 6", "AB = 9")
    c2["premises"][1] = {**c2["premises"][1], "args": {"segment": ["A", "B"], "value": "9"}, "quote": "AB = 9"}
    cases = [
        {"id": "P1", "problem_text": c1["problem_text"], "expect": "SERVE", "oracle": {"distance": ["12"]}},
        {"id": "P2", "problem_text": c2["problem_text"], "expect": "SERVE", "oracle": {"distance": ["12"]}},
    ]
    corpus_path = tmp_path / "two.json"
    corpus_path.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8", newline="\n")

    provider = ScriptedProvider(_ok_body(c1), _ok_body(c2))
    async_sends = []

    async def fake_async_post(self, url, *args, **kwargs):
        async_sends.append(url)
        req = httpx.Request("POST", url)
        # First LLM_ONLY call returns large output costing 62000 * $2.50/1M + 10000 * $0.30/1M = $0.158
        return httpx.Response(200, json={
            "candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}],
            "usageMetadata": {
                "promptTokenCount": 10000,
                "candidatesTokenCount": 52000,
                "thoughtsTokenCount": 10000,
                "totalTokenCount": 72000,
            },
        }, request=req)

    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_async_post)

    terms = _approval_terms(corpus_path, campaign_max_usd=0.25, max_usd=0.25, campaign_max_requests=50, max_requests=50)
    out = E.evaluate(corpus_path, tmp_path / "out.jsonl", terms, sleep=lambda s: None)

    assert len(async_sends) == 1  # Second LLM_ONLY wire call was blocked BEFORE send!
    assert out["stop_reason"] == "COST_CEILING"
    assert out["completed"] is False
    assert out["run_status"] == "INCOMPLETE_PAIRED_EVALUATION"
    assert out["paired_live_evaluation_complete"] == "NO"
    assert out["acceptance"]["verdict"] == "HYBRID_CUTOVER_NO_GO"
    ledger = out["budget_ledger"]
    assert Decimal(ledger["spent_usd"]) <= Decimal("0.25")
    assert Decimal(ledger["inflight_reserved_usd"]) == Decimal("0")
    assert Decimal(ledger["remaining_usd"]) == Decimal("0.25") - Decimal(ledger["spent_usd"])


# 3. Missing or partial usageMetadata is charged conservatively at request_worst_case_usd
@pytest.mark.parametrize("bad_meta_kwargs", [
    {"omit_usage": True},
    {"usage": {}},
    {"usage": {"promptTokenCount": 9000}},  # missing candidatesTokenCount despite non-empty candidate text!
    {"usage": {"promptTokenCount": 0, "candidatesTokenCount": 0, "totalTokenCount": 0}},
])
def test_03_missing_or_partial_usage_is_charged_at_full_request_reservation(tmp_path, monkeypatch, bad_meta_kwargs):
    corpus_path = _make_1_case_corpus(tmp_path)
    provider = ScriptedProvider(_ok_body(SERVED_FIXTURE, **bad_meta_kwargs))
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(E, "run_llm_only",
                        lambda text, key: asyncio.sleep(0, result={"status": "unsupported",
                                                                   "failure_category": "geometry_generation_failed"}))

    terms = _approval_terms(corpus_path, campaign_max_usd=5.0, max_usd=5.0)
    out = E.evaluate(corpus_path, tmp_path / "out.jsonl", terms, sleep=lambda s: None)
    hybrid_row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    # Hybrid request has maxOutputTokens=8192 -> worst-case > $0.020 (far above actual ~$0.00445 or $0.0)
    assert hybrid_row["usd_upper"] > 0.020
    assert out["budget_ledger"]["unverified_requests_charged_at_ceiling"] == 1
    assert Decimal(out["budget_ledger"]["spent_usd"]) > Decimal("0.020")


# 4. HTTP timeout does NOT release reservation back to remaining_usd; settles at worst-case ceiling
def test_04_http_timeout_settles_at_worst_case_and_never_refunds_reservation(tmp_path):
    corpus_path = _make_1_case_corpus(tmp_path)
    terms = _approval_terms(corpus_path, campaign_max_usd=1.0, max_usd=1.0, campaign_max_requests=10, max_requests=10)
    budget = E.SafeCampaignBudget(terms)
    payload = {"contents": [{"parts": [{"text": "hello"}]}], "generationConfig": {"maxOutputTokens": 8192}}
    req_worst = E.request_worst_case_usd_decimal(payload, terms)
    assert req_worst > Decimal("0.020")

    ticket = budget.begin_send(payload)
    assert budget.inflight_reserved_usd == req_worst
    assert budget.remaining_usd == Decimal("1.0") - req_worst

    # Simulate timeout during HTTP call -> response is None
    budget.finish_send(ticket, response=None, error="ReadTimeout")
    assert budget.inflight_reserved_usd == Decimal("0")
    assert budget.spent_usd == req_worst
    assert budget.remaining_usd == Decimal("1.0") - req_worst


# 5. Retries count every request and charge every unverified retry plus verified final response
def test_05_retries_count_all_requests_and_charge_each_attempt(tmp_path, monkeypatch):
    corpus_path = _make_1_case_corpus(tmp_path)
    provider = ScriptedProvider(429, httpx.ReadTimeout("timeout"), 503, _ok_body(SERVED_FIXTURE))
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(E, "run_llm_only",
                        lambda text, key: asyncio.sleep(0, result={"status": "unsupported",
                                                                   "failure_category": "geometry_generation_failed"}))

    terms = _approval_terms(corpus_path)
    out = E.evaluate(corpus_path, tmp_path / "retry.jsonl", terms, sleep=lambda s: None)
    hybrid_row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert hybrid_row["served_correct"] is True
    assert hybrid_row["http_requests"] == 4
    assert out["budget_ledger"]["actual_http_request_count"] == 4
    assert out["budget_ledger"]["retries"] == 3
    assert out["budget_ledger"]["unverified_requests_charged_at_ceiling"] == 3
    # 3 failed attempts at >$0.020 each + 1 verified success (~$0.005) > $0.064
    assert hybrid_row["usd_upper"] > 0.064


# 6. HTTP 400 / 429 / 500 error responses are recorded and conservatively charged in ledger
@pytest.mark.parametrize("status_code,expected_attempts", [(400, 1), (429, 4), (500, 4)])
def test_06_http_error_statuses_400_429_500_recorded_and_charged_conservatively(
    tmp_path, monkeypatch, status_code, expected_attempts
):
    corpus_path = _make_1_case_corpus(tmp_path)
    provider = ScriptedProvider(default=status_code)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(E, "run_llm_only",
                        lambda text, key: asyncio.sleep(0, result={"status": "unsupported",
                                                                   "failure_category": "geometry_generation_failed"}))

    out = E.evaluate(corpus_path, tmp_path / f"err-{status_code}.jsonl", _approval_terms(corpus_path),
                     sleep=lambda s: None)
    ledger = out["budget_ledger"]
    assert ledger["actual_http_request_count"] == expected_attempts
    assert ledger["unverified_requests_charged_at_ceiling"] == expected_attempts
    assert [e["http_status"] for e in ledger["entries"]] == [status_code] * expected_attempts
    assert all(Decimal(e["settled_usd"]) == Decimal(e["request_worst_case_usd"]) for e in ledger["entries"])


# 7. Concurrent reservations (threads + asyncio) never overspend campaign_max_usd or exceed campaign_max_requests
def test_07_concurrent_reservations_never_overspend_or_exceed_request_cap(tmp_path):
    from app.ai import gemini

    corpus_path = _make_1_case_corpus(tmp_path)
    # Part A: USD-constrained concurrency: campaign_max_usd = 0.50, each request worst-case ~0.164 -> at most 3 fit!
    terms_usd = _approval_terms(corpus_path, campaign_max_usd=0.50, max_usd=0.50,
                                campaign_max_requests=100, max_requests=100)
    budget_usd = E.SafeCampaignBudget(terms_usd)
    uncapped_payload = {"contents": [{"parts": [{"text": "concurrent test"}]}], "generationConfig": {}}
    barrier = threading.Barrier(16)
    admitted_usd = []
    lock = threading.Lock()

    def worker_usd():
        barrier.wait()
        try:
            ticket = budget_usd.begin_send(uncapped_payload)
        except gemini.BudgetExceeded:
            return False
        try:
            with lock:
                admitted_usd.append(budget_usd.spent_usd + budget_usd.inflight_reserved_usd)
                assert admitted_usd[-1] <= Decimal("0.50")
        finally:
            budget_usd.finish_send(ticket, response=None, error="SimulatedTimeout")
        return True

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: worker_usd(), range(16)))
    assert sum(results) == 3  # 3 * ~0.16407 = ~0.4922 <= 0.50; 4th would be ~0.656 > 0.50
    assert budget_usd.spent_usd <= Decimal("0.50")
    assert budget_usd.inflight_reserved_usd == Decimal("0")

    # Part B: Request-cap-constrained async concurrency: campaign_max_requests = 7, 25 coroutines racing
    terms_req = _approval_terms(corpus_path, campaign_max_usd=5.0, max_usd=5.0,
                                campaign_max_requests=7, max_requests=7)
    budget_req = E.SafeCampaignBudget(terms_req)

    async def async_worker():
        try:
            ticket = budget_req.begin_send({"generationConfig": {"maxOutputTokens": 8192}})
        except gemini.BudgetExceeded:
            return False
        await asyncio.sleep(0.005)
        budget_req.finish_send(ticket, response=None, error="SimulatedTimeout")
        return True

    async def run_all():
        return await asyncio.gather(*(async_worker() for _ in range(25)))

    res_req = asyncio.run(run_all())
    assert sum(res_req) == 7
    assert budget_req.actual_http_request_count == 7
    assert budget_req.inflight_request_count == 0


# 8. Exact Decimal arithmetic prevents IEEE-754 floating-point rounding overshoot
def test_08_exact_decimal_arithmetic_prevents_float_rounding_overshoot(tmp_path):
    from app.ai import gemini

    corpus_path = _make_1_case_corpus(tmp_path)
    payload = {"generationConfig": {"maxOutputTokens": 1000}}
    terms = _approval_terms(corpus_path, input_usd_per_million=1.0, output_usd_per_million=100.0,
                            campaign_max_usd=1.0, max_usd=1.0)
    one_cost = E.request_worst_case_usd_decimal(payload, terms)
    assert isinstance(one_cost, Decimal)

    # Set campaign_max_usd to 3 * one_cost - 1e-12 (in IEEE-754 float, small epsilons vanish or round unpredictably)
    tight_cap = one_cost * 3 - Decimal("0.000000000001")
    terms_tight = {**terms, "campaign_max_usd": str(tight_cap), "max_usd": float(tight_cap)}
    # Bind exact Decimal cap via string/Decimal-preserving SafeCampaignBudget
    budget = E.SafeCampaignBudget({**terms_tight, "campaign_max_usd": tight_cap})
    for _ in range(2):
        t = budget.begin_send(payload)
        budget.finish_send(t, response=None, error="Timeout")
    with pytest.raises(gemini.BudgetExceeded):
        budget.begin_send(payload)


# 9. Consumed approval cannot be reused
def test_09_consumed_approval_cannot_be_reused(tmp_path):
    approval_file = tmp_path / "owner-approval.json"
    approval_file.write_text('{"owner_decision": "PENDING_OWNER_DECISION"}\n', encoding="utf-8")
    out1 = tmp_path / "run1.jsonl"
    out2 = tmp_path / "run2.jsonl"
    E.claim_approval(approval_file, out1)
    with pytest.raises(E.LiveRefused, match="already consumed"):
        E.claim_approval(approval_file, out2)


# 10. C21 and C26 campaign ledgers remain byte-identical and isolated from H-1 budget
def test_10_c21_and_c26_ledgers_are_immutable_and_isolated_from_h1_campaign(tmp_path, monkeypatch):
    immutable_files = [
        REPO / "docs/evaluation/geometry/runs/hybrid-live-validation/live-pilots-8853c4b0/c21-global-budget-ledger.json",
        REPO / "docs/evaluation/geometry/runs/hybrid-live-validation/live-pilots-8853c4b0/c21-delegated-execution-receipt.json",
        REPO / "docs/evaluation/geometry/runs/hybrid-live-extraction-retest/full/c26-global-budget-ledger.json",
        REPO / "docs/evaluation/geometry/runs/hybrid-live-extraction-retest/full/c21-delegated-execution-receipt.json",
        REPO / "docs/evaluation/geometry/runs/hybrid-live-extraction-retest/full/k1-live.jsonl",
        REPO / "docs/evaluation/geometry/runs/hybrid-live-extraction-retest/full/s2-live.jsonl",
        REPO / "docs/evaluation/geometry/runs/hybrid-live-extraction-retest/full/r1-live.jsonl",
    ]
    before = {p: E.sha256_file(p) for p in immutable_files}

    corpus_path = _make_1_case_corpus(tmp_path)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", ScriptedProvider(_ok_body(SERVED_FIXTURE)))
    monkeypatch.setattr(E, "run_llm_only",
                        lambda text, key: asyncio.sleep(0, result={"status": "unsupported",
                                                                   "failure_category": "geometry_generation_failed"}))
    out = E.evaluate(corpus_path, tmp_path / "h1.jsonl", _approval_terms(corpus_path), sleep=lambda s: None)
    assert out["budget_ledger"]["campaign_isolated"] is True
    assert {p: E.sha256_file(p) for p in immutable_files} == before


# 11. All stop mechanisms work and mark incomplete runs NO-GO / INCOMPLETE_PAIRED_EVALUATION
def test_11_usd_80_percent_and_stop_rules_mark_incomplete_and_block_go(tmp_path, monkeypatch):
    c1 = deepcopy(SERVED_FIXTURE)
    c2 = deepcopy(SERVED_FIXTURE)
    c2["problem_text"] = c2["problem_text"].replace("AB = 6", "AB = 10")
    corpus_path = tmp_path / "two80.json"
    corpus_path.write_text(json.dumps({"cases": [
        {"id": "S1", "problem_text": c1["problem_text"], "expect": "SERVE", "oracle": {"distance": ["12"]}},
        {"id": "S2", "problem_text": c2["problem_text"], "expect": "SERVE", "oracle": {"distance": ["12"]}},
    ]}, ensure_ascii=False), encoding="utf-8", newline="\n")

    # Make Hybrid return huge verified output costing > 80% of $0.20 ($0.165 >= $0.16) on S1 so USD_80_PERCENT fires!
    big_usage = {"promptTokenCount": 10000, "candidatesTokenCount": 60000, "thoughtsTokenCount": 5000,
                 "totalTokenCount": 75000}
    provider = ScriptedProvider(_ok_body(c1, usage=big_usage), _ok_body(c2))
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(E, "run_llm_only",
                        lambda text, key: asyncio.sleep(0, result={"status": "unsupported",
                                                                   "failure_category": "geometry_generation_failed"}))

    out = E.evaluate(corpus_path, tmp_path / "stop80.jsonl",
                     _approval_terms(corpus_path, campaign_max_usd=0.20, max_usd=0.20), sleep=lambda s: None)
    assert out["stop_reason"] == "USD_80_PERCENT"
    assert out["completed"] is False
    assert out["run_status"] == "INCOMPLETE_PAIRED_EVALUATION"
    assert out["paired_live_evaluation_complete"] == "NO"
    assert out["acceptance"]["verdict"] == "HYBRID_CUTOVER_NO_GO"


# 12. Provider calls never occur if approval is unapproved, paid_project_confirmed is False, or oracle_sha256 mismatches
def test_12_zero_provider_calls_when_approval_invalid_or_paid_unconfirmed(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("HTTP post called on invalid approval"))
    monkeypatch.setattr(httpx.AsyncClient, "post", lambda *a, **k: pytest.fail("Async HTTP post called"))
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")

    corpus_path = _make_1_case_corpus(tmp_path)
    for bad_override, pattern in (
        ({"paid_project_confirmed": False}, "paid_project_confirmed"),
        ({"oracle_sha256": "f" * 64}, "oracle_sha256"),
        ({"input_usd_per_million": 0.01}, "input_usd_per_million|verified"),
    ):
        bad_file = tmp_path / "bad-approval.json"
        bad_file.write_text(json.dumps({**_approval_terms(corpus_path, max_requests=5, campaign_max_requests=5,
                                                          **bad_override),
                                        "owner_decision": "PENDING_OWNER_DECISION"}), encoding="utf-8")
        with pytest.raises(E.LiveRefused, match="APPROVED_BY_USER"):
            E.authorize_live(corpus_path, bad_file)
        with pytest.raises(E.LiveRefused, match=pattern):
            E.check_approval_terms(corpus_path.read_bytes(),
                                   _approval_terms(corpus_path, max_requests=5, campaign_max_requests=5, **bad_override))


# 13. Zero fallback to LLM_ONLY when Hybrid fails or refuses
def test_13_no_fallback_to_llm_only_when_hybrid_fails(tmp_path, monkeypatch):
    llm_invocations = []

    async def spy_llm_only(text, api_key):
        llm_invocations.append(text)
        return {"status": "unsupported", "failure_category": "geometry_generation_failed"}

    monkeypatch.setattr(E, "run_llm_only", spy_llm_only)
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    # Direct Hybrid execution on empty/failing extraction never calls LLM_ONLY
    env, extra = E.run_hybrid(SERVED_FIXTURE["problem_text"], ReplayExtractor({}))
    assert env["status"] != "ok"
    assert llm_invocations == []


# 14. Request cap is enforced BEFORE sending the HTTP request on the wire
def test_14_campaign_max_requests_enforced_before_http_send(tmp_path, monkeypatch):
    corpus_path = _make_1_case_corpus(tmp_path)
    provider = ScriptedProvider(default=503)  # transient -> tries up to 4 times unless capped first
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    monkeypatch.setattr(httpx, "post", provider)
    monkeypatch.setattr(E, "run_llm_only",
                        lambda text, key: asyncio.sleep(0, result={"status": "unsupported",
                                                                   "failure_category": "geometry_generation_failed"}))

    terms = _approval_terms(corpus_path, campaign_max_requests=2, max_requests=2)
    out = E.evaluate(corpus_path, tmp_path / "cap2.jsonl", terms, sleep=lambda s: None)
    assert provider.calls == 2
    assert out["http_requests"] == 2
    assert out["budget_ledger"]["actual_http_request_count"] == 2
    assert out["stop_reason"] == "REQUEST_CAP"
    assert out["run_status"] == "INCOMPLETE_PAIRED_EVALUATION"


# 15. C28 §VII–§IX: Scene3D boundary audit, planner composition provenance, clarification & 2x2 paired matrix
def test_15_c28_scene3d_boundary_planner_provenance_and_paired_matrix(tmp_path):
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    hybrid_env, _ = E.run_hybrid(
        SERVED_FIXTURE["problem_text"],
        ReplayExtractor({SERVED_FIXTURE["problem_text"]: SERVED_FIXTURE}),
    )
    assert hybrid_env["status"] == "ok"

    corpus = {
        "schema": "hybrid-master-paired-heldout/2",
        "cases": [
            {
                "id": "C28-POS-1",
                "problem_text": SERVED_FIXTURE["problem_text"],
                "expect": "SERVE",
                "oracle": {"distance": ["12"]},
                "semantic_annotations": {"explicit_goals": ["distance"]},
                "dry_run": {
                    "hybrid_extraction": SERVED_FIXTURE,
                    "llm_only_envelope": hybrid_env,
                },
            },
            {
                "id": "C28-NEG-1",
                "problem_text": "Giải phương trình bậc hai x^2 - 5x + 6 = 0.",
                "expect": "REFUSE",
                "refusal_class": "OUT_OF_DOMAIN",
                "dry_run": {
                    "hybrid_extraction": None,
                    "llm_only_envelope": {"status": "unsupported", "failure_category": "out_of_scope", "error_code": "OUT_OF_SCOPE"},
                },
            },
        ],
    }
    cpath = tmp_path / "c28-dry.json"
    cpath.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    out = E.evaluate(cpath, tmp_path / "c28-out.jsonl", approval=None)

    by = {(r["case_id"], r["arm"]): r for r in out["rows"]}
    h_pos = by[("C28-POS-1", "HYBRID")]
    l_pos = by[("C28-POS-1", "LLM_ONLY")]
    assert h_pos["served_correct"] is True
    assert h_pos["planner_composition"] in ("REGISTERED_DECOMPOSITION", "SOURCE_EXPLICIT_SEQUENCE", "DISCOVERED_FUNCTION_COMPOSITION")
    assert h_pos["clarification_requested"] is False
    assert h_pos["semantic_goal_correct"] is True
    assert h_pos["strict_contract_correct"] is True

    for row in (h_pos, l_pos):
        sc = row["scene_contract"]
        assert sc["envelope_valid"] is True
        assert sc["object_identity_unique"] is True
        assert sc["dependency_order_valid"] is True
        assert sc["explanation_certificate_linked"] is True
        assert sc["target_quantity_mapped"] is True

    paired = out["summary"]["paired"]
    assert paired["both_correct"] == 1
    assert paired["both_incorrect"] == 0
    assert paired["served_correct_diff"] == 0.0
    assert out["summary"]["HYBRID"]["scene_contract_all_valid"] == 1
    assert out["summary"]["HYBRID"]["pedagogical_human_validation"] == "NOT_EVALUATED_BY_H1_AUTOMATED_HARNESS"
