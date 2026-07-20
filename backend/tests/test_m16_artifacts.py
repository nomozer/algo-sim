# -*- coding: utf-8 -*-
"""M16 Task 6 (W6) — sync-lock 5 artifact JSON (docs/evaluation/m16/) so với
builder thật (`app.evaluation.m16_artifacts`). Tiền lệ: `test_capability_
descriptors.py` (M14 §C4) — regenerate-and-compare, lệch = quên chạy
`scripts/generate_m16_artifacts.py`. Nguồn yêu cầu:
.superpowers/sdd/m16-task-6-brief.md.

`run_offline_and_build_all()` tự monkeypatch `pipeline.call_gemini` thủ công
(gán attribute + khôi phục `finally`) — KHÔNG cần fixture `monkeypatch` ở đây;
guard mạng conftest (autouse) vẫn bảo vệ suốt (0 API call thật)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.evaluation.m16_artifacts import run_offline_and_build_all
from app.evaluation.m16_schema import M16_DATASET_VERSION

_DIR = Path(__file__).resolve().parents[2] / "docs/evaluation/m16"

# key (data trả về run_offline_and_build_all()) → tên file JSON commit.
_FILES: dict[str, str] = {
    "case_matrix": "m16-case-matrix.json",
    "coverage_report": "m16-coverage-report.json",
    "offline_results": "m16-offline-results.json",
    "metrics": "m16-metrics.json",
    "failure_ledger": "m16-failure-ledger.json",
}

_ERR_HINT = "chạy lại scripts/generate_m16_artifacts.py"


@pytest.fixture(scope="module")
def artifacts() -> dict:
    return run_offline_and_build_all()


@pytest.fixture(scope="module")
def committed() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for key, filename in _FILES.items():
        path = _DIR / filename
        assert path.exists(), f"thiếu file {path} — {_ERR_HINT}"
        out[key] = json.loads(path.read_text(encoding="utf-8"))
    return out


# ── schema: mọi file đủ schema_version/dataset_version/run_label/run_meta{2 key} ──
def test_5_file_dung_schema_top_level(committed):
    for key, payload in committed.items():
        assert payload["schema_version"] == "1", key
        assert payload["dataset_version"] == M16_DATASET_VERSION, key
        assert payload["run_label"] == "offline", key
        assert set(payload["run_meta"].keys()) == {"git_commit", "generated_at"}, key
        assert "data" in payload, key


# ── sync-lock: bỏ run_meta (2 field volatile) rồi so bằng builder chạy lại ──
def test_sync_lock_regenerate_and_compare(artifacts, committed):
    for key, filename in _FILES.items():
        committed_payload = dict(committed[key])
        committed_payload.pop("run_meta")
        regenerated_payload = {
            "schema_version": "1",
            "dataset_version": M16_DATASET_VERSION,
            "run_label": "offline",
            "data": artifacts[key],
        }
        assert committed_payload == regenerated_payload, f"{filename} lệch với builder thật — {_ERR_HINT}"


# ── nội dung tối thiểu từng artifact (đối chiếu trực tiếp builder, không đoán) ──
def test_case_matrix_du_50_case_va_referenced_cases(artifacts):
    data = artifacts["case_matrix"]
    assert len(data["cases"]) == 50
    assert len(data["referenced_cases"]) > 0
    ids = [c["case_id"] for c in data["cases"]]
    assert len(ids) == len(set(ids))  # unique
    first = data["cases"][0]
    assert set(first.keys()) == {
        "case_id", "group", "archetype", "expected_family", "curriculum_area",
        "result_mode", "complexity", "expected_initial_route", "expected_final_route",
        "expected_gate", "expected_error_code", "analyze_mechanism_expected",
        "algorithmic_request", "recovery_route_exists", "live_eligible", "tags",
    }


def test_coverage_report_locks_dung_thuc_te(artifacts):
    locks = artifacts["coverage_report"]["locks"]
    assert locks["total_cases"] == 50
    assert locks["targets_covered"] == "14/14"
    assert locks["families_boundary"] == "8/8"
    assert locks["families_near_miss"] == "8/8"
    assert locks["live_eligible_count"] > 0


def test_offline_results_50_record_dung_thu_tu_pool(artifacts):
    data = artifacts["offline_results"]
    assert isinstance(data, list)
    assert len(data) == 50
    assert data[0]["case_id"] == "m16-findmax-explicit"


def test_metrics_hard_correctness_khop_test_5(artifacts):
    hc = artifacts["metrics"]["hard_correctness"]
    assert hc["false_positive_simulation"].endswith("/9")
    assert hc["false_positive_simulation"].startswith("0/")
    assert hc["generic_fallback_leak"].startswith("0/")
    assert hc["concrete_envelope_integrity"] != "0/0"
    assert hc["production_evaluation_parity"] == "50/50"
    assert hc["selector_token_in_envelope"] is False
    assert hc["frozen_fingerprint_ok"] is True


def test_failure_ledger_3_injected_proofs_tu_code_that(artifacts):
    proofs = artifacts["failure_ledger"]["injected_proofs"]
    assert len(proofs) == 3
    all_names = {n for p in proofs for n in p["test_names"]}
    assert "test_fault_false_refusal_bi_metric_8_bat" in all_names
    assert "test_fault_leak_metric_12_nhay_khi_gate_hut" in all_names
    assert "test_fault_transient_tach_kenh_retry" in all_names
    for p in proofs:
        assert p["injected"] is True
    for case in artifacts["failure_ledger"]["cases"]:
        assert case["injected"] is False
        assert len(case["categories"]) >= 1
