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
