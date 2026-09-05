# -*- coding: utf-8 -*-
"""NGHĨA VỤ CÓ WITNESS ĐƯỢC KIỂM QUA CHÍNH CÂU LỆNH SINH RA NÓ. 0 lượt gọi.

    `docs/CURVED_DISTANCE_WITNESS_VERIFICATION.md`, 2026-09-05.
    Fixture `c7a` — POST_V3_DEVELOPMENT_FIXTURE (V3 đã tiêu; đây là replay
    tất định trên dữ liệu đã công bố, KHÔNG phải một lượt acceptance mới).

`c7a` khai `distance(container="hinh_non", witness="l")` để nói *"đường sinh"*.
Nhưng `distance` là phép đo **quan hệ** — giữa hai đối tượng — nên checker cũ
thử đo trên chính `hinh_non: curved_solid` và trả *"cặp đối tượng không hợp
lệ"*. Chương trình đúng trọn vẹn (`l=13 · V=100π · Sxq=65π`) bị bác.

Phép đo THẬT nằm ở câu lệnh sinh witness: `l = measure(distance, of=T, wrt=A)`.
`T` và `A` là toán hạng dựng của chính `hinh_non`, nên liên kết chứng minh được
bằng **dữ liệu có cấu trúc** — không bằng tên biến, không bằng chữ trong đề.

⚠️ `distance` GIỮ nghĩa quan hệ. Checker tính lại từ `T` và `A`; `l` chỉ là
witness liên kết, không phải bằng chứng tự xác nhận.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

V3 = GOC.parent / "docs" / "evaluation" / "geometry" / "curved-acceptance-v3"
VB = {"containers": [], "pointers": [], "value_boxes": []}


@pytest.fixture(scope="module")
def c7a():
    """POST_V3_DEVELOPMENT_FIXTURE — hợp đồng + chương trình nguyên văn."""
    d = json.loads((V3 / "curved_acceptance.json").read_text(encoding="utf-8"))
    return {r["id"]: r for r in d["cuoi"]}["c7a"]


def _chay(ca):
    rc = ca["request_contract"]
    c = RequestContract(
        problem_text=rc["problem_text"], input_facts=rc["input_facts"],
        obligations=tuple(Obligation(**o) for o in rc["obligations"]))
    s = SemanticProgramSpec.model_validate(ca["chuong_trinh"])
    return c, s, verify_and_compile(c, s)


def _gt(out):
    return {k: str(v) for k, v in (out.final_memory or {}).items()}


# ══ 2 · TÁI HIỆN ═════════════════════════════════════════════════════════
def test_R1_c7a_dung_tron_ba_dap_so(c7a):
    _c, _s, out = _chay(c7a)
    assert out.executable
    g = _gt(out)
    assert (g["l"], g["V"], g["Sxq"]) == ("13", "100π", "65π")


def test_R2_lien_ket_chung_minh_duoc_bang_DU_LIEU_CAU_TRUC(c7a):
    """`T`, `A` là toán hạng DỰNG của `hinh_non` — không cần đọc chữ nào."""
    from app.simulation.semantic_program.coverage_gate import _phu_thuoc

    _c, spec, _o = _chay(c7a)
    pt = _phu_thuoc(spec.statements, frozenset())
    assert {"T", "A"} <= pt["hinh_non"], pt.get("hinh_non")


# ══ 3 · RESOLVER ═════════════════════════════════════════════════════════
def test_C1_resolver_tra_du_cau_truc(c7a):
    from app.simulation.semantic_program.coverage_gate import phan_giai_witness

    c, spec, _o = _chay(c7a)
    ob = next(o for o in c.obligations if o.kind == "distance")
    r = phan_giai_witness(spec, ob, {m.name: m.type
                                     for m in spec.memory_declarations})
    assert r.witness_target == "l"
    assert r.quantity == "distance"
    assert r.operands == {"of": "T", "wrt": "A"}
    assert r.operand_types == {"of": "point3", "wrt": "point3"}
    assert r.binding_evidence is not None
    assert r.diagnostic_status == "OK"
    assert r.producer_statement is not None


def test_C2_resolver_dan_tu_CHU_KY_khong_chep_tay():
    """Toán hạng bắt buộc đọc từ `BANG_PHEP_DO`, không từ một bảng thứ hai."""
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert BANG_PHEP_DO["distance"].hai_toan_hang is True
    assert BANG_PHEP_DO["volume"].hai_toan_hang is False
    assert BANG_PHEP_DO["lateral_area"].hai_toan_hang is False


# ══ 5 · POSITIVE ═════════════════════════════════════════════════════════
def test_P1_c7a_qua_TRON_va_servable(c7a):
    _c, _s, out = _chay(c7a)
    assert out.stage_reached != "postconditions", getattr(out, "details", None)
    assert out.servable is True, getattr(out, "details", None)
    g = _gt(out)
    assert (g["l"], g["V"], g["Sxq"]) == ("13", "100π", "65π")


def test_P2_ten_witness_TRUNG_TINH_van_phan_giai_duoc():
    """Không được phụ thuộc tên `l`."""
    de = "Cho hai điểm P(0;0;0) và Q(3;4;0). Tính khoảng cách PQ."
    c = RequestContract(
        problem_text=de,
        input_facts=[{"fact_id": "p", "label": "P", "values": ["P"],
                      "provenance": "confirmed"},
                     {"fact_id": "q", "label": "Q", "values": ["Q"],
                      "provenance": "confirmed"}],
        obligations=(Obligation(kind="distance", container="P",
                                params={"witness": "zzz", "wrt": "Q"}),))
    s = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Khoảng cách hai điểm",
        "description": "Đo khoảng cách.", "pedagogical_intent": "Thấy độ dài.",
        "memory_declarations": [
            {"name": "P", "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "p"},
            {"name": "Q", "type": "point3", "initial_value": [3, 4, 0],
             "source_fact_id": "q"},
            {"name": "zzz", "type": "float"}],
        "statements": [
            {"kind": "assign", "target_var": "zzz",
             "expr": {"kind": "measure", "quantity": "distance", "of": "P",
                      "wrt": "Q"}}],
        "visual_bindings": VB})
    out = verify_and_compile(c, s)
    assert out.executable and out.servable, getattr(out, "details", None)
    assert _gt(out)["zzz"] == "5"


def test_P3_phep_do_DA_TOAN_HANG_thu_hai_cung_phan_giai_duoc(c7a):
    """`angle` cũng có `wrt` — resolver phải tổng quát, không riêng distance."""
    from app.simulation.semantic_program.coverage_gate import phan_giai_witness
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert any(p.hai_toan_hang for q, p in BANG_PHEP_DO.items() if q != "distance")
    c, spec, _o = _chay(c7a)
    ob = next(o for o in c.obligations if o.kind == "volume")
    r = phan_giai_witness(spec, ob, {m.name: m.type
                                     for m in spec.memory_declarations})
    assert r.quantity == "volume"
    assert r.operands == {"of": "hinh_non"}, "phép đo MỘT toán hạng"


def test_P6_sibling_giu_binding_rieng(c7a):
    _c, _s, out = _chay(c7a)
    g = _gt(out)
    assert g["V"] == "100π" and g["Sxq"] == "65π"
    assert out.servable is True


def test_P7_coverage_va_postconditions_cung_MOT_resolver():
    for ten in ("coverage_gate.py", "postconditions.py"):
        cay = ast.parse((GOC / "app" / "simulation" / "semantic_program"
                         / ten).read_text(encoding="utf-8"))
        goi = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        assert "phan_giai_witness" in goi, ten


# ══ 5 · HỒI QUY ĐƯỜNG UNARY ══════════════════════════════════════════════
def test_P5_c1a_volume_va_area_van_served():
    c = RequestContract(
        problem_text="Cho khối cầu (S) có bán kính bằng 9. Tính thể tích và "
                     "diện tích mặt cầu (S).",
        input_facts=[{"fact_id": "r", "label": "bán kính", "values": [9],
                      "provenance": "confirmed"}],
        obligations=(Obligation(kind="volume", container="S",
                                params={"witness": "V"}),
                     Obligation(kind="area", container="S",
                                params={"witness": "A"})))
    s = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Khối cầu", "description": "Dựng rồi đo.",
        "pedagogical_intent": "Thấy bán kính quyết định.",
        "memory_declarations": [
            {"name": "r", "type": "float", "initial_value": 9,
             "source_fact_id": "r"},
            {"name": "S", "type": "curved_solid"},
            {"name": "V", "type": "float"}, {"name": "A", "type": "float"}],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "S",
             "curved_kind": "ball", "radius": "r"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "S"}},
            {"kind": "assign", "target_var": "A",
             "expr": {"kind": "measure", "quantity": "lateral_area", "of": "S"}}],
        "visual_bindings": VB})
    out = verify_and_compile(c, s)
    assert out.executable and out.servable, getattr(out, "details", None)
    g = _gt(out)
    assert (g["V"], g["A"]) == ("972π", "324π")


# ══ 5 · FAIL-CLOSED ══════════════════════════════════════════════════════
def _sua_c7a(ca, *, obligations=None, statements=None, decls=None):
    rc = dict(ca["request_contract"])
    ct = json.loads(json.dumps(ca["chuong_trinh"], ensure_ascii=False))
    if obligations is not None:
        rc["obligations"] = obligations
    if statements is not None:
        ct["statements"] = statements
    if decls is not None:
        ct["memory_declarations"] = decls
    c = RequestContract(problem_text=rc["problem_text"],
                        input_facts=rc["input_facts"],
                        obligations=tuple(Obligation(**o)
                                          for o in rc["obligations"]))
    return c, SemanticProgramSpec.model_validate(ct)


def test_F1_witness_khong_ton_tai(c7a):
    ob = [dict(o) for o in c7a["request_contract"]["obligations"]]
    ob[0] = dict(ob[0], params={"witness": "KHONG_CO"})
    c, s = _sua_c7a(c7a, obligations=ob)
    out = verify_and_compile(c, s)
    assert not out.servable


def test_F3_producer_khong_phai_measure(c7a):
    st = json.loads(json.dumps(c7a["chuong_trinh"]["statements"],
                               ensure_ascii=False))
    st[1] = {"kind": "assign", "target_var": "l",
             "expr": {"kind": "literal", "value": 13}}
    c, s = _sua_c7a(c7a, statements=st)
    out = verify_and_compile(c, s)
    assert not out.servable, "khai thẳng 13 KHÔNG được coi là đã chứng thực"


def test_F4_quantity_cua_producer_khac_nghia_vu(c7a):
    st = json.loads(json.dumps(c7a["chuong_trinh"]["statements"],
                               ensure_ascii=False))
    st[1]["expr"]["quantity"] = "volume"
    st[1]["expr"]["of"] = "hinh_non"
    st[1]["expr"].pop("wrt", None)
    c, s = _sua_c7a(c7a, statements=st)
    out = verify_and_compile(c, s)
    assert not out.servable


def test_F5_thieu_wrt(c7a):
    st = json.loads(json.dumps(c7a["chuong_trinh"]["statements"],
                               ensure_ascii=False))
    st[1]["expr"]["wrt"] = None
    c, s = _sua_c7a(c7a, statements=st)
    out = verify_and_compile(c, s)
    assert not out.servable


def test_F8_witness_KHONG_gan_voi_container(c7a):
    """Phản ví dụ: đo giữa hai điểm KHÔNG thuộc khối ⇒ phải bác.

    Nếu chấp nhận mọi distance witness thì một chương trình đo khoảng cách
    giữa hai điểm bất kỳ cũng "chứng thực" được đường sinh của nón — đó là
    thứ làm phép kiểm mất giá trị.
    """
    ct = json.loads(json.dumps(c7a["chuong_trinh"], ensure_ascii=False))
    ct["memory_declarations"] += [
        {"name": "X", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": ct["memory_declarations"][0].get("source_fact_id")},
        {"name": "Y", "type": "point3", "initial_value": [13, 0, 0],
         "source_fact_id": ct["memory_declarations"][0].get("source_fact_id")}]
    ct["statements"][1]["expr"] = {"kind": "measure", "quantity": "distance",
                                   "of": "X", "wrt": "Y"}
    c, s = _sua_c7a(c7a, statements=ct["statements"],
                    decls=ct["memory_declarations"])
    out = verify_and_compile(c, s)
    assert not out.servable, (
        "đo giữa hai điểm rời khối mà vẫn chứng thực được đường sinh ⇒ "
        "phép kiểm vô giá trị")


# ══ 5 · SOURCE GUARD ═════════════════════════════════════════════════════
def _nguon(ten):
    return (GOC / "app" / "simulation" / "semantic_program" / ten).read_text(
        encoding="utf-8")


def test_S1_khong_so_sanh_literal_voi_ten_l():
    for ten in ("coverage_gate.py", "postconditions.py",
                "geometry_obligations.py"):
        assert '== "l"' not in _nguon(ten) and "== 'l'" not in _nguon(ten), ten


def test_S2_khong_co_nhanh_rieng_cho_cone():
    for ten in ("coverage_gate.py", "postconditions.py",
                "geometry_obligations.py"):
        s = _nguon(ten)
        assert '"cone"' not in s and "'cone'" not in s, ten


def test_S3_khong_chep_tay_chu_ky_measure():
    """Toán hạng bắt buộc phải DẪN từ `BANG_PHEP_DO`, không liệt kê lại."""
    cay = ast.parse(_nguon("coverage_gate.py"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == "phan_giai_witness":
            ten = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)} | {
                x.attr for x in ast.walk(n) if isinstance(x, ast.Attribute)}
            assert "BANG_PHEP_DO" in ten or "hai_toan_hang" in ten
            return
    pytest.fail("không tìm thấy `phan_giai_witness`")
