"""M14 Task 7 — lock selector.resolve (§E2): FamilySpec → concrete + validation kép."""

from __future__ import annotations

from app.simulation.families.sorting import SORT_FAMILY_VERSION, resolve, validate_family_spec
from app.validation.simulation import validate_algorithm_config


def _valid(**over):
    base = {"family_version": SORT_FAMILY_VERSION, "variant": "bubble", "array": [5, 2, 9], "order": "asc"}
    base.update(over)
    cfg, err = validate_family_spec(base)
    assert err is None
    return cfg


_ANALYSIS = {"goal": "Sắp xếp điểm", "input_description": "Dãy điểm", "output_description": "Dãy tăng dần"}


def test_bubble_resolve_dung_concrete_id():
    sim_id, config = resolve(_valid(variant="bubble"), _ANALYSIS)
    assert sim_id == "algorithm.bubble_sort"


def test_insertion_resolve_dung_concrete_id():
    sim_id, config = resolve(_valid(variant="insertion"), _ANALYSIS)
    assert sim_id == "algorithm.insertion_sort"


def test_output_qua_duoc_validator_concrete_hien_co():
    sim_id, config = resolve(_valid(order="desc"), _ANALYSIS)
    validated, err = validate_algorithm_config("bubble_sort", config)
    assert err is None and validated is not None


def test_order_va_array_bao_toan():
    sim_id, config = resolve(_valid(array=[3, 1, 2], order="desc"), _ANALYSIS)
    assert config["data"]["array"] == [3, 1, 2]
    assert config["data"]["order"] == "desc"


def test_labels_bao_toan():
    sim_id, config = resolve(_valid(array=[8, 6], labels=["An", "Bình"]), _ANALYSIS)
    assert config["data"]["labels"] == ["An", "Bình"]


def test_adapter_output_khong_chua_family_field():
    sim_id, config = resolve(_valid(), _ANALYSIS)
    assert "family_version" not in config
    assert "variant" not in config
    # đúng shape AnalysisOk (problem + data)
    assert set(config["data"]) <= {"array", "order", "labels"}


def test_adapter_khong_doc_text_van_chay_khi_analysis_rong():
    sim_id, config = resolve(_valid(), {})
    assert sim_id == "algorithm.bubble_sort"
    assert config["problem"]["summary"]  # dùng default, không crash
