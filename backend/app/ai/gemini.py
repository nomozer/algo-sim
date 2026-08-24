"""Lớp gọi Gemini dùng chung + bộ nạp skill.

Skill = file .md trong app/ai/skills/ chứa system prompt (bộ quy tắc) cho một
nhiệm vụ LLM. Tách ra file để: sửa quy tắc không cần đổi code, có version
đưa vào báo cáo, và toàn bộ prompt chỉ tồn tại ở backend (không lộ xuống
trình duyệt).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx

from app.ai.telemetry import current_stage, record_usage

#: Model dùng cho MỌI stage. Đọc từ môi trường để A/B được **mà không phải sửa
#: mã** — sửa mã thì mỗi lần thử một model là một lần `measured_system.tree_hash`
#: trôi, và ta lại đóng băng candidate sáu lần trong một ngày như 2026-08-23.
#:
#: MẶC ĐỊNH GIỮ NGUYÊN `gemini-2.5-flash`: đổi model là quyết định vận hành
#: tường minh, không phải tác dụng phụ của một lần nâng cấp — cùng luật với
#: `SEMANTIC_ROUTE_MODE`.
#:
#: ⚠️ Model là MỘT PHẦN DANH TÍNH của hệ được đo (`model_target` trong seal
#: manifest). Đổi nó ⇒ con số của lượt trước không còn so được trực tiếp. Lượt
#: đo nào cũng phải ghi model đã dùng vào artifact, không suy từ mặc định.
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SKILLS_DIR = Path(__file__).resolve().parent / "skills"

# Lỗi TẠM THỜI đáng retry (quá tải / hạ tầng). 4xx còn lại (400, 403, 404...)
# là lỗi request → KHÔNG retry. Backoff mũ có giới hạn: 1s → 2s → 4s.
TRANSIENT_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4  # 1 lần đầu + tối đa 3 lần retry
BACKOFF_BASE_SECONDS = 1.0

_skill_cache: dict[str, str] = {}


# ── Budget/telemetry (M7.14T) — INERT trong production ────────
# Chỉ là các số nguyên đếm request; live.py bật trần để không đốt quota.
# Không I/O, không đổi hành vi khi budget = None (mặc định).

class BudgetExceeded(RuntimeError):
    """Vượt trần API call do live.py đặt — dừng SẠCH, không gọi thêm."""


class ApiBudget:
    """Đếm request HTTP THẬT + chặn khi vượt trần (M7.14T §7)."""

    def __init__(self, max_api_calls: int | None = None, max_attempts: int | None = None,
                 max_logical_calls: int | None = None):
        self.max_api_calls = max_api_calls
        # Trần LƯỢT LOGIC (số lần `call_gemini` được gọi). Trước 2026-08-21 chỉ
        # có trần HTTP, nên một lượt đánh giá có thể vượt xa ngân sách lượt logic
        # mà không gì chặn: pipeline có nhiều tầng retry TỰ NÓ — `_call_json`
        # retry 1 lần cho analyze/classify, one-route recovery gọi classify
        # thêm lượt nữa, `stage_simulate*` lặp tới 3. Đếm mà không chặn thì con
        # số ngân sách chỉ là lời chúc.
        self.max_logical_calls = max_logical_calls
        # Trần retry TRANSIENT (HTTP) — KHÔNG đụng retry validation của pipeline
        # (3 lần simulate là ngữ nghĩa sản phẩm, đổi là hỏng benchmark).
        self.max_attempts = max_attempts or MAX_ATTEMPTS
        self.http_requests = 0     # tổng request thật (kể cả retry)
        self.logical_calls = 0     # số lần call_gemini được gọi
        self.retry_requests = 0    # request phát sinh do retry transient
        self.transient_hits = 0    # số lần gặp 429/5xx
        self.aborted = False

    def note_call(self) -> None:
        """Gọi TRƯỚC mỗi lượt logic; vượt trần → BudgetExceeded."""
        if (
            self.max_logical_calls is not None
            and self.logical_calls >= self.max_logical_calls
        ):
            self.aborted = True
            raise BudgetExceeded(
                f"Đã chạm trần {self.max_logical_calls} lượt LLM logic — dừng "
                "để không đốt thêm quota."
            )
        self.logical_calls += 1

    def note_request(self, is_retry: bool) -> None:
        """Gọi TRƯỚC mỗi request thật; vượt trần → BudgetExceeded."""
        if self.max_api_calls is not None and self.http_requests >= self.max_api_calls:
            self.aborted = True
            raise BudgetExceeded(
                f"Đã chạm trần {self.max_api_calls} API call — dừng để không đốt thêm quota."
            )
        self.http_requests += 1
        if is_retry:
            self.retry_requests += 1

    def note_transient(self) -> None:
        self.transient_hits += 1


# Budget đang hiệu lực (None = production/pytest: không đếm, không chặn).
BUDGET: ApiBudget | None = None


def set_budget(budget: ApiBudget | None) -> None:
    global BUDGET
    BUDGET = budget


def load_skill(name: str) -> str:
    """Nạp skill theo tên file (không kèm .md), có cache."""
    if name not in _skill_cache:
        _skill_cache[name] = (SKILLS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return _skill_cache[name]


def _co_tham_chieu(obj: Any) -> bool:
    """Schema có `$ref` không? Có ⇒ Gemini KHÔNG diễn đạt được."""
    if isinstance(obj, dict):
        return "$ref" in obj or any(_co_tham_chieu(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_co_tham_chieu(x) for x in obj)
    return False


def _sanitize_gemini_schema(obj: Any) -> Any | None:
    """Dọn schema cho Gemini, hoặc trả `None` khi Gemini không diễn đạt được nó.

    TỪNG HỎNG CÂM VÀ HỎNG TOÀN BỘ (phát hiện 2026-08-22, lượt chạy pilot đầu
    tiên với API thật): bản cũ xoá `$defs` nhưng GIỮ NGUYÊN các `$ref` trỏ vào
    đó, để lại tham chiếu treo, nên payload bị API trả HTTP 400 —

        Unknown name "$ref" ... Unknown name "const" ...

    Hệ quả: `stage_semantic_program` gửi schema sinh từ Pydantic và **chưa từng
    gọi thành công một lần nào**. 1725 test offline vẫn xanh vì tất cả đều mock
    `call_gemini`; chỉ một lượt chạy thật mới lộ ra.

    VÌ SAO KHÔNG NỘI SUY `$ref` THAY VÌ BỎ SCHEMA: schema IR có 37 `$defs`, 421
    `$ref`, 40 `oneOf` kèm `discriminator`, và **đệ quy** (câu lệnh chứa câu
    lệnh). Nội suy một schema đệ quy thì không dừng. Đây là giới hạn của dialect
    schema Gemini, không phải một trường viết sai.

    RÀNG BUỘC CẤU TRÚC KHÔNG MẤT ĐI: nó vốn không nằm ở Gemini. `responseSchema`
    chỉ làm tăng tỉ lệ trúng; thứ BẢO ĐẢM là `validate_semantic_program` chạy
    phía server, và nó vẫn từ chối y như trước. Bỏ schema làm đầu ra kém đều
    hơn, KHÔNG làm hợp đồng lỏng hơn.
    """
    if _co_tham_chieu(obj):
        return None

    if isinstance(obj, dict):
        cleaned: dict = {}
        for k, v in obj.items():
            if k in ("additionalProperties", "$schema", "$defs", "definitions", "default"):
                continue
            # Pydantic phát `const` cho `Literal`; Gemini chỉ biết `enum`.
            if k == "const":
                cleaned["enum"] = [v]
                continue
            cleaned[k] = _sanitize_gemini_schema(v)
        return cleaned
    if isinstance(obj, list):
        return [_sanitize_gemini_schema(item) for item in obj]
    return obj


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
        # JSON mode giữ nguyên trong MỌI trường hợp — đầu ra vẫn phải là JSON.
        generation_config["responseMimeType"] = "application/json"
        an_toan = _sanitize_gemini_schema(response_schema)
        if an_toan is not None:
            generation_config["responseSchema"] = an_toan
        # `None` ⇒ schema có `$ref`, Gemini không diễn đạt được (xem
        # `_sanitize_gemini_schema`). Gửi kèm là HTTP 400 cho MỌI lượt gọi. Bỏ
        # schema, giữ JSON mode; ràng buộc thật vẫn do validator phía server áp.

    parts: list[dict] = []
    if image is not None:
        parts.append({"inline_data": {"mime_type": image["mime_type"], "data": image["data"]}})
    parts.append({"text": user_text})

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": generation_config,
    }
    budget = BUDGET
    max_attempts = budget.max_attempts if budget else MAX_ATTEMPTS
    if budget:
        budget.note_call()

    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(max_attempts):
            if budget:
                budget.note_request(is_retry=attempt > 0)  # vượt trần → BudgetExceeded
            try:
                res = await client.post(url, json=payload)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                    continue
                raise RuntimeError(f"Gemini API timeout hoặc lỗi mạng: {e}")

            if res.status_code == 200:
                break
            if res.status_code in TRANSIENT_STATUS:
                if budget:
                    budget.note_transient()
                # Lỗi tạm thời + còn lượt → chờ backoff rồi thử lại
                if attempt < max_attempts - 1:
                    await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
                    continue
            # Lỗi request (4xx) hoặc hết lượt retry → báo lỗi
            raise RuntimeError(f"Gemini API lỗi HTTP {res.status_code}: {res.text[:300]}")

    body = res.json()

    # Ghi token TRƯỚC khi parse nội dung: lượt trả về rỗng vẫn đã tiêu token, và
    # bỏ sót đúng những lượt hỏng sẽ làm baseline đẹp hơn sự thật.
    record_usage(
        current_stage(), body.get("usageMetadata") if isinstance(body, dict) else None
    )

    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        text = None
    if not text:
        raise RuntimeError("Gemini không trả về nội dung nào.")
    return text
