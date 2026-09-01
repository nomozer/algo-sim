# -*- coding: utf-8 -*-
"""Bộ đếm biên chuẩn hoá — đếm ĐÚNG số lượt gộp, và KHÔNG đếm khi không gộp.

Nửa quan trọng của file này là các ca ÂM TÍNH: một bộ đếm chỉ tăng thì vô dụng.
Nếu `container: "stack"` (đã đúng dạng) cũng bị tính là một lượt gộp thì
`coercion_rate` luôn bằng 100% và không phân biệt được gì.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program import coercion_stats as CS
from app.simulation.semantic_program.contract import (
    SemanticProgramSpec,
    canonical_condition,
    canonical_const_int,
    canonical_container_name,
    canonical_spec_version,
)


@pytest.fixture(autouse=True)
def _sach():
    CS.reset_coercion()
    yield
    CS.reset_coercion()


# ── spec_version ───────────────────────────────────────────────────────────
def test_spec_version_so_bi_gop_thi_dem_len():
    assert canonical_spec_version(1.0) == "1.0"
    assert CS.coercion_report()[CS.LOP_SPEC_VERSION] == 1


def test_spec_version_da_dung_dang_thi_KHONG_dem():
    """Chuỗi `"1.0"` đi thẳng qua — không có gì để gộp."""
    assert canonical_spec_version("1.0") == "1.0"
    assert CS.tong_coercion() == 0


def test_spec_version_sai_phien_ban_KHONG_dem():
    """`2.0` bị từ chối ở tầng Literal, không phải một lượt gộp thành công."""
    canonical_spec_version(2.0)
    assert CS.tong_coercion() == 0


def test_spec_version_bool_KHONG_dem():
    """`True` là subclass của `int` — chặn tường minh, và không tính là gộp."""
    canonical_spec_version(True)
    assert CS.tong_coercion() == 0


# ── container ──────────────────────────────────────────────────────────────
def test_container_var_bi_gop_thi_dem_len():
    assert canonical_container_name({"kind": "var", "name": "stack"}) == "stack"
    assert CS.coercion_report()[CS.LOP_CONTAINER_REF] == 1


def test_container_ten_tran_KHONG_dem():
    assert canonical_container_name("stack") == "stack"
    assert CS.tong_coercion() == 0


def test_container_bieu_thuc_bi_tu_choi_KHONG_dem():
    """Từ chối có dạy ≠ gộp thành công."""
    with pytest.raises(ValueError):
        canonical_container_name({"kind": "index", "container": "a", "index": 0})
    assert CS.tong_coercion() == 0


# ── condition ──────────────────────────────────────────────────────────────
def test_condition_bien_bool_bi_gop_thi_dem_len():
    ra = canonical_condition({"kind": "var", "name": "hop_le"})
    assert ra["kind"] == "compare" and ra["op"] == "=="
    assert CS.coercion_report()[CS.LOP_CONDITION_BOOL] == 1


def test_condition_da_la_menh_de_KHONG_dem():
    goc = {"kind": "is_empty", "container": "stack"}
    assert canonical_condition(goc) is goc
    assert CS.tong_coercion() == 0


def test_condition_arith_KHONG_dem():
    """`2+3` làm điều kiện là lỗi KIỂU thật — không gấp, nên không đếm."""
    canonical_condition({"kind": "arith", "op": "+", "left": {}, "right": {}})
    assert CS.tong_coercion() == 0


# ── step hằng nguyên ───────────────────────────────────────────────────────
def test_step_literal_bi_gop_thi_dem_len():
    assert canonical_const_int({"kind": "literal", "value": 2}) == 2
    assert CS.coercion_report()[CS.LOP_CONST_INT] == 1


def test_step_so_tran_KHONG_dem():
    assert canonical_const_int(2) == 2
    assert CS.tong_coercion() == 0


def test_step_bieu_thuc_bi_tu_choi_KHONG_dem():
    with pytest.raises(ValueError):
        canonical_const_int({"kind": "var", "name": "buoc"})
    assert CS.tong_coercion() == 0


def test_step_literal_bool_bi_tu_choi_KHONG_dem():
    """`True` là subclass của `int` — không được lọt thành bước nhảy 1."""
    with pytest.raises(ValueError):
        canonical_const_int({"kind": "literal", "value": True})
    assert CS.tong_coercion() == 0


# ── báo cáo ────────────────────────────────────────────────────────────────
def test_bao_cao_luon_co_du_bon_lop_ke_ca_khi_bang_0():
    """Vắng mặt không phân biệt được 'chưa nổ' với 'quên gắn bộ đếm'."""
    assert set(CS.coercion_report()) == set(CS.LOP_HOP_LE)
    assert all(v == 0 for v in CS.coercion_report().values())


def test_lop_la_bi_bo_qua_khong_nem_loi():
    """Quan trắc không bao giờ được giết một lượt phân tích."""
    CS.ghi_coercion("lop_khong_ton_tai")
    assert CS.tong_coercion() == 0


def test_reset_xoa_sach():
    canonical_spec_version(1.0)
    CS.reset_coercion()
    assert CS.tong_coercion() == 0


# ── khoá chống trôi ────────────────────────────────────────────────────────
def test_bon_lop_khop_voi_so_bien_chuan_hoa_trong_contract():
    """Thêm một `canonical_*` ở `contract.py` mà quên khai lớp ở đây là ĐỎ.

    Đếm bằng cách soi chính module contract, không chép tay danh sách — chép tay
    thì lần sau người ta sửa một chỗ và test vẫn xanh.
    """
    from app.simulation.semantic_program import contract as C

    bien = [t for t in dir(C) if t.startswith("canonical_")]
    assert len(bien) == len(CS.LOP_HOP_LE), (
        f"`contract.py` có {len(bien)} biên chuẩn hoá ({sorted(bien)}) nhưng "
        f"`coercion_stats.LOP_HOP_LE` khai {len(CS.LOP_HOP_LE)} lớp. Thêm biên "
        f"thì phải thêm lớp, nếu không lượt gộp mới sẽ không ai đếm."
    )


def test_dem_qua_ca_mot_chuong_trinh_that():
    """Đường đi thật: cả BỐN lớp nổ trong MỘT lần dựng `SemanticProgramSpec`.

    Đây là ca dựng đúng chân dung lỗi mà SEALED `7e5df014…` phơi ra: một chương
    trình viết đúng nghĩa nhưng sai cách viết ở bốn chỗ khác nhau. Trước khi có
    bốn biên chuẩn hoá, chương trình này bị vứt sạch.
    """
    spec = SemanticProgramSpec.model_validate({
        "spec_version": 1.0,                                    # ← lớp 1
        "title": "Kiểm ngoặc",
        "memory_declarations": [
            {"name": "stack", "type": "stack", "element_type": "str",
             "initial_value": []},
            {"name": "hop_le", "type": "bool", "initial_value": True},
        ],
        "statements": [
            {"kind": "if",
             "condition": {"kind": "var", "name": "hop_le"},     # ← lớp 3
             "then_body": [
                 {"kind": "push",
                  "container": {"kind": "var", "name": "stack"},  # ← lớp 2
                  "val": {"kind": "literal", "value": "("}},
                 {"kind": "for_range", "loop_var": "i",
                  "start": {"kind": "literal", "value": 0},
                  "end": {"kind": "literal", "value": 3},
                  "step": {"kind": "literal", "value": 1},        # ← lớp 4
                  "body": []},
             ],
             "else_body": []},
        ],
        "visual_bindings": {},
    })
    assert spec.spec_version == "1.0"
    assert CS.coercion_report() == {
        CS.LOP_SPEC_VERSION: 1,
        CS.LOP_CONTAINER_REF: 1,
        CS.LOP_CONDITION_BOOL: 1,
        CS.LOP_CONST_INT: 1,
        # Lớp thứ NĂM (Phase 5A) — `0` là con số ĐÚNG ở đây, không phải chỗ
        # trống cần lấp: chương trình Tin học này không có `construct_solid`,
        # nên biên `faces` chưa từng chạy. So TOÀN BỘ dict thay vì so từng khoá
        # là có chủ đích — thêm một lớp mà quên nghĩ xem nó có nổ trong ca này
        # không thì test sẽ ĐỎ, và đó đúng là lúc phải dừng lại nghĩ.
        CS.LOP_FACE_SYMBOL: 0,
        # Lớp thứ SÁU (2026-09-01) — `0` cũng là con số ĐÚNG, cùng lý do: đây
        # là chương trình Tin học, không có một ô toán hạng hình học nào để
        # `canonical_geometry_name` gỡ bọc. Dòng này viết ra vì khối chú thích
        # ngay trên bảo phải dừng lại nghĩ, và nghĩ xong thì câu trả lời là 0.
        CS.LOP_GEOMETRY_REF: 0,
    }
