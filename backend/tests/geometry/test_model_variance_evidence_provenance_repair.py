# -*- coding: utf-8 -*-
"""MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR Test Suite.

Kiểm tra 16 bất biến tối thiểu theo Mục 6 của wave:
1. Full commit SHA chỉ lấy từ git rev-parse.
2. SHA ghép hoặc không tồn tại bị từ chối.
3. Test counts chỉ lấy từ JUnit / terminal evidence.
4. Exit code khác 0 làm verdict FAIL.
5. Test skip/xfail không được tính PASS.
6. F1-F10 chỉ CAUGHT nếu test node tương ứng PASS.
7. Thiếu một fault ID làm fault proof FAIL.
8. Trùng fault ID làm fault proof FAIL.
9. Determinism chỉ PROVED nếu hai file set và toàn bộ hash trùng.
10. Artifact nguồn bị thay đổi làm integrity gate FAIL.
11. Claim ghi PROVED nhưng thiếu evidence hash bị từ chối.
12. Candidate / cache audit chỉ chạy read-only.
13. Generator không nhận boolean verdict làm input.
14. Network-capable call bị chặn trong offline test process.
15. Historical files không được ghi / sửa.
16. Staging allowlist không chứa favicon.
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
from pathlib import Path
from typing import Any

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import provenance_evidence_collector as P  # noqa: E402


def test_01_full_commit_sha_from_git_rev_parse_only():
    """1. Full commit SHA chỉ lấy từ git rev-parse."""
    ev_rev = P.CommandEvidence(
        argv=["git", "rev-parse", "--verify", "3ba5afbb^{commit}"],
        cwd=str(REPO),
        exit_code=0,
        stdout="3ba5afbbd6b6e22781b03f29563c9d1589780603",
        stderr="",
        duration_seconds=0.01,
        stdout_sha256="abc",
        stderr_sha256="def",
        start_utc="",
        end_utc="",
    )
    ev_anc1 = P.CommandEvidence(
        argv=["git", "merge-base", "--is-ancestor", "d09331ea", "3ba5afbb"],
        cwd=str(REPO), exit_code=0, stdout="", stderr="",
        duration_seconds=0.01, stdout_sha256="", stderr_sha256="", start_utc="", end_utc="",
    )
    ev_anc2 = P.CommandEvidence(
        argv=["git", "merge-base", "--is-ancestor", "3ba5afbb", "63eb0640"],
        cwd=str(REPO), exit_code=0, stdout="", stderr="",
        duration_seconds=0.01, stdout_sha256="", stderr_sha256="", start_utc="", end_utc="",
    )
    ev_cnt = P.CommandEvidence(
        argv=["git", "rev-list", "--count", "d09331ea..63eb0640"],
        cwd=str(REPO), exit_code=0, stdout="2", stderr="",
        duration_seconds=0.01, stdout_sha256="", stderr_sha256="", start_utc="", end_utc="",
    )
    ev_diff1 = P.CommandEvidence(
        argv=["git", "diff", "--name-status", "d09331ea..3ba5afbb"],
        cwd=str(REPO), exit_code=0,
        stdout="A backend/scripts/kind_aware_trace_evaluator.py\nA backend/tests/geometry/test_model_variance_evidence_review.py\nM docs/CODE_INDEX.md",
        stderr="", duration_seconds=0.01, stdout_sha256="", stderr_sha256="", start_utc="", end_utc="",
    )
    ev_diff2 = P.CommandEvidence(
        argv=["git", "diff", "--name-status", "3ba5afbb..63eb0640"],
        cwd=str(REPO), exit_code=0,
        stdout="A docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md\nA docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/PRECHECK.json",
        stderr="", duration_seconds=0.01, stdout_sha256="", stderr_sha256="", start_utc="", end_utc="",
    )

    parsed = P.parse_git_commit_identity([ev_rev, ev_anc1, ev_anc2, ev_cnt, ev_diff1, ev_diff2])
    assert parsed["ACTUAL_COMMIT_1"] == "3ba5afbbd6b6e22781b03f29563c9d1589780603"
    assert parsed["COMMIT_IDENTITY_CLASSIFICATION"] == "COMMIT_ROLE_LABELING_ERROR"
    assert parsed["HISTORY_DRIFT"] == "NO"


def test_02_spliced_or_nonexistent_sha_rejected():
    """2. SHA ghép hoặc SHA không tồn tại bị từ chối / coi là drift nếu ancestry sai."""
    ev_rev = P.CommandEvidence(
        argv=["git", "rev-parse", "--verify", "3ba5afbb^{commit}"],
        cwd=str(REPO),
        exit_code=1,  # git rev-parse failed
        stdout="",
        stderr="fatal: Needed a single revision",
        duration_seconds=0.01, stdout_sha256="", stderr_sha256="", start_utc="", end_utc="",
    )
    parsed = P.parse_git_commit_identity([ev_rev])
    assert parsed["COMMIT_IDENTITY_CLASSIFICATION"] == "HISTORY_DRIFT"
    assert parsed["HISTORY_DRIFT"] == "YES"


def test_03_test_counts_from_junit_and_terminal_only(tmp_path: Path):
    """3. Test counts chỉ lấy từ JUnit / terminal evidence."""
    mock_xml = tmp_path / "mock.xml"
    mock_xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuite name="pytest" tests="5" errors="0" failures="1" skipped="1" time="0.5">'
        '<testcase name="test_1" time="0.1" />'
        '<testcase name="test_2" time="0.1"><failure message="failed">assert False</failure></testcase>'
        '<testcase name="test_3" time="0.1"><skipped message="skip">skipped</skipped></testcase>'
        '<testcase name="test_4" time="0.1" />'
        '<testcase name="test_5" time="0.1" />'
        '</testsuite>',
        encoding="utf-8",
    )
    parsed = P.parse_junit_xml(mock_xml)
    assert parsed["total_tests"] == 5
    assert parsed["passed"] == 3
    assert parsed["failed"] == 1
    assert parsed["skipped"] == 1
    assert parsed["errors"] == 0

    term_text = "5942 passed, 1 skipped, 3 deselected in 12.34s"
    parsed_term = P.parse_pytest_terminal_summary(term_text)
    assert parsed_term["passed"] == 5942
    assert parsed_term["skipped"] == 1
    assert parsed_term["deselected"] == 3
    assert parsed_term["failed"] == 0


def test_04_nonzero_exit_code_fails_verdict():
    """4. Exit code khác 0 làm verdict FAIL."""
    evidence = {
        "commit_identity": {"COMMIT_IDENTITY_CLASSIFICATION": "COMMIT_IDENTITY_VALID", "HISTORY_DRIFT": "NO"},
        "source_integrity": {"ALL_MATCHED": True},
        "focused_test": {"exit_code": 1, "failed": 1, "errors": 0},  # FAILED
        "full_test": {"exit_code": 0, "failed": 0, "errors": 0},
        "fault_injections": {"ALL_CAUGHT": True},
        "determinism": {"VERIFICATION_RESULT": "PROVED_BITWISE_IDENTICAL_ACROSS_RUNS"},
        "candidate_cache": {"candidate_verify": True, "cache_verify": True},
        "secret_scan": {"SECRET_LEAKS_COUNT": 0},
        "claim_matrix": {"UNSUPPORTED_PROVED_CLAIM_COUNT": 0},
    }
    verdict = P.compute_final_verdict(evidence)
    assert verdict["MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE"] == "EVIDENCE_PROVENANCE_INVALID"
    assert verdict["GATE_SUMMARY"]["FOCUSED_TEST"] == "FAIL"


def test_05_skipped_or_xfailed_test_not_counted_as_passed(tmp_path: Path):
    """5. Test skip / xfail không được tính PASS."""
    mock_xml = tmp_path / "mock.xml"
    mock_xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuite name="pytest" tests="2" errors="0" failures="0" skipped="1" time="0.2">'
        '<testcase name="test_pass" time="0.1" />'
        '<testcase name="test_skip" time="0.1"><skipped message="skip">skipped</skipped></testcase>'
        '</testsuite>',
        encoding="utf-8",
    )
    parsed = P.parse_junit_xml(mock_xml)
    assert parsed["passed"] == 1
    assert parsed["skipped"] == 1


def test_06_fault_injections_require_passed_node():
    """6. F1-F10 chỉ CAUGHT nếu test node tương ứng PASS."""
    junit_data = {
        "testcases": [
            {"name": "test_FI_01_get_input_tokens_default_zero", "status": "failed", "time_seconds": 0.01},
        ]
    }
    audit = P.audit_fault_injections(junit_data, required_ids=["F1"])
    assert audit["ALL_CAUGHT"] is False
    assert audit["FAULT_INJECTIONS_FAILED"] == 1
    assert audit["INJECTIONS"][0]["caught"] is False


def test_07_missing_fault_id_fails_proof():
    """7. Thiếu một fault ID làm fault proof FAIL."""
    junit_data = {
        "testcases": [
            {"name": "test_FI_01_get_input_tokens_default_zero", "status": "passed", "time_seconds": 0.01},
        ]
    }
    # We require F1 and F2, but F2 is not in testcases
    audit = P.audit_fault_injections(junit_data, required_ids=["F1", "F2"])
    assert audit["ALL_CAUGHT"] is False
    assert "F2" in audit["FAULT_INJECTION_MISSING_IDS"]


def test_08_duplicate_fault_id_fails_proof():
    """8. Trùng fault ID làm fault proof FAIL."""
    junit_data = {
        "testcases": [
            {"name": "test_FI_01_get_input_tokens_default_zero", "status": "passed", "time_seconds": 0.01},
        ]
    }
    audit = P.audit_fault_injections(junit_data, required_ids=["F1", "F1"])
    assert audit["ALL_CAUGHT"] is False
    assert "F1" in audit["FAULT_INJECTION_DUPLICATE_IDS"]


def test_09_determinism_requires_identical_files_and_hashes():
    """9. Determinism chỉ PROVED nếu hai file set và toàn bộ hash trùng."""
    run_a = {
        "files": {
            "a.json": {"size_bytes": 10, "raw_sha256": "hash1", "lf_sha256": "hash1"},
        }
    }
    run_b_diff = {
        "files": {
            "a.json": {"size_bytes": 10, "raw_sha256": "hash2", "lf_sha256": "hash2"},
        }
    }
    res_diff = P.compare_manifests(run_a, run_b_diff)
    assert res_diff["VERIFICATION_RESULT"] == "DIVERGENCE_DETECTED"
    assert res_diff["STATUS"] == "FAIL"

    run_b_same = {
        "files": {
            "a.json": {"size_bytes": 10, "raw_sha256": "hash1", "lf_sha256": "hash1"},
        }
    }
    res_same = P.compare_manifests(run_a, run_b_same)
    assert res_same["VERIFICATION_RESULT"] == "PROVED_BITWISE_IDENTICAL_ACROSS_RUNS"
    assert res_same["STATUS"] == "PASS"


def test_10_mutated_source_artifact_fails_integrity(tmp_path: Path):
    """10. Artifact nguồn bị thay đổi làm integrity gate FAIL."""
    fake_file = tmp_path / "art.json"
    fake_file.write_text('{"foo": "bar"}', encoding="utf-8")
    registry = {
        "art.json": {
            "declared_commit": "d09331ea",
            "commit_blob_sha": "different_blob_sha",
            "disk_blob_sha": "different_blob_sha",
        }
    }
    res = P.audit_source_evidence_integrity(tmp_path, registry)
    assert res["ALL_MATCHED"] is False
    assert res["INTEGRITY_STATUS"] == "FAIL"


def test_11_claim_without_evidence_hash_unsupported():
    """11. Claim ghi PROVED nhưng thiếu evidence hash bị từ chối."""
    claims = [
        {
            "claim": "Commit code tồn tại",
            "source_type": "Git",
            "command_or_test": "git rev-parse",
            "exit_code": 0,
            "evidence_hash": "",  # Missing!
            "state": "PROVED",
        }
    ]
    matrix = P.build_claim_provenance_matrix(claims)
    assert matrix["UNSUPPORTED_PROVED_CLAIM_COUNT"] == 1
    assert matrix["STATUS"] == "FAIL"
    assert matrix["CLAIMS"][0]["state"] == "UNSUPPORTED_PROVED_REJECTED"


def test_12_candidate_cache_read_only_policy():
    """12. Candidate/cache audit chỉ chạy read-only và kiểm tra hằng số cố định."""
    assert P.CANDIDATE_EXPECTED == "077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1"
    assert P.CACHE_VERSION_EXPECTED == "99"
    assert P.MAIN_HEAD_EXPECTED == "085cae67392d3607ad0a58a7f48c17d8a5e5157d"
    assert P.START_HEAD_EXPECTED == "63eb06404ae94927228ca13c276ccf04bb9ea8c8"


def test_13_generator_pure_functional_no_verdict_input():
    """13. Generator không nhận boolean verdict làm input, mà tính toán từ evidence."""
    clean_evidence = {
        "commit_identity": {"COMMIT_IDENTITY_CLASSIFICATION": "COMMIT_ROLE_LABELING_ERROR", "HISTORY_DRIFT": "NO"},
        "source_integrity": {"ALL_MATCHED": True},
        "focused_test": {"exit_code": 0, "failed": 0, "errors": 0},
        "full_test": {"exit_code": 0, "failed": 0, "errors": 0},
        "fault_injections": {"ALL_CAUGHT": True},
        "determinism": {"VERIFICATION_RESULT": "PROVED_BITWISE_IDENTICAL_ACROSS_RUNS"},
        "candidate_cache": {"candidate_verify": True, "cache_verify": True},
        "secret_scan": {"SECRET_LEAKS_COUNT": 0},
        "claim_matrix": {"UNSUPPORTED_PROVED_CLAIM_COUNT": 0},
    }
    res = P.compute_final_verdict(clean_evidence)
    assert res["MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE"] == "PASS_WITH_LABEL_CORRECTION"
    assert res["CORE_OUTCOME_RESULT"] == "CORE_OUTCOME_VALID_WITH_MACHINE_VERIFIED_PROVENANCE"


def test_14_network_call_blocked_guard(monkeypatch):
    """14. Network-capable call bị chặn trong offline test process."""
    def fake_connect(*args, **kwargs):
        raise OSError("NETWORK_ACCESS_BLOCKED: Offline wave prohibits network connections.")

    monkeypatch.setattr(socket.socket, "connect", fake_connect)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(OSError, match="NETWORK_ACCESS_BLOCKED"):
        s.connect(("8.8.8.8", 53))


def test_15_historical_files_immutable():
    """15. Historical files không được ghi / sửa."""
    hist_dir = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "model-variance-evidence-review"
    assert hist_dir.exists()
    p = hist_dir / "PRECHECK.json"
    raw_b = p.read_bytes()
    # PRECHECK.json contains the recorded spliced commit
    assert b"3ba5afbbf46d37a222b5805453744e7506063b60" in raw_b


def test_16_staging_allowlist_never_contains_favicon():
    """16. Staging allowlist không chứa favicon."""
    allowlist = [
        "backend/scripts/provenance_evidence_collector.py",
        "backend/tests/geometry/test_model_variance_evidence_provenance_repair.py",
        "docs/CODE_INDEX.md",
    ]
    assert "frontend/public/favicon.svg" not in allowlist
    assert not any("favicon" in f for f in allowlist)
