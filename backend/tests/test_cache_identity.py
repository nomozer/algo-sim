# -*- coding: utf-8 -*-
"""KỶ LUẬT PHIÊN BẢN ĐƯỢC MÁY CƯỠNG CHẾ — không phải cache địa chỉ theo nội dung.

─── LỖ NÓ BỊT ────────────────────────────────────────────────────────────────

Khoá cache runtime là *text đã chuẩn hoá + `CACHE_VERSION`*, và bản vá này
**không đổi** điều đó. Vấn đề nằm ở chỗ khác: `CACHE_VERSION` là một con số
**người phải nhớ tăng**. Đổi một prompt, một lược đồ gửi cho mô hình, hay một
chữ ký IR mà quên bump thì một đề đã phân tích tiếp tục được phục vụ bằng
envelope sinh từ **một phiên bản hệ không còn tồn tại** — và không gì phát hiện.

`CURRENT_ARCHITECTURE_GAP_AUDIT §12` gọi đúng tên: *"meaning changes but cache
identity does not"*. Nó không làm hình học sai — kernel vẫn tính đúng — nhưng nó
bẻ **phép đo**: chạy lại sau khi sửa prompt sẽ đo phải bản cũ ở mọi đề đã cache.

─── CÂU ĐÚNG PHẢI NÓI SAU BẢN VÁ NÀY ───────────────────────────────────────

    "Đầu vào tĩnh mang nghĩa không thể đổi mà không làm cổng danh tính cache
     đỏ."

**KHÔNG** phải *"cache tự vô hiệu hoá"* — runtime vẫn dựa vào `CACHE_VERSION`.

─── VÌ SAO CÓ PHÉP TIÊM ────────────────────────────────────────────────────

Một cổng chưa bao giờ đỏ là một cổng chưa được chứng minh. Bốn ca `TIÊM` dưới
đây bắt vân tay đổi thật, bằng cách vá **chính thư mục/hàm mà runtime dùng**,
trong `tmp_path` hoặc qua `monkeypatch` — cây sản phẩm không bẩn một byte.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.main import CACHE_VERSION
from app.runtime_identity import (
    semantic_environment_fingerprint,
    semantic_environment_hash,
    stable_capability_hash,
)

BACKEND = Path(__file__).resolve().parents[1]
KHOA = BACKEND / "cache_identity.lock.json"


def _khoa() -> dict:
    assert KHOA.exists(), (
        "Thiếu `backend/cache_identity.lock.json`. Tạo bằng:\n"
        "  cd backend && .venv/Scripts/python.exe scripts/lock_cache_identity.py")
    return json.loads(KHOA.read_text(encoding="utf-8"))


# ══ CỔNG CHÍNH ═══════════════════════════════════════════════════════════
def test_khoa_gan_dung_CACHE_VERSION_voi_moi_truong_sinh():
    """Cổng của cả bản vá.

    Đỏ ở đây nghĩa là **một trong hai** đã đổi mà cái kia chưa: hoặc môi trường
    sinh đổi (prompt / thẻ / lược đồ / chữ ký IR) mà `CACHE_VERSION` giữ nguyên,
    hoặc `CACHE_VERSION` đã bump mà khoá chưa làm mới. Cả hai đều phải dừng lại
    và xem, không được lặng lẽ xanh.
    """
    k = _khoa()
    nay = semantic_environment_hash()
    doi = [t for t, v in semantic_environment_fingerprint().items()
           if (k.get("components") or {}).get(t) != v]
    assert k.get("cache_version") == CACHE_VERSION and \
        k.get("semantic_environment_hash") == nay, (
        "\n\nMÔI TRƯỜNG SINH NGỮ NGHĨA ĐÃ ĐỔI.\n"
        "Xem lại: envelope đã cache có còn đúng dưới bản mới không?\n"
        "  · CÒN đúng  ⇒ chỉ chạy lại `scripts/lock_cache_identity.py`.\n"
        "  · KHÔNG còn ⇒ bump `CACHE_VERSION` (ba cổng, xem CLAUDE.md §3)\n"
        "                rồi mới chạy lại script.\n\n"
        f"  khoá:  version {k.get('cache_version')} · "
        f"{str(k.get('semantic_environment_hash'))[:16]}…\n"
        f"  hiện:  version {CACHE_VERSION} · {nay[:16]}…\n"
        f"  thành phần đổi: {doi or '(không — chỉ version lệch)'}\n")


def test_thanh_phan_khoa_KHOP_TUNG_CAI_khong_chi_bam_tong():
    """Băm tổng khớp mà một thành phần lệch là điều không xảy ra được — nhưng
    nếu ai đó sửa khoá bằng tay, ca này bắt được, còn ca trên thì không."""
    k = _khoa()
    assert k.get("components") == semantic_environment_fingerprint()


def test_script_verify_dong_y_voi_test():
    """Hai đường đọc cùng một sự thật: người chạy script, CI chạy pytest. Lệch
    nhau thì một trong hai nói dối."""
    r = subprocess.run(
        [sys.executable, str(BACKEND / "scripts" / "lock_cache_identity.py"),
         "--verify"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(BACKEND))
    assert r.returncode == 0, r.stdout + r.stderr


# ══ TÍNH TẤT ĐỊNH ════════════════════════════════════════════════════════
def test_van_tay_TAT_DINH_trong_cung_mot_tien_trinh():
    assert semantic_environment_hash() == semantic_environment_hash()


def test_van_tay_KHONG_phu_thuoc_duong_dan_checkout():
    """Không thành phần nào chứa đường dẫn tuyệt đối, dấu phân cách hệ điều
    hành, hay dấu thời gian — chúng là băm của NỘI DUNG."""
    vt = semantic_environment_fingerprint()
    assert all(isinstance(v, str) and len(v) == 64 for v in vt.values())
    for xau in (str(BACKEND), "\\", "C:", "/home"):
        assert xau not in json.dumps(vt)


def test_bam_chuan_hoa_xuong_dong():
    """File prompt nằm trên bind mount từ Windows; Git đổi CRLF khi chạm file.
    Không chuẩn hoá thì vân tay lệch giữa host và container **mà nội dung không
    đổi một chữ** — một báo động giả, và báo động giả là cách nhanh nhất để một
    cổng bị tắt."""
    from app.runtime_identity import _bam

    assert _bam("a\r\nb") == _bam("a\nb")


# ══ TIÊM · CHỨNG MINH CỔNG ĐỎ ĐƯỢC ═══════════════════════════════════════
def test_TIEM_prompt_doi_thi_van_tay_doi(monkeypatch, tmp_path):
    """Sửa một file `skills/*.md` ⇒ vân tay đổi ⇒ cổng đỏ nếu version giữ nguyên.

    Vá **chính `gemini.SKILLS_DIR`** — thư mục runtime nạp prompt từ đó — chứ
    không vá một danh sách riêng. Nhờ vậy một file prompt MỚI mà runtime dùng
    thì không thể nằm ngoài vân tay: cả hai đọc cùng một chỗ.
    """
    from app.ai import gemini

    truoc = semantic_environment_hash()
    gia = tmp_path / "skills"
    gia.mkdir()
    for f in gemini.SKILLS_DIR.glob("*.md"):
        (gia / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    (gia / "geometry_program_generator.md").write_text(
        "MỘT CÂU KHÁC HẲN — tiêm để kiểm cổng.", encoding="utf-8")
    monkeypatch.setattr(gemini, "SKILLS_DIR", gia)

    sau = semantic_environment_hash()
    assert sau != truoc, "sửa prompt mà vân tay KHÔNG đổi — cổng vô dụng"


def test_TIEM_them_file_prompt_MOI_cung_doi_van_tay(monkeypatch, tmp_path):
    """Ca dễ quên nhất: thêm một prompt mới. Vì vân tay dẫn từ `SKILLS_DIR` chứ
    không từ một danh sách viết tay, nó tự vào."""
    from app.ai import gemini

    truoc = semantic_environment_hash()
    gia = tmp_path / "skills"
    gia.mkdir()
    for f in gemini.SKILLS_DIR.glob("*.md"):
        (gia / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    (gia / "prompt_hoan_toan_moi.md").write_text("nội dung", encoding="utf-8")
    monkeypatch.setattr(gemini, "SKILLS_DIR", gia)

    assert semantic_environment_hash() != truoc


def test_TIEM_chu_ky_IR_doi_thi_van_tay_doi(monkeypatch):
    """Thêm/đổi một chữ ký ở `_CHU_KY` ⇒ `stable_capability_hash` đổi ⇒ vân tay
    đổi. Dùng lại chính băm năng lực, không chép bảng chữ ký sang đây."""
    from app.simulation.semantic_program import ir_static_check as isc

    truoc = semantic_environment_hash()
    bam_truoc = stable_capability_hash()
    monkeypatch.setitem(
        isc._CHU_KY, "phep_tiem_de_kiem_cong",
        ((("point", ("point3",)),), "plane3"))

    assert stable_capability_hash() != bam_truoc
    assert semantic_environment_hash() != truoc, (
        "chữ ký IR đổi mà vân tay môi trường KHÔNG đổi — băm năng lực chưa "
        "được đưa vào vân tay")


def test_TIEM_hop_dong_model_facing_doi_thi_van_tay_doi(monkeypatch):
    """Lược đồ gửi cho mô hình là **đầu vào tĩnh** như prompt. Đổi nó — kể cả
    chỉ đổi một mô tả trường, thứ KHÔNG chạm bảng chữ ký — vẫn phải đổi vân
    tay, nếu không thì một hợp đồng khác đang được gửi dưới cùng một phiên bản.
    """
    from app.simulation.semantic_program import contract as C

    truoc = semantic_environment_hash()
    goc = C.generate_json_schema

    def gia() -> dict:
        s = goc()
        s["title"] = "LƯỢC ĐỒ ĐÃ TIÊM"
        return s

    monkeypatch.setattr(C, "generate_json_schema", gia)
    assert semantic_environment_hash() != truoc


def test_TIEM_chi_bump_VERSION_ma_khong_lam_moi_khoa_thi_DO(monkeypatch):
    """Chiều ngược lại. Khoá không được thành ảnh chụp cũ mà test vẫn xanh:
    bump version rồi quên chạy script ⇒ cặp lệch ⇒ đỏ."""
    import app.main as main_module

    monkeypatch.setattr(main_module, "CACHE_VERSION", "999-tiem")
    k = _khoa()
    assert k.get("cache_version") != main_module.CACHE_VERSION


# ══ HÀNH VI CACHE KHÔNG ĐỔI ══════════════════════════════════════════════
def test_KHOA_CACHE_san_pham_KHONG_doi():
    """Bản vá này là một CỔNG, không phải một khoá cache mới.

    `_cache_key` vẫn băm *text đã chuẩn hoá*, và tra cứu vẫn so `policy_version`
    với `CACHE_VERSION`. Không vân tay nào lọt vào đường chạy thật — nếu lọt,
    mọi hàng cache hiện có mất hiệu lực trong im lặng.
    """
    import inspect

    import app.main as main_module

    src = inspect.getsource(main_module._cache_key)
    for cam in ("semantic_environment", "skill_fingerprint",
                "stable_capability_hash"):
        assert cam not in src, f"vân tay lọt vào khoá cache sản phẩm: {cam}"

    tra = inspect.getsource(main_module._cache_lookup)
    assert "policy_version" in tra and "CACHE_VERSION" in tra


@pytest.mark.parametrize("ten", ["cache_version", "semantic_environment_hash",
                                 "components"])
def test_khoa_co_du_truong_de_LOI_NOI_DUOC_CAI_GI_DOI(ten):
    """Thông điệp chỉ in hai chuỗi hex bắt người đọc tự đi tìm, và họ sẽ bump
    cho xong. Khoá giữ từng thành phần để lời từ chối nêu đúng cái nào đổi."""
    assert ten in _khoa()
