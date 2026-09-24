# -*- coding: utf-8 -*-
"""Lược đồ GỬI Gemini tách khỏi lược đồ THẨM ĐỊNH phía server. 0 lượt gọi mạng.

`GEMINI_VISION_SCHEMA_COMPATIBILITY_FIX` (2026-09-14). Lượt Gemini thật đầu tiên của
đường đọc ảnh (`ORIGINAL_C01_CONTROLLED_PROVIDER_ACCEPTANCE`) nhận HTTP 400
INVALID_ARGUMENT: *"The specified schema produces a constraint that has too many
states for serving"*. Thông điệp nêu hai nguyên nhân khớp lược đồ đang gửi: giới hạn
độ dài mảng (kể cả lồng nhau) và số có `minimum`/`maximum`.

Hợp đồng ở đây:
- lược đồ GỬI (`VISION_TRANSPORT_SCHEMA`) sinh tự động từ lược đồ đầy đủ, bỏ
  `maxItems` · `minItems` · `minimum` · `maximum` ở MỌI độ sâu — để giảm tổng độ phức
  tạp mà máy chủ phải phục vụ, không phải vì chúng "không được hỗ trợ";
- lược đồ ĐẦY ĐỦ (`VISION_RESPONSE_SCHEMA`) và model Pydantic GIỮ NGUYÊN mọi giới hạn,
  và mọi phản hồi vẫn đi qua Pydantic trước khi được dùng.

⚠️ Không test nào ở đây giả lập hay đoán ngưỡng "too many states" của Gemini — ngưỡng
ấy nằm phía máy chủ. Chỉ một request thật mới xác nhận được bản sửa.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import io
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.ai import gemini
from app.ingestion import image_extraction as ie
from app.ingestion.image import normalize_image

TU_KHOA_BO = {"maxItems", "minItems", "minimum", "maximum"}
DE = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. Tính thể tích khối chóp S.ABC."

#: Giới hạn của lược đồ ĐẦY ĐỦ ở 5e01509 — khoá cứng để bản sửa không lặng lẽ nới chúng.
GIOI_HAN_DAY_DU = {
    "$.math_expressions": {"maxItems": 80},
    "$.named_points": {"maxItems": 80},
    "$.named_lines": {"maxItems": 60},
    "$.named_planes": {"maxItems": 60},
    "$.named_solids": {"maxItems": 40},
    "$.given_relations": {"maxItems": 60},
    "$.diagram_observations": {"maxItems": 40},
    "$.text_diagram_conflicts": {"maxItems": 20},
    "$.uncertain_tokens": {"maxItems": 60},
    "$.uncertain_tokens[].alternatives": {"maxItems": 6},
    "$.missing_regions": {"maxItems": 20},
    "$.confidence": {"minimum": 0, "maximum": 1},
}


@pytest.fixture(autouse=True)
def _cache_sach():
    ie.EXTRACTION_CACHE.clear()
    yield
    ie.EXTRACTION_CACHE.clear()


def _gioi_han(schema: dict) -> dict[str, dict]:
    """`{đường dẫn: {từ khoá: giá trị}}` cho mọi từ khoá giới hạn ở mọi nút lược đồ."""
    ra: dict[str, dict] = {}

    def di(nut, duong):
        if not isinstance(nut, dict):
            return
        co = {k: nut[k] for k in TU_KHOA_BO if k in nut}
        if co:
            ra[duong] = co
        for ten, con in (nut.get("properties") or {}).items():
            di(con, f"{duong}.{ten}")
        if isinstance(nut.get("items"), dict):
            di(nut["items"], f"{duong}[]")

    di(schema, "$")
    return ra


def _ban_ghi(**thay) -> dict:
    ban = {
        "problem_text_verbatim": DE, "problem_text_normalized": DE,
        "math_expressions": [{"verbatim": "AB = 3", "normalized": "AB = 3"}],
        "named_points": ["S", "A", "B", "C"], "named_lines": [], "named_planes": ["(ABC)"],
        "named_solids": ["S.ABC"], "given_relations": ["ABC là tam giác vuông tại A"],
        "has_diagram": True, "diagram_observations": [], "text_diagram_conflicts": [],
        "uncertain_tokens": [], "missing_regions": [], "confidence": 0.95,
    }
    ban.update(thay)
    return ban


def _anh():
    buf = io.BytesIO()
    Image.new("RGB", (32, 24), (255, 255, 255)).save(buf, format="PNG")
    return normalize_image(buf.getvalue())


def _ma_loi(raw: str) -> str:
    with pytest.raises(ie.VisionContractError) as exc:
        ie.parse_extraction(raw)
    return exc.value.code


# ══ 1–6 · LƯỢC ĐỒ GỬI VÀ LƯỢC ĐỒ ĐẦY ĐỦ ═══════════════════════════════════
def test_01_luoc_do_gui_KHONG_con_gioi_han_mang_hay_bien_so_o_MOI_do_sau():
    assert _gioi_han(ie.VISION_TRANSPORT_SCHEMA) == {}


def test_02_minItems_duoc_kiem_ke_va_bo_NHAT_QUAN_voi_tu_khoa_con_lai():
    assert not any("minItems" in v for v in _gioi_han(ie.VISION_RESPONSE_SCHEMA).values()), \
        "lược đồ đầy đủ ở 5e01509 không có minItems — nếu thêm, phải kiểm kê lại"
    nguon = {"type": "object", "properties": {"a": {"type": "array", "minItems": 1, "maxItems": 3,
                                                    "items": {"type": "array", "minItems": 2, "items": {"type": "string"}}}}}
    assert _gioi_han(ie.build_gemini_transport_schema(nguon)) == {}


def test_03_luoc_do_DAY_DU_va_model_Pydantic_GIU_NGUYEN_moi_gioi_han():
    assert _gioi_han(ie.VISION_RESPONSE_SCHEMA) == GIOI_HAN_DAY_DU
    js = ie.ImageProblemExtraction.model_json_schema()
    assert js["properties"]["named_points"]["maxItems"] == 80
    assert js["properties"]["confidence"]["minimum"] == 0.0 and js["properties"]["confidence"]["maximum"] == 1.0
    assert js["properties"]["problem_text_verbatim"]["maxLength"] == 8000


def test_04_ham_chuyen_KHONG_sua_tai_cho_luoc_do_nguon():
    nguon = copy.deepcopy(ie.VISION_RESPONSE_SCHEMA)
    truoc = ie.canonical_json_bytes(nguon)
    ra = ie.build_gemini_transport_schema(nguon)
    assert ie.canonical_json_bytes(nguon) == truoc
    assert ra["properties"]["uncertain_tokens"]["items"] is not nguon["properties"]["uncertain_tokens"]["items"]
    assert ie.canonical_json_bytes(ie.VISION_RESPONSE_SCHEMA) == truoc


def test_05_hai_lan_chuyen_cho_canonical_JSON_GIONG_TUNG_BYTE():
    a = ie.canonical_json_bytes(ie.build_gemini_transport_schema(ie.VISION_RESPONSE_SCHEMA))
    b = ie.canonical_json_bytes(ie.build_gemini_transport_schema(ie.VISION_RESPONSE_SCHEMA))
    dao = json.loads(json.dumps(ie.VISION_RESPONSE_SCHEMA), object_pairs_hook=lambda kv: dict(reversed(kv)))
    c = ie.canonical_json_bytes(ie.build_gemini_transport_schema(dao))
    assert a == b == c == ie.canonical_json_bytes(ie.VISION_TRANSPORT_SCHEMA)
    assert hashlib.sha256(a).hexdigest() == ie.VISION_TRANSPORT_SCHEMA_SHA256


def test_06_mang_LONG_alternatives_duoc_xu_ly():
    full = ie.VISION_RESPONSE_SCHEMA["properties"]["uncertain_tokens"]["items"]["properties"]["alternatives"]
    gui = ie.VISION_TRANSPORT_SCHEMA["properties"]["uncertain_tokens"]["items"]["properties"]["alternatives"]
    assert full["maxItems"] == 6 and "maxItems" not in gui
    assert gui == {"type": "array", "items": {"type": "string"}}


# ══ 7–12 · HẬU KIỂM VẪN LÀ PYDANTIC ĐẦY ĐỦ ═════════════════════════════════
@pytest.mark.parametrize("c", [-0.01, 1.5])
def test_07_confidence_NGOAI_khoang_van_bi_Pydantic_tu_choi(c):
    assert _ma_loi(json.dumps(_ban_ghi(confidence=c))) == "VISION_OUTPUT_VALIDATION_FAILED"


@pytest.mark.parametrize("thay", [
    {"named_points": [f"P{i}" for i in range(81)]},
    {"uncertain_tokens": [{"token": "1", "alternatives": list("abcdefg"), "location": "x", "reason": "y"}]},
], ids=["named_points_81", "alternatives_7_long_nhau"])
def test_08_VUOT_so_phan_tu_van_bi_Pydantic_tu_choi(thay):
    assert _ma_loi(json.dumps(_ban_ghi(**thay))) == "VISION_OUTPUT_VALIDATION_FAILED"


def test_09_request_Gemini_THAT_SU_mang_luoc_do_gui_o_bien_HTTP(monkeypatch):
    than: list[dict] = []

    def tra(req: httpx.Request) -> httpx.Response:
        than.append(json.loads(req.content))
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(_ban_ghi())}]}}]})

    goc = httpx.AsyncClient
    monkeypatch.setattr(gemini.httpx, "AsyncClient",
                        lambda *a, **k: goc(*a, **{**k, "transport": httpx.MockTransport(tra)}))
    kq = asyncio.run(ie.extract_problem_from_image(_anh(), "khoa-gia", cache_version=None))
    assert kq.assessment.status == "ready_for_review" and len(than) == 1
    cfg = than[0]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json"
    assert cfg["responseSchema"] == gemini._sanitize_gemini_schema(ie.VISION_TRANSPORT_SCHEMA)
    assert _gioi_han(cfg["responseSchema"]) == {}
    assert than[0]["systemInstruction"]["parts"][0]["text"] == gemini.load_skill(ie.VISION_PROMPT_SKILL)


def test_10_parser_dung_model_Pydantic_DAY_DU_ca_voi_gioi_han_KHONG_co_trong_luoc_do():
    """`maxLength` của `named_points` chỉ có ở Pydantic, không ở lược đồ gửi hay lược đồ đầy đủ."""
    x = ie.parse_extraction(json.dumps(_ban_ghi()))
    assert isinstance(x, ie.ImageProblemExtraction)
    assert _ma_loi(json.dumps(_ban_ghi(named_points=["P" * 25]))) == "VISION_OUTPUT_VALIDATION_FAILED"
    assert _ma_loi(json.dumps(_ban_ghi(status="ok"))) == "VISION_OUTPUT_VALIDATION_FAILED"


def test_11_phan_hoi_sai_mang_ma_VISION_OUTPUT_VALIDATION_FAILED(monkeypatch):
    assert ie.VisionContractError.code == "VISION_OUTPUT_VALIDATION_FAILED"
    assert _ma_loi("không phải json") == "VISION_OUTPUT_VALIDATION_FAILED"

    async def gia(*a, **k):
        return json.dumps(_ban_ghi(confidence=7))

    monkeypatch.setattr(ie, "call_gemini", gia)
    with pytest.raises(ie.VisionContractError) as exc:
        asyncio.run(ie.extract_problem_from_image(_anh(), "khoa-gia", cache_version=None))
    assert exc.value.code == "VISION_OUTPUT_VALIDATION_FAILED"


def test_12_loi_hau_kiem_KHONG_BAO_GIO_la_tu_choi_an_toan(monkeypatch):
    """Tuyến API: 502 kèm mã hậu kiểm — không có `assessment` nào mang status `rejected`."""
    from app import main

    async def gia(*a, **k):
        return json.dumps(_ban_ghi(named_points=[f"P{i}" for i in range(81)]))

    monkeypatch.setattr(ie, "call_gemini", gia)
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), (255, 255, 255)).save(buf, format="PNG")
    import base64

    r = TestClient(main.app).post("/api/image/extract", json={
        "content": base64.b64encode(buf.getvalue()).decode(), "mime_type": "image/png"})
    assert r.status_code == 502, r.text
    body = r.json()
    assert body["reason_code"] == "VISION_OUTPUT_VALIDATION_FAILED"
    assert "assessment" not in body and body.get("status") != "ok"


# ══ 13–17 · XÁC ĐỊNH, KHÔNG BỊA NGƯỠNG, DANH TÍNH ══════════════════════════
def test_13_canonical_hoa_XAC_DINH_voi_ground_truth_va_luoc_do():
    gt = {"cases": [{"case_id": "C01", "expected_text": DE, "critical_facts": {"point_labels": ["S", "A"]}}]}
    dao = {"cases": [{"critical_facts": {"point_labels": ["S", "A"]}, "expected_text": DE, "case_id": "C01"}]}
    assert ie.canonical_json_bytes(gt) == ie.canonical_json_bytes(dao) == ie.canonical_json_bytes(copy.deepcopy(gt))
    assert "hình chóp".encode("utf-8") in ie.canonical_json_bytes(gt), "không escape Unicode"
    assert b": " not in ie.canonical_json_bytes(gt) and b", " not in ie.canonical_json_bytes({"a": [1, 2]})


def test_14_bo_tu_khoa_KHONG_phu_thuoc_gia_tri__khong_co_nguong_tu_bia():
    for gia_tri in (1, 6, 80, 10_000):
        s = {"type": "array", "maxItems": gia_tri, "items": {"type": "number", "minimum": -gia_tri, "maximum": gia_tri}}
        assert ie.build_gemini_transport_schema(s) == {"type": "array", "items": {"type": "number"}}
    assert set(ie.TRANSPORT_SCHEMA_DROPPED_KEYWORDS) == TU_KHOA_BO


def test_15_chi_bo_TU_KHOA__khong_bo_TRUONG_trung_ten_khong_doi_type_required_enum():
    nguon = {"type": "object", "required": ["maximum", "k"],
             "properties": {"maximum": {"type": "string", "enum": ["a", "b"]},
                            "k": {"type": "integer", "minimum": 0}}}
    assert ie.build_gemini_transport_schema(nguon) == {
        "type": "object", "required": ["maximum", "k"],
        "properties": {"maximum": {"type": "string", "enum": ["a", "b"]}, "k": {"type": "integer"}}}

    def bo(n):
        if isinstance(n, dict):
            return {k: bo(v) if k != "properties" else {t: bo(c) for t, c in v.items()}
                    for k, v in n.items() if k not in TU_KHOA_BO}
        return n
    assert ie.VISION_TRANSPORT_SCHEMA == bo(ie.VISION_RESPONSE_SCHEMA)


def test_16_luoc_do_gui_di_qua_bo_loc_Gemini_NGUYEN_VEN():
    assert gemini._sanitize_gemini_schema(ie.VISION_TRANSPORT_SCHEMA) == ie.VISION_TRANSPORT_SCHEMA


def test_17_danh_tinh_va_khoa_cache_DOI_THEO_luoc_do_gui():
    ident = ie.vision_identity("95")
    assert ie.VISION_TRANSPORT_SCHEMA_SHA256[:16] in ident["vision_schema_version"]
    cu = {**ident, "vision_schema_version": ie.VISION_SCHEMA_VERSION}
    assert ie.extraction_cache_key("a" * 64, ident) != ie.extraction_cache_key("a" * 64, cu)
