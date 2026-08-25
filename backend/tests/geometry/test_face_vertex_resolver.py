# -*- coding: utf-8 -*-
"""PHASE 5A — `construct_solid.faces` nhận TÊN ĐỈNH. **0 API call.**

ĐO ĐƯỢC Ở LƯỢT W4 (`8b4025e`): **3/4 ca trượt schema đều là lỗi này**, cùng một
trường:

    statements.N.construct_solid.faces.0.0
      Input should be a valid integer … input_value='S'

`faces: list[list[int]]` dùng chỉ số vị trí vào `vertices` — mã hoá thân thiện
với máy, **thù địch với người**. Và Wave 4 vừa dặn mô hình *"giữ nguyên ký hiệu
điểm"*, nên nó dùng ký hiệu ở mọi chỗ, kể cả đây.

Ở Wave 3 tôi từ chối vá một lỗi hình-dạng-wire tương tự vì *"một lần là giai
thoại"*. Nay là **ba lần, cùng một trường** — ngưỡng đã vượt, và file này khoá
lại cả bản vá lẫn **ranh giới** của nó.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.simulation.semantic_program import coercion_stats as CS
from app.simulation.semantic_program.contract import (
    ConstructSolidStmt,
    SemanticProgramSpec,
)

_DINH = ["A", "B", "C", "D", "S"]
_MAT_CHI_SO = [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
_MAT_TEN = [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"],
            ["C", "D", "S"], ["D", "A", "S"]]


def _khoi(faces, vertices=None) -> ConstructSolidStmt:
    return ConstructSolidStmt(
        target_var="chop", vertices=vertices or _DINH, faces=faces,
        label="S.ABCD",
    )


# ══ PASS — hai hình dạng, MỘT kết quả ════════════════════════════════════
def test_PASS_faces_bang_TEN_dinh():
    assert _khoi(_MAT_TEN).faces == _MAT_CHI_SO


def test_PASS_faces_bang_CHI_SO():
    """Hình dạng cũ KHÔNG hồi quy — mọi chương trình đã viết vẫn chạy."""
    assert _khoi(_MAT_CHI_SO).faces == _MAT_CHI_SO


def test_hai_hinh_dang_cho_CUNG_MOT_khoi():
    assert _khoi(_MAT_TEN).faces == _khoi(_MAT_CHI_SO).faces


def test_TRON_ten_va_chi_so_trong_cung_mot_khoi():
    """Không có gì mơ hồ khi trộn: `int` là chỉ số, `str` là tên. Từ chối trộn
    sẽ là một luật thêm mà không bảo vệ gì."""
    tron = [["A", "B", 2, 3], [0, 1, "S"], ["B", "C", "S"], [2, 3, 4],
            ["D", "A", "S"]]
    assert _khoi(tron).faces == _MAT_CHI_SO


# ══ FAIL — bốn lớp, và mỗi lớp có lý do riêng ════════════════════════════
def test_FAIL_dinh_KHONG_TON_TAI():
    with pytest.raises(ValidationError) as e:
        _khoi([["A", "B", "Z"], ["A", "B", "S"], ["B", "C", "S"],
               ["C", "D", "S"]])
    txt = str(e.value)
    assert "'Z'" in txt
    # Thông điệp phải LIỆT KÊ tên hợp lệ — vòng sửa ≤3 lượt chỉ có ích nếu lỗi
    # nói được phải sửa thành gì.
    assert "đã khai" in txt and "'A'" in txt


def test_FAIL_dinh_LAP_LAI_trong_cung_mot_mat():
    """`["A","B","A"]` là mặt suy biến — không dựng được thành đa giác. Bắt ở
    biên thay vì để kernel vỡ muộn, vì ở đây còn biết TÊN để nói cho người đọc."""
    with pytest.raises(ValidationError, match="lặp lại cùng một đỉnh"):
        _khoi([["A", "B", "A"], ["A", "B", "S"], ["B", "C", "S"],
               ["C", "D", "S"]])


def test_FAIL_lap_lai_ke_ca_khi_khai_bang_CHI_SO():
    with pytest.raises(ValidationError, match="lặp lại"):
        _khoi([[0, 1, 0], [0, 1, 4], [1, 2, 4], [2, 3, 4]])


@pytest.mark.parametrize("xau", [
    [[0, 0, 0], [0, 1, 4], [1, 2, 4], [2, 3, 4]],          # toạ độ lồng
    [[[0, 0, 0], [1, 0, 0]], [0, 1, 4], [1, 2, 4], [2, 3, 4]],
    [[1.5, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4]],        # số thực
    [[True, 1, 2], [0, 1, 4], [1, 2, 4], [2, 3, 4]],       # bool
])
def test_FAIL_TIEM_TOA_DO_hoac_hinh_dang_la(xau):
    """R0 ở biên này: `faces` là **cấu trúc tổ hợp**, không phải dữ liệu hình
    học. Một toạ độ lọt vào đây là LLM tiêm số thẳng vào khối, bỏ qua cả
    `vertices`. `bool` tách riêng vì trong Python nó *là* `int`, và `True` sẽ
    lặng lẽ thành chỉ số 1."""
    with pytest.raises(ValidationError):
        _khoi(xau)


def test_FAIL_toa_do_LONG_khong_bi_nham_thanh_mat():
    """`[[0,0,0],[1,0,0],[0,1,0]]` — ba toạ độ trông y như một mặt ba đỉnh."""
    with pytest.raises(ValidationError) as e:
        _khoi([[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [0, 1, 4], [1, 2, 4],
               [2, 3, 4]])
    assert "TÊN ĐỈNH hoặc chỉ số" in str(e.value)


def test_KHONG_doan_chuoi_so_thanh_chi_so():
    """`"0"` KHÔNG được hiểu thành chỉ số 0.

    Cám dỗ hợp lý (mô hình có thể khai `["0","1","2"]`), nhưng bằng chứng hiện
    có là `["S","A","B"]`. Vá theo thứ CHƯA quan sát được là mở rộng hợp đồng
    bằng suy đoán — đúng chế độ hỏng `RULES §3c` gọi tên. Ghi lại ở đây để lần
    sau ai gặp `["0","1","2"]` thì có bằng chứng mà mở, không mở vì đoán.
    """
    with pytest.raises(ValidationError, match="'0'"):
        _khoi([["0", "1", "2"], [0, 1, 4], [1, 2, 4], [2, 3, 4]])


# ══ ĐẾM COERCION — biết mô hình lệch bao nhiêu ═══════════════════════════
def test_coercion_duoc_DEM_khi_dung_ten():
    CS.reset_coercion()
    _khoi(_MAT_TEN)
    assert CS.coercion_report()[CS.LOP_FACE_SYMBOL] == 1


def test_coercion_KHONG_dem_khi_dung_chi_so():
    """Đếm chỉ có nghĩa nếu nó im lặng khi không có lệch nào."""
    CS.reset_coercion()
    _khoi(_MAT_CHI_SO)
    assert CS.coercion_report()[CS.LOP_FACE_SYMBOL] == 0


def test_lop_moi_nam_trong_LOP_HOP_LE():
    assert CS.LOP_FACE_SYMBOL in CS.LOP_HOP_LE


# ══ KHÔNG ĐỘNG TỚI PHẦN CÒN LẠI ═════════════════════════════════════════
def test_vertices_KHONG_bi_cham():
    """Đồ thị phụ thuộc đọc `st.vertices` (danh sách TÊN). Biên này chỉ đổi
    `faces`; chạm `vertices` là làm hỏng `_phu_thuoc` một cách câm."""
    s = _khoi(_MAT_TEN)
    assert s.vertices == _DINH


def test_phu_thuoc_GIU_NGUYEN_voi_ca_hai_hinh_dang():
    from app.simulation.semantic_program.coverage_gate import (
        _phu_thuoc,
        _producers,
    )

    for mat in (_MAT_TEN, _MAT_CHI_SO):
        st = [_khoi(mat)]
        assert _producers(st) == {"chop"}
        assert _phu_thuoc(st, frozenset())["chop"] == set(_DINH)


def test_kernel_VAN_nhan_dung_chi_so():
    """Kernel không đổi: `exec_construct_solid` vẫn kiểm chỉ số ngoài biên, và
    biên chuẩn hoá KHÔNG được nuốt mất phép kiểm ấy."""
    from app.simulation.geometry import GeometryError, Vec3
    from app.simulation.semantic_program.geometry_exec import exec_construct_solid

    mem = {n: Vec3.of(i, 0, 0) for i, n in enumerate(_DINH)}
    kh, ke = exec_construct_solid(_khoi(_MAT_TEN), mem)
    assert len(kh.vertices) == 5 and len(kh.faces) == 5

    class N:
        target_var, label = "k", None
        vertices = _DINH
        faces = [[0, 1, 2, 3], [0, 1, 9], [1, 2, 4], [2, 3, 4], [3, 0, 4]]

    with pytest.raises(GeometryError, match="ngoài khoảng"):
        exec_construct_solid(N(), mem)


def test_di_tron_duong_voi_faces_bang_TEN():
    """Bằng chứng cuối: một chương trình `geo_09` khai `faces` bằng tên đi được
    tới oracle — không chỉ qua schema."""
    from fractions import Fraction

    from app.simulation.semantic_program.route import verify_and_compile
    from test_geometry_wave2 import _chuong_trinh_geo_09, _hop_dong_geo_09

    ct = _chuong_trinh_geo_09()
    for s in ct["statements"]:
        if s["kind"] == "construct_solid":
            s["faces"] = _MAT_TEN
            s["vertices"] = _DINH
    kq = verify_and_compile(
        _hop_dong_geo_09(), SemanticProgramSpec.model_validate(ct)
    )
    assert kq.executable, f"{kq.stage_reached}: {kq.details}"
    assert kq.final_memory["V"] == Fraction(2, 3)
