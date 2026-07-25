# -*- coding: utf-8 -*-
"""M17 W2B-PATCH2 §B/§C/§D/§H — MANIFEST TẦNG TẤT ĐỊNH + MERGE.

Sự cố live P2 (`docs/evaluation/m17/w2b-patch/live_table_query_patch_report.md`):
đề NĂM tầng, LLM gửi lại spec BA tầng ba lần dù nhận đúng "THIẾU: limit,
aggregate". Cổng fail-closed chặn đúng (0 semantic loss) nhưng đề HỢP LỆ lại
kết thúc bằng từ chối — vi phạm §A (target đã KHAI hỗ trợ 5 tầng thì phải có
đường sinh spec đủ tầng, kiểm chứng được).

Bản vá: từ analyze CÓ CẤU TRÚC (`requested_requirements`) dựng TẤT ĐỊNH một
`RequiredTablePipeline`, rồi MERGE các tầng grounded vào candidate của LLM —
LLM không còn là nguồn DUY NHẤT quyết định tầng nào tồn tại.

RECONSTRUCTION NOTE (trung thực): observer live KHÔNG lưu `requested_requirements`
lẫn candidate spec thô (hai lỗ đo, đã vá ở observer). Ba "failed candidate" ở
đây được TÁI DỰNG trung thành từ bằng chứng đã ghi — thông điệp retry nêu ĐÍCH
DANH tầng nào có mặt (filter/projection/sort) và tầng nào thiếu (limit,
aggregate) trên bảng L4. Tham số tầng lấy từ chính prompt L4 (đã khoá ở oracle).
"""

from __future__ import annotations

import pytest

from app.simulation.table_pipeline_manifest import (
    build_required_pipeline,
    merge_required_stages,
)
from app.simulation.table_query_engine import run_table_query
from app.validation.table_query import validate_table_query_config

# ── bảng + analyze L4 THẬT (tái dựng từ requested_requirements có cấu trúc) ──
_L4_SCHEMA = [
    {"name": "ten", "type": "text", "label": "Tên"},
    {"name": "to", "type": "text", "label": "Tổ"},
    {"name": "diem", "type": "number", "label": "Điểm"},
    {"name": "vang", "type": "number", "label": "Số buổi vắng"},
]
_L4_ROWS = [
    ["An", "A", "9.0", "1"], ["Bình", "B", "8.5", "0"], ["Chi", "A", "6.0", "2"],
    ["Dũng", "A", "9.0", "0"], ["Hà", "B", "7.5", "3"], ["Lan", "A", "7.5", "1"],
    ["Minh", "A", "6.0", "0"], ["Nga", "B", "9.5", "2"],
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
_L4_ANALYSIS = {"requested_requirements": _L4_REQS,
                "requested_operations": sorted({r["operation"] for r in _L4_REQS})}


def _candidate(**stages) -> dict:
    """Candidate LLM (schema + rows + các tầng LLM tự điền)."""
    return {"specVersion": "table-1.0", "schema": _L4_SCHEMA,
            "rows": [dict(zip([c["name"] for c in _L4_SCHEMA], r)) for r in _L4_ROWS],
            **stages}


# Ba "failed candidate" TÁI DỰNG: filter + projection + sort, THIẾU limit+aggregate.
def _three_stage_candidate() -> dict:
    return _candidate(
        filter={"op": "=", "column": "to", "value": "A"},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"},
    )


def _validated(cfg: dict) -> dict:
    v, err = validate_table_query_config(cfg)
    assert err is None, err
    return v


# ════════════════════════════════════════════════════════════════════════
# §B — MANIFEST đủ 5 tầng, KHÔNG chứa kết quả
# ════════════════════════════════════════════════════════════════════════
def test_manifest_du_5_tang_dung_thu_tu():
    p = build_required_pipeline(_L4_ANALYSIS)
    assert p is not None
    assert [s.kind for s in p.ordered_stages] == \
        ["filter", "projection", "sort", "limit", "aggregate"]


def test_manifest_moi_tang_grounded_dung_tham_so():
    p = build_required_pipeline(_L4_ANALYSIS)
    by = {s.kind: s for s in p.ordered_stages}
    assert all(s.grounded for s in p.ordered_stages)
    assert by["filter"].params == {"column": "Tổ", "op": "=", "value": "A"}
    assert by["projection"].params == {"columns": ["Tên", "Điểm"]}
    assert by["sort"].params == {"column": "Điểm", "direction": "desc"}
    assert by["limit"].params == {"count": 3}
    assert by["aggregate"].params == {"func": "avg", "column": "Điểm"}


def test_manifest_khong_chua_ket_qua():
    p = build_required_pipeline(_L4_ANALYSIS)
    blob = repr(p.as_dict())
    for banned in ("result_rows", "aggregateResult", "8.5", "counted",
                   "accepted", "rejected", "ordered_indices"):
        assert banned not in blob


def test_manifest_co_order_version():
    p = build_required_pipeline(_L4_ANALYSIS)
    assert p.order_version  # phiên bản thứ tự pipeline, không rỗng


def test_manifest_aggregate_func_suy_tu_operation_khi_thieu_field():
    """analyze mã hoá func trong chính operation (`:avg`) mà không điền
    aggregate_func → vẫn grounded, func='avg' (không phụ thuộc một field)."""
    analysis = {"requested_requirements": [
        {"operation": "relational_table_query:avg", "query_group": 1,
         "aggregate_column": "Điểm"},  # KHÔNG có aggregate_func
    ]}
    p = build_required_pipeline(analysis)
    agg = p.stage("aggregate")
    assert agg.grounded is True
    assert agg.params == {"func": "avg", "column": "Điểm"}


def test_manifest_none_khi_khong_co_requested_requirements():
    assert build_required_pipeline({"requested_requirements": None}) is None
    assert build_required_pipeline({}) is None


# ════════════════════════════════════════════════════════════════════════
# §C/§D/§H — MERGE khôi phục tầng thiếu, giữ phần hợp lệ
# ════════════════════════════════════════════════════════════════════════
def test_H_candidate_ba_tang_duoc_merge_thanh_nam_tang():
    p = build_required_pipeline(_L4_ANALYSIS)
    cand = _validated(_three_stage_candidate())
    merged, log = merge_required_stages(cand, p)

    v, err = validate_table_query_config(merged)
    assert err is None, err
    assert v["limit"] == 3
    assert v["aggregate"] == {"func": "avg", "column": "diem"}
    # phần LLM đã làm đúng được GIỮ
    assert v["filter"] == {"op": "=", "column": "to", "value": "A"}
    assert v["projection"] == ["ten", "diem"]
    assert v["sort"] == {"column": "diem", "direction": "desc"}
    assert set(log["inserted_stages"]) == {"limit", "aggregate"}
    assert log["merge_applied"] is True


def test_H_merged_final_dung_ket_qua():
    p = build_required_pipeline(_L4_ANALYSIS)
    merged, _ = merge_required_stages(_validated(_three_stage_candidate()), p)
    out = run_table_query(_validated(merged))
    assert [r["ten"] for r in out["result_rows"]] == ["An", "Dũng", "Lan"]
    assert out["aggregateResult"]["value"] == pytest.approx(8.5)
    assert out["aggregateResult"]["counted"] == 3
    for leak in ("aggregateResult", "result_rows", "ordered_indices", "steps"):
        assert leak not in merged


def test_H_merge_ghi_log_day_du():
    p = build_required_pipeline(_L4_ANALYSIS)
    _, log = merge_required_stages(_validated(_three_stage_candidate()), p)
    for key in ("candidate_stage_set", "inserted_stages", "corrected_stages",
                "confirmed_stages", "unresolved_fields", "merge_applied"):
        assert key in log
    assert set(log["candidate_stage_set"]) == {"filter", "projection", "sort"}


def test_H_candidate_du_5_tang_khong_bi_dung_cham():
    """Candidate đã đủ + đúng → merge chỉ XÁC NHẬN, không sửa gì."""
    p = build_required_pipeline(_L4_ANALYSIS)
    full = _validated(_candidate(
        filter={"op": "=", "column": "to", "value": "A"},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"},
        limit=3, aggregate={"func": "avg", "column": "diem"}))
    merged, log = merge_required_stages(full, p)
    assert log["inserted_stages"] == []
    assert log["corrected_stages"] == []
    assert set(log["confirmed_stages"]) == {"filter", "projection", "sort",
                                            "limit", "aggregate"}


# ── FAULT INJECTION §H 1-5 ──────────────────────────────────────
def test_H_fault1_xoa_limit_duoc_khoi_phuc():
    p = build_required_pipeline(_L4_ANALYSIS)
    cand = _validated(_candidate(
        filter={"op": "=", "column": "to", "value": "A"},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"},
        aggregate={"func": "avg", "column": "diem"}))  # THIẾU limit
    merged, log = merge_required_stages(cand, p)
    assert merged["limit"] == 3
    assert "limit" in log["inserted_stages"]
    assert run_table_query(_validated(merged))["aggregateResult"]["counted"] == 3


def test_H_fault2_xoa_aggregate_duoc_khoi_phuc():
    p = build_required_pipeline(_L4_ANALYSIS)
    cand = _validated(_candidate(
        filter={"op": "=", "column": "to", "value": "A"},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"}, limit=3))  # THIẾU aggregate
    merged, log = merge_required_stages(cand, p)
    assert merged["aggregate"] == {"func": "avg", "column": "diem"}
    assert "aggregate" in log["inserted_stages"]


def test_H_fault3_limit_sai_so_bi_phat_hien_va_sua():
    """limit 3→5 SAI: merge PHÁT HIỆN (ghi log) và sửa về đúng manifest."""
    p = build_required_pipeline(_L4_ANALYSIS)
    cand = _validated(_candidate(
        filter={"op": "=", "column": "to", "value": "A"},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"},
        limit=5, aggregate={"func": "avg", "column": "diem"}))
    merged, log = merge_required_stages(cand, p)
    assert merged["limit"] == 3
    corr = {c["stage"]: c for c in log["corrected_stages"]}
    assert "limit" in corr
    assert corr["limit"]["from"] == 5 and corr["limit"]["to"] == 3


def test_H_fault4_aggregate_sai_ham_bi_phat_hien_va_sua():
    p = build_required_pipeline(_L4_ANALYSIS)
    cand = _validated(_candidate(
        filter={"op": "=", "column": "to", "value": "A"},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"}, limit=3,
        aggregate={"func": "sum", "column": "diem"}))  # SUM sai, phải là AVG
    merged, log = merge_required_stages(cand, p)
    assert merged["aggregate"]["func"] == "avg"
    corr = {c["stage"]: c for c in log["corrected_stages"]}
    assert "aggregate" in corr


def test_H_fault5_thu_tu_tang_luon_canonical():
    """Không có cách biểu diễn thứ tự khác trong spec (dict theo tên tầng);
    engine LUÔN áp canonical order → aggregate SAU limit."""
    from app.simulation.table_query_engine import PIPELINE_STAGE_ORDER
    p = build_required_pipeline(_L4_ANALYSIS)
    merged, _ = merge_required_stages(_validated(_three_stage_candidate()), p)
    out = run_table_query(_validated(merged))
    kinds = [s["kind"] for s in out["steps"]]
    assert kinds.index("limit") < kinds.index("accumulate")
    # thứ tự authoritative do engine sở hữu, không do thứ tự khoá trong spec
    assert PIPELINE_STAGE_ORDER == ("filter", "projection", "sort", "limit", "aggregate")


# ── §C/§E — KHÔNG bịa tầng khi analyze thiếu evidence ────────────
def test_tang_khong_grounded_khong_bi_merge_bia():
    """analyze nêu sort nhưng THIẾU cột sort → không grounded → merge KHÔNG chèn."""
    analysis = {"requested_requirements": [
        {"operation": "relational_table_query:sort", "query_group": 1},  # thiếu sort_column
        {"operation": "relational_table_query:filter", "query_group": 1,
         "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
    ]}
    p = build_required_pipeline(analysis)
    by = {s.kind: s for s in p.ordered_stages}
    assert by["sort"].grounded is False
    assert "sort_column" in by["sort"].unresolved_fields
    cand = _validated(_candidate())  # LLM cũng không có sort
    merged, log = merge_required_stages(cand, p)
    assert merged.get("sort") is None, "không grounded thì KHÔNG được bịa"
    assert "filter" in log["inserted_stages"]
    assert any(u.startswith("sort:") for u in log["unresolved_fields"])


def test_column_khong_co_trong_schema_thi_khong_ground_duoc():
    """Manifest nêu cột mà schema LLM không có → không resolve được → không chèn."""
    analysis = {"requested_requirements": [
        {"operation": "relational_table_query:aggregate"
                      if False else "relational_table_query:avg",
         "query_group": 1, "aggregate_func": "avg", "aggregate_column": "Cột Lạ"},
    ]}
    p = build_required_pipeline(analysis)
    cand = _validated(_candidate())
    merged, log = merge_required_stages(cand, p)
    assert merged.get("aggregate") is None
    assert any("aggregate" in u for u in log["unresolved_fields"])


def test_merge_khong_bao_gio_them_final_result():
    p = build_required_pipeline(_L4_ANALYSIS)
    merged, _ = merge_required_stages(_validated(_three_stage_candidate()), p)
    for banned in ("aggregateResult", "result_rows", "filtered_indices",
                   "ordered_indices", "steps"):
        assert banned not in merged
