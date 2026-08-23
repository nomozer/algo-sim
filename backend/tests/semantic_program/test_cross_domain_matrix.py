# -*- coding: utf-8 -*-
"""MA TRẬN XUYÊN MIỀN — bảy lớp trạng thái, một bộ cổng.

VÌ SAO KHOÁ BẰNG TEST chứ không chỉ để script chạy tay: cả wave vNext trước đó
dựa vào đúng MỘT case, và chính vì thế hai lỗi sản phẩm sống sót (`queue_view`
đọc spec tĩnh · `pop` áp LIFO lên FIFO) — cả hai vô hình với bằng chứng
chỉ-có-Stack. Ma trận chỉ có giá trị nếu nó chạy mỗi lần, và nếu nó ĐỎ ĐƯỢC.

Nửa thứ hai của file này quan trọng hơn nửa đầu: bản đầu của ma trận **rỗng** —
gỡ binding mà 6/7 lớp vẫn xanh. Test tiêm lỗi là thứ duy nhất phát hiện ra điều
đó, và là thứ giữ cho nó không quay lại.
"""
import importlib.util
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.learner_surface import check_learner_surface
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)

ROOT = Path(__file__).resolve().parents[3]


def _matrix_module():
    p = ROOT / "backend" / "scripts" / "cross_domain_matrix.py"
    spec = importlib.util.spec_from_file_location("cross_domain_matrix", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _matrix_module()


def _bien_dong(spec, ten: str) -> bool:
    r = SemanticProgramInterpreter(max_steps=300).execute(spec)
    return len({repr(s.memory_snapshot.get(ten)) for s in r.trace}) > 1


def _bo_container(spec, ten: str):
    vb = spec.visual_bindings
    return spec.model_copy(
        update={
            "visual_bindings": vb.model_copy(
                update={
                    "containers": [
                        c for c in (vb.containers or []) if c.semantic_id != ten
                    ]
                }
            )
        }
    )


def _bo_box(spec, var_ref: str):
    vb = spec.visual_bindings
    return spec.model_copy(
        update={
            "visual_bindings": vb.model_copy(
                update={
                    "value_boxes": [
                        b for b in (vb.value_boxes or []) if b.var_ref != var_ref
                    ]
                }
            )
        }
    )


# ── Nửa 1: bảy lớp đều qua ─────────────────────────────────────────────────


@pytest.mark.parametrize("case", M.CASES, ids=[c[0] for c in M.CASES])
def test_moi_lop_qua_toan_bo_cong(case):
    r = M._chay_mot_case(*case)
    hong = [g for g, v in r["gates"].items() if not v]
    assert r["pass"], f"{r['lop']}: trượt {hong} · {r['ghi_chu']}"


def test_du_BAY_lop_khong_thieu_lop_nao():
    """Thiếu một lớp là ma trận mất đúng giá trị của nó."""
    assert {c[0] for c in M.CASES} == {
        "scalar", "array", "string", "stack",
        "derived_sequence", "tree", "graph",
    }


def test_dap_an_duoc_kiem_TAY_khong_chep_tu_dau_ra_cua_he():
    """Oracle phải độc lập, nếu không cổng `EXPECTED_RESULT` là tautology."""
    mong = {lop: exp for lop, _, _, exp in M.CASES}
    # 21 = 10101₂ ⇒ bit thứ 2 = 1 · max([12,45,67,23,89,34]) = 89 (chỉ số 4)
    assert mong["scalar"]["bit_is_set"] is True
    assert mong["array"] == {"max_val": 89, "max_idx": 4}
    # prefix([2,4,1,7,3]) = [2,6,7,14,17] · preorder A(B,C) = A,B,C
    assert mong["derived_sequence"]["pref"] == [2, 6, 7, 14, 17]
    assert mong["tree"]["order"] == ["A", "B", "C"]
    assert mong["graph"]["order"] == ["1", "2", "3", "4", "5"]


# ── Nửa 2: ma trận phải ĐỎ ĐƯỢC ────────────────────────────────────────────


@pytest.mark.parametrize("case", M.CASES, ids=[c[0] for c in M.CASES])
def test_go_binding_cua_trang_thai_bien_dong_thi_DO(case):
    """Gỡ đường lên màn hình của thứ ĐANG DIỄN TIẾN ⇒ ma trận phải bắt.

    Lớp `scalar` không có container nào nên gỡ ô giá trị của witness — cùng ý
    nghĩa: thứ người học cần nhìn biến mất.
    """
    lop, spec, wit, exp = case
    ten = next(
        (
            c.semantic_id
            for c in (spec.visual_bindings.containers or [])
            if _bien_dong(spec, c.semantic_id)
        ),
        None,
    )
    hong = _bo_container(spec, ten) if ten else _bo_box(spec, wit)

    r = M._chay_mot_case(lop, hong, wit, exp)
    assert not r["pass"], f"{lop}: gỡ '{ten or wit}' mà ma trận vẫn xanh — cổng rỗng"


# ── Nửa 3: dữ liệu đề PHẢI thấy được, kể cả khi nó là VÔ HƯỚNG ────────────


def _spec_scalar_ghim(bind_num: bool) -> SemanticProgramSpec:
    """Bài vô hướng tối giản: đầu vào `n` ghim về đề, kết quả `r` có ô hiển thị."""
    from app.simulation.semantic_program.contract import (
        AssignStmt,
        BinaryArithExpr,
        LiteralExpr,
        VarRefExpr,
        VisualBindings,
        VisualValueBoxBinding,
    )

    boxes = [VisualValueBoxBinding(box_id="r_box", var_ref="r", label="Kết quả")]
    if bind_num:
        boxes.append(VisualValueBoxBinding(box_id="n_box", var_ref="n", label="n"))
    return SemanticProgramSpec(
        title="Nhân đôi một số",
        memory_declarations=[
            MemoryDeclaration(name="n", type="int", initial_value=21, source_fact_id="I1"),
            MemoryDeclaration(name="r", type="int", initial_value=0),
        ],
        statements=[
            AssignStmt(
                target_var="r",
                expr=BinaryArithExpr(
                    op="*", left=VarRefExpr(name="n"), right=LiteralExpr(value=2)
                ),
            )
        ],
        visual_bindings=VisualBindings(containers=[], pointers=[], value_boxes=boxes),
    )


def _contract_I1() -> RequestContract:
    return RequestContract(
        input_facts=(InputFact(fact_id="I1", label="số đề cho", values=(21,)),)
    )


@pytest.mark.parametrize("bind_num,mong_ok", [(True, True), (False, False)])
def test_du_lieu_de_VO_HUONG_cung_phai_hien(bind_num, mong_ok):
    """Miễn trừ vô hướng là để tha biến ĐẾM/TẠM, không phải tha dữ liệu đề.

    Bài "kiểm tra bit thứ k của n" giấu mất `n` thì học sinh xem một mô phỏng
    không biết đang xét số nào. `source_fact_id` là chỗ phân biệt hai loại đó,
    nên luật neo vào nó chứ không neo vào kiểu.
    """
    spec = _spec_scalar_ghim(bind_num)
    res = SemanticProgramInterpreter(max_steps=50).execute(spec)
    env = compile_semantic_program_to_envelope(spec)
    kq = check_learner_surface(_contract_I1(), spec, res, env)

    assert kq.ok is mong_ok, kq.invisible
    if not mong_ok:
        assert any("'n'" in u and "dữ liệu đề" in u for u in kq.invisible), kq.invisible
