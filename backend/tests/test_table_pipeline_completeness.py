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


# ── 1. THIẾU TẦNG → không được trả ok ─────────────────────────────
def test_L4_spec_thieu_limit_va_aggregate_bi_chan(monkeypatch):
    """Đúng spec mà live sinh ra: ba tầng đầu, thiếu limit + aggregate.

    LLM được báo lại và vẫn gửi y hệt cả 3 lượt ⇒ từ chối trung thực."""
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                       filter=_FULL["filter"], projection=_FULL["projection"],
                       sort=_FULL["sort"])
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET))] + [thieu] * 3)

    assert env["status"] != "ok", "spec thiếu tầng KHÔNG được trả ok"
    assert env["failure_category"] == "semantic_incomplete"
    assert env.get("simulation_id") is None and env.get("config") is None
    c = env["completeness"]
    assert c["dropped_pipeline_stages"] == ["limit", "aggregate"]
    assert c["requested_pipeline"] == ["filter", "projection", "sort", "limit", "aggregate"]
    assert c["represented_pipeline"] == ["filter", "projection", "sort"]
    assert c["completeness_decision"] == "incomplete"
    for banned in ("{", "}", "None", "aggregate"):
        assert banned not in env["reason"], env["reason"]


def test_L4_khong_bao_gio_leak_sang_generic(monkeypatch):
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"])
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET))] + [thieu] * 3)
    assert env.get("simulation_id") != "generic.rule_scene"
    assert env["status"] == "unsupported"


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


# ── 3. SAI THAM SỐ TẦNG → cũng là trả lời sai đề ─────────────────
def test_L4_limit_sai_so_bi_bat(monkeypatch):
    """Đề xin 3 dòng đầu, spec cắt 5 dòng — có đủ tầng nhưng SAI yêu cầu."""
    sai = _table_cfg(_L4_SCHEMA, _L4_ROWS, **{**_FULL, "limit": 5})
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET))] + [sai] * 3)

    assert env["status"] != "ok"
    mism = env["completeness"]["mismatched_stage_parameters"]
    assert [m["stage"] for m in mism] == ["limit"]
    assert mism[0]["requested"] == 3 and mism[0]["represented"] == 5


def test_L4_ham_tong_hop_sai_bi_bat(monkeypatch):
    sai = _table_cfg(_L4_SCHEMA, _L4_ROWS,
                     **{**_FULL, "aggregate": {"func": "sum", "column": "diem"}})
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET))] + [sai] * 3)
    assert env["status"] != "ok"
    mism = env["completeness"]["mismatched_stage_parameters"]
    assert [m["stage"] for m in mism] == ["aggregate"]
    assert mism[0]["requested"] == "avg" and mism[0]["represented"] == "sum"


# ── SỬA ĐƯỢC THÌ SỬA: thiếu tầng phải quay lại simulate, không từ chối ngay ──
def test_L4_thieu_tang_duoc_bao_lai_va_lan_hai_dung_thi_chay(monkeypatch):
    """§A.4 — mục tiêu cuối là đề HỢP LỆ chạy được đủ, không phải từ chối cho
    xong. Thiếu tầng là lỗi SỬA ĐƯỢC: báo lại cho lượt simulate sau."""
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"],
                       projection=_FULL["projection"], sort=_FULL["sort"])
    du = _table_cfg(_L4_SCHEMA, _L4_ROWS, **_FULL)
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)), thieu, du])

    assert env["status"] == "ok", env.get("reason")
    out = run_table_query(env["config"])
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3


def test_L4_bao_lai_van_thieu_thi_tu_choi_trung_thuc(monkeypatch):
    """Hết lượt mà vẫn thiếu → từ chối trung thực, KHÔNG nhận spec nửa vời."""
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"],
                       projection=_FULL["projection"], sort=_FULL["sort"])
    env = _run(monkeypatch, [_an_l4(), json.dumps(_classify(TARGET)),
                             thieu, thieu, thieu])
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "semantic_incomplete"
    assert env.get("config") is None


def test_loi_bao_lai_neu_dich_danh_tung_buoc_thieu(monkeypatch):
    """Thông điệp gửi lại LLM phải nói RÕ thiếu bước nào — nói chung chung thì
    lượt sau cũng sai y hệt (bài học từ live: retry mù không cứu được gì)."""
    prompts: list[str] = []
    thieu = _table_cfg(_L4_SCHEMA, _L4_ROWS, filter=_FULL["filter"])
    du = _table_cfg(_L4_SCHEMA, _L4_ROWS, **_FULL)
    responses = [_an_l4(), json.dumps(_classify(TARGET)), thieu, du]

    async def spy(api_key, system_prompt, user_text, response_schema=None,
                  temperature=0.2, image=None):
        prompts.append(user_text)
        return responses.pop(0)

    monkeypatch.setattr(pipeline, "call_gemini", spy)
    env = asyncio.run(pipeline.run_pipeline(_L4_ASK, "khoa-gia"))
    assert env["status"] == "ok"
    retry_prompt = prompts[-1]
    assert "projection" in retry_prompt and "sort" in retry_prompt
    assert "limit" in retry_prompt and "aggregate" in retry_prompt


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
