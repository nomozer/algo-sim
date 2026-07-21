# -*- coding: utf-8 -*-
"""M17-RC1 §A — lock runtime identity + logic chẩn đoán của runtime doctor.

Bệnh đã cháy: container chạy CACHE_VERSION "7" (thời M10) nhiều milestone mà
không gì báo. Test này khoá: (1) danh tính DẪN XUẤT từ registry (thêm target
là hash đổi, không phải sửa tay); (2) doctor phân loại đúng từng kiểu lệch.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from app.runtime_identity import (  # noqa: E402
    catalog_fingerprint,
    runtime_identity,
    stable_catalog_hash,
)
from app.simulation.catalog import CATALOG  # noqa: E402
from app.simulation.descriptor import FamilyId, ReachabilityLevel  # noqa: E402
from runtime_doctor import diagnose  # noqa: E402


# ── danh tính dẫn xuất, không hard-code ──
def test_danh_tinh_dan_xuat_tu_registry():
    ident = runtime_identity()
    assert ident["family_count"] == len(FamilyId)
    assert ident["target_count"] == len(CATALOG)
    assert ident["registered_target_ids"] == sorted(CATALOG)
    ai = sorted(
        sid for sid, s in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in s.reachability
    )
    assert ident["registered_ai_reachable_ids"] == ai
    assert ident["ai_reachable_target_count"] == len(ai)
    # renderer = domain FE; executor = executor_id — đều dẫn xuất
    assert ident["registered_renderer_ids"] == sorted({s.domain for s in CATALOG.values()})
    assert ident["registered_executor_ids"] == sorted({s.executor_id for s in CATALOG.values()})


def test_hash_tat_dinh_va_nhay_voi_thay_doi_catalog():
    assert stable_catalog_hash() == stable_catalog_hash()  # tất định
    fp = catalog_fingerprint()
    # đổi MỘT chi tiết bất kỳ → hash phải đổi (chứng minh hash bao trùm)
    import hashlib, json  # noqa: E401
    mutated = json.loads(json.dumps(fp))
    any_target = sorted(mutated["targets"])[0]
    mutated["targets"][any_target]["config_contract_version"] += "-x"
    h2 = hashlib.sha256(
        json.dumps(mutated, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert h2 != stable_catalog_hash()


def test_git_sha_khong_bia_khi_thieu(monkeypatch):
    monkeypatch.delenv("ALGOSIM_GIT_SHA", raising=False)
    assert runtime_identity()["git_sha"] == "unknown"  # trung thực, không đoán


# ── doctor: phân loại đúng từng kiểu lệch ──
def _src() -> dict:
    s = runtime_identity()
    s["git_sha"] = "abc123"
    return s


def _codes(findings) -> set[str]:
    return {f["category"] for f in findings}


def test_khop_hoan_toan_khong_finding():
    src = _src()
    assert diagnose(src, dict(src), "abc123") == []


def test_stale_image_khi_sha_lech():
    src = _src()
    rt = dict(src, git_sha="deadbee")
    assert "RUNTIME_STALE_IMAGE" in _codes(diagnose(src, rt, "abc123"))


def test_khong_ket_luan_khi_sha_unknown():
    """Runtime không biết SHA (build cũ) → KHÔNG được kết luận stale từ SHA;
    các tín hiệu khác (cache/hash) mới là bằng chứng."""
    src = _src()
    rt = dict(src, git_sha="unknown")
    assert "RUNTIME_STALE_IMAGE" not in _codes(diagnose(src, rt, "abc123"))


def test_cache_version_mismatch():
    src = _src()
    rt = dict(src, cache_version="7")  # đúng ca đã cháy
    assert "CACHE_VERSION_MISMATCH" in _codes(diagnose(src, rt, "abc123"))


def test_catalog_hash_mismatch():
    src = _src()
    rt = dict(src, stable_catalog_hash="0" * 64)
    assert "CATALOG_HASH_MISMATCH" in _codes(diagnose(src, rt, "abc123"))


def test_thieu_target_family_executor_renderer():
    src = _src()
    rt = dict(src)
    rt["registered_target_ids"] = [t for t in src["registered_target_ids"] if t != "tree.traversal"]
    rt["family_ids"] = [f for f in src["family_ids"] if f != "tree_traversal"]
    rt["registered_renderer_ids"] = [d for d in src["registered_renderer_ids"] if d != "tree"]
    rt["registered_executor_ids"] = [e for e in src["registered_executor_ids"] if e != "tree.traversal"]
    codes = _codes(diagnose(src, rt, "abc123"))
    assert {"MISSING_RUNTIME_TARGET", "MISSING_RUNTIME_FAMILY",
            "MISSING_RUNTIME_RENDERER", "MISSING_RUNTIME_EXECUTOR"} <= codes


def test_moi_finding_deu_kem_huong_dan_sua():
    src = _src()
    rt = dict(src, cache_version="7", stable_catalog_hash="0" * 64)
    for f in diagnose(src, rt, "abc123"):
        assert "docker compose" in f["fix"]
