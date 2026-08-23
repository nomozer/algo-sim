# -*- coding: utf-8 -*-
"""C₁b — realized coverage, SAU execution (spec §5.3).

C₁a một mình KHÔNG phân biệt được **"có viết"** với **"có chạy"**. Một chương
trình khai đúng witness, đúng kiểu, có câu lệnh tạo ra nó — nhưng câu lệnh ấy
nằm trong nhánh không bao giờ đạt tới. C₁a PASS, và mô phỏng phát ra một
"nghĩa vụ" chưa từng xảy ra.

Ba câu hỏi tách bạch:
    C₁a — witness hợp lệ về CẤU TRÚC chưa?          (trước execution)
    C₁b — witness có được HIỆN THỰC HOÁ không?      (ở đây)
    C₂  — kết quả có THOẢ TÍNH CHẤT không?          (postconditions.py)
"""
from app.simulation.semantic_program.contract import (
    AssignStmt,
    CompareCond,
    ForRangeStmt,
    IfStmt,
    IndexRefExpr,
    LengthExpr,
    LiteralExpr,
    MemoryDeclaration,
    SemanticProgramSpec,
    VarRefExpr,
)
from app.simulation.semantic_program.coverage_gate import (
    check_realized_coverage,
    check_structural_coverage,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract

_HOP_DONG = RequestContract(
    obligations=(
        Obligation(kind="extremum", container="a",
                   params={"cmp": "min", "witness": "min_value"}),
    )
)


def _chay(spec):
    return SemanticProgramInterpreter(max_steps=300).execute(spec)


def _spec_nhanh_chet() -> SemanticProgramSpec:
    """`assign min_value` nằm trong nhánh có điều kiện KHÔNG BAO GIỜ đúng."""
    return SemanticProgramSpec(
        title="Nhánh chết",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[5, 1, 9]),
            MemoryDeclaration(name="min_value", type="int", initial_value=None),
        ],
        statements=[
            IfStmt(
                condition=CompareCond(op="==", left=LiteralExpr(value=1),
                                      right=LiteralExpr(value=2)),
                then_body=[AssignStmt(target_var="min_value",
                                      expr=LiteralExpr(value=1))],
                else_body=[],
            )
        ],
    )


def _spec_that_su_chay() -> SemanticProgramSpec:
    return SemanticProgramSpec(
        title="Tìm nhỏ nhất",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[5, 1, 9]),
            MemoryDeclaration(name="min_value", type="int", initial_value=None),
        ],
        statements=[
            AssignStmt(target_var="min_value",
                       expr=IndexRefExpr(container="a", index=LiteralExpr(value=0))),
            ForRangeStmt(
                loop_var="i",
                start=LiteralExpr(value=1),
                end=LengthExpr(container="a"),
                body=[
                    IfStmt(
                        condition=CompareCond(
                            op="<",
                            left=IndexRefExpr(container="a",
                                              index=VarRefExpr(name="i")),
                            right=VarRefExpr(name="min_value"),
                        ),
                        then_body=[
                            AssignStmt(
                                target_var="min_value",
                                expr=IndexRefExpr(container="a",
                                                  index=VarRefExpr(name="i")),
                            )
                        ],
                        else_body=[],
                    )
                ],
            ),
        ],
    )


def test_c1a_PASS_nhung_c1b_FAIL_o_nhanh_chet():
    """Đây là toàn bộ lý do C₁b tồn tại."""
    spec = _spec_nhanh_chet()
    assert check_structural_coverage(_HOP_DONG, spec).ok, "C₁a phải PASS ở ví dụ này"

    res = check_realized_coverage(_HOP_DONG, spec, _chay(spec))
    assert not res.ok
    assert res.error_code == "OBLIGATION_WITNESS_UNREALIZED"
    assert any("min_value" in m for m in res.missing)


def test_chuong_trinh_that_su_chay_thi_ca_hai_deu_PASS():
    spec = _spec_that_su_chay()
    assert check_structural_coverage(_HOP_DONG, spec).ok
    assert check_realized_coverage(_HOP_DONG, spec, _chay(spec)).ok


def test_witness_gan_gia_tri_None_khong_tinh_la_hien_thuc_hoa():
    """Khai biến rồi để `None` suốt lượt chạy = chưa tạo ra gì."""
    spec = _spec_nhanh_chet()
    res = check_realized_coverage(_HOP_DONG, spec, _chay(spec))
    assert not res.ok


def test_hop_dong_rong_thi_PASS():
    spec = _spec_that_su_chay()
    assert check_realized_coverage(RequestContract(), spec, _chay(spec)).ok


def test_nghia_vu_muc_yeu_khong_bi_C1b_ket_toi_thieu():
    """Mức yếu là chuyện của §5.4, không phải 'witness chưa hiện thực hoá'."""
    hop_dong = RequestContract(
        obligations=(
            Obligation(kind="structural_traversal", container="a",
                       params={"witness": "khong_ton_tai"}),
        )
    )
    spec = _spec_that_su_chay()
    res = check_realized_coverage(hop_dong, spec, _chay(spec))
    assert res.ok, "C₁b phải BỎ QUA nghĩa vụ không có checker — C₁a đã xử nó rồi"
