"""Usage that limits access (guest trial, daily quota) is recorded exactly once per served attempt, durably and
atomically — under concurrency, retries, restarts and database failures (run axo-final-reliability-premerge-gate).

The REAL `/api/analyze` path runs (`HYBRID_ROUTE_MODE=staging-replay`: recorded extraction, exact engine, 0 provider
calls); only the replay is slowed so concurrent requests really overlap. Telemetry (observational) is separate.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import event, select

from app import idempotency as idem
from tests.conftest_classroom import api, register  # noqa: F401

SERVED_TEXT = ("Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. Cạnh bên AD = 5. "
               "Tính thể tích khối lăng trụ ABC.DEF.")
REFUSED_TEXT = SERVED_TEXT.replace("lăng trụ đứng", "lăng trụ")


def _payload(text: str, right: bool) -> dict:
    solid = "Cho hình lăng trụ đứng ABC.DEF" if right else "Cho hình lăng trụ ABC.DEF"
    premises = [{"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A"},
                {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3"},
                {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4"},
                {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "5"}, "quote": "AD = 5"}]
    if right:
        premises.append({"kind": "right_prism", "args": {"base": list("ABC"), "top": list("DEF")}, "quote": solid})
    return {"schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
            "solids": [{"solid_id": "pr", "solid_type": "prism", "notation": "ABC.DEF", "quote": solid}],
            "premises": premises,
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "pr", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "pr"},
                            "quote": "Tính thể tích khối lăng trụ ABC.DEF."}]}


@pytest.fixture
def route(api, monkeypatch, tmp_path):  # noqa: F811
    """Real Hybrid /4 route on a recorded extraction; `state["delay"]` slows each replay to force overlap."""
    import app.ai.hybrid_offline as HO

    corpus = tmp_path / "replay.json"
    corpus.write_text(json.dumps({"schema": HO.LOCAL_REPLAY_SCHEMA, "outputs": {
        SERVED_TEXT: _payload(SERVED_TEXT, True), REFUSED_TEXT: _payload(REFUSED_TEXT, False)}}, ensure_ascii=False),
        encoding="utf-8")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(corpus))
    state = {"delay": 0.4, "runs": 0}
    original = HO.StagingReplay.run

    def slow_run(self, *a, **k):
        state["runs"] += 1
        time.sleep(state["delay"])
        return original(self, *a, **k)

    monkeypatch.setattr(HO.StagingReplay, "run", slow_run)
    import app.main as M
    with M.SessionLocal() as s:                       # every attempt computes (no cross-attempt cache hit)
        s.execute(M.SimulationCache.__table__.delete())
        s.commit()
    monkeypatch.setattr(M, "_cache_lookup", lambda *a, **k: None)
    idem._entries.clear()
    yield state
    idem._entries.clear()
    while _OPEN_CLIENTS:
        _OPEN_CLIENTS.pop().__exit__(None, None, None)


_OPEN_CLIENTS: list = []


def _post(client, key: str, text: str = SERVED_TEXT):
    return client.post("/api/analyze", json={"input": {"type": "text", "content": text}},
                       headers={idem.HEADER: key})


def _concurrently(*calls):
    out: list = [None] * len(calls)

    def run(i, fn):
        out[i] = fn()

    ts = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return out


def _served(r) -> bool:
    return r.status_code == 200 and r.json().get("route_d", {}).get("status") == "SERVED"


def _key(n: int) -> str:
    return "a" + f"{n:032x}"


def _guest_trials(client) -> int:
    return 1 - client.get("/api/auth/me").json()["entitlement"]["trialsLeft"]


def _user(api, email, *, limit=None, used=0):  # noqa: F811
    import app.main as M
    from app.accounts.router import _ensure_user_meta_row, _utc_today_str
    from app.persistence.classroom_models import User
    from tests.conftest_classroom import new_client

    # Entered once on this thread: a non-entered TestClient builds an event loop per request, and two threads doing
    # that at once deadlock in the offline network guard's socketpair (`backend/conftest.py`).
    client = new_client(api).__enter__()
    _OPEN_CLIENTS.append(client)
    assert register(client, email=email, name=email.split("@")[0]).status_code == 200
    with M.SessionLocal() as s:
        uid = s.execute(select(User.id).where(User.email == email)).scalar_one()
        meta = _ensure_user_meta_row(s, uid)
        meta.custom_daily_limit, meta.used_today, meta.usage_date = limit, used, _utc_today_str()
        s.commit()
    return client, uid


def _used_today(uid: int) -> int:
    import app.main as M
    from app.persistence.classroom_models import UserAccountMeta
    with M.SessionLocal() as s:
        return s.execute(select(UserAccountMeta.used_today).where(UserAccountMeta.user_id == uid)).scalar_one()


def test_two_tabs_of_one_guest_get_at_most_the_trial_limit(api, route):  # noqa: F811
    api.get("/api/auth/me")
    r1, r2 = _concurrently(lambda: _post(api, _key(1)), lambda: _post(api, _key(2)))
    assert sorted([_served(r1), _served(r2)]) == [False, True], (r1.status_code, r2.status_code)
    assert {r1.status_code, r2.status_code} == {200, 402}
    assert _guest_trials(api) == 1


def test_concurrent_submits_never_exceed_the_daily_quota(api, route):  # noqa: F811
    client, uid = _user(api, "quota@algosim.edu.vn", limit=2, used=1)
    rs = _concurrently(*[(lambda k=k: _post(client, _key(k))) for k in (1, 2, 3)])
    assert sum(map(_served, rs)) == 1, [r.status_code for r in rs]
    assert sorted(r.status_code for r in rs) == [200, 429, 429]
    assert _used_today(uid) == 2


def test_concurrent_attempts_of_one_account_are_each_counted(api, route):  # noqa: F811
    client, uid = _user(api, "many@algosim.edu.vn", limit=50)
    rs = _concurrently(*[(lambda k=k: _post(client, _key(k))) for k in range(6)])
    assert all(map(_served, rs))
    assert _used_today(uid) == 6


def test_two_accounts_at_once_are_charged_independently(api, route):  # noqa: F811
    (a, ua), (b, ub) = _user(api, "a@algosim.edu.vn", limit=5), _user(api, "b@algosim.edu.vn", limit=5)
    ra, rb = _concurrently(lambda: _post(a, _key(1)), lambda: _post(b, _key(1)))
    assert _served(ra) and _served(rb)
    assert (_used_today(ua), _used_today(ub)) == (1, 1)


def test_retry_of_a_served_attempt_after_a_restart_is_not_charged_again(api, route):  # noqa: F811
    client, uid = _user(api, "restart@algosim.edu.vn", limit=5)
    assert _served(_post(client, _key(7)))
    idem._entries.clear()                            # the in-process idempotency table is lost on restart
    assert _served(_post(client, _key(7)))
    assert _used_today(uid) == 1


def test_retry_after_an_infrastructure_failure_is_charged_once(api, route, monkeypatch):  # noqa: F811
    client, uid = _user(api, "retry@algosim.edu.vn", limit=5)
    good = __import__("os").environ["HYBRID_REPLAY_CORPUS"]
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", good + ".missing")
    assert _post(client, _key(8)).status_code >= 500
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", good)
    assert _served(_post(client, _key(8)))
    assert _used_today(uid) == 1


def test_a_refused_analysis_uses_no_trial_and_no_quota(api, route):  # noqa: F811
    client, uid = _user(api, "refused@algosim.edu.vn", limit=5)
    r = _post(client, _key(9), REFUSED_TEXT)
    assert r.status_code == 200 and r.json()["route_d"]["status"] == "REFUSED"
    assert _used_today(uid) == 0
    api.get("/api/auth/me")
    assert _post(api, _key(10), REFUSED_TEXT).json()["route_d"]["status"] == "REFUSED"
    assert _guest_trials(api) == 0


@pytest.fixture
def fail_writes():
    """Make writes touching the given SQL fragments fail like a locked SQLite database (engine-level, ORM or Core)."""
    import app.main as M

    targets: list[str] = []                       # statement prefixes, e.g. "update user_account_meta"
    engine = M.SessionLocal.kw["bind"]

    def before(conn, cursor, statement, params, context, executemany):
        s = " ".join(statement.lower().split())
        if any(s.startswith(t) for t in targets):
            raise sqlite3.OperationalError("database is locked")

    event.listen(engine, "before_cursor_execute", before)
    yield targets
    event.remove(engine, "before_cursor_execute", before)


def test_a_served_analysis_is_never_left_uncharged_when_the_quota_write_fails(api, route, fail_writes):  # noqa: F811
    client, uid = _user(api, "lock@algosim.edu.vn", limit=5)
    fail_writes.append("update user_account_meta")
    r = _post(client, _key(11))
    fail_writes.clear()
    assert not (_served(r) and _used_today(uid) == 0), "analysis served without charging the daily quota"
    if not _served(r):
        assert r.status_code == 503 and route["runs"] == 0      # refused before any provider work


def test_a_telemetry_failure_is_logged_and_never_loses_the_quota_charge(api, route, fail_writes, caplog):  # noqa: F811
    client, uid = _user(api, "telemetry@algosim.edu.vn", limit=5)
    fail_writes.append("insert into admin_analysis_telemetry")
    with caplog.at_level(logging.WARNING):
        r = _post(client, _key(12))
    fail_writes.clear()
    assert _served(r)
    assert _used_today(uid) == 1
    assert any("telemetry" in rec.getMessage().lower() for rec in caplog.records)


def test_a_reservation_counts_before_the_provider_runs(api, route, monkeypatch):  # noqa: F811
    """Process killed after the analysis but before finalisation: the attempt is already counted (fail closed)."""
    import app.main as M
    client, uid = _user(api, "crash@algosim.edu.vn", limit=5)
    seen = {}
    original = M._analyze_hybrid_route

    async def observe(*a, **k):
        seen["used_during_run"] = _used_today(uid)
        return await original(*a, **k)

    monkeypatch.setattr(M, "_analyze_hybrid_route", observe)
    assert _served(_post(client, _key(13)))
    assert seen["used_during_run"] == 1 and _used_today(uid) == 1


def test_a_request_without_a_session_gets_one_and_runs_nothing(api, route):  # noqa: F811
    """No valid session ⇒ the server issues a guest session (httponly cookie) but runs no analysis for that request;
    the retry with the cookie is a normal, counted guest attempt."""
    api.cookies.clear()
    r = _post(api, _key(20))
    assert r.status_code == 401 and r.json()["reason_code"] == "session_required"
    assert route["runs"] == 0
    assert "algosim_session=" in r.headers.get("set-cookie", "") and "httponly" in r.headers["set-cookie"].lower()
    assert _served(_post(api, _key(20)))           # same attempt, now with the issued cookie
    assert route["runs"] == 1 and _guest_trials(api) == 1


def test_dropping_the_cookie_never_reaches_the_provider(api, route):  # noqa: F811
    for n in range(5):
        api.cookies.clear()
        assert _post(api, _key(30 + n)).status_code == 401
    assert route["runs"] == 0


def test_an_unknown_or_forged_session_is_not_a_session(api, route):  # noqa: F811
    api.cookies.clear()
    api.cookies.set("algosim_session", "forged-" + "0" * 40)
    assert _post(api, _key(40)).status_code == 401
    assert route["runs"] == 0


def test_image_extraction_without_a_session_runs_nothing(api, monkeypatch):  # noqa: F811
    import app.main as M
    calls = []
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.setattr(M, "decode_image_base64", lambda *a, **k: calls.append("decode") or b"")
    api.cookies.clear()
    r = api.post("/api/image/extract", json={"content": "AAAA", "mime_type": "image/png"})
    assert r.status_code == 401 and r.json()["reason_code"] == "session_required"
    assert calls == []


def test_the_ledger_has_one_row_per_attempt_at_the_storage_layer():
    from app.persistence.classroom_models import AnalysisUsageLedger
    uniques = [tuple(c.name for c in u.columns) for u in AnalysisUsageLedger.__table__.constraints
               if u.__class__.__name__ == "UniqueConstraint"]
    assert ("scope", "attempt_key") in uniques
