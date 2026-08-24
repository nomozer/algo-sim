# -*- coding: utf-8 -*-
"""IR hình học chạy được end-to-end — Bước 3. **0 API call.**

Đây là test trả lời câu *"hệ đã sinh được mô phỏng hình học chưa"* ở tầng
**biểu diễn**: một chương trình viết bằng đúng từ vựng mà LLM sẽ dùng, chạy qua
interpreter thật, ra trace thật.

KHOÁ R0 — nửa quan trọng nhất của file: chương trình **không được** chứa toạ độ
kết quả. Nó khai `A(0,0,0)` (đề cho) và nói *"lấy giao tuyến của hai mặt phẳng
này"*; toạ độ giao tuyến do kernel tính. Nếu một ngày ai đó thêm trường
`result` vào `ConstructPointStmt` "cho nhanh", `test_R0_*` dưới đây đỏ.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry import GeometryError, Line3, Plane3, Vec3
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter


def _chop_spec(statements: list[dict], them: list[dict] | None = None) -> dict:
    """Chóp `S.ABCD` đáy vuông cạnh 1, `S(0,0,2)` — cấu hình Toán 11."""
    return {
        "spec_version": "1.0",
        "title": "Thiết diện hình chóp",
        "description": "Dựng thiết diện của mặt phẳng với hình chóp S.ABCD.",
        "pedagogical_intent": "Thấy giao tuyến hình thành theo từng mặt.",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
            {"name": "B", "type": "point3", "initial_value": [1, 0, 0]},
            {"name": "C", "type": "point3", "initial_value": [1, 1, 0]},
            {"name": "D", "type": "point3", "initial_value": [0, 1, 0]},
            {"name": "S", "type": "point3", "initial_value": [0, 0, 2]},
            {"name": "chop", "type": "solid", "initial_value": {
                "vertices": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 2]],
                "faces": [[0, 3, 2, 1], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]],
            }},
            *(them or []),
        ],
        "statements": statements,
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }


def _chay(raw: dict):
    return SemanticProgramInterpreter().execute(
        SemanticProgramSpec.model_validate(raw)
    )


# ── 1. Chương trình hình học CHẠY ĐƯỢC ────────────────────────────────────
def test_dung_trung_diem_va_duong_thang():
    kq = _chay(_chop_spec([
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "A", "b": "B"}, "label": "M"},
        {"kind": "construct_line", "target_var": "d",
         "through_a": "M", "through_b": "S", "label": "d"},
    ]))
    assert kq.final_memory["M"] == Vec3.of(F(1, 2), 0, 0), "kiểm tay: trung điểm AB"
    assert isinstance(kq.final_memory["d"], Line3)


def test_dung_diem_chia_doan_theo_ti_le():
    """`AM = 2MB` ⇒ `t = 2/3` ⇒ `M(2/3, 0, 0)`. Kiểm tay."""
    kq = _chay(_chop_spec([
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": "2/3"}},
    ]))
    assert kq.final_memory["M"] == Vec3.of(F(2, 3), 0, 0)


def test_dung_hinh_chieu_S_xuong_day():
    kq = _chay(_chop_spec(
        [{"kind": "construct_point", "target_var": "H",
          "expr": {"kind": "project_onto", "point": "S", "target": "day"}}],
        them=[{"name": "day", "type": "plane3",
               "initial_value": {"through": [[0, 0, 0], [1, 0, 0], [1, 1, 0]]}}],
    ))
    assert kq.final_memory["H"] == Vec3.of(0, 0, 0), "kiểm tay: chân đường cao là A"


def test_dung_giao_tuyen_hai_mat_phang():
    kq = _chay(_chop_spec(
        [{"kind": "construct_line", "target_var": "g",
          "through_a": "A", "through_b": "B"}],
        them=[{"name": "sab", "type": "plane3",
               "initial_value": {"through": [[0, 0, 2], [0, 0, 0], [1, 0, 0]]}}],
    ))
    assert isinstance(kq.final_memory["g"], Line3)
    assert isinstance(kq.final_memory["sab"], Plane3)


# ── 2. Thiết diện → NHIỀU bước timeline ───────────────────────────────────
def test_thiet_dien_sinh_MOT_BUOC_MOI_CANH():
    """Một câu lệnh IR → nhiều khung hình. Thứ tự cạnh do kernel quyết."""
    kq = _chay(_chop_spec(
        [{"kind": "construct_section", "target_var": "td",
          "solid": "chop", "plane": "mp"}],
        them=[{"name": "mp", "type": "plane3",
               "initial_value": {"through": [[0, 0, 1], [1, 0, 1], [1, 1, 1]]}}],
    ))
    canh = [s for s in kq.trace if s.action == "section_edge"]
    assert len(canh) == 4, "cắt ngang chóp ở nửa chiều cao ⇒ tứ giác"
    assert len({s.details["mat"] for s in canh}) == 4, "mỗi cạnh một mặt khác nhau"


def test_moi_buoc_thiet_dien_co_LOI_KE_rieng():
    kq = _chay(_chop_spec(
        [{"kind": "construct_section", "target_var": "td",
          "solid": "chop", "plane": "mp"}],
        them=[{"name": "mp", "type": "plane3",
               "initial_value": {"through": [[0, 0, 1], [1, 0, 1], [1, 1, 1]]}}],
    ))
    ke = [s.tier1_narration for s in kq.trace if s.action == "section_edge"]
    assert len(set(ke)) == len(ke), "hai bước không được cùng một lời kể"
    assert all("nối" in k for k in ke)


def test_loi_ke_KHOP_voi_toa_do_trong_details():
    """Bất biến #31 ở miền hình học: lời kể suy từ ĐÚNG trạng thái bước đó."""
    kq = _chay(_chop_spec(
        [{"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "C"}, "label": "M"}],
    ))
    b = next(s for s in kq.trace if s.action == "construct_point")
    assert b.details["toa_do"] == ["1/2", "1/2", "0"]
    assert "1/2" in b.tier1_narration


# ── 3. FAIL-CLOSED xuyên tầng ─────────────────────────────────────────────
def test_giao_hai_mat_SONG_SONG_thi_chuong_trinh_HONG():
    """Lỗi kernel phải bay lên, không bị interpreter nuốt."""
    with pytest.raises(GeometryError) as e:
        _chay(_chop_spec(
            [{"kind": "construct_point", "target_var": "X",
              "expr": {"kind": "intersect_line_plane", "line": "d", "plane": "mp"}}],
            them=[
                {"name": "d", "type": "line3",
                 "initial_value": {"through": [[0, 0, 5], [1, 0, 5]]}},
                {"name": "mp", "type": "plane3",
                 "initial_value": {"through": [[0, 0, 0], [1, 0, 0], [1, 1, 0]]}},
            ],
        ))
    assert e.value.code == "PARALLEL_NO_INTERSECTION"


def test_tham_chieu_ten_KHONG_KHAI_bi_VALIDATOR_bat_tinh():
    """Bắt TĨNH là đúng tầng hơn — lỗi nêu ra trước khi tốn một bước chạy nào,
    và thông báo nói được tên nào thiếu."""
    with pytest.raises(ValueError, match="KHONG_CO"):
        _chay(_chop_spec([
            {"kind": "construct_point", "target_var": "M",
             "expr": {"kind": "midpoint", "a": "A", "b": "KHONG_CO"}},
        ]))


def test_day_dung_HAI_BUOC_duoc_chap_nhan():
    """`M = trung điểm AB` rồi `d = MS`. Đây là hình dạng của MỌI bài dựng hình
    — validator không đăng ký biến vừa dựng thì nó từ chối oan toàn bộ miền."""
    kq = _chay(_chop_spec([
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
        {"kind": "construct_point", "target_var": "N",
         "expr": {"kind": "midpoint", "a": "M", "b": "C"}},
    ]))
    assert kq.final_memory["N"] == Vec3.of(F(3, 4), F(1, 2), 0), "kiểm tay"


def test_dung_SAI_KIEU_thi_hong():
    """Chiếu một điểm lên… một điểm."""
    with pytest.raises(GeometryError) as e:
        _chay(_chop_spec([
            {"kind": "construct_point", "target_var": "H",
             "expr": {"kind": "project_onto", "point": "S", "target": "A"}},
        ]))
    assert e.value.code == "GEOMETRY_OPERAND_TYPE"


def test_khoi_khai_sai_hinh_dang_thi_hong_NGAY_LUC_KHOI_TAO():
    with pytest.raises(GeometryError) as e:
        _chay({
            "spec_version": "1.0", "title": "Khối hỏng",
            "description": "Khối khai thiếu bảng mặt.",
            "pedagogical_intent": "Chỉ dùng cho test.",
            "memory_declarations": [
                {"name": "k", "type": "solid", "initial_value": {"vertices": []}}],
            "statements": [],
            "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
        })
    assert e.value.code == "GEOMETRY_OPERAND_TYPE"


# ── 4. KHOÁ R0 — LLM không được sở hữu toạ độ kết quả ─────────────────────
def test_R0_cau_lenh_dung_KHONG_co_truong_toa_do_ket_qua():
    """Thêm `result`/`coords` vào đây là trao quyền quyết kết quả cho LLM, và
    toàn bộ luận điểm của đề tài mất hiệu lực."""
    from app.simulation.semantic_program.contract import (
        ConstructLineStmt, ConstructPointStmt, ConstructSectionStmt,
    )

    for M in (ConstructPointStmt, ConstructLineStmt, ConstructSectionStmt):
        truong = set(M.model_fields)
        cam = truong & {"result", "coords", "value", "toa_do", "answer", "output"}
        assert not cam, f"{M.__name__} có trường kết quả: {cam}"


def test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN():
    """Mọi trường của năm biểu thức hình học phải là chuỗi (tên) — nhận được
    một mảng số nghĩa là toạ độ đi thẳng từ LLM vào."""
    from app.simulation.semantic_program.contract import (
        DivideSegmentExpr, IntersectLinePlaneExpr, IntersectPlanePlaneExpr,
        MidpointExpr, ProjectOntoExpr,
    )

    for M in (IntersectLinePlaneExpr, IntersectPlanePlaneExpr, MidpointExpr,
              ProjectOntoExpr, DivideSegmentExpr):
        for ten, f in M.model_fields.items():
            if ten == "kind":
                continue
            assert f.annotation is str, \
                f"{M.__name__}.{ten} kiểu {f.annotation}, phải là str (TÊN)"


def test_R0_geometry_exec_khong_import_tang_AI():
    import inspect

    from app.simulation.semantic_program import geometry_exec

    src = inspect.getsource(geometry_exec)
    assert "app.ai" not in src and "gemini" not in src.lower()
