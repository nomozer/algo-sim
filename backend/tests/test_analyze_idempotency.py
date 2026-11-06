"""`POST /api/analyze` idempotency (`app/idempotency.py`): one attempt key = at most one pipeline execution.

The pipeline is replaced by a counting fake AFTER the trial gate (`_analyze_hybrid_route`), so the real gate, the real
telemetry middleware and the real trial charge stay on the path; 0 provider calls.
"""
from __future__ import annotations

import asyncio
import logging
import threading

import pytest
from fastapi.responses import JSONResponse

from app import idempotency as idem
from tests.conftest_classroom import api  # noqa: F401

TEXT = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2. Tính thể tích khối chóp."
BODY = {"input": {"type": "text", "content": TEXT}}
K1, K2 = "a" + "1" * 32, "a" + "2" * 32


@pytest.fixture(autouse=True)
def _clean_table():
    idem._entries.clear()
    yield
    idem._entries.clear()


@pytest.fixture
def pipeline(api, monkeypatch):  # noqa: F811
    """Counting fake of the Hybrid route. The guest trial / daily quota of a SERVED result is charged around it by
    the usage ledger (`main._analyze_counted`), exactly as for the real route."""
    import app.main as main_mod

    state = {"calls": 0, "status": 200, "delay": 0.0}

    async def fake(text, mode, api_key, algosim_session):
        state["calls"] += 1
        n = state["calls"]
        if state["delay"]:
            await asyncio.sleep(state["delay"])
        if state["status"] != 200:
            return JSONResponse(status_code=state["status"], content={"error": "x", "reason_code": "PROVIDER_UNAVAILABLE",
                                                                       "failure_kind": "INFRASTRUCTURE_FAILURE"})
        return JSONResponse(content={"route_d": {"status": "SERVED"}, "execution": n},
                            headers={"Cache-Control": "no-store", "X-Algosim-Cache": "none"})

    monkeypatch.setattr(main_mod, "_analyze_hybrid_route", fake)
    api.get("/api/auth/me")
    return state


def _post(client, key=None, body=BODY):
    return client.post("/api/analyze", json=body, headers={idem.HEADER: key} if key else {})


def _trials_left(client):
    return client.get("/api/auth/me").json()["entitlement"]["trialsLeft"]


def test_one_submit_runs_once(api, pipeline):  # noqa: F811
    r = _post(api, K1)
    assert r.status_code == 200 and r.json()["execution"] == 1 and pipeline["calls"] == 1
    assert "idempotent-replayed" not in r.headers


def test_two_independent_submits_of_the_same_text_are_two_attempts(api, pipeline, monkeypatch):  # noqa: F811
    import app.accounts.policy as pol
    monkeypatch.setattr(pol, "GUEST_TRIAL_LIMIT", 5, raising=False)
    a, b = _post(api, K1), _post(api, K2)
    assert (a.json()["execution"], b.json()["execution"]) == (1, 2) and pipeline["calls"] == 2


def test_retry_after_lost_response_replays_and_does_not_charge_a_second_trial(api, pipeline):  # noqa: F811
    before = _trials_left(api)
    first = _post(api, K1)                    # the server finished; pretend the client never saw it
    retry = _post(api, K1)
    assert pipeline["calls"] == 1
    assert retry.status_code == 200 and retry.content == first.content
    assert retry.headers["idempotent-replayed"] == "true"
    assert retry.headers["x-algosim-cache"] == first.headers["x-algosim-cache"]
    assert _trials_left(api) == before - 1


def test_replay_is_served_even_after_the_trial_gate_would_now_close(api, pipeline):  # noqa: F811
    """The original consumed the last guest trial; its own retry must get its result, not 402."""
    first = _post(api, K1)
    assert _trials_left(api) == 0
    assert _post(api, K1).content == first.content
    assert _post(api, K2).status_code == 402          # a NEW attempt is still gated


def test_same_key_different_payload_is_a_conflict_and_runs_nothing(api, pipeline):  # noqa: F811
    _post(api, K1)
    other = {"input": {"type": "text", "content": TEXT + " Tính diện tích đáy."}}
    r = _post(api, K1, other)
    assert r.status_code == 409 and r.json()["reason_code"] == "IDEMPOTENCY_KEY_REUSED"
    assert pipeline["calls"] == 1
    assert TEXT not in r.text


def test_backend_error_is_never_replayed_and_a_retry_runs_again(api, pipeline):  # noqa: F811
    pipeline["status"] = 503
    assert _post(api, K1).status_code == 503
    pipeline["status"] = 200
    r = _post(api, K1)
    assert r.status_code == 200 and r.json()["execution"] == 2 and "idempotent-replayed" not in r.headers


def test_invalid_key_is_rejected_and_no_key_keeps_legacy_behaviour(api, pipeline):  # noqa: F811
    r = _post(api, "short")
    assert r.status_code == 400 and r.json()["reason_code"] == "IDEMPOTENCY_KEY_INVALID" and pipeline["calls"] == 0
    _post(api)
    assert pipeline["calls"] == 1 and not idem._entries


def test_another_session_with_the_same_key_never_sees_the_replay(api, pipeline):  # noqa: F811
    from tests.conftest_classroom import new_client

    _post(api, K1)
    other = new_client(api)
    other.get("/api/auth/me")
    r = _post(other, K1)
    assert r.json()["execution"] == 2 and "idempotent-replayed" not in r.headers


def test_completed_entry_expires(api, pipeline, monkeypatch):  # noqa: F811
    import app.accounts.policy as pol
    monkeypatch.setattr(pol, "GUEST_TRIAL_LIMIT", 5, raising=False)
    now = [1000.0]
    monkeypatch.setattr(idem.time, "monotonic", lambda: now[0])
    _post(api, K1)
    now[0] += idem.TTL_S + 1
    assert _post(api, K1).json()["execution"] == 2


def test_concurrent_same_key_requests_execute_once(api, pipeline):  # noqa: F811
    """Two real HTTP requests overlapping on the server's event loop (TestClient shares one loop across threads)."""
    pipeline["delay"] = 0.4
    out: list = [None, None]

    def go(i):
        out[i] = _post(api, K1)

    ts = [threading.Thread(target=go, args=(i,)) for i in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert pipeline["calls"] == 1
    assert out[0].content == out[1].content and out[0].status_code == out[1].status_code == 200
    assert sorted(o.headers.get("idempotent-replayed", "") for o in out) == ["", "true"]


def test_no_problem_text_in_logs(api, pipeline, caplog):  # noqa: F811
    with caplog.at_level(logging.DEBUG):
        _post(api, K1)
        _post(api, K1)
        _post(api, K1, {"input": {"type": "text", "content": TEXT + " khác"}})
    assert TEXT not in caplog.text and K1 not in caplog.text


# ── run_once in isolation: the in-progress / timeout / cancellation states, deterministic ──

def _ok(n):
    return JSONResponse(content={"n": n})


def test_retry_while_in_progress_waits_for_the_original():
    async def main():
        gate, calls = asyncio.Event(), []

        async def execute():
            calls.append(1)
            await gate.wait()
            return _ok(len(calls))

        first = asyncio.create_task(idem.run_once(K1, "s", "p", execute))
        await asyncio.sleep(0)
        retry = asyncio.create_task(idem.run_once(K1, "s", "p", execute))
        await asyncio.sleep(0)
        assert not retry.done()
        gate.set()
        a, b = await first, await retry
        return calls, a, b

    calls, a, b = asyncio.run(main())
    assert calls == [1] and a.body == b.body and b.headers["idempotent-replayed"] == "true"


def test_in_progress_wait_times_out_with_retry_after(monkeypatch):
    monkeypatch.setattr(idem, "WAIT_S", 0.05)

    async def main():
        gate = asyncio.Event()

        async def execute():
            await gate.wait()
            return _ok(1)

        first = asyncio.create_task(idem.run_once(K1, "s", "p", execute))
        await asyncio.sleep(0)
        try:      # bounded: without the guard this call would block on the gate instead of timing out
            return await asyncio.wait_for(idem.run_once(K1, "s", "p", execute), 2)
        finally:
            gate.set()
            await first

    r = asyncio.run(main())
    assert r.status_code == 409 and b"IDEMPOTENCY_REQUEST_IN_PROGRESS" in r.body and r.headers["retry-after"] == "5"


def test_cancelled_original_is_forgotten_and_a_waiter_runs_it_once():
    async def main():
        calls = []

        async def slow():
            calls.append("slow")
            await asyncio.sleep(10)
            return _ok(0)

        async def fast():
            calls.append("fast")
            return _ok(1)

        first = asyncio.create_task(idem.run_once(K1, "s", "p", slow))
        await asyncio.sleep(0)
        waiters = [asyncio.create_task(idem.run_once(K1, "s", "p", fast)) for _ in range(2)]
        await asyncio.sleep(0)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        rs = [await w for w in waiters]
        return calls, rs

    calls, rs = asyncio.run(main())
    assert calls == ["slow", "fast"]            # the two waiters coalesce into ONE fresh execution
    assert rs[0].body == rs[1].body


def test_table_is_bounded(monkeypatch):
    monkeypatch.setattr(idem, "MAX_ENTRIES", 3)

    async def main():
        for i in range(6):
            await idem.run_once(f"a{i:032d}", "s", "p", lambda i=i: asyncio.sleep(0, _ok(i)))

    asyncio.run(main())
    assert len(idem._entries) <= 4


# ── operational telemetry middleware (app/main.py) on the same path ──

def _telemetry_rows_and_used_today(main_mod):
    from sqlalchemy import func, select

    from app.persistence.classroom_models import AdminAnalysisTelemetry, UserAccountMeta

    with main_mod.SessionLocal() as s:
        n = s.execute(select(func.count()).select_from(AdminAnalysisTelemetry)).scalar_one()
        used = s.execute(select(func.coalesce(func.sum(UserAccountMeta.used_today), 0))).scalar_one()
    return n, used


def test_a_replayed_attempt_is_not_counted_twice_in_telemetry_or_daily_quota(api, pipeline):  # noqa: F811
    import app.main as main_mod
    from tests.conftest_classroom import register

    assert register(api, email="idem@algosim.edu.vn", name="Idem").status_code == 200
    _post(api, K1)
    assert _post(api, K1).headers["idempotent-replayed"] == "true"
    assert _telemetry_rows_and_used_today(main_mod) == (1, 1)
    _post(api, K2)                                          # a new attempt IS counted
    assert _telemetry_rows_and_used_today(main_mod) == (2, 2)


def test_middleware_passes_body_and_every_header_through(api, monkeypatch):  # noqa: F811
    import app.main as main_mod

    async def fake(text, mode, api_key, s):
        r = JSONResponse(content={"route_d": {"status": "REFUSED"}, "k": "ữ" * 50}, headers={"X-Algosim-Cache": "none"})
        r.raw_headers.append((b"vary", b"Cookie"))
        r.raw_headers.append((b"vary", b"Origin"))
        return r

    monkeypatch.setattr(main_mod, "_analyze_hybrid_route", fake)
    api.get("/api/auth/me")                  # a guest session, as the app opens one on first load
    r = _post(api)
    assert r.json() == {"route_d": {"status": "REFUSED"}, "k": "ữ" * 50}
    assert r.headers.get_list("vary") == ["Cookie", "Origin"]
    assert r.headers["content-type"] == "application/json" and r.headers["x-algosim-cache"] == "none"
    assert int(r.headers["content-length"]) == len(r.content)


def test_shipped_deployment_runs_one_server_process():
    """`app/idempotency.py` is an in-process table: its at-most-once guarantee holds only with ONE server process.
    Lock that assumption on the shipped configuration — adding workers/replicas must come with the DB-backed variant."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    cmd = next(line for line in (root / "backend" / "Dockerfile").read_text(encoding="utf-8").splitlines() if line.startswith("CMD"))
    assert "uvicorn app.main:app" in cmd and "gunicorn" not in cmd
    assert not re.search(r"--workers|WEB_CONCURRENCY", cmd), cmd
    for compose in root.glob("docker-compose*.yml"):
        body = compose.read_text(encoding="utf-8")
        assert not re.search(r"^\s*replicas:|WEB_CONCURRENCY|--workers", body, re.MULTILINE), compose.name


def test_overlapping_analyses_are_charged_only_their_own_tokens(api, monkeypatch):  # noqa: F811
    """Telemetry tokens are per request, not a process-wide before/after delta (two overlapping requests used to
    be charged each other's tokens: totals double-counted)."""
    import time

    from sqlalchemy import select
    from starlette.concurrency import run_in_threadpool

    import app.main as main_mod
    from app.ai.telemetry import record_usage
    from app.persistence.classroom_models import AdminAnalysisTelemetry
    from tests.conftest_classroom import register

    async def fake(text, mode, api_key, s):
        def provider_call():                      # the live route calls the provider from a worker thread
            time.sleep(0.3)
            record_usage("typed_fact_next", {"promptTokenCount": 60, "candidatesTokenCount": 40, "totalTokenCount": 100})
            time.sleep(0.3)
        await run_in_threadpool(provider_call)
        return JSONResponse(content={"route_d": {"status": "SERVED"}})

    monkeypatch.setattr(main_mod, "_analyze_hybrid_route", fake)
    assert register(api, email="tok@algosim.edu.vn", name="Tok").status_code == 200
    ts = [threading.Thread(target=_post, args=(api, k)) for k in (K1, K2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    with main_mod.SessionLocal() as s:
        rows = s.execute(select(AdminAnalysisTelemetry.total_tokens, AdminAnalysisTelemetry.input_tokens)).all()
    assert sorted(rows) == [(100, 60), (100, 60)], rows
