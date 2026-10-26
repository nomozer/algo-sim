"""Receipt publication survives a restrictive Windows console without changing the gate exit."""
import importlib.util
import io
import json
from pathlib import Path

import pytest


@pytest.mark.parametrize("code", [0, 7])
def test_receipt_written_utf8_before_cp1252_console_output(tmp_path, code):
    runner = _runner()
    raw = io.BytesIO()
    console = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
    receipt = {"exit_code": code, "message": "Đã kiểm chứng — kết quả thật"}
    assert runner.publish_receipt(receipt, tmp_path, code, console) == code
    assert json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8")) == receipt
    console.flush()
    assert json.loads(raw.getvalue().decode("cp1252")) == receipt


def test_console_failure_does_not_override_failure_or_erase_receipt(tmp_path):
    class BrokenConsole:
        def write(self, value):
            assert (tmp_path / "receipt.json").exists()
            raise OSError("synthetic closed console")
    assert _runner().publish_receipt({"exit_code": 7}, tmp_path, 7, BrokenConsole()) == 7
    assert json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))["exit_code"] == 7


def _runner():
    path = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-v2-after-main-integration/tools/run_t3.py"
    spec = importlib.util.spec_from_file_location("recovery_t3_runner", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner
