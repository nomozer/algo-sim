# -*- coding: utf-8 -*-
"""M17-Lite W1 — FROZEN LOCK 6 artifact docs/evaluation/m17/wave1/.

Wave 1 CLOSEOUT: artifact wave1 là bản ghi LỊCH SỬ trạng thái catalog TẠI
Wave 1 (18 target, 2 intentional gap còn lại: quicksort partition + Dijkstra
weighted). Từ Wave 2 catalog lại thay đổi (tree_traversal, ...) nên KHÔNG
regenerate-so-khớp sống — PIN SHA-256 (tiền lệ wave0 + frozen fingerprint M16).
Sửa một byte data → đỏ. Wave sau có artifact + lock riêng.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17" / "wave1"

_JSON_PINS = {
    "authenticity_results.json": "3ead1bc89ca43ebbe9e7766025e8271f6accbc0d5da9cae681609db14342c9ad",
    "authenticity_metrics.json": "2baabcc0b22975c1778ad95a0fc72a0d57fe90b907949cb9aa2186e243557df8",
    "generic_leak_ledger.json": "6f56485ac353a50a18b61f070ba43ad2a3e585026d5c9e94c791835e5bb03938",
    "curriculum_coverage.json": "2b043fa8e0858e7ce9e6ce5b57f8a165a1f8679d49f6ebe9b5870faed3f42f74",
}
_MD_PINS = {
    "simulation_authenticity_report.md": "2421981d64e5b7ba71a761bb3fe76faaef322975349937e84a67cb47860832fc",
    "curriculum_gap_report.md": "4c3e908102a73fc8ff427829b9c2b175e7d76cc16eef26abfb9af92b13afc2f5",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _data(name: str) -> dict:
    return json.loads((_DIR / name).read_text(encoding="utf-8"))["data"]


def test_cau_truc_payload_json():
    for name in _JSON_PINS:
        payload = json.loads((_DIR / name).read_text(encoding="utf-8"))
        assert payload["schema_version"] == "1", name
        assert payload["run_label"] == "wave1-offline", name
        assert set(payload["run_meta"].keys()) == {"git_commit", "generated_at"}, name


def test_frozen_pin_json_data():
    for name, pin in _JSON_PINS.items():
        got = _sha(json.dumps(_data(name), ensure_ascii=False, sort_keys=True))
        assert got == pin, f"{name}: data lịch sử W1 bị sửa (pin {pin[:12]}…, got {got[:12]}…)"


def test_frozen_pin_markdown():
    for name, pin in _MD_PINS.items():
        got = _sha((_DIR / name).read_text(encoding="utf-8"))
        assert got == pin, f"{name}: nội dung lịch sử W1 bị sửa"


# ── invariant đọc-được (bổ trợ pin, không mâu thuẫn) ──
def test_metric_invariants_wave1():
    m = _data("authenticity_metrics.json")
    assert m["total_cases"] == 68  # 18 target × ~3–4 archetype + 2 near-miss + 5 control
    assert m["generic_leak"]["unconditional_leaks"] == 0
    # 2 intentional gap còn lại (quicksort partition + Dijkstra weighted đã bị
    # đưa vào near-miss? không — near-miss chỉ 2 cơ chế comparison_sort còn gap)
    assert m["near_miss_gap_recall"]["numerator"] == m["near_miss_gap_recall"]["denominator"] == 2
    assert m["false_refusal_on_ok_archetypes"] == 0
    assert m["classification_histogram"] == {"REAL": 17, "PARTIAL": 1}


def test_leak_ledger_conditional_van_pin_probe():
    entries = _data("generic_leak_ledger.json")["entries"]
    verdicts = {e["case_id"]: e["verdict"] for e in entries}
    # probe adversarial duyệt cây VẪN CONDITIONAL_LEAK (tree_traversal là Wave 2)
    assert verdicts["aud-regression-tree-adversarial"] == "CONDITIONAL_LEAK_CONFIRMED"
    assert verdicts["aud-regression-tree-honest"] == "BLOCKED_FAIL_CLOSED"


def test_gap_flip_phan_anh_trong_coverage_artifact():
    cov = _data("curriculum_coverage.json")
    verdicts = cov["intentional_gap_verdicts"]
    # W1: chỉ còn 2 cơ chế near-miss (comparison_sort partition + other) — hex &
    # selection ĐÃ flip owned nên KHÔNG còn trong near-miss verdict.
    assert "positional_representation.non_binary_base" not in verdicts
    assert "comparison_sort.select_extreme_repeated" not in verdicts
    assert "comparison_sort.partition_recursive" in verdicts
