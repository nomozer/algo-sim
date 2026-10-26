"""Real Windows process handles plus injected OS failures; no provider calls."""
import ctypes
import importlib
import json
import os
import sys

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows job object API")


def _stopped(pid):
    from ctypes import wintypes as W
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    kernel.CloseHandle.argtypes = [W.HANDLE]
    handle = kernel.OpenProcess(0x100000, False, pid)
    if not handle:
        assert ctypes.get_last_error() == 87, "Cannot verify process termination"
        return True
    try:
        return kernel.WaitForSingleObject(handle, 0) == 0
    finally:
        kernel.CloseHandle(handle)


@pytest.fixture
def job_module():
    return importlib.import_module("scripts.windows_process_job")


def test_normal_completion_preserves_exit_and_unicode_log(tmp_path, job_module):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    log = tmp_path / "normal.log"
    result = batch.invoke([sys._base_executable, "-c", "print('Đã hoàn tất')"], 10, log)
    assert result["status"] == "PASS" and result["exit_code"] == 0
    assert result["process_tree"]["active_processes"] == 0
    assert "Đã hoàn tất" in log.read_text(encoding="utf-8")
    log.rename(tmp_path / "closed.log")


def test_timeout_stops_parent_child_and_grandchild(tmp_path, job_module):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    leaf = "import os,time; print(os.getpid(),flush=True); time.sleep(60)"
    child = f"import os,subprocess,sys,time; print(os.getpid(),flush=True); subprocess.Popen([sys.executable,'-u','-c',{leaf!r}]); time.sleep(60)"
    parent = f"import os,subprocess,sys,time; print(os.getpid(),flush=True); subprocess.Popen([sys.executable,'-u','-c',{child!r}]); time.sleep(60)"
    log = tmp_path / "tree.log"
    result = batch.invoke([sys._base_executable, "-u", "-c", parent], 2, log)
    pids = [int(value) for value in log.read_text(encoding="utf-8").split()]
    assert len(set(pids)) == 3
    assert result["status"] == "INCOMPLETE_TIMEOUT" and result["exit_code"] is None
    assert result["process_tree"]["active_processes"] == 0
    assert set(pids) <= set(result["process_tree"]["pids_before_cleanup"])
    assert all(_stopped(pid) for pid in pids)
    (tmp_path / "process-observation.json").write_text(json.dumps({"pids": pids, "all_stopped": True,
                                                                 "job": result["process_tree"]}), encoding="utf-8")


def test_parent_exit_does_not_leave_its_child_alive(tmp_path, job_module):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    code = "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print(p.pid,flush=True)"
    log = tmp_path / "exit-race.log"
    result = batch.invoke([sys._base_executable, "-u", "-c", code], 10, log)
    assert result["exit_code"] == 0 and result["status"] == "PASS"
    assert result["process_tree"]["active_processes"] == 0
    assert _stopped(int(log.read_text().strip()))


def test_spawn_error_is_not_a_geometry_refusal(tmp_path, job_module):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    with pytest.raises(FileNotFoundError):
        batch.invoke([str(tmp_path / "missing-program.exe")], 1, tmp_path / "spawn.log")


@pytest.mark.parametrize("operation", ["TerminateJobObject", "QueryInformationJobObject"])
def test_os_cleanup_failure_stays_failure_and_close_reaps_owned_process(tmp_path, monkeypatch, job_module, operation):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    log = tmp_path / "failure.log"
    code = "import os,time; print(os.getpid(),flush=True); time.sleep(60)"
    def denied(*args):
        ctypes.set_last_error(5)
        return 0
    monkeypatch.setattr(job_module._kernel, operation, denied)
    with pytest.raises(RuntimeError, match="WATCHDOG_TERMINATION_FAILED"):
        batch.invoke([sys._base_executable, "-u", "-c", code], .5, log)
    assert _stopped(int(log.read_text().strip()))


def test_job_creation_failure_never_starts_workload(tmp_path, monkeypatch, job_module):
    batch = importlib.import_module("scripts.run_schema_contract_offline")
    marker = tmp_path / "must-not-run"
    def denied(*args):
        ctypes.set_last_error(5)
        return None
    monkeypatch.setattr(job_module._kernel, "CreateJobObjectW", denied)
    with pytest.raises(OSError):
        batch.invoke([sys._base_executable, "-c", f"open({str(marker)!r},'w').close()"], 1, tmp_path / "denied.log")
    assert not marker.exists()


def test_close_wait_timeout_remains_a_persistable_harness_failure(monkeypatch, job_module):
    process = job_module.WindowsJobProcess.__new__(job_module.WindowsJobProcess)
    process.job, process.process = None, 1234
    def still_waiting(timeout):
        assert timeout == 5
        raise job_module.subprocess.TimeoutExpired("synthetic pending I/O", timeout)
    process.wait = still_waiting
    closed = []
    monkeypatch.setattr(job_module._kernel, "CloseHandle", lambda handle: closed.append(handle) or 1)
    with pytest.raises(RuntimeError, match="WATCHDOG_TERMINATION_FAILED"):
        process.close()
    assert closed == [1234] and process.process is None
