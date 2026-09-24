# -*- coding: utf-8 -*-
"""TEST SUITE CHỨNG MINH HARNESS ĐỘC LẬP VỚI TÊN BRANCH.

Khẳng định rằng:
1. Harness của `run_multicase_benchmark` chạy giống nhau trên mọi tên branch.
2. `diagnose_analyze_failure_cluster.precheck()` chấp nhận bất kỳ branch hợp lệ nào.
3. `run_preregistered_failure_reproduction.run_precheck()` chấp nhận bất kỳ branch hợp lệ nào.
4. `audit_second_family_preregistration_evidence.audit_precheck()` độc lập với tên branch.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import diagnose_analyze_failure_cluster as D
import run_preregistered_failure_reproduction as R
import audit_second_family_preregistration_evidence as AUDIT
import test_completion_runner_repair as TR


@pytest.mark.parametrize("branch_name", [
    "main",
    "feat/rectangular-base-pyramid-compiler",
    "arbitrary-feature-branch-xyz",
    "hotfix/test-isolation-123",
])
def test_diagnose_precheck_independent_of_branch(monkeypatch, branch_name):
    """precheck() của diagnose_analyze_failure_cluster chạy độc lập với branch."""
    real_run = subprocess.run

    def fake_run(cmd, *a, **k):
        if len(cmd) >= 3 and cmd[0] == "git" and cmd[1] == "branch" and cmd[2] == "--show-current":
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{branch_name}\n", stderr="")
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", fake_run)
    pk = D.precheck()
    assert pk["BRANCH"] == branch_name
    assert pk["PRECHECK_STATUS"] == "PASS"


@pytest.mark.parametrize("branch_name", [
    "main",
    "feat/rectangular-base-pyramid-compiler",
    "feat/some-other-feature",
])
def test_reproduce_precheck_independent_of_branch(monkeypatch, branch_name):
    """run_precheck() của reproduce_preregistered_failures chạy độc lập với branch."""
    real_run = subprocess.run

    def fake_run(cmd, *a, **k):
        if len(cmd) >= 3 and cmd[0] == "git" and cmd[1] == "branch" and cmd[2] == "--show-current":
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{branch_name}\n", stderr="")
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", fake_run)
    pk = R.run_precheck()
    assert pk["BRANCH"] == branch_name
    assert pk["CANDIDATE_VERIFY"] is True
    assert pk["CACHE_IDENTITY_VERIFY"] is True


@pytest.mark.parametrize("branch_name", [
    "main",
    "feat/rectangular-base-pyramid-compiler",
    "custom-branch-name",
])
def test_audit_second_family_precheck_independent_of_branch(monkeypatch, branch_name):
    """audit_precheck() của second family evidence repair chạy độc lập với branch."""
    real_run_git = AUDIT.run_git

    def fake_run_git(args):
        if len(args) >= 3 and args[0] == "rev-parse" and args[1] == "--abbrev-ref" and args[2] == "HEAD":
            return 0, branch_name
        return real_run_git(args)

    monkeypatch.setattr(AUDIT, "run_git", fake_run_git)
    pk = AUDIT.audit_precheck()
    assert pk["branch"] == branch_name
    assert pk["valid"] is True


def test_completion_runner_runs_under_arbitrary_branch(tmp_path, monkeypatch):
    """TR._chay_main chạy hoàn toàn độc lập với branch thật đang checkout."""
    real_run = subprocess.run

    def fake_run(cmd, *a, **k):
        if len(cmd) >= 3 and cmd[0] == "git" and cmd[1] == "branch" and cmd[2] == "--show-current":
            return subprocess.CompletedProcess(cmd, 0, stdout="arbitrary-branch-test\n", stderr="")
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", fake_run)
    ma, thay = TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))
    assert thay == TR.CON_LAI
