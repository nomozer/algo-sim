# -*- coding: utf-8 -*-
"""M17 W2B-PATCH §A (L4) — ĐỦ TẦNG PIPELINE, không chỉ đủ family.

Sự cố live L4: đề hỏi NĂM tầng nối tiếp

    lọc tổ A → chọn cột (Tên, Điểm) → sắp xếp Điểm giảm dần → lấy 3 dòng đầu
    → tính điểm trung bình của 3 bạn đó

nhưng spec dựng ra chỉ có ba tầng đầu — và hệ vẫn trả `status=ok`. Học sinh
nhận về 5 dòng không sắp giới hạn và KHÔNG có trung bình nào, mà không hề được
báo là đề đã bị trả lời thiếu. Đó là mất mát ngữ nghĩa.

Nguyên nhân gốc: PHA 2 của completeness so ở tầng TARGET
(`satisfies_semantic_operations`), mà target `database.relational_table_query`
khai nó đáp ứng CẢ CHÍN operation — nên mọi spec, dù thiếu tầng nào, cũng
"đủ". Cái phải so là **spec ĐÃ VALIDATE thực sự dựng được tầng nào**.

Bất biến sau bản vá: `status=ok` ⟹ `dropped_pipeline_stages` rỗng VÀ
`mismatched_stage_parameters` rỗng.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import _analysis, _classify, _table_cfg
from app.simulation.table_query_engine import (
    PIPELINE_STAGE_ORDER,
    run_table_query,
    stages_of,
)

TARGET = "database.relational_table_query"

# Bảng L4 THẬT (live) — 8 dòng, tổ A có 5 bạn.
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
    {"description": "tổ của các bạn", "labels": ["A", "B", "A", "A", "B", "A", "A", "B"]},
]
# Năm tầng CÙNG một truy vấn (analyze khai cùng query_group).
_L4_GROUP = {"query_group": 1, "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"}
_L4_REQS = [
    {"operation": "relational_table_query:filter", **_L4_GROUP},
    {"operation": "relational_table_query:projection", **_L4_GROUP,
     "projection_columns": ["Tên", "Điểm"]},
    {"operation": "relational_table_query:sort", **_L4_GROUP,
     "sort_column": "Điểm", "sort_direction": "desc"},
    {"operation": "relational_table_query:limit", **_L4_GROUP, "limit": 3},
    {"operation": "relational_table_query:avg", **_L4_GROUP,
     "aggregate_func": "avg", "aggregate_column": "Điểm"},
]
_L4_ASK = ("Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 "
           "học sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.")


def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted"
        return responses.pop(0)
    return f


def _run(monkeypatch, responses, text=_L4_ASK):
    monkeypatch.setattr(pipeline, "call_gemini", _fake(list(responses)))
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


def _an_l4():
    return json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal=_L4_ASK),
        "requested_operations": sorted({r["operation"] for r in _L4_REQS}),
        "requested_requirements": _L4_REQS,
    }, ensure_ascii=False)


_FULL = dict(filter={"op": "=", "column": "to", "value": "A"},
             projection=["ten", "diem"],
             sort={"column": "diem", "direction": "desc"},
             limit=3,
             aggregate={"func": "avg", "column": "diem"})


# ── 1. THIẾU TẦNG (analyze grounds đủ) → MERGE bù, KHÔNG từ chối (W2B-PATCH2 §A) ──
def test_L4_spec_thieu_limit_va_aggregate_duoc_merge_bu(monkeypatch):
    """Đúng spec live P2: ba tầng đầu, thiếu limit + aggregate. analyze grounds
    đủ 5 tầng ⇒ merge tất định bù limit+aggregate ⇒ CHẠY, không từ chối.

    (Trước PATCH2: từ chối trung thực. PATCH2 §A: request hợp lệ trong hợp đồng
    phải có đường sinh spec đủ tầng — cổng fail-closed chỉ là chốt cuối.)"""
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                       filter=_FULL["filter"], projection=_FULL["projection"],
                       sort=_FULL["sort"])
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), thieu])

    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    cfg = env["config"]
    assert cfg["limit"] == 3
    assert cfg["aggregate"] == {"func": "avg", "column": "diem"}
    out = run_table_query(cfg)
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3


def test_L4_khong_bao_gio_leak_sang_generic(monkeypatch):
    """Dù merge bù tầng, route LUÔN ở database (không bao giờ leak generic)."""
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"])
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), thieu])
    assert env.get("simulation_id") != "generic.rule_scene"
    assert env["simulation_id"] == TARGET
    assert env["status"] == "ok"


# ── 2. ĐỦ NĂM TẦNG → chạy, engine sở hữu kết quả ─────────────────
def test_L4_du_nam_tang_thi_chay_va_ra_dung_ket_qua(monkeypatch):
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)),
                             _table_cfg(_L4_SCHEMA, _L4_ROWS, **_FULL)])

    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == TARGET
    assert env.get("completeness") is None

    out = run_table_query(env["config"])
    assert [r["ten"] for r in out["result_rows"]] == ["An", "Dũng", "Lan"]
    assert len(out["result_rows"]) == 3
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3
    for leaked in ("aggregateResult", "result_rows", "ordered_indices", "steps"):
        assert leaked not in env["config"], "đáp án không được nằm trong spec"


# ── 3. SAI THAM SỐ TẦNG (analyze grounds đúng) → MERGE sửa về manifest ────
def test_L4_limit_sai_so_duoc_merge_sua(monkeypatch):
    """Đề xin 3 dòng đầu, LLM cắt 5 — merge SỬA limit về 3 theo manifest."""
    sai = _table_cfg(_L4_SCHEMA, _L4_ROWS, **{**_FULL, "limit": 5})
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), sai])

    assert env["status"] == "ok", env.get("reason")
    assert env["config"]["limit"] == 3
    out = run_table_query(env["config"])
    assert out["aggregateResult"]["counted"] == 3
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)


def test_L4_ham_tong_hop_sai_duoc_merge_sua(monkeypatch):
    """LLM để SUM, manifest yêu cầu AVG — merge sửa về avg."""
    sai = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                     **{**_FULL, "aggregate": {"func": "sum", "column": "diem"}})
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), sai])
    assert env["status"] == "ok", env.get("reason")
    assert env["config"]["aggregate"]["func"] == "avg"
    out = run_table_query(env["config"])
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)


# ── MERGE TẤT ĐỊNH: thiếu tầng (grounded) được bù NGAY, không cần retry LLM ──
def test_L4_thieu_tang_duoc_merge_ngay_luot_dau(monkeypatch):
    """§A — merge tất định bù tầng grounded ngay lượt đầu; KHÔNG còn phụ thuộc
    LLM sửa qua retry (bài học live: retry mù không cứu được gì)."""
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"],
                       projection=_FULL["projection"], sort=_FULL["sort"])
    # CHỈ một response simulate: merge phải hoàn tất mà không cần lượt hai.
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), thieu])

    assert env["status"] == "ok", env.get("reason")
    out = run_table_query(env["config"])
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3


def test_L4_manifest_hint_liet_ke_du_5_tang_trong_prompt(monkeypatch):
    """§C — prompt simulate mang manifest máy-đọc đủ 5 tầng để LLM điền đúng."""
    prompts: list[str] = []
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"])
    responses = [_an_l4(), json.dumps(_classify(TARGET)), thieu]

    async def spy(api_key, system_prompt, user_text, response_schema=None,
                  temperature=0.2, image=None):
        prompts.append(user_text)
        return responses.pop(0)

    monkeypatch.setattr(pipeline, "call_gemini", spy)
    env = asyncio.run(pipeline.run_pipeline(_L4_ASK, "khoa-gia"))
    assert env["status"] == "ok"
    sim_prompt = next(p for p in prompts if "simulation_id đã chọn" in p)
    for stage in ("filter", "projection", "sort", "limit", "aggregate"):
        assert stage in sim_prompt


def test_L4_khong_ground_duoc_thi_van_fail_closed(monkeypatch):
    """Chốt cuối GIỮ NGUYÊN: manifest nêu tầng theo cột KHÔNG có trong schema →
    merge không resolve được → không bịa → completeness từ chối fail-closed."""
    reqs = [
        {"operation": "relational_table_query:filter", "query_group": 1,
         "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
        {"operation": "relational_table_query:sort", "query_group": 1,
         "sort_column": "Xếp hạng ẩn", "sort_direction": "desc"},  # cột không có
    ]
    an = json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal="Lọc tổ A, sắp theo xếp hạng"),
        "requested_operations": sorted({r["operation"] for r in reqs}),
        "requested_requirements": reqs}, ensure_ascii=False)
    only_filter = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"])
    env = _run(monkeypatch, [an, json.dumps(_classify(TARGET))] + [only_filter] * 3,
               "Lọc tổ A rồi sắp theo xếp hạng ẩn.")
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "semantic_incomplete"
    assert env.get("config") is None


# ── ĐỐI CHỨNG chặn oan: đề ít tầng thì spec ít tầng vẫn hợp lệ ────
def test_de_chi_hoi_mot_tang_thi_spec_mot_tang_van_ok(monkeypatch):
    reqs = [{"operation": "relational_table_query:sort",
             "sort_column": "Điểm", "sort_direction": "desc"}]
    an = json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal="Sắp xếp giảm dần"),
        "requested_operations": ["relational_table_query:sort"],
        "requested_requirements": reqs,
    }, ensure_ascii=False)
    env = _run(monkeypatch, [an, json.dumps(_classify(TARGET)),
                             _table_cfg(_L4_SCHEMA, _L4_ROWS,
                                        sort={"column": "diem", "direction": "desc"})],
               "Sắp xếp giảm dần theo Điểm.")
    assert env["status"] == "ok", env.get("reason")
    assert env.get("completeness") is None


def test_spec_lam_THEM_tang_khong_bi_coi_la_thieu(monkeypatch):
    """Thêm tầng KHÔNG phải mất mát ngữ nghĩa — chỉ thiếu mới là."""
    reqs = [{"operation": "relational_table_query:avg",
             "aggregate_func": "avg", "aggregate_column": "Điểm"}]
    an = json.dumps({
        **_analysis(objects=_L4_OBJECTS, data=_L4_DATA, goal="Điểm trung bình"),
        "requested_operations": ["relational_table_query:avg"],
        "requested_requirements": reqs,
    }, ensure_ascii=False)
    env = _run(monkeypatch, [an, json.dumps(_classify(TARGET)),
                             _table_cfg(_L4_SCHEMA, _L4_ROWS,
                                        projection=["ten", "diem"],
                                        aggregate={"func": "avg", "column": "diem"})],
               "Điểm trung bình của cả bảng là bao nhiêu?")
    assert env["status"] == "ok", env.get("reason")


# ── THỨ TỰ TẦNG: công bố một nguồn, engine phải làm đúng thế ──────
def test_thu_tu_tang_authoritative_khop_engine():
    """`aggregate` tính TRÊN kết quả SAU `limit` — khoá bằng số, không bằng lời."""
    assert PIPELINE_STAGE_ORDER == ("filter", "projection", "sort", "limit", "aggregate")
    cfg = {"specVersion": "table-1.0", "schema": _L4_SCHEMA, "rows": _L4_ROWS,
           **_FULL, "normalizations": []}
    out = run_table_query(cfg)
    # Nếu aggregate chạy TRƯỚC limit thì trung bình của cả 5 bạn tổ A = 7.5.
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3
    kinds = [s["kind"] for s in out["steps"]]
    assert kinds.index("limit") < kinds.index("accumulate")


def test_hop_dong_prompt_cong_bo_thu_tu_that():
    from app.simulation.catalog import CATALOG

    contract = CATALOG[TARGET].contract
    for stage in PIPELINE_STAGE_ORDER:
        assert stage in contract
    assert "limit" in contract and "aggregate" in contract


def test_stages_of_doc_thang_spec_khong_doc_narration():
    cfg = {"specVersion": "table-1.0", "schema": _L4_SCHEMA, "rows": _L4_ROWS,
           **_FULL, "notes": "có lọc, có sắp xếp, có trung bình"}
    assert stages_of(cfg) == {"filter": True, "projection": True, "sort": True,
                              "limit": True, "aggregate": True}
    tron = {"specVersion": "table-1.0", "schema": _L4_SCHEMA, "rows": _L4_ROWS,
            "notes": "đã lọc và sắp xếp và tính trung bình rồi"}
    assert stages_of(tron) == {"filter": False, "projection": False, "sort": False,
                               "limit": False, "aggregate": False}
