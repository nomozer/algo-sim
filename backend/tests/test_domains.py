# -*- coding: utf-8 -*-
"""Test 3 domain mới M5: validator + catalog + classify.

Khóa chặt (§6): config KHÔNG được chứa timeline/state/frames — engine tự sinh.
"""

import json

import pytest

from app.ai import pipeline
from app.simulation.catalog import CATALOG, catalog_text
from app.validation.simulation import (
    validate_binary_config,
    validate_logic_config,
    validate_network_config,
)

NET_CONFIG = {
    "nodes": [
        {"id": "client", "type": "client"},
        {"id": "router", "type": "router"},
        {"id": "server", "type": "server"},
    ],
    "links": [["client", "router"], ["router", "server"]],
    "source": "client",
    "destination": "server",
}


# ── catalog ───────────────────────────────────────────────────

def test_catalog_co_3_sim_moi():
    for sim_id in ("logic.and_gate", "binary.decimal_to_binary", "network.packet_routing"):
        assert sim_id in CATALOG
    text = catalog_text()
    assert "logic.and_gate" in text
    assert "binary.decimal_to_binary" in text
    assert "network.packet_routing" in text


def test_moi_enum_trong_schema_chi_la_string():
    """M7.6 §1: Gemini structured output chỉ nhận enum kiểu STRING.
    enum kiểu số (như [0,1] trên INTEGER) gây HTTP 400 — invariant chống tái phát."""

    def walk(node, path):
        if isinstance(node, dict):
            if "enum" in node:
                for v in node["enum"]:
                    assert isinstance(v, str), f"{path}: enum có giá trị không phải STRING: {v!r}"
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    for sim_id, spec in CATALOG.items():
        walk(spec.config_schema, sim_id)


# ── logic ─────────────────────────────────────────────────────

def test_logic_config_hop_le():
    config, err = validate_logic_config({"inputA": 1, "inputB": 0})
    assert err is None
    assert config == {"inputA": 1, "inputB": 0, "notes": None}


def test_logic_config_sai_bi_reject():
    assert validate_logic_config({"inputA": 2, "inputB": 0})[0] is None
    assert validate_logic_config({"inputA": 1})[0] is None


def test_logic_khong_nhan_output_tu_llm():
    """§6: config không được mang output/state — chỉ đầu vào."""
    config, err = validate_logic_config({"inputA": 1, "inputB": 1, "state": {"output": 1}})
    assert config is None
    assert "engine" in err.lower() or "cấm" in err


# ── binary ────────────────────────────────────────────────────

def test_binary_config_hop_le_va_noi_bit():
    config, err = validate_binary_config({"decimalValue": 13, "bitWidth": 2})
    assert err is None
    assert config["decimalValue"] == 13
    assert config["bitWidth"] == 4  # tự nới đủ chứa 13
    assert "tăng số bit" in (config["notes"] or "")


def test_binary_config_sai_bi_reject():
    assert validate_binary_config({"decimalValue": -1, "bitWidth": 4})[0] is None
    assert validate_binary_config({"decimalValue": 5, "bitWidth": 0})[0] is None
    assert validate_binary_config({"decimalValue": 300, "bitWidth": 8})[0] is None


def test_binary_khong_nhan_bits_tu_llm():
    config, err = validate_binary_config({"decimalValue": 5, "bitWidth": 4, "bits": [0, 1, 0, 1]})
    # "bits" không nằm trong FORBIDDEN nhưng cũng bị bỏ qua (không vào config).
    # Còn "state"/"frames" thì bị chặn:
    config2, err2 = validate_binary_config({"decimalValue": 5, "bitWidth": 4, "frames": []})
    assert config2 is None
    assert "engine" in err2.lower() or "cấm" in err2
    # config hợp lệ vẫn chỉ có decimal/bitWidth
    assert config is not None
    assert set(config.keys()) == {"decimalValue", "bitWidth", "notes"}


# ── network ───────────────────────────────────────────────────

def test_network_config_hop_le():
    config, err = validate_network_config(NET_CONFIG)
    assert err is None
    assert config["source"] == "client"
    assert len(config["nodes"]) == 3


def test_network_khong_duong_di_bi_reject():
    bad = {**NET_CONFIG, "links": [["client", "router"]]}  # server cô lập
    config, err = validate_network_config(bad)
    assert config is None
    assert "đường đi" in err


def test_network_link_sai_bi_reject():
    bad = {**NET_CONFIG, "links": [["client", "khong-ton-tai"]]}
    assert validate_network_config(bad)[0] is None


def test_network_khong_nhan_timeline_tu_llm():
    """§6: mấu chốt — network config KHÔNG được chứa timeline. Engine BFS tự dựng."""
    bad = {**NET_CONFIG, "timeline": [{"step": 1}]}
    config, err = validate_network_config(bad)
    assert config is None
    assert "engine" in err.lower() or "cấm" in err


# ── classify chọn đúng sim mới (pipeline mock) ─────────────────

def _fake_gemini(responses):
    calls = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        calls.append(user_text)
        return responses.pop(0)

    return fake, calls


def test_classify_chon_dung_logic_and_gate(monkeypatch):
    import asyncio

    analysis = {
        "objects": ["cổng AND"],
        "data": [],
        "relations": [],
        "processes": ["xét đầu ra"],
        "constraints": [],
        "goal": "Khi nào cổng AND ra 1",
        "input_description": "Hai đầu vào",
        "output_description": "Đầu ra cổng AND",
        "notes": None,
    }
    fake, calls = _fake_gemini(
        [
            json.dumps(analysis),
            json.dumps({"status": "ok", "simulation_id": "logic.and_gate", "reason": None}),
            json.dumps({"inputA": 0, "inputB": 0}),
        ]
    )
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    env = asyncio.run(pipeline.run_pipeline("Khi nào cổng AND có đầu ra bằng 1?", "khoa-gia"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "logic.and_gate"
    assert env["domain"] == "logic"
    assert env["config"] == {"inputA": 0, "inputB": 0, "notes": None}
    # danh mục trong prompt classify phải chứa sim mới
    assert "logic.and_gate" in calls[1]
