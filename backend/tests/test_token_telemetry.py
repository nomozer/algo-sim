# -*- coding: utf-8 -*-
"""Đo token theo TỪNG STAGE — điều kiện tiên quyết của mọi tối ưu (spec §6.1).

Trước wave này `usageMetadata` không được ghi ở BẤT KỲ đâu trong backend
(spec E12), nên "tốn ít token" là mong muốn chứ chưa phải số.
"""
import pytest

from app.ai.telemetry import record_usage, reset_usage, usage_report


@pytest.fixture(autouse=True)
def _sach():
    reset_usage()
    yield
    reset_usage()


def test_ghi_du_nam_truong_theo_stage():
    record_usage(
        "analyze",
        {
            "promptTokenCount": 1200,
            "candidatesTokenCount": 300,
            "cachedContentTokenCount": 800,
            "totalTokenCount": 1500,
            "thoughtsTokenCount": 40,
        },
    )
    rep = usage_report()["analyze"]
    assert rep["prompt_tokens"] == 1200
    assert rep["candidates_tokens"] == 300
    assert rep["cached_content_tokens"] == 800
    assert rep["total_tokens"] == 1500
    assert rep["thoughts_tokens"] == 40
    assert rep["calls"] == 1


def test_thieu_thoughts_thi_ve_0_khong_no():
    """`thoughtsTokenCount` chỉ có ở một số model — vắng mặt không được làm hỏng."""
    record_usage("classify", {"promptTokenCount": 10, "totalTokenCount": 12})
    rep = usage_report()["classify"]
    assert rep["thoughts_tokens"] == 0
    assert rep["cached_content_tokens"] == 0


def test_cong_don_nhieu_luot_cung_stage():
    record_usage("simulate", {"totalTokenCount": 100})
    record_usage("simulate", {"totalTokenCount": 250})
    rep = usage_report()["simulate"]
    assert rep["total_tokens"] == 350
    assert rep["calls"] == 2


def test_tach_bach_giua_cac_stage():
    record_usage("analyze", {"totalTokenCount": 100})
    record_usage("semantic_program", {"totalTokenCount": 700})
    rep = usage_report()
    assert rep["analyze"]["total_tokens"] == 100
    assert rep["semantic_program"]["total_tokens"] == 700


def test_usage_rong_hoac_none_thi_bo_qua():
    record_usage("analyze", None)
    record_usage("analyze", {})
    assert usage_report() == {}


def test_gia_tri_la_khong_lam_no():
    """API trả kiểu lạ thì đếm 0, không được ném lỗi giữa pipeline."""
    record_usage("analyze", {"totalTokenCount": None, "promptTokenCount": "x"})
    assert usage_report()["analyze"]["total_tokens"] == 0
