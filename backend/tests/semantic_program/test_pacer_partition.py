# -*- coding: utf-8 -*-
"""Bất biến #32 — pacer GỘP, không BỎ.

Gộp nằm ngoài VisualTraceAdapter để adapter giữ song ánh frame k ⇔ trace[k];
có song ánh đó thì bất biến #31 mới là định lý (spec §4.4).

Ngân sách trình bày tách hẳn ngân sách thực thi: chạm trần trình bày KHÔNG
phải lỗi — hạ mức chi tiết, không bao giờ cắt (spec §4.3).
"""
from app.simulation.semantic_program.pacer import pace
from app.simulation.semantic_program.visual_adapter import VisualFrame


def _frames(n: int) -> list[VisualFrame]:
    return [
        VisualFrame(
            step_index=i, narration=f"buoc {i}", tier1_fact=f"buoc {i}", objects=[]
        )
        for i in range(n)
    ]


def test_phan_hoach_day_du_khong_chong_lan():
    steps = pace(_frames(50), budget=10).view_steps
    assert steps[0].frame_lo == 0
    assert steps[-1].frame_hi == 49
    for a, b in zip(steps, steps[1:]):
        assert b.frame_lo == a.frame_hi + 1, "Có khung bị bỏ hoặc chồng lấn"


def test_khong_sinh_khung_moi():
    res = pace(_frames(50), budget=10)
    total = sum(s.frame_hi - s.frame_lo + 1 for s in res.view_steps)
    assert total == 50


def test_vua_ngan_sach_thi_khong_gop():
    res = pace(_frames(8), budget=10)
    assert res.grouping_level == "step"
    assert len(res.view_steps) == 8


def test_qua_ngan_sach_thi_gop_va_khai_bao():
    res = pace(_frames(500), budget=10)
    assert res.grouping_level == "iteration"
    assert len(res.view_steps) <= 10
    assert res.overflow is False


def test_khong_bao_gio_cat_bo_khung():
    """Trần trình bày KHÔNG phải lỗi và KHÔNG được cắt (luật cứng #12)."""
    res = pace(_frames(5000), budget=10)
    total = sum(s.frame_hi - s.frame_lo + 1 for s in res.view_steps)
    assert total == 5000, "Pacer đã CẮT khung — vi phạm luật cấm cắt câm"


def test_timeline_rong_khong_no():
    res = pace([], budget=10)
    assert res.view_steps == []
    assert res.overflow is False
