"""C26 §V — the live Hybrid product route's REAL timeout configuration (0 provider calls).

Live Run 3 saw a valid Gemini 2.5 Flash response at 20.86 s. These tests pin what `/api/analyze` actually applies in
`HYBRID_ROUTE_MODE=live` (env > defaults: `HYBRID_LIVE_TIMEOUT_SECONDS` = 60 s per attempt, `HYBRID_LIVE_DEADLINE_SECONDS`
= 3 × per attempt) and that a slow valid answer is not cut while a hung request still times out, with no fallback.
"""
import httpx
import pytest

from app.ai import gemini
from app.ai import hybrid_offline as H
from tests.test_hybrid_product_integration import (  # noqa: F401 — autouse DB isolation + the shared live fixture
    SECRET_KEY, _gemini_ok_body, _post, isolated_sqlite_db, staging_env,
)

OBSERVED_MAX_VALID_LATENCY_S = 20.863          # live-pilots-8853c4b0, case K-B02


def _live(monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")


@pytest.mark.parametrize("env,expected", [
    ({}, (60.0, 180.0)),
    ({"HYBRID_LIVE_TIMEOUT_SECONDS": "25"}, (25.0, 75.0)),
    ({"HYBRID_LIVE_TIMEOUT_SECONDS": "40", "HYBRID_LIVE_DEADLINE_SECONDS": "90"}, (40.0, 90.0)),
    ({"HYBRID_LIVE_TIMEOUT_SECONDS": "abc", "HYBRID_LIVE_DEADLINE_SECONDS": "-1"}, (60.0, 180.0)),
])
def test_product_route_applies_env_over_defaults(staging_env, monkeypatch, env, expected):
    prism, _, _ = staging_env
    _live(monkeypatch)
    for k in ("HYBRID_LIVE_TIMEOUT_SECONDS", "HYBRID_LIVE_DEADLINE_SECONDS"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    seen = []

    def fake(api_key, model=None, timeout_seconds=60.0, *, deadline_seconds=None, **_kw):
        seen.append((timeout_seconds, deadline_seconds))
        return lambda _req: _gemini_ok_body(prism)

    monkeypatch.setattr(H, "_live_provider_transport", fake)
    assert _post(prism["problem_text"]).status_code == 200
    assert seen == [expected]
    assert min(expected) > OBSERVED_MAX_VALID_LATENCY_S   # defaults never cut the slowest valid answer seen live


class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.mark.parametrize("deadline_env,status", [(None, 200), ("15", 504)])
def test_a_slow_valid_answer_is_served_unless_the_operator_sets_a_shorter_deadline(staging_env, monkeypatch,
                                                                                    deadline_env, status):
    prism, _, _ = staging_env
    _live(monkeypatch)
    monkeypatch.delenv("HYBRID_LIVE_TIMEOUT_SECONDS", raising=False)
    if deadline_env is None:
        monkeypatch.delenv("HYBRID_LIVE_DEADLINE_SECONDS", raising=False)
    else:
        monkeypatch.setenv("HYBRID_LIVE_DEADLINE_SECONDS", deadline_env)
    clock = _Clock()
    monkeypatch.setattr(H, "perf_counter", clock)
    calls = []

    def fake(api_key, model=None, timeout_seconds=60.0, *, deadline_seconds=None, **_kw):
        def send(_req):
            calls.append(1)
            clock.t += OBSERVED_MAX_VALID_LATENCY_S          # the provider answers validly after 20.86 s
            return _gemini_ok_body(prism)
        return send

    monkeypatch.setattr(H, "_live_provider_transport", fake)
    res = _post(prism["problem_text"])
    assert res.status_code == status and len(calls) == 1      # exactly one request either way
    if status == 504:
        assert res.json()["reason_code"] == "HYBRID_DEADLINE_EXCEEDED"
        assert res.json()["failure_kind"] == "INFRASTRUCTURE_FAILURE" and "route_d" not in res.json()
    else:
        assert res.json()["route_d"]["status"] == "SERVED"
    assert SECRET_KEY not in res.text


def test_a_hung_provider_times_out_per_attempt_within_the_retry_cap(monkeypatch):
    sent = []

    def fake_live_transport(api_key, model=None, timeout_seconds=60.0):
        def send_once(request, *, is_retry=False, timeout_override=None):
            sent.append((is_retry, timeout_override))
            raise httpx.ReadTimeout("hung")
        return send_once

    monkeypatch.setattr("app.ai.function_calling.live_transport", fake_live_transport)
    send = H._live_provider_transport(SECRET_KEY, model="gemini-2.5-flash", timeout_seconds=60.0,
                                      deadline_seconds=180.0, sleep=lambda _s: None)
    with pytest.raises(H.HybridTransportTimeout):
        send({"contents": []})
    assert 1 <= len(sent) <= gemini.MAX_ATTEMPTS
    assert all(t is not None and t <= 60.0 for _r, t in sent)
    assert [r for r, _t in sent] == [False] + [True] * (len(sent) - 1)
