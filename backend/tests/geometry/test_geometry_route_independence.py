# -*- coding: utf-8 -*-
"""Đường hình học KHÔNG được phụ thuộc thẩm quyền Tin học. **0 API call.**

`GEOMETRY_PRODUCT_CUTOVER §3`. Ba câu hỏi, và cả ba phải là KHÔNG:

    GEOMETRY_DEPENDS_ON_INFORMATICS_ANALYZE     → NO
    GEOMETRY_DEPENDS_ON_INFORMATICS_CLASSIFIER  → NO
    GEOMETRY_DEPENDS_ON_INFORMATICS_CATALOG     → NO

⚠️ **Soi AST, không khớp chuỗi.** Guard khớp chuỗi trong kho này đã ba lần bắt
trúng chính chú thích của nó rồi báo xanh — `tests/source_scan.than_ma` sinh ra
đúng vì chuyện ấy. Ở đây đi xa hơn một bước: đọc cây gọi hàm THẬT của
`_chay_duong_hinh_hoc`, nên một lời gọi mới lén vào sẽ ĐỎ dù nó nằm trong một
biến, một alias hay một dòng không ai đọc.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

PIPELINE = (pathlib.Path(__file__).resolve().parents[2]
            / "app" / "ai" / "pipeline.py")

#: Thẩm quyền TIN HỌC — đường hình học không được chạm một cái nào.
CAM = {
    "stage_analyze": "analyze.md Tin học",
    "stage_classify": "classifier danh mục Tin học",
    "classify_with_one_route_recovery": "vòng phục hồi của classifier",
    "build_representation_plan": "kế hoạch biểu diễn suy từ analysis Tin học",
    "check_scope_and_simulatability": "cổng phạm vi đọc enum analyze.md",
    "check_execution_authority": "cổng quyền thực thi đọc analysis Tin học",
    "stage_simulate": "điền config cho một target danh mục",
    "catalog_text": "từ vựng danh mục Tin học",
    "llm_choices": "menu target Tin học",
}


def _cay() -> ast.Module:
    return ast.parse(PIPELINE.read_text(encoding="utf-8"))


def _ham(ten: str) -> ast.AST:
    for nut in ast.walk(_cay()):
        if isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and nut.name == ten:
            return nut
    raise AssertionError(f"không tìm thấy `{ten}` trong pipeline.py")


def _ten_duoc_goi(nut: ast.AST) -> set[str]:
    """Mọi TÊN được gọi bên trong một hàm, kể cả qua thuộc tính."""
    ra: set[str] = set()
    for x in ast.walk(nut):
        if isinstance(x, ast.Call):
            f = x.func
            if isinstance(f, ast.Name):
                ra.add(f.id)
            elif isinstance(f, ast.Attribute):
                ra.add(f.attr)
    return ra


def test_duong_hinh_hoc_khong_goi_mot_tham_quyen_TIN_HOC_nao():
    goi = _ten_duoc_goi(_ham("_chay_duong_hinh_hoc"))
    cham = sorted(goi & set(CAM))
    assert not cham, (
        "đường hình học đang gọi thẩm quyền Tin học: "
        + "; ".join(f"`{t}` ({CAM[t]})" for t in cham))


def test_run_pipeline_re_sang_hinh_hoc_TRUOC_moi_lượt_LLM():
    """Rẽ phải nằm trước `stage_analyze`, nếu không lượt gọi thừa vẫn bị tiêu.

    Đây là điều kiện mà một phép kiểm "có gọi hay không" bỏ sót: rẽ SAU thì
    hàm hình học vẫn sạch, mà đề hình học vẫn tốn một lượt Tin học.
    """
    rp = _ham("run_pipeline")
    dong_re = dong_analyze = None
    for x in ast.walk(rp):
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name):
            if x.func.id == "_chay_duong_hinh_hoc" and dong_re is None:
                dong_re = x.lineno
            if x.func.id == "stage_analyze" and dong_analyze is None:
                dong_analyze = x.lineno
    assert dong_re is not None, "`run_pipeline` không rẽ sang đường hình học"
    assert dong_analyze is not None, "không còn `stage_analyze`?"
    assert dong_re < dong_analyze, (
        f"rẽ hình học ở dòng {dong_re} nhưng `stage_analyze` ở {dong_analyze} — "
        "rẽ phải nằm TRƯỚC, nếu không đề hình học vẫn tiêu một lượt Tin học")


@pytest.mark.parametrize("mo_dun", [
    "app.simulation.semantic_program.route",
    "app.simulation.semantic_program.contract",
    "app.simulation.semantic_program.ir_static_check",
    "app.simulation.semantic_program.grounding_gate",
    "app.simulation.semantic_program.interpreter",
    "app.simulation.semantic_program.geometry_exec",
    "app.simulation.semantic_program.scene3d",
    "app.simulation.geometry.kernel",
    "app.simulation.geometry.measure",
])
def test_runtime_hinh_hoc_khong_nhap_danh_muc_TIN_HOC(mo_dun):
    """Tầng chạy của hình học không được nhập `catalog`/`dsl`.

    Đây là bất biến ĐÃ CÓ (`analyze_contract.py`: *"TÁCH HẲN khỏi từ vựng
    catalog"*), nhưng chưa từng có test khoá — và một bất biến chỉ sống trong
    chú thích thì nó là một lời hứa, không phải một ràng buộc.
    """
    import importlib

    m = importlib.import_module(mo_dun)
    src = pathlib.Path(m.__file__).read_text(encoding="utf-8")
    for nut in ast.walk(ast.parse(src)):
        ten = ""
        if isinstance(nut, ast.ImportFrom):
            ten = nut.module or ""
        elif isinstance(nut, ast.Import):
            ten = " ".join(a.name for a in nut.names)
        assert "simulation.catalog" not in ten and "simulation.dsl" not in ten, (
            f"{mo_dun} nhập danh mục/DSL Tin học: {ten}")
