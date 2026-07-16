# backend/tests/test_generic_engine_m13.py
"""M13 §3.4: runtime fail-closed — không còn undefined-thành-0 im lặng."""
import pytest
from app.simulation.generic_engine import (
    GenericEvaluationError, initial_base, values_of,
)


def _spec(objects, rules):
    return {"objects": objects, "rules": rules, "processes": [], "interactions": []}


def test_chuoi_dao_thu_tu_hoi_tu_dung_gia_tri():
    spec = _spec(
        [{"id": "x", "type": "switch", "value": 1},
         {"id": "mid", "type": "value_box"}, {"id": "kq", "type": "value_box"}],
        [{"type": "weighted_sum", "target": "kq", "inputs": ["mid"], "weights": [2]},
         {"type": "weighted_sum", "target": "mid", "inputs": ["x"], "weights": [3]}],
    )
    values = values_of(spec, initial_base(spec))
    assert values["mid"] == 3 and values["kq"] == 6  # trước đây cũng đúng nhờ fixed-point — GIỮ NGUYÊN


def test_toan_hang_khong_ton_tai_trong_values_nem_typed_error():
    # Validator chặn từ trước; đây là LƯỚI SAU CÙNG (defense in depth):
    spec = _spec(
        [{"id": "e1", "type": "edge"}, {"id": "kq", "type": "value_box"}],
        [{"type": "weighted_sum", "target": "kq", "inputs": ["e1"], "weights": [1]}],
    )
    with pytest.raises(GenericEvaluationError) as ei:
        values_of(spec, initial_base(spec))
    assert ei.value.code == "unresolved_dependency_after_bound"


def test_ket_qua_non_finite_nem_typed_error():
    spec = _spec(
        [{"id": "v", "type": "value_box", "value": 1e308}, {"id": "kq", "type": "value_box"}],
        [{"type": "weighted_sum", "target": "kq", "inputs": ["v"], "weights": [1e308]}],
    )
    with pytest.raises(GenericEvaluationError) as ei:
        values_of(spec, initial_base(spec))
    assert ei.value.code == "non_finite_numeric_value"
