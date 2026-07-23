# -*- coding: utf-8 -*-
"""M17 W2B-S1 — lock CHỮ KÝ MỤC TIÊU + luật "một truy vấn".

Phủ đủ 7 nhóm §5. Điều phải giữ cân bằng: gộp ĐÚNG chỗ (hai cách nói cùng một
mục tiêu) và KHÔNG gộp sai chỗ (hai mục tiêu khác nhau) — sai chiều nào cũng
hỏng: gộp sai gây mất mát ngữ nghĩa, không gộp gây từ chối oan.
"""

from __future__ import annotations

import pytest

from app.simulation.completeness_gate import check_requested_combination
from app.simulation.goal_signature import canonical_goal_signature, query_key
from app.simulation.operations import requirements_from_structured

TABLE = "relational_table_query"


def req(op, **goal):
    return {"operation": f"{TABLE}:{op}", **goal}


def an(*reqs):
    return {"requested_operations": sorted({r["operation"] for r in reqs}),
            "requested_requirements": list(reqs)}


# ── chữ ký: ổn định, giữ kiểu, không phụ thuộc thứ tự khoá ────────
def test_khong_phu_thuoc_thu_tu_khoa():
    a = canonical_goal_signature(
        {"filter_column": "to", "filter_op": "=", "filter_value": "A",
         "aggregate_func": "count"})
    b = canonical_goal_signature(
        {"aggregate_func": "count", "filter_value": "A", "filter_op": "=",
         "filter_column": "to"})
    assert a == b and a is not None


def test_giu_kieu_cua_literal():
    """"5" (chuỗi) KHÁC 5 (số) — ép chung sẽ gộp nhầm hai điều kiện khác nhau."""
    s = canonical_goal_signature({"filter_column": "x", "filter_op": "=", "filter_value": "5"})
    n = canonical_goal_signature({"filter_column": "x", "filter_op": "=", "filter_value": 5})
    assert s != n
    # nhưng 6 và 6.0 là CÙNG một giá trị
    assert (canonical_goal_signature({"filter_column": "x", "filter_op": ">", "filter_value": 6})
            == canonical_goal_signature({"filter_column": "x", "filter_op": ">", "filter_value": 6.0}))


def test_chuan_hoa_cot_va_toan_tu_theo_hop_dong():
    """Hai cách DIỄN ĐẠT tương đương ⇒ CÙNG chữ ký (chống từ chối oan)."""
    a = canonical_goal_signature({"filter_column": "diem", "filter_op": ">", "filter_value": 6})
    b = canonical_goal_signature({"filter_column": " Diem ", "filter_op": "lon_hon", "filter_value": 6})
    assert a == b


def test_thu_tu_cot_chieu_khong_quan_trong():
    assert (canonical_goal_signature({"projection_columns": ["ten", "diem"]})
            == canonical_goal_signature({"projection_columns": ["diem", "ten"]}))


def test_phan_biet_predicate_va_cot_tong_hop_khac_nhau():
    A = canonical_goal_signature({"filter_column": "to", "filter_op": "=", "filter_value": "A"})
    B = canonical_goal_signature({"filter_column": "to", "filter_op": "=", "filter_value": "B"})
    assert A != B
    assert (canonical_goal_signature({"aggregate_func": "sum", "aggregate_column": "diem"})
            != canonical_goal_signature({"aggregate_func": "sum", "aggregate_column": "tuoi"}))
    # COUNT(*) phân biệt tường minh với COUNT(cột)
    assert (canonical_goal_signature({"aggregate_func": "count"})
            != canonical_goal_signature({"aggregate_func": "count", "aggregate_column": "diem"}))


def test_khong_neu_gi_thi_chu_ky_None():
    assert canonical_goal_signature({}) is None
    assert canonical_goal_signature({"operation": "x"}) is None
    assert canonical_goal_signature("khong phai dict") is None


def test_chu_ky_khong_chua_ket_qua():
    """Chữ ký mô tả YÊU CẦU. Trường lạ (kể cả đáp án) bị bỏ qua hoàn toàn."""
    sig = canonical_goal_signature(
        {"aggregate_func": "count", "result": 42, "value": 42, "answer": "2"})
    assert sig == canonical_goal_signature({"aggregate_func": "count"})
    assert "42" not in sig


def test_query_group_tuong_minh_thang_chu_ky():
    """Các tầng cùng một truy vấn khai chung `query_group` ⇒ một nhóm."""
    assert query_key({"filter_column": "a"}, 0) == query_key({"sort_column": "b"}, 0)
    assert query_key({}, 0) != query_key({}, 1)


# ── §5: 7 nhóm non-regression ─────────────────────────────────────
def _blocked(analysis, fam=TABLE):
    return check_requested_combination(analysis, {fam})


def test_case1_cung_COUNT_dien_dat_hai_cach_thi_gop():
    assert _blocked(an(
        req("count", filter_column="diem", filter_op=">", filter_value=6),
        req("count", filter_column="Diem", filter_op="lon_hon", filter_value=6.0),
    )) is None


def test_case2_COUNT_va_SUM_cung_dieu_kien_khong_gop():
    reqs = requirements_from_structured(an(
        req("count", filter_column="to", filter_op="=", filter_value="A"),
        req("sum", filter_column="to", filter_op="=", filter_value="A",
            aggregate_func="sum", aggregate_column="diem"),
    ))
    assert len(reqs) == 2
    assert _blocked(an(
        req("count", filter_column="to", filter_op="=", filter_value="A"),
        req("sum", filter_column="to", filter_op="=", filter_value="A",
            aggregate_func="sum", aggregate_column="diem"),
    )) is not None


def test_case3_COUNT_A_va_COUNT_B_khong_gop_va_bi_chan():
    v = _blocked(an(
        req("count", filter_column="to", filter_op="=", filter_value="A"),
        req("count", filter_column="to", filter_op="=", filter_value="B"),
    ))
    assert v is not None
    assert v[2]["independent_goal_count"] == 2
    assert v[2]["detected_by"] == "independent_goal"


def test_case4_pipeline_mot_truy_van_PASS():
    g = {"query_group": 0, "filter_column": "diem", "filter_op": ">=", "filter_value": 6}
    assert _blocked(an(req("filter", **g), req("projection", **g),
                       req("sort", **g), req("limit", **g))) is None


def test_case5_hai_pipeline_cung_aggregate_khac_predicate_bi_chan():
    assert _blocked(an(
        req("avg", query_group=0, filter_column="to", filter_op="=", filter_value="A",
            aggregate_func="avg", aggregate_column="diem"),
        req("avg", query_group=1, filter_column="to", filter_op="=", filter_value="B",
            aggregate_func="avg", aggregate_column="diem"),
    )) is not None


@pytest.mark.parametrize("ops,fam", [
    (["single_pass_scan:find_max", "single_pass_scan:find_min"], "single_pass_scan"),
    (["graph_traversal:bfs", "graph_traversal:dfs"], "graph_traversal"),
    (["comparison_sort:bubble", "comparison_sort:insertion"], "comparison_sort"),
    (["tree_traversal:preorder", "tree_traversal:inorder",
      "tree_traversal:postorder", "tree_traversal:level_order"], "tree_traversal"),
])
def test_case6_hanh_vi_chan_cu_KHONG_doi(ops, fam):
    """max+min · BFS+DFS · hai sort · bốn tree traversal vẫn bị chặn y như cũ
    (chúng KHÔNG khai mục tiêu có cấu trúc nên luật mới không đụng tới)."""
    assert check_requested_combination({"requested_operations": ops}, {fam}) is not None


def test_case7_boolean_sibling_target_van_KHONG_bi_tu_choi_oan():
    """§C1.1 giữ nguyên: ba target logic quy về một yêu cầu."""
    assert check_requested_combination(
        {"requested_operations": ["boolean_composition:rule_scene",
                                  "boolean_composition:boolean_dag"]},
        {"boolean_composition"}) is None


def test_family_chua_khai_muc_tieu_khong_bi_luat_moi_dung_toi():
    """Tương thích ngược: mọi yêu cầu goal=None ⇒ một nhóm ⇒ không kích hoạt."""
    from app.simulation.operations import query_keys_of

    a = {"requested_requirements": [
        {"operation": "single_pass_scan:find_max"},
        {"operation": "single_pass_scan:find_min"}]}
    assert query_keys_of(a, {"single_pass_scan"}) == [None]
