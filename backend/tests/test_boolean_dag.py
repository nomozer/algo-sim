# -*- coding: utf-8 -*-
"""M17 W1 — lock logic.boolean_dag: validator BE fail-closed + catalog entry.

Executor/oracle sống ở FE (dag.test.tsx — oracle đệ quy độc lập mọi gán trị);
BE lock validator mirror: cycle, arity, ref, dangling, bound, id trùng.
Pipeline end-to-end do audit matrix chạy (test_authenticity_audit).
"""

from __future__ import annotations

import pytest

from app.simulation.catalog import CATALOG
from app.validation.simulation import validate_boolean_dag_config


def _cfg(inputs=None, gates=None, output="g"):
    return {
        "inputs": inputs if inputs is not None else [{"id": "A", "value": 0}, {"id": "B", "value": 1}],
        "gates": gates if gates is not None else [{"id": "g", "op": "AND", "inputs": ["A", "B"]}],
        "output": output,
    }


def test_hop_le_chuan():
    cfg, err = validate_boolean_dag_config(_cfg())
    assert err is None
    assert cfg["output"] == "g"
    assert cfg["gates"][0]["op"] == "AND"


def test_cycle_reject():
    cfg, err = validate_boolean_dag_config(_cfg(
        gates=[
            {"id": "g1", "op": "AND", "inputs": ["A", "g2"]},
            {"id": "g2", "op": "NOT", "inputs": ["g1"]},
        ],
        output="g2",
    ))
    assert cfg is None and "CYCLE" in err


@pytest.mark.parametrize("op,n_inputs", [("NOT", 2), ("AND", 1), ("XOR", 3), ("OR", 1)])
def test_arity_sai_reject(op, n_inputs):
    refs = ["A", "B", "A"][:n_inputs]
    cfg, err = validate_boolean_dag_config(_cfg(gates=[{"id": "g", "op": op, "inputs": refs}]))
    assert cfg is None and "cần đúng" in err


def test_ref_khong_ton_tai_va_id_trung_reject():
    cfg, err = validate_boolean_dag_config(_cfg(gates=[{"id": "g", "op": "NOT", "inputs": ["Z"]}]))
    assert cfg is None and "không tồn tại" in err
    cfg, err = validate_boolean_dag_config(_cfg(
        inputs=[{"id": "A", "value": 0}, {"id": "A", "value": 1}],
        gates=[{"id": "g", "op": "NOT", "inputs": ["A"]}],
    ))
    assert cfg is None and "trùng" in err


def test_output_phai_la_cong():
    cfg, err = validate_boolean_dag_config(_cfg(output="A"))
    assert cfg is None and "MỘT cổng" in err


def test_cong_lo_lung_reject():
    cfg, err = validate_boolean_dag_config(_cfg(
        gates=[
            {"id": "g1", "op": "AND", "inputs": ["A", "B"]},
            {"id": "g2", "op": "OR", "inputs": ["A", "B"]},
        ],
        output="g1",
    ))
    assert cfg is None and "g2" in err


def test_op_ngoai_enum_va_value_sai_reject():
    cfg, err = validate_boolean_dag_config(_cfg(gates=[{"id": "g", "op": "NAND", "inputs": ["A", "B"]}]))
    assert cfg is None and "AND, OR, NOT, XOR" in err
    cfg, err = validate_boolean_dag_config(_cfg(inputs=[{"id": "A", "value": 2}]))
    assert cfg is None


def test_bound_reject():
    many_inputs = [{"id": f"i{k}", "value": 0} for k in range(5)]
    cfg, err = validate_boolean_dag_config(_cfg(inputs=many_inputs))
    assert cfg is None and "1–4" in err
    many_gates = [{"id": f"g{k}", "op": "NOT", "inputs": ["A"]} for k in range(9)]
    cfg, err = validate_boolean_dag_config(_cfg(gates=many_gates, output="g0"))
    assert cfg is None and "1–8" in err


def test_forbidden_keys_reject():
    raw = _cfg()
    raw["steps"] = [1]
    cfg, err = validate_boolean_dag_config(raw)
    assert cfg is None and "bị cấm" in err


def test_catalog_entry_descriptor_day_du():
    spec = CATALOG["logic.boolean_dag"]
    assert spec.domain == "logic"
    assert spec.config_contract_version == "logic-dag-1.0"
    owned = {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
    assert owned == {"boolean_composition.bounded_gate_dag"}
