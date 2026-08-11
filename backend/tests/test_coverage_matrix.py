"""M14 §O — lock coverage matrix: enum ĐÓNG, mỗi unit đúng một status, khai trung thực."""

from __future__ import annotations

import dataclasses

import pytest

from app.simulation.coverage import (
    SupportKind,
    curriculum_support_rows,
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
    # CSDL bảng/truy vấn: W2B ĐÃ ship target thật nên không còn là CAPABILITY_GAP,
    # nhưng cũng KHÔNG được tô SUPPORTED — pipeline nhiều tầng bằng ngôn ngữ tự
    # nhiên vẫn PARTIAL/EXPERIMENTAL và Wave 2B chưa CLOSE.
    assert by_id["database_table_query"].status is CoverageStatus.PARTIAL
    assert "NOT CLOSED" in by_id["database_table_query"].note
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


# ── W4B-3A — TRỤC THỨ HAI: KIỂU HỖ TRỢ ────────────────────────────────────
#
# `CoverageStatus` trả lời "có phủ không", `SupportKind` trả lời "học sinh làm
# được gì". Bảng chỉ có trục thứ nhất đọc thành lời hứa lớn hơn sản phẩm: một
# mục chỉ bấm-Tiến-để-xem và một mục học sinh đổi được mô hình đều hiện
# "SUPPORTED" y hệt nhau.


def test_moi_unit_khai_support_kind_thuoc_enum_dong():
    for u in KNOWLEDGE_UNITS:
        assert isinstance(u.support_kind, SupportKind), f"{u.unit_id} support_kind ngoài enum"
    allowed = {k.value for k in SupportKind}
    for row in curriculum_support_rows():
        assert row["support_kind"] in allowed


def test_moi_unit_co_bang_chung_cho_kieu_ho_tro():
    """Khai một KIỂU mà không nói VÌ SAO thì lần sau không ai kiểm lại được."""
    for u in KNOWLEDGE_UNITS:
        assert u.support_evidence.strip(), f"{u.unit_id} thiếu support_evidence"


def test_hai_truc_khong_duoc_mau_thuan_nhau():
    """Ràng buộc chéo — đây mới là chỗ bảng phủ hay nói dối.

    Ngoài phạm vi ⇔ không phải thứ nên mô phỏng; cố ý từ chối ⇒ chưa hỗ trợ.
    Không có chiều ngược lại: một mục PARTIAL vẫn có thể hỗ trợ theo kiểu
    tương tác cho phần đã làm được.
    """
    for u in KNOWLEDGE_UNITS:
        if u.status is CoverageStatus.OUT_OF_SCOPE:
            assert u.support_kind is SupportKind.NOT_SIMULATION_SUITABLE, u.unit_id
        if u.support_kind is SupportKind.NOT_SIMULATION_SUITABLE:
            assert u.status is CoverageStatus.OUT_OF_SCOPE, u.unit_id
        if u.status is CoverageStatus.CAPABILITY_GAP:
            assert u.support_kind is SupportKind.UNSUPPORTED, u.unit_id


def test_khong_duoc_tuyen_bo_phu_toan_bo_chuong_trinh():
    """CURRICULUM_SUPPORT_PARTIAL — giữ nguyên trừ khi CHÍNH bảng chứng minh khác.

    Điều kiện để bỏ nhãn PARTIAL là KHÔNG còn unit nào PARTIAL/UNSUPPORTED trong
    phạm vi đã khoanh. Test này là chỗ phát hiện điều đó, không phải một lời hứa.
    """
    in_scope = [u for u in KNOWLEDGE_UNITS if u.status is not CoverageStatus.OUT_OF_SCOPE]
    unfinished = [u.unit_id for u in in_scope
                  if u.support_kind in (SupportKind.PARTIAL, SupportKind.UNSUPPORTED)]
    assert unfinished, (
        "Không còn unit PARTIAL/UNSUPPORTED nào — nếu đúng thì CẬP NHẬT nhãn "
        "CURRICULUM_SUPPORT_PARTIAL trong docs, đừng để nó nói dè dặt hơn sự thật."
    )


def test_bang_curriculum_sap_theo_kieu_ho_tro_va_du_moi_unit():
    rows = curriculum_support_rows()
    assert len(rows) == len(KNOWLEDGE_UNITS)
    assert {r["unit_id"] for r in rows} == {u.unit_id for u in KNOWLEDGE_UNITS}
