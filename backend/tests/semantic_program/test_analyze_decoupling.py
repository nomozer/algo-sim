# -*- coding: utf-8 -*-
"""Route semantic KHÔNG dùng từ vựng dẫn xuất catalog (spec §3.5, E5).

Khoá phạm vi cũ nằm ngay trong response schema của `analyze`:
`requested_operations` và `requested_mechanisms` dùng
`enum: list(analyze_exposed_operations())`, dẫn xuất từ 24 target. Bài ngoài
catalog thì LLM **không có từ vựng để khai**, nên tháo hai cổng kia vẫn chưa đủ.

Cách tách: HAI schema riêng, không trộn chung một enum. Catalog vocabulary vẫn
sống cho đường module; nó chỉ không được quyết định admissibility của route
semantic.
"""
import json

from app.simulation.operations import analyze_exposed_operations
from app.simulation.semantic_program.analyze_contract import (
    SEMANTIC_ANALYZE_SCHEMA,
    build_request_contract,
)
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS
from app.simulation.semantic_program.request_contract import RequestContract

_PAYLOAD = {
    "input_facts": [
        {"id": "I1", "kind": "array", "label": "dãy nhiệt độ", "value": [28, 31, 35]},
        {"id": "I2", "kind": "int", "label": "ngưỡng", "value": 30},
    ],
    "obligations": [
        {"kind": "extremum", "container": "t", "witness": "max_val", "cmp": "max"}
    ],
    "prescribed_procedure": None,
}


def test_enum_nghia_vu_dung_bang_taxonomy_da_dong_bang():
    enum = SEMANTIC_ANALYZE_SCHEMA["properties"]["obligations"]["items"]["properties"][
        "kind"
    ]["enum"]
    assert set(enum) == set(OBLIGATION_KINDS)


def test_schema_semantic_khong_chua_gia_tri_nao_dan_xuat_catalog():
    """Guard chống trôi ngược: ai đó tiện tay dán enum catalog vào là ĐỎ."""
    catalog = set(analyze_exposed_operations())
    text = json.dumps(SEMANTIC_ANALYZE_SCHEMA, ensure_ascii=False)
    lan_vao = sorted(v for v in catalog if f'"{v}"' in text)
    assert not lan_vao, (
        f"Giá trị dẫn xuất catalog lọt vào schema route semantic: {lan_vao}"
    )


def test_build_request_contract_dong_bang_thanh_bat_bien():
    import pydantic
    import pytest

    contract = build_request_contract(_PAYLOAD)
    assert isinstance(contract, RequestContract)
    assert len(contract.obligations) == 1
    assert contract.obligations[0].kind == "extremum"
    assert contract.obligations[0].witness == "max_val"
    with pytest.raises(pydantic.ValidationError):
        contract.obligations = ()


def test_input_fact_giu_nguyen_id_de_IR_tham_chieu():
    contract = build_request_contract(_PAYLOAD)
    assert [f.fact_id for f in contract.input_facts] == ["I1", "I2"]
    assert contract.fact("I1").values == (28, 31, 35)
    assert contract.fact("I2").values == (30,)
    assert contract.fact("khong_co") is None


def test_nghia_vu_ngoai_taxonomy_bi_loai_o_khau_dong_bang():
    """Server ĐÓNG BĂNG nghĩa là server lọc, không phải chép nguyên lời LLM."""
    xau = json.loads(json.dumps(_PAYLOAD))
    xau["obligations"].append(
        {"kind": "predicate_verdict", "container": "t", "witness": "ok"}
    )
    contract = build_request_contract(xau)
    kinds = [o.kind for o in contract.obligations]
    assert "predicate_verdict" not in kinds, (
        "Nghĩa vụ ngoài taxonomy phải bị loại ở khâu đóng băng — giữ lại thì "
        "C₁a sau đó mới phát hiện, muộn hơn một tầng"
    )
    assert kinds == ["extremum"]


def test_payload_rong_van_ra_hop_dong_hop_le():
    contract = build_request_contract({})
    assert contract.obligations == ()
    assert contract.input_facts == ()


def test_prescribed_procedure_dung_tap_dong_rieng_khong_lay_tu_catalog():
    from app.simulation.semantic_program.obligations import SEMANTIC_PRESCRIBED_PROCEDURES

    enum = SEMANTIC_ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"]
    assert set(enum) == set(SEMANTIC_PRESCRIBED_PROCEDURES)
