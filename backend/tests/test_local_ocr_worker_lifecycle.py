"""Exercise the real JSON-lines transport without loading OCR models."""
import sys
import time

import pytest

from app.ingestion import local_ocr as ocr


def test_worker_exit_is_reported_without_waiting_for_request_deadline(tmp_path, monkeypatch):
    script = tmp_path / "exit_worker.py"
    script.write_text("import sys\nsys.stdin.readline()\n", encoding="utf-8")
    monkeypatch.setattr(ocr, "_WORKER_PATH", script)
    worker = ocr._Worker(sys.executable)
    try:
        started = time.perf_counter()
        with pytest.raises(OSError):
            worker.request({"id": "crash"}, timeout_s=2)
        assert time.perf_counter() - started < 1.5
    finally:
        worker.kill()


@pytest.mark.parametrize("reply", ['[]', 'null', '"bad"'])
def test_non_object_worker_reply_fails_at_transport_boundary(tmp_path, monkeypatch, reply):
    script = tmp_path / "reply_worker.py"
    script.write_text(f"import sys\nsys.stdin.readline()\nprint({reply!r}, flush=True)\n", encoding="utf-8")
    monkeypatch.setattr(ocr, "_WORKER_PATH", script)
    worker = ocr._Worker(sys.executable)
    try:
        with pytest.raises(ValueError):
            worker.request({"id": "invalid"}, timeout_s=2)
    finally:
        worker.kill()


def test_shutdown_reaps_worker_and_closes_pipes():
    worker = ocr._Worker(sys.executable)
    worker.ensure()
    proc = worker.proc
    assert proc is not None
    worker.kill()
    assert proc.poll() is not None
    assert proc.stdin.closed and proc.stdout.closed


def test_worker_timeout_then_restart_returns_only_fresh_response(tmp_path, monkeypatch):
    script = tmp_path / "slow_worker.py"
    script.write_text("import sys,time\nsys.stdin.readline()\ntime.sleep(5)\n", encoding="utf-8")
    monkeypatch.setattr(ocr, "_WORKER_PATH", script)
    worker = ocr._Worker(sys.executable)
    try:
        with pytest.raises(TimeoutError):
            worker.request({"id": "old"}, timeout_s=0.1)
        script.write_text("import sys,json\nfor line in sys.stdin:\n print(json.dumps(json.loads(line)), flush=True)\n", encoding="utf-8")
        assert worker.request({"id": "fresh"}, timeout_s=2) == {"id": "fresh"}
    finally:
        worker.kill()
