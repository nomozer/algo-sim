# -*- coding: utf-8 -*-
"""regular-hexagonal-pyramid (G05) — chóp lục giác đều qua đúng route sản phẩm (amendment §26, khuôn T11). 0 lượt gọi.

Nhãn ghi trước: `docs/evaluation/geometry/runs/regular-hexagonal-pyramid/labels.json` (oracle `oracle.py`, từ kích thước
đề) + lớp đính chính `label_corrections.json`. Chương trình kiểu mô hình: đáy lục giác đều trong KHUNG AFFINE (cơ sở 60°),
metric dẫn xuất từ đề (`do_luong_cua`), như T8.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from fractions import Fraction

import pytest

from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.assumption_gate import do_luong_cua
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.shape_constraint import che_muc_tieu, doc_rang_buoc, phan_chua_doc

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/regular-hexagonal-pyramid"
sys.path.insert(0, str(RUN / "diagnostics"))
from cases import LABELS, hop_dong_va_chuong_trinh  # noqa: E402

SUA = json.loads((RUN / "label_corrections.json").read_text(encoding="utf-8"))["rows"]
MONG = {k: SUA[k]["now"] if k in SUA else r["expect"] for k, r in LABELS.items()}


def test_oracle_doc_lap():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


@pytest.mark.parametrize("rid", sorted(LABELS))
def test_route_theo_nhan(rid):
    contract, sp = hop_dong_va_chuong_trinh(rid)
    out = verify_and_compile(contract, sp)
    loai, _, gia_tri = MONG[rid].partition(":")
    if loai == "refused":
        assert not out.servable, (out.stage_reached, out.details)
        return
    assert out.servable and out.assumption_certificate == "C1", (out.stage_reached, out.reason_code, out.details)
    canh = _dung_scene3d(sp, contract)
    w = "V" if LABELS[rid]["ask"] == "volume" else "d_SA"
    assert next(o["value"] for o in canh["objects"] if o["id"] == w) == gia_tri
    # Scene3D: khối 7 đỉnh, 7 mặt; metric khung cho renderer (toạ độ cảnh là toạ độ khung, chính xác)
    assert "chart_metric" in canh
    khoi = next(o for o in canh["objects"] if o["id"] == "khoi")
    assert len(khoi["vertex_ids"]) == 7


def test_metric_dan_xuat_tu_de_khong_tu_bo_cuc():
    """Cùng đề, hai bố cục affine khác nhau (tịnh tiến) ⇒ cùng đáp số; đề thiếu chiều cao ⇒ không metric."""
    c, sp = hop_dong_va_chuong_trinh("H1_side_height")
    assert do_luong_cua(LABELS["H1_side_height"]["text"], sp) is not None
    c2, sp2 = hop_dong_va_chuong_trinh("N1_missing_height")
    assert do_luong_cua(LABELS["N1_missing_height"]["text"], sp2) is None


@pytest.mark.parametrize("rid", sorted(LABELS))
def test_bo_doc(rid):
    de = che_muc_tieu(LABELS[rid]["text"])
    rb = doc_rang_buoc(de)
    co = any(r.kind == "regular_hexagonal_pyramid" for r in rb)
    luc_giac = LABELS[rid]["text_claims_regular"] and len(LABELS[rid]["names"]) == 7   # ngũ giác đều: ngoài miền
    assert co == luc_giac, [(r.kind, r.entities) for r in rb]
    if co:
        assert not phan_chua_doc(de)                       # "lục giác đều", cạnh đáy… đều được đọc


_LUC_GIAC_HUU_TI = {"A": [1, -1, 0], "B": [1, 0, -1], "C": [0, 1, -1], "D": [-1, 1, 0], "E": [-1, 0, 1], "F": [0, -1, 1]}


@pytest.mark.parametrize("S, mong", [([1, 1, 1], "served:3"), ([2, 1, 0], "refused")], ids=["nhat_quan", "dinh_lech"])
def test_c0_luc_giac_deu_huu_ti(S, mong):
    """Lục giác đều CÓ toạ độ hữu tỉ (mặt x + y + z = 0, cạnh √2); đỉnh trên trục (1,1,1) cao √3 ⇒ V = (√3/2)·2·√3 = 3."""
    sys.path.insert(0, str(RUN.parent / "c0-whole-solid-grounding" / "diagnostics"))
    import c0_whole_solid_cases as M
    M.LABELS["_hex"] = {"text": "Cho hình chóp lục giác đều S.ABCDEF với {coords}. Tính thể tích khối chóp S.ABCDEF.",
                        "points": {**_LUC_GIAC_HUU_TI, "S": S},
                        "solid": {"kind": "pyramid", "apex": "S", "base": list("ABCDEF")}}
    _de, c, sp = M.hop_dong_va_chuong_trinh("_hex")
    out = verify_and_compile(c, sp)
    if mong == "refused":
        assert (out.servable, out.reason_code) == (False, "SOURCE_SHAPE_CONTRADICTS_COORDINATES")
        return
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    assert out.servable and out.assumption_certificate == "C0"
    assert Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"])) == 3
