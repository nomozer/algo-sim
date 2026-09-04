# -*- coding: utf-8 -*-
"""`area` + `lateral_area` — TỪ analyze ĐẾN checker. **0 lượt gọi model.**

    `ANALYZE_OBLIGATION_SURFACE_COMPLETION`, 2026-09-04.

Cả hai đã là **lượng đo** từ Phase 1/Phase 2 nhưng chưa bao giờ là **nghĩa vụ**,
nên `analyze_contract` loại chúng IM LẶNG khỏi `RequestContract` (dòng 489) và
mọi đề hỏi diện tích mất câu hỏi của nó trước khi tới bất kỳ cổng nào.

Đo được ở `CURVED_V3_RESEAL_PREFLIGHT`: pool V3 dùng `area` 8 lượt,
`lateral_area` 6 lượt; **14/18 ca dương** mang ít nhất một nghĩa vụ bị loại, và
**7/9 ô dương** chỉ chứa ca như thế.
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry.curved import Circle3, CurvedSolid
from app.simulation.geometry.exact import Plane3, Vec3
from app.simulation.geometry.radical import display, is_exact_number, radical
from app.simulation.geometry.section import cross_section
from app.simulation.semantic_program.analyze_contract import (
    analyze_schema_for,
    build_request_contract,
)
from app.simulation.semantic_program.geometry_obligations import GEOMETRY_CHECKERS
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    NGHIA_VU_DO,
    kieu_chu_the_nghia_vu,
)
from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    Obligation,
    accepts_container_type,
)
from app.simulation.semantic_program.postconditions import CHECKERS
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

v = Vec3.of
GOC = Path(__file__).resolve().parents[3]
HAI = ("area", "lateral_area")


def box(a, b, c):
    from app.simulation.geometry.section import Polyhedron
    P = [v(0, 0, 0), v(a, 0, 0), v(a, b, 0), v(0, b, 0),
         v(0, 0, c), v(a, 0, c), v(a, b, c), v(0, b, c)]
    return Polyhedron(tuple(P), ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
                                (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)))


# ══ D1 · AUTHORITY VÀ LƯỢC ĐỒ ═════════════════════════════════════════════
@pytest.mark.parametrize("q", HAI)
def test_D1a_la_nghia_vu_va_co_checker(q):
    assert q in BANG_PHEP_DO, "phải vẫn là một lượng đo"
    assert q in NGHIA_VU_DO, "phải là một nghĩa vụ"
    assert q in OBLIGATION_KINDS
    assert q in GEOMETRY_CHECKERS, "nghĩa vụ KHÔNG checker ⇒ mãi mức yếu"
    assert q in CHECKERS, "`CHECKERS` dẫn từ `GEOMETRY_CHECKERS`, không bảng hai"


@pytest.mark.parametrize("q", HAI)
def test_D1b_kieu_chu_the_DAN_XUAT_tu_bang_phep_do(q):
    """Không danh sách kiểu nào chép tay — mở lượng đo cho kiểu mới là nghĩa vụ
    tự nhận kiểu ấy."""
    assert kieu_chu_the_nghia_vu(q) == frozenset(BANG_PHEP_DO[q].kieu_of)
    assert OBLIGATION_KINDS[q] == kieu_chu_the_nghia_vu(q)


def test_D1c_KHONG_co_ban_sao_viet_tay_cua_danh_sach_nghia_vu_do():
    """Quét mã sản phẩm: không nơi nào liệt kê tay tập nghĩa vụ ĐO."""
    import ast

    goc = GOC / "backend" / "app"
    xau = []
    for f in goc.rglob("*.py"):
        if f.name == "measure_contract.py":
            continue  # THẨM QUYỀN — chỗ duy nhất được liệt kê
        cay = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, (ast.Set, ast.List, ast.Tuple)):
                gt = {x.value for x in n.elts
                      if isinstance(x, ast.Constant) and isinstance(x.value, str)}
                if set(NGHIA_VU_DO) <= gt:
                    xau.append(f"{f.relative_to(goc)}:{n.lineno}")
    assert xau == [], f"bản sao danh sách nghĩa vụ đo: {xau}"


@pytest.mark.parametrize("q", HAI)
def test_D1d_enum_lược_do_analyze_chua_kind_moi(q):
    sc = json.dumps(analyze_schema_for("hinh_hoc"), ensure_ascii=False)
    assert f'"{q}"' in sc


@pytest.mark.parametrize("q", HAI)
def test_D1e_analyze_KHONG_con_loai_im_lang(q):
    hd = build_request_contract(
        {"problem_text": "x",
         "input_facts": [{"id": "f", "kind": "int", "label": "l", "values": [3]}],
         "obligations": [{"kind": q, "container": "K", "witness": "S"}]},
        "Cho hình. Tính diện tích.", "hinh_hoc")
    assert [o.kind for o in hd.obligations] == [q]
    assert hd.obligations[0].container == "K"
    assert hd.obligations[0].witness == "S"


@pytest.mark.parametrize("q", HAI)
def test_D1f_round_trip_giu_nguyen_container_witness_quantity(q):
    hd = RequestContract(
        problem_text="x", input_facts=(),
        obligations=(Obligation(kind=q, container="K", params={"witness": "S"}),))
    lai = RequestContract.model_validate(json.loads(hd.model_dump_json()))
    assert lai.obligations[0].kind == q
    assert lai.obligations[0].container == "K"
    assert lai.obligations[0].witness == "S"


def test_D1g_kind_LA_van_bi_loai_fail_closed():
    hd = build_request_contract(
        {"problem_text": "x", "input_facts": [],
         "obligations": [{"kind": "khong_ton_tai", "container": "K",
                          "witness": "S"}]},
        "x", "hinh_hoc")
    assert hd.obligations == ()


# ══ D2 · CHECKER CHÍNH XÁC ════════════════════════════════════════════════
#: Kỳ vọng dựng ĐỘC LẬP với đường thực thi — công thức SGK gõ thẳng.
MAU_AREA = [
    # tam giác vuông 4×3 ⇒ S = 6
    ((v(0, 0, 0), v(4, 0, 0), v(4, 3, 0)), F(6)),
    # vuông 2×2 ⇒ S = 4
    ((v(0, 0, 0), v(2, 0, 0), v(2, 2, 0), v(0, 2, 0)), F(4)),
    # đường tròn r² = 16 ⇒ S = 16π
    (Circle3(v(0, 0, 0), v(0, 0, 1), F(16)), radical(16, 1, 1)),
]
MAU_LATERAL = [
    (CurvedSolid("ball", v(0, 0, 0), None, v(6, 0, 0)), radical(144, 1, 1)),
    (CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 5), v(3, 0, 0)),
     radical(30, 1, 1)),
    (CurvedSolid("cone", v(0, 0, 0), v(0, 0, 4), v(3, 0, 0)), radical(15, 1, 1)),
]


def _chay(kind, chu_the, khai):
    ob = Obligation(kind=kind, container="X", params={"witness": "w"})
    return GEOMETRY_CHECKERS[kind]({"X": chu_the, "w": khai}, ob)


@pytest.mark.parametrize("x,mong", MAU_AREA)
def test_D2a_area_dung_thi_verified(x, mong):
    assert _chay("area", x, mong) is None


@pytest.mark.parametrize("x,mong", MAU_LATERAL)
def test_D2b_lateral_area_dung_thi_verified(x, mong):
    assert _chay("lateral_area", x, mong) is None


@pytest.mark.parametrize("kind,mau", [("area", MAU_AREA),
                                      ("lateral_area", MAU_LATERAL)])
def test_D2c_gia_tri_SAI_bi_bac(kind, mau):
    for x, _ in mau:
        loi = _chay(kind, x, F(104729))
        assert loi and "giá trị không khớp" in loi


@pytest.mark.parametrize("kind,xau", [
    ("area", CurvedSolid("ball", v(0, 0, 0), None, v(1, 0, 0))),
    ("lateral_area", Circle3(v(0, 0, 0), v(0, 0, 1), F(4))),
])
def test_D2d_sai_KIEU_chu_the_bao_dung_benh(kind, xau):
    loi = _chay(kind, xau, F(1))
    assert loi and "cần" in loi
    assert "giá trị không khớp" not in loi, "sai kiểu ≠ sai số"


@pytest.mark.parametrize("kind,mau", [("area", MAU_AREA),
                                      ("lateral_area", MAU_LATERAL)])
def test_D2e_thieu_witness_thi_MUC_YEU_khong_phai_vi_pham(kind, mau):
    x = mau[0][0]
    ob = Obligation(kind=kind, container="X", params={})
    assert GEOMETRY_CHECKERS[kind]({"X": x}, ob) is None


def test_D2f_area_nhan_section_dung_dien_tich_thiet_dien():
    sec = cross_section(box(2, 2, 2), Plane3(v(0, 0, 1), v(0, 0, 1)))
    assert accepts_container_type("area", "section")
    assert _chay("area", sec, F(4)) is None
    assert _chay("area", sec, F(5)) is not None


def test_D2g_checker_TINH_LAI_tu_hinh_khong_tin_witness():
    """Đổi hình thì phán quyết phải đổi theo — nếu không, checker chỉ đang so
    witness với chính nó."""
    a = CurvedSolid("ball", v(0, 0, 0), None, v(6, 0, 0))
    b = CurvedSolid("ball", v(0, 0, 0), None, v(1, 0, 0))
    assert _chay("lateral_area", a, radical(144, 1, 1)) is None
    assert _chay("lateral_area", b, radical(144, 1, 1)) is not None


# ══ D3 · END-TO-END ═══════════════════════════════════════════════════════
def _ct(obs, facts=None):
    return RequestContract(
        problem_text="Cho hình nón đáy tâm O bán kính 3, chiều cao 4.",
        input_facts=tuple(facts or [
            {"fact_id": "f", "label": "hình nón", "values": ["O"],
             "provenance": "confirmed"}]),
        obligations=tuple(obs))


NON = {
    "title": "Hình nón — mặt xung quanh và đáy",
    "memory_declarations": [
        {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": "f"},
        {"name": "S", "type": "point3", "initial_value": [0, 0, 4],
         "source_fact_id": "f"},
        {"name": "A", "type": "point3", "initial_value": [3, 0, 0],
         "source_fact_id": "f"},
        {"name": "non", "type": "curved_solid"},
        {"name": "Sxq", "type": "float"},
    ],
    "statements": [
        {"kind": "construct_curved_solid", "target_var": "non",
         "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
         "rim_point": "A"},
        {"kind": "assign", "target_var": "Sxq",
         "expr": {"kind": "measure", "quantity": "lateral_area", "of": "non"}},
    ],
}


def test_D3a_lateral_area_di_tron_tuyen_toi_served():
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    oc = verify_and_compile(
        _ct([Obligation(kind="lateral_area", container="non",
                        params={"witness": "Sxq"})]),
        SemanticProgramSpec.model_validate(NON))
    assert oc.servable, oc.details
    assert oc.stage_reached == "served"
    dl = {k: display(x) for k, x in (oc.final_memory or {}).items()
          if is_exact_number(x)}
    assert dl["Sxq"] == "15π"          # πrl = π·3·5
    assert oc.constraints_verified == ["lateral_area(non)"]


def test_D3b_area_tren_vat_DUNG_bang_construct_star():
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    raw = {
        "title": "Đa giác đáy",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": xy,
             "source_fact_id": "f"}
            for n, xy in (("A", [0, 0, 0]), ("B", [4, 0, 0]), ("C", [4, 3, 0]))
        ] + [{"name": "T", "type": "polygon3"}, {"name": "S", "type": "float"}],
        "statements": [
            {"kind": "construct_polygon", "target_var": "T",
             "vertices": ["A", "B", "C"]},
            {"kind": "assign", "target_var": "S",
             "expr": {"kind": "measure", "quantity": "area", "of": "T"}},
        ],
    }
    oc = verify_and_compile(
        _ct([Obligation(kind="area", container="T", params={"witness": "S"})]),
        SemanticProgramSpec.model_validate(raw))
    assert oc.servable, oc.details
    assert {k: display(x) for k, x in oc.final_memory.items()
            if is_exact_number(x)}["S"] == "6"


def test_D3c_HAI_nghia_vu_tren_HAI_vat__rebind_khong_de_len_nhau():
    """Chứng minh cơ chế rebind theo TỪNG nghĩa vụ của
    `OBLIGATION_BINDING_CONTRACT` không bị hai nghĩa vụ ghi đè lẫn nhau."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    raw = json.loads(json.dumps(NON))
    raw["memory_declarations"] += [{"name": "V", "type": "float"}]
    raw["statements"] += [
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "non"}}]
    oc = verify_and_compile(
        _ct([Obligation(kind="lateral_area", container="non",
                        params={"witness": "Sxq"}),
             Obligation(kind="volume", container="non",
                        params={"witness": "V"})]),
        SemanticProgramSpec.model_validate(raw))
    assert oc.servable, oc.details
    assert sorted(oc.constraints_verified) == ["lateral_area(non)", "volume(non)"]
    dl = {k: display(x) for k, x in oc.final_memory.items() if is_exact_number(x)}
    assert (dl["Sxq"], dl["V"]) == ("15π", "12π")


def test_D3d_container_CAN_REBIND_van_noi_dung():
    """Hợp đồng gọi tên một vật SAI KIỂU; net ⓪ nối qua witness."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.coverage_gate import (
        check_structural_coverage)

    raw = json.loads(json.dumps(NON))
    raw["memory_declarations"] += [{"name": "day", "type": "point3",
                                    "initial_value": [0, 0, 0],
                                    "source_fact_id": "f"}]
    ct = _ct([Obligation(kind="lateral_area", container="day",
                         params={"witness": "Sxq"})])
    spec = SemanticProgramSpec.model_validate(raw)
    kq = check_structural_coverage(ct, spec)
    assert kq.ok, kq.missing
    assert kq.ten_da_hoa_giai == {"day": "non"}


# ══ D4 · TIÊM LỖI ═════════════════════════════════════════════════════════
@pytest.mark.parametrize("q", HAI)
def test_D4a_go_khoi_authority_thi_analyze_loai_lai(q, monkeypatch):
    from app.simulation.semantic_program import obligations as OB

    monkeypatch.delitem(OB.OBLIGATION_KINDS, q)
    hd = build_request_contract(
        {"problem_text": "x", "input_facts": [],
         "obligations": [{"kind": q, "container": "K", "witness": "S"}]},
        "x", "hinh_hoc")
    assert hd.obligations == (), "gỡ authority mà analyze vẫn giữ ⇒ test vô nghĩa"


@pytest.mark.parametrize("q", HAI)
def test_D4b_go_checker_thi_nghia_vu_roi_xuong_MUC_YEU(q, monkeypatch):
    from app.simulation.semantic_program import postconditions as PC
    from app.simulation.semantic_program.obligations import has_server_owned_checker

    monkeypatch.delitem(PC.CHECKERS, q)
    assert not has_server_owned_checker(q) or q not in PC.CHECKERS


def test_D4c_checker_nhan_SAI_MemoryType_thi_test_kieu_do():
    """R0/an toàn kiểu: chủ thể sai kiểu KHÔNG được lọt thành 'đã xác nhận'."""
    assert _chay("lateral_area", box(1, 1, 1), F(1)) is not None
    assert _chay("area", CurvedSolid("ball", v(0, 0, 0), None, v(1, 0, 0)),
                 F(1)) is not None
