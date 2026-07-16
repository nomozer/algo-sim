# -*- coding: utf-8 -*-
"""M12 — định tuyến NL cho algorithm.scan (mock, offline).

Khóa các bất biến (khuôn test_encap_routing):
- CATALOG đăng ký algorithm.scan; enum classify DẪN XUẤT từ CATALOG;
- schema Gemini của scan DẪN XUẤT từ hằng scan_engine (anti-pattern #1);
- validator R0: từ chối khóa engine-owned + spec sai; nhận spec đúng;
- classify.md mang ranh giới: scan CHỈ cho biến thể ngoài bài chuyên biệt,
  ưu tiên chuyên biệt khi khớp, vòng lặp biến tự do vẫn unsupported;
- e2e mock: đề tiếng Việt "tìm phần tử đầu tiên vượt ngưỡng" → envelope scan.
"""

import asyncio
import json

from app.ai import pipeline
from app.simulation.catalog import CATALOG, catalog_text
from app.simulation.scan_engine import CONDITION_OPS, MARKINGS, STOPS, UPDATE_KINDS
from app.validation.simulation import validate_scan_config

SCAN_ID = "algorithm.scan"

SCAN_ANALYSIS = {
    "objects": ["dãy nhiệt độ", "ngưỡng 35"],
    "data": [{"description": "nhiệt độ các ngày", "values": [32, 31, 36, 30, 37], "labels": []}],
    "relations": [],
    "processes": ["duyệt lần lượt", "dừng khi gặp ngày đầu tiên vượt ngưỡng"],
    "constraints": [],
    "goal": "Tìm ngày đầu tiên có nhiệt độ vượt 35 độ",
    "input_description": "Dãy nhiệt độ 5 ngày",
    "output_description": "Vị trí ngày đầu tiên vượt ngưỡng",
    "notes": None,
}

GOOD_SPEC = {
    "scan_version": "1.0",
    "array": [32, 31, 36, 30, 37],
    "seed": {"from": "constant", "value": 35, "varName": "nguong"},
    "compare": {"kind": "to_constant", "op": ">", "value": 35},
    "update": {"kind": "none"},
    "marking": "match_highlight",
    "stop": "first_match",
}


def _fake_gemini(responses: list[str]):
    calls: list[dict] = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        calls.append({"system": system_prompt, "user": user_text, "schema": response_schema})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


# ── 1. Catalog + schema dẫn xuất ──────────────────────────────

def test_catalog_dang_ky_scan():
    assert SCAN_ID in CATALOG
    spec = CATALOG[SCAN_ID]
    assert spec.domain == "algorithm"
    assert "engine" in spec.contract or "interpreter" in spec.contract
    assert "KHÔNG" in spec.contract  # R0 nói tường minh trong hợp đồng


def test_scan_schema_enum_dan_xuat_tu_scan_engine():
    """Enum trong structured output phải TRÙNG hằng của scan_engine — một
    nguồn; enum viết tay từng làm Gemini không thể phát giá trị mới."""
    props = CATALOG[SCAN_ID].config_schema["properties"]
    assert props["compare"]["properties"]["op"]["enum"] == list(CONDITION_OPS)
    assert props["update"]["properties"]["kind"]["enum"] == list(UPDATE_KINDS)
    assert props["marking"]["enum"] == list(MARKINGS)
    assert props["stop"]["enum"] == list(STOPS)


def test_classify_schema_enum_co_scan():
    enum = pipeline._classify_schema()["properties"]["simulation_id"]["enum"]
    assert SCAN_ID in enum
    assert "algorithm.linear_search" in enum  # bài chuyên biệt còn nguyên


# ── 2. Ranh giới ngữ nghĩa trong DATA đưa vào prompt ──────────

def test_catalog_text_mang_ranh_gioi_scan():
    text = catalog_text()
    assert "ĐẦU TIÊN" in text  # phân biệt với linear_search (so bằng)
    assert "chuyên biệt" in text


def test_classify_skill_co_quy_tac_scan():
    from app.ai.gemini import load_skill

    skill = load_skill("classify")
    assert "algorithm.scan" in skill
    assert "BIẾN TỰ DO" in skill or "biến tự do" in skill  # loop-gap M11 giữ nguyên


# ── 3. Validator R0 ───────────────────────────────────────────

def test_validate_scan_config_chan_khoa_engine_owned():
    bad = {**GOOD_SPEC, "steps": [{"i": 0}]}
    cfg, err = validate_scan_config(bad)
    assert cfg is None
    assert "steps" in err or "khóa" in err.lower()


def test_validate_scan_config_nhan_spec_dung():
    cfg, err = validate_scan_config(GOOD_SPEC)
    assert err is None
    assert cfg["stop"] == "first_match"


# ── 4. E2E mock: đề tiếng Việt → envelope algorithm.scan ──────

def test_pipeline_e2e_mock_ra_envelope_scan(monkeypatch):
    responses = [
        json.dumps(SCAN_ANALYSIS),
        json.dumps({"status": "ok", "simulation_id": SCAN_ID, "reason": "quét một lượt, dừng ở phần tử đầu thỏa bất đẳng thức"}),
        json.dumps(GOOD_SPEC),
    ]
    fake, calls = _fake_gemini(responses)
    monkeypatch.setattr(pipeline, "call_gemini", fake)

    envelope = asyncio.run(
        pipeline.run_pipeline(
            "Nhiệt độ 5 ngày là 32, 31, 36, 30, 37 độ. Tìm ngày đầu tiên có nhiệt độ vượt 35 độ.",
            api_key="x",
        )
    )
    assert envelope["status"] == "ok"
    assert envelope["simulation_id"] == SCAN_ID
    assert envelope["config"]["stop"] == "first_match"
    # LLM không sinh timeline/kết quả — config chỉ là cấu hình khai báo
    assert "steps" not in envelope["config"]
    assert "timeline" not in envelope["config"]
