"""A session guard waiting for SQLite must let concurrent response cleanup run."""
import asyncio
import sqlite3

from fastapi.responses import JSONResponse

from app import main


def test_prepare_session_guard_does_not_block_transaction_cleanup(tmp_path, monkeypatch):
    path = tmp_path / "session-guard.db"
    locker = sqlite3.connect(path)
    locker.execute("CREATE TABLE sessions (id INTEGER)")
    locker.commit()
    locker.execute("BEGIN EXCLUSIVE")

    def guard(_token):
        with sqlite3.connect(path, timeout=0.3) as connection:
            connection.execute("INSERT INTO sessions VALUES (1)")
        return JSONResponse(status_code=401, content={"reason_code": "session_required"})

    monkeypatch.setattr(main, "_cong_luot_thu", guard)

    async def exercise():
        async def release_other_response_transaction():
            await asyncio.sleep(0)
            locker.commit()

        response, _ = await asyncio.gather(
            main.input_prepare(main.InputPrepareBody(content="unused"), None),
            release_other_response_transaction(),
        )
        return response

    try:
        assert asyncio.run(exercise()).status_code == 401
        assert locker.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
    finally:
        locker.close()


def test_prepare_keeps_the_event_loop_free_while_local_ocr_runs(monkeypatch):
    """Run `local-semantic-source-gate-reliability`: OCR is seconds of blocking work. Run on the event loop it stalled every
    other request (a trivial /api/health took 8.5 s under 8 uploads), so an /api/auth/me transaction could not commit
    and SQLite writers timed out with SQLITE_BUSY. The loop must keep ticking while OCR runs."""
    import asyncio
    import base64
    import time

    from app.ingestion import local_ocr_route as LR
    from app.ingestion import unified_input as U
    from tests.test_image_first_local_ocr import _fake_rec, _png_bytes

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setattr(LR, "count_problem_headers_on_page", lambda data: None)

    def slow_ocr(data, figs):
        time.sleep(0.8)                                  # stands in for the sidecar round trip
        return _fake_rec(True)

    monkeypatch.setattr(LR, "run_local_ocr_route", slow_ocr)

    async def scenario():
        gaps: list[float] = []
        done = asyncio.Event()

        async def ticker():
            last = time.perf_counter()
            while not done.is_set():
                await asyncio.sleep(0.02)
                now = time.perf_counter()
                gaps.append(now - last)
                last = now

        tick = asyncio.create_task(ticker())
        out = await U.prepare_unified_input(content=base64.b64encode(_png_bytes()).decode(), declared_mime="image/png", filename="de.png")
        done.set()
        await tick
        return out, (max(gaps) if gaps else float("inf"))  # no tick at all = blocked for the whole call

    out, worst_gap = asyncio.run(scenario())
    assert out.status == "ready"
    assert worst_gap < 0.4, f"event loop blocked for {worst_gap:.2f}s during OCR"
