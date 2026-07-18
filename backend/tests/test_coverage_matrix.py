"""M14 §O — lock coverage matrix: enum ĐÓNG, mỗi unit đúng một status, khai trung thực."""

from __future__ import annotations

import dataclasses

import pytest

from app.simulation.coverage import (
    KNOWLEDGE_UNITS,
    CoverageStatus,
    KnowledgeUnit,
    coverage_rows,
)

VALID_STATUSES = set(CoverageStatus)


def test_moi_unit_co_status_thuoc_enum_dong():
    for u in KNOWLEDGE_UNITS:
        assert isinstance(u.status, CoverageStatus), f"{u.unit_id} status ngoài enum"
    # rows dùng .value → phải là một trong 5 chuỗi enum, không trạng thái tự do
    allowed = {s.value for s in CoverageStatus}
    for row in coverage_rows():
        assert row["status"] in allowed


def test_unit_id_khong_trung():
    ids = [u.unit_id for u in KNOWLEDGE_UNITS]
    assert len(ids) == len(set(ids)), "unit_id trùng"


def test_moi_unit_co_anchor_va_label_khong_rong():
    for u in KNOWLEDGE_UNITS:
        assert u.curriculum_anchor.strip(), f"{u.unit_id} thiếu curriculum_anchor"
        assert u.label.strip(), f"{u.unit_id} thiếu label"


def test_gap_va_out_of_scope_duoc_khai_trung_thuc():
    by_id = {u.unit_id: u for u in KNOWLEDGE_UNITS}
    # §7b: Dijkstra trọng số là CAPABILITY_GAP (câu trả lời đúng dài hạn), không SUPPORTED
    assert by_id["dijkstra_weighted_shortest_path"].status is CoverageStatus.CAPABILITY_GAP
    # CSDL bảng/truy vấn chưa có → gap trung thực, không được tô SUPPORTED
    assert by_id["database_table_query"].status is CoverageStatus.CAPABILITY_GAP
    # §7 trang trí → OUT_OF_SCOPE
    assert by_id["ai_ml_datascience_overview"].status is CoverageStatus.OUT_OF_SCOPE


def test_sorting_la_supported_M15_claim_boundary():
    # M15 W5 (Task 16): pilot M14 tốt nghiệp SUPPORTED sau khi formalize thành
    # comparison_sort family selector (M15 W1-W3). Note PHẢI tự giới hạn claim:
    # n nhỏ (targeted acceptance), không phải bằng chứng thống kê.
    by_id = {u.unit_id: u for u in KNOWLEDGE_UNITS}
    sorting = by_id["sorting"]
    assert sorting.status is CoverageStatus.SUPPORTED
    assert "không phải bằng chứng thống kê" in sorting.note.lower()


def test_khong_yeu_cau_tat_ca_SUPPORTED_nhung_phai_co_it_nhat_moi_trang_thai_dung_ngu_canh():
    # O4: không yêu cầu 100% SUPPORTED — matrix phải trung thực có cả gap/out-of-scope
    statuses = {u.status for u in KNOWLEDGE_UNITS}
    assert CoverageStatus.CAPABILITY_GAP in statuses
    assert CoverageStatus.OUT_OF_SCOPE in statuses
    # M15 W5: sorting tốt nghiệp PILOT → SUPPORTED (xem
    # test_sorting_la_supported_M15_claim_boundary) — hiện KHÔNG còn unit nào
    # ở PILOT; enum member vẫn mở cho pilot tương lai, không xoá.


def test_knowledge_unit_immutable():
    u = KNOWLEDGE_UNITS[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        u.status = CoverageStatus.SUPPORTED  # type: ignore[misc]
