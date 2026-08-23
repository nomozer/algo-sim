# -*- coding: utf-8 -*-
"""ROUTE NGỮ NGHĨA PHẢI ĐƯỢC NỐI VÀO ĐƯỜNG SẢN PHẨM THẬT.

─── SỰ CỐ ─────────────────────────────────────────────────────────────────

`main.py` gọi `run_pipeline(text, api_key, pattern_store=...)` — KHÔNG truyền
`semantic_route`. Tham số ấy mặc định `"off"` trong `ai/pipeline.py`, nên
`_semantic_shadow` **không bao giờ chạy trong production**.

Hệ quả learner-facing đã chụp được màn hình: bài "kiểm tra ngoặc bằng Stack" rơi
xuống `generic.rule_scene` — miền khai báo tĩnh — và hiện narration "đẩy '(' vào
ngăn xếp" ở bước 8/17 trong khi hình ngăn xếp RỖNG. Engine duy nhất mang trạng
thái theo bước (`SemanticProgramInterpreter`) bị tắt ở đúng chỗ nó cần chạy.

Đây KHÔNG phải lỗi của route ngữ nghĩa. Nó chưa từng được gọi.

─── VÌ SAO TEST NÀY TỒN TẠI ───────────────────────────────────────────────

Mọi unit test của route đều xanh — chúng gọi thẳng `run_pipeline(...,
semantic_route="shadow")`. Không test nào hỏi câu *"đường HTTP thật có truyền
tham số ấy không?"*. Đúng khoảng trống mà bất biến #22 đã từng vá một lần
(`stage_semantic_program` không có ai gọi): mảnh nào cũng xanh mà chưa mảnh nào
được ghép.

Test này khoá **đường dây**, không khoá hành vi route. Nó ĐỎ nếu `main.py` lại
bỏ mất tham số.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

#: Đúng đề đã dựng nên màn hình hỏng.
DE_BAI = "Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng ngăn xếp Stack với chuỗi {[()]}."


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _bat_run_pipeline():
    """Chộp tham số `run_pipeline` NHẬN ĐƯỢC, không quan tâm nó làm gì."""
    da_nhan: dict = {}

    async def gia(text, api_key, **kw):
        da_nhan.update(kw)
        da_nhan["text"] = text
        return {
            "status": "unsupported",
            "reason": "test double",
            "failure_category": "capability_gap",
        }

    return gia, da_nhan


def test_main_py_TRUYEN_semantic_route_vao_run_pipeline(client, monkeypatch):
    """Cọc chính. Bỏ `semantic_route=` khỏi `main.py` ⇒ test này ĐỎ."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia-cho-test")
    gia, da_nhan = _bat_run_pipeline()

    with patch("app.main.run_pipeline", gia):
        client.post(
            "/api/analyze",
            json={"input": {"type": "text", "content": DE_BAI}},
        )

    assert "semantic_route" in da_nhan, (
        "`main.py` gọi `run_pipeline` mà KHÔNG truyền `semantic_route`. Tham số "
        "mặc định là 'off', nên route sinh ngữ nghĩa không bao giờ chạy trong "
        "sản phẩm — đúng sự cố đã chụp màn hình."
    )


def test_che_do_route_do_SERVER_so_huu_va_doc_duoc_tu_moi_truong(monkeypatch):
    """Phải bật `serve` được TƯỜNG MINH, và không hard-code riêng bài nào."""
    from app.main import semantic_route_mode

    monkeypatch.delenv("SEMANTIC_ROUTE_MODE", raising=False)
    assert semantic_route_mode() == "off", "Mặc định phải là 'off' — production không đổi một bit khi chưa ai bật."

    for che_do in ("shadow", "serve", "off"):
        monkeypatch.setenv("SEMANTIC_ROUTE_MODE", che_do)
        assert semantic_route_mode() == che_do


def test_gia_tri_la_bi_ep_ve_off_chu_khong_no_giua_chung(monkeypatch):
    """Cấu hình sai chính tả KHÔNG được biến thành một chế độ thứ tư im lặng."""
    from app.main import semantic_route_mode

    for rac in ("serve ", "SERVE", "bat", "1", "true", ""):
        monkeypatch.setenv("SEMANTIC_ROUTE_MODE", rac)
        assert semantic_route_mode() in ("off", "shadow", "serve"), f"giá trị lạ {rac!r} lọt ra ngoài tập hợp lệ"


def test_che_do_da_cau_hinh_DEN_DUOC_run_pipeline(client, monkeypatch):
    """Không chỉ 'có truyền' — phải truyền ĐÚNG giá trị đang cấu hình."""
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia-cho-test")
    monkeypatch.setenv("SEMANTIC_ROUTE_MODE", "serve")
    gia, da_nhan = _bat_run_pipeline()

    with patch("app.main.run_pipeline", gia):
        client.post(
            "/api/analyze",
            json={"input": {"type": "text", "content": DE_BAI}},
        )

    assert da_nhan.get("semantic_route") == "serve"
