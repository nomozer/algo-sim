# -*- coding: utf-8 -*-
"""M17-RC1 §A — lock runtime identity + logic chẩn đoán của runtime doctor.

Bệnh đã cháy: container chạy CACHE_VERSION "7" (thời M10) nhiều milestone mà
không gì báo. Test này khoá: (1) danh tính DẪN XUẤT từ registry (thêm target
là hash đổi, không phải sửa tay); (2) doctor phân loại đúng từng kiểu lệch.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

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


# ── KHOÁ 1:1 NĂNG LỰC BACKEND ↔ MODULE FRONTEND ───────────────────────────
#
# VÌ SAO PHẢI DỰNG LẠI. Khoá cũ là `capability-descriptors.test.ts`: nó so
# `capability-descriptors.json` (sinh từ `CATALOG`) với các module frontend đăng
# ký. Cả ba vế đều đã gỡ cùng danh mục 24 target, nên từ lúc đó **không còn gì**
# nối hai phía — và đúng chế độ hỏng mà khoá cũ sinh ra để chặn lại mở toang:
# backend phát một `simulation_id` không ai đăng ký thì `store.loadEnvelope` từ
# chối *ở runtime*, không test nào đỏ.
#
# Bản này đọc THẲNG mã nguồn TS thay vì một artifact trung gian — cùng khuôn
# `tests/geometry/test_scene3d_ts_sync.py`. Không còn artifact nào để quên sinh
# lại, nên cũng không còn khoảng lệch giữa "đã chạy script" và "đã đúng".

_FE = Path(__file__).resolve().parents[2] / "frontend" / "src" / "simulations"


def _id_frontend_dang_ky() -> set[str]:
    """Tập `simulation_id` mà frontend THẬT SỰ đăng ký.

    Đi qua `registerAllSimulations()` → các `register…Domain()` được gọi → hằng
    `id:` trong module tương ứng. Không đọc cả cây `domains/`: một module tồn
    tại mà không được gọi thì nó KHÔNG phải năng lực đang chạy, và gộp nó vào
    đây là cách khoá tự nói dối theo chiều dễ dãi.
    """
    index = (_FE / "index.ts").read_text(encoding="utf-8")
    than = re.search(
        r"export function registerAllSimulations\(\)[^{]*\{(.*?)\n\}", index, re.S
    )
    assert than, "không tìm thấy `registerAllSimulations` — đổi tên?"

    goi = re.findall(r"\n\s*(register\w*Domain)\(\);", than.group(1))
    assert goi, "`registerAllSimulations` không gọi domain nào — khoá thành vô nghĩa"

    ids: set[str] = set()
    for ten in goi:
        # `registerSemanticDomain` → `./domains/semantic`
        m = re.search(rf'import \{{ {ten} \}} from "\./(.+?)";', index)
        assert m, f"không lần ra module của `{ten}`"
        src = (_FE / f"{m.group(1)}" / "index.ts").read_text(encoding="utf-8")
        ids |= set(re.findall(r'\n\s*id: "([^"]+)",', src))
    return ids


def test_frontend_dang_ky_DUNG_nhung_id_backend_phat_ra():
    """Song ánh hai chiều. Thiếu vế nào cũng là một chế độ hỏng riêng.

    Thừa ở backend ⇒ đề hợp lệ chạy xong rồi không có gì vẽ nó.
    Thừa ở frontend ⇒ một module không bao giờ được gọi, và người sau đọc nó
    như năng lực đang có.
    """
    backend = {runtime_identity()["simulation_id"]}
    frontend = _id_frontend_dang_ky()
    assert backend == frontend, (
        f"lệch: chỉ backend phát {sorted(backend - frontend)} · "
        f"chỉ frontend đăng ký {sorted(frontend - backend)}"
    )


def test_phep_do_lan_ra_duoc_id_that_khong_phai_tap_rong():
    """Guard rỗng-mà-xanh: parser hỏng thì mọi assert trên thành vô nghĩa.

    `test_scene3d_ts_sync` đã phải học bài này một lần — nên bắt phép dò khẳng
    định nó đọc ra đúng chuỗi id, chứ không chỉ "không lệch".
    """
    assert _id_frontend_dang_ky() == {"generic.semantic_program"}


def test_khoa_11_DO_DUOC_khi_frontend_lech(tmp_path, monkeypatch):
    """Tiêm lỗi: đổi id ở phía TS ⇒ khoá phải đỏ.

    Khoá chưa từng đỏ là khoá chưa được chứng minh (`ARCHITECTURE_MAP §8` #14).
    Ca này dựng một cây `simulations/` giả đúng hình dạng thật rồi trỏ `_FE`
    sang đó — không đụng mã sản phẩm để chụp được ảnh.
    """
    (tmp_path / "domains" / "semantic").mkdir(parents=True)
    (tmp_path / "index.ts").write_text(
        'import { registerSemanticDomain } from "./domains/semantic";\n'
        "export function registerAllSimulations(): void {\n"
        "  registerSemanticDomain();\n"
        "}\n",
        encoding="utf-8",
    )
    (tmp_path / "domains" / "semantic" / "index.ts").write_text(
        'const mod = {\n  id: "generic.SAI_LECH",\n};\n', encoding="utf-8"
    )
    # Patch theo ĐỐI TƯỢNG module, không theo chuỗi tên: dạng chuỗi nạp một bản
    # sao thứ hai của chính file này (`tests.test_runtime_identity` ≠ tên pytest
    # đang chạy nó) và vá vào bản sao ấy — guard vẫn đọc file thật rồi xanh giả.
    monkeypatch.setattr(sys.modules[__name__], "_FE", tmp_path)

    assert _id_frontend_dang_ky() == {"generic.SAI_LECH"}  # parser vẫn đọc được
    with pytest.raises(AssertionError, match="lệch"):
        test_frontend_dang_ky_DUNG_nhung_id_backend_phat_ra()
