# -*- coding: utf-8 -*-
"""VÂN TAY PROMPT — chống "container gửi prompt cũ". **0 API call.**

─── LỖ MÀ FILE NÀY BỊT ────────────────────────────────────────────────────

`runtime_doctor` so `git_sha`, `CACHE_VERSION`, `stable_catalog_hash`. **Cả ba
đều KHỚP** khi backend đang gửi cho LLM một prompt cũ, vì không phép so nào
trong ba đọc một file `.md`. Docstring của chính nó chỉ *cảnh báo bằng lời*:

    "prompt được CACHE THEO TIẾN TRÌNH → phải restart, không đủ nếu chỉ lưu file"

Một lời dặn không phải một cổng. Đo được trong lượt hợp nhất môi trường
2026-08-25: `runtime_doctor` báo PASS trong khi tiến trình đang chạy một bản
`runtime_identity` cũ hơn source.

─── VÌ SAO ĐO `_skill_cache` CHỨ KHÔNG ĐỌC LẠI ĐĨA ────────────────────────

Nếu vân tay đọc lại file trên đĩa rồi băm, nó sẽ báo "khớp" trong **đúng cái ca
nó sinh ra để bắt** — file đã đúng, chỉ tiến trình là cũ. Nên nó phải băm thứ
tiến trình ĐANG GIỮ.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.ai import gemini
from app.runtime_identity import skill_fingerprint


@pytest.fixture
def cache_sach():
    """Cache prompt là TOÀN CỤC trong tiến trình — không dọn thì một test làm
    bẩn test sau, và cái bẩn ấy trông y hệt thứ ta đang đo."""
    cu = dict(gemini._skill_cache)
    gemini._skill_cache.clear()
    yield
    gemini._skill_cache.clear()
    gemini._skill_cache.update(cu)


# ══ ĐO THỨ TIẾN TRÌNH ĐANG GIỮ ═══════════════════════════════════════════
def test_tien_trinh_moi_khoi_dong_thi_CHUA_NAP_gi(cache_sach):
    """`da_nap` rỗng KHÔNG phải lỗi — chưa lượt nào chạy thì chưa prompt nào bị
    giữ, và khi ấy không có gì cũ được."""
    f = skill_fingerprint()
    assert f["da_nap"] == {} and f["cu"] == []
    assert len(f["tren_dia"]) >= 10, "phải thấy MỌI skill trên đĩa"


def test_nap_mot_skill_thi_no_hien_ra(cache_sach):
    gemini.load_skill("geometry_analyze")
    f = skill_fingerprint()
    assert set(f["da_nap"]) == {"geometry_analyze"}
    assert f["cu"] == [], "vừa nạp từ đĩa thì không thể cũ"


def test_PROMPT_CU_TRONG_TIEN_TRINH_bi_bat(cache_sach):
    """Tiêm lỗi giả — cổng chưa từng đỏ là cổng chưa được chứng minh.

    Đây đúng là hiện trường thật: sửa `skills/*.md`, quên restart, và LLM đọc
    bản cũ trong khi mọi phép so khác nói "khớp".
    """
    gemini.load_skill("geometry_program_generator")
    gemini._skill_cache["geometry_program_generator"] = "BẢN CŨ"
    assert skill_fingerprint()["cu"] == ["geometry_program_generator"]


def test_bam_CHUAN_HOA_xuong_dong(cache_sach):
    """Skill nằm trên bind mount từ host Windows; Git đổi CRLF khi chạm file.
    Không chuẩn hoá thì vân tay lệch mà nội dung không đổi một chữ — một báo
    động giả, và báo động giả là cách nhanh nhất để một cổng bị tắt."""
    goc = gemini.load_skill("semantic_analyze")
    gemini._skill_cache["semantic_analyze"] = goc.replace("\n", "\r\n")
    assert skill_fingerprint()["cu"] == []


def test_the_van_pham_co_trong_van_tay(cache_sach):
    """Thẻ sinh TỪ `contract.py` và ghép vào user message: đổi một model Pydantic
    là đổi thứ LLM đọc, mà KHÔNG file `.md` nào bị sửa. Ca dễ quên nhất."""
    assert len(skill_fingerprint()["grammar_card"]) == 64


# ══ DOCTOR PHẢI ĐỎ, KHÔNG ĐƯỢC IM ════════════════════════════════════════
def _doctor():
    import importlib.util
    from pathlib import Path

    dd = Path(__file__).resolve().parents[1] / "scripts" / "runtime_doctor.py"
    spec = importlib.util.spec_from_file_location("_rd", dd)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _nen() -> dict:
    from app.runtime_identity import runtime_identity

    return runtime_identity()


def _ma(findings) -> set[str]:
    return {f["category"] for f in findings}


def test_doctor_bat_PROMPT_STALE_IN_PROCESS():
    rd = _doctor()
    src = _nen()
    rt = {**src, "skills": {**src["skills"], "cu": ["geometry_analyze"]}}
    assert "PROMPT_STALE_IN_PROCESS" in _ma(
        rd.diagnose(src, rt, src["git_sha"]))


def test_doctor_bat_SKILL_FILE_MISMATCH():
    rd = _doctor()
    src = _nen()
    dia = {**src["skills"]["tren_dia"], "semantic_program": "0" * 64}
    rt = {**src, "skills": {**src["skills"], "tren_dia": dia}}
    assert "SKILL_FILE_MISMATCH" in _ma(rd.diagnose(src, rt, src["git_sha"]))


def test_doctor_bat_GRAMMAR_CARD_MISMATCH():
    rd = _doctor()
    src = _nen()
    rt = {**src, "skills": {**src["skills"], "grammar_card": "0" * 64}}
    assert "GRAMMAR_CARD_MISMATCH" in _ma(rd.diagnose(src, rt, src["git_sha"]))


def test_doctor_KHONG_DUOC_IM_khi_runtime_thieu_van_tay():
    """Một cổng không đo được phải nói "không đo được", KHÔNG được nói "khớp".

    Bản đầu của tôi `if rt_sk and src_sk:` — runtime cũ không khai `skills` thì
    cả khối bị bỏ qua và doctor báo PASS. Đó đúng là lỗi module này sinh ra để
    chặn, lọt ngay trong chính nó.
    """
    rd = _doctor()
    src = _nen()
    rt = {k: v for k, v in src.items() if k != "skills"}
    assert "PROMPT_FINGERPRINT_MISSING" in _ma(
        rd.diagnose(src, rt, src["git_sha"]))


def test_doctor_XANH_khi_moi_thu_khop():
    rd = _doctor()
    src = _nen()
    assert rd.diagnose(src, dict(src), src["git_sha"]) == []


# ══ ĐƯỜNG DÂY: ENDPOINT PHẢI PHƠI RA ═════════════════════════════════════
def test_endpoint_diagnostics_runtime_co_khoa_skills():
    from app.main import app

    body = TestClient(app).get("/api/diagnostics/runtime").json()
    assert "skills" in body, "doctor đọc endpoint này — thiếu khoá là mù"
    for k in ("tren_dia", "da_nap", "cu", "grammar_card", "tong"):
        assert k in body["skills"], k
