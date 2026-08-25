# -*- coding: utf-8 -*-
"""PHASE 6.6 — ổn định sinh chương trình hình học. **0 API call.**

Hai việc, và mỗi việc trả lời một trong hai nhóm vấn đề đã phân loại sau lượt
hợp nhất môi trường:

    TASK 1  hợp đồng chưa đủ biểu đạt   →  `construct_polygon`
    TASK 2  LLM sinh ký hiệu không ổn   →  resolver theo TOPOLOGY

File này cũng khoá những điều Phase 6.6 **CẤM**, vì một ràng buộc chỉ nằm trong
lời dặn thì lượt sau sẽ bị vượt qua mà không ai thấy.
"""
from __future__ import annotations

import typing

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.coverage_gate import (
    check_structural_coverage,
)
from app.simulation.semantic_program.domain_profile import (
    khop_theo_topo,
    tach_ky_hieu_diem,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.validator import validate_semantic_program

DIEM = {
    "A": [0, 0, 0], "B": [3, 0, 0], "C": [3, 3, 0], "D": [0, 3, 0],
    "S": [0, 0, 4],
}


def _spec(khai: list[dict], cau_lenh: list[dict]) -> dict:
    return {
        "title": "phase 6.6 on dinh sinh hinh hoc",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v}
            for n, v in DIEM.items()
        ] + khai,
        "statements": cau_lenh,
    }


def _chay(raw: dict):
    return SemanticProgramInterpreter().execute(
        SemanticProgramSpec.model_validate(raw))


# ══ TASK 1 — `construct_polygon` ═════════════════════════════════════════
def test_day_ABCD_nay_NOI_DUOC_nhu_mot_vat():
    """Đề *"hình chóp S.ABCD có đáy ABCD là hình vuông"* nêu một vật: **đáy**.

    Trước Phase 6.6, IR không có từ nào cho một MIỀN PHẲNG HỮU HẠN — chỉ có mặt
    phẳng vô hạn (`construct_plane`) và cả khối (`construct_solid`). Nên mô hình
    phải bịa đường, và bốn lượt smoke cho thấy nó bịa theo HAI cách khác nhau:
    `assign literal` và `initial_value` — cùng một ý định, hai triệu chứng.
    """
    raw = _spec(
        [{"name": "ABCD", "type": "polygon3"}],
        [{"kind": "construct_polygon", "target_var": "ABCD",
          "vertices": ["A", "B", "C", "D"], "label": "ABCD"}])
    assert validate_semantic_program(raw).ok
    dg = _chay(raw).final_memory["ABCD"]
    assert isinstance(dg, tuple) and len(dg) == 4


def test_dinh_TRUNG_NHAU_thi_NEM():
    """`A B C A` không phải đa giác — nó là đường gấp khúc khép sớm."""
    from app.simulation.geometry import GeometryError

    with pytest.raises(GeometryError, match="TRÙNG NHAU"):
        _chay(_spec(
            [{"name": "X", "type": "polygon3"}],
            [{"kind": "construct_polygon", "target_var": "X",
              "vertices": ["A", "B", "C", "A"]}]))


def test_KHONG_DONG_PHANG_thi_NEM():
    """Bốn điểm không đồng phẳng KHÔNG tạo thành một hình phẳng. Cho qua là dựng
    một vật không tồn tại, rồi renderer sẽ vẽ ra thứ trông hợp lý mà sai."""
    from app.simulation.geometry import GeometryError

    with pytest.raises(GeometryError, match="đồng phẳng"):
        _chay(_spec(
            [{"name": "X", "type": "polygon3"}],
            [{"kind": "construct_polygon", "target_var": "X",
              "vertices": ["A", "B", "C", "S"]}]))


def test_da_giac_len_duoc_CANH_3D_ma_KHONG_sua_renderer():
    """Bằng chứng cho *"không thêm renderer"*: `polygon3` đã có ô sẵn trong
    `RENDER_HINT` từ Phase 5C, và lớp chiếu đã biết tuple-các-đỉnh."""
    from app.simulation.semantic_program.scene3d import RENDER_HINT, build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    raw = _spec(
        [{"name": "ABCD", "type": "polygon3"}],
        [{"kind": "construct_polygon", "target_var": "ABCD",
          "vertices": ["A", "B", "C", "D"]}])
    spec = SemanticProgramSpec.model_validate(raw)
    canh = build_scene3d(build_simulation_state(spec, _chay(raw)))
    o = next(x for x in canh["objects"] if x["id"] == "ABCD")
    assert o["render"] == RENDER_HINT["polygon3"] == "polygon"


def test_R0_construct_polygon_nhan_TEN_khong_nhan_TOA_DO():
    """Thêm một trường toạ độ vào đây là trao quyền quyết kết quả cho LLM."""
    from app.simulation.semantic_program.contract import ConstructPolygonStmt

    truong = set(ConstructPolygonStmt.model_fields)
    assert truong == {"kind", "target_var", "vertices", "label"}
    assert ConstructPolygonStmt.model_fields["vertices"].annotation == list[str]


# ══ TASK 2 — resolver theo TOPOLOGY ══════════════════════════════════════
def _spec_duong(ten: str, qua: tuple[str, str]) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate(_spec(
        [{"name": ten, "type": "line3"}, {"name": "Q", "type": "point3"}],
        [{"kind": "construct_line", "target_var": ten,
          "through_a": qua[0], "through_b": qua[1]},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "midpoint", "a": "A", "b": "D"}}]))


_HD_AD = RequestContract(obligations=(
    Obligation(kind="point_on_line", container="AD", params={"witness": "Q"}),))


@pytest.mark.parametrize("ten", [
    "line_AD",       # phụ tố đầu
    "AD_line",       # phụ tố cuối
    "DA",            # ĐẢO thứ tự hai đầu mút
    "AD_segment",    # phụ tố chưa từng thấy
    "duong_thang_1", # tên KHÔNG liên quan gì tới chính tả
])
def test_moi_cach_dat_ten_deu_khop_vi_TOPOLOGY_giong_nhau(ten):
    """Resolver hỏi *"vật nào ĐƯỢC DỰNG TỪ đúng những điểm này"*, nên tên gọi
    thành KHÔNG LIÊN QUAN.

    Đây là điều một danh sách bí danh không làm được: `duong_thang_1` không chia
    một ký tự nào với `AD`, mà vẫn khớp — vì nó được dựng từ `{A, D}`.
    """
    kq = check_structural_coverage(_HD_AD, _spec_duong(ten, ("A", "D")))
    assert kq.ok, kq.missing
    assert "topology" in kq.symbol_reconciled[0]


def test_KHONG_che_loi_semantic_THAT():
    """Điều kiện Phase 6.6 nêu thẳng. Chương trình dựng đường qua `A` và `S`
    trong khi đề hỏi về `AD` là SAI THẬT, và resolver phải để nó trượt."""
    kq = check_structural_coverage(_HD_AD, _spec_duong("line_AS", ("A", "S")))
    assert not kq.ok


def test_MO_HO_thi_fail_closed():
    """Hai đường cùng qua `A` và `D` ⇒ không ai biết hợp đồng nói cái nào."""
    spec = SemanticProgramSpec.model_validate(_spec(
        [{"name": "l1", "type": "line3"}, {"name": "l2", "type": "line3"},
         {"name": "Q", "type": "point3"}],
        [{"kind": "construct_line", "target_var": "l1",
          "through_a": "A", "through_b": "D"},
         {"kind": "construct_line", "target_var": "l2",
          "through_a": "D", "through_b": "A"},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "midpoint", "a": "A", "b": "D"}}]))
    assert not check_structural_coverage(_HD_AD, spec).ok


def test_KIEU_cung_loc_ung_vien():
    """`point_on_line` đòi một `line3`. Một mặt phẳng dựng từ cùng tập điểm
    KHÔNG được nhận — resolver dùng chính `accepts_container_type`, không tự
    chế bảng kiểu thứ hai."""
    assert khop_theo_topo(
        "ABC", {"A", "B", "C"},
        {"mp": ("plane3", frozenset({"A", "B", "C"}))},
        lambda k: k == "line3") is None


def test_tach_ky_hieu_doi_MOI_KY_HIEU_la_DIEM_DA_KHAI():
    """Điều kiện chặt nhất của cả resolver. Không có nó thì `MAX` đọc thành ba
    điểm và hàm biến thành một máy đoán."""
    assert tach_ky_hieu_diem("AD", {"A", "D"}) == ("A", "D")
    assert tach_ky_hieu_diem("(ABCD)", {"A", "B", "C", "D"}) == ("A", "B", "C", "D")
    assert tach_ky_hieu_diem("S.ABCD", {"S", "A", "B", "C", "D"})[0] == "S"
    assert tach_ky_hieu_diem("MAX", {"A", "B"}) is None      # X, M chưa khai
    assert tach_ky_hieu_diem("A", {"A"}) is None             # một điểm lẻ


def test_vat_khai_bang_INITIAL_VALUE_khong_co_topology():
    """Không dựng thì không có tập điểm để so — và resolver phải nói "không",
    chứ không được đoán từ tên."""
    assert khop_theo_topo("AD", {"A", "D"},
                          {"line_AD": ("line3", frozenset())},
                          lambda k: True) is None


# ══ ĐIỀU PHASE 6.6 CẤM — khoá lại, không để nằm trong lời dặn ════════════
def test_KHONG_them_target_moi():
    from app.simulation.catalog import CATALOG

    assert len(CATALOG) == 24, "Phase 6.6 cấm thêm target"


def test_DANH_SACH_PHU_TO_KHONG_DUOC_DAI_THEM():
    """*"Không thêm alias thủ công theo từng lỗi LLM."*

    `_PHU_TO_KIEU` là lưới CUỐI và là lưới duy nhất dựa vào chính tả. Sau khi có
    resolver topology, nó chỉ còn phục vụ vật khai bằng `initial_value`. Dài
    thêm sau mỗi lượt đỏ là đúng thứ Phase 6.6 cấm — nên độ dài bị ghim.
    """
    from app.simulation.semantic_program.domain_profile import _PHU_TO_KIEU

    assert len(_PHU_TO_KIEU) <= 14, (
        "thêm phụ tố là vá theo một lỗi LLM cụ thể — hãy hỏi vì sao resolver "
        "topology không xử được ca ấy trước đã"
    )


def test_KHONG_them_primitive_nao_KHAC_ngoai_construct_polygon():
    """Phase 6.6 mở ĐÚNG MỘT câu lệnh. Sáu phép dựng, không hơn."""
    from app.simulation.semantic_program.contract import SemanticStatement

    tags = {typing.get_args(a)[1].tag
            for a in typing.get_args(typing.get_args(SemanticStatement)[0])
            if "construct" in str(a)}
    assert tags == {"construct_point", "construct_line", "construct_plane",
                    "construct_polygon", "construct_solid", "construct_section"}


def test_KHONG_sua_KERNEL_hinh_hoc():
    """`construct_polygon` chỉ GỌI thứ kernel đã có (`same_point`, `coplanar`),
    không thêm một phép tính nào vào kernel."""
    from app.simulation.geometry import predicates as P

    assert hasattr(P, "coplanar") and hasattr(P, "same_point")
    from app.simulation.semantic_program import geometry_exec as G

    src = typing.cast(str, G.exec_construct_polygon.__doc__ or "")
    assert "không sửa kernel" in src
