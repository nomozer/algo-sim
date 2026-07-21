# -*- coding: utf-8 -*-
"""M17-Lite W0 — sync-lock 6 artifact docs/evaluation/m17/wave0/.

Theo tiền lệ test_m16_artifacts.py: bỏ run_meta (2 field volatile) rồi so
`data` với builder chạy lại; 2 file markdown tất định (không timestamp) so
NGUYÊN VĂN. Artifact trôi khỏi nguồn → đỏ; chạy lại
`python scripts/generate_m17_wave0_artifacts.py` để tái sinh.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.evaluation.authenticity_artifacts import (
    build_authenticity_metrics,
    build_authenticity_report_md,
    build_authenticity_results,
    build_curriculum_coverage,
    build_gap_report_md,
    build_generic_leak_ledger_artifact,
    run_offline_audit,
)

_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17" / "wave0"
_ERR_HINT = "chạy: cd backend && .venv/Scripts/python.exe scripts/generate_m17_wave0_artifacts.py"

_JSON_FILES = (
    "authenticity_results.json",
    "authenticity_metrics.json",
    "generic_leak_ledger.json",
    "curriculum_coverage.json",
)
_MD_FILES = ("simulation_authenticity_report.md", "curriculum_gap_report.md")


@pytest.fixture(scope="module")
def records():
    return run_offline_audit()


@pytest.fixture(scope="module")
def committed():
    out = {}
    for name in _JSON_FILES:
        path = _DIR / name
        assert path.exists(), f"thiếu {path} — {_ERR_HINT}"
        out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


def test_cau_truc_payload(committed):
    for name, payload in committed.items():
        assert payload["schema_version"] == "1", name
        assert payload["run_label"] == "wave0-offline", name
        assert set(payload["run_meta"].keys()) == {"git_commit", "generated_at"}, name
        assert "data" in payload, name


def test_sync_lock_json(records, committed):
    rebuilt = {
        "authenticity_results.json": build_authenticity_results(records),
        "authenticity_metrics.json": build_authenticity_metrics(records),
        "generic_leak_ledger.json": build_generic_leak_ledger_artifact(records),
        "curriculum_coverage.json": build_curriculum_coverage(records),
    }
    for name in _JSON_FILES:
        # round-trip qua JSON để chuẩn hoá kiểu (tuple→list, v.v.)
        fresh = json.loads(json.dumps(rebuilt[name], ensure_ascii=False))
        assert committed[name]["data"] == fresh, f"{name} trôi khỏi nguồn — {_ERR_HINT}"


def test_sync_lock_markdown(records):
    fresh = {
        "simulation_authenticity_report.md": build_authenticity_report_md(records),
        "curriculum_gap_report.md": build_gap_report_md(records),
    }
    for name in _MD_FILES:
        path = _DIR / name
        assert path.exists(), f"thiếu {path} — {_ERR_HINT}"
        assert path.read_text(encoding="utf-8") == fresh[name], f"{name} trôi — {_ERR_HINT}"


def test_leak_ledger_dung_3_quan_sat(committed):
    entries = committed["generic_leak_ledger.json"]["data"]["entries"]
    verdicts = {e["case_id"]: e["verdict"] for e in entries}
    assert verdicts == {
        "aud-leak-dijkstra": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-honest": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-adversarial": "CONDITIONAL_LEAK_CONFIRMED",
    }
