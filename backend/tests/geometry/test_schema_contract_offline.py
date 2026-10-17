"""Real subprocess exit/watchdog checks; synthetic receipts only, no provider or research corpus."""
import importlib
import sys
import ctypes
import json
import os

import pytest


def test_invocation_preserves_actual_exit_code_and_log(tmp_path):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    log = tmp_path / "child.log"
    result = batch.invoke([sys._base_executable, "-c", "print('synthetic'); raise SystemExit(7)"], 10, log)
    assert result["exit_code"] == 7 and result["status"] == "FAILURE"
    assert result["duration_seconds"] >= 0 and "synthetic" in log.read_text()


def test_watchdog_is_incomplete_runtime_failure_not_geometry_refusal(tmp_path):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    result = batch.invoke([sys._base_executable, "-c", "import time; time.sleep(60)"], .3, tmp_path / "timeout.log")
    assert result["status"] == "INCOMPLETE_TIMEOUT" and result["exit_code"] is None
    assert result["duration_seconds"] < 10
    assert "REFUSED" not in str(result)


@pytest.mark.skipif(os.name != "nt", reason="Windows descendant-handle check")
def test_windows_watchdog_terminates_the_invocation_child_tree(tmp_path):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    code = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print(p.pid,flush=True); time.sleep(60)"
    log = tmp_path / "tree.log"
    result = batch.invoke([sys._base_executable, "-u", "-c", code], 2, log)
    assert result["status"] == "INCOMPLETE_TIMEOUT"
    pid = int(log.read_text().strip())
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x100000, False, pid)
    if handle:
        try:
            assert kernel.WaitForSingleObject(handle, 0) == 0
        finally:
            kernel.CloseHandle(handle)


@pytest.mark.parametrize("launch_error", [False, True])
def test_matrix_stops_after_first_nonzero_exit_and_rejects_overwrite(tmp_path, monkeypatch, launch_error):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    inp = {"protocol": {"lock_status": "LOCKED", "offline_watchdog_seconds": 10}}
    monkeypatch.setattr(batch.R.E, "load_inputs", lambda p: inp)
    class Harness:
        def identity(self, data, mode):
            return {"mode": mode, "arm": "synthetic"}
    monkeypatch.setattr(batch.R, "harness", lambda *args: Harness())
    calls = []
    def failed(*args):
        calls.append(args)
        if launch_error:
            raise FileNotFoundError("synthetic missing interpreter")
        return {"status": "FAILURE", "exit_code": 7, "duration_seconds": .01}
    monkeypatch.setattr(batch, "invoke", failed)
    doc = batch.run_matrix(tmp_path, tmp_path / "out", sys._base_executable)
    assert len(calls) == 1 and doc["status"] == "INCOMPLETE"
    assert [r["status"] for r in doc["invocations"]] == ["FAILURE_HARNESS" if launch_error else "FAILURE"] + ["NOT_STARTED"] * 7
    with pytest.raises(batch.R.V1.PilotStopped, match="OUTPUT_EXISTS"):
        batch.run_matrix(tmp_path, tmp_path / "out", sys._base_executable)


@pytest.mark.parametrize("tamper", [None, "identity", "live", "hash", "schedule", "infra", "class"])
def test_receipt_check_rejects_tampered_or_incomplete_execution(tmp_path, tamper):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    identity = {"arm": "synthetic", "mode": "PILOT"}
    planned = [{"case_id": "a", "sample": 1}]
    state = {"identity": identity, "rows": [{"case_id": "a", "sample": 0}], "live_model_calls": 0,
             "execution_class": "GOLD"}
    if tamper == "schedule":
        state["rows"] = []
    if tamper == "infra":
        state["rows"][0]["infra"] = "SYNTHETIC_FAILURE"
    state["rows_sha256"] = batch.R.V1._sha(state["rows"])
    score = {"identity": dict(identity), "execution_class": "GOLD", "live_model_calls": 0,
             "source_manifest_rows_sha256": state["rows_sha256"], "schema": batch.R.E.SCORER_VERSION,
             "schedule": batch.R.E.validate_schedule(state, planned)}
    if tamper == "identity":
        score["identity"]["mode"] = "LOCKED"
    if tamper == "live":
        state["live_model_calls"] = 1
    if tamper == "hash":
        state["rows_sha256"] = "changed"
    if tamper == "class":
        state["execution_class"] = "LIVE"
    for name, value in (("manifest", state), ("score", score)):
        (tmp_path / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
    if tamper:
        with pytest.raises(batch.R.V1.PilotStopped):
            batch.check_receipt(tmp_path, identity, planned, "gold")
    else:
        assert batch.check_receipt(tmp_path, identity, planned, "gold")["status"] == "COMPLETE"
