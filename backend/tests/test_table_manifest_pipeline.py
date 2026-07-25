# -*- coding: utf-8 -*-
"""M17 W2B-PATCH2 §C/§D/§E — MERGE trong PRODUCTION `run_pipeline`.

Chứng minh sự cố live P2 nay được vá ĐẦU-CUỐI: LLM sinh spec BA tầng (đúng cái
đã thất bại live) → merge tất định bù limit+aggregate từ manifest → status=ok,
AVG 8.5. KHÔNG dựng pipeline mirror (bất biến #22): đi thẳng `run_pipeline`.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import _analysis, _classify, _table_cfg
from app.simulation.table_query_engine import run_table_query

TARGET = "database.relational_table_query"

_L4_SCHEMA = [
    {"name": "ten", "type": "text", "label": "Tên"},
    {"name": "to", "type": "text", "label": "Tổ"},
    {"name": "diem", "type": "number", "label": "Điểm"},
    {"name": "vang", "type": "number", "label": "Số buổi vắng"},
]
_L4_ROWS = [
    {"ten": "An", "to": "A", "diem": 9.0, "vang": 1},
    {"ten": "Bình", "to": "B", "diem": 8.5, "vang": 0},
    {"ten": "Chi", "to": "A", "diem": 6.0, "vang": 2},
    {"ten": "Dũng", "to": "A", "diem": 9.0, "vang": 0},
    {"ten": "Hà", "to": "B", "diem": 7.5, "vang": 3},
    {"ten": "Lan", "to": "A", "diem": 7.5, "vang": 1},
    {"ten": "Minh", "to": "A", "diem": 6.0, "vang": 0},
    {"ten": "Nga", "to": "B", "diem": 9.5, "vang": 2},
]
_L4_OBJECTS = ["bảng học sinh", "cột Tên", "cột Tổ", "cột Điểm", "cột Số buổi vắng"]
_L4_DATA = [
    {"description": "điểm các bạn", "values": [9.0, 8.5, 6.0, 9.0, 7.5, 7.5, 6.0, 9.5],
     "labels": ["An", "Bình", "Chi", "Dũng", "Hà", "Lan", "Minh", "Nga"]},
    {"description": "tổ", "labels": ["A", "B", "A", "A", "B", "A", "A", "B"]},
]
_GROUP = {"query_group": 1}
_L4_REQS = [
    {"operation": "relational_table_query:filter", **_GROUP,
     "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
    {"operation": "relational_table_query:projection", **_GROUP,
     "projection_columns": ["Tên", "Điểm"]},
    {"operation": "relational_table_query:sort", **_GROUP,
     "sort_column": "Điểm", "sort_direction": "desc"},
    {"operation": "relational_table_query:limit", **_GROUP, "limit": 3},
    {"operation": "relational_table_query:avg", **_GROUP,
     "aggregate_func": "avg", "aggregate_column": "Điểm"},
]
_ASK = ("Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học "
        "sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.")


def _an_l4():
    return json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal=_ASK),
        "requested_operations": sorted({r["operation"] for r in _L4_REQS}),
        "requested_requirements": _L4_REQS,
    }, ensure_ascii=False)


def _run(monkeypatch, responses, text=_ASK):
    q = list(responses)

    async def fake(api_key, system_prompt, user_text, response_schema=None,
                   temperature=0.2, image=None):
        assert q, "gọi nhiều hơn scripted"
        return q.pop(0)

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


# LLM sinh BA tầng (đúng cái đã thất bại live P2): filter+projection+sort.
_THREE_STAGE = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                          filter={"op": "=", "column": "to", "value": "A"},
                          projection=["ten", "diem"],
                          sort={"column": "diem", "direction": "desc"})


def test_P2_ba_tang_LLM_duoc_merge_thanh_nam_tang_chay_dung(monkeypatch):
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), _THREE_STAGE])
    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    cfg = env["config"]
    # merge đã bù limit + aggregate
    assert cfg["limit"] == 3
    assert cfg["aggregate"] == {"func": "avg", "column": "diem"}
    out = run_table_query(cfg)
    assert [r["ten"] for r in out["result_rows"]] == ["An", "Dũng", "Lan"]
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3
    for leak in ("aggregateResult", "result_rows", "ordered_indices", "steps"):
        assert leak not in cfg


def test_P2_merge_khong_ton_them_luot_simulate(monkeypatch):
    """Merge tất định ⇒ MỘT lượt simulate là đủ (không còn 3 lượt như live)."""
    calls = {"n": 0}

    async def fake(api_key, system_prompt, user_text, response_schema=None,
                   temperature=0.2, image=None):
        calls["n"] += 1
        return [_an_l4(), json.dumps(_classify(TARGET)), _THREE_STAGE][calls["n"] - 1]

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline(_ASK, "khoa-gia"))
    assert env["status"] == "ok"
    assert calls["n"] == 3, "analyze + classify + ĐÚNG MỘT simulate"


def test_P2_manifest_hint_vao_prompt_simulate(monkeypatch):
    """§C — manifest máy-đọc phải được nhồi vào prompt simulate."""
    q = [_an_l4(), json.dumps(_classify(TARGET)), _THREE_STAGE]
    seen = {}

    async def fake(api_key, system_prompt, user_text, response_schema=None,
                   temperature=0.2, image=None):
        if "simulation_id đã chọn" in user_text:
            seen["prompt"] = user_text
        return q.pop(0)

    monkeypatch.setattr(pipeline, "call_gemini", fake)
    asyncio.run(pipeline.run_pipeline(_ASK, "khoa-gia"))
    assert "YÊU CẦU TẦNG" in seen.get("prompt", "")
    assert "limit" in seen["prompt"] and "aggregate" in seen["prompt"]


# ── §E — fail-closed GIỮ NGUYÊN khi analyze thiếu evidence ────────
def test_E_analyze_thieu_tham_so_tang_thi_van_fail_closed(monkeypatch):
    """Đề nêu limit nhưng KHÔNG cho số → không grounded → merge không bịa →
    nếu LLM cũng bỏ → completeness từ chối (không status=ok nửa vời)."""
    reqs = [
        {"operation": "relational_table_query:filter", **_GROUP,
         "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
        {"operation": "relational_table_query:limit", **_GROUP},  # THIẾU số limit
    ]
    an = json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal="Lọc tổ A, lấy vài dòng đầu"),
        "requested_operations": sorted({r["operation"] for r in reqs}),
        "requested_requirements": reqs}, ensure_ascii=False)
    # LLM chỉ dựng filter, bỏ limit (cả 3 lượt)
    only_filter = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                             filter={"op": "=", "column": "to", "value": "A"})
    env = _run(monkeypatch, [an, json.dumps(_classify(TARGET))] + [only_filter] * 3,
               "Lọc tổ A rồi lấy vài dòng đầu.")
    assert env["status"] == "unsupported"
    assert env.get("config") is None


def test_E_khong_bia_tang_cot_khong_co_trong_bang(monkeypatch):
    """Manifest nêu sort theo cột mà bảng LLM không có → không resolve → không
    chèn; nếu đó là tầng bắt buộc và LLM bỏ → fail-closed (không bịa)."""
    reqs = [{"operation": "relational_table_query:sort", **_GROUP,
             "sort_column": "Xếp hạng", "sort_direction": "desc"}]
    an = json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal="Sắp theo xếp hạng"),
        "requested_operations": ["relational_table_query:sort"],
        "requested_requirements": reqs}, ensure_ascii=False)
    no_sort = _table_cfg(_L4_SCHEMA, _L4_ROWS)  # không có cột "Xếp hạng", không sort
    env = _run(monkeypatch, [an, json.dumps(_classify(TARGET))] + [no_sort] * 3,
               "Sắp theo xếp hạng giảm dần.")
    assert env["status"] == "unsupported"
    assert env.get("config") is None


# ── không hồi quy: đề ĐÃ đủ tầng vẫn chạy, không bị merge phá ─────
def test_de_du_tang_san_khong_bi_merge_lam_hong(monkeypatch):
    full = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                      filter={"op": "=", "column": "to", "value": "A"},
                      projection=["ten", "diem"],
                      sort={"column": "diem", "direction": "desc"},
                      limit=3, aggregate={"func": "avg", "column": "diem"})
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), full])
    assert env["status"] == "ok"
    out = run_table_query(env["config"])
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
