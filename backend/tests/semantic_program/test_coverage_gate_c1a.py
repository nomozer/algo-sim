# -*- coding: utf-8 -*-
"""C₁a — structural coverage, TRƯỚC execution (spec §5.3).

Trả lời: *mỗi nghĩa vụ có witness hợp lệ VỀ CẤU TRÚC không?*
KHÔNG trả lời: *chạy xong có thoả không?* — đó là C₂, và *witness có thật sự
được hiện thực hoá không?* — đó là C₁b.
"""
import pytest

from app.simulation.semantic_program.contract import (
    AssignStmt,
    CompareCond,
    IfStmt,
    IndexRefExpr,
    LiteralExpr,
    MemoryDeclaration,
    SemanticProgramSpec,
    VarRefExpr,
)
from app.simulation.semantic_program.coverage_gate import check_structural_coverage
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract


def _spec_tim_max() -> SemanticProgramSpec:
    """Chương trình khai `max_val` và có câu gán cho nó."""
    return SemanticProgramSpec(
        title="Tìm giá trị lớn nhất",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[3, 9, 2]),
            MemoryDeclaration(name="max_val", type="int", initial_value=0),
        ],
        statements=[
            AssignStmt(
                target_var="max_val",
                expr=IndexRefExpr(container="a", index=LiteralExpr(value=0)),
            )
        ],
    )


def _ob(kind="extremum", container="a", **params) -> Obligation:
    return Obligation(kind=kind, container=container, params=params)


def test_du_nghia_vu_thi_pass():
    contract = RequestContract(
        obligations=(_ob(cmp="max", witness="max_val"),)
    )
    res = check_structural_coverage(contract, _spec_tim_max())
    assert res.ok, res.missing


def test_de_hoi_hai_viec_ma_chuong_trinh_lam_mot_thi_tu_choi():
    """Đúng chỗ 'đề hỏi cả max lẫn min mà chỉ làm max' bị chặn."""
    contract = RequestContract(
        obligations=(
            _ob(cmp="max", witness="max_val"),
            _ob(cmp="min", witness="min_val"),
        )
    )
    res = check_structural_coverage(contract, _spec_tim_max())
    assert not res.ok
    assert res.error_code == "REQUESTED_OPERATION_UNCOVERED"
    assert any("min_val" in m for m in res.missing)


def test_witness_chua_khai_bao_thi_tu_choi():
    contract = RequestContract(obligations=(_ob(cmp="max", witness="khong_khai"),))
    res = check_structural_coverage(contract, _spec_tim_max())
    assert not res.ok
    assert res.error_code == "REQUESTED_OPERATION_UNCOVERED"


def test_witness_khai_bao_nhung_khong_co_producer_thi_tu_choi():
    """Khai biến rồi bỏ đó — không câu lệnh nào tạo ra nó."""
    spec = _spec_tim_max()
    spec.memory_declarations.append(
        MemoryDeclaration(name="mo_coi", type="int", initial_value=None)
    )
    contract = RequestContract(obligations=(_ob(cmp="max", witness="mo_coi"),))
    res = check_structural_coverage(contract, spec)
    assert not res.ok
    assert any("producer" in m for m in res.missing)


def test_thieu_witness_thi_tu_choi():
    contract = RequestContract(obligations=(_ob(cmp="max"),))
    res = check_structural_coverage(contract, _spec_tim_max())
    assert not res.ok
    assert any("witness" in m for m in res.missing)


def test_kieu_container_khong_hop_voi_nghia_vu_thi_tu_choi():
    """`ordering` chỉ áp cho array — gọi nó trên int là sai từ vựng."""
    contract = RequestContract(
        obligations=(_ob(kind="ordering", container="max_val", cmp="asc",
                         witness="max_val"),)
    )
    res = check_structural_coverage(contract, _spec_tim_max())
    assert not res.ok
    assert any("không hợp" in m for m in res.missing)


def _spec_co_cay() -> SemanticProgramSpec:
    """Spec mang một `tree_node` — cần cho nghĩa vụ mức yếu duy nhất còn lại.

    `structural_traversal` chỉ nhận `tree_node`; gắn nó lên mảng thì C₁a rơi vào
    nhánh "kiểu không hợp" và test không còn kiểm được điều nó định kiểm.
    """
    return SemanticProgramSpec(
        title="Duyệt cây",
        memory_declarations=[
            MemoryDeclaration(name="a", type="tree_node",
                              initial_value={"val": "A", "left": None, "right": None}),
            MemoryDeclaration(name="max_val", type="int", initial_value=0),
        ],
        statements=[AssignStmt(target_var="max_val", expr=LiteralExpr(value=1))],
    )


def test_nghia_vu_khong_co_checker_thi_bao_muc_yeu_khong_phai_thieu():
    """Mức YẾU ≠ thiếu nghĩa vụ. Phải phân biệt để §5.4 xử đúng.

    Dùng `structural_traversal` — nghĩa vụ mức yếu DUY NHẤT còn lại sau khi
    `predicate_verdict` có checker (2026-08-23). Lưu ý mức yếu của
    `predicate_verdict` nằm ở tầng khác: C₁a chỉ hỏi *kind có checker không*,
    còn *vị từ cụ thể có kiểm được không* thì C₂ mới trả lời.
    """
    contract = RequestContract(
        obligations=(_ob(kind="structural_traversal", container="a", witness="max_val"),)
    )
    res = check_structural_coverage(contract, _spec_co_cay())
    assert not res.ok
    assert res.error_code == "SEMANTIC_VERIFICATION_UNAVAILABLE"
    assert res.weak_kinds == ["structural_traversal"]


def test_producer_nam_trong_nhanh_long_van_tinh_la_co():
    """C₁a chỉ kiểm CẤU TRÚC — nhánh có chạy hay không là việc của C₁b."""
    spec = _spec_tim_max()
    spec.statements = [
        IfStmt(
            condition=CompareCond(op="<", left=VarRefExpr(name="max_val"),
                                  right=LiteralExpr(value=100)),
            then_body=[AssignStmt(target_var="max_val", expr=LiteralExpr(value=9))],
            else_body=[],
        )
    ]
    contract = RequestContract(obligations=(_ob(cmp="max", witness="max_val"),))
    assert check_structural_coverage(contract, spec).ok


def test_hop_dong_rong_thi_pass():
    assert check_structural_coverage(RequestContract(), _spec_tim_max()).ok


def test_contract_la_bat_bien_khong_sua_duoc():
    """Nghĩa vụ đóng băng — stage sinh KHÔNG có quyền khai lại (§5.2)."""
    import pydantic

    c = RequestContract(obligations=(_ob(cmp="max", witness="max_val"),))
    with pytest.raises(pydantic.ValidationError):
        c.obligations = ()
