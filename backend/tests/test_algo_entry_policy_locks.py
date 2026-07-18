import pytest
from app.validation.simulation import validate_algorithm_config

ALL_8 = ["find_max", "find_min", "sum_if", "count_if",
         "linear_search", "binary_search", "bubble_sort", "insertion_sort"]


def _valid_config(aid: str) -> dict:
    """Fixture builder: config HỢP LỆ TỐI THIỂU per algorithm_id — điểm xuất phát
    của MỌI negative test (chống false-green: sai chỉ vì đúng MỘT mutation)."""
    data: dict = {"array": [5, 2, 9, 1]}
    if aid in ("linear_search", "binary_search"):
        data["target"] = 9
    if aid in ("sum_if", "count_if"):
        data["condition"] = {"op": ">", "value": 3}
    if aid in ("bubble_sort", "insertion_sort"):
        data["order"] = "asc"
    return {"problem": {"summary": "s", "input": "i", "output": "o"}, "data": data}


@pytest.mark.parametrize("aid", ALL_8)
def test_fixture_goc_hop_le(aid):
    """Chống false-green: fixture gốc PHẢI validate xanh trước khi mutate."""
    config, err = validate_algorithm_config(aid, _valid_config(aid))
    assert err is None and config is not None


@pytest.mark.parametrize("aid,field,expected_msg", [
    ("linear_search", "target", '"data.target"'),
    ("binary_search", "target", '"data.target"'),
    ("sum_if", "condition", '"data.condition"'),
    ("count_if", "condition", '"data.condition"'),
    ("bubble_sort", "order", '"data.order"'),
    ("insertion_sort", "order", '"data.order"'),
])
def test_xoa_dung_mot_required_field_ra_dung_nhanh_loi(aid, field, expected_msg):
    cfg = _valid_config(aid)
    del cfg["data"][field]                          # mutate ĐÚNG MỘT thuộc tính
    config, err = validate_algorithm_config(aid, cfg)
    assert config is None
    assert expected_msg in (err or "")              # đúng NHÁNH lỗi — không chỉ is None


@pytest.mark.parametrize("aid", ALL_8)
def test_bounds_2_15_tu_fixture_hop_le(aid):
    cfg = _valid_config(aid)
    cfg["data"]["array"] = [7]                      # mutate ĐÚNG MỘT thuộc tính
    config, err = validate_algorithm_config(aid, cfg)
    assert config is None
    assert "2–15" in (err or "")                    # message đặc trưng của nhánh bounds


# ── Khóa 7 — BỐN proof RIÊNG BIỆT cho binary_search (cùng một fixture unsorted) ──

def _unsorted_binsearch() -> dict:
    cfg = _valid_config("binary_search")
    cfg["data"]["array"] = [9, 3, 7]
    cfg["data"]["labels"] = ["chin", "ba", "bay"]
    cfg["data"]["target"] = 7
    return cfg


def test_binsearch_normalization_tat_dinh_khong_refuse():
    config, err = validate_algorithm_config("binary_search", _unsorted_binsearch())
    assert err is None and config is not None       # KHÔNG refuse
    assert config["data"]["array"] == [3, 7, 9]     # normalize tất định


def test_binsearch_label_giu_lien_ket_theo_gia_tri():
    config, _ = validate_algorithm_config("binary_search", _unsorted_binsearch())
    assert config["data"]["labels"] == ["ba", "bay", "chin"]  # label đi theo GIÁ TRỊ


def test_binsearch_annotation_su_pham_ton_tai():
    config, _ = validate_algorithm_config("binary_search", _unsorted_binsearch())
    assert "sắp xếp trước" in (config["notes"] or "")


def test_binsearch_idempotent_tren_output_da_chuan_hoa():
    config, _ = validate_algorithm_config("binary_search", _unsorted_binsearch())
    config2, err2 = validate_algorithm_config("binary_search", config)
    assert err2 is None and config2["data"]["array"] == [3, 7, 9]
