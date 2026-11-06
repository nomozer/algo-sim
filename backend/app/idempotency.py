"""Idempotency of `POST /api/analyze`: one learner submit (the client's attempt ID) runs the pipeline at most once.

The client sends `Idempotency-Key: <attempt id>` (the same ID for its own network retries, a new one per submit). The key
is an ATTEMPT identity, never a geometry identity — two submits of the same text are two attempts (two executions; the
envelope cache, keyed by the exact text, is what makes the second one cheap).

States of one `(scope, key)` entry:
- in progress → a second request with the same payload WAITS for the first and gets its response (no second provider
  call, no second guest-trial charge); after `WAIT_S` it gets 409 `IDEMPOTENCY_REQUEST_IN_PROGRESS` + `Retry-After`;
- completed (2xx) → replayed byte for byte with `Idempotent-Replayed: true` until `TTL_S` expires;
- failed (non-2xx, exception, cancellation) → forgotten, so a retry executes again (a 5xx is never replayed as a result);
- same key, different payload → 409 `IDEMPOTENCY_KEY_REUSED`, nothing runs.

Scope is the hashed session cookie: one session can never read another's entry. Nothing here logs; the problem text is
held only as a sha256 and inside the stored response (memory only, bounded by `MAX_ENTRIES` and `TTL_S`).

ponytail: in-process dict — correct for the shipped single uvicorn process (Dockerfile CMD has no `--workers`); several
workers/hosts would each keep their own table, so the guarantee does NOT hold there. Upgrade path: a DB row with a unique
`(scope, key)` constraint and a state column.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi.responses import JSONResponse
from starlette.responses import Response

HEADER = "Idempotency-Key"
KEY_RE = re.compile(r"[A-Za-z0-9_-]{16,128}")
TTL_S = 600.0
WAIT_S = 240.0          # > the live route's default deadline (3 × 60 s), so a coalesced retry normally gets the result
MAX_ENTRIES = 2048


@dataclass
class _Entry:
    payload_hash: str
    done: asyncio.Future            # → (status, body, headers) when stored, None when the original failed
    expires: float = float("inf")   # set when completed; an in-progress entry is never purged


_entries: dict[tuple[str, str], _Entry] = {}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _error(status: int, code: str, msg: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": msg, "reason_code": code},
                        headers={"Cache-Control": "no-store", **(headers or {})})


def _purge(now: float) -> None:
    for k in [k for k, e in _entries.items() if e.expires <= now]:
        del _entries[k]
    if len(_entries) > MAX_ENTRIES:            # oldest completed first (dict keeps insertion order)
        for k in [k for k, e in _entries.items() if e.done.done()][: len(_entries) - MAX_ENTRIES]:
            del _entries[k]


def _replay(stored: tuple[int, bytes, dict[str, str]]) -> Response:
    status, body, headers = stored
    return Response(content=body, status_code=status, headers={**headers, "Idempotent-Replayed": "true"})


async def run_once(key: str | None, session_cookie: str | None, payload: str,
                   execute: Callable[[], Awaitable[Response]]) -> Response:
    """Run `execute` at most once per `(session, key, payload)`; no key ⇒ run it (legacy clients)."""
    if key is None:
        return await execute()
    if not KEY_RE.fullmatch(key):
        return _error(400, "IDEMPOTENCY_KEY_INVALID", "Mã lượt gửi không hợp lệ.")
    k, ph = (_sha(session_cookie or ""), key), _sha(payload)
    _purge(time.monotonic())
    while (e := _entries.get(k)) is not None:   # no await between the last check and the insert below ⇒ atomic
        if e.payload_hash != ph:
            return _error(409, "IDEMPOTENCY_KEY_REUSED", "Mã lượt gửi này đã dùng cho một đề khác.")
        try:
            stored = await asyncio.wait_for(asyncio.shield(e.done), timeout=WAIT_S)
        except asyncio.TimeoutError:
            return _error(409, "IDEMPOTENCY_REQUEST_IN_PROGRESS", "Lượt gửi này vẫn đang được xử lý.",
                          {"Retry-After": "5"})
        if stored is not None:
            return _replay(stored)
        # the original failed and removed itself: loop, then run it ourselves (or wait for whoever got there first)
    entry = _Entry(ph, asyncio.get_running_loop().create_future())
    _entries[k] = entry
    try:
        resp = await execute()
    except BaseException:
        _entries.pop(k, None)
        entry.done.set_result(None)
        raise
    if 200 <= resp.status_code < 300 and isinstance(getattr(resp, "body", None), bytes):
        headers = {h: v for h, v in resp.headers.items() if h.lower() != "content-length"}
        entry.expires = time.monotonic() + TTL_S
        entry.done.set_result((resp.status_code, resp.body, headers))
    else:
        _entries.pop(k, None)
        entry.done.set_result(None)
    return resp
