# -*- coding: utf-8 -*-
"""M17-Lite W0 — FROZEN LOCK 6 artifact docs/evaluation/m17/wave0/.

Wave 0 đã CLOSEOUT (user duyệt, phương án (a) — xem PROVENANCE.md): artifact
wave0 là bản ghi LỊCH SỬ của trạng thái catalog TẠI Wave 0 (14 target,
4 intentional gap). Từ Wave 1 catalog thay đổi (selection_sort owned, v.v.)
nên KHÔNG còn regenerate-so-khớp (kiểu sync-lock sống) — thay bằng PIN
SHA-256 (tiền lệ frozen fingerprint M16): sửa một byte data → đỏ.

Artifact wave MỚI (wave1, ...) có sync-lock sống riêng của nó.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17" / "wave0"

# PIN nội dung (data JSON canonical sort_keys / MD nguyên văn) — đóng băng khi
# user duyệt closeout W0 (commit 42f472b). KHÔNG bao giờ cập nhật trừ khi user
# phê duyệt tường minh việc sửa bản ghi lịch sử.
_JSON_PINS = {
    "authenticity_results.json": "6d40d580a6808028e014f2874d718bda3df156aa0e227ab25e0671b17a6a69e9",
    "authenticity_metrics.json": "d164f1d6c120d469d273373d1bf56a3ce57b4a39350e940858bd63f366a858c3",
    "generic_leak_ledger.json": "6f56485ac353a50a18b61f070ba43ad2a3e585026d5c9e94c791835e5bb03938",
    "curriculum_coverage.json": "434e8217a4b9f5670be825723700c3ed4219e077b13c212d9c1538f101c00fb2",
}
_MD_PINS = {
    "simulation_authenticity_report.md": "fe31b710d52d86472018adf7e5a18140fa573410fa0b2fec4581ea9807097383",
    "curriculum_gap_report.md": "7d2a0167f3e30caa95c559928a1dcea58693c0bbc462dd372041bf56fc0f2ef4",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_cau_truc_payload_json():
    for name in _JSON_PINS:
        payload = json.loads((_DIR / name).read_text(encoding="utf-8"))
        assert payload["schema_version"] == "1", name
        assert payload["run_label"] == "wave0-offline", name
        assert set(payload["run_meta"].keys()) == {"git_commit", "generated_at"}, name
        assert "data" in payload, name


def test_frozen_pin_json_data():
    for name, pin in _JSON_PINS.items():
        data = json.loads((_DIR / name).read_text(encoding="utf-8"))["data"]
        got = _sha(json.dumps(data, ensure_ascii=False, sort_keys=True))
        assert got == pin, f"{name}: data lịch sử W0 bị sửa (pin {pin[:12]}…, got {got[:12]}…)"


def test_frozen_pin_markdown():
    for name, pin in _MD_PINS.items():
        got = _sha((_DIR / name).read_text(encoding="utf-8"))
        assert got == pin, f"{name}: nội dung lịch sử W0 bị sửa"


def test_leak_ledger_dung_3_quan_sat_lich_su():
    entries = json.loads(
        (_DIR / "generic_leak_ledger.json").read_text(encoding="utf-8")
    )["data"]["entries"]
    verdicts = {e["case_id"]: e["verdict"] for e in entries}
    assert verdicts == {
        "aud-leak-dijkstra": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-honest": "BLOCKED_FAIL_CLOSED",
        "aud-regression-tree-adversarial": "CONDITIONAL_LEAK_CONFIRMED",
    }
