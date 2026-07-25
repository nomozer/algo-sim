# -*- coding: utf-8 -*-
"""M17 W2B-PATCH3 §B/§C/§H — VALIDATOR HOÀN CHỈNH THAM SỐ TẦNG (analyze).

Sự cố live P2 (`docs/evaluation/m17/w2b-patch2/`, SHA `4d9e8ac`): analyze phát đủ
5 operation nhưng để TRỐNG tham số bắt buộc của 4/5 tầng (chỉ `sort` có tham số).
Manifest đúng khi KHÔNG tự đoán → merge không bù được → fail-closed. Root defect
nằm ở analyze parameter completeness.

Validator này chạy SAU analyze, TRƯỚC manifest/simulate: một operation name MỘT
MÌNH KHÔNG đủ evidence — tầng chỉ grounded khi mọi tham số bắt buộc đã có.
"""

from __future__ import annotations

from app.simulation.analyze_table_params import validate_table_parameters

# ── EXACT live P2 analyze payload (chép nguyên từ artifact 4d9e8ac, KHÔNG
#    hand-populate) — 5 operation, 4 tầng thiếu tham số bắt buộc ──
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


def _an(reqs):
    return {"requested_requirements": reqs}


# ════════════════════════════════════════════════════════════════════════
# §G — EXACT LIVE SYMPTOM: validator PHẢI phát hiện 4 tầng incomplete
# ════════════════════════════════════════════════════════════════════════
def test_exact_live_p2_payload_incomplete():
    r = validate_table_parameters(_an(_LIVE_P2_REQS))
    assert r["analyze_parameter_decision"] == "incomplete"
    assert set(r["requested_stages"]) == {"filter", "projection", "sort", "limit", "aggregate"}
    assert r["grounded_stages"] == ["sort"]
    assert set(r["incomplete_stages"]) == {"filter", "projection", "limit", "aggregate"}


def test_exact_live_p2_missing_parameters_dung_tung_tang():
    r = validate_table_parameters(_an(_LIVE_P2_REQS))
    mp = r["missing_parameters_by_stage"]
    assert set(mp["filter"]) == {"filter_column", "filter_op", "filter_value"}
    assert mp["projection"] == ["projection_columns"]
    assert mp["limit"] == ["limit"]
    assert mp["aggregate"] == ["aggregate_column"]  # func 'avg' suy từ operation


# ════════════════════════════════════════════════════════════════════════
# §B — grounded khi ĐỦ tham số bắt buộc
# ════════════════════════════════════════════════════════════════════════
def _full_p2():
    g = {"query_group": 1}
    return [
        {"operation": "relational_table_query:filter", **g,
         "filter_column": "Tổ", "filter_op": "=", "filter_value": "A"},
        {"operation": "relational_table_query:projection", **g,
         "projection_columns": ["Tên", "Điểm"]},
        {"operation": "relational_table_query:sort", **g,
         "sort_column": "Điểm", "sort_direction": "desc"},
        {"operation": "relational_table_query:limit", **g, "limit": 3},
        {"operation": "relational_table_query:avg", **g,
         "aggregate_func": "avg", "aggregate_column": "Điểm"},
    ]


def test_du_tham_so_thi_grounded_complete():
    r = validate_table_parameters(_an(_full_p2()))
    assert r["analyze_parameter_decision"] == "complete"
    assert set(r["grounded_stages"]) == {"filter", "projection", "sort", "limit", "aggregate"}
    assert r["incomplete_stages"] == []


# ── §H positive 6/7/8 — ngoại lệ null-operator + COUNT(*) ─────────
def test_H6_filter_is_not_null_khong_can_value():
    reqs = [{"operation": "relational_table_query:filter", "query_group": 1,
             "filter_column": "Điểm", "filter_op": "is not null"}]
    r = validate_table_parameters(_an(reqs))
    assert r["grounded_stages"] == ["filter"]
    assert r["analyze_parameter_decision"] == "complete"


def test_H7_count_star_khong_can_column():
    reqs = [{"operation": "relational_table_query:count", "query_group": 1,
             "aggregate_func": "count", "count_mode": "star"}]
    r = validate_table_parameters(_an(reqs))
    assert r["grounded_stages"] == ["aggregate"]
    assert r["analyze_parameter_decision"] == "complete"


def test_H8_count_column_yeu_cau_column():
    reqs = [{"operation": "relational_table_query:count", "query_group": 1,
             "aggregate_func": "count", "aggregate_column": "Tên"}]
    r = validate_table_parameters(_an(reqs))
    assert r["grounded_stages"] == ["aggregate"]
    # count có cột → hợp lệ, count(*) hay count(cột) đều được, đủ tham số
    assert r["analyze_parameter_decision"] == "complete"


# ── §H negative 1-7 ──────────────────────────────────────────────
def test_neg1_limit_khong_co_so():
    reqs = [{"operation": "relational_table_query:limit", "query_group": 1}]
    r = validate_table_parameters(_an(reqs))
    assert "limit" in r["incomplete_stages"]
    assert "limit" in r["missing_parameters_by_stage"]["limit"]


def test_neg2_avg_khong_xac_dinh_cot():
    reqs = [{"operation": "relational_table_query:avg", "query_group": 1,
             "aggregate_func": "avg"}]  # thiếu aggregate_column
    r = validate_table_parameters(_an(reqs))
    assert "aggregate" in r["incomplete_stages"]
    assert "aggregate_column" in r["missing_parameters_by_stage"]["aggregate"]


def test_neg4_filter_thieu_value_la_incomplete():
    reqs = [{"operation": "relational_table_query:filter", "query_group": 1,
             "filter_column": "Tổ", "filter_op": "="}]  # thiếu value, op cần value
    r = validate_table_parameters(_an(reqs))
    assert "filter" in r["incomplete_stages"]
    assert "filter_value" in r["missing_parameters_by_stage"]["filter"]


def test_neg5_limit_khong_hop_le():
    for bad in (0, -3, 2.5, True):
        reqs = [{"operation": "relational_table_query:limit", "query_group": 1,
                 "limit": bad}]
        r = validate_table_parameters(_an(reqs))
        assert "limit" in r["incomplete_stages"], bad
        assert "limit" in r["invalid_parameters_by_stage"].get("limit", []), bad


def test_neg6_avg_khong_co_column_incomplete():
    reqs = [{"operation": "relational_table_query:avg", "query_group": 1,
             "aggregate_column": None}]
    r = validate_table_parameters(_an(reqs))
    assert "aggregate" in r["incomplete_stages"]


def test_neg7_count_star_bi_doi_thanh_count_column_thi_khong_tu_dong():
    """count_mode='star' KÈM aggregate_column → mâu thuẫn khai báo → invalid,
    KHÔNG tự đoán biến COUNT(*) thành COUNT(cột)."""
    reqs = [{"operation": "relational_table_query:count", "query_group": 1,
             "aggregate_func": "count", "count_mode": "star",
             "aggregate_column": "Tên"}]
    r = validate_table_parameters(_an(reqs))
    assert "aggregate" in r["incomplete_stages"]
    assert "aggregate" in r["invalid_parameters_by_stage"]


# ── §D — literal giữ type, không đoán ─────────────────────────────
def test_filter_value_giu_type_string_khong_ep_so():
    reqs = [{"operation": "relational_table_query:filter", "query_group": 1,
             "filter_column": "Mã", "filter_op": "=", "filter_value": "3"}]
    r = validate_table_parameters(_an(reqs))
    assert r["analyze_parameter_decision"] == "complete"
    # validator KHÔNG được ép "3" thành số — chỉ kiểm presence
    assert r["grounded_stages"] == ["filter"]


def test_filter_value_zero_khong_bi_coi_la_thieu():
    reqs = [{"operation": "relational_table_query:filter", "query_group": 1,
             "filter_column": "Điểm", "filter_op": "=", "filter_value": 0}]
    r = validate_table_parameters(_an(reqs))
    assert r["analyze_parameter_decision"] == "complete", "0 là giá trị hợp lệ"


# ── §H negative 10 — family khác KHÔNG phát sinh table check ──────
def test_neg10_family_khac_khong_bi_anh_huong():
    reqs = [{"operation": "tree_traversal:preorder", "query_group": 1}]
    r = validate_table_parameters(_an(reqs))
    assert r["requested_stages"] == []
    assert r["analyze_parameter_decision"] == "not_applicable"


def test_analyze_khong_co_requested_requirements():
    r = validate_table_parameters({})
    assert r["analyze_parameter_decision"] == "not_applicable"
    r2 = validate_table_parameters({"requested_requirements": None})
    assert r2["analyze_parameter_decision"] == "not_applicable"


def test_khong_chua_ket_qua_cuoi():
    r = validate_table_parameters(_an(_full_p2()))
    blob = repr(r)
    for banned in ("result_rows", "aggregateResult", "8.5", "counted"):
        assert banned not in blob
