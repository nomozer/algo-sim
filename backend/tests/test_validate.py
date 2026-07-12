# -*- coding: utf-8 -*-
"""Test validator config theo domain (M3 §6, §9)."""

from app.validation.simulation import check_forbidden_keys, validate_algorithm_config


def _raw(**overrides):
    base = {
        "problem": {"summary": "s", "input": "i", "output": "o"},
        "data": {"array": [7.5, 9, 6], "labels": None, "target": None, "condition": None, "order": None},
        "data_generated": False,
        "notes": None,
    }
    base.update(overrides)
    return base


def test_config_hop_le_duoc_chuan_hoa():
    config, err = validate_algorithm_config("find_max", _raw())
    assert err is None
    assert config["algorithm_id"] == "find_max"
    assert config["data"]["array"] == [7.5, 9, 6]


def test_thieu_problem_van_hop_le_voi_gia_tri_mac_dinh():
    config, err = validate_algorithm_config("find_max", {"data": {"array": [1, 2, 3]}})
    assert err is None
    assert config["problem"]["summary"]  # có mặc định, không rỗng


def test_binary_search_day_chua_sap_tu_sap_va_chu_thich():
    config, err = validate_algorithm_config(
        "binary_search",
        _raw(data={"array": [9, 4, 7], "labels": ["C", "A", "B"], "target": 7}),
    )
    assert err is None
    assert config["data"]["array"] == [4, 7, 9]
    assert config["data"]["labels"] == ["A", "B", "C"]  # nhãn đi theo giá trị
    assert "sắp xếp trước" in config["notes"]


def test_thieu_target_bao_loi_dung_thong_diep():
    config, err = validate_algorithm_config("linear_search", _raw(data={"array": [1, 2, 3]}))
    assert config is None
    assert "data.target" in err


def test_mang_qua_dai_bi_tu_choi():
    config, err = validate_algorithm_config("find_max", _raw(data={"array": list(range(20))}))
    assert config is None
    assert "15" in err


def test_labels_lech_do_dai():
    config, err = validate_algorithm_config(
        "find_max", _raw(data={"array": [1, 2, 3], "labels": ["A", "B"]})
    )
    assert config is None
    assert "labels" in err


def test_condition_sai_op():
    config, err = validate_algorithm_config(
        "count_if", _raw(data={"array": [1, 2], "condition": {"op": "~", "value": 1}})
    )
    assert config is None
    assert "condition" in err


def test_sort_thieu_order():
    config, err = validate_algorithm_config("bubble_sort", _raw(data={"array": [3, 1, 2]}))
    assert config is None
    assert "order" in err


def test_cam_llm_sinh_dien_bien():
    """Yêu cầu cốt lõi M3 §5: config chứa steps/timeline bị chặn ở validator."""
    for bad_key in ("steps", "timeline", "state", "frames"):
        config, err = validate_algorithm_config("find_max", _raw(**{bad_key: [1, 2]}))
        assert config is None, f"khóa {bad_key} phải bị từ chối"
        assert "engine" in err.lower() or "cấm" in err

    assert check_forbidden_keys({"data": {}}) is None
    assert check_forbidden_keys({"timeline": []}) is not None
