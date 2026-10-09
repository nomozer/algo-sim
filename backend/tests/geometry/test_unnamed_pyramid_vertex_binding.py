# -*- coding: utf-8 -*-
"""unnamed-pyramid-vertex-binding — chính sách A (§25): chóp đều không tên mà đề gọi tên điểm thiếu toạ độ (§24 không
gắn được) nằm TRONG vùng từ chối và bị cổng chặn — không phục vụ một cách đặt tên đỉnh đề chưa cố định.

Nhãn toán học (`labels.json`, `oracle.py`, nghiên cứu phương án B) giữ nguyên; kỳ vọng sản phẩm của chính sách A ở
`policy_a_labels.json`: cả 21 hàng bị từ chối (5 vì giới hạn năng lực, 16 vì an toàn). 0 lượt gọi model.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import subprocess
import sys

import pytest

from app.ai import pipeline as PL
from app.simulation.semantic_program.shape_constraint import neu_khoi_da_dien
from tests.geometry import test_regular_square_pyramid as SQ
from tests.geometry import test_regular_triangular_pyramid as TR

RUN = pathlib.Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/unnamed-pyramid-vertex-binding"
TOAN = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
CHINH_SACH = json.loads((RUN / "policy_a_labels.json").read_text(encoding="utf-8"))["rows"]
MOD = {"square": SQ, "triangular": TR}
TRUOC = "TEMPLATE_NOT_MATCHED unnamed regular pyramid"


def _ket_qua(rid: str, monkeypatch) -> dict:
    corpus, ca = rid.split("/")
    mod = MOD[corpus]
    monkeypatch.setitem(mod.NHAN, ca, {**mod.NHAN[ca], "text": TOAN[rid]["text"]})
    return mod.ket_qua(ca)


def test_oracle_toan_hoc_khong_doi():
    assert subprocess.run([sys.executable, str(RUN / "oracle.py")], capture_output=True).returncode == 0


def test_nhan_chinh_sach_phu_21_hang_va_khong_tuyen_bo_vo_nghiem():
    assert set(CHINH_SACH) == set(TOAN) and len(CHINH_SACH) == 21
    assert all(r["expect_policy_a"] == "refused" for r in CHINH_SACH.values())
    xac_dinh = {k for k, r in TOAN.items() if r["text_verdict"].startswith("determined")}
    assert {k for k, r in CHINH_SACH.items() if r["why"].startswith("capability_limit")} == {
        k for k in xac_dinh if "program_defect" not in TOAN[k]["facts"]}


@pytest.mark.parametrize("rid", sorted(CHINH_SACH))
def test_chinh_sach_a_tu_choi_ca_21(rid, monkeypatch):
    kq = _ket_qua(rid, monkeypatch)
    assert "served" not in kq, (rid, kq.get("served"))
    assert kq["reason_code"] != "SOURCE_SHAPE_CONTRADICTS_COORDINATES"   # không phải mâu thuẫn toạ độ
    if CHINH_SACH[rid]["baseline_a7c56942"].startswith("served"):        # 12 hàng mới bị chặn: chính cổng §25
        assert (kq["stage"], kq["reason_code"]) == ("assumption", "ASSUMPTION_INVARIANCE_UNPROVEN")
        assert any(d.startswith(TRUOC) for d in kq["details"]), kq["details"]
    else:                                                                # 9 hàng đã từ chối: giữ chặng cũ
        assert f"refused:{kq['stage']}:{kq['reason_code']}" == CHINH_SACH[rid]["baseline_a7c56942"]


def test_vung_tu_choi_gom_chop_deu_khong_ten_co_ten_diem():
    assert neu_khoi_da_dien("Cho hình chóp tứ giác đều có AB = 4, SA = 3. Tính thể tích khối chóp.")
    assert neu_khoi_da_dien("Cho hình chóp tứ giác đều có cạnh đáy bằng 4. Tính thể tích khối chóp.")
    assert not neu_khoi_da_dien("Cho tam giác ABC có AB = 4. Tính diện tích tam giác ABC.")


def test_khong_scene3d_qua_pipeline(monkeypatch):
    rid = "square/R2_N9_contradiction_program_fits_lengths"
    corpus, ca = rid.split("/")
    monkeypatch.setitem(SQ.NHAN, ca, {**SQ.NHAN[ca], "text": TOAN[rid]["text"]})
    contract, prog = SQ._nap(ca)

    async def analyze(*_a, **_k):
        return contract, None

    async def program(*_a, **_k):
        from app.simulation.semantic_program.contract import SemanticProgramSpec
        return SemanticProgramSpec.model_validate(prog), None

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "stage_semantic_program", program)
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    env = asyncio.run(PL.run_pipeline(TOAN[rid]["text"], "fake_key"))
    assert env.get("status") != "ok" and not env.get("scene3d"), env
    assert env.get("reason_code") == "ASSUMPTION_INVARIANCE_UNPROVEN"
