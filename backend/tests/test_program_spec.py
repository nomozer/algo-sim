# -*- coding: utf-8 -*-
"""M17 W2C(+C1) — hợp đồng `ProgramSpec` + validator FAIL-CLOSED.

Bất biến khoá:
- ngữ pháp ĐÓNG (không hàm/đệ quy/mảng/chuỗi/float/IO/break);
- **§L1** khai báo ≠ khởi tạo; đọc biến chưa chắc có giá trị là TỪ CHỐI;
  hệ KHÔNG bịa 0/false/null làm mặc định;
- **§L2** bề mặt LLM là biểu thức INLINE, nông, phi đệ quy — không bảng biểu
  thức, không tự đặt id, không tham chiếu chéo; normalizer TẤT ĐỊNH;
- KHÔNG coercion ("5"≠5, true≠1, 1≠true);
- while BẮT BUỘC có biên; giới hạn đọc từ MỘT nguồn (`program_spec.LIMITS`);
- spec KHÔNG mang kết quả/diễn biến (R0).
"""
from __future__ import annotations

import pytest

from app.simulation.program_spec import (
    LIMITS,
    OPERAND_KINDS,
    SPEC_VERSION,
    STATEMENT_KINDS,
    NormalizeError,
    normalize_inline_program,
    statement_kind_enum,
)
from app.validation.program import validate_program_config


# ── dựng spec bằng bề mặt INLINE ────────────────────────────────
def iv(n):
    return {"kind": "int", "int_value": n}


def bv(b):
    return {"kind": "bool", "bool_value": b}


def var(n):
    return {"kind": "var", "name": n}


def val(left, op=None, right=None):
    v = {"left": left}
    if op is not None:
        v["op"], v["right"] = op, right
    return v


def atom(left, op=None, right=None, negated=False):
    a = {"left": left}
    if op is not None:
        a["op"], a["right"] = op, right
    if negated:
        a["negated"] = True
    return a


def cond(atoms, op=None):
    c = {"atoms": atoms}
    if op is not None:
        c["op"] = op
    return c


def prog(variables, statements, main, **over):
    spec = {"program_version": SPEC_VERSION, "variables": variables,
            "statements": statements, "main": main}
    spec.update(over)
    return spec


def ok(spec):
    cfg, err = validate_program_config(spec)
    assert cfg is not None, f"đáng lẽ hợp lệ nhưng bị từ chối: {err}"
    return cfg


def rejected(spec) -> str:
    cfg, err = validate_program_config(spec)
    assert cfg is None, "đáng lẽ bị từ chối nhưng lại qua"
    return err


# base: x = 3 ; y = x + 1
def base(**over):
    spec = {
        "program_version": SPEC_VERSION,
        "variables": [{"name": "x", "type": "integer", "int_value": 3},
                      {"name": "y", "type": "integer"}],
        "statements": [{"id": "s1", "kind": "assign", "target": "y",
                        "value": val(var("x"), "+", iv(1))}],
        "main": ["s1"],
    }
    spec.update(over)
    return spec


# ══════════════ ngữ pháp đóng ══════════════

def test_ngu_phap_dong_dung_bon_cau_lenh():
    assert set(STATEMENT_KINDS) == {"assign", "if", "while", "output"}
    assert set(OPERAND_KINDS) == {"int", "bool", "var"}


def test_schema_gemini_dan_xuat_va_KHONG_con_bang_bieu_thuc():
    """§L2: LLM không còn phải tự dựng bảng biểu thức rồi tham chiếu bằng id."""
    from app.simulation.catalog import CATALOG

    schema = CATALOG["algorithm.bounded_control_flow"].config_schema
    props = schema["properties"]
    assert "expressions" not in props, "bề mặt LLM vẫn còn bảng biểu thức"
    assert props["statements"]["items"]["properties"]["kind"]["enum"] == statement_kind_enum()
    # biểu thức nằm INLINE trong câu lệnh
    val_schema = props["statements"]["items"]["properties"]["value"]
    assert val_schema["properties"]["left"]["properties"]["kind"]["enum"] == list(OPERAND_KINDS)


@pytest.mark.parametrize("kind", ["function", "for", "break", "continue", "call", "return"])
def test_cau_lenh_ngoai_ngu_phap_bi_tu_choi(kind):
    err = rejected(base(statements=[{"id": "s1", "kind": kind, "target": "y",
                                     "value": val(iv(1))}]))
    assert "không hỗ trợ" in err


@pytest.mark.parametrize("op", ["**", "and", "sqrt", "<<"])
def test_toan_tu_so_hoc_ngoai_ngu_phap_bi_tu_choi(op):
    err = rejected(base(statements=[
        {"id": "s1", "kind": "assign", "target": "y", "value": val(var("x"), op, iv(1))}]))
    assert "không hỗ trợ" in err


@pytest.mark.parametrize("kind", ["call", "index", "lambda", "attribute"])
def test_toan_hang_ngoai_ngu_phap_bi_tu_choi(kind):
    err = rejected(base(statements=[
        {"id": "s1", "kind": "assign", "target": "y", "value": val({"kind": kind})}]))
    assert "không hỗ trợ" in err


# ══════════════ §L1 — khai báo ≠ khởi tạo ══════════════

def test_L1_bien_khai_bao_khong_co_gia_tri_ban_dau_la_HOP_LE():
    """Đề "nếu x>0 thì y=1 ngược lại y=-1" KHÔNG nói y ban đầu bằng mấy."""
    cfg = ok(prog(
        [{"name": "x", "type": "integer", "int_value": -2},
         {"name": "y", "type": "integer"}],
        [{"id": "t", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "e", "kind": "assign", "target": "y", "value": val(iv(-1))},
         {"id": "s", "kind": "if", "condition": cond([atom(val(var("x")), ">", val(iv(0)))]),
          "then_body": ["t"], "else_body": ["e"]}],
        ["s"]))
    y = next(v for v in cfg["variables"] if v["name"] == "y")
    assert y["initialized"] is False
    # KHÔNG bịa giá trị mặc định
    assert y["int_value"] is None and y["bool_value"] is None


def test_L1_gan_truoc_roi_doc_la_hop_le():
    ok(prog(
        [{"name": "y", "type": "integer"}, {"name": "z", "type": "integer"}],
        [{"id": "a", "kind": "assign", "target": "y", "value": val(iv(5))},
         {"id": "b", "kind": "assign", "target": "z", "value": val(var("y"), "+", iv(1))}],
        ["a", "b"]))


def test_L1_doc_bien_chua_gan_bi_TU_CHOI():
    err = rejected(prog(
        [{"name": "y", "type": "integer"}, {"name": "z", "type": "integer"}],
        [{"id": "b", "kind": "assign", "target": "z", "value": val(var("y"), "+", iv(1))}],
        ["b"]))
    assert "chưa chắc chắn có giá trị" in err


def test_L1_ca_hai_nhanh_deu_gan_thi_y_CHAC_CHAN_co_gia_tri():
    ok(prog(
        [{"name": "x", "type": "integer", "int_value": 1},
         {"name": "y", "type": "integer"}],
        [{"id": "t", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "e", "kind": "assign", "target": "y", "value": val(iv(0))},
         {"id": "s", "kind": "if", "condition": cond([atom(val(var("x")), ">", val(iv(0)))]),
          "then_body": ["t"], "else_body": ["e"]},
         {"id": "u", "kind": "output", "value": val(var("y"))}],
        ["s", "u"]))


def test_L1_chi_nhanh_then_gan_thi_CHUA_chac_chan():
    """Nhánh then có thể KHÔNG chạy — không được coi là đã khởi tạo."""
    err = rejected(prog(
        [{"name": "x", "type": "integer", "int_value": 1},
         {"name": "y", "type": "integer"}],
        [{"id": "t", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "s", "kind": "if", "condition": cond([atom(val(var("x")), ">", val(iv(0)))]),
          "then_body": ["t"], "else_body": []},
         {"id": "u", "kind": "output", "value": val(var("y"))}],
        ["s", "u"]))
    assert "chưa chắc chắn có giá trị" in err


def test_L1_gan_trong_while_KHONG_du_de_coi_la_da_khoi_tao():
    """Vòng lặp có thể chạy 0 lượt."""
    err = rejected(prog(
        [{"name": "x", "type": "integer", "int_value": 9},
         {"name": "y", "type": "integer"}],
        [{"id": "b", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "w", "kind": "while", "condition": cond([atom(val(var("x")), "<", val(iv(5)))]),
          "body": ["b"], "max_iterations": 5},
         {"id": "u", "kind": "output", "value": val(var("y"))}],
        ["w", "u"]))
    assert "chưa chắc chắn có giá trị" in err


def test_L1_doc_bien_chua_gan_NGAY_TRONG_dieu_kien_bi_tu_choi():
    err = rejected(prog(
        [{"name": "y", "type": "integer"}, {"name": "z", "type": "integer", "int_value": 0}],
        [{"id": "t", "kind": "assign", "target": "z", "value": val(iv(1))},
         {"id": "s", "kind": "if", "condition": cond([atom(val(var("y")), ">", val(iv(0)))]),
          "then_body": ["t"]}],
        ["s"]))
    assert "chưa chắc chắn có giá trị" in err


def test_L1_khong_tu_sinh_gia_tri_mac_dinh():
    cfg = ok(base())
    y = next(v for v in cfg["variables"] if v["name"] == "y")
    assert y["int_value"] is None, "hệ đã bịa giá trị ban đầu cho biến chưa khởi tạo"


# ══════════════ §L2 — biểu thức inline ══════════════

def test_L2_so_sanh_inline_normalize_dung():
    exprs, stmts = normalize_inline_program([
        {"id": "s", "kind": "while", "body": ["b"], "max_iterations": 3,
         "condition": cond([atom(val(var("x")), "<", val(iv(5)))])}])
    kinds = [e["kind"] for e in exprs]
    assert "compare" in kinds and "var" in kinds and "int" in kinds
    assert stmts[0]["condition"] == exprs[-1]["id"]


def test_L2_so_hoc_inline_normalize_dung():
    exprs, stmts = normalize_inline_program([
        {"id": "s", "kind": "assign", "target": "x", "value": val(var("x"), "+", iv(1))}])
    top = next(e for e in exprs if e["kind"] == "binary")
    assert top["op"] == "+"
    assert stmts[0]["value"] == top["id"]


def test_L2_a_AND_NOT_b_normalize_dung():
    exprs, _ = normalize_inline_program([
        {"id": "s", "kind": "if", "then_body": ["t"],
         "condition": cond([atom(val(var("a"))), atom(val(var("b")), negated=True)], op="and")}])
    assert any(e["kind"] == "unary" and e["op"] == "not" for e in exprs)
    assert any(e["kind"] == "logic" and e["op"] == "and" for e in exprs)


def test_L2_bien_la_bi_tu_choi():
    err = rejected(base(statements=[
        {"id": "s1", "kind": "assign", "target": "y", "value": val(var("khong_co"))}]))
    assert "chưa được khai báo" in err


def test_L2_normalization_TAT_DINH():
    """Cùng input ⇒ cùng output, kể cả id sinh ra."""
    raw = [{"id": "s", "kind": "assign", "target": "y", "value": val(var("x"), "*", iv(2))}]
    a = normalize_inline_program(raw)
    b = normalize_inline_program(raw)
    assert a == b


def test_L2_KHONG_con_tham_chieu_cheo_id_o_be_mat():
    """Spec kiểu cũ (statements trỏ vào bảng expressions bằng chuỗi id) KHÔNG
    còn được chấp nhận — một bề mặt duy nhất, không hai hợp đồng cạnh tranh."""
    old = prog(
        [{"name": "x", "type": "integer", "int_value": 1}],
        [{"id": "s1", "kind": "assign", "target": "x", "value": "e_1"}],
        ["s1"], expressions=[{"id": "e_1", "kind": "int", "int_value": 2}])
    assert validate_program_config(old)[0] is None


def test_L2_nhom_logic_qua_nhieu_ve_bi_tu_choi():
    n = LIMITS["max_condition_atoms"] + 1
    err = rejected(prog(
        [{"name": "a", "type": "boolean", "bool_value": True},
         {"name": "x", "type": "integer", "int_value": 0}],
        [{"id": "t", "kind": "assign", "target": "x", "value": val(iv(1))},
         {"id": "s", "kind": "if", "then_body": ["t"],
          "condition": cond([atom(val(var("a")))] * n, op="and")}],
        ["s"]))
    assert str(LIMITS["max_condition_atoms"]) in err


def test_L2_nhieu_ve_ma_thieu_toan_tu_logic_bi_tu_choi():
    err = rejected(prog(
        [{"name": "a", "type": "boolean", "bool_value": True},
         {"name": "x", "type": "integer", "int_value": 0}],
        [{"id": "t", "kind": "assign", "target": "x", "value": val(iv(1))},
         {"id": "s", "kind": "if", "then_body": ["t"],
          "condition": cond([atom(val(var("a"))), atom(val(var("a")))])}],
        ["s"]))
    assert "toán tử" in err


def test_L2_normalizer_KHONG_bu_toan_tu_thieu():
    with pytest.raises(NormalizeError):
        normalize_inline_program([
            {"id": "s", "kind": "assign", "target": "y",
             "value": {"left": iv(1), "right": iv(2)}}])   # có right mà thiếu op


# ══════════════ không coercion ══════════════

def test_chuoi_khong_thanh_so():
    err = rejected(base(variables=[{"name": "x", "type": "integer", "int_value": "5"},
                                   {"name": "y", "type": "integer"}]))
    assert "số nguyên" in err


def test_true_khong_thanh_1_va_1_khong_thanh_true():
    assert validate_program_config(base(variables=[
        {"name": "x", "type": "integer", "int_value": True},
        {"name": "y", "type": "integer"}]))[0] is None
    assert validate_program_config(base(variables=[
        {"name": "x", "type": "boolean", "bool_value": 1},
        {"name": "y", "type": "integer"}]))[0] is None


def test_gan_sai_kieu_bi_tu_choi():
    err = rejected(prog(
        [{"name": "x", "type": "integer", "int_value": 3},
         {"name": "b", "type": "boolean"}],
        [{"id": "s1", "kind": "assign", "target": "b", "value": val(var("x"))}],
        ["s1"]))
    assert "không tự đổi kiểu" in err


def test_so_sanh_bang_hai_kieu_khac_nhau_bi_tu_choi():
    err = rejected(prog(
        [{"name": "x", "type": "integer", "int_value": 1},
         {"name": "b", "type": "boolean", "bool_value": True},
         {"name": "y", "type": "integer"}],
        [{"id": "t", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "s", "kind": "if", "then_body": ["t"],
          "condition": cond([atom(val(var("x")), "==", val(var("b")))])}],
        ["s"]))
    assert "cùng kiểu" in err


def test_phep_cong_tren_boolean_bi_tu_choi():
    err = rejected(prog(
        [{"name": "b", "type": "boolean", "bool_value": True},
         {"name": "y", "type": "integer"}],
        [{"id": "s1", "kind": "assign", "target": "y", "value": val(var("b"), "+", iv(1))}],
        ["s1"]))
    assert "số nguyên" in err


@pytest.mark.parametrize("kind", ["if", "while"])
def test_dieu_kien_khong_phai_boolean_bi_tu_choi(kind):
    head = {"id": "s", "kind": kind, "condition": cond([atom(val(var("x")))])}
    head.update({"then_body": ["t"]} if kind == "if"
                else {"body": ["t"], "max_iterations": 5})
    err = rejected(prog(
        [{"name": "x", "type": "integer", "int_value": 1},
         {"name": "y", "type": "integer"}],
        [{"id": "t", "kind": "assign", "target": "y", "value": val(iv(1))}, head],
        ["s"]))
    assert "đúng/sai" in err


# ══════════════ while có biên ══════════════

def _while_spec(max_iterations):
    w = {"id": "w", "kind": "while",
         "condition": cond([atom(val(var("x")), "<", val(iv(5)))]), "body": ["b"]}
    if max_iterations is not None:
        w["max_iterations"] = max_iterations
    return prog([{"name": "x", "type": "integer", "int_value": 1}],
                [{"id": "b", "kind": "assign", "target": "x",
                  "value": val(var("x"), "+", iv(1))}, w], ["w"])


def test_while_thieu_bien_bi_tu_choi():
    assert "max_iterations" in rejected(_while_spec(None))


def test_while_vuot_tran_hop_dong_bi_tu_choi():
    err = rejected(_while_spec(LIMITS["max_while_iterations"] + 1))
    assert str(LIMITS["max_while_iterations"]) in err


def test_while_co_bien_hop_le_thi_qua():
    cfg = ok(_while_spec(10))
    assert next(s for s in cfg["statements"] if s["kind"] == "while")["max_iterations"] == 10


# ══════════════ giới hạn một nguồn ══════════════

def test_qua_nhieu_bien():
    n = LIMITS["max_variables"] + 1
    err = rejected(base(variables=[{"name": f"v{i}", "type": "integer", "int_value": 0}
                                   for i in range(n)]))
    assert str(LIMITS["max_variables"]) in err


def test_qua_nhieu_cau_lenh():
    n = LIMITS["max_statement_nodes"] + 1
    err = rejected(base(
        statements=[{"id": f"s{i}", "kind": "assign", "target": "y", "value": val(iv(1))}
                    for i in range(n)],
        main=[f"s{i}" for i in range(n)]))
    assert str(LIMITS["max_statement_nodes"]) in err


def test_long_qua_sau_bi_tu_choi():
    c = cond([atom(val(bv(True)))])
    err = rejected(prog(
        [{"name": "y", "type": "integer"}],
        [{"id": "leaf", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "l3", "kind": "if", "condition": c, "then_body": ["leaf"]},
         {"id": "l2", "kind": "if", "condition": c, "then_body": ["l3"]},
         {"id": "l1", "kind": "if", "condition": c, "then_body": ["l2"]}],
        ["l1"]))
    assert str(LIMITS["max_nesting_depth"]) in err


def test_chia_cho_khong_bi_bat():
    err = rejected(base(statements=[
        {"id": "s1", "kind": "assign", "target": "y", "value": val(var("x"), "//", iv(0))}]))
    assert "chia cho 0" in err


# ══════════════ cấu trúc tham chiếu câu lệnh ══════════════

def test_cau_lenh_thuoc_hai_khoi_bi_tu_choi():
    c = cond([atom(val(bv(True)))])
    err = rejected(prog(
        [{"name": "y", "type": "integer"}],
        [{"id": "leaf", "kind": "assign", "target": "y", "value": val(iv(1))},
         {"id": "a", "kind": "if", "condition": c, "then_body": ["leaf"]},
         {"id": "b", "kind": "if", "condition": c, "then_body": ["leaf"]}],
        ["a", "b"]))
    assert "chỉ thuộc một khối" in err


def test_cau_lenh_mo_coi_bi_tu_choi():
    err = rejected(base(statements=[
        {"id": "s1", "kind": "assign", "target": "y", "value": val(iv(1))},
        {"id": "mo_coi", "kind": "assign", "target": "y", "value": val(iv(2))}]))
    assert "không nằm trong chương trình" in err


# ══════════════ R0 ══════════════

@pytest.mark.parametrize("key", ["trace", "steps", "final_environment", "result", "iterations"])
def test_spec_mang_ket_qua_bi_tu_choi(key):
    err = rejected(base(**{key: [{"x": 3}]}))
    assert "KHÔNG được chứa kết quả" in err


def test_ca_hop_le_tra_config_sach():
    cfg = ok(base())
    assert cfg["program_version"] == SPEC_VERSION
    assert cfg["main"] == ["s1"]
    # biểu thức nội bộ được SINH RA (implementation detail), không do LLM đưa vào
    assert all(e["id"].startswith("_e") for e in cfg["expressions"])
    assert cfg["variables"][0]["initialized"] is True
