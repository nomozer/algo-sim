# -*- coding: utf-8 -*-
"""c0-whole-solid-grounding — C0 kiểm khẳng định TOÀN KHỐI của đề (lăng trụ đứng/xiên, hộp chữ nhật, lập phương, chóp
đều, tứ diện đều, số đo, tâm đáy, chiều cao) trên toạ độ đề cho (amendment §22).

Nhãn ghi trước: `docs/evaluation/geometry/runs/c0-whole-solid-grounding/labels.json` (oracle `oracle.py`, chỉ từ đề).
0 lượt gọi model.
"""
from __future__ import annotations

import asyncio
import pathlib
import subprocess
import sys
from fractions import Fraction

import pytest

from app.ai import pipeline as PL
from app.simulation.semantic_program.assumption_gate import _doc_de
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.route import verify_and_compile

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/c0-whole-solid-grounding"
sys.path.insert(0, str(RUN / "diagnostics"))
from c0_whole_solid_cases import LABELS, hop_dong_va_chuong_trinh  # noqa: E402

MA = "SOURCE_SHAPE_CONTRADICTS_COORDINATES"
#: Hàng mâu thuẫn đã bị cổng KHÁC từ chối từ trước (baseline `probe_9762f441.log`) — §22 không đổi chúng.
TU_CHOI_TRUOC = {"RSP_C_centre_off": "construction_binding", "P_C_prism_top_not_translate": "execution"}


def test_oracle_doc_lap_dong_y_voi_nhan():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


@pytest.mark.parametrize("rid", sorted(LABELS))
def test_c0_toan_khoi_theo_nhan(rid):
    _de, contract, sp = hop_dong_va_chuong_trinh(rid)
    out = verify_and_compile(contract, sp)
    loai, _, gia_tri = LABELS[rid]["expect"].partition(":")
    if loai == "served":
        assert out.servable and out.assumption_certificate == "C0", (out.stage_reached, out.reason_code, out.details)
        assert Fraction(str(SemanticProgramInterpreter().execute(sp).final_memory["V"])) == Fraction(gia_tri)
        return
    assert not out.servable, out.details
    if rid in TU_CHOI_TRUOC:
        assert out.stage_reached == TU_CHOI_TRUOC[rid], (out.stage_reached, out.reason_code)
        return
    assert (out.stage_reached, out.reason_code) == ("assumption", MA), (out.stage_reached, out.reason_code)
    sai = {d.split(" ", 1)[1].split("(", 1)[0] for d in out.details if d.startswith("C0_SHAPE_CONTRADICTION")}
    assert sai & set(LABELS[rid]["kinds"]), (sai, LABELS[rid]["kinds"])
    assert out.reason_subjects


def test_chieu_cao_khong_phai_canh_ben():
    """H_K: S(1;1;4) — cạnh bên SA = √18 ≠ 4 nhưng khoảng cách tới đáy = 4 ⇒ nhất quán; H_C: S(0;0;3) ⇒ 3 ≠ 4."""
    for rid, ok in (("H_K_pyramid_height_not_lateral_edge", True), ("H_C_pyramid_height", False)):
        _de, c, sp = hop_dong_va_chuong_trinh(rid)
        assert verify_and_compile(c, sp).servable is ok, rid


@pytest.mark.parametrize("de", [
    "Cho hình lập phương ABCD.A'B'C'D' cạnh bằng 2. Tính thể tích khối lập phương.",
    "Cho hình chóp tứ giác đều có cạnh đáy bằng 2 và chiều cao bằng 3. Tính thể tích khối chóp.",
], ids=["khong_toa_do", "khoi_khong_ten"])
def test_thieu_du_kien_khong_phai_mau_thuan(de):
    """Không toạ độ / khối không tên: ràng buộc toàn khối có thể được đọc nhưng §22 không có gì để kiểm."""
    from app.simulation.semantic_program.assumption_gate import _mau_thuan_c0

    class _KhongDiem:
        def ten_theo_khoa(self):
            return {}

        def dinh_nghia(self, ten):
            raise KeyError(ten)

    _gt, rb, inv, _dd = _doc_de(de)
    assert {r.kind for r in rb} & {"cube", "cube_edge", "height"}      # đọc được khẳng định, nhưng không có toạ độ
    assert _mau_thuan_c0(rb, _KhongDiem(), inv) == []


def test_mau_thuan_toan_khoi_khong_co_scene3d_qua_pipeline(monkeypatch):
    de, contract, sp = hop_dong_va_chuong_trinh("CU_C_cuboid_oblique_lateral")

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
