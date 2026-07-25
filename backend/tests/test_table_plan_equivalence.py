# -*- coding: utf-8 -*-
"""M17 W2B-PATCH2 §F/§G — TƯƠNG ĐƯƠNG NGỮ NGHĨA hai kế hoạch truy vấn.

Sự cố live P1: đề "Tính điểm trung bình của CÁC Ô CÓ DỮ LIỆU". Oracle của ta
khoá kế hoạch = chỉ `aggregate avg`. LLM sinh `filter(cột điểm IS NOT NULL) +
aggregate avg` — cùng ra 8.25/4, grounding perfect, empty→0=0. Runner chấm LỆCH
vì so `rows` (4 vs 6) mặc dù giá trị vô hướng cần tìm bằng nhau.

Quy tắc HẸP có chủ đích (KHÔNG phải tolerance chung cho mọi tầng thừa): chỉ coi
hai kế hoạch tương đương khi tầng thừa duy nhất là NON-NULL CHECK trên chính cột
tổng hợp, mục tiêu là vô hướng, và hàm tổng hợp vốn đã bỏ qua null.

Đây là lớp ĐÁNH GIÁ (audit/runner), KHÔNG đổi hành vi production; production chạy
đúng spec nào cũng ra cùng con số.
"""

from __future__ import annotations

from app.evaluation.table_plan_equivalence import plans_equivalent

# Kế hoạch = {filter, projection, sort, limit, aggregate, wants_rows}.
# Tham số ở KHÔNG GIAN ID cột (đã resolve).


def _plan(filter=None, projection=None, sort=None, limit=None, aggregate=None,
          wants_rows=False):
    return {"filter": filter, "projection": projection, "sort": sort,
            "limit": limit, "aggregate": aggregate, "wants_rows": wants_rows}


def _isnotnull(col):
    return {"op": "!=", "column": col, "value": None}


# ── §G — CA DƯƠNG: filter non-null trên cột agg ⇔ aggregate thuần ──
def test_avg_voi_non_null_filter_tuong_duong_avg_thuan():
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter=_isnotnull("diem"),
                        aggregate={"func": "avg", "column": "diem"})
    r = plans_equivalent(requested, represented)
    assert r["equivalent"] is True
    assert r["rule"] == "aggregate_ignores_null_filter"


def test_sum_min_max_cung_tuong_duong_khi_null_ignored():
    for func in ("sum", "min", "max"):
        requested = _plan(aggregate={"func": func, "column": "diem"})
        represented = _plan(filter=_isnotnull("diem"),
                            aggregate={"func": func, "column": "diem"})
        assert plans_equivalent(requested, represented)["equivalent"] is True, func


def test_count_column_voi_non_null_filter_tuong_duong():
    requested = _plan(aggregate={"func": "count", "column": "diem"})
    represented = _plan(filter=_isnotnull("diem"),
                        aggregate={"func": "count", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is True


def test_hai_ke_hoach_giong_het_nhau_tuong_duong():
    p = _plan(aggregate={"func": "avg", "column": "diem"})
    r = plans_equivalent(p, dict(p))
    assert r["equivalent"] is True
    assert r["rule"] == "identical"


# ── §G — CA ÂM: KHÔNG được coi là tương đương ──────────────────
def test_am1_filter_cot_khac_khong_tuong_duong():
    """AVG Điểm nhưng filter Tổ=A → thay đổi tập dòng có ý nghĩa."""
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter={"op": "=", "column": "to", "value": "A"},
                        aggregate={"func": "avg", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am2_filter_nguong_gia_tri_khong_tuong_duong():
    """AVG Điểm nhưng filter Điểm>=8 → KHÔNG phải non-null check."""
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter={"op": ">=", "column": "diem", "value": 8},
                        aggregate={"func": "avg", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am3_count_sao_khong_tuong_duong_voi_non_null():
    """COUNT(*) đếm CẢ ô trống; non-null filter đổi kết quả → KHÔNG tương đương."""
    requested = _plan(aggregate={"func": "count", "column": None})
    represented = _plan(filter=_isnotnull("diem"),
                        aggregate={"func": "count", "column": None})
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am4_them_limit_khong_tu_bo_qua():
    """AVG + limit: tầng thừa là limit, KHÔNG phải non-null → không tương đương."""
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter=_isnotnull("diem"), limit=3,
                        aggregate={"func": "avg", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am5_query_can_tra_rows_thi_row_set_co_y_nghia():
    """Đề cần TRẢ danh sách hàng → khác tập hàng là khác kết quả."""
    requested = _plan(aggregate={"func": "avg", "column": "diem"}, wants_rows=True)
    represented = _plan(filter=_isnotnull("diem"),
                        aggregate={"func": "avg", "column": "diem"},
                        wants_rows=True)
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am6_them_projection_khong_tuong_duong():
    """Non-null filter OK nhưng KÈM projection → không còn "chỉ" non-null."""
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter=_isnotnull("diem"), projection=["ten", "diem"],
                        aggregate={"func": "avg", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am7_hai_predicate_khong_tuong_duong():
    """filter là AND(non-null, khác) → có predicate bổ sung → không tương đương."""
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(
        filter={"op": "and", "clauses": [
            _isnotnull("diem"), {"op": ">=", "column": "diem", "value": 5}]},
        aggregate={"func": "avg", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is False


def test_am8_khac_aggregate_column_khong_tuong_duong():
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter=_isnotnull("vang"),
                        aggregate={"func": "avg", "column": "diem"})
    assert plans_equivalent(requested, represented)["equivalent"] is False


# ── bằng chứng máy-đọc bắt buộc (§F) ─────────────────────────────
def test_ket_qua_ghi_du_bang_chung():
    requested = _plan(aggregate={"func": "avg", "column": "diem"})
    represented = _plan(filter=_isnotnull("diem"),
                        aggregate={"func": "avg", "column": "diem"})
    r = plans_equivalent(requested, represented)
    for key in ("equivalent", "rule", "requested_plan", "represented_plan",
                "structural_difference"):
        assert key in r
    assert r["structural_difference"]["extra_stages"] == ["filter"]
