# -*- coding: utf-8 -*-
"""Guard NGUỒN GỐC dữ kiện cho ảnh chỉ có hình — VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX. 0 lượt gọi mạng.

Lỗi được sửa: `DIAGRAM_OBSERVATION_PROVENANCE_LEAK`. Lượt đọc C03 thật (ảnh chỉ có hình + nhãn) bị từ chối
đúng `MISSING_PROBLEM_TEXT`, nhưng mô hình ghi ba quan hệ vuông góc ĐỌC TỪ KÝ HIỆU HÌNH vào `given_relations`
— trường mang nghĩa "dữ kiện đề phát biểu" — và bản ghi ấy đi nguyên vào phản hồi công khai. Không phải bịa
hoàn toàn: ký hiệu có thật trên hình; sai là NGUỒN GỐC.

Fixture là đầu ra THẬT của lượt ấy (`fixtures/c03_vision_extraction_replay_redacted.json`). Phạm vi: DIAGRAM_ONLY
/ `MISSING_PROBLEM_TEXT` — không có câu nào ở đây về tài liệu vừa có chữ vừa có hình.

Tên test mang chữ cái hợp đồng A–J của wave. Tập trường dữ kiện được KHAI RIÊNG ở đây, không đọc từ sản
phẩm: bớt một trường khỏi guard thì test phải thấy, không được mù theo.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import logging
import uuid
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main as main_module
from app.ai import gemini
from app.ingestion import image_extraction as ie
from app.ingestion.image import normalize_image
from app.persistence.db import init_db
from tests.test_photo_problem_live_runner import (  # noqa: F401 — kho/de/_khong_cho_backoff là fixture
    CA_P1,
    RNB,
    R,
    _ca,
    _chay,
    _json,
    _khong_cho_backoff,
    _kich_ban,
    de,
    kho,
)

TESTS = Path(__file__).resolve().parent
GOC = TESTS.parents[1]
FIXTURE = json.loads((TESTS / "fixtures" / "c03_vision_extraction_replay_redacted.json").read_text(encoding="utf-8"))
C03 = FIXTURE["extraction"]
FRONTEND_FIXTURE = GOC / "frontend" / "src" / "components" / "photo-c03-diagram-only.fixture.json"
QUAN_HE_C03 = ["SA vuông góc với AC", "SA vuông góc với AB", "Góc BAC là góc vuông"]
#: Trường MANG DỮ KIỆN lời đề (khai độc lập với sản phẩm — xem docstring).
TRUONG_DU_KIEN = ("problem_text_verbatim", "problem_text_normalized", "math_expressions", "given_relations")
SU_KIEN = "VISION_DIAGRAM_FACTS_QUARANTINED"
KHOA_TELEMETRY = {"event", "scope", "rejection_code", "quarantined_fields", "item_counts", "sha256",
                  "quarantined_fact_count", "raw_model_fact_fields_empty", "safe_public_fact_fields_empty",
                  "diagram_observation_count"}
DE = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với đáy và SA = 3. "
      "Tính thể tích khối chóp S.ABCD.")

#: Các đầu ra RÒ dữ kiện mà guard phải cách ly — C03 thật, cộng hai biến thể cùng hình dạng lỗi.
BIEN_THE_RO = {
    "c03_that": C03,
    "c03_them_cong_thuc_tu_hinh": {**C03, "math_expressions": [{"verbatim": "∠BAC = 90°", "normalized": "∠BAC = 90°"}]},
    "c03_chu_ngan_khong_phai_de": {**C03, "problem_text_verbatim": "Hình 1", "problem_text_normalized": "Hình 1"},
}
#: Tài liệu CÓ lời đề — guard không được đụng (dạng C01: chữ + hình + quan hệ; dạng C02: chữ + công thức).
CO_LOI_DE = {
    "chu_va_hinh_co_quan_he": {**C03, "problem_text_verbatim": DE, "problem_text_normalized": DE,
                               "math_expressions": [{"verbatim": "SA = 3", "normalized": "SA = 3"}],
                               "named_points": ["S", "A", "B", "C", "D"], "named_solids": ["S.ABCD"],
                               "given_relations": ["SA vuông góc với đáy", "ABCD là hình vuông"]},
    "chu_khong_hinh_co_cong_thuc": {**C03, "problem_text_verbatim": DE, "problem_text_normalized": DE,
                                    "math_expressions": [{"verbatim": "2x − z + 12 = 0", "normalized": "2x − z + 12 = 0"}],
                                    "given_relations": [], "has_diagram": False, "diagram_observations": []},
}

client = TestClient(main_module.app)


@pytest.fixture(autouse=True)
def _cache_sach():
    ie.EXTRACTION_CACHE.clear()
    yield
    ie.EXTRACTION_CACHE.clear()


def _gia(monkeypatch, tra) -> list[int]:
    goi: list[int] = []

    async def fake(*a, **k):
        goi.append(1)
        await asyncio.sleep(0)
        if isinstance(tra, BaseException):
            raise tra
        return tra if isinstance(tra, str) else json.dumps(tra, ensure_ascii=False)

    monkeypatch.setattr(ie, "call_gemini", fake)
    return goi


def _anh() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (48, 36), (255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


def _post(monkeypatch, tra) -> httpx.Response:
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    _gia(monkeypatch, tra)
    return client.post("/api/image/extract", json={"content": base64.b64encode(_anh()).decode(), "mime_type": "image/png"})


def _doc(monkeypatch, tra, cache_version=None):
    _gia(monkeypatch, tra)
    return asyncio.run(ie.extract_problem_from_image(normalize_image(_anh()), "khoa-gia", cache_version=cache_version))


def _co_du_kien(x: dict) -> dict:
    """Trường dữ kiện KHÔNG rỗng (rỗng = đúng `""` hoặc `[]`)."""
    return {t: x[t] for t in TRUONG_DU_KIEN if x[t] not in ("", [])}


def _chuoi_du_kien(x: dict) -> list[str]:
    ra: list[str] = []
    for t, v in _co_du_kien(x).items():
        for muc in (v if isinstance(v, list) else [v]):
            ra.extend([muc["verbatim"], muc["normalized"]] if isinstance(muc, dict) else [muc])
    return ra


def _bam(v) -> str:
    return hashlib.sha256(ie.canonical_json_bytes(v)).hexdigest()


def _su_kien(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if SU_KIEN in r.getMessage()]


# ── tiền đề: fixture là đầu ra thật, nguyên vẹn ─────────────────────────────
def test_fixture_C03_NGUYEN_VEN_va_qua_Pydantic_day_du():
    assert _bam(C03) == FIXTURE["provenance"]["extraction_canonical_sha256"]
    assert ie.parse_extraction(json.dumps(C03, ensure_ascii=False)).model_dump() == C03
    assert C03["given_relations"] == QUAN_HE_C03 and not C03["problem_text_verbatim"]


# ── A ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(BIEN_THE_RO))
def test_A_payload_CONG_KHAI_khong_mang_du_kien_khi_khong_co_loi_de(ten, monkeypatch):
    raw = BIEN_THE_RO[ten]
    assert _co_du_kien(raw), "tiền đề: mô hình ĐÃ trả dữ kiện"
    r = _post(monkeypatch, raw)
    assert r.status_code == 200
    d = r.json()
    assert _co_du_kien(d["extraction"]) == {}
    assert d["extraction"]["given_relations"] == []
    assert d["assessment"]["problem_text"] == ""
    for s in _chuoi_du_kien(raw):
        assert s not in r.text, f"dữ kiện bị cách ly vẫn nằm trong phản hồi: {s!r}"


# ── B ───────────────────────────────────────────────────────────────────────
def test_B_quan_sat_tu_hinh_GIU_NGUYEN_o_vung_chi_quan_sat(monkeypatch):
    d = _post(monkeypatch, C03).json()["extraction"]
    for t in ("diagram_observations", "has_diagram", "named_points", "named_lines", "named_planes", "named_solids",
              "text_diagram_conflicts", "uncertain_tokens", "missing_regions", "confidence"):
        assert d[t] == C03[t], t
    assert len(d["diagram_observations"]) == 7


# ── C ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(BIEN_THE_RO))
def test_C_ma_tu_choi_van_la_MISSING_PROBLEM_TEXT(ten, monkeypatch):
    a = _post(monkeypatch, BIEN_THE_RO[ten]).json()["assessment"]
    assert (a["status"], a["rejection_code"], a["requires_confirmation"]) == ("rejected", "MISSING_PROBLEM_TEXT", True)
    assert a["learner_message"] == ie.REJECTION_MESSAGES["MISSING_PROBLEM_TEXT"]


# ── D ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(BIEN_THE_RO))
def test_D1_duong_analyze_anh_cu_KHONG_toi_pipeline(ten, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.setattr(main_module, "CACHE_VERSION", f"test-{uuid.uuid4()}")
    init_db()
    thay: list[str] = []

    async def fake_pipeline(text, api_key, **kw):
        thay.append(text)
        return {"status": "ok"}

    monkeypatch.setattr(main_module, "run_pipeline", fake_pipeline)
    _gia(monkeypatch, BIEN_THE_RO[ten])
    r = client.post("/api/analyze", json={"input": {"type": "image", "content": base64.b64encode(_anh()).decode(),
                                                    "mime_type": "image/png"}})
    assert r.status_code == 400 and thay == []
    for s in _chuoi_du_kien(BIEN_THE_RO[ten]):
        assert s not in r.text


def _chay_c03(kho, de, vision):
    p1 = RNB.doc_raw_theo_thu_tu(CA_P1)
    # Phản hồi tầng B CÓ SẴN cho C03 — nếu runner gọi, nó được phục vụ và lộ ra.
    thay = {("C03", "vision"): [vision], ("C03", "analyze"): p1["semantic_analyze"],
            ("C03", "synthesis"): p1["semantic_program"]}
    r = _chay(kho, "C03", kich_ban=_kich_ban(de, thay))
    return r, _json(r, "RUN_SUMMARY.json")


def test_D2_runner_C03_CHI_mot_luot_vision_khong_analyze_synthesis_canh(kho, de):
    r, tt = _chay_c03(kho, de, json.dumps(C03, ensure_ascii=False))
    assert r.prov.calls == [("C03", "vision")]
    assert (tt["ANALYZE_HTTP_REQUESTS"], tt["SYNTHESIS_HTTP_REQUESTS"]) == (0, 0)
    assert _ca(tt, "C03")["STAGE_B_HTTP_ATTEMPTS"] == 0
    assert not (r.ra / "C03_ANALYZE_RESULT.json").exists() and not (r.ra / "C03_SCENE_RESULT.json").exists()


# ── E ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(BIEN_THE_RO))
def test_E1_guard_DUNG_ca_khi_mo_hinh_van_tra_du_kien(ten, monkeypatch):
    raw = BIEN_THE_RO[ten]
    kq = _doc(monkeypatch, raw)
    cong = kq.extraction.model_dump()
    assert kq.assessment.rejection_code == "MISSING_PROBLEM_TEXT"
    assert _co_du_kien(cong) == {} and kq.assessment.problem_text == ""
    blob = json.dumps({"extraction": cong, "assessment": kq.assessment.to_dict()}, ensure_ascii=False)
    for s in _chuoi_du_kien(raw):
        assert s not in blob
    # Không sao chép, không diễn giải: vùng quan sát đúng bằng bản mô hình trả.
    assert cong["diagram_observations"] == raw["diagram_observations"]


def test_E2_ban_trong_CACHE_cung_di_qua_guard(monkeypatch):
    goi = _gia(monkeypatch, C03)
    anh = normalize_image(_anh())
    dau = asyncio.run(ie.extract_problem_from_image(anh, "khoa-gia", cache_version="95"))
    sau = asyncio.run(ie.extract_problem_from_image(anh, "khoa-gia", cache_version="95"))
    assert len(goi) == 1 and dau.cached is False and sau.cached is True
    for kq in (dau, sau):
        assert _co_du_kien(kq.extraction.model_dump()) == {} and kq.assessment.problem_text == ""


def test_E3_runner_C03_bao_RIENG_ban_mo_hinh_ban_cong_khai_va_so_cach_ly(kho, de):
    r, tt = _chay_c03(kho, de, json.dumps(C03, ensure_ascii=False))
    assert r.code == R.EXIT_PASS, (r.out, r.err)
    c = _ca(tt, "C03")
    assert c["RAW_MODEL_FACT_FIELDS_EMPTY"] is False
    assert c["SAFE_PUBLIC_FACT_FIELDS_EMPTY"] is True
    assert c["QUARANTINED_FACT_FIELDS"] == ["given_relations"] and c["QUARANTINED_FACT_COUNT"] == 3
    assert c["DIAGRAM_OBSERVATIONS_USED_AS_FACTS"] == "NO"
    assert c["C03_SAFE_REJECTION"] is True and c["SILENT_HALLUCINATION"] == 0
    tho = _json(r, "C03_RAW_EXTRACTION.json")
    assert tho["extraction"]["given_relations"] == QUAN_HE_C03      # bản mô hình trả — chỉ ở thư mục chạy
    assert _co_du_kien(tho["public_extraction"]) == {}


def test_E4_runner_CHAM_DOC_LAP__guard_bi_vo_hieu_thi_C03_FAIL(kho, de, monkeypatch):
    # Vô hiệu guard bằng cách để nó không còn trường nào để cách ly. Runner phải tự thấy dữ kiện trong bản công
    # khai — không được tin nhãn guard tự khai.
    monkeypatch.setattr(ie, "FACT_BEARING_FIELDS", (), raising=False)
    r, tt = _chay_c03(kho, de, json.dumps(C03, ensure_ascii=False))
    c = _ca(tt, "C03")
    assert r.code == R.EXIT_CASE_FAIL
    assert c["C03_SAFE_REJECTION"] is False and c["SILENT_HALLUCINATION"] == 1
    assert c["SAFE_PUBLIC_FACT_FIELDS_EMPTY"] is False and c["DIAGRAM_OBSERVATIONS_USED_AS_FACTS"] == "YES"
    assert any(x.startswith("C03_PUBLIC_FACT_FIELDS_NOT_EMPTY") for x in c["fail_reasons"])


# ── F ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten, truong", [
    ("c03_that", ["given_relations"]),
    ("c03_them_cong_thuc_tu_hinh", ["math_expressions", "given_relations"]),
    ("c03_chu_ngan_khong_phai_de", ["problem_text_verbatim", "problem_text_normalized", "given_relations"]),
])
def test_F_telemetry_TEN_TRUONG_SO_MUC_BAM__khong_noi_dung_tho(ten, truong, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    raw = BIEN_THE_RO[ten]
    kq = _doc(monkeypatch, raw)
    ban = _su_kien(caplog)
    assert len(ban) == 1
    tele = json.loads(ban[0].getMessage().split(" ", 1)[1])
    assert set(tele) == KHOA_TELEMETRY
    assert tele["event"] == SU_KIEN and tele["rejection_code"] == "MISSING_PROBLEM_TEXT"
    assert tele["quarantined_fields"] == truong
    assert tele["item_counts"] == {t: (len(raw[t]) if isinstance(raw[t], list) else 1) for t in truong}
    assert tele["sha256"] == {t: _bam(raw[t]) for t in truong}
    assert tele["quarantined_fact_count"] == sum(tele["item_counts"].values())
    assert (tele["raw_model_fact_fields_empty"], tele["safe_public_fact_fields_empty"]) == (False, True)
    assert tele["diagram_observation_count"] == len(raw["diagram_observations"])
    assert kq.provenance_guard.to_telemetry() == tele
    lo = caplog.text + json.dumps(tele, ensure_ascii=False)
    for s in _chuoi_du_kien(raw):
        assert s not in lo, f"telemetry ghi nội dung thô: {s!r}"
    assert json.dumps(raw, ensure_ascii=False) not in lo


# ── G ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(CO_LOI_DE))
def test_G_tai_lieu_CO_loi_de__guard_KHONG_dong_vao(ten, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    raw = CO_LOI_DE[ten]
    d = _post(monkeypatch, raw).json()
    x = ie.parse_extraction(json.dumps(raw, ensure_ascii=False))
    assert d["extraction"] == x.model_dump()
    assert d["assessment"] == ie.assess_extraction(x).to_dict()
    assert d["assessment"]["status"] == "ready_for_review"
    assert not _su_kien(caplog)


# ── H ───────────────────────────────────────────────────────────────────────
def test_H_thieu_loi_de_KHONG_ro_du_kien__giu_nguyen(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    raw = {**C03, "given_relations": []}
    d = _post(monkeypatch, raw).json()
    x = ie.parse_extraction(json.dumps(raw, ensure_ascii=False))
    assert d["extraction"] == x.model_dump()
    assert d["assessment"] == ie.assess_extraction(x).to_dict()
    assert d["assessment"]["rejection_code"] == "MISSING_PROBLEM_TEXT"
    assert not _su_kien(caplog)


# ── I ───────────────────────────────────────────────────────────────────────
def test_I_fixture_giao_dien_KHOP_ban_cong_khai_backend_dung(monkeypatch):
    """`photo-problem-panel.test.tsx` vẽ đúng bản này: quan sát dưới nhãn tham khảo, ô dựng trống, nút khoá."""
    d = _post(monkeypatch, C03).json()
    assert json.loads(FRONTEND_FIXTURE.read_text(encoding="utf-8")) == {"extraction": d["extraction"],
                                                                        "assessment": d["assessment"]}


# ── J ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("tra, ma_http, ma", [
    (RuntimeError("Gemini API lỗi HTTP 503"), 503, "VISION_UNAVAILABLE"),
    ("không phải JSON", 502, "VISION_OUTPUT_VALIDATION_FAILED"),
    ({**C03, "truong_la": 1}, 502, "VISION_OUTPUT_VALIDATION_FAILED"),
    ({**C03, "confidence": 1.5}, 502, "VISION_OUTPUT_VALIDATION_FAILED"),
], ids=["provider", "json", "pydantic_thua_truong", "pydantic_ngoai_khoang"])
def test_J1_loi_provider_luoc_do_Pydantic_KHONG_BAO_GIO_la_tu_choi_an_toan(tra, ma_http, ma, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    r = _post(monkeypatch, tra)
    assert r.status_code == ma_http and r.json()["reason_code"] == ma
    assert not {"assessment", "extraction"} & set(r.json())
    assert "MISSING_PROBLEM_TEXT" not in r.text
    assert not _su_kien(caplog)


@pytest.mark.parametrize("vision, tien_to", [
    (httpx.Response(503, json={"error": "tam thoi"}), "VISION_PROVIDER_ERROR"),
    ("không phải JSON", "VISION_CONTRACT_ERROR"),
    (json.dumps({**C03, "truong_la": 1}, ensure_ascii=False), "VISION_CONTRACT_ERROR"),
], ids=["http_503", "json", "pydantic"])
def test_J2_runner_C03_loi_KHONG_tinh_la_tu_choi_an_toan(kho, de, vision, tien_to):
    r, tt = _chay_c03(kho, de, vision)
    c = _ca(tt, "C03")
    assert c["C03_SAFE_REJECTION"] is False and c["status"] != "PASS"
    assert c["fail_reasons"][0].startswith(tien_to)
    assert r.prov.calls == [("C03", "vision")]


# ── bề mặt mô hình: prompt nói luật, lược đồ gửi KHÔNG lớn thêm ───────────────
def test_prompt_noi_du_kien_chi_tu_chu__hinh_vao_quan_sat__khong_loi_de_thi_rong():
    dong = gemini.load_skill(ie.VISION_PROMPT_SKILL).splitlines()
    d4 = next(x for x in dong if x.startswith("4. "))
    d9 = next(x for x in dong if x.startswith("9. "))
    assert "`given_relations`" in d4 and "`diagram_observations`" in d4 and "hình" in d4
    assert "mục 3–4" in d9 and "rỗng" in d9


def test_luoc_do_gui_Gemini_va_luoc_do_day_du_KHONG_doi():
    assert ie.VISION_TRANSPORT_SCHEMA_SHA256 == "4681095460246d6c0598ace071b44c710b09cf3f3a912dc4aa652618d7c49a43"
    assert ie.VISION_RESPONSE_SCHEMA_SHA256 == "77dfe727288d6e82468a236179c84cdfecdd29c51346215f981d9104dda1a31f"
    assert ie.VISION_SCHEMA_IDENTITY == "photo-problem-extraction/1+gemini-transport-4681095460246d6c"
