# -*- coding: utf-8 -*-
"""M17 W2B — engine truy vấn bảng: đối chiếu ORACLE ĐỘC LẬP + validator fail-closed.

Oracle viết TAY trong test (list comprehension thuần Python), KHÔNG gọi lại
engine — nếu engine sai thì hai bên lệch. Đây là điều kiện để tin kết quả:
engine tự so với chính nó thì chứng minh được gì.
"""

from __future__ import annotations

import pytest

from app.simulation.table_query_engine import (
    MAX_PREDICATES,
    MAX_ROWS,
    run_table_query,
)
from app.validation.table_query import validate_table_query_config

SCHEMA = [
    {"name": "ten", "type": "text"},
    {"name": "diem", "type": "number"},
    {"name": "to", "type": "text"},
    {"name": "noi_tru", "type": "boolean"},
]
ROWS = [
    {"ten": "An", "diem": 8.5, "to": "A", "noi_tru": True},
    {"ten": "Bình", "diem": 6.0, "to": "B", "noi_tru": False},
    {"ten": "Chi", "diem": 9.0, "to": "A", "noi_tru": False},
    {"ten": "Dũng", "diem": 6.0, "to": "C", "noi_tru": True},
    {"ten": "Hà", "diem": 7.25, "to": "B", "noi_tru": True},
]


def cfg(**over) -> dict:
    base = {"specVersion": "table-1.0", "schema": SCHEMA, "rows": ROWS}
    base.update(over)
    v, err = validate_table_query_config(base)
    assert err is None, err
    return v


def kinds(res) -> list[str]:
    return [s["kind"] for s in res["steps"]]


# ── dấu vết ĐỦ 9 giai đoạn, ĐÚNG thứ tự ───────────────────────────
def test_dau_vet_du_chin_giai_doan_dung_thu_tu():
    res = run_table_query(cfg(
        filter={"op": ">", "column": "diem", "value": 6.5},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"},
        limit=2,
        aggregate={"func": "avg", "column": "diem"},
    ))
    k = kinds(res)
    order = ["read_row", "evaluate", "filtered_set", "projection", "sort",
             "limit", "accumulate", "result"]
    pos = [k.index(x) for x in order]
    assert pos == sorted(pos), f"thứ tự giai đoạn sai: {k}"
    assert {"keep", "drop"} & set(k), "thiếu bước giữ/loại"
    assert k[-1] == "result"
    # mỗi dòng nguồn được ĐỌC đúng một lần
    assert k.count("read_row") == len(ROWS)


def test_khong_lo_ket_qua_o_buoc_dau():
    """Bất biến sư phạm: bước 0 KHÔNG được chứa kết quả cuối."""
    res = run_table_query(cfg(aggregate={"func": "count"}))
    first = res["steps"][0]
    assert first["kind"] == "read_row"
    assert "aggregate" not in first["detail"]
    assert "rows" not in first["detail"]


# ── lọc: đối chiếu oracle ─────────────────────────────────────────
@pytest.mark.parametrize("pred,oracle", [
    ({"op": ">", "column": "diem", "value": 6.5},
     lambda r: r["diem"] > 6.5),
    ({"op": "=", "column": "to", "value": "A"},
     lambda r: r["to"] == "A"),
    ({"op": "!=", "column": "noi_tru", "value": True},
     lambda r: r["noi_tru"] is not True),
    ({"op": "contains", "column": "ten", "value": "n"},
     lambda r: "n" in r["ten"].lower()),
    ({"op": "and", "clauses": [
        {"op": ">=", "column": "diem", "value": 7},
        {"op": "=", "column": "to", "value": "A"}]},
     lambda r: r["diem"] >= 7 and r["to"] == "A"),
    ({"op": "or", "clauses": [
        {"op": "<", "column": "diem", "value": 6.5},
        {"op": "=", "column": "noi_tru", "value": True}]},
     lambda r: r["diem"] < 6.5 or r["noi_tru"] is True),
])
def test_loc_khop_oracle_doc_lap(pred, oracle):
    res = run_table_query(cfg(filter=pred))
    expected = [i for i, r in enumerate(ROWS) if oracle(r)]
    assert res["filtered_indices"] == expected


def test_moi_dong_deu_co_ly_do_giu_hoac_loai():
    """Học sinh phải thấy VÌ SAO, không chỉ thấy kết quả."""
    res = run_table_query(cfg(filter={"op": ">", "column": "diem", "value": 6.5}))
    verdicts = [s for s in res["steps"] if s["kind"] in ("keep", "drop")]
    assert len(verdicts) == len(ROWS)
    for v in verdicts:
        assert v["detail"]["reasons"], "phán quyết không kèm lý do"


# ── sắp xếp ỔN ĐỊNH ───────────────────────────────────────────────
def test_sap_xep_on_dinh_giu_thu_tu_goc_khi_bang_nhau():
    """Bình và Dũng cùng 6.0 → phải giữ nguyên thứ tự gốc (1 trước 3)."""
    res = run_table_query(cfg(sort={"column": "diem", "direction": "asc"}))
    order = res["ordered_indices"]
    assert order.index(1) < order.index(3)
    oracle = sorted(range(len(ROWS)), key=lambda i: ROWS[i]["diem"])
    assert order == oracle


def test_sap_xep_giam_dan_van_on_dinh():
    res = run_table_query(cfg(sort={"column": "diem", "direction": "desc"}))
    assert res["ordered_indices"].index(1) < res["ordered_indices"].index(3)


# ── tổng hợp: đối chiếu oracle ────────────────────────────────────
@pytest.mark.parametrize("agg,oracle", [
    ({"func": "count"}, lambda rs: len(rs)),
    ({"func": "sum", "column": "diem"}, lambda rs: sum(r["diem"] for r in rs)),
    ({"func": "min", "column": "diem"}, lambda rs: min(r["diem"] for r in rs)),
    ({"func": "max", "column": "diem"}, lambda rs: max(r["diem"] for r in rs)),
])
def test_tong_hop_khop_oracle(agg, oracle):
    res = run_table_query(cfg(aggregate=agg))
    assert res["aggregateResult"]["value"] == pytest.approx(oracle(ROWS))


def test_trung_binh_khop_oracle_va_tich_luy_tung_buoc():
    res = run_table_query(cfg(
        filter={"op": ">", "column": "diem", "value": 6.5},
        aggregate={"func": "avg", "column": "diem"}))
    kept = [r for r in ROWS if r["diem"] > 6.5]
    assert res["aggregateResult"]["value"] == pytest.approx(
        sum(r["diem"] for r in kept) / len(kept), abs=1e-4)
    acc = [s for s in res["steps"] if s["kind"] == "accumulate"]
    assert len(acc) == len(kept), "tích luỹ phải hiện TỪNG bước, không nhảy ra một số"


def test_count_sau_loc_dem_dung_tap_da_loc():
    res = run_table_query(cfg(
        filter={"op": "=", "column": "to", "value": "A"},
        aggregate={"func": "count"}))
    assert res["aggregateResult"]["value"] == sum(1 for r in ROWS if r["to"] == "A")


# ── pipeline kết hợp ──────────────────────────────────────────────
def test_pipeline_ket_hop_khop_oracle():
    res = run_table_query(cfg(
        filter={"op": ">=", "column": "diem", "value": 6.0},
        projection=["ten", "diem"],
        sort={"column": "diem", "direction": "desc"},
        limit=3))
    oracle = [r for r in ROWS if r["diem"] >= 6.0]
    oracle = sorted(oracle, key=lambda r: -r["diem"])[:3]
    assert res["result_rows"] == [{"ten": r["ten"], "diem": r["diem"]} for r in oracle]
    assert res["projected_columns"] == ["ten", "diem"]


# ── validator FAIL-CLOSED ─────────────────────────────────────────
@pytest.mark.parametrize("over,fragment", [
    ({"rows": []}, "chưa có dòng"),
    ({"schema": []}, "Thiếu lược đồ"),
    ({"filter": {"op": ">", "column": "ten", "value": 5}}, "không dùng được"),
    ({"filter": {"op": ">", "column": "khong_co", "value": 5}}, "không có trong bảng"),
    ({"filter": {"op": "like", "column": "ten", "value": "A"}}, "không hỗ trợ"),
    ({"projection": ["khong_co"]}, "không có trong bảng"),
    ({"sort": {"column": "diem", "direction": "lung_tung"}}, "Chiều sắp xếp"),
    ({"limit": 0}, "≥ 1"),
    ({"limit": 999}, "lớn hơn số dòng"),
    ({"aggregate": {"func": "sum", "column": "ten"}}, "kiểu số"),
    ({"aggregate": {"func": "median", "column": "diem"}}, "không hỗ trợ"),
    ({"aggregate": {"func": "sum"}}, "cần một cột"),
    ({"specVersion": "table-9.9"}, "specVersion"),
])
def test_validator_tu_choi_config_sai(over, fragment):
    base = {"specVersion": "table-1.0", "schema": SCHEMA, "rows": ROWS, **over}
    v, err = validate_table_query_config(base)
    assert v is None, f"đáng lẽ phải từ chối: {over}"
    assert fragment in err, f"lý do không nêu đúng vấn đề: {err}"


def test_validator_ep_kieu_va_tu_choi_o_sai_kieu():
    v, err = validate_table_query_config({
        "schema": [{"name": "n", "type": "number"}], "rows": [{"n": "12"}]})
    assert err is None and v["rows"][0]["n"] == 12       # chuỗi số → ép được
    v2, err2 = validate_table_query_config({
        "schema": [{"name": "n", "type": "number"}], "rows": [{"n": "cao"}]})
    assert v2 is None and "không phải số" in err2        # chữ → TỪ CHỐI


def test_validator_chan_vuot_bien():
    many = [{"ten": f"HS{i}", "diem": 5, "to": "A", "noi_tru": True}
            for i in range(MAX_ROWS + 1)]
    v, err = validate_table_query_config(
        {"schema": SCHEMA, "rows": many})
    assert v is None and str(MAX_ROWS) in err

    deep = {"op": "and", "clauses": [
        {"op": "and", "clauses": [
            {"op": "and", "clauses": [{"op": ">", "column": "diem", "value": 1},
                                      {"op": "<", "column": "diem", "value": 9}]},
            {"op": ">", "column": "diem", "value": 2}]},
        {"op": ">", "column": "diem", "value": 3}]}
    v2, err2 = validate_table_query_config(
        {"schema": SCHEMA, "rows": ROWS, "filter": deep})
    assert v2 is None and "lồng quá" in err2

    wide = {"op": "and", "clauses": [
        {"op": ">", "column": "diem", "value": i} for i in range(MAX_PREDICATES + 1)]}
    v3, err3 = validate_table_query_config(
        {"schema": SCHEMA, "rows": ROWS, "filter": wide})
    assert v3 is None and str(MAX_PREDICATES) in err3


def test_dong_thieu_o_thanh_None_khong_bia_gia_tri():
    v, err = validate_table_query_config({
        "schema": SCHEMA, "rows": [{"ten": "An", "diem": 8}]})
    assert err is None
    assert v["rows"][0]["to"] is None and v["rows"][0]["noi_tru"] is None


def test_o_trong_bi_bo_qua_khi_tong_hop_khong_coi_la_0():
    """Không được coi ô trống là 0 — đó là bịa dữ liệu (bài học M13 silent-zero)."""
    v, err = validate_table_query_config({
        "schema": [{"name": "d", "type": "number"}],
        "rows": [{"d": 10}, {"d": None}, {"d": 20}]})
    assert err is None
    res = run_table_query({**v, "aggregate": {"func": "avg", "column": "d"}})
    assert res["aggregateResult"]["value"] == pytest.approx(15.0)   # KHÔNG phải 10.0
    assert res["aggregateResult"]["counted"] == 2
