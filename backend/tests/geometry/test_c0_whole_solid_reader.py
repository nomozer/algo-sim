# -*- coding: utf-8 -*-
"""c0-whole-solid-reader — bộ đọc nhận khẳng định chóp ĐỀU viết `có đỉnh S và đáy ABCD` và `chóp đều S.ABCD` như ký
hiệu chuẩn `chóp tứ/tam giác đều S.ABCD`; phủ định không phải tiền đề.

Nhãn ghi trước: `docs/evaluation/geometry/runs/c0-whole-solid-reader/labels.json` (oracle `oracle.py`, `claims` viết
tay). C1: luật tương đương `c1_rule` trên hai corpus chóp đều. 0 lượt gọi model.
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
from app.simulation.semantic_program.shape_constraint import doc_rang_buoc
from tests.geometry import test_regular_square_pyramid as SQ
from tests.geometry import test_regular_triangular_pyramid as TR

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/c0-whole-solid-reader"
sys.path.insert(0, str(RUN.parent / "c0-whole-solid-grounding" / "diagnostics"))
import c0_whole_solid_cases as M  # noqa: E402

ROWS = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
MA = "SOURCE_SHAPE_CONTRADICTS_COORDINATES"
DEU = {"regular_square_pyramid", "regular_triangular_pyramid"}


def _ca(rid: str):
    M.LABELS[rid] = ROWS[rid]
    return M.hop_dong_va_chuong_trinh(rid)


def _bo(text: str) -> list:
    return sorted((r.kind, r.entities, str(r.value)) for r in doc_rang_buoc(text))


def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


# ══ C0 — toạ độ đề cho vs khẳng định chóp đều ═══════════════════════════════
@pytest.mark.parametrize("rid", sorted(r for r in ROWS if ROWS[r]["expect"] != "baseline"))
def test_c0_theo_nhan(rid):
    _de, contract, sp = _ca(rid)
    out = verify_and_compile(contract, sp)
    loai, _, gia_tri = ROWS[rid]["expect"].partition(":")
    if loai == "served":
        assert out.servable and out.assumption_certificate == "C0", (out.stage_reached, out.reason_code, out.details)
        assert Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"])) == Fraction(gia_tri)
        return
    assert (out.servable, out.stage_reached, out.reason_code) == (False, "assumption", MA), out.details
    assert any(d.startswith("C0_SHAPE_CONTRADICTION regular_") for d in out.details), out.details
    assert out.reason_subjects


@pytest.mark.parametrize("rid", sorted(r for r in ROWS if ROWS[r]["expect"] == "baseline"))
def test_chop_deu_khong_ten_khong_gan_vao_khoi_nao(rid):
    """Giới hạn ghi nhận: dữ kiện không gọi tên đỉnh/đáy ⇒ không khẳng định chóp đều nào được phát (không đoán)."""
    de, _c, _sp = _ca(rid)
    assert not {r.kind for r in doc_rang_buoc(de)} & DEU


@pytest.mark.parametrize("de, deu", [
    ("Cho {coords}; đây không phải là hình chóp tứ giác đều S.ABCD.", set()),
    ("Cho {coords}; S.ABCD không phải là hình chóp đều S.ABCD.", set()),
    ("Cho {coords}; đó không phải hình chóp tứ giác đều có đỉnh S và đáy ABCD.", set()),
    ("Cho hình chóp đều S.ABCDE.", set()),
    ("Cho hình chóp có đỉnh S và đáy ABCD.", set()),
    ("Cho hình chóp đều S.ABCD và khối chóp ngũ giác đều T.MNPQR.", {("S", "A", "B", "C", "D")}),
], ids=["phu_dinh_chuan", "phu_dinh_chop_deu", "phu_dinh_dinh_day", "ngu_giac", "khong_deu", "ngu_giac_chuan"])
def test_khong_phat_khang_dinh_chop_deu_sai(de, deu):
    """Phủ định, đáy ≠ 3/4 đỉnh, chóp không "đều": không khẳng định chóp đều nào."""
    assert {r.entities for r in doc_rang_buoc(de) if r.kind in DEU} == deu


def test_mau_thuan_khong_co_scene3d_qua_pipeline(monkeypatch):
    de, contract, sp = _ca("P1_C_square")

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


# ══ C1 — luật tương đương (`c1_rule`) ════════════════════════════════════════
_CHUAN = re.compile(r"(?P<noun>[Hh]ình|[Kk]hối) chóp (?P<g>tứ|tam) giác đều (?P<S>[A-Z])\.(?P<b>[A-Z]{3,4})(?![A-Za-z'])")
_VIET_LAI = {
    "apex_base": lambda m: f"{m['noun']} chóp {m['g']} giác đều có đỉnh {m['S']} và đáy {m['b']}",
    "regular_notation": lambda m: f"{m['noun']} chóp đều {m['S']}.{m['b']}",
}
_C1 = [(ten, mod, ca, v) for ten, mod in (("square", SQ), ("triangular", TR)) for ca in sorted(mod.NHAN)
       if _CHUAN.search(mod.NHAN[ca]["text"]) for v in _VIET_LAI]


def _ket_cuc(mod, ca) -> str:
    k = mod.ket_qua(ca)
    return f"served:{k['served']}" if "served" in k else f"refused:{k['stage']}:{k['reason_code']}"


@pytest.mark.parametrize("ten, mod, ca, v", _C1, ids=[f"{t}-{c}-{v}" for t, _m, c, v in _C1])
def test_c1_loi_viet_moi_tuong_duong_ky_hieu_chuan(ten, mod, ca, v, monkeypatch):
    goc = mod.NHAN[ca]
    m = _CHUAN.search(goc["text"])
    moi = goc["text"][:m.start()] + _VIET_LAI[v](m) + goc["text"][m.end():]
    assert _bo(moi) == _bo(goc["text"])
    chuan = _ket_cuc(mod, ca)
    monkeypatch.setitem(mod.NHAN, ca, {**goc, "text": moi})
    assert _ket_cuc(mod, ca) == chuan
