# -*- coding: utf-8 -*-
"""WITNESS PHẢI DẪN XUẤT TỪ DỮ LIỆU — cổng hỏi về CÔNG VIỆC, không về đáp án.

─── LỖ HỔNG ĐÃ ĐO ĐƯỢC (live 2026-08-24) ──────────────────────────────────────

Đề chuỗi ngoặc. LLM chép đúng `{[()]}`, khai đủ `stack`/`char`/`top_char`, rồi
gán thẳng `hop_le = true`. Vòng lặp KHÔNG chạy: `total_steps=2`, `stack=null`.

Mọi cổng phía trước đều xanh — có producer, kiểu hợp — và **C₂ cũng xanh**, vì
nó tính lại độc lập ra `True` và witness cũng `True`. Khớp.

Đó là giới hạn CẤU TRÚC của một oracle kiểm ĐÁP ÁN: nó không phân biệt được
"tính đúng" với "đoán trúng". Với phán quyết nhị phân, đoán bừa đúng 50%.

Cổng này bổ khuyết đúng chỗ ấy bằng một câu hỏi khác hẳn: *witness có dẫn xuất
từ dữ liệu không?* — trả lời được TĨNH, trước khi chạy, và không phụ thuộc đáp
án đúng hay sai.

TỔNG QUÁT cho mọi nghĩa vụ, không riêng `predicate_verdict`:
`extremum(arr, max_val)` gán thẳng `max_val = 89` cũng qua C₂ y hệt.
"""
import pytest

from app.simulation.semantic_program.contract import (
    AssignStmt,
    BinaryArithExpr,
    CompareCond,
    ForEachStmt,
    IfStmt,
    IndexRefExpr,
    LiteralExpr,
    MemoryDeclaration,
    PushStmt,
    SemanticProgramSpec,
    VarRefExpr,
)
from app.simulation.semantic_program.coverage_gate import (
    _bao_dong,
    _phu_thuoc,
    check_structural_coverage,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract

from .fixtures_coverage_18 import ALL_18_COVERAGE_FIXTURES


def _hd(kind="predicate_verdict", container="chuoi", witness="kq", **p):
    return RequestContract(
        obligations=(
            Obligation(kind=kind, container=container,
                       params={"witness": witness, **p}),
        )
    )


def _decl_chung():
    return [
        MemoryDeclaration(name="chuoi", type="str", initial_value="{[()]}",
                          source_fact_id="I1"),
        MemoryDeclaration(name="stack", type="stack", element_type="str",
                          initial_value=[]),
        MemoryDeclaration(name="kq", type="bool", initial_value=False),
    ]


# ── Nửa 1: BẮT được chương trình đoán bừa ─────────────────────────────────


def test_gan_THANG_dap_an_thi_C1a_CHAN():
    """Tái hiện đúng chương trình LLM sinh ra ở lượt live 2026-08-24."""
    doan = SemanticProgramSpec(
        title="Khai đáp án mà không tính",
        memory_declarations=_decl_chung(),
        statements=[AssignStmt(target_var="kq", expr=LiteralExpr(value=True))],
    )
    kq = check_structural_coverage(_hd(pred="balanced_delimiters"), doan)
    assert not kq.ok
    assert any("không dẫn xuất từ" in m for m in kq.missing), kq.missing


def test_C2_KHONG_bat_duoc_cung_chuong_trinh_ay():
    """Vế đối chứng — không có nó thì không thấy được vì sao cổng này cần tồn tại.

    C₂ tính lại độc lập ra `True`, witness cũng `True`, nên nó KHỚP. Oracle
    kiểm đáp án không có cách nào phân biệt tính đúng với đoán trúng.
    """
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.postconditions import check_postconditions

    doan = SemanticProgramSpec(
        title="Khai đáp án mà không tính",
        memory_declarations=_decl_chung(),
        statements=[AssignStmt(target_var="kq", expr=LiteralExpr(value=True))],
    )
    hd = _hd(pred="balanced_delimiters")
    assert check_postconditions(hd, doan, SemanticProgramInterpreter().execute(doan)).ok


def test_lo_hong_TONG_QUAT_khong_rieng_predicate_verdict():
    """`extremum` gán thẳng đáp án đúng cũng phải bị chặn."""
    spec = SemanticProgramSpec(
        title="Khai max mà không duyệt",
        memory_declarations=[
            MemoryDeclaration(name="arr", type="array", element_type="int",
                              initial_value=[12, 45, 89], source_fact_id="I1"),
            MemoryDeclaration(name="mx", type="int", initial_value=0),
        ],
        statements=[AssignStmt(target_var="mx", expr=LiteralExpr(value=89))],
    )
    kq = check_structural_coverage(
        _hd(kind="extremum", container="arr", witness="mx", cmp="max"), spec
    )
    assert not kq.ok and any("không dẫn xuất từ" in m for m in kq.missing)


# ── Nửa 2: KHÔNG kêu oan ──────────────────────────────────────────────────


def test_dan_xuat_qua_NHANH_van_tinh_la_dan_xuat():
    """`kq = False` trong nhánh so sánh phần tử ⇒ phụ thuộc ĐIỀU KHIỂN.

    Thiếu vế này thì mọi chương trình đúng dùng `if` để kết luận đều bị kết
    tội — và một cổng kêu oan là một cổng sẽ bị tắt.
    """
    spec = SemanticProgramSpec(
        title="Kết luận qua nhánh",
        memory_declarations=_decl_chung(),
        statements=[
            ForEachStmt(
                item_var="c",
                container_or_expr="chuoi",
                body=[
                    IfStmt(
                        condition=CompareCond(
                            op="==", left=VarRefExpr(name="c"),
                            right=LiteralExpr(value="("),
                        ),
                        then_body=[PushStmt(container="stack",
                                            val=VarRefExpr(name="c"))],
                        else_body=[AssignStmt(target_var="kq",
                                              expr=LiteralExpr(value=False))],
                    )
                ],
            )
        ],
    )
    kq = check_structural_coverage(_hd(pred="balanced_delimiters"), spec)
    assert kq.ok, kq.missing


def test_dan_xuat_BAC_CAU_qua_nhieu_buoc():
    """`kq ← t ← arr[0]`: phụ thuộc qua ba bước vẫn là phụ thuộc."""
    spec = SemanticProgramSpec(
        title="Bắc cầu",
        memory_declarations=[
            MemoryDeclaration(name="arr", type="array", element_type="int",
                              initial_value=[1, 2], source_fact_id="I1"),
            MemoryDeclaration(name="t", type="int", initial_value=0),
            MemoryDeclaration(name="kq", type="int", initial_value=0),
        ],
        statements=[
            AssignStmt(target_var="t",
                       expr=IndexRefExpr(container="arr",
                                         index=LiteralExpr(value=0))),
            AssignStmt(target_var="kq",
                       expr=BinaryArithExpr(op="+", left=VarRefExpr(name="t"),
                                            right=LiteralExpr(value=1))),
        ],
    )
    assert "arr" in _bao_dong(_phu_thuoc(spec.statements, frozenset()), "kq")


@pytest.mark.parametrize(
    "spec", ALL_18_COVERAGE_FIXTURES,
    ids=[s.title[:24] for s in ALL_18_COVERAGE_FIXTURES],
)
def test_khong_fixture_nao_bi_ket_toi_oan(spec):
    """Mọi biến ĐƯỢC GHI của 18 fixture chuẩn đều dẫn xuất từ dữ liệu đề.

    Đây là phép kiểm dương tính giả của cả cổng: 18 chương trình này viết tay,
    đúng, và đại diện cho toàn bộ dải primitive. Cổng chấm sai một cái là hỏng.
    """
    dep = _phu_thuoc(spec.statements, frozenset())
    nguon = {d.name for d in spec.memory_declarations
             if d.initial_value not in (None, [], {}, "", 0)}
    xau = [w for w in dep if not (nguon & _bao_dong(dep, w))]
    assert xau == [], f"bị chấm là không dẫn xuất: {xau}"
