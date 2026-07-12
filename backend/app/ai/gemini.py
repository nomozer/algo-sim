"""Lớp gọi Gemini dùng chung + bộ nạp skill.

Skill = file .md trong app/ai/skills/ chứa system prompt (bộ quy tắc) cho một
nhiệm vụ LLM. Tách ra file để: sửa quy tắc không cần đổi code, có version
đưa vào báo cáo, và toàn bộ prompt chỉ tồn tại ở backend (không lộ xuống
trình duyệt).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

MODEL = "gemini-2.5-flash"
SKILLS_DIR = Path(__file__).resolve().parent / "skills"

# Lỗi TẠM THỜI đáng retry (quá tải / hạ tầng). 4xx còn lại (400, 403, 404...)
# là lỗi request → KHÔNG retry. Backoff mũ có giới hạn: 1s → 2s → 4s.
TRANSIENT_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4  # 1 lần đầu + tối đa 3 lần retry
BACKOFF_BASE_SECONDS = 1.0

_skill_cache: dict[str, str] = {}


def load_skill(name: str) -> str:
    """Nạp skill theo tên file (không kèm .md), có cache."""
    if name not in _skill_cache:
        _skill_cache[name] = (SKILLS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return _skill_cache[name]


async def call_gemini(
    api_key: str,
    system_prompt: str,
    user_text: str,
    response_schema: dict | None = None,
    temperature: float = 0.2,
    image: dict | None = None,
) -> str:
    """Gọi Gemini một lượt; ép structured output khi có response_schema.

    `image` (tùy chọn): {"mime_type": ..., "data": <base64>} — dùng cho bước
    phiên dịch ảnh (M4). Ảnh chỉ là một part của đầu vào, không đổi contract.
    """
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={api_key}"
    )
    generation_config: dict = {"temperature": temperature}
    if response_schema is not None:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = response_schema

    parts: list[dict] = []
    if image is not None:
        parts.append({"inline_data": {"mime_type": image["mime_type"], "data": image["data"]}})
    parts.append({"text": user_text})

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": generation_config,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(MAX_ATTEMPTS):
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                break
            # Lỗi tạm thời + còn lượt → chờ backoff rồi thử lại
            if res.status_code in TRANSIENT_STATUS and attempt < MAX_ATTEMPTS - 1:
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                continue
            # Lỗi request (4xx) hoặc hết lượt retry → báo lỗi
            raise RuntimeError(f"Gemini API lỗi HTTP {res.status_code}: {res.text[:300]}")

    body = res.json()
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        text = None
    if not text:
        raise RuntimeError("Gemini không trả về nội dung nào.")
    return text
