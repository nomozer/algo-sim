# -*- coding: utf-8 -*-
"""Interpreter và validator phải FAIL-CLOSED ở biên. **0 API call.**

LUẬT (giữ nguyên từ audit 2026-08-24): không no-op im lặng · không trả `None` khi đó là lỗi ngữ nghĩa · không tự bịa
giá trị mặc định. Vi phạm ⇒ lỗi tường minh, và route dịch nó thành `servable=False`.

(/13) Bản trước khoá luật này trên thao tác container (pop/dequeue/peek trên rỗng, index ngoài biên, `map_get`) —
từ vựng ấy đã gỡ cùng miền Tin học. Ba luật CHUNG còn lại được khoá ở đây, cộng luật "mọi checker ứng với một nghĩa vụ
có thật" chuyển từ `test_postconditions.py` (file ấy chỉ còn ca Tin học nên đã gỡ).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import (
    ERR_SAI_KIEU,
    SemanticExecutionError,
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.validator import validate_semantic_program


def _spec(memory: list[dict], statements: list[dict]) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0",
        "title": "Chương trình kiểm biên",
        "memory_declarations": memory,
        "statements": statements,
    })


def test_bieu_thuc_khong_co_nhanh_thuc_thi_thi_NEM_ke_ca_khi_bo_qua_validator():
    """Phòng thủ chiều sâu: thêm một biểu thức vào union mà quên nhánh ở interpreter là LỖI HỢP ĐỒNG — trả `None`
    biến nó thành một giá trị hợp lệ chạy tiếp. Gọi thẳng `_eval_value`, không qua validator."""
    it = SemanticProgramInterpreter()
    it.memory = {}
    with pytest.raises(SemanticExecutionError) as e:
        it._eval_value(SimpleNamespace(kind="khong_ton_tai"))
    assert e.value.code == ERR_SAI_KIEU and "khong_ton_tai" in str(e.value)


def test_validator_tu_choi_bien_chua_khai():
    spec = _spec([{"name": "k", "type": "int", "initial_value": 0}],
                 [{"kind": "assign", "target_var": "k", "expr": {"kind": "var", "name": "chua_khai"}}])
    kq = validate_semantic_program(spec)
    assert not kq.ok and "chua_khai" in kq.error


def test_validator_tu_choi_break_ngoai_vong_lap():
    kq = validate_semantic_program(_spec([], [{"kind": "break"}]))
    assert not kq.ok and "break" in kq.error


def test_break_TRONG_vong_lap_thi_hop_le():
    spec = _spec([], [{"kind": "for_range", "loop_var": "i", "start": {"kind": "literal", "value": 0},
                       "end": {"kind": "literal", "value": 3}, "body": [{"kind": "break"}]}])
    assert validate_semantic_program(spec).ok
    assert SemanticProgramInterpreter().execute(spec).status == "completed"


def test_moi_checker_deu_ung_voi_mot_nghia_vu_co_that():
    """Checker không có nghĩa vụ nào gọi tới là mã chết trông như năng lực."""
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS
    from app.simulation.semantic_program.postconditions import CHECKERS

    assert set(CHECKERS) <= set(OBLIGATION_KINDS), sorted(set(CHECKERS) - set(OBLIGATION_KINDS))
