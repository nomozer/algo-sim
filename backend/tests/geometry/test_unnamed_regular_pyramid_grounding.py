# -*- coding: utf-8 -*-
"""unnamed-regular-pyramid-grounding — chóp đều KHÔNG TÊN (§24): bộ đọc phát khẳng định `()` (không đoán tên); cổng gắn
nó vào khối duy nhất của chương trình CHỈ KHI đề không gọi tên điểm nào thiếu toạ độ, rồi KIỂM như ký hiệu chuẩn.

Nhãn ghi trước: `docs/evaluation/geometry/runs/unnamed-regular-pyramid-grounding/labels.json` (47 hàng C1 của hai corpus
chóp đều + hàng C0; oracle `oracle.py` dẫn xuất lại đáp số từ kích thước đề). 0 lượt gọi model.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import re
import subprocess
import sys
from fractions import Fraction

import pytest

from app.ai import pipeline as PL
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.shape_constraint import doc_rang_buoc, neu_khoi_da_dien, ten_diem_khong_toa_do
from tests.geometry import test_regular_square_pyramid as SQ
from tests.geometry import test_regular_triangular_pyramid as TR

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/unnamed-regular-pyramid-grounding"
sys.path.insert(0, str(RUN.parent / "c0-whole-solid-grounding" / "diagnostics"))
import c0_whole_solid_cases as M  # noqa: E402

NHAN = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))
C1, C0 = NHAN["c1_rows"], NHAN["c0_rows"]
MOD = {"square": SQ, "triangular": TR}
MA = "SOURCE_SHAPE_CONTRADICTS_COORDINATES"
DEU = {"regular_square_pyramid", "regular_triangular_pyramid"}


def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


# ══ C1 — 47 đề không tên ════════════════════════════════════════════════════
def _ket_cuc(rid: str, monkeypatch) -> str:
    corpus, ca = rid.split("/")
    mod = MOD[corpus]
    monkeypatch.setitem(mod.NHAN, ca, {**mod.NHAN[ca], "text": C1[rid]["text"]})
    k = mod.ket_qua(ca)
    return f"served:{k['served']}" if "served" in k else f"refused:{k['stage']}:{k['reason_code']}"


def _khop(nhan: str, ket: str) -> bool:
    if nhan.startswith("served:"):
        return ket == nhan
    _t, st, ma = nhan.split(":")
    _k, kst, kma = ket.split(":") if ket.startswith("refused") else ("", "", "")
    return ket.startswith("refused") and st in ("*", kst) and ma in ("*", kma)


@pytest.mark.parametrize("rid", sorted(C1))
def test_c1_khong_ten_theo_nhan(rid, monkeypatch):
    r = C1[rid]
    ket = _ket_cuc(rid, monkeypatch)
    if r["scope"] == "bind":
        assert _khop(r["expect"], ket), (r["class"], r["expect"], ket)
    else:                                      # tên điểm thiếu toạ độ: không gắn, giữ như main
        assert ket == r["baseline_ede8d329"], (r["class"], r["baseline_ede8d329"], ket)


def test_c1_dem_theo_lop():
    lop = {}
    for r in C1.values():
        lop.setdefault((r["scope"], r["class"]), 0)
        lop[(r["scope"], r["class"])] += 1
    assert lop == {("bind", "correct"): 13, ("bind", "wrong_value"): 4, ("bind", "served_label_refused"): 8,
                   ("bind", "refused"): 1, ("unchanged", "correct"): 9, ("unchanged", "served_label_refused"): 3,
                   ("unchanged", "refused"): 9}


# ══ C0 — toạ độ đề cho ═══════════════════════════════════════════════════════
@pytest.mark.parametrize("rid", sorted(C0))
def test_c0_khong_ten_theo_nhan(rid):
    M.LABELS[rid] = C0[rid]
    de, contract, sp = M.hop_dong_va_chuong_trinh(rid)
    out = verify_and_compile(contract, sp)
    loai, _, gia_tri = C0[rid]["expect"].partition(":")
    if loai == "served":
        assert out.servable and out.assumption_certificate == "C0", (out.stage_reached, out.reason_code, out.details)
        assert Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"])) == Fraction(gia_tri)
    elif loai == "refused":
        assert (out.servable, out.stage_reached, out.reason_code) == (False, "assumption", MA), out.details
        assert any(d.startswith("C0_SHAPE_CONTRADICTION regular_") for d in out.details)
    else:                                      # không gắn được ⇒ ngoài vùng, như main
        assert out.servable and not neu_khoi_da_dien(de)


def test_mau_thuan_khong_ten_khong_co_scene3d_qua_pipeline(monkeypatch):
    M.LABELS["U_C_square"] = C0["U_C_square"]
    de, contract, sp = M.hop_dong_va_chuong_trinh("U_C_square")

    async def analyze(*_a, **_k):
        return contract, None

    async def program(*_a, **_k):
        return sp, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "stage_semantic_program", program)
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    env = asyncio.run(PL.run_pipeline(de, "fake_key"))
    assert env.get("status") != "ok" and not env.get("scene3d"), env
    assert env.get("reason_code") == MA and env.get("refusal_cause") == "SOURCE"


# ══ bộ đọc — không đoán tên, phủ định, một thẩm quyền "tên điểm thiếu toạ độ" ═════
@pytest.mark.parametrize("de, ten", [
    ("Cho hình chóp tứ giác đều có cạnh đáy bằng 4, chiều cao bằng 3. Tính thể tích khối chóp.", set()),
    ("Cho hình chóp tứ giác đều với A(0;0;0), B(2;0;0), S(1;1;3). Tính thể tích khối chóp.", set()),
    ("Cho hình chóp tứ giác đều có AB = 4, SA = 3. Tính thể tích khối chóp.", {"A", "B", "S"}),
    ("Cho hình chóp tứ giác đều có cạnh đáy bằng 4. Tính độ dài cạnh bên SA.", {"S", "A"}),
    ("Cho hình chóp tứ giác đều với A(0;0;0), S(1;1;3). Gọi M là trung điểm của SA.", {"M"}),
])
def test_ten_diem_khong_toa_do(de, ten):
    assert ten_diem_khong_toa_do(de) == ten


@pytest.mark.parametrize("de, ky_vong", [
    ("Cho hình chóp tứ giác đều có cạnh đáy bằng 4.", {("regular_square_pyramid", ())}),
    ("Cho khối chóp tam giác đều có cạnh đáy 3.", {("regular_triangular_pyramid", ())}),
    ("Cho A(0;0;0); đây không phải là hình chóp tứ giác đều.", set()),
    ("Cho hình chóp với A(0;0;0). Chứng minh đó là hình chóp tứ giác đều.", set()),
    ("Cho hình chóp tứ giác đều và hình lập phương.", set()),
    ("Cho hình chóp ngũ giác đều có cạnh đáy bằng 4.", set()),
])
def test_bo_doc_khong_doan_ten(de, ky_vong):
    from app.simulation.semantic_program.shape_constraint import che_muc_tieu
    assert {(r.kind, r.entities) for r in doc_rang_buoc(che_muc_tieu(de)) if r.kind in DEU} == ky_vong
    assert all(not re.search(r"[A-Z]", "".join(r.entities)) for r in doc_rang_buoc(de) if r.kind in DEU)
