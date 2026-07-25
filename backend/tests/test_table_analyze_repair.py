# -*- coding: utf-8 -*-
"""M17 W2B-PATCH3 §E/§F/§G/§I — BOUNDED ANALYZE REPAIR + end-to-end.

Deterministic patch (`patch_requirements`) — thuần, không LLM: chỉ ĐIỀN field
còn thiếu, KHÔNG ghi đè field đã hợp lệ, KHÔNG thêm stage mới. Rồi end-to-end qua
production `run_pipeline` (mock): analyze trả EXACT live P2 payload (incomplete)
→ bounded repair (mock) điền tham số → manifest 5 tầng → merge → AVG 8.5/3.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import _analysis, _classify, _table_cfg
from app.simulation.analyze_table_params import (
    patch_requirements,
    validate_table_parameters,
)
from app.simulation.table_query_engine import run_table_query

TARGET = "database.relational_table_query"

# EXACT live P2 requested_requirements (4d9e8ac) — incomplete.
_LIVE_P2_REQS = [
    {"operation": "relational_table_query:filter", "query_group": 0,
     "sort_column": None, "sort_direction": None},
    {"operation": "relational_table_query:projection", "query_group": 0,
     "sort_column": None, "sort_direction": None},
    {"operation": "relational_table_query:sort", "query_group": 0,
     "sort_column": "Điểm", "sort_direction": "desc"},
    {"operation": "relational_table_query:limit", "query_group": 0,
     "sort_column": None, "sort_direction": None},
    {"operation": "relational_table_query:avg", "query_group": 0,
     "sort_column": None, "sort_direction": None},
]
# repair chỉ điền THAM SỐ THIẾU (không đụng sort đã hợp lệ).
_REPAIR_REQS = [
    {"operation": "relational_table_query:filter",
     "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
    {"operation": "relational_table_query:projection",
     "projection_columns": ["Tên", "Điểm"]},
    {"operation": "relational_table_query:limit", "limit": 3},
    {"operation": "relational_table_query:avg", "aggregate_column": "Điểm"},
]


# ════════════════════════════════════════════════════════════════════════
# §E — DETERMINISTIC PATCH (pure)
# ════════════════════════════════════════════════════════════════════════
def test_patch_dien_du_tham_so_va_grounded():
    patched = patch_requirements(_LIVE_P2_REQS, _REPAIR_REQS)
    r = validate_table_parameters({"requested_requirements": patched})
    assert r["analyze_parameter_decision"] == "complete"
    assert set(r["grounded_stages"]) == {"filter", "projection", "sort", "limit", "aggregate"}


def test_patch_khong_ghi_de_field_da_hop_le():
    """sort đã có "Điểm"/"desc" — repair KHÔNG được đổi nó."""
    tampered = [{"operation": "relational_table_query:sort",
                 "sort_column": "Tên", "sort_direction": "asc"}]
    patched = patch_requirements(_LIVE_P2_REQS, tampered)
    sort = next(i for i in patched if i["operation"].endswith(":sort"))
    assert sort["sort_column"] == "Điểm" and sort["sort_direction"] == "desc"


def test_patch_khong_them_stage_moi():
    """repair trả stage KHÔNG có trong original → bỏ qua (không thêm)."""
    extra = _REPAIR_REQS + [{"operation": "relational_table_query:count",
                             "aggregate_func": "count"}]
    patched = patch_requirements(_LIVE_P2_REQS, extra)
    ops = {i["operation"] for i in patched}
    assert "relational_table_query:count" not in ops


def test_patch_giu_query_group():
    patched = patch_requirements(_LIVE_P2_REQS, _REPAIR_REQS)
    assert all(i.get("query_group") == 0 for i in patched)


def test_patch_khong_dung_toi_data_object():
    """Patch chỉ đụng requested_requirements — không đổi rows/schema/objects."""
    an = {"objects": ["bảng"], "data": [{"description": "x"}],
          "requested_requirements": _LIVE_P2_REQS}
    patch_requirements(an["requested_requirements"], _REPAIR_REQS)
    assert an["objects"] == ["bảng"] and an["data"] == [{"description": "x"}]


# ════════════════════════════════════════════════════════════════════════
# §G/§F — END-TO-END qua run_pipeline (mock)
# ════════════════════════════════════════════════════════════════════════
_L4_SCHEMA = [
    {"name": "ten", "type": "text", "label": "Tên"},
    {"name": "to", "type": "text", "label": "Tổ"},
    {"name": "diem", "type": "number", "label": "Điểm"},
    {"name": "vang", "type": "number", "label": "Số buổi vắng"},
]
_L4_ROWS = [
    {"ten": "An", "to": "A", "diem": 9.0, "vang": 1}, {"ten": "Bình", "to": "B", "diem": 8.5, "vang": 0},
    {"ten": "Chi", "to": "A", "diem": 6.0, "vang": 2}, {"ten": "Dũng", "to": "A", "diem": 9.0, "vang": 0},
    {"ten": "Hà", "to": "B", "diem": 7.5, "vang": 3}, {"ten": "Lan", "to": "A", "diem": 7.5, "vang": 1},
    {"ten": "Minh", "to": "A", "diem": 6.0, "vang": 0}, {"ten": "Nga", "to": "B", "diem": 9.5, "vang": 2},
]
_OBJECTS = ["bảng học sinh", "cột Tên", "cột Tổ", "cột Điểm", "cột Số buổi vắng"]
_DATA = [{"description": "điểm", "values": [9, 8.5, 6, 9, 7.5, 7.5, 6, 9.5],
          "labels": ["An", "Bình", "Chi", "Dũng", "Hà", "Lan", "Minh", "Nga"]},
         {"description": "tổ", "labels": ["A", "B", "A", "A", "B", "A", "A", "B"]}]
_ASK = ("Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học "
        "sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.")

# 3-stage simulate candidate (đúng cái live P2 sinh ra).
_THREE_STAGE = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                          filter={"op": "=", "column": "to", "value": "A"},
                          projection=["ten", "diem"],
                          sort={"column": "diem", "direction": "desc"})


def _live_incomplete_analyze():
    return json.dumps({**_analysis(objects=_OBJECTS, data=_DATA, goal=_ASK),
                       "requested_operations": sorted({r["operation"] for r in _LIVE_P2_REQS}),
                       "requested_requirements": _LIVE_P2_REQS}, ensure_ascii=False)


def _repair_response():
    return json.dumps({"requested_requirements": _REPAIR_REQS}, ensure_ascii=False)


def _run(responses, text=_ASK, observer=None):
    q = list(responses)

    async def fake(api_key, system_prompt, user_text, response_schema=None,
                   temperature=0.2, image=None):
        assert q, "gọi nhiều hơn scripted"
        return q.pop(0)

    pipeline.call_gemini = fake
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia", observer=observer))


def test_G_exact_live_p2_repair_thanh_5_tang_chay_dung(monkeypatch):
    monkeypatch.setattr(pipeline, "call_gemini", None)
    # analyze(incomplete) → REPAIR → classify → simulate(3-stage) → merge(5)
    env = _run([_live_incomplete_analyze(), _repair_response(),
                json.dumps(_classify(TARGET)), _THREE_STAGE])
    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    cfg = env["config"]
    assert cfg["filter"] == {"op": "=", "column": "to", "value": "A"}
    assert cfg["projection"] == ["ten", "diem"]
    assert cfg["sort"] == {"column": "diem", "direction": "desc"}
    assert cfg["limit"] == 3
    assert cfg["aggregate"] == {"func": "avg", "column": "diem"}
    out = run_table_query(cfg)
    assert [r["ten"] for r in out["result_rows"]] == ["An", "Dũng", "Lan"]
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3
    for leak in ("aggregateResult", "result_rows", "steps"):
        assert leak not in cfg


def test_I_metrics_repair_attempted_va_succeeded(monkeypatch):
    from app.evaluation.observer import AttemptObserver
    monkeypatch.setattr(pipeline, "call_gemini", None)
    obs = AttemptObserver()
    _run([_live_incomplete_analyze(), _repair_response(),
          json.dumps(_classify(TARGET)), _THREE_STAGE], observer=obs)
    ev = {et: d for (et, d) in obs.events if et in ("analyze_param_check", "analyze_param_repair")}
    assert "analyze_param_check" in ev
    assert ev["analyze_param_check"]["decision"] == "incomplete"
    assert "analyze_param_repair" in ev
    assert ev["analyze_param_repair"]["attempted"] is True
    assert ev["analyze_param_repair"]["succeeded"] is True
    assert set(ev["analyze_param_repair"]["incomplete_before"]) == {"filter", "projection", "limit", "aggregate"}
    assert ev["analyze_param_repair"]["incomplete_after"] == []


def test_I_analyze_du_ngay_dau_khong_repair(monkeypatch):
    """Analyze đầy đủ ngay attempt đầu → KHÔNG repair (không tốn lượt thừa)."""
    monkeypatch.setattr(pipeline, "call_gemini", None)
    full_reqs = [
        {"operation": "relational_table_query:filter", "query_group": 1,
         "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
        {"operation": "relational_table_query:projection", "query_group": 1,
         "projection_columns": ["Tên", "Điểm"]},
        {"operation": "relational_table_query:sort", "query_group": 1,
         "sort_column": "Điểm", "sort_direction": "desc"},
        {"operation": "relational_table_query:limit", "query_group": 1, "limit": 3},
        {"operation": "relational_table_query:avg", "query_group": 1,
         "aggregate_func": "avg", "aggregate_column": "Điểm"},
    ]
    an = json.dumps({**_analysis(objects=_OBJECTS, data=_DATA, goal=_ASK),
                     "requested_operations": sorted({r["operation"] for r in full_reqs}),
                     "requested_requirements": full_reqs}, ensure_ascii=False)
    from app.evaluation.observer import AttemptObserver
    obs = AttemptObserver()
    # KHÔNG có repair response trong queue — nếu pipeline gọi repair sẽ cạn queue.
    env = _run([an, json.dumps(_classify(TARGET)), _THREE_STAGE], observer=obs)
    assert env["status"] == "ok"
    rep = next((d for (et, d) in obs.events if et == "analyze_param_repair"), None)
    assert rep is None or rep["attempted"] is False


def test_F_repair_van_thieu_thi_fail_closed(monkeypatch):
    """Repair KHÔNG điền được (trả lại y cũ) → still incomplete → fail-closed,
    KHÔNG simulate, KHÔNG bịa."""
    monkeypatch.setattr(pipeline, "call_gemini", None)
    empty_repair = json.dumps({"requested_requirements": []}, ensure_ascii=False)
    # analyze(incomplete) → repair(rỗng) → classify → simulate 3x (thiếu limit+agg)
    env = _run([_live_incomplete_analyze(), empty_repair,
                json.dumps(_classify(TARGET)), _THREE_STAGE, _THREE_STAGE, _THREE_STAGE])
    assert env["status"] == "unsupported"
    assert env.get("config") is None
    assert env.get("simulation_id") != "generic.rule_scene"


def test_neg9_repair_khong_doi_source_rows_schema(monkeypatch):
    """Repair chỉ đụng requirements — rows/schema của simulate không bị đổi."""
    monkeypatch.setattr(pipeline, "call_gemini", None)
    env = _run([_live_incomplete_analyze(), _repair_response(),
                json.dumps(_classify(TARGET)), _THREE_STAGE])
    assert env["status"] == "ok"
    # 8 dòng nguồn giữ nguyên trong config (merge/repair không đụng rows)
    assert len(env["config"]["rows"]) == 8
