# -*- coding: utf-8 -*-
"""Cache theo TUYẾN (run `hybrid-pre-main-hardening`).

Trước bản này khoá cache là `sha256(đề)` và lookup chỉ so `CACHE_VERSION`: bật `GEOMETRY_COMPILER_MODE` (hay một tuyến
mới) mà không bump thì người học nhận envelope `LLM_ONLY` cũ; rollback thì ngược lại. Và chế độ được đọc HAI lần (ở
`main` khi tra/ghi cache, ở `pipeline` khi định tuyến) — đổi env giữa lượt thì hàng ghi mang nhãn của chế độ không chạy.

Bất biến khoá ở đây:
  - đổi chế độ ⇒ MISS, cả hai chiều; mặc định giữ identity = `CACHE_VERSION` (hàng hiện có vẫn trúng, không bump);
  - identity của chế độ compiler đổi khi phiên bản compiler/adapter/fact-graph/primitive đổi;
  - MỘT ảnh chụp mỗi lượt: tra, chạy, ghi cùng một chế độ, kể cả khi env đổi giữa chừng.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.ai import pipeline as PL
from app.main import app
from app.persistence.db import SessionLocal, SimulationCache, init_db

client = TestClient(app)
DE = "Cho hình chóp S.ABCD có đáy là hình vuông, tính thể tích khối chóp S.ABCD. ({})"


@pytest.fixture()
def phien(monkeypatch):
    """CACHE_VERSION riêng (≤7 ký tự: identity có hậu tố vẫn vừa String(16)), đề riêng, dọn hàng ở cuối."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    monkeypatch.setattr(main_module, "CACHE_VERSION", f"t{uuid.uuid4().hex[:6]}")
    init_db()
    de = DE.format(uuid.uuid4().hex[:8])
    goi: list = []

    async def gia(text, api_key, pattern_store=None, **kw):
        # Chế độ pipeline THỰC SỰ chạy: ảnh chụp nếu được truyền, nếu không thì env lúc ấy (hành vi trước bản này).
        rp = kw.get("route_policy")
        goi.append(rp)
        che_do = rp.geometry_compiler_mode if rp else (os.environ.get("GEOMETRY_COMPILER_MODE") or "LLM_ONLY")
        return {"status": "ok", "simulation_id": "geometry.scene3d", "domain": "geometry", "visual_mode": "3d",
                "title": che_do, "description": "d", "config": {}, "notes": None}

    monkeypatch.setattr(main_module, "run_pipeline", gia)
    yield de, goi
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=main_module._cache_key(de)).delete()
        s.commit()


def _phan_tich(de):
    r = client.post("/api/analyze", json={"input": {"type": "text", "content": de}})
    assert r.status_code == 200, r.text
    return r.json()


def test_bat_compiler_khong_dung_lai_envelope_LLM_ONLY(phien, monkeypatch):
    de, goi = phien
    assert _phan_tich(de)["title"] == "LLM_ONLY"
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    b = _phan_tich(de)
    assert not b.get("cached") and b["title"] == "DETERMINISTIC_FIRST", b
    assert len(goi) == 2


def test_rollback_ve_LLM_ONLY_khong_dung_lai_envelope_compiler(phien, monkeypatch):
    de, goi = phien
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    assert _phan_tich(de)["title"] == "DETERMINISTIC_FIRST"
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE")
    b = _phan_tich(de)
    assert not b.get("cached") and b["title"] == "LLM_ONLY", b


def test_cung_che_do_van_trung_cache_va_mac_dinh_giu_identity_CACHE_VERSION(phien, monkeypatch):
    de, goi = phien
    _phan_tich(de)
    assert _phan_tich(de).get("cached") is True and len(goi) == 1
    with SessionLocal() as s:
        row = s.query(SimulationCache).filter_by(key=main_module._cache_key(de)).first()
        assert row.policy_version == main_module.CACHE_VERSION   # hàng hiện có (ghi ở mặc định) vẫn trúng sau bản này
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    _phan_tich(de)
    assert _phan_tich(de).get("cached") is True and len(goi) == 2


def test_identity_compiler_doi_khi_phien_ban_compiler_doi_va_vua_cot(monkeypatch):
    from app.simulation.geometry_compiler import compiler as Cmp

    mac_dinh = main_module._policy_identity(PL.route_policy_snapshot({}))
    gc = main_module._policy_identity(PL.route_policy_snapshot({"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"}))
    assert mac_dinh == main_module.CACHE_VERSION and gc != mac_dinh and len(gc) <= 16
    assert main_module._policy_identity(PL.route_policy_snapshot({"GEOMETRY_COMPILER_MODE": "la"})) == mac_dinh
    monkeypatch.setattr(Cmp, "COMPILER_VERSION", Cmp.COMPILER_VERSION + "+khac")
    gc2 = main_module._policy_identity(PL.route_policy_snapshot({"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"}))
    assert gc2 != gc
    assert main_module._policy_identity(PL.route_policy_snapshot({})) == mac_dinh


def test_mot_anh_chup_moi_luot_du_env_doi_giua_chung(phien, monkeypatch):
    """Pipeline đổi env GIỮA lượt: chế độ chạy và nhãn hàng ghi vẫn là ảnh chụp lúc vào."""
    de, goi = phien
    cu = main_module.run_pipeline

    async def doi_giua(text, api_key, pattern_store=None, **kw):
        monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
        return await cu(text, api_key, pattern_store, **kw)

    monkeypatch.setattr(main_module, "run_pipeline", doi_giua)
    assert _phan_tich(de)["title"] == "LLM_ONLY"
    with SessionLocal() as s:
        row = s.query(SimulationCache).filter_by(key=main_module._cache_key(de)).first()
        assert row.policy_version == main_module.CACHE_VERSION


def test_pipeline_dinh_tuyen_theo_anh_chup_khong_doc_lai_env(monkeypatch):
    """`run_pipeline(route_policy=…)` quyết định bằng ảnh chụp: env nói compiler nhưng ảnh chụp `LLM_ONLY` ⇒ không
    compiler (gọi provider), và ngược lại env rỗng nhưng ảnh chụp compiler ⇒ compiler dùng, 0 lượt provider."""
    from tests.geometry.test_prism_production_route import _prism_p01_contract

    text, contract = _prism_p01_contract()

    async def analyze(*a, **k):
        return contract, None

    goi_provider = []

    async def gemini(*a, **k):
        goi_provider.append(1)
        raise RuntimeError("PROVIDER")

    monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
    monkeypatch.setattr(PL, "call_gemini", gemini)

    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")
    with pytest.raises(RuntimeError, match="PROVIDER"):
        asyncio.run(PL.run_pipeline(text, "k", route_policy=PL.route_policy_snapshot({})))
    assert goi_provider == [1]

    monkeypatch.delenv("GEOMETRY_COMPILER_MODE")
    env = asyncio.run(PL.run_pipeline(
        text, "k", route_policy=PL.route_policy_snapshot({"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"})))
    assert env.get("status") == "ok" and goi_provider == [1], env.get("reason")


def test_cache_clear_khong_coi_hang_cua_che_do_khac_la_cu():
    """`scripts/cache_clear.py --cu` từng xoá mọi hàng `!= CACHE_VERSION`, kể cả hàng hợp lệ `CACHE_VERSION:<băm>`
    của chế độ compiler (review độc lập của run `hybrid-pre-main-hardening`)."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "cache_clear", Path(__file__).resolve().parents[1] / "scripts" / "cache_clear.py")
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)
    gc = main_module._policy_identity(PL.route_policy_snapshot({"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"}))
    assert cc.con_hieu_luc(main_module.CACHE_VERSION, main_module.CACHE_VERSION)
    assert cc.con_hieu_luc(gc, main_module.CACHE_VERSION)
    assert not cc.con_hieu_luc("124", "125") and not cc.con_hieu_luc("1250", "125") and not cc.con_hieu_luc(None, "125")
    assert not cc.con_hieu_luc("124:abcd1234", "125")


def test_route_policy_bat_bien():
    rp = PL.route_policy_snapshot({})
    with pytest.raises(Exception):
        rp.geometry_compiler_mode = "DETERMINISTIC_FIRST"  # type: ignore[misc]
