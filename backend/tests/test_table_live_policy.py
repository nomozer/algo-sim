# -*- coding: utf-8 -*-
"""M17 W2B-PATCH2 §F/§I — CHÍNH SÁCH CHẤM + DỪNG cho live runner bảng.

`final_result_accepted` (§F): chấp nhận ca P1 (LLM thêm non-null filter trên cột
tổng hợp) là ĐÚNG khi giá trị + counted khớp, KHÔNG nới thành tolerance chung.

`supported_stop_reason` (§I): với case supported, MỌI status khác "ok" đều là lỗi
và phải DỪNG — vá đúng lỗ hổng runner cũ (chỉ dừng khi status=="error", nên P2
trả "unsupported" đã lọt qua tới P4).
"""

from __future__ import annotations

from app.evaluation.table_plan_equivalence import (
    final_result_accepted,
    supported_stop_reason,
)


def _plan(**kw):
    base = {"filter": None, "projection": None, "sort": None, "limit": None,
            "aggregate": None, "wants_rows": False}
    base.update(kw)
    return base


# ── §F — chấp nhận kết quả ───────────────────────────────────────
def test_final_khop_het_thi_chap_nhan():
    ef = {"rows": [{"a": 1}], "aggregate": {"value": 8.25, "counted": 4}}
    r = final_result_accepted(ef, dict(ef), _plan(aggregate={"func": "avg", "column": "d"}),
                              _plan(aggregate={"func": "avg", "column": "d"}))
    assert r["accepted"] is True and r["rule"] == "identical"


def test_P1_rows_lech_nhung_non_null_filter_tuong_duong_chap_nhan():
    """P1 THẬT: expected giữ 6 dòng (2 None); represented lọc còn 4; AVG 8.25/4
    cả hai. Kế hoạch tương đương ⇒ chấp nhận."""
    expected = {"rows": [1, 2, 3, 4, 5, 6], "aggregate": {"value": 8.25, "counted": 4}}
    actual = {"rows": [1, 3, 4, 6], "aggregate": {"value": 8.25, "counted": 4}}
    req = _plan(aggregate={"func": "avg", "column": "diem"})
    rep = _plan(filter={"op": "!=", "column": "diem", "value": None},
                aggregate={"func": "avg", "column": "diem"})
    r = final_result_accepted(expected, actual, req, rep)
    assert r["accepted"] is True
    assert r["rule"] == "aggregate_ignores_null_filter"
    assert r["equivalence"]["equivalent"] is True


def test_gia_tri_aggregate_lech_thi_KHONG_chap_nhan_du_ke_hoach_tuong_duong():
    """§F điều kiện 6: giá trị/counted phải khớp — lệch số thì từ chối, kể cả
    kế hoạch trông tương đương."""
    expected = {"rows": [1, 2], "aggregate": {"value": 8.25, "counted": 4}}
    actual = {"rows": [1], "aggregate": {"value": 9.0, "counted": 3}}
    req = _plan(aggregate={"func": "avg", "column": "diem"})
    rep = _plan(filter={"op": "!=", "column": "diem", "value": None},
                aggregate={"func": "avg", "column": "diem"})
    assert final_result_accepted(expected, actual, req, rep)["accepted"] is False


def test_ke_hoach_khong_tuong_duong_thi_rows_lech_la_that_bai():
    """filter cột khác → không tương đương → rows lệch là lỗi thật."""
    expected = {"rows": [1, 2, 3], "aggregate": {"value": 8.5, "counted": 3}}
    actual = {"rows": [1, 2], "aggregate": {"value": 8.5, "counted": 3}}
    req = _plan(aggregate={"func": "avg", "column": "diem"})
    rep = _plan(filter={"op": "=", "column": "to", "value": "A"},
                aggregate={"func": "avg", "column": "diem"})
    assert final_result_accepted(expected, actual, req, rep)["accepted"] is False


def test_khong_aggregate_thi_rows_phai_khop_dung():
    """Đề trả danh sách hàng (không aggregate) → rows lệch là lỗi, không nới."""
    expected = {"rows": [1, 2, 3], "aggregate": None}
    actual = {"rows": [1, 2], "aggregate": None}
    req = _plan(filter={"op": ">=", "column": "diem", "value": 8},
                projection=["ten"], wants_rows=True)
    assert final_result_accepted(expected, actual, req, dict(req))["accepted"] is False


# ── §I — chính sách DỪNG cho supported case ──────────────────────
def test_status_ok_thi_khong_dung():
    assert supported_stop_reason("ok", grounding_perfect=True,
                                 result_leakage=False, dropped_stages=[]) is None


def test_status_error_thi_dung():
    assert supported_stop_reason("error", grounding_perfect=None,
                                 result_leakage=False, dropped_stages=[]) is not None


def test_status_unsupported_thi_dung():
    """LỖ HỔNG CŨ: runner chỉ dừng khi 'error' nên P2 ('unsupported') lọt qua."""
    r = supported_stop_reason("unsupported", grounding_perfect=None,
                              result_leakage=False, dropped_stages=[])
    assert r is not None


def test_status_semantic_incomplete_va_none_deu_dung():
    kw = dict(grounding_perfect=None, result_leakage=False, dropped_stages=[])
    assert supported_stop_reason("semantic_incomplete", **kw) is not None
    assert supported_stop_reason(None, **kw) is not None
    assert supported_stop_reason("insufficient_specification", **kw) is not None


def test_ok_nhung_ro_ri_ket_qua_van_dung():
    assert supported_stop_reason("ok", grounding_perfect=True,
                                 result_leakage=True, dropped_stages=[]) is not None


def test_ok_nhung_thieu_tang_van_dung():
    assert supported_stop_reason("ok", grounding_perfect=True,
                                 result_leakage=False, dropped_stages=["limit"]) is not None
