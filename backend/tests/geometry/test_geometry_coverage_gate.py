# -*- coding: utf-8 -*-
"""C₁b ở miền hình học — witness phải DẪN XUẤT từ dữ liệu. **0 API call.**

VÌ SAO FILE NÀY TỒN TẠI: audit trước Phase 5 đo được `_phu_thuoc` trả về `{}`
cho MỌI chương trình hình học — nó dispatch theo `kind` và không có nhánh nào
cho ba câu lệnh dựng. Hậu quả không phải "bỏ sót": nó là **từ chối oan toàn bộ
miền**, kèm thông báo nói sai bệnh (*"khai đáp án chứ không tính nó"* trong khi
chương trình tính đúng).

Ba ca dưới đây là ba ca bạn yêu cầu, và chúng phải đi **theo cặp**: nếu chỉ có
ca FAIL thì một `_phu_thuoc` hỏng (trả `{}`) vẫn xanh hết; nếu chỉ có ca PASS
thì một cổng bị tắt cũng xanh hết.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.coverage_gate import (
    _bao_dong,
    _phu_thuoc,
    check_realized_coverage,
    check_structural_coverage,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract

_DAY = {"through": [[0, 0, 0], [1, 0, 0], [1, 1, 0]]}


def _spec(mem: list[dict], stmts: list[dict]) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0",
        "title": "Hình chiếu vuông góc",
        "description": "Dựng hình chiếu vuông góc của một điểm lên mặt phẳng.",
        "pedagogical_intent": "Thấy chân đường vuông góc nằm ở đâu.",
        "memory_declarations": mem,
        "statements": stmts,
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    })


def _hop_dong(kind: str, container: str, witness: str) -> RequestContract:
    return RequestContract(
        facts=[],
        obligations=[Obligation(kind=kind, container=container,
                                params={"witness": witness})],
    )


def _c1a(kind: str, container: str, witness: str, spec: SemanticProgramSpec):
    """C₁a — kiểm TĨNH, và là chỗ hỏi *"witness có DẪN XUẤT từ dữ liệu không"*.

    ⚠️ Hai cổng, hai câu hỏi, đừng lẫn: C₁a hỏi **cấu trúc** (chương trình có
    đường tạo ra thứ đề hỏi không, và thứ ấy có phụ thuộc đầu vào không);
    C₁b (`check_realized_coverage`) chạy SAU thực thi và hỏi **lượt chạy này**
    có thật sự tạo ra witness không. Bản đầu của file này gọi nhầm C₁b cho ba
    ca dẫn xuất, và hai ca lẽ ra FAIL thì PASS — vì C₁b không hỏi câu ấy.
    """
    return check_structural_coverage(_hop_dong(kind, container, witness), spec)


def _c1b(kind: str, container: str, witness: str, spec: SemanticProgramSpec):
    """C₁b — chạy SAU thực thi, hỏi witness có được tạo ra trong lượt này không."""
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )

    kq = SemanticProgramInterpreter().execute(spec)
    return check_realized_coverage(_hop_dong(kind, container, witness), spec, kq)


# ── Ca 1: dựng hình ĐÚNG ⇒ coverage PASS ──────────────────────────────────
def test_1_chuong_trinh_dung_hinh_dung_thi_QUA():
    """`H = hình chiếu của S lên (day)` — H dẫn xuất từ cả `S` lẫn `day`."""
    s = _spec(
        [{"name": "S", "type": "point3", "initial_value": [0, 0, 2]},
         {"name": "day", "type": "plane3", "initial_value": _DAY},
         {"name": "H", "type": "point3", "initial_value": None}],
        [{"kind": "construct_point", "target_var": "H",
          "expr": {"kind": "project_onto", "point": "S", "target": "day"}}],
    )
    r = _c1a("point_on_plane", "day", "H", s)
    assert r.ok, r.missing


def test_1b_day_dung_HAI_BUOC_van_dan_xuat_qua_BAO_DONG():
    """`M = trung điểm AB` rồi `d = MS`: `d` dẫn xuất gián tiếp về `A`, `B`.
    Bao đóng phải bắc được qua nhiều bước, nếu không mọi bài dựng nhiều bước
    đều bị kết tội."""
    s = _spec(
        [{"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
         {"name": "B", "type": "point3", "initial_value": [1, 0, 0]},
         {"name": "S", "type": "point3", "initial_value": [0, 0, 2]},
         {"name": "M", "type": "point3", "initial_value": None},
         {"name": "d", "type": "line3", "initial_value": None}],
        [{"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
         {"kind": "construct_line", "target_var": "d",
          "through_a": "M", "through_b": "S"}],
    )
    assert "A" in _bao_dong(_phu_thuoc(s.statements, frozenset()), "d")


def test_1c_thiet_dien_dan_xuat_tu_KHOI_va_MAT_PHANG():
    s = _spec(
        [{"name": "chop", "type": "solid", "initial_value": {
            "vertices": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 2]],
            "faces": [[0, 3, 2, 1], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]}},
         {"name": "mp", "type": "plane3", "initial_value": {
             "through": [[0, 0, 1], [1, 0, 1], [1, 1, 1]]}},
         {"name": "td", "type": "polygon3", "initial_value": None}],
        [{"kind": "construct_section", "target_var": "td",
          "solid": "chop", "plane": "mp"}],
    )
    dep = _bao_dong(_phu_thuoc(s.statements, frozenset()), "td")
    assert {"chop", "mp"} <= dep


# ── Ca 2: khai thẳng ĐIỂM KẾT QUẢ ⇒ FAIL ──────────────────────────────────
def test_2_khai_thang_diem_ket_qua_thi_TRUOT():
    """LLM tự điền toạ độ chân đường vuông góc thay vì dựng nó.

    Đây là cách vi phạm R0 tinh vi nhất ở miền này: schema đã cấm trường
    `result` trong câu lệnh dựng, nên cửa còn lại là **khai một `point3` với
    `initial_value` là đáp án** rồi gắn nghĩa vụ lên nó.
    """
    s = _spec(
        [{"name": "S", "type": "point3", "initial_value": [0, 0, 2]},
         {"name": "day", "type": "plane3", "initial_value": _DAY},
         # ĐÁP ÁN gán thẳng — không có phép dựng nào
         {"name": "H", "type": "point3", "initial_value": [0, 0, 0]}],
        [],
    )
    r = _c1a("point_on_plane", "day", "H", s)
    assert not r.ok
    # C₁a có HAI lớp chặn nối tiếp, và ca này dừng ở lớp ĐẦU: không câu lệnh
    # nào tạo ra `H` ⇒ *"không có producer hợp lệ"*. Ca 3 mới chạm được lớp
    # thứ hai (*"không dẫn xuất"*) vì ở đó có `assign` nên `H` CÓ producer.
    assert any("producer" in m for m in r.missing), r.missing


# ── Ca 3: gán đáp án hình học vào bộ nhớ qua `assign` ⇒ FAIL ──────────────
def test_3_gan_dap_an_bang_assign_thi_TRUOT():
    """Cửa sau thứ hai: dùng `assign` với `literal` thay vì `construct_point`.
    Chương trình *trông như* có bước chạy, nhưng bước ấy không đọc gì từ đề."""
    s = _spec(
        [{"name": "S", "type": "point3", "initial_value": [0, 0, 2]},
         {"name": "day", "type": "plane3", "initial_value": _DAY},
         {"name": "H", "type": "point3", "initial_value": None}],
        [{"kind": "assign", "target_var": "H",
          "expr": {"kind": "literal", "value": [0, 0, 0]}}],
    )
    r = _c1a("point_on_plane", "day", "H", s)
    assert not r.ok
    assert any("không dẫn xuất" in m for m in r.missing), r.missing


# ── Khoá chống hồi quy: `{}` rỗng phải làm CA 1 đỏ, không chỉ ca 2/3 ──────
def test_phu_thuoc_RONG_thi_ca_dung_cung_truot__khoa_hoi_quy():
    """Bằng chứng ba ca trên đi theo CẶP có tác dụng.

    Trước bản vá, `_phu_thuoc` trả `{}` cho mọi chương trình hình học — ca 2 và
    ca 3 vẫn xanh (chúng mong FAIL), chỉ ca 1 đỏ. Test này giữ lại quan sát ấy
    để lần sau ai gỡ nhánh dựng ra khỏi `_phu_thuoc` thì thấy ngay vì sao.
    """
    s = _spec(
        [{"name": "S", "type": "point3", "initial_value": [0, 0, 2]},
         {"name": "day", "type": "plane3", "initial_value": _DAY},
         {"name": "H", "type": "point3", "initial_value": None}],
        [{"kind": "construct_point", "target_var": "H",
          "expr": {"kind": "project_onto", "point": "S", "target": "day"}}],
    )
    dep = _phu_thuoc(s.statements, frozenset())
    assert dep != {}, "nhánh câu lệnh dựng đã bị gỡ khỏi `_phu_thuoc`"
    assert _bao_dong(dep, "H") >= {"S", "day"}


def test_ratio_KHONG_bi_hieu_nham_la_ten_vung_nho():
    """`divide_segment.ratio` là một phân số, không phải tên. Bảng tra ở
    `validator` cố ý không gồm nó — nếu gồm, `'2/3'` sẽ thành một phụ thuộc ma."""
    s = _spec(
        [{"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
         {"name": "B", "type": "point3", "initial_value": [1, 0, 0]},
         {"name": "M", "type": "point3", "initial_value": None}],
        [{"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "divide_segment", "a": "A", "b": "B", "ratio": "2/3"}}],
    )
    assert _bao_dong(_phu_thuoc(s.statements, frozenset()), "M") == {"A", "B"}
