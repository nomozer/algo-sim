# -*- coding: utf-8 -*-
"""PIN SHA-256 của bằng chứng LỊCH SỬ thời Tin học — `docs/evaluation/m17/wave0/` và `docs/evaluation/m17/wave1/`.

repo-cleanup: gộp `test_m17_wave0_artifacts.py` + `test_m17_wave1_artifacts.py` (tên chỉ mang mã lượt) vào một file
nói đúng việc nó làm. Mọi pin và mọi khẳng định giữ NGUYÊN; tên thư mục `m17/wave0`, `m17/wave1` là danh tính của bằng
chứng đã phát hành (`docs/evaluation/RUN_NAMING.md`), không đổi.

Hai bản ghi là trạng thái catalog Tin học TẠI Wave 0 (14 target, 4 intentional gap — user duyệt closeout, phương án
(a), PROVENANCE.md, commit 42f472b) và TẠI Wave 1 (18 target, 2 gap còn lại: quicksort partition + Dijkstra weighted).
Catalog ấy đã gỡ, nên không còn regenerate-so-khớp — chỉ PIN: sửa một byte data → đỏ. KHÔNG bao giờ cập nhật pin trừ
khi user phê duyệt tường minh việc sửa bản ghi lịch sử.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_M17 = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17"

_PINS = {
    "wave0": {
        "json": {
            "authenticity_results.json": "6d40d580a6808028e014f2874d718bda3df156aa0e227ab25e0671b17a6a69e9",
            "authenticity_metrics.json": "d164f1d6c120d469d273373d1bf56a3ce57b4a39350e940858bd63f366a858c3",
            "generic_leak_ledger.json": "6f56485ac353a50a18b61f070ba43ad2a3e585026d5c9e94c791835e5bb03938",
            "curriculum_coverage.json": "434e8217a4b9f5670be825723700c3ed4219e077b13c212d9c1538f101c00fb2",
        },
        "md": {
            "simulation_authenticity_report.md": "fe31b710d52d86472018adf7e5a18140fa573410fa0b2fec4581ea9807097383",
            "curriculum_gap_report.md": "7d2a0167f3e30caa95c559928a1dcea58693c0bbc462dd372041bf56fc0f2ef4",
        },
    },
    "wave1": {
        "json": {
            "authenticity_results.json": "3ead1bc89ca43ebbe9e7766025e8271f6accbc0d5da9cae681609db14342c9ad",
            "authenticity_metrics.json": "2baabcc0b22975c1778ad95a0fc72a0d57fe90b907949cb9aa2186e243557df8",
            "generic_leak_ledger.json": "6f56485ac353a50a18b61f070ba43ad2a3e585026d5c9e94c791835e5bb03938",
            "curriculum_coverage.json": "2b043fa8e0858e7ce9e6ce5b57f8a165a1f8679d49f6ebe9b5870faed3f42f74",
        },
        "md": {
            "simulation_authenticity_report.md": "2421981d64e5b7ba71a761bb3fe76faaef322975349937e84a67cb47860832fc",
            "curriculum_gap_report.md": "4c3e908102a73fc8ff427829b9c2b175e7d76cc16eef26abfb9af92b13afc2f5",
        },
    },
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _data(snapshot: str, name: str) -> dict:
    return json.loads((_M17 / snapshot / name).read_text(encoding="utf-8"))["data"]


def test_cau_truc_payload_json():
    for snapshot, pins in _PINS.items():
        for name in pins["json"]:
            payload = json.loads((_M17 / snapshot / name).read_text(encoding="utf-8"))
            assert payload["schema_version"] == "1", (snapshot, name)
            assert payload["run_label"] == f"{snapshot}-offline", (snapshot, name)
            assert set(payload["run_meta"].keys()) == {"git_commit", "generated_at"}, (snapshot, name)
            assert "data" in payload, (snapshot, name)


def test_frozen_pin_json_data():
    for snapshot, pins in _PINS.items():
        for name, pin in pins["json"].items():
            got = _sha(json.dumps(_data(snapshot, name), ensure_ascii=False, sort_keys=True))
            assert got == pin, f"{snapshot}/{name}: data lịch sử bị sửa (pin {pin[:12]}…, got {got[:12]}…)"


def test_frozen_pin_markdown():
    for snapshot, pins in _PINS.items():
        for name, pin in pins["md"].items():
            got = _sha((_M17 / snapshot / name).read_text(encoding="utf-8"))
            assert got == pin, f"{snapshot}/{name}: nội dung lịch sử bị sửa"


def test_wave0_leak_ledger_dung_3_quan_sat_lich_su():
    entries = _data("wave0", "generic_leak_ledger.json")["entries"]
    verdicts = {e["case_id"]: e["verdict"] for e in entries}
    assert verdicts == {
        "aud-leak-dijkstra": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-honest": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-adversarial": "CONDITIONAL_LEAK_CONFIRMED",
    }


# ── invariant đọc-được của Wave 1 (bổ trợ pin, không mâu thuẫn) ──
def test_wave1_metric_invariants():
    m = _data("wave1", "authenticity_metrics.json")
    assert m["total_cases"] == 68  # 18 target × ~3–4 archetype + 2 near-miss + 5 control
    assert m["generic_leak"]["unconditional_leaks"] == 0
    # near-miss chỉ còn 2 cơ chế comparison_sort còn gap
    assert m["near_miss_gap_recall"]["numerator"] == m["near_miss_gap_recall"]["denominator"] == 2
    assert m["false_refusal_on_ok_archetypes"] == 0
    assert m["classification_histogram"] == {"REAL": 17, "PARTIAL": 1}


def test_wave1_leak_ledger_conditional_van_pin_probe():
    entries = _data("wave1", "generic_leak_ledger.json")["entries"]
    verdicts = {e["case_id"]: e["verdict"] for e in entries}
    # probe adversarial duyệt cây VẪN CONDITIONAL_LEAK (tree_traversal là Wave 2)
    assert verdicts["aud-regression-tree-adversarial"] == "CONDITIONAL_LEAK_CONFIRMED"
    assert verdicts["aud-regression-tree-honest"] == "BLOCKED_FAIL_CLOSED"


def test_wave1_gap_flip_phan_anh_trong_coverage_artifact():
    verdicts = _data("wave1", "curriculum_coverage.json")["intentional_gap_verdicts"]
    # W1: hex & selection ĐÃ flip owned nên KHÔNG còn trong near-miss verdict.
    assert "positional_representation.non_binary_base" not in verdicts
    assert "comparison_sort.select_extreme_repeated" not in verdicts
    assert "comparison_sort.partition_recursive" in verdicts
