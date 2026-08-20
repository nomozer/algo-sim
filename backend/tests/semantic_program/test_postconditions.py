# -*- coding: utf-8 -*-
"""C₂ — hậu điều kiện SERVER-OWNED, executable (spec §5.3, §3.6).

Chạy SAU execution, CHỈ trên nghĩa vụ đã qua C₁a và C₁b.

`POSTCONDITION_VIOLATED` chỉ mang nghĩa **"hậu điều kiện server-owned bị vi
phạm"**. Nó KHÔNG phải bằng chứng "AI hiểu sai đề": hậu điều kiện do LLM đề xuất
mà vi phạm thì chỉ chứng minh chương trình TỰ MÂU THUẪN — một kết luận yếu hơn
hẳn. Oracle độc lập thật nằm ở đối chứng module và held-out benchmark.
"""
from app.simulation.semantic_program.contract import (
    AssignStmt,
    IndexRefExpr,
    LiteralExpr,
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.postconditions import (
    CHECKERS,
    check_postconditions,
)
from app.simulation.semantic_program.request_contract import RequestContract


def _spec_gan_phan_tu_dau() -> SemanticProgramSpec:
    """`m` nhận a[0] = 5, trong khi max thật là 9 và min thật là 1."""
    return SemanticProgramSpec(
        title="Gán phần tử đầu",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[5, 1, 9]),
            MemoryDeclaration(name="m", type="int", initial_value=None),
        ],
        statements=[
            AssignStmt(target_var="m",
                       expr=IndexRefExpr(container="a", index=LiteralExpr(value=0)))
        ],
    )


def _chay(spec):
    return SemanticProgramInterpreter(max_steps=300).execute(spec)


def _hd(kind, **params):
    return RequestContract(
        obligations=(Obligation(kind=kind, container="a", params=params),)
    )


def test_extremum_khong_thoa_thi_violated():
    spec = _spec_gan_phan_tu_dau()
    res = check_postconditions(_hd("extremum", cmp="max", witness="m"), spec, _chay(spec))
    assert not res.ok
    assert res.error_code == "POSTCONDITION_VIOLATED"
    assert any("9" in v for v in res.violations), res.violations


def test_extremum_thoa_thi_pass():
    spec = SemanticProgramSpec(
        title="Gán đúng max",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[5, 1, 9]),
            MemoryDeclaration(name="m", type="int", initial_value=None),
        ],
        statements=[AssignStmt(target_var="m", expr=LiteralExpr(value=9))],
    )
    assert check_postconditions(_hd("extremum", cmp="max", witness="m"), spec, _chay(spec)).ok


def test_cung_mot_chuong_trinh_nhung_nghia_vu_khac_thi_ket_qua_khac():
    """`m = 5` không phải max (9) và cũng không phải min (1)."""
    spec = _spec_gan_phan_tu_dau()
    res_max = check_postconditions(_hd("extremum", cmp="max", witness="m"), spec, _chay(spec))
    res_min = check_postconditions(_hd("extremum", cmp="min", witness="m"), spec, _chay(spec))
    assert not res_max.ok and not res_min.ok


def test_aggregate_matching_dem_va_tong():
    spec = SemanticProgramSpec(
        title="Đếm/tổng",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[4, 7, 12, 5]),
            MemoryDeclaration(name="k", type="int", initial_value=None),
        ],
        statements=[AssignStmt(target_var="k", expr=LiteralExpr(value=2))],
    )
    ok = check_postconditions(_hd("aggregate_matching", op="count", pred="even", witness="k"),
                              spec, _chay(spec))
    assert ok.ok, ok.violations
    xau = check_postconditions(_hd("aggregate_matching", op="sum", pred="even", witness="k"),
                               spec, _chay(spec))
    assert not xau.ok  # tổng số chẵn là 16, không phải 2


def test_ordering_kiem_day_da_sap():
    spec = SemanticProgramSpec(
        title="Dãy đã sắp",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[1, 5, 9]),
            MemoryDeclaration(name="m", type="int", initial_value=None),
        ],
        statements=[AssignStmt(target_var="m", expr=LiteralExpr(value=0))],
    )
    assert check_postconditions(_hd("ordering", cmp="asc", witness="a"), spec, _chay(spec)).ok


def test_ordering_day_chua_sap_thi_violated():
    spec = _spec_gan_phan_tu_dau()  # a = [5, 1, 9]
    res = check_postconditions(_hd("ordering", cmp="asc", witness="a"), spec, _chay(spec))
    assert not res.ok


def test_first_match_index_dung_vi_tri_dau_tien():
    spec = SemanticProgramSpec(
        title="Vị trí đầu tiên",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[30, 32, 36, 37]),
            MemoryDeclaration(name="vt", type="int", initial_value=None),
        ],
        statements=[AssignStmt(target_var="vt", expr=LiteralExpr(value=2))],
    )
    ok = check_postconditions(
        _hd("first_match_index", pred="gt", threshold=35, witness="vt"), spec, _chay(spec))
    assert ok.ok, ok.violations

    spec.statements = [AssignStmt(target_var="vt", expr=LiteralExpr(value=3))]
    xau = check_postconditions(
        _hd("first_match_index", pred="gt", threshold=35, witness="vt"), spec, _chay(spec))
    assert not xau.ok, "vị trí 3 cũng > 35 nhưng KHÔNG phải vị trí ĐẦU TIÊN"


def test_nghia_vu_khong_co_checker_thi_bo_qua_khong_ket_toi():
    """Mức yếu ≠ vi phạm. Nó là verification_gap ở §5.4, xử ở C₁a."""
    spec = _spec_gan_phan_tu_dau()
    assert check_postconditions(_hd("predicate_verdict", witness="m"), spec, _chay(spec)).ok


def test_moi_checker_deu_ung_voi_mot_nghia_vu_co_that():
    """Checker mồ côi = nhánh chết; nghĩa vụ thiếu checker = mức yếu câm."""
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    thua = sorted(set(CHECKERS) - set(OBLIGATION_KINDS))
    assert not thua, f"Checker không ứng với nghĩa vụ nào: {thua}"
