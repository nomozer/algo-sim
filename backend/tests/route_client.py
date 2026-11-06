"""A client with a valid server-issued session and a generous daily limit, for route tests that are NOT about quota.

`/api/analyze` and `/api/image/extract` run nothing without a session (`session_required`), and a guest session holds one
trial. Tests of routing, caching or error mapping post many times, so they act as a signed-in account whose custom daily
limit (the admin mechanism `user_account_meta.custom_daily_limit`) is far above what one test sends. Quota itself is
tested in `test_analysis_usage_ledger.py`, `test_guest_trial.py` and `test_analyze_idempotency.py`.
"""
from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

ROUTE_TEST_DAILY_LIMIT = 100_000


def sign_in(client: TestClient) -> TestClient:
    """Give `client` a fresh signed-in session (in whatever database `app.main.SessionLocal` points to)."""
    import app.main as M
    from app.accounts import service
    from app.accounts.policy import Role
    from app.accounts.router import _ensure_user_meta_row

    with M.SessionLocal() as s:
        user = service.create_user(s, email=f"route-{secrets.token_hex(6)}@algosim.test", display_name="Route test",
                                   password="r" + secrets.token_hex(8), role=Role.STUDENT)
        s.flush()
        _ensure_user_meta_row(s, user.id).custom_daily_limit = ROUTE_TEST_DAILY_LIMIT
        token = service.new_session(s, user_id=user.id).token
        s.commit()
    client.cookies.set(service.SESSION_COOKIE, token)
    return client


def route_client(app, **kwargs) -> TestClient:
    return sign_in(TestClient(app, **kwargs))
