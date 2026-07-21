# -*- coding: utf-8 -*-
"""M17-RC1 §B — lock catalog auto-discovery conformance.

Đây là lưới an toàn CHO MỌI TARGET, sinh từ registry: thêm target thứ 20 mà
quên validator/executor/renderer/contract/fixture/classify-exposure là ĐỎ ngay,
không cần ai nhớ thêm nó vào danh sách nào.
"""

from __future__ import annotations

from app.catalog_conformance import (
    DECLARED_MULTI_OWNER,
    ai_reachable_ids,
    build_matrix,
    mechanism_ownership,
    source_runtime_parity,
    target_conformance,
)
from app.simulation.catalog import CATALOG


def test_matrix_phu_dung_moi_ai_reachable_target():
    rows = build_matrix()
    assert [r["target_id"] for r in rows] == ai_reachable_ids()
    assert len(rows) == len(ai_reachable_ids()) > 0


def test_moi_target_du_manh_ghep():
    """Không target nào thiếu validator/executor/renderer/contract/fixture/
    classify-exposure/ownership/config-contract."""
    violations = target_conformance()
    assert violations == [], f"target thiếu mảnh: {violations}"


def test_ownership_owned_xor_gap_va_multi_owner_khai_ro():
    violations = mechanism_ownership()
    assert violations == [], f"vi phạm ownership: {violations}"


def test_multi_owner_deu_co_ly_do_viet_ro():
    """Khai multi-owner phải KÈM LÝ DO — chống 'khai cho qua test'."""
    for mech, reason in DECLARED_MULTI_OWNER.items():
        assert len(reason) > 30, f"{mech}: lý do quá sơ sài"


def test_phat_hien_target_thieu_manh(monkeypatch):
    """Fault injection: bỏ authenticity contract của một target → phải ĐỎ.
    Chứng minh test không đúng-rỗng."""
    import app.catalog_conformance as cc

    rows = build_matrix()
    victim = rows[0]["target_id"]
    broken = [dict(r, authenticity_contract=False) if r["target_id"] == victim else r
              for r in rows]
    codes = {v["code"] for v in cc.target_conformance(broken)}
    assert "MISSING_AUTHENTICITY_CONTRACT" in codes


def test_parity_bat_target_mat_o_runtime():
    fake_runtime = {
        "registered_target_ids": [t for t in CATALOG if t != "tree.traversal"],
        "registered_renderer_ids": sorted({s.domain for s in CATALOG.values()}),
    }
    codes = {v["code"] for v in source_runtime_parity(fake_runtime)}
    assert "MISSING_RUNTIME_TARGET" in codes
    assert source_runtime_parity(None)[0]["code"] == "RUNTIME_UNAVAILABLE"


def test_moi_target_co_renderer_va_executor_that():
    """renderer_id = domain FE, executor_id = engine — không được rỗng/None."""
    for r in build_matrix():
        assert r["renderer_id"], r["target_id"]
        assert r["executor_id"], r["target_id"]
        assert r["validator_id"], r["target_id"]
