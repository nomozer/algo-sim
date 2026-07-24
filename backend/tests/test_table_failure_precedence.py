# -*- coding: utf-8 -*-
"""M17 W2B-PATCH §B (L5) — THỨ TỰ ƯU TIÊN CỦA LÝ DO TỪ CHỐI.

Sự cố live L5: đề "Lọc các học sinh có điểm từ 8 trở lên và sắp xếp giảm dần"
KHÔNG kèm bảng nào. Hệ từ chối (an toàn) nhưng báo sai bản chất:

    semantic_incomplete — "Đề đang hỏi 2 truy vấn độc lập… hãy tách ra"

Học sinh làm theo lời khuyên đó sẽ tách thành hai câu hỏi và vẫn bị từ chối,
vì lỗi THẬT là CHƯA CÓ BẢNG. Hai khuyết tật độc lập cùng gây ra chuyện này:

1. `_has_table` quá dễ dãi — "≥2 object + có con số nào đó" đủ để coi là đã có
   bảng, nên cổng đủ-dữ-kiện không bắt được đề không có bảng;
2. lọc và sắp xếp là HAI TẦNG của MỘT truy vấn, nhưng chữ ký mục tiêu khác nhau
   nên bị đếm thành hai truy vấn độc lập ⇒ chặn oan cả đề HỢP LỆ có bảng.

Thứ tự đúng: route → đủ dữ kiện → completeness → validation → execution.
"""

from __future__ import annotations

import asyncio
import json

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

TARGET = "database.relational_table_query"

# analyze của đề KHÔNG có bảng: vẫn nêu vài danh từ và một con số (ngưỡng 8),
# đúng như analyze thật của L5 — đây chính là hình dạng đã lọt cổng.
_NO_TABLE_OBJECTS = ["học sinh", "điểm"]
_NO_TABLE_DATA = [{"description": "điểm từ 8 trở lên"}]


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted"
        return responses.pop(0)
    return f


def _run(monkeypatch, responses, text):
    monkeypatch.setattr(pipeline, "call_gemini", _fake(list(responses)))
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


def _req(op, **goal):
    return {"operation": f"relational_table_query:{op}", **goal}


def _an(goal, reqs, *, objects, data):
    return json.dumps({
        **_analysis(objects=objects, data=data, goal=goal),
        "requested_operations": sorted({r["operation"] for r in reqs}),
        "requested_requirements": reqs,
    }, ensure_ascii=False)


# ── 1. THIẾU BẢNG là lý do CHÍNH, không phải "tách truy vấn" ──────
def test_L5_loc_va_sap_xep_khong_co_bang_thi_bao_thieu_bang(monkeypatch):
    env = _run(monkeypatch, [
        _an("Lọc học sinh điểm từ 8 trở lên rồi sắp xếp giảm dần", [
            _req("filter", filter_column="điểm", filter_op=">=", filter_value="8"),
            _req("sort", sort_column="điểm", sort_direction="desc"),
        ], objects=_NO_TABLE_OBJECTS, data=_NO_TABLE_DATA),
        json.dumps(_classify(TARGET)),
    ], "Lọc các học sinh có điểm từ 8 trở lên và sắp xếp giảm dần.")

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "insufficient_specification"
    assert env["error_code"] == "input_insufficient"
    assert env["input_sufficiency"]["missing_inputs"] == ["table_schema_and_rows"]
    assert env.get("simulation_id") is None and env.get("config") is None
    # thông điệp phải NÓI VỀ BẢNG, tuyệt đối không xui học sinh tách truy vấn
    assert "bảng" in env["reason"].lower()
    assert "tách" not in env["reason"].lower()


# ── 2. có bảng + hai truy vấn độc lập → completeness (giữ nguyên) ─
def test_hai_truy_van_doc_lap_co_bang_van_la_semantic_incomplete(monkeypatch):
    env = _run(monkeypatch, [
        _an("Đếm học sinh tổ A và đếm học sinh tổ B", [
            _req("count", filter_column="to", filter_op="=", filter_value="A"),
            _req("count", filter_column="to", filter_op="=", filter_value="B"),
        ], objects=_TB_OBJECTS, data=_TB_DATA),
        json.dumps(_classify(TARGET)),
    ], "Cho bảng điểm, đếm số bạn tổ A và đếm số bạn tổ B.")

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "semantic_incomplete"
    assert env["error_code"] == "multiple_operations_not_supported"
    assert env["completeness"]["independent_goal_count"] == 2


# ── 3. thiếu bảng THẮNG multi-goal khi cả hai cùng sai ────────────
def test_thieu_bang_thang_khi_dong_thoi_co_hai_truy_van(monkeypatch):
    env = _run(monkeypatch, [
        _an("Đếm học sinh tổ A và đếm học sinh tổ B", [
            _req("count", filter_column="tổ", filter_op="=", filter_value="A"),
            _req("count", filter_column="tổ", filter_op="=", filter_value="B"),
        ], objects=_NO_TABLE_OBJECTS, data=[]),
        json.dumps(_classify(TARGET)),
    ], "Đếm số bạn tổ A và đếm số bạn tổ B.")

    assert env["failure_category"] == "insufficient_specification", (
        "chưa có bảng thì đừng bắt học sinh tách truy vấn trước")
    assert "tách" not in env["reason"].lower()
    # chẩn đoán phụ vẫn được GIỮ cho dev — chỉ không đưa lên mặt học sinh
    assert env["input_sufficiency"]["missing_inputs"] == ["table_schema_and_rows"]


# ── 4. ĐỐI CHỨNG chặn oan: cùng đề đó KÈM bảng phải chạy ──────────
def test_loc_va_sap_xep_co_bang_la_mot_truy_van_hop_le(monkeypatch):
    env = _run(monkeypatch, [
        _an("Lọc điểm từ 8 trở lên rồi sắp xếp giảm dần", [
            _req("filter", filter_column="diem", filter_op=">=", filter_value="8"),
            _req("sort", sort_column="diem", sort_direction="desc"),
        ], objects=_TB_OBJECTS, data=_TB_DATA),
        json.dumps(_classify(TARGET)),
        _table_cfg(_TB_SCHEMA, _TB_ROWS,
                   filter={"op": ">=", "column": "diem", "value": 8},
                   sort={"column": "diem", "direction": "desc"}),
    ], "Cho bảng điểm, lọc bạn điểm từ 8 trở lên và sắp xếp giảm dần.")

    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    assert env.get("completeness") is None, "lọc + sắp xếp là MỘT truy vấn"


# ── không lây sang family khác ────────────────────────────────────
def test_cay_thieu_cau_truc_van_bao_dung_loai_loi(monkeypatch):
    """Thứ tự ưu tiên dùng chung không được đổi kết luận của family khác."""
    env = _run(monkeypatch, [
        json.dumps({**_analysis(objects=["cây"], data=[], relations=[],
                                goal="Duyệt cây theo thứ tự trước"),
                    "requested_operations": ["tree_traversal:preorder"]}),
        json.dumps(_classify("tree.traversal")),
    ], "Duyệt cây theo thứ tự trước.")
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "insufficient_specification"
