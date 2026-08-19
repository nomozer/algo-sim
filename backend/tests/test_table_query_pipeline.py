# -*- coding: utf-8 -*-
"""M17 W2B — 10 fixture bắt buộc, chạy qua PRODUCTION `run_pipeline`.

Không dựng pipeline mirror (bất biến #22). Mỗi fixture kiểm đúng một mệnh đề,
và các fixture "phải từ chối" đều kiểm thêm: KHÔNG tạo simulation, KHÔNG leak
sang generic, thông điệp học sinh sạch.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import (
    _TB_DATA,
    _TB_OBJECTS,
    _TB_ROWS,
    _TB_SCHEMA,
    _analysis,
    _classify,
    _table_cfg,
)
from app.simulation.table_query_engine import run_table_query

TARGET = "database.relational_table_query"


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted (đáng lẽ đã dừng sớm)"
        return responses.pop(0)
    return f


def _an(goal, ops=None, **kw):
    a = {**_analysis(objects=_TB_OBJECTS, data=_TB_DATA, goal=goal, **kw)}
    if ops is not None:
        a["requested_operations"] = ops
    return json.dumps(a, ensure_ascii=False)


def _run(monkeypatch, responses, text="Cho bảng điểm lớp, hãy truy vấn."):
    monkeypatch.setattr(pipeline, "call_gemini", _fake(list(responses)))
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


def _ok(env):
    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    assert env["domain"] == "database"
    return env["config"]


# ── 1. lọc + chọn cột ─────────────────────────────────────────────
def test_fx1_loc_va_chon_cot(monkeypatch):
    env = _run(monkeypatch, [
        _an("Lọc bạn điểm trên 7, hiện tên và điểm",
            ["relational_table_query:filter", "relational_table_query:projection"]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": ">", "column": "diem", "value": 7},
                   projection=["ten", "diem"]),
    ])
    cfg = _ok(env)
    res = run_table_query(cfg)
    assert [r["ten"] for r in res["result_rows"]] == ["An", "Chi", "Hà"]
    assert set(res["result_rows"][0]) == {"ten", "diem"}


# ── 2. lọc + sắp xếp giảm dần ─────────────────────────────────────
def test_fx2_loc_va_sap_xep_giam_dan(monkeypatch):
    env = _run(monkeypatch, [
        _an("Lọc điểm ≥6 rồi sắp giảm dần",
            ["relational_table_query:filter", "relational_table_query:sort"]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": ">=", "column": "diem", "value": 6},
                   sort={"column": "diem", "direction": "desc"}),
    ])
    res = run_table_query(_ok(env))
    assert [r["diem"] for r in res["result_rows"]] == [9.0, 8.5, 7.25, 6.0, 6.0]


# ── 3. COUNT sau lọc ──────────────────────────────────────────────
def test_fx3_count_sau_loc(monkeypatch):
    env = _run(monkeypatch, [
        _an("Đếm học sinh tổ A",
            ["relational_table_query:filter", "relational_table_query:count"]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": "=", "column": "to", "value": "A"},
                   aggregate={"func": "count"}),
    ])
    res = run_table_query(_ok(env))
    assert res["aggregateResult"]["value"] == 2


# ── 4. AVG ────────────────────────────────────────────────────────
def test_fx4_avg(monkeypatch):
    env = _run(monkeypatch, [
        _an("Điểm trung bình cả lớp", ["relational_table_query:avg"]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS, aggregate={"func": "avg", "column": "diem"}),
    ])
    res = run_table_query(_ok(env))
    assert res["aggregateResult"]["value"] == pytest.approx(36.75 / 5)


# ── 5. pipeline kết hợp — KHÔNG bị completeness gate chặn (fixture 9) ──
def test_fx5_va_fx9_pipeline_ket_hop_khong_bi_chan_oan(monkeypatch):
    """NĂM tầng trong MỘT truy vấn: family khai `pipeline` nên đây là hợp lệ."""
    env = _run(monkeypatch, [
        _an("Lọc, chọn cột, sắp xếp, lấy 2 dòng đầu, tính trung bình", [
            "relational_table_query:filter", "relational_table_query:projection",
            "relational_table_query:sort", "relational_table_query:limit",
            "relational_table_query:avg",
        ]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": ">=", "column": "diem", "value": 6},
                   projection=["ten", "diem"],
                   sort={"column": "diem", "direction": "desc"}, limit=2,
                   aggregate={"func": "avg", "column": "diem"}),
    ])
    cfg = _ok(env)
    assert env.get("completeness") is None, "pipeline hợp lệ KHÔNG được coi là xung đột"
    res = run_table_query(cfg)
    assert res["aggregateResult"]["value"] == pytest.approx((9.0 + 8.5) / 2)


# ── 6. thiếu bảng → insufficient (dùng cổng DÙNG CHUNG §C2) ───────
def test_fx6_thieu_bang_thi_tu_choi_khong_bia(monkeypatch):
    env = _run(monkeypatch, [
        json.dumps({**_analysis(objects=[], data=[], relations=[],
                                goal="Lọc học sinh giỏi"), "requested_operations": []}),
        json.dumps(_classify(TARGET)),
    ], "Hãy lọc ra những học sinh giỏi trong bảng.")
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "insufficient_specification"
    assert env["error_code"] == "input_insufficient"
    assert env.get("simulation_id") is None and env.get("config") is None
    assert env["input_sufficiency"]["missing_inputs"] == ["table_schema_and_rows"]
    for banned in ("{", "}", "schema", "JSON", "None"):
        assert banned not in env["reason"]


# ── 7. JOIN → unsupported trung thực ──────────────────────────────
def test_fx7_join_bi_tu_choi_o_classify(monkeypatch):
    env = _run(monkeypatch, [
        _an("Ghép bảng học sinh với bảng lớp", []),
        json.dumps(_classify(None, status="unsupported",
                             reason="Ghép nhiều bảng (JOIN) vượt năng lực v1.")),
    ], "Ghép bảng Học sinh với bảng Lớp rồi liệt kê tên lớp của từng bạn.")
    assert env["status"] == "unsupported"
    assert env.get("simulation_id") is None
    assert env.get("config") is None


# ── 8. sai kiểu/toán tử → validator từ chối (cạn retry) ───────────
def test_fx8_sai_toan_tu_bi_validator_chan(monkeypatch):
    """>" trên cột chữ: validator từ chối cả 3 lần → status=error (synthesis_exhausted), KHÔNG có
    envelope ok nào được phát."""
    bad = _table_cfg(_TB_SCHEMA, _TB_ROWS,
                     filter={"op": ">", "column": "ten", "value": "M"})
    env = _run(monkeypatch, [
        _an("Lọc theo tên", ["relational_table_query:filter"]),
        json.dumps(_classify(TARGET)), bad, bad, bad,
    ])
    assert env.get("status") == "error"
    assert env.get("failure_category") == "synthesis_exhausted"
    assert "config" not in env


# ── 10. HAI truy vấn độc lập → phải từ chối trung thực ────────────
def _req(op, **goal):
    return {"operation": f"relational_table_query:{op}", **goal}


def _an_req(goal_text, reqs):
    a = {**_analysis(objects=_TB_OBJECTS, data=_TB_DATA, goal=goal_text),
         "requested_operations": sorted({r["operation"] for r in reqs}),
         "requested_requirements": reqs}
    return json.dumps(a, ensure_ascii=False)


def test_fx10_hai_truy_van_doc_lap_phai_tu_choi(monkeypatch):
    """W2B-S1: hai phép đếm trên HAI điều kiện khác nhau là HAI truy vấn.
    Chạy cái nào cũng là bỏ im lặng cái kia ⇒ từ chối trung thực."""
    env = _run(monkeypatch, [
        _an_req("Đếm học sinh tổ A và đếm học sinh tổ B", [
            _req("count", filter_column="to", filter_op="=", filter_value="A"),
            _req("count", filter_column="to", filter_op="=", filter_value="B"),
        ]),
        json.dumps(_classify(TARGET)),
    ], "Cho bảng điểm, đếm số bạn tổ A và đếm số bạn tổ B.")
    assert env["status"] == "unsupported"
    assert env["error_code"] == "multiple_operations_not_supported"
    assert env.get("simulation_id") is None and env.get("config") is None
    c = env["completeness"]
    assert c["independent_goal_count"] == 2
    assert len(set(c["independent_goal_keys"])) == 2, "hai mục tiêu phải KHÁC chữ ký"
    assert "tách" in env["reason"]
    for banned in ("{", "}", "filter=", "table.aggregate"):
        assert banned not in env["reason"], f"thông điệp lộ id kỹ thuật: {env['reason']}"


def test_fx10b_cung_mot_COUNT_dien_dat_hai_lan_thi_gop(monkeypatch):
    """Đối chứng chống chặn oan: CÙNG một phép đếm nói hai cách tương đương
    (">"/"lớn hơn", 6 và 6.0) ⇒ MỘT truy vấn ⇒ vẫn chạy."""
    env = _run(monkeypatch, [
        _an_req("Đếm học sinh điểm trên 6", [
            _req("count", filter_column="diem", filter_op=">", filter_value=6),
            _req("count", filter_column=" Diem ", filter_op="lon_hon", filter_value=6.0),
        ]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": ">", "column": "diem", "value": 6},
                   aggregate={"func": "count"}),
    ])
    _ok(env)
    assert env.get("completeness") is None


def test_fx10c_COUNT_va_SUM_cung_dieu_kien_van_la_hai_truy_van(monkeypatch):
    """Spec mang ĐÚNG MỘT hàm tổng hợp ⇒ đếm + tính tổng là hai yêu cầu."""
    env = _run(monkeypatch, [
        _an_req("Đếm tổ A và tính tổng điểm tổ A", [
            _req("count", filter_column="to", filter_op="=", filter_value="A"),
            _req("sum", filter_column="to", filter_op="=", filter_value="A",
                 aggregate_func="sum", aggregate_column="diem"),
        ]),
        json.dumps(_classify(TARGET)),
    ], "Đếm số bạn tổ A và tính tổng điểm tổ A.")
    assert env["status"] == "unsupported"
    assert env["error_code"] == "multiple_operations_not_supported"


def test_fx10d_pipeline_mot_truy_van_khong_bi_chan_oan(monkeypatch):
    """Bốn tầng CÙNG một truy vấn (cùng query_group) ⇒ KHÔNG chặn."""
    g = {"query_group": 0, "filter_column": "diem", "filter_op": ">=",
         "filter_value": 6}
    env = _run(monkeypatch, [
        _an_req("Lọc, chọn cột, sắp xếp, lấy 2 dòng", [
            _req("filter", **g), _req("projection", **g),
            _req("sort", **g), _req("limit", **g),
        ]),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": ">=", "column": "diem", "value": 6},
                   projection=["ten", "diem"],
                   sort={"column": "diem", "direction": "desc"}, limit=2),
    ])
    _ok(env)
    assert env.get("completeness") is None


# ── không leak sang generic ở BẤT KỲ nhánh nào ────────────────────
def test_khong_bao_gio_leak_sang_generic(monkeypatch):
    """Đề bảng thiếu dữ kiện KHÔNG được rơi vào generic.rule_scene."""
    env = _run(monkeypatch, [
        json.dumps({**_analysis(objects=[], data=[], goal="Lọc bảng"),
                    "requested_operations": []}),
        json.dumps(_classify(TARGET)),
    ], "Lọc bảng dữ liệu.")
    assert env.get("simulation_id") != "generic.rule_scene"


def test_hai_hop_dong_va_engine_khong_troi_khoi_nhau():
    """Giới hạn trong hợp đồng prompt phải là giới hạn engine THẬT thi hành."""
    from app.simulation.catalog import CATALOG
    from app.simulation.table_query_engine import MAX_COLUMNS, MAX_ROWS

    contract = CATALOG[TARGET].contract
    assert str(MAX_ROWS) in contract and str(MAX_COLUMNS) in contract
