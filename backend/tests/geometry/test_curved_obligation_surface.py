# -*- coding: utf-8 -*-
"""NGHĨA VỤ `area` CỦA MẶT CẦU ≡ `lateral_area`. **0 lượt gọi model.**

    `docs/CURVED_OBLIGATION_SURFACE_ALIGNMENT.md`, 2026-09-05.
    Nguồn: `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` §10① — khoảng trống chắn
    trước mọi thứ hai wave trước vừa mở.

Với **khối cầu** — và chỉ khối cầu — hai câu là MỘT:

    "diện tích mặt cầu"        = 4πR²
    "diện tích mặt cong của S" = 4πR²

Vì mặt cầu **không có đáy**: toàn bộ bề mặt chính là mặt cong. Với trụ và nón
thì không — `S_tp = S_xq + S_đáy` — nên `area` và `lateral_area` ở đó vẫn là
hai nghĩa khác nhau, và gộp chúng là nói dối về hình học.

⚠️ Tương đương phải **theo HỌ**, không theo MemoryType: cầu, trụ và nón dùng
chung `curved_solid`, nên quyết định bằng `MemoryType` một mình sẽ kéo cả trụ
lẫn nón vào theo.
"""
from __future__ import annotations

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

VB = {"containers": [], "pointers": [], "value_boxes": []}
DE_CAU = ("Cho khối cầu (S) có bán kính bằng 9. Tính thể tích khối cầu và "
          "diện tích mặt cầu (S).")


def _hd(de, facts, obl):
    return RequestContract(
        problem_text=de, input_facts=facts,
        obligations=tuple(Obligation(**o) for o in obl))


def _spec(decls, stmts):
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Khối cong", "description": "Dựng rồi đo.",
        "pedagogical_intent": "Thấy vô hướng quyết định phép đo.",
        "memory_declarations": decls, "statements": stmts,
        "visual_bindings": VB})


def _khoi_vo_huong(kind, ten="S", r=9, h=None, do=("lateral_area",)):
    """Khối cong khai bằng vô hướng + pose canonical (nền wave trước)."""
    decls = [{"name": "r", "type": "float", "initial_value": r,
              "source_fact_id": "r"}, {"name": ten, "type": "curved_solid"}]
    st = {"kind": "construct_curved_solid", "target_var": ten,
          "curved_kind": kind, "radius": "r"}
    if h is not None:
        decls.append({"name": "h", "type": "float", "initial_value": h,
                      "source_fact_id": "h"})
        st["height"] = "h"
    stmts = [st]
    for q in do:
        w = {"lateral_area": "A", "volume": "V", "radius": "R"}[q]
        decls.append({"name": w, "type": "float"})
        stmts.append({"kind": "assign", "target_var": w,
                      "expr": {"kind": "measure", "quantity": q, "of": ten}})
    return _spec(decls, stmts)


FACT_R = {"fact_id": "r", "label": "bán kính", "values": [9],
          "provenance": "confirmed"}
FACT_H = {"fact_id": "h", "label": "chiều cao", "values": [10],
          "provenance": "confirmed"}


# ══ B · TÁI HIỆN TRƯỚC SỬA ═══════════════════════════════════════════════
def test_B_lech_tu_vung_KHONG_con_chan_o_cong_phu():
    """Bản ghi của lỗi đã sửa — trước wave này ca dưới đây dừng ở
    `structural_coverage` / `requested_operation_uncovered`.

    Dựng · tĩnh · xuất xứ đều QUA; **chỉ** cổng phủ chặn, và chặn vì một lệch
    TỪ VỰNG: `analyze` nói `area` (đúng cách SGK gọi), cổng phủ đòi
    `lateral_area`. Không lượt gọi model nào liên quan.
    """
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "volume", "container": "S", "params": {"witness": "V"}},
              {"kind": "area", "container": "S", "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong("ball",
                                                do=("volume", "lateral_area")))
    assert out.stage_reached != "structural_coverage", (
        "lệch từ vựng đã được sửa — ca này không được chết ở cổng phủ nữa")
    assert out.error_code != "requested_operation_uncovered"


# ══ C · HELPER DẪN TỪ THẨM QUYỀN ═════════════════════════════════════════
@pytest.mark.parametrize("nv,kieu,ho,mong", [
    ("area", "curved_solid", "ball", "lateral_area"),
    ("area", "curved_solid", "cylinder", "area"),
    ("area", "curved_solid", "cone", "area"),
    ("area", "polygon3", None, "area"),
    ("area", "section", None, "area"),
    ("area", "circle3", None, "area"),
    ("volume", "curved_solid", "ball", "volume"),
    ("lateral_area", "curved_solid", "ball", "lateral_area"),
    ("radius", "curved_solid", "ball", "radius"),
])
def test_C_nghia_vu_chinh_tac(nv, kieu, ho, mong):
    from app.simulation.semantic_program.measure_contract import (
        nghia_vu_chinh_tac,
    )

    assert nghia_vu_chinh_tac(nv, kieu, ho) == mong


def test_C_cot_authority_nam_o_KHOI_CONG():
    """Metadata thuộc bảng HỌ, không phải một danh sách song song."""
    from app.simulation.geometry.curved import KHOI_CONG

    assert KHOI_CONG["ball"].nghia_vu_area_la == "lateral_area"
    assert KHOI_CONG["cylinder"].nghia_vu_area_la is None
    assert KHOI_CONG["cone"].nghia_vu_area_la is None


# ══ E1 · `c1a` REPLAY ════════════════════════════════════════════════════
def test_E1_c1a_qua_tron_va_cho_dung_hai_dap_so():
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "volume", "container": "S", "params": {"witness": "V"}},
              {"kind": "area", "container": "S", "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong("ball",
                                                do=("volume", "lateral_area")))
    assert out.executable, getattr(out, "reason", None)
    gt = {k: str(v) for k, v in (out.final_memory or {}).items()}
    assert gt.get("V") == "972π"
    assert gt.get("A") == "324π"
    assert out.stage_reached not in ("structural_coverage", "postconditions")
    assert out.servable is True, getattr(out, "reason", None)


# ══ E2 · CONTROL PHẲNG — nghĩa `area` KHÔNG đổi ══════════════════════════
@pytest.mark.parametrize("kieu", ["polygon3", "section", "circle3"])
def test_E2_area_cua_hinh_phang_giu_nguyen_nghia(kieu):
    from app.simulation.semantic_program.measure_contract import (
        nghia_vu_chinh_tac,
    )

    assert nghia_vu_chinh_tac("area", kieu, None) == "area"
    assert nghia_vu_chinh_tac("area", kieu, "ball") == "area", (
        "kiểu phẳng thì HỌ cong không được có tiếng nói")


# ══ E3 · CONTROL THEO HỌ ═════════════════════════════════════════════════
def test_E3_ball_area_obligation_voi_lateral_witness_QUA():
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "area", "container": "S", "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong("ball"))
    assert out.executable and out.servable, getattr(out, "reason", None)


def test_E3_ball_lateral_area_obligation_QUA():
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "lateral_area", "container": "S",
               "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong("ball"))
    assert out.executable and out.servable, getattr(out, "reason", None)


@pytest.mark.parametrize("kind", ["cylinder", "cone"])
def test_E3_tru_va_non_area_obligation_VAN_bi_chan(kind):
    """`S_tp = S_xq + S_đáy` — gộp là nói dối về hình học."""
    de = f"Cho hình {kind} bán kính đáy 9, chiều cao 10. Tính diện tích."
    hd = _hd(de, [FACT_R, FACT_H],
             [{"kind": "area", "container": "S", "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong(kind, h=10))
    assert not out.executable
    assert out.error_code == "requested_operation_uncovered"


@pytest.mark.parametrize("kind", ["cylinder", "cone"])
def test_E3_tru_va_non_lateral_area_obligation_QUA(kind):
    de = f"Cho hình {kind} bán kính đáy 9, chiều cao 10. Tính diện tích xung quanh."
    hd = _hd(de, [FACT_R, FACT_H],
             [{"kind": "lateral_area", "container": "S",
               "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong(kind, h=10))
    assert out.executable, getattr(out, "reason", None)


# ══ E4 · NHIỀU NGHĨA VỤ — chỉ `area` được quy đổi ═══════════════════════
def test_E4_chi_area_duoc_quy_doi_sibling_giu_nguyen():
    from app.simulation.semantic_program.measure_contract import (
        nghia_vu_chinh_tac,
    )

    assert nghia_vu_chinh_tac("volume", "curved_solid", "ball") == "volume"
    assert nghia_vu_chinh_tac("radius", "curved_solid", "ball") == "radius"
    assert nghia_vu_chinh_tac("area", "curved_solid", "ball") == "lateral_area"


def test_E4_ba_nghia_vu_cung_mot_qua_cau():
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "volume", "container": "S", "params": {"witness": "V"}},
              {"kind": "area", "container": "S", "params": {"witness": "A"}},
              {"kind": "radius", "container": "S", "params": {"witness": "R"}}])
    out = verify_and_compile(
        hd, _khoi_vo_huong("ball", do=("volume", "lateral_area", "radius")))
    assert out.executable, getattr(out, "reason", None)
    gt = {k: str(v) for k, v in (out.final_memory or {}).items()}
    assert (gt.get("V"), gt.get("A"), gt.get("R")) == ("972π", "324π", "9")


# ══ E5/D4 · BINDING ══════════════════════════════════════════════════════
def test_E5_khong_co_producer_thi_van_bi_chan():
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "area", "container": "KHONG_CO",
               "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong("ball"))
    assert not out.executable


def test_E5_sai_MemoryType_thi_van_bi_chan():
    """`area` trên một ĐIỂM vẫn phải chặn — quy đổi không nới kiểu."""
    hd = _hd("Cho điểm A. Tính diện tích.",
             [{"fact_id": "a", "label": "A", "values": ["A"],
               "provenance": "confirmed"}],
             [{"kind": "area", "container": "A", "params": {"witness": "S"}}])
    spec = _spec(
        [{"name": "A", "type": "point3", "initial_value": [0, 0, 0],
          "source_fact_id": "a"}, {"name": "S", "type": "float"}],
        [{"kind": "assign", "target_var": "S",
          "expr": {"kind": "literal", "value": 1}}])
    out = verify_and_compile(hd, spec)
    assert not out.executable


# ══ F · PARITY: COVERAGE ↔ POSTCONDITIONS ═══════════════════════════════
def test_F_hai_consumer_cung_goi_MOT_helper():
    """Quét nguồn: cả hai phải dẫn từ cùng thẩm quyền, không ai chép."""
    import ast

    goc = GOC / "app" / "simulation" / "semantic_program"
    # `postconditions.py` — nơi CHỌN checker — chứ không phải
    # `geometry_obligations.py`, nơi chỉ ĐỊNH NGHĨA checker.
    for ten in ("coverage_gate.py", "postconditions.py"):
        cay = ast.parse((goc / ten).read_text(encoding="utf-8"))
        goi = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        assert "nghia_vu_chinh_tac" in goi, (
            f"{ten} không gọi helper — hai consumer sẽ trôi khỏi nhau")


def test_F_parity_tren_ca_THAT():
    """Coverage nhận ⇒ checker phải chứng thực được, và ngược lại."""
    hd = _hd(DE_CAU, [FACT_R],
             [{"kind": "area", "container": "S", "params": {"witness": "A"}}])
    out = verify_and_compile(hd, _khoi_vo_huong("ball"))
    # qua cổng phủ…
    assert out.stage_reached != "structural_coverage"
    # …và qua luôn hậu điều kiện, tức checker cũng nhận cùng quy đổi.
    assert out.servable is True, getattr(out, "reason", None)


# ══ G · TIÊM LỖI ═════════════════════════════════════════════════════════
def test_G4_quyet_dinh_bang_MemoryType_MOT_MINH_la_SAI():
    """Tiêm ④: bỏ họ đi thì trụ/nón bị kéo theo — đó là toàn bộ rủi ro."""
    from app.simulation.semantic_program.measure_contract import (
        nghia_vu_chinh_tac,
    )

    theo_ho = {h: nghia_vu_chinh_tac("area", "curved_solid", h)
               for h in ("ball", "cylinder", "cone")}
    assert len(set(theo_ho.values())) == 2, (
        f"quy đổi phải PHÂN BIỆT theo họ, đang cho {theo_ho}")


def test_G8_khong_doc_TU_KHOA_trong_de_bai():
    """Tiêm ⑧: nhận diện cầu bằng chữ trong đề là rửa năng lực."""
    import ast

    goc = GOC / "app" / "simulation" / "semantic_program"
    cay = ast.parse((goc / "measure_contract.py").read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == "nghia_vu_chinh_tac":
            ten = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)} | {
                x.attr for x in ast.walk(n) if isinstance(x, ast.Attribute)}
            assert "problem_text" not in ten and "de" not in ten
            return
    pytest.fail("không tìm thấy `nghia_vu_chinh_tac`")


def test_G10_measure_area_KHONG_mo_cho_curved_solid():
    """Tiêm ⑩: tương đương thuộc tầng NGHĨA VỤ, không nới toán hạng IR."""
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert "curved_solid" not in BANG_PHEP_DO["area"].kieu_of
    assert "curved_solid" in BANG_PHEP_DO["lateral_area"].kieu_of
