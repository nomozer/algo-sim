"""M14 Task 5 — lock SortingFamilySpec schema + validate_family_spec fail-closed (§D)."""

from __future__ import annotations

import pytest

from app.simulation.families.sorting import (
    SORT_FAMILY_VERSION,
    SORTING_FAMILY_SCHEMA,
    validate_family_spec,
)


def _spec(**over):
    base = {"family_version": SORT_FAMILY_VERSION, "variant": "bubble", "array": [5, 2, 9], "order": "asc"}
    base.update(over)
    return base


def test_bubble_positive():
    cfg, err = validate_family_spec(_spec())
    assert err is None and cfg["variant"] == "bubble" and cfg["array"] == [5, 2, 9]


def test_insertion_positive_desc():
    cfg, err = validate_family_spec(_spec(variant="insertion", order="desc"))
    assert err is None and cfg["variant"] == "insertion" and cfg["order"] == "desc"


def test_labels_khop_do_dai():
    cfg, err = validate_family_spec(_spec(array=[8, 6], labels=["An", "Bình"]))
    assert err is None and cfg["labels"] == ["An", "Bình"]


def test_labels_lech_do_dai_reject():
    cfg, err = validate_family_spec(_spec(array=[8, 6], labels=["An"]))
    assert cfg is None and "labels" in err


@pytest.mark.parametrize("arr", [[1], list(range(16)), [1, float("nan")], [1, "x"], "notlist"])
def test_array_bound_va_so_huu_han(arr):
    cfg, err = validate_family_spec(_spec(array=arr))
    assert cfg is None and err


def test_variant_ngoai_enum_reject():
    cfg, err = validate_family_spec(_spec(variant="selection"))
    assert cfg is None and "variant" in err


def test_family_version_sai_reject():
    cfg, err = validate_family_spec(_spec(family_version="sort-fam-9"))
    assert cfg is None and "family_version" in err


def test_key_la_reject_khong_strip():
    cfg, err = validate_family_spec(_spec(steps=[1, 2, 3]))
    assert cfg is None and "ngoài SortingFamilySpec" in err


def test_order_sai_reject():
    cfg, err = validate_family_spec(_spec(order="giảm"))
    assert cfg is None and "order" in err


def test_schema_dong_dung_field():
    props = set(SORTING_FAMILY_SCHEMA["properties"])
    assert props == {"family_version", "variant", "array", "order", "labels", "notes"}
    assert SORTING_FAMILY_SCHEMA["properties"]["variant"]["enum"] == ["bubble", "insertion"]
