"""M14 Task 3 — sync-lock capability-descriptors.json (§C4): đổi metadata mà quên
chạy generate_capability_descriptors.py → test ĐỎ (khuôn dsl-contract.json)."""

from __future__ import annotations

import json
from pathlib import Path

from app.simulation.catalog import capability_descriptors

_JSON = (
    Path(__file__).resolve().parents[2]
    / "frontend/src/simulations/capability-descriptors.json"
)


def test_descriptor_json_khong_troi_khoi_nguon():
    committed = json.loads(_JSON.read_text(encoding="utf-8"))
    assert committed == capability_descriptors()


def test_cau_truc_co_ban():
    d = capability_descriptors()
    assert len(d["runtime_targets"]) == 14
    assert "comparison_sort" in d["family_selectors"]
    token = d["family_selectors"]["comparison_sort"]["selector_token"]
    # token selector KHÔNG được là một runtime target
    assert token not in d["runtime_targets"]
    assert token in d["llm_choices"]
    assert "algorithm.bubble_sort" not in d["llm_choices"]
