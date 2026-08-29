# -*- coding: utf-8 -*-
"""THẨM ĐỊNH TĨNH — mỗi họ lỗi một cặp SAI/ĐÚNG. 0 API call.

Fixtures viết ĐỘC LẬP, **không chép ca V3**: V3 đã đóng thành bằng chứng, và
lấy đề của nó làm ca hồi quy là biến tập xác nhận thành tập DEV.

Luật của mỗi cặp, và nó là điểm của cả file:

  · bản SAI phải chết **TRƯỚC kernel** — validator HOẶC `kiem_tinh` bắt được;
  · bản ĐÚNG tương ứng phải đi trọn tới execution — nếu không, cổng mới đang
    chặn cả chương trình hợp lệ, tức nó không phải một cổng mà là một bức tường.

─── RANH GIỚI VỚI VALIDATOR, đo được chứ không đoán ──────────────────────

`validate_semantic_program` **đã** hỏi câu *"tên này có tồn tại không"* cho cả
toán hạng câu lệnh dựng lẫn toán hạng biểu thức hình học. Viết lại nó ở
`ir_static_check` là dựng nguồn sự thật thứ hai. Bốn thứ nó KHÔNG hỏi — và cả
bốn đều là một cái chết ở kernel trong V3:

    khai báo rỗng (`None` xuống kernel) · sai KIỂU toán hạng ·
    `ratio` không phải phân số · `measure` sai loại đối tượng

`test_ranh_gioi_voi_validator` khoá đúng ranh giới ấy: mất nó thì lần sau ai
đó lại chép phép kiểm tồn tại vào tầng này.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.ir_static_check import (
    ERR_DUNG_TRUOC_KHI_DUNG,
    ERR_KHONG_HUU_TI,
    ERR_SAI_KIEU,
    kiem_tinh,
)
from app.simulation.semantic_program.validator import validate_semantic_program


def _payload(decls: list[dict], stmts: list[dict]) -> dict:
    return {
        "simulation_id": "geometry.demo", "title": "Demo dựng hình",
        "description": "Chương trình mẫu cho thẩm định tĩnh",
        "pedagogical_intent": "Cho thấy cơ chế ẩn",
        "memory_declarations": decls, "statements": stmts, "obligations": [],
    }


def chan_truoc_kernel(decls, stmts) -> tuple[str, str]:
    """`(tầng bắt được, lời từ chối)`. `("qua", "")` ⇒ đi tới được kernel."""
    val = validate_semantic_program(_payload(decls, stmts))
    if not val.ok:
        return "validator", val.error
    kq = kiem_tinh(val.spec)
    if not kq.ok:
        return "ir_static", kq.phan_hoi()
    return "qua", ""


def _spec(decls, stmts):
    val = validate_semantic_program(_payload(decls, stmts))
    assert val.ok, val.error
    return val.spec


def _diem(ten: str, xyz) -> dict:
    return {"name": ten, "type": "point3", "initial_value": list(xyz),
            "model_assumption": f"chọn {ten}"}


_BON_DIEM = [_diem("A", (0, 0, 0)), _diem("B", (1, 0, 0)),
             _diem("C", (1, 1, 0)), _diem("S", (0, 0, 1))]


# ══ HỌ 1 · TÊN KHÔNG TỒN TẠI — validator đã sở hữu ════════════════════════
@pytest.mark.parametrize("stmts", [
    [{"kind": "construct_line", "target_var": "d",
      "through_a": "A", "through_b": "P"}],
    [{"kind": "construct_point", "target_var": "M",
      "expr": {"kind": "midpoint", "a": "Z", "b": "B"}}],
])
def test_SAI_ten_khong_ton_tai_chet_o_validator(stmts):
    tang, _ = chan_truoc_kernel(_BON_DIEM, stmts)
    assert tang == "validator"


# ══ HỌ 2 · KHAI BÁO RỖNG ⇒ `None` xuống kernel ════════════════════════════
def test_SAI_khai_bao_khong_co_gia_tri():
    """Đây đúng là `GEOMETRY_OPERAND_TYPE: điểm 'P' là NoneType` của V3.

    Validator cho qua vì `P` CÓ trong `memory_declarations` — câu hỏi tồn tại
    trả lời đúng. Câu hỏi *"nó có giá trị chưa"* thì chưa ai hỏi.
    """
    decls = _BON_DIEM + [{"name": "P", "type": "point3"}]
    stmts = [{"kind": "construct_line", "target_var": "d",
              "through_a": "A", "through_b": "P"}]
    tang, loi = chan_truoc_kernel(decls, stmts)
    assert tang == "ir_static"
    assert ERR_DUNG_TRUOC_KHI_DUNG in loi and "chưa có giá trị" in loi


def test_DUNG_khai_bao_rong_nhung_da_duoc_dung_truoc():
    decls = _BON_DIEM + [{"name": "P", "type": "point3"}]
    stmts = [
        {"kind": "construct_point", "target_var": "P",
         "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
        {"kind": "construct_line", "target_var": "d",
         "through_a": "A", "through_b": "P"},
    ]
    assert chan_truoc_kernel(decls, stmts) == ("qua", "")


# ══ HỌ 3 · SAI KIỂU TOÁN HẠNG ═════════════════════════════════════════════
def test_SAI_duong_dung_lam_diem():
    tang, loi = chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_line", "target_var": "d",
         "through_a": "A", "through_b": "B"},
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "d", "b": "C"}},
    ])
    assert tang == "ir_static" and ERR_SAI_KIEU in loi
    assert "line3" in loi and "point3" in loi


def test_SAI_mat_phang_dung_lam_duong():
    tang, loi = chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_plane", "target_var": "ABC",
         "through": ["A", "B", "C"]},
        {"kind": "construct_point", "target_var": "I",
         "expr": {"kind": "intersect_line_plane",
                  "line": "ABC", "plane": "ABC"}},
    ])
    assert tang == "ir_static" and ERR_SAI_KIEU in loi


def test_SAI_diem_dung_lam_mat_phang():
    tang, loi = chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_line", "target_var": "SA",
         "through_a": "S", "through_b": "A"},
        {"kind": "construct_point", "target_var": "I",
         "expr": {"kind": "intersect_line_plane", "line": "SA", "plane": "C"}},
    ])
    assert tang == "ir_static" and ERR_SAI_KIEU in loi


def test_DUNG_giao_duong_voi_mat():
    assert chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_plane", "target_var": "ABC",
         "through": ["A", "B", "C"]},
        {"kind": "construct_line", "target_var": "SA",
         "through_a": "S", "through_b": "A"},
        {"kind": "construct_point", "target_var": "I",
         "expr": {"kind": "intersect_line_plane",
                  "line": "SA", "plane": "ABC"}},
    ]) == ("qua", "")


def test_SAI_do_the_tich_tren_mot_DIEM():
    tang, loi = chan_truoc_kernel(_BON_DIEM, [
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "A"}},
    ])
    assert tang == "ir_static" and ERR_SAI_KIEU in loi


def test_DUNG_do_the_tich_tren_KHOI():
    assert chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_solid", "target_var": "chop",
         "vertices": ["A", "B", "C", "S"],
         "faces": [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]]},
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
    ]) == ("qua", "")


# ══ HỌ 4 · SỐ HỮU TỈ CHÍNH XÁC ════════════════════════════════════════════
@pytest.mark.parametrize("xau", ["2:1", "a", "2a/3", "", "1,5"])
def test_SAI_ti_le_khong_phai_phan_so(xau: str):
    tang, loi = chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": xau}},
    ])
    assert tang == "ir_static" and ERR_KHONG_HUU_TI in loi, f"{xau!r} phải bị bác"


@pytest.mark.parametrize("xau", ["2/1", "1/2", "2", "-3", "0", "4/5", "1.2"])
def test_DUNG_ti_le_huu_ti(xau: str):
    """`"1.2"` NHẬN, và có lý do: `Fraction("1.2")` là `6/5` — CHÍNH XÁC.

    Thứ bị cấm là `float` của JSON, nơi độ chính xác mất ngay lúc parse. Một
    chuỗi thập phân thì không mất gì cả. Bác nó là chặt hơn cả kernel, tức từ
    chối một chương trình chạy đúng.
    """
    assert chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": xau}},
    ]) == ("qua", ""), f"{xau!r} là phân số hợp lệ"


def test_KHONG_tu_dien_giai_lai_2_cham_1():
    """`2:1` KHÔNG được lặng lẽ hiểu thành `2/1`.

    `AM = 2MB` cho `t = 2/3`, còn đọc `2:1` theo lối khác cho `t = 2`. Đoán một
    trong hai là dựng sai hình mà mọi cổng vẫn xanh.
    """
    _, loi = chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": "2:1"}},
    ])
    assert "2:1" in loi


# ══ HỌ 5 · DỰNG NHIỀU BƯỚC HỢP LỆ — KHÔNG ĐƯỢC CHẶN OAN ═══════════════════
def test_DUNG_chuoi_dung_nhieu_buoc():
    assert chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
        {"kind": "construct_point", "target_var": "N",
         "expr": {"kind": "midpoint", "a": "B", "b": "C"}},
        {"kind": "construct_plane", "target_var": "SMN",
         "through": ["S", "M", "N"]},
        {"kind": "construct_line", "target_var": "AC",
         "through_a": "A", "through_b": "C"},
        {"kind": "construct_point", "target_var": "I",
         "expr": {"kind": "intersect_line_plane", "line": "AC", "plane": "SMN"}},
    ]) == ("qua", "")


def test_DUNG_chia_doan_roi_dung_tiep():
    assert chan_truoc_kernel(_BON_DIEM, [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": "2/3"}},
        {"kind": "construct_line", "target_var": "SM",
         "through_a": "S", "through_b": "M"},
        {"kind": "construct_plane", "target_var": "ABC",
         "through": ["A", "B", "C"]},
        {"kind": "construct_point", "target_var": "H",
         "expr": {"kind": "project_onto", "point": "S", "target": "ABC"}},
    ]) == ("qua", "")


# ══ RANH GIỚI với validator — khoá để không ai chép phép kiểm sang tầng này ══
def test_ranh_gioi_voi_validator():
    """Bốn thứ `kiem_tinh` sở hữu, và ĐÚNG bốn thứ ấy validator để lọt."""
    lot = [
        (_BON_DIEM + [{"name": "P", "type": "point3"}],
         [{"kind": "construct_line", "target_var": "d",
           "through_a": "A", "through_b": "P"}]),
        (_BON_DIEM,
         [{"kind": "construct_line", "target_var": "d",
           "through_a": "A", "through_b": "B"},
          {"kind": "construct_point", "target_var": "M",
           "expr": {"kind": "midpoint", "a": "d", "b": "C"}}]),
        (_BON_DIEM,
         [{"kind": "construct_point", "target_var": "M",
           "expr": {"kind": "divide_segment", "a": "A", "b": "B",
                    "ratio": "2:1"}}]),
        (_BON_DIEM,
         [{"kind": "assign", "target_var": "V",
           "expr": {"kind": "measure", "quantity": "volume", "of": "A"}}]),
    ]
    for decls, stmts in lot:
        assert validate_semantic_program(_payload(decls, stmts)).ok, \
            "validator KHÔNG hỏi câu này — nếu nó bắt được thì tầng tĩnh thừa"
        assert not kiem_tinh(_spec(decls, stmts)).ok


# ══ GIỚI HẠN ĐÃ BIẾT — khoá để lời khai không tự mục đi ═══════════════════
def test_GIOI_HAN_nhanh_khong_chay_van_lot():
    """`None` VẪN tới được kernel qua một nhánh không chạy. Đây là SỰ THẬT.

    Test này không bảo vệ một tính năng — nó bảo vệ một **lời khai trung
    thực**. Nếu ngày nào đó phân tích theo nhánh được làm, test này ĐỎ, và
    người sửa phải xoá nó cùng đoạn "GIỚI HẠN CÒN LẠI" trong docstring module.
    Bỏ test đi thì báo cáo sẽ dần nói *"None không bao giờ tới kernel"* — một
    câu mạnh hơn thứ hệ thật sự bảo đảm.
    """
    decls = _BON_DIEM + [{"name": "P", "type": "point3"},
                         {"name": "c", "type": "bool", "initial_value": False}]
    stmts = [
        {"kind": "if", "condition": {"kind": "var", "name": "c"},
         "then_body": [{"kind": "construct_point", "target_var": "P",
                        "expr": {"kind": "midpoint", "a": "A", "b": "B"}}]},
        {"kind": "construct_line", "target_var": "d",
         "through_a": "A", "through_b": "P"},
    ]
    assert chan_truoc_kernel(decls, stmts) == ("qua", ""), (
        "nếu điều này đã bị chặn thì GIỚI HẠN đã đóng — cập nhật docstring "
        "module và xoá test này")


# ══ PHẢN HỒI phải MÁY ĐỌC ĐƯỢC (§5) ═══════════════════════════════════════
def test_phan_hoi_ngan_va_co_dia_chi():
    kq = kiem_tinh(_spec(
        _BON_DIEM + [{"name": "P", "type": "point3"}],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "P"}]))
    s = kq.phan_hoi()
    assert s.startswith("#1 ") and ERR_DUNG_TRUOC_KHI_DUNG in s and "'P'" in s
    assert len(s) < 200, "phản hồi phải NGẮN — prompt chính không được phình"
    i = kq.issues[0]
    assert (i.error_code and i.instruction == 1 and i.object_id == "P"
            and i.expected and i.actual), "đủ 5 trường máy đọc được"
