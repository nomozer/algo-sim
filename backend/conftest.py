# -*- coding: utf-8 -*-
"""Cấu hình pytest (M7.14T) — OFFLINE-FIRST.

Hai việc:
1. Giúp pytest import được package `app` khi chạy từ thư mục backend/.
2. HARD GUARD: pytest mặc định KHÔNG BAO GIỜ gọi Gemini thật.

Vì sao guard đặt Ở ĐÂY chứ không trong app/ai/gemini.py:
- Biên mạng thật là `httpx.AsyncClient.post` — chỉ gemini.py dùng httpx.
  Patch đúng biên đó thì test nào QUÊN MOCK sẽ chết TRƯỚC khi ra mạng.
- tests/test_gemini.py có quyền chính đáng gọi call_gemini với transport GIẢ
  (nó thay hẳn gemini.httpx.AsyncClient) — guard ở biên thật không đụng tới nó.
- Production code không phải mang logic test.

Hệ quả quan trọng: toàn bộ suite xanh ⇔ KHÔNG test nào chạm mạng (nếu có, nó
đã raise). Đây chính là bằng chứng cho "pytest = 0 real API call".

Thoát guard: chỉ khi ALLOW_LIVE_AI=1 (dùng cho live eval, không dùng trong CI).
"""

import os

import httpx
import pytest

BLOCK_MESSAGE = "Real Gemini API call blocked during offline tests."


def live_allowed() -> bool:
    return os.getenv("ALLOW_LIVE_AI") == "1"


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    """Chặn MỌI HTTP POST thật qua httpx + gỡ key thật khỏi môi trường.

    Lớp 2 (gỡ key): backend/.env được load_dotenv nạp lúc import db.py, nên
    GEMINI_API_KEY THẬT nằm trong os.environ suốt phiên pytest. Test nào cần
    key giả vẫn tự monkeypatch.setenv (chạy sau fixture này).
    """
    if live_allowed():
        return

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Chặn ở TRANSPORT MẠNG THẬT, không phải ở client: TestClient của FastAPI
    # dùng ASGITransport (in-process, không ra mạng) nên vẫn chạy bình thường.
    async def blocked_async(self, *args, **kwargs):
        raise RuntimeError(BLOCK_MESSAGE)

    def blocked_sync(self, *args, **kwargs):
        raise RuntimeError(BLOCK_MESSAGE)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked_async)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked_sync)
