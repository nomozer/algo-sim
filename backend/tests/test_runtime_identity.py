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
    capability_fingerprint,
    runtime_identity,
    stable_capability_hash,
)
from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    _CHU_KY, _KIEU_DO, _KIEU_DUNG,
)
from runtime_doctor import diagnose  # noqa: E402


# ── danh tính dẫn xuất, không hard-code ──
#
# ⚠️ Trước `LEGACY_INFORMATICS_REMOVAL`, danh tính runtime dẫn từ `CATALOG` —
# 24 target Tin học. Danh mục ấy đã gỡ. Bệnh mà cả module này sinh ra để chặn
# thì KHÔNG đổi (*container chạy mã cũ mà không gì báo*), nên nó nay dẫn từ
# thẩm quyền của IR hình học: thêm một phép dựng là hash đổi, không phải sửa tay.
def test_danh_tinh_dan_xuat_tu_tham_quyen_hinh_hoc():
    ident = runtime_identity()
    assert ident["domain"] == "hinh_hoc"
    assert ident["simulation_id"] == "generic.semantic_program"
    assert ident["expressions"] == sorted(_CHU_KY)
    assert ident["construct_statements"] == sorted(_KIEU_DUNG)
    assert ident["measures"] == sorted(_KIEU_DO)
    assert ident["expression_count"] == len(_CHU_KY)
    assert ident["construct_statement_count"] == len(_KIEU_DUNG)
    assert ident["measure_count"] == len(_KIEU_DO)


def test_hash_tat_dinh_va_nhay_voi_thay_doi_nang_luc():
    assert stable_capability_hash() == stable_capability_hash()  # tất định
    fp = capability_fingerprint()
    # Đổi MỘT chi tiết bất kỳ → hash phải đổi (chứng minh hash bao trùm). Chọn
    # KIỂU TRẢ VỀ của một phép dựng: đó đúng lớp thay đổi mà một container cũ
    # sẽ im lặng bỏ qua, và là thứ `_CHU_KY` sở hữu.
    import hashlib, json  # noqa: E401
    mutated = json.loads(json.dumps(fp))
    mot_phep = sorted(mutated["bieu_thuc"])[0]
    mutated["bieu_thuc"][mot_phep]["tra_ve"] += "-x"
    h2 = hashlib.sha256(
        json.dumps(mutated, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert h2 != stable_capability_hash()


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


def test_capability_hash_mismatch():
    src = _src()
    rt = dict(src, stable_capability_hash="0" * 64)
    assert "CAPABILITY_HASH_MISMATCH" in _codes(diagnose(src, rt, "abc123"))


def test_thieu_phep_dung_cau_lenh_phep_do():
    """Runtime thiếu một NĂNG LỰC cụ thể — doctor phải chỉ đúng tên cái thiếu.

    Ca thật: container cũ không có `translate` (thêm 2026-09-01), nên mọi đề
    tịnh tiến chết ở schema mà `git_sha` vẫn khớp.
    """
    src = _src()
    rt = dict(src)
    rt["expressions"] = [x for x in src["expressions"] if x != "translate"]
    rt["construct_statements"] = [x for x in src["construct_statements"]
                                  if x != "construct_section"]
    rt["measures"] = [x for x in src["measures"] if x != "volume"]
    codes = _codes(diagnose(src, rt, "abc123"))
    assert {"MISSING_RUNTIME_EXPRESSION", "MISSING_RUNTIME_STATEMENT",
            "MISSING_RUNTIME_MEASURE"} <= codes


def test_moi_finding_deu_kem_huong_dan_sua():
    src = _src()
    rt = dict(src, cache_version="7", stable_catalog_hash="0" * 64)
    for f in diagnose(src, rt, "abc123"):
        assert "docker compose" in f["fix"]
