# -*- coding: utf-8 -*-
"""M13: contract-lock — nguồn giá trị dẫn xuất từ PRIMITIVE_ROLES, không viết tay."""
import json
from pathlib import Path

from app.simulation.dsl.manifest import (
    RULE_IO_ROLES,
    dsl_semantic_contract,
    rule_types,
    value_provider_types,
)


def test_numeric_providers_dan_xuat_tu_manifest():
    # Snapshot CÓ Ý THỨC: đổi manifest thì test này phải được cập nhật kèm lý do.
    assert value_provider_types("numeric") == {"switch", "lamp", "value_box"}


def test_logical_providers_dan_xuat_tu_manifest():
    assert value_provider_types("logical") == {"switch", "lamp"}


def test_relational_khong_phai_value_provider():
    assert "node" not in value_provider_types("numeric")
    assert "edge" not in value_provider_types("numeric")


def test_rule_io_roles_phu_du_moi_rule_type_cua_manifest():
    """Anti-pattern #1: thêm rule type vào manifest mà quên khai input/output
    role → hợp đồng im lặng thiếu → Task 3/5 under-enforce. Khoá completeness."""
    assert set(RULE_IO_ROLES) == rule_types()


def test_dsl_contract_json_khong_troi_khoi_manifest():
    """Đổi manifest mà quên chạy generate_dsl_contract.py → test ĐỎ (anti-pattern #1)."""
    committed = json.loads(
        (Path(__file__).resolve().parents[2] / "frontend/src/simulations/domains/generic/dsl-contract.json")
        .read_text(encoding="utf-8")
    )
    assert committed == dsl_semantic_contract()
