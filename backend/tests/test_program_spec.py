# -*- coding: utf-8 -*-
"""M17 W2C — hợp đồng `ProgramSpec` + validator FAIL-CLOSED.

Bất biến khoá ở đây:
- ngữ pháp ĐÓNG (không hàm/đệ quy/mảng/chuỗi/float/IO/break);
- KHÔNG coercion ("5"≠5, true≠1, 1≠true);
- while BẮT BUỘC có biên;
- giới hạn đọc từ MỘT nguồn (`program_spec.LIMITS`), không magic number;
- spec KHÔNG được mang kết quả/diễn biến (R0).
"""
from __future__ import annotations

import pytest

from app.simulation.program_spec import (
    EXPRESSION_KINDS,
    LIMITS,
    SPEC_VERSION,
    STATEMENT_KINDS,
    all_operators,
    expression_kind_enum,
    statement_kind_enum,
)
from app.validation.program import validate_program_config


def _spec(**over) -> dict:
    """x = 3 ; y = x*2 + 1 (hợp lệ) — base cho các ca biến tấu."""
    base = {
        "program_version": SPEC_VERSION,
        "variables": [
            {"name": "x", "type": "integer", "int_value": 3},
            {"name": "y", "type": "integer", "int_value": 0},
        ],
        "expressions": [
            {"id": "e_x", "kind": "var", "name": "x"},
            {"id": "e_2", "kind": "int", "int_value": 2},
            {"id": "e_1", "kind": "int", "int_value": 1},
            {"id": "e_mul", "kind": "binary", "op": "*", "left": "e_x", "right": "e_2"},
            {"id": "e_sum", "kind": "binary", "op": "+", "left": "e_mul", "right": "e_1"},
        ],
        "statements": [{"id": "s1", "kind": "assign", "target": "y", "value": "e_sum"}],
        "main": ["s1"],
    }
    base.update(over)
    return base


# ── ngữ pháp đóng ───────────────────────────────────────────────

def test_ngu_phap_dong_dung_bon_cau_lenh_va_bay_bieu_thuc():
    """Ngữ pháp là HỢP ĐỒNG: nới thêm loại câu lệnh/biểu thức phải sửa ở đây —
    không lặng lẽ trượt thành trình thông dịch tổng quát."""
    assert set(STATEMENT_KINDS) == {"assign", "if", "while", "output"}
    assert set(EXPRESSION_KINDS) == {"int", "bool", "var", "unary", "binary", "compare", "logic"}


def test_schema_enum_dan_xuat_tu_program_spec():
    """Anti-pattern #1: enum của schema Gemini phải DẪN XUẤT, không viết tay."""
    from app.simulation.catalog import CATALOG

    props = CATALOG["algorithm.bounded_control_flow"].config_schema["properties"]
    assert props["statements"]["items"]["properties"]["kind"]["enum"] == statement_kind_enum()
    assert props["expressions"]["items"]["properties"]["kind"]["enum"] == expression_kind_enum()
    assert props["expressions"]["items"]["properties"]["op"]["enum"] == all_operators()


@pytest.mark.parametrize("kind", ["function", "for", "break", "continue", "call", "return"])
def test_cau_lenh_ngoai_ngu_phap_bi_tu_choi(kind):
    cfg, err = validate_program_config(_spec(
        statements=[{"id": "s1", "kind": kind, "target": "y", "value": "e_sum"}]))
    assert cfg is None and "không hỗ trợ" in err


@pytest.mark.parametrize("kind", ["call", "index", "slice", "lambda", "attribute"])
def test_bieu_thuc_ngoai_ngu_phap_bi_tu_choi(kind):
    spec = _spec()
    spec["expressions"].append({"id": "e_bad", "kind": kind})
    cfg, err = validate_program_config(spec)
    assert cfg is None and "không hỗ trợ" in err


# ── không coercion ──────────────────────────────────────────────

def test_chuoi_khong_thanh_so():
    cfg, err = validate_program_config(_spec(
        variables=[{"name": "x", "type": "integer", "int_value": "5"}]))
    assert cfg is None and "số nguyên" in err


def test_true_khong_thanh_1_va_1_khong_thanh_true():
    cfg, err = validate_program_config(_spec(
        variables=[{"name": "x", "type": "integer", "int_value": True}]))
    assert cfg is None, "True là bool — không được nhận làm số nguyên"

    cfg, err = validate_program_config(_spec(
        variables=[{"name": "x", "type": "boolean", "bool_value": 1}]))
    assert cfg is None, "1 không được nhận làm giá trị đúng/sai"


def test_gan_sai_kieu_bi_tu_choi():
    spec = _spec(variables=[
        {"name": "x", "type": "integer", "int_value": 3},
        {"name": "y", "type": "boolean", "bool_value": False},
    ])
    cfg, err = validate_program_config(spec)  # y là boolean nhưng gán biểu thức số
    assert cfg is None and "không tự đổi kiểu" in err


def test_so_sanh_bang_hai_kieu_khac_nhau_bi_tu_choi():
    spec = _spec()
    spec["variables"].append({"name": "b", "type": "boolean", "bool_value": True})
    spec["expressions"] += [
        {"id": "e_b", "kind": "var", "name": "b"},
        {"id": "e_eq", "kind": "compare", "op": "==", "left": "e_x", "right": "e_b"},
    ]
    spec["statements"] = [
        {"id": "s_in", "kind": "assign", "target": "y", "value": "e_1"},
        {"id": "s1", "kind": "if", "condition": "e_eq", "then_body": ["s_in"]},
    ]
    spec["main"] = ["s1"]
    cfg, err = validate_program_config(spec)
    assert cfg is None and "cùng kiểu" in err


def test_phep_cong_tren_boolean_bi_tu_choi():
    spec = _spec()
    spec["variables"].append({"name": "b", "type": "boolean", "bool_value": True})
    spec["expressions"] += [
        {"id": "e_b", "kind": "var", "name": "b"},
        {"id": "e_add", "kind": "binary", "op": "+", "left": "e_b", "right": "e_1"},
    ]
    spec["statements"] = [{"id": "s1", "kind": "assign", "target": "y", "value": "e_add"}]
    cfg, err = validate_program_config(spec)
    assert cfg is None and "số nguyên" in err


# ── biến chưa khai báo ──────────────────────────────────────────

def test_dung_bien_chua_khai_bao_bi_tu_choi():
    spec = _spec()
    spec["expressions"].append({"id": "e_z", "kind": "var", "name": "z"})
    cfg, err = validate_program_config(spec)
    assert cfg is None and "chưa được khai báo" in err


def test_gan_cho_bien_chua_khai_bao_bi_tu_choi():
    cfg, err = validate_program_config(_spec(
        statements=[{"id": "s1", "kind": "assign", "target": "z", "value": "e_sum"}]))
    assert cfg is None and "chưa khai báo" in err


def test_bien_khai_bao_trung_bi_tu_choi():
    cfg, err = validate_program_config(_spec(variables=[
        {"name": "x", "type": "integer", "int_value": 1},
        {"name": "x", "type": "integer", "int_value": 2},
    ]))
    assert cfg is None and "hai lần" in err


# ── điều kiện phải là boolean ───────────────────────────────────

@pytest.mark.parametrize("kind", ["if", "while"])
def test_dieu_kien_khong_phai_boolean_bi_tu_choi(kind):
    spec = _spec()
    body = {"id": "s_in", "kind": "assign", "target": "y", "value": "e_1"}
    head = {"id": "s1", "kind": kind, "condition": "e_x"}  # e_x là số nguyên
    head.update({"then_body": ["s_in"]} if kind == "if"
                else {"body": ["s_in"], "max_iterations": 5})
    spec["statements"] = [body, head]
    spec["main"] = ["s1"]
    cfg, err = validate_program_config(spec)
    assert cfg is None and "đúng/sai" in err


# ── while phải có biên ──────────────────────────────────────────

def _while_spec(max_iterations) -> dict:
    spec = _spec()
    spec["expressions"] += [
        {"id": "e_5", "kind": "int", "int_value": 5},
        {"id": "e_lt", "kind": "compare", "op": "<", "left": "e_x", "right": "e_5"},
        {"id": "e_inc", "kind": "binary", "op": "+", "left": "e_x", "right": "e_1"},
    ]
    w = {"id": "s_w", "kind": "while", "condition": "e_lt", "body": ["s_b"]}
    if max_iterations is not None:
        w["max_iterations"] = max_iterations
    spec["statements"] = [
        {"id": "s_b", "kind": "assign", "target": "x", "value": "e_inc"}, w,
    ]
    spec["main"] = ["s_w"]
    return spec


def test_while_thieu_bien_bi_tu_choi():
    cfg, err = validate_program_config(_while_spec(None))
    assert cfg is None and "max_iterations" in err


def test_while_vuot_tran_hop_dong_bi_tu_choi():
    cfg, err = validate_program_config(_while_spec(LIMITS["max_while_iterations"] + 1))
    assert cfg is None and str(LIMITS["max_while_iterations"]) in err


def test_while_co_bien_hop_le_thi_qua():
    cfg, err = validate_program_config(_while_spec(10))
    assert err is None and cfg["statements"][1]["max_iterations"] == 10


# ── giới hạn đọc từ MỘT nguồn ───────────────────────────────────

def test_qua_nhieu_bien():
    n = LIMITS["max_variables"] + 1
    cfg, err = validate_program_config(_spec(
        variables=[{"name": f"v{i}", "type": "integer", "int_value": 0} for i in range(n)]))
    assert cfg is None and str(LIMITS["max_variables"]) in err


def test_qua_nhieu_cau_lenh():
    n = LIMITS["max_statement_nodes"] + 1
    spec = _spec(
        statements=[{"id": f"s{i}", "kind": "assign", "target": "y", "value": "e_1"}
                    for i in range(n)],
        main=[f"s{i}" for i in range(n)])
    cfg, err = validate_program_config(spec)
    assert cfg is None and str(LIMITS["max_statement_nodes"]) in err


def test_bieu_thuc_lon_hon_gioi_han_do_sau():
    spec = _spec()
    prev = "e_1"
    for i in range(LIMITS["max_expression_depth"] + 1):
        spec["expressions"].append(
            {"id": f"d{i}", "kind": "binary", "op": "+", "left": prev, "right": "e_1"})
        prev = f"d{i}"
    spec["statements"] = [{"id": "s1", "kind": "assign", "target": "y", "value": prev}]
    cfg, err = validate_program_config(spec)
    assert cfg is None and str(LIMITS["max_expression_depth"]) in err


def test_long_qua_sau_bi_tu_choi():
    """Lồng if trong if trong if = 3 tầng > giới hạn 2."""
    spec = _spec()
    spec["expressions"].append(
        {"id": "e_t", "kind": "bool", "bool_value": True})
    spec["statements"] = [
        {"id": "s_leaf", "kind": "assign", "target": "y", "value": "e_1"},
        {"id": "s_l3", "kind": "if", "condition": "e_t", "then_body": ["s_leaf"]},
        {"id": "s_l2", "kind": "if", "condition": "e_t", "then_body": ["s_l3"]},
        {"id": "s_l1", "kind": "if", "condition": "e_t", "then_body": ["s_l2"]},
    ]
    spec["main"] = ["s_l1"]
    cfg, err = validate_program_config(spec)
    assert cfg is None and str(LIMITS["max_nesting_depth"]) in err


def test_chia_cho_khong_tinh_duoc_tinh_thi_bi_bat():
    spec = _spec()
    spec["expressions"] += [
        {"id": "e_0", "kind": "int", "int_value": 0},
        {"id": "e_div", "kind": "binary", "op": "//", "left": "e_x", "right": "e_0"},
    ]
    spec["statements"] = [{"id": "s1", "kind": "assign", "target": "y", "value": "e_div"}]
    cfg, err = validate_program_config(spec)
    assert cfg is None and "chia cho 0" in err


# ── cấu trúc tham chiếu ─────────────────────────────────────────

def test_bieu_thuc_vong_bi_tu_choi():
    spec = _spec()
    spec["expressions"] += [
        {"id": "c1", "kind": "binary", "op": "+", "left": "c2", "right": "e_1"},
        {"id": "c2", "kind": "binary", "op": "+", "left": "c1", "right": "e_1"},
    ]
    cfg, err = validate_program_config(spec)
    assert cfg is None and "vòng" in err


def test_cau_lenh_thuoc_hai_khoi_bi_tu_choi():
    spec = _spec()
    spec["expressions"].append({"id": "e_t", "kind": "bool", "bool_value": True})
    spec["statements"] = [
        {"id": "s_leaf", "kind": "assign", "target": "y", "value": "e_1"},
        {"id": "s_a", "kind": "if", "condition": "e_t", "then_body": ["s_leaf"]},
        {"id": "s_b", "kind": "if", "condition": "e_t", "then_body": ["s_leaf"]},
    ]
    spec["main"] = ["s_a", "s_b"]
    cfg, err = validate_program_config(spec)
    assert cfg is None and "chỉ thuộc một khối" in err


def test_cau_lenh_mo_coi_bi_tu_choi():
    spec = _spec()
    spec["statements"].append(
        {"id": "s_orphan", "kind": "assign", "target": "y", "value": "e_1"})
    cfg, err = validate_program_config(spec)
    assert cfg is None and "không nằm trong chương trình" in err


# ── R0: spec không mang kết quả ─────────────────────────────────

@pytest.mark.parametrize("key", ["trace", "steps", "final_environment", "result", "iterations"])
def test_spec_mang_ket_qua_bi_tu_choi(key):
    """R0: LLM chỉ mô tả CHƯƠNG TRÌNH; diễn biến và kết quả là của engine."""
    cfg, err = validate_program_config(_spec(**{key: [{"x": 3}]}))
    assert cfg is None and "KHÔNG được chứa kết quả" in err


# ── ca hợp lệ ───────────────────────────────────────────────────

def test_ca_hop_le_tra_config_sach():
    cfg, err = validate_program_config(_spec())
    assert err is None
    assert cfg["program_version"] == SPEC_VERSION
    assert [s["id"] for s in cfg["statements"]] == ["s1"]
    assert cfg["main"] == ["s1"]
    # trường chuẩn hoá đầy đủ để executor không phải đoán
    assert cfg["variables"][0] == {"name": "x", "type": "integer",
                                   "int_value": 3, "bool_value": None}
